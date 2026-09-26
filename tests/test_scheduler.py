"""Tests for the scheduler module."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest


def test_already_sent_true():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = [{"id": "x"}]
    from src.automation.scheduler import already_sent
    assert already_sent(db, "enr-1", date(2026, 9, 18)) is True
    upper_bound = db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.call_args.args[1]
    assert upper_bound == "2026-09-19T00:00:00"


def test_already_sent_false():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = []
    from src.automation.scheduler import already_sent
    assert already_sent(db, "enr-1", date(2026, 9, 18)) is False


def test_send_reminders_uses_logged_attempt_and_updates_engagement():
    from src.automation.scheduler import send_reminders

    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"name": "Python", "class_time": "09:00:00"}
    ]
    enrollment = SimpleNamespace(
        id="enrollment-1", student_id="student-1", course_id="course-1"
    )
    student = SimpleNamespace(name="Sample Student", phone="+15555550101")
    channel = MagicMock(name="whatsapp")
    settings = SimpleNamespace(active_channel="whatsapp", rate_limit_delay_seconds=0)

    with patch(
        "src.automation.scheduler.build_reminder_queue", return_value=[enrollment]
    ), patch(
        "src.automation.scheduler.get_student", return_value=student
    ), patch(
        "src.automation.scheduler.get_settings", return_value=settings
    ), patch(
        "src.automation.engagement.update_engagement", return_value="active"
    ) as update_engagement, patch(
        "src.channels.base.get_channel", return_value=channel
    ), patch(
        "src.channels.base.send_and_log", return_value=True
    ) as send_and_log:
        assert send_reminders(db, date(2026, 9, 18)) == 1

    update_engagement.assert_called_once_with(db, "enrollment-1", date(2026, 9, 18))
    assert send_and_log.call_args.args[0:3] == (db, channel, student)
    assert send_and_log.call_args.args[4] == "enrollment-1"
