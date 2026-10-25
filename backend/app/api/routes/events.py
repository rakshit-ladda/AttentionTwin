from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.event import (
    NotificationEvent,
    NotificationDecision,
    ObservedOutcome,
    CounterfactualPrediction,
    UserFeedback,
    utc_now,
)
from app.schemas.event import (
    NotificationEventCreate,
    NotificationEventResponse,
    NotificationDecisionCreate,
    NotificationDecisionResponse,
    ObservedOutcomeCreate,
    ObservedOutcomeResponse,
    CounterfactualPredictionCreate,
    CounterfactualPredictionResponse,
    UserFeedbackCreate,
    UserFeedbackResponse,
    EventHistoryResponse,
)

router = APIRouter()


def _get_event_or_404(event_id: int, db: Session) -> NotificationEvent:
    event = db.get(NotificationEvent, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification event with ID {event_id} not found",
        )
    return event


@router.post(
    "/events",
    response_model=NotificationEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification event",
)
def create_event(
    event_in: NotificationEventCreate,
    db: Session = Depends(get_db),
):
    """Record an incoming notification event with contextual parameters."""
    event = NotificationEvent(
        text=event_in.text,
        source_app=event_in.source_app,
        category=event_in.category,
        timestamp=event_in.timestamp or utc_now(),
        context_data=event_in.context_data,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get(
    "/events",
    response_model=List[NotificationEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List notification events",
)
def list_events(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset index for pagination"),
    source_app: Optional[str] = Query(None, description="Filter by source app"),
    category: Optional[str] = Query(None, description="Filter by notification category"),
    db: Session = Depends(get_db),
):
    """List notification events in reverse chronological order with optional filtering."""
    stmt = select(NotificationEvent)
    if source_app:
        stmt = stmt.where(NotificationEvent.source_app == source_app)
    if category:
        stmt = stmt.where(NotificationEvent.category == category)
    stmt = stmt.order_by(NotificationEvent.timestamp.desc()).offset(offset).limit(limit)
    return db.scalars(stmt).all()


@router.get(
    "/events/{event_id}",
    response_model=NotificationEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a notification event",
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details of a single notification event by its ID."""
    return _get_event_or_404(event_id, db)


@router.post(
    "/events/{event_id}/decisions",
    response_model=NotificationDecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a notification decision",
)
def record_decision(
    event_id: int,
    decision_in: NotificationDecisionCreate,
    db: Session = Depends(get_db),
):
    """Record the action taken (allow, suppress, defer) and reasoning for a notification."""
    _get_event_or_404(event_id, db)
    decision = NotificationDecision(
        event_id=event_id,
        action=decision_in.action,
        reason=decision_in.reason,
        timestamp=decision_in.timestamp or utc_now(),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.post(
    "/events/{event_id}/outcomes",
    response_model=ObservedOutcomeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an observed outcome",
)
def record_observed_outcome(
    event_id: int,
    outcome_in: ObservedOutcomeCreate,
    db: Session = Depends(get_db),
):
    """Record empirical outcome of what actually happened after a notification."""
    _get_event_or_404(event_id, db)
    outcome = ObservedOutcome(
        event_id=event_id,
        outcome_type=outcome_in.outcome_type,
        interaction_measurements=outcome_in.interaction_measurements,
        timestamp=outcome_in.timestamp or utc_now(),
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


@router.post(
    "/events/{event_id}/predictions",
    response_model=CounterfactualPredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a counterfactual prediction",
)
def record_counterfactual_prediction(
    event_id: int,
    prediction_in: CounterfactualPredictionCreate,
    db: Session = Depends(get_db),
):
    """Store estimated outcome for alternative candidate actions without fabricating results."""
    _get_event_or_404(event_id, db)
    prediction = CounterfactualPrediction(
        event_id=event_id,
        proposed_action=prediction_in.proposed_action,
        predicted_outcome=prediction_in.predicted_outcome,
        model_version=prediction_in.model_version,
        timestamp=prediction_in.timestamp or utc_now(),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.post(
    "/events/{event_id}/feedback",
    response_model=UserFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record user feedback",
)
def record_user_feedback(
    event_id: int,
    feedback_in: UserFeedbackCreate,
    db: Session = Depends(get_db),
):
    """Record optional user feedback for an event, decision, or prediction."""
    _get_event_or_404(event_id, db)

    # Validate foreign references if supplied
    if feedback_in.decision_id is not None:
        decision = db.get(NotificationDecision, feedback_in.decision_id)
        if not decision or decision.event_id != event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Decision ID {feedback_in.decision_id} does not belong to event {event_id}",
            )

    if feedback_in.prediction_id is not None:
        prediction = db.get(CounterfactualPrediction, feedback_in.prediction_id)
        if not prediction or prediction.event_id != event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prediction ID {feedback_in.prediction_id} does not belong to event {event_id}",
            )

    feedback = UserFeedback(
        event_id=event_id,
        decision_id=feedback_in.decision_id,
        prediction_id=feedback_in.prediction_id,
        feedback_rating=feedback_in.feedback_rating,
        feedback_label=feedback_in.feedback_label,
        comment=feedback_in.comment,
        timestamp=feedback_in.timestamp or utc_now(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get(
    "/events/{event_id}/history",
    response_model=EventHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve complete event history",
)
def get_event_history(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full audit history for an event including decisions, outcomes, predictions, and feedback."""
    event = _get_event_or_404(event_id, db)
    return EventHistoryResponse(
        event=NotificationEventResponse.model_validate(event),
        decisions=[NotificationDecisionResponse.model_validate(d) for d in event.decisions],
        observed_outcomes=[ObservedOutcomeResponse.model_validate(o) for o in event.observed_outcomes],
        counterfactual_predictions=[
            CounterfactualPredictionResponse.model_validate(p) for p in event.counterfactual_predictions
        ],
        feedback=[UserFeedbackResponse.model_validate(f) for f in event.feedback],
    )
