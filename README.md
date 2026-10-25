# AttentionTwin — Personal Attention Digital Twin

> **CASCADE 2026 — IIIT Nagpur Hackathon Project**  
> **Phase 1: Project Foundation & Architecture Shell**  
> **Phase 2: Database Persistence & Event APIs**

AttentionTwin is a personal Attention Digital Twin designed to model how an individual responds to notifications and estimate the outcomes of **allowing**, **suppressing**, or **deferring** a notification.

The defining requirement is **counterfactual comparison**: evaluating predicted outcomes under different actions for the **same** notification and user context. The core prediction engine runs locally on scikit-learn without mandatory external cloud APIs or paid dependencies.

---

## Architecture Overview

```
d:\digital_twin\
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions (venv, node_modules, sqlite, secrets)
├── README.md                 # Project documentation and run commands
├── attention_twin.db         # Local SQLite database (auto-created on startup)
├── backend\
│   ├── requirements.txt      # FastAPI, Uvicorn, Pydantic, SQLAlchemy, scikit-learn
│   ├── app\
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI entrypoint, lifespan db init, route registration
│   │   ├── core\
│   │   │   ├── __init__.py
│   │   │   └── config.py     # Pydantic Settings, DATABASE_URL, CORS configuration
│   │   ├── db\
│   │   │   ├── __init__.py
│   │   │   ├── base.py       # SQLAlchemy 2.0 DeclarativeBase
│   │   │   └── session.py    # Engine, SessionLocal, get_db dependency, foreign keys
│   │   ├── models\
│   │   │   ├── __init__.py
│   │   │   └── event.py      # Event, Decision, Outcome, Prediction, Feedback models
│   │   ├── schemas\
│   │   │   ├── __init__.py
│   │   │   └── event.py      # Pydantic validation schemas and history aggregate
│   │   └── api\
│   │       ├── __init__.py
│   │       └── routes\
│   │           ├── __init__.py
│   │           ├── health.py # GET /api/health implementation
│   │           └── events.py # Notification event CRUD, decisions, outcomes, history
│   └── tests\
│       ├── __init__.py
│       ├── test_health.py    # Health check tests
│       └── test_events.py    # Isolated SQLite in-memory tests for events & integrity
└── frontend\
    ├── index.html            # Vite HTML shell with typography
    ├── package.json          # React 18, Vite, TypeScript, Recharts, Lucide
    ├── tsconfig.json         # Strict TypeScript configuration
    ├── tsconfig.node.json    # TypeScript node config for Vite
    ├── vite.config.ts        # Vite config with /api reverse proxy to 127.0.0.1:8000
    └── src\
        ├── main.tsx          # React application entrypoint
        ├── App.tsx           # Main application shell with live health check
        ├── index.css         # Dark AI analytics theme & custom styling
        ├── App.css           # Component layouts and responsive design
        ├── types\
        │   └── index.ts      # TypeScript interfaces and navigation types
        └── components\
            ├── Header.tsx             # Brand header with dynamic backend pulse
            ├── Navigation.tsx         # Tab navigation across modules
            ├── StatusBanner.tsx       # Real-time proxy status & environment chip
            └── PlaceholderSection.tsx # Unambiguous 'not yet implemented' views
```

---

## Database Schema & Persistence

Database file location: **`d:\digital_twin\attention_twin.db`** (SQLite, configured via `DATABASE_URL` in `.env`).  
SQLite foreign keys are enforced via `PRAGMA foreign_keys = ON;`.

### Entities & Relationships

1. **`NotificationEvent` (`notification_events`)**
   - `id`: Integer (PK, Autoincrement)
   - `text`: Text (notification body or summary)
   - `source_app`: String(100) (e.g. `Slack`, `Gmail`, `WhatsApp`)
   - `category`: String(100) (e.g. `communication`, `work`, `alert`)
   - `timestamp`: DateTime(timezone=True)
   - `context_data`: JSON (optional contextual telemetry: e.g. `current_focus_mode`, `active_window`)
   - *Cascades to*: decisions, observed outcomes, counterfactual predictions, feedback.

2. **`NotificationDecision` (`notification_decisions`)**
   - `id`: Integer (PK, Autoincrement)
   - `event_id`: Integer (FK -> `notification_events.id`, CASCADE)
   - `action`: String(50) (`allow`, `suppress`, `defer`)
   - `reason`: Text (explanation or rule rationale)
   - `timestamp`: DateTime(timezone=True)

