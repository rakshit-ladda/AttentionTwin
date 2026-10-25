"""
AttentionTwin Action-Aware Counterfactual Engine
================================================
Compares candidate intervention actions (allow, defer, suppress) for the SAME notification context.
Guarantees that all pre-decision contextual attributes remain strictly identical while varying
only the intervention action and its associated delivery policy.
"""

import os
import json
from typing import Dict, Any, List, Optional
import pandas as pd
import joblib

from app.ml.action_aware_trainer import ACTION_AWARE_ALL_FEATURES
from app.ml.feature_schema import COLD_START_DEFAULTS
from app.schemas.counterfactual import (
    CounterfactualCompareRequest,
    CounterfactualCompareResponse,
    CounterfactualScenarioResult,
)

CANDIDATE_ACTIONS: List[str] = ["allow", "defer", "suppress"]

ACTION_POLICY_EXPLANATIONS = {
    "allow": "Immediate delivery upon arrival; notification interrupts current task immediately. High interruption cost during active focus blocks.",
    "defer": "Delivery postponed to next scheduled break window; immediate distraction is avoided while context is preserved for later review.",
    "suppress": "Alert silenced and archived directly to silent digest; zero immediate interruption, reviewed only asynchronously by user.",
}


def check_support_warning(req_dict: Dict[str, Any], action: str) -> Optional[str]:
    """Check if the action/context combination has low representation in baseline training data."""
    app_cat = req_dict.get("app_category", "")
    notif_cat = req_dict.get("notification_category", "")
    focus_mode = req_dict.get("focus_mode", "")

    if app_cat == "system_alert" and action == "suppress":
        return "Suppression of critical system alerts has very low frequency (<1%) in training data; simulated outcome has elevated epistemic uncertainty."
    if notif_cat == "direct_message" and action == "suppress":
        return "Suppression of personal direct messages is rare in baseline routing heuristics; outcome estimates may reflect sparse sample support."
    if focus_mode == "deep_work" and action == "allow" and app_cat in ("marketing", "social"):
        return "Immediate delivery of marketing/social alerts during deep work is infrequently observed in historical routing heuristics."
    return None


# Empirical and cognitive estimates based on task-switching research (e.g. Mark et al., UC Irvine)
APP_CATEGORY_BROWSING_MINUTES: Dict[str, float] = {
    "social": 14.0,
    "entertainment": 16.0,
    "marketing": 6.0,
    "communication": 4.5,
    "work": 5.0,
    "productivity": 3.0,
    "system": 2.5,
    "system_alert": 2.5,
    "finance": 4.0,
    "health": 3.0,
}

FOCUS_MODE_RESUMPTION_DELAY_MINUTES: Dict[str, float] = {
    "deep_work": 12.0,      # High cognitive reorientation cost to re-enter coding flow
    "meeting": 5.0,         # Moderate reorientation cost
    "casual_browsing": 2.0,  # Low switching cost
    "off_hours": 1.0,        # Minimal penalty
    "break": 0.5,
}


