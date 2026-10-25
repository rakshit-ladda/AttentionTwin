"""
AttentionTwin Feature Engineering Pipeline
=========================================
Transforms raw notification events into validated, leakage-safe, model-ready feature datasets.

Guarantees:
- Chronological computation: Historical stats use ONLY events occurring before the target event.
- Zero future leakage: No current or future outcome informs any input feature.
- Cold-start safety: Clean neutral defaults applied when no history exists.
- Clean semantic types: Categorical strings preserved without arbitrary numeric encodings.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.ml.feature_schema import (
    ALL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    NUMERIC_FEATURE_NAMES,
    TARGET_BINARY,
    TARGET_MULTICLASS,
    COLD_START_DEFAULTS,
)


def extract_single_event_features(
    raw_event: Dict[str, Any],
    user_history_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Extract model-ready features for a single notification event.
    Optionally computes historical features using user_history_events (which MUST occur before raw_event).
    """
    ts_str = raw_event["timestamp"]
    if isinstance(ts_str, str):
        ts = datetime.fromisoformat(ts_str)
    else:
        ts = ts_str

    hour = ts.hour
    day_of_week = ts.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0

    context = raw_event.get("context_data") or {}
    focus_mode = context.get("focus_mode") or COLD_START_DEFAULTS["focus_mode"]
    is_focus_session = int(context.get("is_focus_session", COLD_START_DEFAULTS["is_focus_session"]))

    text = raw_event.get("text") or ""
    text_length = raw_event.get("text_length") or len(text)

    # Base feature dictionary
    features: Dict[str, Any] = {
        "source_app": raw_event.get("source_app", "unknown"),
        "app_category": raw_event.get("app_category", "unknown"),
        "notification_category": raw_event.get("notification_category", "unknown"),
        "focus_mode": focus_mode,
        "text_length": text_length,
        "hour_of_day": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_focus_session": is_focus_session,
    }

    # Historical feature calculation
    if not user_history_events:
        # Cold start: apply neutral baseline defaults
        features["recent_notification_count_15m"] = COLD_START_DEFAULTS["recent_notification_count_15m"]
        features["minutes_since_last_notification"] = COLD_START_DEFAULTS["minutes_since_last_notification"]
        features["notification_load_1h"] = COLD_START_DEFAULTS["notification_load_1h"]
        features["app_historical_open_rate"] = COLD_START_DEFAULTS["app_historical_open_rate"]
        features["app_historical_ignore_rate"] = COLD_START_DEFAULTS["app_historical_ignore_rate"]
        features["user_historical_open_rate"] = COLD_START_DEFAULTS["user_historical_open_rate"]
        features["recent_allow_rate_1h"] = COLD_START_DEFAULTS["recent_allow_rate_1h"]
        features["recent_suppress_rate_1h"] = COLD_START_DEFAULTS["recent_suppress_rate_1h"]
    else:
        # Filter strictly prior events
        prior = [
            e for e in user_history_events
            if (datetime.fromisoformat(e["timestamp"]) if isinstance(e["timestamp"], str) else e["timestamp"]) < ts
        ]

        if not prior:
            for k in [
                "recent_notification_count_15m",
                "minutes_since_last_notification",
                "notification_load_1h",
                "app_historical_open_rate",
                "app_historical_ignore_rate",
                "user_historical_open_rate",
                "recent_allow_rate_1h",
                "recent_suppress_rate_1h",
            ]:
                features[k] = COLD_START_DEFAULTS[k]
        else:
            # Most recent prior event
            prior_ts = [
                datetime.fromisoformat(e["timestamp"]) if isinstance(e["timestamp"], str) else e["timestamp"]
                for e in prior
            ]
            last_ts = max(prior_ts)
            gap_minutes = max(0.0, (ts - last_ts).total_seconds() / 60.0)
            features["minutes_since_last_notification"] = min(gap_minutes, 1440.0)

            # Rolling window counts
            fifteen_m_ago = (ts.timestamp() - 15 * 60)
            one_h_ago = (ts.timestamp() - 60 * 60)

            count_15m = sum(
                1 for e, e_ts in zip(prior, prior_ts)
                if e_ts.timestamp() >= fifteen_m_ago
            )
            count_1h = sum(
                1 for e, e_ts in zip(prior, prior_ts)
                if e_ts.timestamp() >= one_h_ago
            )
            features["recent_notification_count_15m"] = count_15m
            features["notification_load_1h"] = count_1h

            # Global user historical open rate
            opened_prior = [
                e for e in prior
                if e.get("outcome", {}).get("opened_within_5min") == 1
                or e.get("outcome", {}).get("outcome_label") == "opened_quickly"
            ]
            features["user_historical_open_rate"] = round(len(opened_prior) / len(prior), 3)

            # App-specific historical rates
            app_prior = [e for e in prior if e.get("source_app") == features["source_app"]]
            if app_prior:
                app_opened = sum(
                    1 for e in app_prior
                    if e.get("outcome", {}).get("opened_within_5min") == 1
                    or e.get("outcome", {}).get("outcome_label") == "opened_quickly"
                )
                app_ignored = sum(
                    1 for e in app_prior
                    if e.get("outcome", {}).get("outcome_label") == "ignored"
                )
                features["app_historical_open_rate"] = round(app_opened / len(app_prior), 3)
                features["app_historical_ignore_rate"] = round(app_ignored / len(app_prior), 3)
            else:
                features["app_historical_open_rate"] = COLD_START_DEFAULTS["app_historical_open_rate"]
                features["app_historical_ignore_rate"] = COLD_START_DEFAULTS["app_historical_ignore_rate"]

            # Recent decision rates in the past 1 hour
            recent_1h_events = [e for e, e_ts in zip(prior, prior_ts) if e_ts.timestamp() >= one_h_ago]
            if recent_1h_events:
                allows = sum(1 for e in recent_1h_events if e.get("decision", {}).get("action") == "allow")
                suppresses = sum(1 for e in recent_1h_events if e.get("decision", {}).get("action") == "suppress")
                features["recent_allow_rate_1h"] = round(allows / len(recent_1h_events), 3)
                features["recent_suppress_rate_1h"] = round(suppresses / len(recent_1h_events), 3)
            else:
                features["recent_allow_rate_1h"] = COLD_START_DEFAULTS["recent_allow_rate_1h"]
                features["recent_suppress_rate_1h"] = COLD_START_DEFAULTS["recent_suppress_rate_1h"]

    return features


