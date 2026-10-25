from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AttentionTwin - Personal Attention Digital Twin",
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
# Also expose /health at root for convenience
app.include_router(health.router, prefix="", tags=["health"])


@app.get("/")
def root():
    return {
        "message": "Welcome to AttentionTwin API",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
