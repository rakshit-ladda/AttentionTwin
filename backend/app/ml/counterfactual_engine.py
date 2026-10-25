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

        # Batch predict classes and probabilities
        preds = self.model.predict(scenarios_df)
        probs = self.model.predict_proba(scenarios_df)[:, 1]

        results: List[CounterfactualScenarioResult] = []
        for idx, action in enumerate(CANDIDATE_ACTIONS):
            pred_class = int(preds[idx])
            prob_opened = float(probs[idx])
            label = "opened_within_5min" if pred_class == 1 else "not_opened_quickly"

            # Determine qualitative risk
            is_focus = base_data.get("is_focus_session", 0) == 1 or base_data.get("focus_mode") in ("deep_work", "meeting")
            if action == "allow":
                risk = "high" if is_focus else ("medium" if prob_opened > 0.5 else "low")
            elif action == "defer":
                risk = "low"
            else:  # suppress
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
                )
            )

        # Build comparative narrative
        allow_prob = next(r.probability_opened_quickly for r in results if r.proposed_action == "allow")
        defer_prob = next(r.probability_opened_quickly for r in results if r.proposed_action == "defer")
        suppress_prob = next(r.probability_opened_quickly for r in results if r.proposed_action == "suppress")

        narrative = (
            f"Holding context invariant: 'ALLOW' predicts a {allow_prob * 100:.1f}% likelihood of prompt interaction "
            f"with immediate task disruption risk. 'DEFER' postpones delivery to the next break window, lowering prompt "
            f"interaction to {defer_prob * 100:.1f}%. 'SUPPRESS' archives the alert to digest mode with {suppress_prob * 100:.1f}% "
            f"prompt interaction likelihood, eliminating immediate attention fragmentation."
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
