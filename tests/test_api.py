"""Tests for API endpoints."""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_health():
    from src.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@patch("src.api.routes_jobs.get_db")
@patch("src.api.routes_jobs.send_reminders", return_value=3)
def test_run_daily_job(mock_send, mock_db):
    from src.main import app
    client = TestClient(app)
    r = client.post("/run-daily-job")
    assert r.status_code == 200
    assert r.json()["reminders_sent"] == 3
