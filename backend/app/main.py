from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db
from app.api.routes import health, events, ml, counterfactuals


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager ensuring database tables are initialized on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AttentionTwin - Personal Attention Digital Twin",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(health.router, prefix="", tags=["health"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(ml.router, prefix="/api", tags=["models"])
app.include_router(counterfactuals.router, prefix="/api", tags=["counterfactuals"])


@app.get("/")
def root():
    return {
        "message": "Welcome to AttentionTwin API",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
