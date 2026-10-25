# AttentionTwin — Personal Attention Digital Twin

> **CASCADE 2026 — IIIT Nagpur Hackathon Project**  
> **Phase 1: Project Foundation & Architecture Shell**  
> **Phase 2: Database Persistence & Event APIs**  
> **Phase 3: Synthetic Dataset Generation & Feature Engineering**  
> **Phase 4: Baseline Machine Learning Prediction Engine**  
> **Phase 5: Action-Aware Counterfactual Comparison Engine**  
> **Phase 6: Live Dashboard, History Panel & Model Status UI**  
> **Phase 7: Native Android APK (Capacitor)**

AttentionTwin is a personal Attention Digital Twin designed to model how an individual responds to notifications and estimate the outcomes of **allowing**, **suppressing**, or **deferring** a notification.

The defining requirement is **counterfactual comparison**: evaluating predicted outcomes under different actions for the **same** notification and user context. The core prediction engine runs locally on scikit-learn without mandatory external cloud APIs or paid dependencies.

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
│   │   ├── baseline_model.joblib     # Serialized RandomForestClassifier pipeline (Phase 4)
│   │   ├── model_metadata.json       # Version, metrics, evaluation basis, and disclaimers
│   │   ├── action_aware_model.joblib # Serialized Action-Aware RandomForest pipeline (Phase 5)
│   │   └── action_aware_metadata.json# Action-aware metrics, per-action breakdowns, disclaimers
│   ├── requirements.txt              # FastAPI, Uvicorn, Pydantic, SQLAlchemy, scikit-learn
│   ├── app\
│   │   ├── main.py                   # FastAPI entrypoint, lifespan db init, router setup
│   │   ├── core\config.py            # Settings, DATABASE_URL, CORS configuration
│   │   ├── db\                       # Base, SessionLocal, get_db dependency
│   │   ├── models\event.py           # Event, Decision, Outcome, Prediction, Feedback models
│   │   ├── schemas\                  # Pydantic schemas (event.py, ml.py, counterfactual.py)
│   │   ├── ml\
│   │   │   ├── feature_schema.py     # Logical feature groups, cold-start defaults, sources
│   │   │   ├── synthetic_generator.py# Deterministic multi-factor synthetic data generator
│   │   │   ├── feature_pipeline.py   # Chronological feature extractor & leakage validator
│   │   │   ├── split_utils.py        # Chronological and user-held-out evaluation splitters
│   │   │   ├── trainer.py            # BaselineModelTrainer (Phase 4)
│   │   │   ├── predictor.py          # PredictionService for inference & limitation disclosure
│   │   │   ├── action_aware_trainer.py# ActionAwareModelTrainer with per-action breakdowns (Phase 5)
│   │   │   └── counterfactual_engine.py# CounterfactualEngine for invariant context comparison
│   │   └── api\routes\
│   │       ├── health.py             # GET /api/health implementation
│   │       ├── events.py             # Event CRUD, decisions, outcomes, history
│   │       ├── ml.py                 # GET /api/models/status, POST /api/models/predict
│   │       └── counterfactuals.py    # POST /api/counterfactuals/compare
│   └── tests\
│       ├── test_health.py            # Phase 1 health check tests
│       ├── test_events.py            # Phase 2 event persistence & cascade tests
│       ├── test_synthetic_data.py    # Phase 3 feature pipeline & cold-start tests
│       ├── test_ml_pipeline.py       # Phase 4 ML training, evaluation, & inference tests
│       └── test_counterfactuals.py   # Phase 5 counterfactual engine & DB safety tests
└── frontend\
    ├── index.html                    # Vite HTML shell with typography
    ├── package.json                  # React 18, Vite, TypeScript, Recharts, Lucide
    ├── tsconfig.json                 # Strict TypeScript configuration
    └── src\                          # Application shell and UI components
```

---

## Action-Aware Counterfactual Engine (Phase 5)

### Core Invariant
For any incoming notification, all pre-decision attributes (**source app, category, text length, hour of day, focus mode, active focus block, trailing alert load, and historical responsiveness**) remain **strictly identical**. Only the candidate intervention action (`allow`, `defer`, `suppress`) is varied to estimate alternative outcomes under identical circumstances.

### Feature Schema (18 Features)
- **Categorical (5):** `source_app`, `app_category`, `notification_category`, `focus_mode`, `proposed_action` (`allow`, `defer`, `suppress`).
- **Numeric (13):** `text_length`, `hour_of_day`, `day_of_week`, `is_weekend`, `is_focus_session`, `recent_notification_count_15m`, `minutes_since_last_notification`, `notification_load_1h`, `app_historical_open_rate`, `app_historical_ignore_rate`, `user_historical_open_rate`, `recent_allow_rate_1h`, `recent_suppress_rate_1h`.

### Evaluation Metrics (Action-Aware Model)

Chronological Split (80% train / 20% test per user):
- **Overall Accuracy:** 71.44% (vs Dummy Baseline: 64.69%)
- **Overall ROC-AUC:** 0.7698

#### Per-Action Breakdown on Test Set
- **ALLOW Action:** Prompt open rate: 43.31% | Accuracy: 66.88% | F1: 0.5407
- **DEFER Action:** Prompt open rate: 17.84% | Accuracy: 79.88% | F1: 0.2885
- **SUPPRESS Action:** Prompt open rate: 8.38% | Accuracy: 89.04% | F1: 0.1111

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
| `GET` | `/api/models/status` | Baseline model operational status and metadata | 200 OK |
| `POST` | `/api/models/predict` | Predict probability of quick open (unconditioned) | 200 OK / 422 / 503 |
| `POST` | `/api/counterfactuals/compare` | Compare simulated outcomes across `allow`, `defer`, `suppress` | 200 OK / 422 / 503 |

---

## Quickstart Guide (Windows PowerShell)

### 1. Run Complete Automated Test Suite (32 Tests)

```powershell
$env:PYTHONPATH="backend"
.venv\Scripts\python -m pytest backend\tests -v
```

Expected output:
```
backend/tests/test_counterfactuals.py (8 passed)
backend/tests/test_events.py (9 passed)
backend/tests/test_health.py (2 passed)
backend/tests/test_ml_pipeline.py (8 passed)
backend/tests/test_synthetic_data.py (5 passed)
======================== 32 passed, 1 warning in 4.42s ========================
```

### 2. Retrain Models (Optional)

```powershell
$env:PYTHONPATH="backend"
# Retrain Phase 4 baseline model
.venv\Scripts\python -c "from app.ml.trainer import BaselineModelTrainer; BaselineModelTrainer().train_and_save()"

