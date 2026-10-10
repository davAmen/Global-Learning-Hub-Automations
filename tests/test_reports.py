"""Tests for daily report aggregation and delivery."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def test_build_report_excludes_administrator_attempts_from_student_totals():
    from src.reports.daily_report import build_report

    db = MagicMock()
    queries = {}

    def table(name):
        query = MagicMock()
        queries[name] = query
        if name == "courses":
            query.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(
                data=[{"id": "course-1", "name": "Python"}]
            )
        elif name == "enrollments":
            query.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(
                data=[{"id": "enrollment-1", "status": "active"}]
            )
        elif name == "engagement_log":
            query.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(
                data=[{"status": "active"}]
            )
        elif name == "reminder_log":
            query.select.return_value.gte.return_value.lt.return_value.execute.return_value = SimpleNamespace(
                data=[
                    {"enrollment_id": "enrollment-1", "delivery_status": "sent"},
                    {"enrollment_id": None, "delivery_status": "sent"},
                    {"enrollment_id": "enrollment-2", "delivery_status": "failed"},
                ]
            )
        return query

    db.table.side_effect = table

    report = build_report(db, date(2026, 9, 18))

    assert report["courses_today"] == 1
    assert report["total_enrolled"] == 1
    assert report["engagement"]["active"] == 1
    assert report["reminders"] == {"sent": 1, "failed": 1}
    upper_bound = (
        queries["reminder_log"]
        .select.return_value.gte.return_value.lt.call_args.args[1]
    )
    assert upper_bound == "2026-09-19T00:00:00"


def test_send_report_logs_attempt_through_configured_backup():
    from src.reports.daily_report import send_report_to_admin

    report = {
        "date": "2026-09-26",
        "courses_today": 1,
        "total_enrolled": 1,
        "engagement": {"active": 1, "low_engagement": 0, "needs_followup": 0},
        "reminders": {"sent": 1, "failed": 0},
    }
    settings = SimpleNamespace(backup_channel="telegram")
    db = MagicMock()
    db.table.return_value.select.return_value.is_.return_value.gte.return_value.lt.return_value.execute.return_value.data = []
    channel = MagicMock()

    with patch("src.reports.daily_report.get_settings", return_value=settings), patch(
        "src.reports.daily_report.get_channel", return_value=channel
    ) as get_channel, patch(
        "src.reports.daily_report.send_and_log", return_value=True
    ) as send_and_log:
        assert send_report_to_admin(report, db) is True

    get_channel.assert_called_once_with("telegram")
    args = send_and_log.call_args.args
    assert args[:3] == (db, channel, None)
    assert args[4] is None
    assert "Reminders sent: 1" in args[3]
    assert "Reminders failed: 0" in args[3]


def test_send_report_skips_a_second_attempt_on_the_same_day():
    from src.reports.daily_report import send_report_to_admin

    report = {"date": "2026-09-26"}
    settings = SimpleNamespace(backup_channel="telegram")
    db = MagicMock()
    db.table.return_value.select.return_value.is_.return_value.gte.return_value.lt.return_value.execute.return_value.data = [
        {"id": "previous-attempt"}
    ]

    with patch("src.reports.daily_report.get_settings", return_value=settings), patch(
        "src.reports.daily_report.get_channel"
    ) as get_channel, patch("src.reports.daily_report.send_and_log") as send_and_log:
        assert send_report_to_admin(report, db) is False

    get_channel.assert_not_called()
    send_and_log.assert_not_called()
