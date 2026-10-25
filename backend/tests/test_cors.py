"""CORS preflight and cross-origin security tests for AttentionTwin backend.

Verifies that the backend allows preflight OPTIONS requests from both local Vite
development servers and native Capacitor Android WebView origins, while rejecting
unauthorized origins.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_cors_preflight_android_webview_http_localhost():
    """Verify OPTIONS preflight succeeds for Capacitor Android WebView origin http://localhost."""
    response = client.options(
        "/api/counterfactuals/compare",
        headers={
            "Origin": "http://localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost"
    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods
    allow_headers = response.headers.get("access-control-allow-headers", "").lower()
    assert "content-type" in allow_headers


def test_cors_preflight_android_capacitor_scheme():
    """Verify OPTIONS preflight succeeds for capacitor://localhost scheme."""
    response = client.options(
        "/api/counterfactuals/compare",
        headers={
            "Origin": "capacitor://localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "capacitor://localhost"


def test_cors_preflight_android_https_scheme():
    """Verify OPTIONS preflight succeeds for https://localhost scheme."""
    response = client.options(
        "/api/counterfactuals/compare",
        headers={
            "Origin": "https://localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://localhost"


def test_cors_preflight_vite_development_origin():
    """Verify OPTIONS preflight succeeds for local Vite dev server at http://localhost:5173."""
    response = client.options(
        "/api/counterfactuals/compare",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_preflight_disallowed_origin_rejected():
    """Verify OPTIONS preflight is rejected with 400 for unauthorized external origins."""
    response = client.options(
        "/api/counterfactuals/compare",
        headers={
            "Origin": "http://unauthorized-domain.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 400
    assert "Disallowed CORS origin" in response.text


def test_cors_simple_get_includes_allow_origin():
    """Verify that a GET request from Android WebView receives access-control-allow-origin header."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost"
