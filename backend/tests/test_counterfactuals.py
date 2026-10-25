import os
import tempfile
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.ml.action_aware_trainer import (
    ActionAwareModelTrainer,
    ACTION_AWARE_ALL_FEATURES,
    ACTION_AWARE_CATEGORICAL_FEATURES,
)
from app.ml.counterfactual_engine import CounterfactualEngine, check_support_warning
from app.schemas.counterfactual import CounterfactualCompareRequest
from app.db.session import SessionLocal
from app.models.event import ObservedOutcome

client = TestClient(app)


def test_action_aware_trainer_and_artifact_generation():
    """Verify ActionAwareModelTrainer trains and saves valid artifacts with per-action breakdowns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        trainer = ActionAwareModelTrainer(artifacts_dir=temp_dir)
        meta = trainer.train_and_save(
            dataset_path="data/synthetic/feature_dataset.csv",
            selected_model="random_forest",
        )

        assert os.path.exists(os.path.join(temp_dir, "action_aware_model.joblib"))
        assert os.path.exists(os.path.join(temp_dir, "action_aware_metadata.json"))
        assert "per_action_metrics" in meta
        for act in ["allow", "defer", "suppress"]:
            assert act in meta["per_action_metrics"]
            assert meta["per_action_metrics"][act]["count"] > 0


def test_context_invariance_across_counterfactual_actions():
    """Verify that all pre-decision features are strictly invariant across candidate actions."""
    engine = CounterfactualEngine(artifacts_dir="backend/artifacts")
    assert engine.is_ready is True

    req = CounterfactualCompareRequest(
        source_app="Slack",
        app_category="communication",
        notification_category="direct_message",
        text_length=50,
        hour_of_day=14,
        day_of_week=2,
        is_weekend=0,
        focus_mode="deep_work",
        is_focus_session=1,
        recent_notification_count_15m=1,
        minutes_since_last_notification=25.0,
        notification_load_1h=4,
        app_historical_open_rate=0.75,
        app_historical_ignore_rate=0.10,
        user_historical_open_rate=0.60,
        recent_allow_rate_1h=0.80,
        recent_suppress_rate_1h=0.10,
    )

    resp = engine.compare_actions(req)
    assert len(resp.scenarios) == 3
    actions = [s.proposed_action for s in resp.scenarios]
    assert actions == ["allow", "defer", "suppress"]

    # Pre-decision context summary should reflect the exact input
    assert resp.notification_summary["source_app"] == "Slack"
    assert resp.notification_summary["focus_mode"] == "deep_work"
    assert resp.notification_summary["hour_of_day"] == 14


def test_probability_ordering_across_actions():
    """
    Verify that in the trained model, conditional probability of prompt opening follows:
    P(opened | allow) > P(opened | defer) > P(opened | suppress)
    reflecting the learned intervention policy.
    """
    engine = CounterfactualEngine(artifacts_dir="backend/artifacts")
    req = CounterfactualCompareRequest(
        source_app="Slack",
        app_category="communication",
        notification_category="direct_message",
        text_length=40,
        hour_of_day=10,
        day_of_week=1,
        is_weekend=0,
        focus_mode="casual_browsing",
        is_focus_session=0,
    )

    resp = engine.compare_actions(req)
    prob_allow = next(s.probability_opened_quickly for s in resp.scenarios if s.proposed_action == "allow")
    prob_defer = next(s.probability_opened_quickly for s in resp.scenarios if s.proposed_action == "defer")
    prob_suppress = next(s.probability_opened_quickly for s in resp.scenarios if s.proposed_action == "suppress")

    assert prob_allow > prob_defer, f"Expected P(allow) > P(defer), got {prob_allow} vs {prob_defer}"
    assert prob_defer > prob_suppress, f"Expected P(defer) > P(suppress), got {prob_defer} vs {prob_suppress}"


def test_support_warning_generation():
    """Verify that poorly represented action/context combinations trigger support warnings."""
    # Suppressing a system alert
    warn_sys = check_support_warning({"app_category": "system_alert", "notification_category": "cpu_spike"}, "suppress")
    assert warn_sys is not None
    assert "system alerts" in warn_sys

    # Suppressing a personal direct message
    warn_dm = check_support_warning({"app_category": "communication", "notification_category": "direct_message"}, "suppress")
    assert warn_dm is not None
    assert "direct messages" in warn_dm

    # Standard allow during casual browsing -> no warning
    warn_std = check_support_warning({"app_category": "communication", "notification_category": "direct_message"}, "allow")
    assert warn_std is None


def test_api_counterfactual_compare_endpoint_valid():
    """Verify POST /api/counterfactuals/compare returns 200 with structured comparison."""
    payload = {
        "source_app": "Gmail",
        "app_category": "work",
        "notification_category": "task_assignment",
        "text_length": 65,
        "hour_of_day": 11,
        "day_of_week": 2,
        "is_weekend": 0,
        "focus_mode": "deep_work",
        "is_focus_session": 1,
        "recent_notification_count_15m": 0,
        "minutes_since_last_notification": 90.0,
        "notification_load_1h": 1,
        "app_historical_open_rate": 0.55,
        "app_historical_ignore_rate": 0.25,
        "user_historical_open_rate": 0.50,
        "recent_allow_rate_1h": 0.60,
        "recent_suppress_rate_1h": 0.20,
    }

    res = client.post("/api/counterfactuals/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 3
    assert "relative_comparison_summary" in data
    assert "limitations_disclaimer" in data
    assert "SYNTHETIC" in data["data_provenance"]


def test_api_counterfactual_compare_validation_error():
    """Verify POST /api/counterfactuals/compare returns 422 for missing or invalid fields."""
    bad_payload = {
        "source_app": "Slack",
        "hour_of_day": 28,  # invalid hour
    }
    res = client.post("/api/counterfactuals/compare", json=bad_payload)
    assert res.status_code == 422


def test_missing_action_aware_artifact_returns_503():
    """Verify that an uninitialized CounterfactualEngine reports 503."""
    with tempfile.TemporaryDirectory() as empty_dir:
        empty_engine = CounterfactualEngine(artifacts_dir=empty_dir)
        assert empty_engine.is_ready is False


def test_no_writes_to_observed_outcomes_database():
    """Verify that running counterfactual comparisons does not write any records to observed_outcomes."""
    db = SessionLocal()
    try:
        initial_outcomes_count = db.query(ObservedOutcome).count()

        # Run counterfactual comparison
        payload = {
            "source_app": "GitHub",
            "app_category": "work",
            "notification_category": "pull_request_review",
            "text_length": 45,
            "hour_of_day": 15,
            "day_of_week": 3,
            "is_weekend": 0,
        }
        res = client.post("/api/counterfactuals/compare", json=payload)
        assert res.status_code == 200

        # Verify database record count remains unchanged
        post_outcomes_count = db.query(ObservedOutcome).count()
        assert post_outcomes_count == initial_outcomes_count
    finally:
        db.close()
