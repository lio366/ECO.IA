"""Tests for the FastAPI application."""
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def client():
    from api.main import create_app
    app = create_app()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["system"] == "ECO-IA"


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_hosting_plans_requires_api_key(client):
    resp = client.get("/api/v1/services/hosting/plans")
    assert resp.status_code == 401


def test_hosting_plans_with_api_key(monkeypatch, client):
    monkeypatch.setenv("ECO_IA_API_KEY", "test-key")
    # Reload settings cache
    from config import settings as settings_mod
    settings_mod.get_settings.cache_clear()
    resp = client.get(
        "/api/v1/services/hosting/plans",
        headers={"X-API-Key": "test-key"},
    )
    assert resp.status_code == 200
    plans = resp.json()
    assert isinstance(plans, list)
    assert len(plans) > 0


def test_admin_requires_admin_key(client):
    resp = client.get("/api/v1/admin/health")
    assert resp.status_code == 403


def test_admin_health_with_key(monkeypatch, client):
    monkeypatch.setenv("ECO_IA_ADMIN_KEY", "admin-key")
    from config import settings as settings_mod
    settings_mod.get_settings.cache_clear()
    resp = client.get(
        "/api/v1/admin/health",
        headers={"X-Admin-Key": "admin-key"},
    )
    assert resp.status_code == 200


def test_docs_accessible(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_dashboard(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "ECO-IA" in resp.text
