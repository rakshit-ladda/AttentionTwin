import os
import tempfile
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.ml.feature_schema import (
    ALL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    NUMERIC_FEATURE_NAMES,
    TARGET_BINARY,
)
from app.ml.trainer import BaselineModelTrainer, build_preprocessor
from app.ml.predictor import PredictionService
from app.schemas.ml import NotificationPredictionRequest

client = TestClient(app)


def test_build_preprocessor_transformation():
    """Verify ColumnTransformer handles numeric scaling and categorical encoding properly."""
    df_sample = pd.DataFrame([{
        "source_app": "Slack",
        "app_category": "communication",
        "notification_category": "direct_message",
        "focus_mode": "deep_work",
        "text_length": 50,
        "hour_of_day": 14,
        "day_of_week": 2,
        "is_weekend": 0,
        "is_focus_session": 1,
        "recent_notification_count_15m": 2,
        "minutes_since_last_notification": 15.0,
        "notification_load_1h": 5,
        "app_historical_open_rate": 0.8,
        "app_historical_ignore_rate": 0.1,
        "user_historical_open_rate": 0.6,
        "recent_allow_rate_1h": 0.7,
        "recent_suppress_rate_1h": 0.1,
    }])

    preprocessor = build_preprocessor()
    transformed = preprocessor.fit_transform(df_sample)
    # Output should be numeric 2D array without NaN
    assert transformed.shape[0] == 1
    assert not pd.isna(transformed).any()


def test_model_training_and_saving_in_temp_dir():
    """Test trainer runs on synthetic dataset, computes metrics, and serializes artifacts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        trainer = BaselineModelTrainer(artifacts_dir=temp_dir)
        meta = trainer.train_and_save(
            dataset_path="data/synthetic/feature_dataset.csv",
            split_strategy="chronological",
            selected_model="random_forest",
        )

        assert os.path.exists(os.path.join(temp_dir, "baseline_model.joblib"))
        assert os.path.exists(os.path.join(temp_dir, "model_metadata.json"))
        assert meta["model_name"] == "RandomForestClassifier"
        assert meta["target_variable"] == TARGET_BINARY
        assert "dummy_baseline" in meta["comparison"]
        assert meta["metrics"]["accuracy"] > meta["comparison"]["dummy_baseline"]["accuracy"]


def test_prediction_service_save_load_consistency():
    """Verify PredictionService accurately loads saved model and computes probabilities."""
    with tempfile.TemporaryDirectory() as temp_dir:
        trainer = BaselineModelTrainer(artifacts_dir=temp_dir)
        trainer.train_and_save(
            dataset_path="data/synthetic/feature_dataset.csv",
            split_strategy="chronological",
            selected_model="random_forest",
        )

        service = PredictionService(artifacts_dir=temp_dir)
        assert service.is_ready is True

        req = NotificationPredictionRequest(
            source_app="Slack",
            app_category="communication",
            notification_category="direct_message",
            text_length=45,
            hour_of_day=11,
            day_of_week=1,
            is_weekend=0,
            focus_mode="casual_browsing",
            is_focus_session=0,
        )

        pred_resp = service.predict(req)
        assert pred_resp.predicted_class in [0, 1]
        assert 0.0 <= pred_resp.probability_opened_quickly <= 1.0
        assert "SYNTHETIC" in pred_resp.data_provenance
        assert len(pred_resp.limitations_disclaimer) > 0


def test_api_models_status_endpoint():
    """Verify GET /api/models/status returns operational model metadata."""
    res = client.get("/api/models/status")
    assert res.status_code == 200
    data = res.json()
    assert data["is_model_loaded"] is True
    assert data["target"] == TARGET_BINARY
    assert "metrics" in data


def test_api_models_predict_endpoint_valid():
    """Verify POST /api/models/predict accepts valid feature payload."""
    payload = {
        "source_app": "GitHub",
        "app_category": "work",
        "notification_category": "pull_request_review",
        "text_length": 72,
        "hour_of_day": 15,
        "day_of_week": 3,
        "is_weekend": 0,
        "focus_mode": "deep_work",
        "is_focus_session": 1,
        "recent_notification_count_15m": 1,
        "minutes_since_last_notification": 45.0,
        "notification_load_1h": 3,
        "app_historical_open_rate": 0.65,
        "app_historical_ignore_rate": 0.15,
        "user_historical_open_rate": 0.55,
        "recent_allow_rate_1h": 0.8,
        "recent_suppress_rate_1h": 0.0,
    }

    res = client.post("/api/models/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["predicted_class"] in [0, 1]
    assert "probability_opened_quickly" in data
    assert "limitations_disclaimer" in data


def test_api_models_predict_endpoint_validation_errors():
    """Verify POST /api/models/predict returns 422 for invalid payloads."""
    # Missing source_app and hour_of_day
    bad_payload = {
        "app_category": "work",
    }
    res = client.post("/api/models/predict", json=bad_payload)
    assert res.status_code == 422

    # hour_of_day out of range (25)
    invalid_hour = {
        "source_app": "Slack",
        "app_category": "communication",
        "notification_category": "dm",
        "hour_of_day": 25,
        "day_of_week": 1,
    }
    res = client.post("/api/models/predict", json=invalid_hour)
    assert res.status_code == 422


def test_missing_model_artifact_returns_503():
    """Verify that if artifacts are missing, predictor reports not ready / returns 503."""
    with tempfile.TemporaryDirectory() as empty_dir:
        empty_service = PredictionService(artifacts_dir=empty_dir)
        assert empty_service.is_ready is False
        status = empty_service.get_status()
        assert status.is_model_loaded is False


def test_no_target_leakage_in_features():
    """Verify that target columns are strictly absent from ALL_FEATURE_NAMES."""
    assert TARGET_BINARY not in ALL_FEATURE_NAMES
    assert "outcome_label" not in ALL_FEATURE_NAMES
    assert "response_latency_seconds" not in ALL_FEATURE_NAMES
