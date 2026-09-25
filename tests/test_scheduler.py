"""Tests for scheduler idempotency."""

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4


def _db_with_reminder_rows(rows):
    db = MagicMock()
    query = (
        db.table.return_value
        .select.return_value
        .eq.return_value
        .gte.return_value
        .lt.return_value
        .limit.return_value
        .execute.return_value
    )
    query.data = rows
    return db


def test_already_sent_true():
    from src.automation.scheduler import already_sent

    db = _db_with_reminder_rows([{"id": "x"}])
    assert already_sent(db, "enr-1", date(2026, 9, 18)) is True


def test_already_sent_false():
    from src.automation.scheduler import already_sent

    db = _db_with_reminder_rows([])
    assert already_sent(db, "enr-1", date(2026, 9, 18)) is False


def test_claim_precedes_send_and_blocks_competing_worker(monkeypatch):
    from src.automation import scheduler
    from src.channels import base

    enrollment = MagicMock(id=uuid4(), student_id=uuid4(), course_id=uuid4())
    student = MagicMock(name="Sample Student")
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"name": "Sample Course", "class_time": "18:00"}
    ]
    channel = MagicMock(name="channel")
    channel.name = "whatsapp"
    channel.send.return_value = True
    monkeypatch.setattr(base, "get_channel", lambda _: channel)
    monkeypatch.setattr(scheduler, "build_reminder_queue", lambda *_: [enrollment])
    monkeypatch.setattr(scheduler, "get_student", lambda *_: student)
    monkeypatch.setattr(scheduler, "already_sent", lambda *_: False)
    monkeypatch.setattr("src.automation.engagement.update_engagement", lambda *_: "active")
    monkeypatch.setattr(scheduler.time, "sleep", lambda *_: None)

    claim = db.table.return_value.insert.return_value.execute.return_value
    claim.data = [{"id": str(uuid4())}]
    assert scheduler.send_reminders(db, date(2026, 9, 18)) == 1
    assert db.table.return_value.insert.call_count == 1
    assert channel.send.call_count == 1
    assert db.table.return_value.update.call_count == 1

    db.table.return_value.insert.return_value.execute.side_effect = RuntimeError("duplicate claim")
    assert scheduler.send_reminders(db, date(2026, 9, 18)) == 0
    assert channel.send.call_count == 1
