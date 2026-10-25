from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationPredictionRequest(BaseModel):
    """Payload representing a notification event and its context at arrival time."""
    source_app: str = Field(..., description="Application name (e.g. Slack, WhatsApp)")
    app_category: str = Field(..., description="Category (e.g. communication, work, social)")
    notification_category: str = Field(..., description="Notification subtype (e.g. direct_message, mention)")
    text_length: int = Field(default=65, ge=1, le=5000, description="Character count of notification text")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of arrival in 24-hour format")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Mon, 6=Sun)")
    is_weekend: int = Field(default=0, ge=0, le=1, description="1 if weekend else 0")
    focus_mode: str = Field(default="casual_browsing", description="Active focus state")
    is_focus_session: int = Field(default=0, ge=0, le=1, description="1 if timed focus block active else 0")
    recent_notification_count_15m: Optional[int] = Field(default=0, ge=0, description="Alerts in last 15m")
    minutes_since_last_notification: Optional[float] = Field(default=120.0, ge=0.0, description="Gap since last alert")
    notification_load_1h: Optional[int] = Field(default=0, ge=0, description="Alerts in last 60m")
    app_historical_open_rate: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Prior app open rate")
    app_historical_ignore_rate: Optional[float] = Field(default=0.3, ge=0.0, le=1.0, description="Prior app ignore rate")
    user_historical_open_rate: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Global user open rate")
    recent_allow_rate_1h: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Recent allow fraction")
    recent_suppress_rate_1h: Optional[float] = Field(default=0.2, ge=0.0, le=1.0, description="Recent suppress fraction")

    model_config = ConfigDict(extra="ignore")


class NotificationPredictionResponse(BaseModel):
    """Structured response detailing the baseline model prediction and limitations."""
    predicted_class: int = Field(..., description="Predicted binary target: 1 = opened_within_5min, 0 = delayed/ignored")
    predicted_label: str = Field(..., description="Descriptive label (opened_within_5min or not_opened_quickly)")
    probability_opened_quickly: float = Field(..., description="Model estimated probability of quick opening")
    model_version: str = Field(..., description="Identifier of the serving model artifact")
    data_provenance: str = Field(..., description="Indicates synthetic vs real data training provenance")
    evaluation_basis: str = Field(..., description="Summary of split strategy used during training evaluation")
    limitations_disclaimer: str = Field(..., description="Mandatory qualification of model boundaries")

    model_config = ConfigDict(from_attributes=True)


class ModelStatusResponse(BaseModel):
    """Status metadata for the loaded baseline model."""
    is_model_loaded: bool = Field(..., description="Whether a trained model artifact is active in memory")
    model_name: Optional[str] = Field(default=None, description="Classifier architecture")
    model_version: Optional[str] = Field(default=None, description="Artifact release version")
    target: Optional[str] = Field(default=None, description="Target variable definition")
    data_provenance: str = Field(..., description="Synthetic development data disclaimer")
    features_count: Optional[int] = Field(default=None, description="Count of input features")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Evaluation metrics on validation split")
    trained_at: Optional[str] = Field(default=None, description="Timestamp of training execution")

    model_config = ConfigDict(from_attributes=True)
