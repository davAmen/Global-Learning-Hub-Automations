"""Tests for API endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_health():
    from src.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@patch("src.api.auth.get_settings")
@patch("src.api.routes_jobs.get_db")
@patch("src.api.routes_jobs.send_reminders", return_value=3)
def test_run_daily_job(mock_send, mock_db, mock_settings):
    from src.main import app
    mock_settings.return_value.admin_api_key = "test-only-secret"
    client = TestClient(app)
    assert client.post("/run-daily-job").status_code == 403
    r = client.post("/run-daily-job", headers={"x-admin-key": "test-only-secret"})
    assert r.status_code == 200
    assert r.json()["reminders_sent"] == 3


def test_unverified_webhook_cannot_change_status():
    from src.main import app
    client = TestClient(app)
    assert client.post("/webhooks/whatsapp", json={"message_id": "x", "status": "sent"}).status_code == 501
