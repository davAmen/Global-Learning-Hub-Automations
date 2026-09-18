"""Tests for daily report module."""

from datetime import date
from unittest.mock import MagicMock


def test_build_report_returns_dict():
    from src.reports.daily_report import build_report
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    report = build_report(db, date(2026, 9, 18))
    assert "date" in report
    assert "courses_today" in report
