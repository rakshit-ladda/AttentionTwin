import pytest
from datetime import datetime
import pandas as pd

from app.ml.synthetic_generator import SyntheticDataGenerator
from app.ml.feature_pipeline import FeaturePipeline, validate_feature_dataset, extract_single_event_features
from app.ml.split_utils import chronological_split, user_held_out_split
from app.ml.feature_schema import (
    ALL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    NUMERIC_FEATURE_NAMES,
    TARGET_BINARY,
    COLD_START_DEFAULTS,
)


def test_deterministic_synthetic_generation():
    """Verify that using the same seed produces identical synthetic datasets."""
    gen1 = SyntheticDataGenerator(seed=123)
    data1 = gen1.generate_dataset(num_users=3, num_events=30, days=2)

    gen2 = SyntheticDataGenerator(seed=123)
    data2 = gen2.generate_dataset(num_users=3, num_events=30, days=2)

    assert data1["metadata"]["seed"] == 123
    assert len(data1["events"]) == len(data2["events"])
    assert data1["events"][0]["text"] == data2["events"][0]["text"]
    assert data1["events"][0]["timestamp"] == data2["events"][0]["timestamp"]
    assert data1["events"][-1]["outcome"] == data2["events"][-1]["outcome"]


def test_feature_pipeline_schema_and_types():
    """Verify that feature pipeline transforms raw events into a compliant DataFrame."""
    gen = SyntheticDataGenerator(seed=42)
    raw = gen.generate_dataset(num_users=2, num_events=40, days=2)

    pipeline = FeaturePipeline()
    df = pipeline.transform(raw["events"])

    # Required feature columns present
    for col in ALL_FEATURE_NAMES:
        assert col in df.columns, f"Feature column {col} missing from pipeline output"

    # Target columns present
    assert TARGET_BINARY in df.columns
    assert "outcome_label" in df.columns

    # Check that categoricals remain strings
    for col in CATEGORICAL_FEATURE_NAMES:
        assert pd.api.types.is_string_dtype(df[col]), f"Categorical feature {col} must remain string type"

    # Validation function reports valid
    val_summary = validate_feature_dataset(df)
    assert val_summary["is_valid"] is True
    assert len(val_summary["errors"]) == 0


def test_cold_start_neutral_defaults():
    """Verify that an event with no prior history receives documented cold-start defaults."""
    raw_event = {
        "event_id": 101,
        "timestamp": "2026-10-25T10:00:00Z",
        "source_app": "Slack",
        "app_category": "communication",
        "notification_category": "direct_message",
        "text": "Hello world",
        "context_data": {},
    }

    # Zero user history
    feats = extract_single_event_features(raw_event, user_history_events=None)
    assert feats["app_historical_open_rate"] == COLD_START_DEFAULTS["app_historical_open_rate"]
    assert feats["user_historical_open_rate"] == COLD_START_DEFAULTS["user_historical_open_rate"]
    assert feats["recent_notification_count_15m"] == 0
    assert feats["minutes_since_last_notification"] == COLD_START_DEFAULTS["minutes_since_last_notification"]


def test_no_future_leakage_in_historical_features():
    """Verify that historical stats only consider events strictly prior to current event."""
    t1 = "2026-10-25T10:00:00Z"
    t2 = "2026-10-25T10:30:00Z"
    t3 = "2026-10-25T11:00:00Z"

    events = [
        {
            "event_id": 1,
            "user_id": "u1",
            "timestamp": t1,
            "source_app": "Slack",
            "app_category": "communication",
            "notification_category": "dm",
            "text": "Alert 1",
            "decision": {"action": "allow"},
            "outcome": {"opened_within_5min": 1, "outcome_label": "opened_quickly"},
        },
        {
            "event_id": 2,
            "user_id": "u1",
            "timestamp": t2,
            "source_app": "Slack",
            "app_category": "communication",
            "notification_category": "dm",
            "text": "Alert 2",
            "decision": {"action": "allow"},
            "outcome": {"opened_within_5min": 0, "outcome_label": "ignored"},
        },
        {
            "event_id": 3,
            "user_id": "u1",
            "timestamp": t3,
            "source_app": "Slack",
            "app_category": "communication",
            "notification_category": "dm",
            "text": "Alert 3",
            "decision": {"action": "allow"},
            "outcome": {"opened_within_5min": 1, "outcome_label": "opened_quickly"},
        },
    ]

    pipeline = FeaturePipeline()
    df = pipeline.transform(events)

    # Event 1: Cold start
    assert df.loc[0, "user_historical_open_rate"] == COLD_START_DEFAULTS["user_historical_open_rate"]

    # Event 2: Should know ONLY about Event 1 (1 open / 1 event = 1.0)
    assert df.loc[1, "user_historical_open_rate"] == 1.0
    assert df.loc[1, "minutes_since_last_notification"] == 30.0

    # Event 3: Should know about Event 1 & 2 (1 open, 1 ignored out of 2 = 0.5)
    # Does NOT leak Event 3's own outcome
    assert df.loc[2, "user_historical_open_rate"] == 0.5


def test_split_strategies():
    """Verify chronological and user-held-out splits maintain integrity."""
    gen = SyntheticDataGenerator(seed=42)
    raw = gen.generate_dataset(num_users=4, num_events=80, days=3)
    pipeline = FeaturePipeline()
    df = pipeline.transform(raw["events"])

    # 1. Chronological split
    train_c, test_c, meta_c = chronological_split(df, train_ratio=0.75)
    assert len(train_c) + len(test_c) == len(df)
    assert meta_c["train_rows"] == len(train_c)
    assert meta_c["test_rows"] == len(test_c)

    # 2. User-held-out split
    train_u, test_u, meta_u = user_held_out_split(df, test_users_count=1, seed=42)
    assert len(train_u) + len(test_u) == len(df)
    assert len(meta_u["test_users"]) == 1
    # Test users must NOT appear in training set
    train_users_set = set(train_u["user_id"].unique())
    for tu in meta_u["test_users"]:
        assert tu not in train_users_set
