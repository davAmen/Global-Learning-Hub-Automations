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
@patch("src.api.routes_jobs.send_report_to_admin", return_value=True)
@patch("src.api.routes_jobs.build_report")
@patch("src.api.routes_jobs.send_reminders", return_value=3)
def test_run_daily_job(mock_send, mock_build_report, mock_send_report, mock_db, mock_settings):
    from src.main import app
    mock_settings.return_value.admin_api_key = "test-only-secret"
    mock_build_report.return_value = {"date": "2026-09-18"}
    client = TestClient(app)
    assert client.post("/run-daily-job").status_code == 403
    r = client.post("/run-daily-job", headers={"x-admin-key": "test-only-secret"})
    assert r.status_code == 200
    assert r.json()["reminders_sent"] == 3
    assert r.json()["report_sent"] is True
    run_date = mock_send.call_args.args[1]
    assert mock_build_report.call_args.args == (mock_db.return_value, run_date)
    mock_send_report.assert_called_once_with(
        mock_build_report.return_value, db=mock_db.return_value
    )


def test_unverified_webhook_cannot_change_status():
    from src.main import app
    client = TestClient(app)
    assert client.post("/webhooks/whatsapp", json={"message_id": "x", "status": "sent"}).status_code == 501


def test_scheduled_job_uses_one_date_for_reminders_and_report():
    from src.main import run_scheduled_job

    db = MagicMock()
    report = {"date": "2026-09-18"}
    with patch("src.database.get_db", return_value=db), patch(
        "src.automation.scheduler.send_reminders"
    ) as send_reminders, patch(
        "src.reports.daily_report.build_report", return_value=report
    ) as build_report, patch(
        "src.reports.daily_report.send_report_to_admin"
    ) as send_report:
        run_scheduled_job()

    run_date = send_reminders.call_args.args[1]
    assert build_report.call_args.args == (db, run_date)
    send_report.assert_called_once_with(report, db=db)
