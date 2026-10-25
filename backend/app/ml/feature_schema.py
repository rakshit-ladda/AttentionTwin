"""
AttentionTwin ML Feature Schema Specification
=============================================
Defines the information available when a notification arrives, logical feature groups,
provenance/derivation types, and neutral cold-start baselines.

Feature Sources:
- OBSERVED: Directly recorded telemetry from event payload (e.g. text length, source app).
- CONTEXT_DERIVED: State of the device/user at notification arrival (e.g. focus mode).
- RULE_DERIVED: Deterministic calendar/clock calculations (e.g. hour, day of week, weekend).
- HISTORICAL_DERIVED: Aggregate statistics computed strictly over prior events (e.g. past open rate).
- SIMULATION_ONLY: Latent variables used solely in synthetic generation, NEVER exposed to models.
"""

from typing import Dict, List, Any

# 1. NOTIFICATION FEATURES (available immediately upon arrival)
NOTIFICATION_FEATURES: Dict[str, Dict[str, str]] = {
    "source_app": {
        "type": "categorical",
        "source": "OBSERVED",
        "description": "Identifier of the application posting the notification (e.g. Slack, WhatsApp)",
    },
    "app_category": {
        "type": "categorical",
        "source": "RULE_DERIVED",
        "description": "Functional domain of the application (e.g. communication, work, social, alert)",
    },
    "notification_category": {
        "type": "categorical",
        "source": "OBSERVED",
        "description": "Content classification label (e.g. direct_message, mention, news, marketing)",
    },
    "text_length": {
        "type": "numeric",
        "source": "OBSERVED",
        "description": "Character count of the notification text summary/preview",
    },
    "hour_of_day": {
        "type": "numeric",
        "source": "RULE_DERIVED",
        "description": "Hour of the day in local time (0 - 23)",
    },
    "day_of_week": {
        "type": "numeric",
        "source": "RULE_DERIVED",
        "description": "Day of week (0 = Monday, 6 = Sunday)",
    },
    "is_weekend": {
        "type": "numeric",
        "source": "RULE_DERIVED",
        "description": "Binary indicator: 1 if Saturday or Sunday, else 0",
    },
}

# 2. CONTEXT FEATURES (device and user state at arrival time)
CONTEXT_FEATURES: Dict[str, Dict[str, str]] = {
    "focus_mode": {
        "type": "categorical",
        "source": "CONTEXT_DERIVED",
        "description": "Active user activity state (e.g. deep_work, meeting, casual_browsing, off_hours)",
    },
    "is_focus_session": {
        "type": "numeric",
        "source": "CONTEXT_DERIVED",
        "description": "Binary flag indicating whether a timed focus block or DND is active (1 or 0)",
    },
    "recent_notification_count_15m": {
        "type": "numeric",
        "source": "CONTEXT_DERIVED",
        "description": "Number of alerts received across all apps in the preceding 15 minutes",
    },
    "minutes_since_last_notification": {
        "type": "numeric",
        "source": "CONTEXT_DERIVED",
        "description": "Time elapsed since the immediately preceding notification (capped at 1440 min)",
    },
    "notification_load_1h": {
        "type": "numeric",
        "source": "CONTEXT_DERIVED",
        "description": "Total notification volume received in the trailing 60 minutes",
    },
}

# 3. HISTORICAL BEHAVIORAL FEATURES (computed strictly on prior events, avoiding future leakage)
HISTORICAL_FEATURES: Dict[str, Dict[str, str]] = {
    "app_historical_open_rate": {
        "type": "numeric",
        "source": "HISTORICAL_DERIVED",
        "description": "Proportion of prior notifications from this specific app that the user opened quickly (<5m)",
    },
    "app_historical_ignore_rate": {
        "type": "numeric",
        "source": "HISTORICAL_DERIVED",
        "description": "Proportion of prior notifications from this app that were ignored or dismissed without action",
    },
    "user_historical_open_rate": {
        "type": "numeric",
        "source": "HISTORICAL_DERIVED",
        "description": "Global historical open rate for this user across all applications prior to this event",
    },
    "recent_allow_rate_1h": {
        "type": "numeric",
        "source": "HISTORICAL_DERIVED",
        "description": "Fraction of interventions in the past hour where the alert was allowed immediately",
    },
    "recent_suppress_rate_1h": {
        "type": "numeric",
        "source": "HISTORICAL_DERIVED",
        "description": "Fraction of interventions in the past hour where alerts were suppressed",
    },
}

# 4. COLD-START DEFAULTS FOR NEW USERS (Neutral, uninformative priors)
COLD_START_DEFAULTS: Dict[str, Any] = {
    "app_historical_open_rate": 0.5,    # Neutral uninformative prior
    "app_historical_ignore_rate": 0.3,  # Neutral prior
    "user_historical_open_rate": 0.5,   # Neutral prior
    "recent_allow_rate_1h": 0.5,
    "recent_suppress_rate_1h": 0.2,
    "recent_notification_count_15m": 0,
    "minutes_since_last_notification": 120.0, # 2 hours default gap
    "notification_load_1h": 0,
    "is_focus_session": 0,
    "focus_mode": "casual_browsing",
}

# 5. MODEL-READY FEATURE LISTS
CATEGORICAL_FEATURE_NAMES: List[str] = [
    "source_app",
    "app_category",
    "notification_category",
    "focus_mode",
]

NUMERIC_FEATURE_NAMES: List[str] = [
    "text_length",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_focus_session",
    "recent_notification_count_15m",
    "minutes_since_last_notification",
    "notification_load_1h",
    "app_historical_open_rate",
    "app_historical_ignore_rate",
    "user_historical_open_rate",
    "recent_allow_rate_1h",
    "recent_suppress_rate_1h",
]

ALL_FEATURE_NAMES: List[str] = CATEGORICAL_FEATURE_NAMES + NUMERIC_FEATURE_NAMES

# 6. TARGET VARIABLES SPECIFICATION
TARGET_BINARY: str = "opened_within_5min"  # 1 = opened within 5 minutes, 0 = ignored/delayed
TARGET_MULTICLASS: str = "outcome_label"   # opened_quickly, opened_later, ignored

METADATA_COLUMNS: List[str] = [
    "event_id",
    "user_id",
    "timestamp",
    "decision_action",  # intervention applied: allow, suppress, defer
]

SIMULATION_ONLY_COLUMNS: List[str] = [
    "user_responsiveness_trait",
    "simulated_distraction_score",
    "true_latent_urgency",
]
