# AttentionTwin — Personal Attention Digital Twin

> **CASCADE 2026 — IIIT Nagpur Hackathon Project**  
> **Phase 1: Project Foundation & Architecture Shell**  
> **Phase 2: Database Persistence & Event APIs**  
> **Phase 3: Synthetic Dataset Generation & Feature Engineering**  
> **Phase 4: Baseline Machine Learning Prediction Engine**

AttentionTwin is a personal Attention Digital Twin designed to model how an individual responds to notifications and estimate the outcomes of **allowing**, **suppressing**, or **deferring** a notification.

The core prediction engine runs locally on scikit-learn without mandatory external cloud APIs or paid dependencies.

---

## Architecture Overview

```
d:\digital_twin\
├── data\
│   └── synthetic\
│       ├── raw_synthetic_events.json # 8,000 raw synthetic event records
│       ├── feature_dataset.csv       # Model-ready features table with binary & multiclass targets
│       ├── metadata.json             # Seed, generator version, provenance, and summary stats
│       └── README.md                 # Data dictionary, assumptions, cold-start handling
├── backend\
│   ├── artifacts\
│   │   ├── baseline_model.joblib     # Serialized RandomForestClassifier pipeline
│   │   └── model_metadata.json       # Version, metrics, evaluation basis, and disclaimers
│   ├── requirements.txt              # FastAPI, Uvicorn, Pydantic, SQLAlchemy, scikit-learn
│   ├── app\
│   │   ├── main.py                   # FastAPI entrypoint, lifespan db init, router setup
│   │   ├── core\config.py            # Settings, DATABASE_URL, CORS configuration
│   │   ├── db\                       # Base, SessionLocal, get_db dependency
│   │   ├── models\event.py           # Event, Decision, Outcome, Prediction, Feedback models
│   │   ├── schemas\                  # Pydantic schemas (event.py, ml.py)
│   │   ├── ml\
│   │   │   ├── feature_schema.py     # Logical feature groups, cold-start defaults, sources
│   │   │   ├── synthetic_generator.py# Deterministic multi-factor synthetic data generator
│   │   │   ├── feature_pipeline.py   # Chronological feature extractor & leakage validator
│   │   │   ├── split_utils.py        # Chronological and user-held-out evaluation splitters
│   │   │   ├── trainer.py            # BaselineModelTrainer (Dummy, Logistic, RandomForest)
│   │   │   └── predictor.py          # PredictionService for inference & limitation disclosure
│   │   └── api\routes\
│   │       ├── health.py             # GET /api/health implementation
│   │       ├── events.py             # Event CRUD, decisions, outcomes, history
│   │       └── ml.py                 # GET /api/models/status, POST /api/models/predict
│   └── tests\
│       ├── test_health.py            # Phase 1 health check tests
│       ├── test_events.py            # Phase 2 event persistence & cascade tests
│       ├── test_synthetic_data.py    # Phase 3 feature pipeline & cold-start tests
│       └── test_ml_pipeline.py       # Phase 4 ML training, evaluation, & inference tests
└── frontend\
    ├── index.html                    # Vite HTML shell with typography
    ├── package.json                  # React 18, Vite, TypeScript, Recharts, Lucide
    ├── tsconfig.json                 # Strict TypeScript configuration
    └── src\                          # Application shell and UI components
```

---

## Machine Learning Feature Schema (Phase 3 & 4)

### Target Definition
- **Target Variable:** `opened_within_5min` (Binary: `1` = opened within 5 minutes, `0` = delayed or ignored).
- **Secondary Multiclass Representation:** `outcome_label` (`opened_quickly`, `opened_later`, `ignored`).

### Feature Groups

1. **Notification Features (at arrival):**
   - `source_app` (Categorical: `Slack`, `Gmail`, `WhatsApp`, `GitHub`, `Calendar`, etc.)
   - `app_category` (Categorical: `communication`, `work`, `productivity`, `social`, etc.)
   - `notification_category` (Categorical: `direct_message`, `meeting_reminder`, `cpu_spike`, etc.)
   - `text_length` (Numeric: character length of notification preview)
   - `hour_of_day` (Numeric: 0–23)
   - `day_of_week` (Numeric: 0=Mon, 6=Sun)
   - `is_weekend` (Numeric: 1 or 0)

