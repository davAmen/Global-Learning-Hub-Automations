"""Tests for the scheduler module."""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest


def test_already_sent_true():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = [{"id": "x"}]
    from src.automation.scheduler import already_sent
    assert already_sent(db, "enr-1", date(2026, 9, 18)) is True


def test_already_sent_false():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = []
    from src.automation.scheduler import already_sent
    assert already_sent(db, "enr-1", date(2026, 9, 18)) is False