class CounterfactualEngine:
    """Service orchestrating counterfactual scenario simulation across candidate intervention actions."""

    def __init__(self, artifacts_dir: str = "backend/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.model = None
        self.metadata = None
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load the action-aware model and its metadata."""
        model_path = os.path.join(self.artifacts_dir, "action_aware_model.joblib")
        meta_path = os.path.join(self.artifacts_dir, "action_aware_metadata.json")

        if os.path.exists(model_path) and os.path.exists(meta_path):
            try:
                self.model = joblib.load(model_path)
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                return True
            except Exception:
                self.model = None
                self.metadata = None
                return False
        return False

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.metadata is not None

    def compare_actions(self, request: CounterfactualCompareRequest) -> CounterfactualCompareResponse:
        """
        Evaluate candidate actions for the exact same pre-decision notification context.
        Predicts open probabilities and estimates browsing time, resumption delay, and total disruption.
        """
        if not self.is_ready:
            raise RuntimeError("Action-aware model artifact is not loaded or has not been trained yet.")

        base_data = request.model_dump()

        # Apply cold-start defaults for any omitted numeric features
        for feat in ACTION_AWARE_ALL_FEATURES:
            if feat not in base_data or base_data[feat] is None:
                if feat != "proposed_action":
                    base_data[feat] = COLD_START_DEFAULTS.get(feat, 0.0)

        # Construct 3 rows: pre-decision features are strictly invariant, only proposed_action varies
        scenario_rows = []
        for action in CANDIDATE_ACTIONS:
            row = dict(base_data)
            row["proposed_action"] = action
            scenario_rows.append(row)

        scenarios_df = pd.DataFrame(scenario_rows)[ACTION_AWARE_ALL_FEATURES]

        # Batch predict classes and probabilities via trained action-aware model
        preds = self.model.predict(scenarios_df)
        probs = self.model.predict_proba(scenarios_df)[:, 1]

        # Context evaluation
        is_focus = (
            base_data.get("is_focus_session", 0) == 1
            or base_data.get("focus_mode") in ("deep_work", "meeting")
        )
        app_cat = str(base_data.get("app_category", "")).lower()
        notif_cat = str(base_data.get("notification_category", "")).lower()
        focus_mode = str(base_data.get("focus_mode", "casual_browsing"))

        # Base cognitive parameters for this scenario
        base_browsing = APP_CATEGORY_BROWSING_MINUTES.get(app_cat, 5.0)
        base_resumption = FOCUS_MODE_RESUMPTION_DELAY_MINUTES.get(focus_mode, 2.0)
        if base_data.get("is_focus_session") == 1:
            base_resumption = max(base_resumption, 10.0)

        # Attention preservation recommendation policy
        if app_cat in ("system", "system_alert") or notif_cat in ("cpu_spike", "service_outage", "build_failure"):
            recommended_action = "allow"
            recommendation_rationale = (
                "Critical system infrastructure alert requires immediate developer attention; "
                "operational risk outweighs task interruption cost."
            )
        elif app_cat == "marketing":
            recommended_action = "suppress"
            recommendation_rationale = (
                "Low-value promotional alert during work hours. Silencing to digest mode "
                "eliminates attention fragmentation with zero loss of valuable context."
            )
        elif is_focus and app_cat in ("social", "entertainment", "marketing"):
            recommended_action = "defer"
            recommendation_rationale = (
                f"User is actively in a focus block ({focus_mode}). "
                "Social notifications impose substantial task disruption (~15-25 min). "
                "Postponing delivery to the scheduled break window (+25m) protects coding flow."
            )
        elif is_focus:
            recommended_action = "defer"
            recommendation_rationale = (
                f"Active focus session detected ({focus_mode}). Deferring notification to the upcoming "
                "break window avoids immediate context switching while preserving it for prompt review."
            )
        else:
            recommended_action = "allow"
            recommendation_rationale = (
                "User is in a flexible or off-hours context. Immediate delivery allows timely interaction "
                "with manageable task disruption."
            )

        results: List[CounterfactualScenarioResult] = []
        for idx, action in enumerate(CANDIDATE_ACTIONS):
            pred_class = int(preds[idx])
            prob_opened = float(probs[idx])
            label = "opened_within_5min" if pred_class == 1 else "not_opened_quickly"

            if action == "allow":
                # If allowed, browsing and resumption delay are incurred proportional to open probability
                est_browsing = round(prob_opened * base_browsing, 1)
                est_resumption = round(prob_opened * base_resumption, 1)
                est_interruption = round(est_browsing + est_resumption, 1)
                deferred_mins = None
                risk = "high" if is_focus and est_interruption >= 10.0 else ("medium" if prob_opened > 0.4 else "low")
            elif action == "defer":
                # If deferred to break window: immediate interruption is eliminated
                est_browsing = 0.0
                est_resumption = 0.0
                est_interruption = 0.0
                deferred_mins = 25  # Postponed to next break window at +25 minutes
                risk = "low"
            else:  # suppress
                # Silenced to silent digest: zero immediate loss
                est_browsing = 0.0
                est_resumption = 0.0
                est_interruption = 0.0
                deferred_mins = None
                risk = "negligible"

            warning = check_support_warning(base_data, action)

            results.append(
                CounterfactualScenarioResult(
                    proposed_action=action,
                    predicted_class=pred_class,
                    predicted_label=label,
                    probability_opened_quickly=round(prob_opened, 4),
                    expected_interruption_risk=risk,
                    timing_explanation=ACTION_POLICY_EXPLANATIONS[action],
                    support_warning=warning,
                    estimated_interruption_minutes=est_interruption,
                    estimated_browsing_minutes=est_browsing,
                    estimated_resumption_delay_minutes=est_resumption,
                    deferred_delivery_minutes=deferred_mins,
                    is_recommended=(action == recommended_action),
                )
            )

        # Build comparative narrative
        allow_res = next(r for r in results if r.proposed_action == "allow")
        defer_res = next(r for r in results if r.proposed_action == "defer")
        suppress_res = next(r for r in results if r.proposed_action == "suppress")

        narrative = (
            f"Holding context invariant: 'ALLOW' predicts a {allow_res.probability_opened_quickly * 100:.1f}% open probability, "
            f"incurring ~{allow_res.estimated_interruption_minutes}m total task disruption ({allow_res.estimated_browsing_minutes}m browsing "
            f"+ {allow_res.estimated_resumption_delay_minutes}m resumption delay). 'DEFER' postpones delivery to the scheduled break window "
            f"(+{defer_res.deferred_delivery_minutes}m), eliminating immediate task disruption (0.0m loss). 'SUPPRESS' archives to silent digest mode (0.0m loss)."
        )

        return CounterfactualCompareResponse(
            notification_summary={
                "source_app": base_data["source_app"],
                "app_category": base_data["app_category"],
                "notification_category": base_data["notification_category"],
                "focus_mode": base_data["focus_mode"],
                "is_focus_session": base_data["is_focus_session"],
                "hour_of_day": base_data["hour_of_day"],
            },
            scenarios=results,
            relative_comparison_summary=narrative,
            recommended_action=recommended_action,
            recommendation_rationale=recommendation_rationale,
            model_version=self.metadata.get("model_version", "action_aware_v1.0.0"),
            data_provenance=self.metadata.get("data_provenance", "SYNTHETIC_DEVELOPMENT_DATA"),
            limitations_disclaimer=(
                "The comparison is exploratory and trained on synthetic development data. "
                "It must not be interpreted as a proven causal effect, verified attention prediction, "
                "or guaranteed best action. No automatic device or notification suppression is performed."
            ),
        )


# Global singleton instance
counterfactual_engine = CounterfactualEngine()
