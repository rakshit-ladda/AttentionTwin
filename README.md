# AttentionTwin — Personal Attention Digital Twin

> **CASCADE 2026 — IIIT Nagpur Hackathon Project**  
> **Phase 1: Project Foundation & Architecture Shell**

AttentionTwin is a personal Attention Digital Twin designed to model how an individual responds to notifications and estimate the outcomes of **allowing**, **suppressing**, or **deferring** a notification.

The defining requirement is **counterfactual comparison**: evaluating predicted outcomes under different actions for the **same** notification and user context. The core prediction engine runs locally on scikit-learn without mandatory external cloud APIs or paid dependencies.

---

## Architecture Overview (Phase 1)

```
d:\digital_twin\
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions (venv, node_modules, sqlite, secrets)
├── README.md                 # Project documentation and run commands
├── backend\
│   ├── requirements.txt      # FastAPI, Uvicorn, Pydantic, pytest, scikit-learn
│   ├── app\
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI entrypoint with CORS & route registration
│   │   ├── core\
│   │   │   ├── __init__.py
│   │   │   └── config.py     # Pydantic Settings & environment configuration
│   │   └── api\
│   │       ├── __init__.py
│   │       └── routes\
│   │           ├── __init__.py
│   │           └── health.py # GET /api/health implementation
│   └── tests\
│       ├── __init__.py
│       └── test_health.py    # Automated TestClient tests for health checks
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

## Prerequisites

- **Windows 10/11** with **PowerShell**
- **Python 3.11+** installed
- **Node.js v18+** and **npm** installed

---

## Quickstart Guide (Windows PowerShell)

All commands below are formatted for standard **Windows PowerShell**.

### 1. Backend Setup

From the project root (`d:\digital_twin`):

```powershell
# Create the Python virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Upgrade pip and install backend requirements
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

### 2. Run Backend Automated Tests

Verify that backend endpoints operate properly:

```powershell
# From project root with venv activated:
pytest backend\tests -v

# Or directly using the virtual environment interpreter:
.venv\Scripts\python -m pytest backend\tests -v
```

Expected output:
```
backend/tests/test_health.py::test_health_check_api_prefix PASSED
backend/tests/test_health.py::test_health_check_root_endpoint PASSED
```

### 3. Start Backend Server

Start the FastAPI ASGI server with hot reloading enabled on port `8000`:

```powershell
# Option A: From project root
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Option B: From inside the backend directory
cd backend
..\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 4. Frontend Setup

Open a **separate** Windows PowerShell window:

```powershell
cd d:\digital_twin\frontend

# Install dependencies (React, Vite, Recharts, Lucide-React)
npm install
```

### 5. Start Frontend Development Server

```powershell
cd d:\digital_twin\frontend
npm run dev
```

- Frontend URL: `http://localhost:5173`
- The Vite development proxy automatically routes all requests starting with `/api` to `http://127.0.0.1:8000`.

---

## Health Check Endpoint Specification

### `GET /api/health`

Returns service health and metadata:

```json
{
  "status": "healthy",
  "service": "AttentionTwin API",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-10-25T10:14:14.000000+00:00"
}
```

---

## Application Shell & Sections (Phase 1)

In Phase 1, the frontend application shell presents a dark, professional AI analytics UI with live backend connectivity indicator. In accordance with strict development integrity rules, no synthetic predictions, fake ML metrics, or mock user statistics are rendered.

The four core modules are clearly demarcated as **Not Yet Implemented**:

1. **Attention Profile** (Target: Phase 2): Cognitive state modeling, baseline responsiveness, and circadian focus curves.
2. **Notification Simulator** (Target: Phase 3): Interactive input harness to evaluate incoming notification disruption across contexts.
3. **Counterfactual Comparison** (Target: Phase 3 & 4): The central engine comparing predicted outcomes for the **same** notification across **ALLOW**, **SUPPRESS**, and **DEFER**.
4. **History and Learning** (Target: Phase 4): Local interaction logs and offline incremental retraining loop.