class FeaturePipeline:
    """End-to-end transformation from raw synthetic event stream to model-ready DataFrame."""

    def transform(self, events: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Process events chronologically per user, computing historical features with zero future leakage.
        """
        # Ensure events are sorted chronologically
        events_sorted = sorted(events, key=lambda x: x["timestamp"])

        # Group by user to maintain historical state per user
        user_history: Dict[str, List[Dict[str, Any]]] = {}
        rows = []

        for e in events_sorted:
            u_id = e.get("user_id", "default_user")
            history = user_history.setdefault(u_id, [])

            # Extract features using ONLY history prior to this event
            feats = extract_single_event_features(e, user_history_events=history)

            # Metadata & Targets
            row = {
                "event_id": e.get("event_id"),
                "user_id": u_id,
                "timestamp": e.get("timestamp"),
                "decision_action": e.get("decision", {}).get("action", "allow"),
                **feats,
            }

            # Outcome labels (target representation)
            outcome = e.get("outcome", {})
            row[TARGET_BINARY] = int(outcome.get("opened_within_5min", 0))
            row[TARGET_MULTICLASS] = str(outcome.get("outcome_label", "ignored"))

            rows.append(row)
            # Add to history for subsequent events
            history.append(e)

        df = pd.DataFrame(rows)
        return df


def validate_feature_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate dataset against schema contracts, missing values, and leakage invariants.
    """
    errors: List[str] = []

    # 1. Required columns
    for col in ALL_FEATURE_NAMES + [TARGET_BINARY, TARGET_MULTICLASS, "user_id", "timestamp"]:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    # 2. Null values
    null_counts = df[ALL_FEATURE_NAMES + [TARGET_BINARY]].isnull().sum()
    nulls = null_counts[null_counts > 0].to_dict()
    if nulls:
        errors.append(f"Found unexpected missing values in feature/target columns: {nulls}")

    # 3. Target binary values
    if TARGET_BINARY in df.columns:
        invalid_binary = df[~df[TARGET_BINARY].isin([0, 1])]
        if len(invalid_binary) > 0:
            errors.append(f"Invalid binary target values found (must be 0 or 1): count={len(invalid_binary)}")

    # 4. Target multiclass values
    if TARGET_MULTICLASS in df.columns:
        allowed_multiclass = {"opened_quickly", "opened_later", "ignored"}
        invalid_multi = df[~df[TARGET_MULTICLASS].isin(allowed_multiclass)]
        if len(invalid_multi) > 0:
            errors.append(f"Invalid multiclass target values: count={len(invalid_multi)}")

    # 5. Chronological order per user
    if "user_id" in df.columns and "timestamp" in df.columns:
        for u_id, group in df.groupby("user_id"):
            ts_series = pd.to_datetime(group["timestamp"])
            if not ts_series.is_monotonic_increasing:
                errors.append(f"Events for user {u_id} are not monotonically increasing in time.")
                break

    # Summary metrics
    summary = {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "num_rows": len(df),
        "num_users": int(df["user_id"].nunique()) if "user_id" in df.columns else 0,
        "date_min": str(df["timestamp"].min()) if "timestamp" in df.columns else None,
        "date_max": str(df["timestamp"].max()) if "timestamp" in df.columns else None,
        "target_binary_distribution": df[TARGET_BINARY].value_counts(normalize=True).to_dict() if TARGET_BINARY in df.columns else {},
        "target_multiclass_distribution": df[TARGET_MULTICLASS].value_counts(normalize=True).to_dict() if TARGET_MULTICLASS in df.columns else {},
        "decision_distribution": df["decision_action"].value_counts(normalize=True).to_dict() if "decision_action" in df.columns else {},
        "app_distribution": df["source_app"].value_counts(normalize=True).head(5).to_dict() if "source_app" in df.columns else {},
    }

    return summary
