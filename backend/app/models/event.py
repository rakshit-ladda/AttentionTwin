from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationEvent(Base):
    """Core notification event representing an incoming alert and its context."""
    __tablename__ = "notification_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_app: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    decisions: Mapped[List["NotificationDecision"]] = relationship(
        "NotificationDecision",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="NotificationDecision.timestamp",
    )
    observed_outcomes: Mapped[List["ObservedOutcome"]] = relationship(
        "ObservedOutcome",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="ObservedOutcome.timestamp",
    )
    counterfactual_predictions: Mapped[List["CounterfactualPrediction"]] = relationship(
        "CounterfactualPrediction",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="CounterfactualPrediction.timestamp",
    )
    feedback: Mapped[List["UserFeedback"]] = relationship(
        "UserFeedback",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="UserFeedback.timestamp",
    )


class NotificationDecision(Base):
    """Action chosen/taken for a notification event (allow, suppress, defer)."""
    __tablename__ = "notification_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. allow, suppress, defer
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    event: Mapped["NotificationEvent"] = relationship("NotificationEvent", back_populates="decisions")


class ObservedOutcome(Base):
    """Factual, empirical outcome of what actually happened after a notification."""
    __tablename__ = "observed_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    outcome_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    interaction_measurements: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    event: Mapped["NotificationEvent"] = relationship("NotificationEvent", back_populates="observed_outcomes")


class CounterfactualPrediction(Base):
    """Estimated outcome for alternative actions under the identical event context."""
    __tablename__ = "counterfactual_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposed_action: Mapped[str] = mapped_column(String(50), nullable=False)  # allow, suppress, defer
    predicted_outcome: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    event: Mapped["NotificationEvent"] = relationship(
        "NotificationEvent",
        back_populates="counterfactual_predictions",
    )


class UserFeedback(Base):
    """User subjective feedback on notification, decision, or prediction."""
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notification_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("notification_decisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    prediction_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("counterfactual_predictions.id", ondelete="SET NULL"),
        nullable=True,
    )
    feedback_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g., 1 to 5
    feedback_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    event: Mapped["NotificationEvent"] = relationship("NotificationEvent", back_populates="feedback")
