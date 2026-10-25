"""
AttentionTwin Synthetic Development Dataset Generator
======================================================
Generates deterministic, synthetic notification streams for development and pipeline evaluation.

DISCLAIMER:
SYNTHETIC DEVELOPMENT DATA — NOT REAL USER DATA.
Assumptions and simulated relationships are designed solely to test data pipelines,
feature transformers, and baseline algorithms without claiming to represent real human psychology.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import numpy as np


APP_CATALOG = [
    {"source_app": "Slack", "app_category": "communication", "base_open_prob": 0.75},
    {"source_app": "Gmail", "app_category": "work", "base_open_prob": 0.55},
    {"source_app": "WhatsApp", "app_category": "communication", "base_open_prob": 0.70},
    {"source_app": "GitHub", "app_category": "work", "base_open_prob": 0.60},
    {"source_app": "Calendar", "app_category": "productivity", "base_open_prob": 0.85},
    {"source_app": "Twitter", "app_category": "social", "base_open_prob": 0.35},
    {"source_app": "Instagram", "app_category": "social", "base_open_prob": 0.40},
    {"source_app": "Datadog", "app_category": "system_alert", "base_open_prob": 0.80},
    {"source_app": "Amazon", "app_category": "marketing", "base_open_prob": 0.20},
    {"source_app": "UberEats", "app_category": "marketing", "base_open_prob": 0.30},
]

NOTIFICATION_CATEGORIES = {
    "communication": ["direct_message", "group_mention", "channel_broadcast"],
    "work": ["pull_request_review", "task_assignment", "project_update"],
    "productivity": ["meeting_reminder", "task_due", "timer_expired"],
    "social": ["new_follower", "friend_post", "trending_topic"],
    "system_alert": ["cpu_spike", "service_outage", "build_failure"],
    "marketing": ["special_discount", "order_status", "promotional_offer"],
}

FOCUS_MODES = ["deep_work", "meeting", "casual_browsing", "off_hours"]


class SyntheticDataGenerator:
    """Deterministic generator for synthetic development notification event logs."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def generate_dataset(
        self,
        num_users: int = 10,
        num_events: int = 8000,
        days: int = 14,
        start_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate synthetic notification events across multiple synthetic users.

        Returns a dictionary containing:
        - metadata: provenance, seed, generator version, disclaimer
        - events: raw synthetic event records with decisions and outcomes
        """
        if start_date is None:
            start_date = datetime(2026, 10, 1, 8, 0, 0, tzinfo=timezone.utc)

        # 1. Define synthetic user archetypes
        user_profiles = {}
        for u_id in range(1, num_users + 1):
            user_key = f"user_{u_id:03d}"
            # Latent traits (SIMULATION ONLY - NOT LEAKED TO MODEL FEATURES)
            user_profiles[user_key] = {
                "user_id": user_key,
                "responsiveness_trait": float(self.rng.uniform(0.3, 0.9)),
                "deep_work_preference": float(self.rng.uniform(0.2, 0.7)),
                "notification_sensitivity": float(self.rng.uniform(0.4, 0.8)),
            }

        events_per_user = num_events // num_users
        all_events: List[Dict[str, Any]] = []

        event_global_id = 1
        total_seconds = days * 24 * 3600

        for user_key, profile in user_profiles.items():
            user_events: List[Dict[str, Any]] = []

            # Generate random timestamps over the time window for this user
            offsets = np.sort(self.rng.uniform(0, total_seconds, size=events_per_user))

            for offset in offsets:
                event_time = start_date + timedelta(seconds=float(offset))
                hour = event_time.hour
                day_of_week = event_time.weekday()
                is_weekend = 1 if day_of_week >= 5 else 0

                # Pick an application based on time of day
                if 9 <= hour <= 17 and not is_weekend:
                    # Workday hours: prioritize work/comm/productivity
                    p_weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.05, 0.03, 0.05, 0.01, 0.01]
                else:
                    # Off-hours: prioritize social/comm/marketing
                    p_weights = [0.08, 0.05, 0.25, 0.04, 0.03, 0.20, 0.20, 0.02, 0.08, 0.05]
                
                app_idx = self.rng.choice(len(APP_CATALOG), p=p_weights)
                app_info = APP_CATALOG[app_idx]
                app_name = app_info["source_app"]
                app_cat = app_info["app_category"]
                
                cat_choices = NOTIFICATION_CATEGORIES[app_cat]
                notif_cat = self.rng.choice(cat_choices)

                # Determine contextual focus mode
                if is_weekend:
                    focus_mode = "off_hours" if (hour < 11 or hour > 21) else "casual_browsing"
                    is_focus = 0
                elif 9 <= hour <= 12 or 14 <= hour <= 17:
                    roll = self.rng.uniform(0, 1)
                    if roll < profile["deep_work_preference"]:
                        focus_mode = "deep_work"
                        is_focus = 1
                    elif roll < profile["deep_work_preference"] + 0.25:
                        focus_mode = "meeting"
                        is_focus = 1
                    else:
                        focus_mode = "casual_browsing"
                        is_focus = 0
                else:
                    focus_mode = "off_hours"
                    is_focus = 0

                text_len = int(self.rng.normal(65, 25))
                text_len = max(10, min(text_len, 250))
                preview_text = f"[{app_name}] {notif_cat.replace('_', ' ').capitalize()} notification payload"

                # Simulated intervention decision: allow, defer, suppress
                # In development, decisions reflect baseline heuristics
                if focus_mode in ("deep_work", "meeting") and app_cat in ("social", "marketing"):
                    decision_action = self.rng.choice(["defer", "suppress"], p=[0.6, 0.4])
                    reason = "Non-essential notification during active focus block"
                elif app_cat == "system_alert" or notif_cat == "direct_message":
                    decision_action = "allow"
                    reason = "High communication or system priority"
                else:
                    decision_action = self.rng.choice(["allow", "defer", "suppress"], p=[0.65, 0.25, 0.10])
                    reason = "Standard heuristic routing"

                # Latent simulation outcome logic (SIMULATION ONLY)
                # Calculates realistic interaction delay and outcome label based on features
                urgency_factor = 0.35 if app_cat in ("system_alert", "productivity") else 0.0
                if notif_cat in ("direct_message", "pull_request_review"):
                    urgency_factor += 0.25

                base_prob = (
                    app_info["base_open_prob"] * 0.4
                    + profile["responsiveness_trait"] * 0.3
                    + urgency_factor
                    - (0.35 if focus_mode in ("deep_work", "meeting") else 0.0)
                    - (0.45 if decision_action == "suppress" else 0.0)
                    - (0.20 if decision_action == "defer" else 0.0)
                )
                open_quick_prob = float(np.clip(base_prob, 0.05, 0.95))

                outcome_roll = self.rng.uniform(0, 1)
                if outcome_roll < open_quick_prob:
                    outcome_label = "opened_quickly"
                    opened_within_5min = 1
                    latency_seconds = float(self.rng.exponential(scale=60.0))
                    latency_seconds = max(5.0, min(latency_seconds, 290.0))
                elif outcome_roll < open_quick_prob + (1.0 - open_quick_prob) * 0.55:
                    outcome_label = "opened_later"
                    opened_within_5min = 0
                    latency_seconds = float(self.rng.uniform(300.0, 7200.0))
                else:
                    outcome_label = "ignored"
                    opened_within_5min = 0
                    latency_seconds = None

                event_record = {
                    "event_id": event_global_id,
                    "user_id": user_key,
                    "timestamp": event_time.isoformat(),
                    "text": preview_text,
                    "source_app": app_name,
                    "app_category": app_cat,
                    "notification_category": notif_cat,
                    "text_length": text_len,
                    "context_data": {
                        "focus_mode": focus_mode,
                        "is_focus_session": is_focus,
                    },
                    "decision": {
                        "action": decision_action,
                        "reason": reason,
                    },
                    "outcome": {
                        "outcome_label": outcome_label,
                        "opened_within_5min": opened_within_5min,
                        "response_latency_seconds": latency_seconds,
                    },
                    # Simulation latent metadata (STRICTLY ISOLATED, NOT EXPOSED TO MODEL)
                    "simulation_metadata": {
                        "user_responsiveness_trait": profile["responsiveness_trait"],
                        "computed_open_quick_prob": open_quick_prob,
                    },
                }

                user_events.append(event_record)
                event_global_id += 1

            all_events.extend(user_events)

        # Sort all events strictly by timestamp
        all_events.sort(key=lambda x: x["timestamp"])

        metadata = {
            "disclaimer": "SYNTHETIC DEVELOPMENT DATA — NOT REAL USER DATA",
            "generator_version": "1.0.0",
            "seed": self.seed,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "num_users": num_users,
            "num_events": len(all_events),
            "date_range": {
                "start": all_events[0]["timestamp"],
                "end": all_events[-1]["timestamp"],
            },
            "simulation_assumptions": [
                "App category and notification category influence likelihood of quick response.",
                "Active deep_work or meeting focus modes decrease immediate response probability.",
                "Intervention action (suppress/defer) delays or prevents prompt interaction.",
                "Synthetic user archetypes have persistent responsiveness traits.",
                "Latent simulation traits are strictly isolated from model features.",
            ],
        }

        return {
            "metadata": metadata,
            "events": all_events,
        }