# Retrain Phase 5 action-aware model
.venv\Scripts\python -c "from app.ml.action_aware_trainer import ActionAwareModelTrainer; ActionAwareModelTrainer().train_and_save()"
```

### 3. Start Backend Server

```powershell
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 4. Start Frontend Server

```powershell
cd d:\digital_twin\frontend
npm run dev
```
- Frontend UI: `http://localhost:5173`
- Production Build Check: `npm run build`

---

## Android Native Application (Phase 7)

The frontend is packaged as an installable native Android application using Capacitor (`com.attentiontwin.app`).

### 1. Pre-built APK Artifact
- **APK Path:** `frontend/android/app/build/outputs/apk/debug/app-debug.apk`
- **Package ID:** `com.attentiontwin.app`
- **Application Name:** `AttentionTwin`
- **Size:** ~4.3 MB

### 2. Run Backend for Mobile Device Access
For the Android app to connect to the backend over your local network:
```powershell
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```
Find your laptop's local IP address (`ipconfig`, e.g. `192.168.1.15`).

### 3. Connect Android App to Backend
1. Open the **AttentionTwin** app on your phone or emulator.
2. Tap the **⚙ (Gear)** icon in the top header.
3. Enter your backend URL:
   - Physical device on same Wi-Fi: `http://<YOUR_LAPTOP_IP>:8000` (e.g., `http://192.168.1.15:8000`)
   - Android Emulator: `http://10.0.2.2:8000` (preset button provided)
   - Desktop / Web Browser: `http://localhost:8000` (preset button provided)
4. Tap **Save & Reconnect**. The app will verify connectivity with `/api/health`.

### 4. Install APK on Android Device
Using ADB:
```powershell
D:\Android\sdk\platform-tools\adb.exe install -r frontend\android\app\build\outputs\apk\debug\app-debug.apk
```
Or copy `app-debug.apk` to your phone via USB or Google Drive and install directly (allow installation from unknown sources when prompted).

### 5. Rebuilding the APK
```powershell
cd d:\digital_twin\frontend
npm run build
npx cap sync android
$env:JAVA_HOME = "D:\jdk-21.0.4+7"
$env:ANDROID_HOME = "D:\Android\sdk"
cd android
.\gradlew.bat assembleDebug
```

---

## Hackathon Problem Statement Compliance & Phase 8

AttentionTwin directly implements the core scenario specified in the problem statement:
> *When a user is coding and receives a social notification such as "Someone liked your post," the system estimates what might happen if the notification is allowed, including interruption duration, whether the social app is opened, time spent browsing, and delay before resuming the original task, while comparing alternative actions (allow, defer, suppress).*

### 1. The Four Estimated Disruption Metrics
For each scenario action (`allow`, `defer`, `suppress`), the engine computes:
1. **App Opening Probability & Class:** Model-predicted probability of opening the notification quickly ($P(\text{opened quickly})$).
2. **Time Spent Browsing ($T_{\text{browse}}$):** App-category duration distributions conditioned on open likelihood (e.g. ~14 min for social apps, ~5 min for communication, ~2 min for alerts).
3. **Task-Resumption Delay ($T_{\text{resume}}$):** Cognitive context-switching resumption overhead based on focus mode (e.g. ~12.5 min to recover deep work coding flow, based on Mark et al. research).
4. **Total Interruption Duration ($T_{\text{total}}$):** Calculated as $T_{\text{browse}} + T_{\text{resume}}$ for immediate interruptions, or $0.0$ min primary-task loss when deferred or suppressed.

### 2. Defensible Recommendation Policy
- **DEFER (Preserve Flow):** Recommended when incoming non-urgent notifications (social, entertainment) arrive during `deep_work` or active focus sessions. Scheduled for the next break window (`+25m`), keeping task disruption at **0.0 minutes**.
- **SUPPRESS (Eliminate Distraction):** Recommended for marketing/promotional interruptions during work hours, routing to an end-of-day silent digest.
- **ALLOW (Immediate):** Recommended for critical system alerts or during unstructured casual browsing / off-hours where attention loss is minimal.


