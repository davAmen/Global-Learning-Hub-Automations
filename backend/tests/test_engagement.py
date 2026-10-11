"""Tests for engagement module."""

from datetime import date
from unittest.mock import MagicMock
import pytest


def test_classify_active():
    from src.automation.engagement import classify
    assert classify(0) == "active"
    assert classify(7) == "active"
    assert classify(5) == "active"


def test_classify_low_engagement():
    from src.automation.engagement import classify
    assert classify(8) == "low_engagement"
    assert classify(14) == "low_engagement"
    assert classify(10) == "low_engagement"


def test_classify_needs_followup():
    from src.automation.engagement import classify
    assert classify(15) == "needs_followup"
    assert classify(30) == "needs_followup"
    assert classify(100) == "needs_followup"


def test_days_since_last_submission_no_data():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    from src.automation.engagement import days_since_last_submission, NEEDS_FOLLOWUP_DAYS
    result = days_since_last_submission(db, "enr-1", date(2026, 9, 18))
    assert result == NEEDS_FOLLOWUP_DAYS + 1


def test_days_since_last_submission_with_data():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"date": "2026-09-10"}
    ]
    from src.automation.engagement import days_since_last_submission
    result = days_since_last_submission(db, "enr-1", date(2026, 9, 18))
    assert result == 8


def test_update_engagement_insert():
    db = MagicMock()
    # No existing record
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
    # No submission history
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    # Insert succeeds
    db.table.return_value.insert.return_value.execute.return_value.data = [{"id": "new-id"}]
    
    from src.automation.engagement import update_engagement
    status = update_engagement(db, "enr-1", date(2026, 9, 18))
    
    assert status in ["active", "low_engagement", "needs_followup"]
    db.table.return_value.insert.assert_called_once()


def test_update_engagement_update():
    db = MagicMock()
    # Existing record
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"id": "existing-id"}]
    # No submission history
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    # Update succeeds
    db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "existing-id"}]
    
    from src.automation.engagement import update_engagement
    status = update_engagement(db, "enr-1", date(2026, 9, 18))
    
    assert status in ["active", "low_engagement", "needs_followup"]
    db.table.return_value.update.assert_called_once()


def test_engagement_thresholds():
    from src.automation.engagement import LOW_ENGAGEMENT_DAYS, NEEDS_FOLLOWUP_DAYS
    assert LOW_ENGAGEMENT_DAYS == 7
    assert NEEDS_FOLLOWUP_DAYS == 14