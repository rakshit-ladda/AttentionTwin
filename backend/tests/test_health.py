from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_api_prefix():
    """Verify GET /api/health returns 200 and valid JSON."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_health_check_root_endpoint():
    """Verify GET /health also functions properly."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
