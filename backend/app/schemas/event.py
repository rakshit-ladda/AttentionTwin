from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_ACTIONS = {"allow", "suppress", "defer"}


class NotificationEventBase(BaseModel):
    text: str = Field(..., min_length=1, description="Notification body or summary")
    source_app: str = Field(..., min_length=1, max_length=100, description="Application origin (e.g. Slack, Email)")
    category: str = Field(..., min_length=1, max_length=100, description="Category (e.g. communication, alert, work)")
    context_data: Optional[Dict[str, Any]] = Field(default=None, description="Contextual telemetry if available")


class NotificationEventCreate(NotificationEventBase):
    timestamp: Optional[datetime] = Field(default=None, description="Event occurrence timestamp, defaults to now")


class NotificationEventResponse(NotificationEventBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationDecisionBase(BaseModel):
    action: str = Field(..., description="Action taken: allow, suppress, or defer")
    reason: Optional[str] = Field(default=None, description="Explanation or rule rationale")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        clean_action = v.strip().lower()
        if clean_action not in ALLOWED_ACTIONS:
            raise ValueError(f"Action must be one of {sorted(ALLOWED_ACTIONS)}, received: {v}")
        return clean_action


class NotificationDecisionCreate(NotificationDecisionBase):
    timestamp: Optional[datetime] = Field(default=None, description="Decision timestamp, defaults to now")


class NotificationDecisionResponse(NotificationDecisionBase):
    id: int
    event_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ObservedOutcomeBase(BaseModel):
    outcome_type: str = Field(..., min_length=1, max_length=50, description="Observed outcome classification")
    interaction_measurements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Factual interaction measurements without fabricated values",
    )


class ObservedOutcomeCreate(ObservedOutcomeBase):
    timestamp: Optional[datetime] = Field(default=None, description="Outcome timestamp, defaults to now")


class ObservedOutcomeResponse(ObservedOutcomeBase):
    id: int
    event_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class CounterfactualPredictionBase(BaseModel):
    proposed_action: str = Field(..., description="Proposed alternative action: allow, suppress, or defer")
    predicted_outcome: Dict[str, Any] = Field(..., description="Estimated outcome metrics under this action")
    model_version: str = Field(..., min_length=1, max_length=100, description="Model identifier or version")

    @field_validator("proposed_action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        clean_action = v.strip().lower()
        if clean_action not in ALLOWED_ACTIONS:
            raise ValueError(f"Proposed action must be one of {sorted(ALLOWED_ACTIONS)}, received: {v}")
        return clean_action


class CounterfactualPredictionCreate(CounterfactualPredictionBase):
    timestamp: Optional[datetime] = Field(default=None, description="Prediction timestamp, defaults to now")


class CounterfactualPredictionResponse(CounterfactualPredictionBase):
    id: int
    event_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class UserFeedbackBase(BaseModel):
    decision_id: Optional[int] = Field(default=None, description="Optional associated decision ID")
    prediction_id: Optional[int] = Field(default=None, description="Optional associated prediction ID")
    feedback_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating (1-5)")
    feedback_label: Optional[str] = Field(default=None, max_length=50, description="Label or category of feedback")
    comment: Optional[str] = Field(default=None, description="User textual comments")


class UserFeedbackCreate(UserFeedbackBase):
    timestamp: Optional[datetime] = Field(default=None, description="Feedback timestamp, defaults to now")


class UserFeedbackResponse(UserFeedbackBase):
    id: int
    event_id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class EventHistoryResponse(BaseModel):
    event: NotificationEventResponse
    decisions: List[NotificationDecisionResponse]
    observed_outcomes: List[ObservedOutcomeResponse]
    counterfactual_predictions: List[CounterfactualPredictionResponse]
    feedback: List[UserFeedbackResponse]

    model_config = ConfigDict(from_attributes=True)