2. **Context Features (at arrival):**
   - `focus_mode` (Categorical: `deep_work`, `meeting`, `casual_browsing`, `off_hours`)
   - `is_focus_session` (Numeric: 1 or 0)
   - `recent_notification_count_15m` (Numeric: alerts in preceding 15m)
   - `minutes_since_last_notification` (Numeric: elapsed minutes, capped at 1440)
   - `notification_load_1h` (Numeric: alert volume in preceding 60m)

3. **Historical Behavioral Features (strictly prior events):**
   - `app_historical_open_rate` (Numeric: 0.0–1.0)
   - `app_historical_ignore_rate` (Numeric: 0.0–1.0)
   - `user_historical_open_rate` (Numeric: 0.0–1.0)
   - `recent_allow_rate_1h` (Numeric: 0.0–1.0)
   - `recent_suppress_rate_1h` (Numeric: 0.0–1.0)

---

## Baseline ML Evaluation Results (Phase 4)

Evaluated via **Chronological Split** (train on first 80% time, evaluate on subsequent 20% future events per user):

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DummyClassifier** (Most Frequent) | 64.69% | 0.00% | 0.00% | 0.00 | 0.5000 | Always predicts negative majority class |
| **Logistic Regression** | 72.13% | 71.48% | 35.04% | 0.4703 | 0.7192 | Linear baseline with `ColumnTransformer` |
| **RandomForestClassifier** (Saved) | 71.63% | 73.22% | 30.97% | 0.4353 | 0.7139 | Non-linear baseline with probability output |

> **Limitations & Disclaimer:**  
> This model was trained on synthetic simulation data. Predictions reflect synthetic heuristics and do not establish real human distraction or true behavioral probability.

---

## API Endpoints Reference

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and metadata | 200 OK |
| `POST` | `/api/events` | Create a new notification event with context | 201 Created |
| `GET` | `/api/events` | List events with pagination and filters | 200 OK |
| `GET` | `/api/events/{id}` | Retrieve specific notification event | 200 OK / 404 |
| `POST` | `/api/events/{id}/decisions` | Record action taken (`allow`, `suppress`, `defer`) | 201 Created / 404 |
| `POST` | `/api/events/{id}/outcomes` | Record factual observed outcome and interaction metrics | 201 Created / 404 |
| `POST` | `/api/events/{id}/predictions`| Store counterfactual prediction for candidate action | 201 Created / 404 |
| `POST` | `/api/events/{id}/feedback` | Record user rating (1–5) and comments | 201 Created / 400 / 404 |
| `GET` | `/api/events/{id}/history` | Retrieve complete event audit trail | 200 OK / 404 |
| `GET` | `/api/models/status` | Model operational status, metadata, and provenance | 200 OK |
| `POST` | `/api/models/predict` | Predict probability of notification quick open | 200 OK / 422 / 503 |

---

## Quickstart Guide (Windows PowerShell)

### 1. Run Automated Test Suite (24 Tests)

```powershell
$env:PYTHONPATH="backend"
.venv\Scripts\python -m pytest backend\tests -v
```

All 24 unit and integration tests across Phase 1, Phase 2, Phase 3, and Phase 4 pass in ~3.8 seconds.

### 2. Retrain Baseline Models (Optional)

```powershell
$env:PYTHONPATH="backend"
.venv\Scripts\python -c "from app.ml.trainer import BaselineModelTrainer; BaselineModelTrainer().train_and_save()"
```

### 3. Start Backend Server

```powershell
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 4. Start Frontend Server

Open a separate terminal:

```powershell
cd d:\digital_twin\frontend
npm run dev
```
- Frontend UI: `http://localhost:5173`
- Production Build Check: `npm run build`
