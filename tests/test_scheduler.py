"""Tests for scheduler idempotency."""

from datetime import date
from unittest.mock import MagicMock


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