3. **`ObservedOutcome` (`observed_outcomes`)**
   - `id`: Integer (PK, Autoincrement)
   - `event_id`: Integer (FK -> `notification_events.id`, CASCADE)
   - `outcome_type`: String(50) (e.g. `responded_immediately`, `deferred_until_break`, `ignored`)
   - `timestamp`: DateTime(timezone=True)
   - `interaction_measurements`: JSON (factual interaction metrics without fabricated values)

4. **`CounterfactualPrediction` (`counterfactual_predictions`)**
   - `id`: Integer (PK, Autoincrement)
   - `event_id`: Integer (FK -> `notification_events.id`, CASCADE)
   - `proposed_action`: String(50) (`allow`, `suppress`, `defer`)
   - `predicted_outcome`: JSON (e.g. estimated disruption scores, information delay penalty)
   - `model_version`: String(100)
   - `timestamp`: DateTime(timezone=True)

5. **`UserFeedback` (`user_feedback`)**
   - `id`: Integer (PK, Autoincrement)
   - `event_id`: Integer (FK -> `notification_events.id`, CASCADE)
   - `decision_id`: Integer (FK -> `notification_decisions.id`, SET NULL, optional)
   - `prediction_id`: Integer (FK -> `counterfactual_predictions.id`, SET NULL, optional)
   - `feedback_rating`: Integer (1 to 5)
   - `feedback_label`: String(50)
   - `comment`: Text
   - `timestamp`: DateTime(timezone=True)

---

## API Endpoints Reference

All endpoints are prefixed with `/api` and return standard JSON payloads.

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and metadata | 200 OK |
| `POST` | `/api/events` | Create a new notification event with context | 201 Created |
| `GET` | `/api/events` | List events with pagination (`limit`, `offset`) and filters (`source_app`, `category`) | 200 OK |
| `GET` | `/api/events/{event_id}` | Retrieve a specific notification event | 200 OK / 404 Not Found |
| `POST` | `/api/events/{event_id}/decisions` | Record action taken (`allow`, `suppress`, `defer`) and reason | 201 Created / 404 Not Found |
| `POST` | `/api/events/{event_id}/outcomes` | Record factual observed outcome and interaction metrics | 201 Created / 404 Not Found |
| `POST` | `/api/events/{event_id}/predictions`| Store counterfactual prediction for candidate action | 201 Created / 404 Not Found |
| `POST` | `/api/events/{event_id}/feedback` | Record user rating and comments | 201 Created / 400 / 404 |
| `GET` | `/api/events/{event_id}/history` | Retrieve full history (decisions, outcomes, predictions, feedback) | 200 OK / 404 Not Found |

---

## Prerequisites

- **Windows 10/11** with **PowerShell**
- **Python 3.11+** installed
- **Node.js v18+** and **npm** installed

---

## Quickstart Guide (Windows PowerShell)

### 1. Run Automated Tests

Automated tests run on an isolated in-memory SQLite database (`sqlite:///:memory:`) so production and development databases are never corrupted:

```powershell
# From project root with venv:
.venv\Scripts\python -m pytest backend\tests -v
```

Expected output:
```
backend/tests/test_events.py::test_create_and_retrieve_event PASSED
backend/tests/test_events.py::test_list_events_with_filters_and_pagination PASSED
backend/tests/test_events.py::test_record_decisions_valid_and_invalid PASSED
backend/tests/test_events.py::test_record_observed_outcome PASSED
backend/tests/test_events.py::test_record_counterfactual_prediction PASSED
backend/tests/test_events.py::test_record_user_feedback_and_validation PASSED
backend/tests/test_events.py::test_event_history_aggregation PASSED
backend/tests/test_events.py::test_nonexistent_event_ids_return_404 PASSED
backend/tests/test_events.py::test_referential_integrity_and_cascade_delete PASSED
backend/tests/test_health.py::test_health_check_api_prefix PASSED
backend/tests/test_health.py::test_health_check_root_endpoint PASSED
======================== 11 passed, 1 warning in 0.90s ========================
```

### 2. Start Backend Server

```powershell
# From project root:
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 3. Start Frontend Server

Open a separate Windows PowerShell terminal:

```powershell
cd d:\digital_twin\frontend
npm run dev
```

- Frontend URL: `http://localhost:5173`
- The Vite reverse proxy routes `/api/*` to `http://127.0.0.1:8000`.
- To verify frontend build integrity: `npm run build`
