from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CounterfactualCompareRequest(BaseModel):
    """Pre-decision notification arrival features holding context constant across actions."""
    source_app: str = Field(..., description="Application name (e.g. Slack, WhatsApp, GitHub)")
    app_category: str = Field(..., description="Application domain (e.g. communication, work, social)")
    notification_category: str = Field(..., description="Notification subtype (e.g. direct_message, cpu_spike)")
    text_length: int = Field(default=65, ge=1, le=5000, description="Character count of notification text")
    hour_of_day: int = Field(..., ge=0, le=23, description="Arrival hour in 24-hour format")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
    is_weekend: int = Field(default=0, ge=0, le=1, description="1 if weekend else 0")
    focus_mode: str = Field(default="casual_browsing", description="Active user cognitive state")
    is_focus_session: int = Field(default=0, ge=0, le=1, description="1 if timed focus session active else 0")
    recent_notification_count_15m: Optional[int] = Field(default=0, ge=0, description="Alerts in last 15m")
    minutes_since_last_notification: Optional[float] = Field(default=120.0, ge=0.0, description="Minutes since last alert")
    notification_load_1h: Optional[int] = Field(default=0, ge=0, description="Alerts in last 60m")
    app_historical_open_rate: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Prior app open rate")
    app_historical_ignore_rate: Optional[float] = Field(default=0.3, ge=0.0, le=1.0, description="Prior app ignore rate")
    user_historical_open_rate: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Global user open rate")
    recent_allow_rate_1h: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Recent allow fraction")
    recent_suppress_rate_1h: Optional[float] = Field(default=0.2, ge=0.0, le=1.0, description="Recent suppress fraction")

    model_config = ConfigDict(extra="ignore")


class CounterfactualScenarioResult(BaseModel):
    """Predicted outcome simulation under a single candidate action."""
    proposed_action: str = Field(..., description="Evaluated action: allow, defer, or suppress")
    predicted_class: int = Field(..., description="Predicted binary outcome: 1 = opened_within_5min, 0 = delayed/ignored")
    predicted_label: str = Field(..., description="Descriptive label (opened_within_5min or not_opened_quickly)")
    probability_opened_quickly: float = Field(..., description="Model estimated probability of quick opening under this action")
    expected_interruption_risk: str = Field(..., description="Qualitative interruption risk (high, medium, low, negligible)")
    timing_explanation: str = Field(..., description="Explanation of action timing and intervention assumption")
    support_warning: Optional[str] = Field(default=None, description="Warning if action/context combo has low data representation")
    
    # Quantitative duration estimates required by Problem Statement
    estimated_interruption_minutes: float = Field(
        default=0.0,
        description="Estimated total task disruption time in minutes (browsing + resumption delay)"
    )
    estimated_browsing_minutes: float = Field(
        default=0.0,
        description="Estimated duration spent actively browsing the notification/app in minutes"
    )
    estimated_resumption_delay_minutes: float = Field(
        default=0.0,
        description="Estimated cognitive latency to resume original task focus in minutes"
    )
    deferred_delivery_minutes: Optional[int] = Field(
        default=None,
        description="Minutes until delivery if deferred to next scheduled focus break"
    )
    is_recommended: bool = Field(
        default=False,
        description="True if this action is recommended by the attention protection policy"
    )

    model_config = ConfigDict(from_attributes=True)


class CounterfactualCompareResponse(BaseModel):
    """Side-by-side comparison of candidate actions for the exact same notification context."""
    notification_summary: Dict[str, Any] = Field(..., description="Pre-decision notification parameters evaluated")
    scenarios: List[CounterfactualScenarioResult] = Field(..., description="Simulated outcomes across candidate actions")
    relative_comparison_summary: str = Field(..., description="Comparative narrative explaining relative trade-offs")
    recommended_action: str = Field(
        default="defer",
        description="Optimal intervention recommendation based on attention preservation policy"
    )
    recommendation_rationale: str = Field(
        default="",
        description="Defensible explanation for the recommended action"
    )
    model_version: str = Field(..., description="Action-aware model version")
    data_provenance: str = Field(..., description="Synthetic development data provenance disclosure")
    limitations_disclaimer: str = Field(..., description="Mandatory qualification of model boundaries")

    model_config = ConfigDict(from_attributes=True)

