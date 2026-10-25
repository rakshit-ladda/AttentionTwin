import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.event import NotificationEvent, NotificationDecision

# Isolated in-memory database for testing
TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@sa_event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create a pristine isolated test database for each test function."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# --- Tests for Notification Event Lifecycle ---

def test_create_and_retrieve_event():
    """Test creating a synthetic notification event and retrieving it by ID."""
    synthetic_payload = {
        "text": "[SYNTHETIC] Team standup meeting starting in 5 minutes",
        "source_app": "Slack",
        "category": "communication",
        "context_data": {
            "current_focus_mode": "deep_work",
            "active_window": "VS Code",
            "urgency_level": "medium",
        },
    }

    # Create event
    res = client.post("/api/events", json=synthetic_payload)
    assert res.status_code == 201
    created_data = res.json()
    event_id = created_data["id"]
    assert created_data["text"] == synthetic_payload["text"]
    assert created_data["source_app"] == "Slack"
    assert created_data["category"] == "communication"
    assert created_data["context_data"]["current_focus_mode"] == "deep_work"
    assert "timestamp" in created_data

    # Retrieve event
    get_res = client.get(f"/api/events/{event_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == event_id
    assert get_res.json()["text"] == synthetic_payload["text"]


def test_list_events_with_filters_and_pagination():
    """Test listing synthetic events with category filters and pagination."""
    # Seed 3 synthetic events
    client.post("/api/events", json={
        "text": "[SYNTHETIC] Server alert CPU spike",
        "source_app": "Grafana",
        "category": "system_alert",
    })
    client.post("/api/events", json={
        "text": "[SYNTHETIC] Lunch invitation",
        "source_app": "WhatsApp",
        "category": "social",
    })
    client.post("/api/events", json={
        "text": "[SYNTHETIC] CI pipeline passed",
        "source_app": "GitHub",
        "category": "system_alert",
    })

    # List all
    all_res = client.get("/api/events")
    assert all_res.status_code == 200
    events = all_res.json()
    assert len(events) == 3

    # Filter by category
    filter_res = client.get("/api/events?category=system_alert")
    assert filter_res.status_code == 200
    filtered = filter_res.json()
    assert len(filtered) == 2
    assert all(e["category"] == "system_alert" for e in filtered)

    # Filter with pagination limit
    limit_res = client.get("/api/events?limit=1&offset=0")
    assert limit_res.status_code == 200
    assert len(limit_res.json()) == 1


def test_record_decisions_valid_and_invalid():
    """Test recording decisions across allowed actions and validating invalid actions."""
    # Create synthetic parent event
    event_res = client.post("/api/events", json={
        "text": "[SYNTHETIC] Urgent bug assigned to you",
        "source_app": "Jira",
        "category": "work",
    })
    event_id = event_res.json()["id"]

    # Record valid action: 'defer'
    defer_res = client.post(f"/api/events/{event_id}/decisions", json={
        "action": "defer",
        "reason": "User is currently in deep focus session",
    })
    assert defer_res.status_code == 201
    assert defer_res.json()["action"] == "defer"
    assert defer_res.json()["event_id"] == event_id

    # Record valid action with mixed case: 'ALLOW'
    allow_res = client.post(f"/api/events/{event_id}/decisions", json={
        "action": "ALLOW",
        "reason": "Critical production priority",
    })
    assert allow_res.status_code == 201
    assert allow_res.json()["action"] == "allow"

    # Attempt invalid action: 'block_forever' -> expect 422 validation failure
    invalid_res = client.post(f"/api/events/{event_id}/decisions", json={
        "action": "block_forever",
        "reason": "Non-standard action",
    })
    assert invalid_res.status_code == 422


def test_record_observed_outcome():
    """Test recording empirical observed outcomes without fabricated data."""
    event_res = client.post("/api/events", json={
        "text": "[SYNTHETIC] Code review requested",
        "source_app": "GitHub",
        "category": "work",
    })
    event_id = event_res.json()["id"]

    outcome_payload = {
        "outcome_type": "delayed_response",
        "interaction_measurements": {
            "response_latency_seconds": 184.5,
            "session_interrupted": True,
        },
    }

    res = client.post(f"/api/events/{event_id}/outcomes", json=outcome_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["outcome_type"] == "delayed_response"
    assert data["event_id"] == event_id
    assert data["interaction_measurements"]["response_latency_seconds"] == 184.5


def test_record_counterfactual_prediction():
    """Test recording counterfactual predictions isolated from empirical observations."""
    event_res = client.post("/api/events", json={
        "text": "[SYNTHETIC] Marketing newsletter notification",
        "source_app": "Gmail",
        "category": "marketing",
    })
    event_id = event_res.json()["id"]

    prediction_payload = {
        "proposed_action": "suppress",
        "predicted_outcome": {
            "predicted_distraction_score": 0.05,
            "information_loss_penalty": 0.02,
        },
        "model_version": "scikit_baseline_v0.1",
    }

    pred_res = client.post(f"/api/events/{event_id}/predictions", json=prediction_payload)
    assert pred_res.status_code == 201
    data = pred_res.json()
    assert data["proposed_action"] == "suppress"
    assert data["model_version"] == "scikit_baseline_v0.1"
    assert data["predicted_outcome"]["predicted_distraction_score"] == 0.05


def test_record_user_feedback_and_validation():
    """Test recording user feedback and enforcing reference validation."""
    event_res = client.post("/api/events", json={
        "text": "[SYNTHETIC] Promotional sale push",
        "source_app": "ShoppingApp",
        "category": "promotions",
    })
    event_id = event_res.json()["id"]

    dec_res = client.post(f"/api/events/{event_id}/decisions", json={
        "action": "suppress",
        "reason": "Low priority promo during work hours",
    })
    decision_id = dec_res.json()["id"]

    # Valid feedback linked to decision
    fb_res = client.post(f"/api/events/{event_id}/feedback", json={
        "decision_id": decision_id,
        "feedback_rating": 5,
        "feedback_label": "helpful",
        "comment": "Good decision, that would have derailed my focus.",
    })
    assert fb_res.status_code == 201
    fb_data = fb_res.json()
    assert fb_data["feedback_rating"] == 5
    assert fb_data["decision_id"] == decision_id

    # Invalid decision ID belonging to non-existent ID
    bad_dec_res = client.post(f"/api/events/{event_id}/feedback", json={
        "decision_id": 99999,
        "feedback_rating": 3,
    })
    assert bad_dec_res.status_code == 400


def test_event_history_aggregation():
    """Test retrieving complete history (decisions, outcomes, predictions, feedback)."""
    # 1. Create event
    event_res = client.post("/api/events", json={
        "text": "[SYNTHETIC] Direct message from manager",
        "source_app": "Slack",
        "category": "communication",
    })
    event_id = event_res.json()["id"]

    # 2. Record decision
    client.post(f"/api/events/{event_id}/decisions", json={
        "action": "allow",
        "reason": "Direct message from key collaborator",
    })

    # 3. Record observed outcome
    client.post(f"/api/events/{event_id}/outcomes", json={
        "outcome_type": "responded_immediately",
        "interaction_measurements": {"response_latency_seconds": 12.0},
    })

    # 4. Record counterfactual prediction
    client.post(f"/api/events/{event_id}/predictions", json={
        "proposed_action": "defer",
        "predicted_outcome": {"predicted_distraction_reduction": 0.4},
        "model_version": "baseline_v0.1",
    })

    # 5. Record feedback
    client.post(f"/api/events/{event_id}/feedback", json={
        "feedback_rating": 4,
        "comment": "Allowing was the right call.",
    })

    # 6. Retrieve full history
    hist_res = client.get(f"/api/events/{event_id}/history")
    assert hist_res.status_code == 200
    hist = hist_res.json()

    assert hist["event"]["id"] == event_id
    assert len(hist["decisions"]) == 1
    assert hist["decisions"][0]["action"] == "allow"
    assert len(hist["observed_outcomes"]) == 1
    assert hist["observed_outcomes"][0]["outcome_type"] == "responded_immediately"
    assert len(hist["counterfactual_predictions"]) == 1
    assert hist["counterfactual_predictions"][0]["proposed_action"] == "defer"
    assert len(hist["feedback"]) == 1
    assert hist["feedback"][0]["feedback_rating"] == 4


def test_nonexistent_event_ids_return_404():
    """Ensure operations on non-existent event IDs return 404 Not Found."""
    non_existent = 999999
    assert client.get(f"/api/events/{non_existent}").status_code == 404
    assert client.get(f"/api/events/{non_existent}/history").status_code == 404
    assert client.post(f"/api/events/{non_existent}/decisions", json={"action": "allow"}).status_code == 404
    assert client.post(f"/api/events/{non_existent}/outcomes", json={"outcome_type": "ignored"}).status_code == 404
    assert client.post(f"/api/events/{non_existent}/predictions", json={
        "proposed_action": "allow",
        "predicted_outcome": {},
        "model_version": "test",
    }).status_code == 404
    assert client.post(f"/api/events/{non_existent}/feedback", json={"feedback_rating": 5}).status_code == 404


def test_referential_integrity_and_cascade_delete():
    """Test foreign key enforcement and cascading deletion using an ORM session."""
    db = TestingSessionLocal()
    try:
        # Create event
        event = NotificationEvent(
            text="[SYNTHETIC] Integrity check event",
            source_app="TestApp",
            category="test",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.id

        # Add decision linked to event
        decision = NotificationDecision(
            event_id=event_id,
            action="allow",
        )
        db.add(decision)
        db.commit()

        # Enforce foreign key violation when inserting with invalid event_id
        with pytest.raises(IntegrityError):
            bad_decision = NotificationDecision(
                event_id=888888,
                action="suppress",
            )
            db.add(bad_decision)
            db.commit()
        db.rollback()

        # Test cascading deletion: deleting the event should delete child records
        db.delete(event)
        db.commit()

        # Decision should now be gone
        remaining_decisions = db.query(NotificationDecision).filter_by(event_id=event_id).all()
        assert len(remaining_decisions) == 0
    finally:
        db.close()
