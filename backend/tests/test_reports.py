"""Tests for daily report module."""

from datetime import date
from unittest.mock import MagicMock, patch
import pytest


def test_build_report_returns_dict():
    from src.reports.daily_report import build_report
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    report = build_report(db, date(2026, 9, 18))
    assert "date" in report
    assert "courses_today" in report
    assert "total_enrolled" in report
    assert "engagement" in report
    assert "reminders" in report


def test_build_report_with_courses():
    from src.reports.daily_report import build_report
    db = MagicMock()
    
    course_id = "course-1"
    enr_id = "enr-1"
    
    # Setup mock responses for each table query
    mock_courses = MagicMock()
    mock_courses.data = [{"id": course_id, "name": "Test Course"}]
    
    mock_enrollments = MagicMock()
    mock_enrollments.data = [{"id": enr_id, "status": "active"}]
    
    mock_engagement = MagicMock()
    mock_engagement.data = [{"status": "active"}]
    
    mock_reminders = MagicMock()
    mock_reminders.data = [{"delivery_status": "sent"}]
    
    # Track call counts to return appropriate mock
    call_counts = {"courses": 0, "enrollments": 0, "engagement_log": 0, "reminder_log": 0}
    
    def table_side_effect(table_name):
        mock = MagicMock()
        if table_name == "courses":
            mock.select.return_value.eq.return_value.execute.return_value = mock_courses
        elif table_name == "enrollments":
            mock.select.return_value.eq.return_value.execute.return_value = mock_enrollments
        elif table_name == "engagement_log":
            mock.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_engagement
        elif table_name == "reminder_log":
            mock.select.return_value.gte.return_value.lt.return_value.execute.return_value = mock_reminders
        return mock
    
    db.table.side_effect = table_side_effect
    
    report = build_report(db, date(2026, 9, 18))
    assert report["courses_today"] == 1
    assert report["total_enrolled"] == 1
    assert report["engagement"]["active"] == 1
    assert report["reminders"]["sent"] == 1


def test_build_report_engagement_counts():
    from src.reports.daily_report import build_report
    db = MagicMock()
    
    course_id = "course-1"
    enr_ids = ["enr-1", "enr-2", "enr-3"]
    
    mock_courses = MagicMock()
    mock_courses.data = [{"id": course_id, "name": "Test Course"}]
    
    mock_enrollments = MagicMock()
    mock_enrollments.data = [{"id": eid, "status": "active"} for eid in enr_ids]
    
    # Each enrollment gets a different engagement status
    engagement_responses = [
        MagicMock(data=[{"status": "active"}]),
        MagicMock(data=[{"status": "low_engagement"}]),
        MagicMock(data=[{"status": "needs_followup"}]),
    ]
    
    mock_reminders = MagicMock()
    mock_reminders.data = [
        {"delivery_status": "sent"},
        {"delivery_status": "failed"},
        {"delivery_status": "sent"},
    ]
    
    engagement_call_count = [0]
    
    def make_engagement_mock():
        idx = engagement_call_count[0]
        engagement_call_count[0] += 1
        return engagement_responses[idx % 3]
    
    def table_side_effect(table_name):
        mock = MagicMock()
        if table_name == "courses":
            mock.select.return_value.eq.return_value.execute.return_value = mock_courses
        elif table_name == "enrollments":
            mock.select.return_value.eq.return_value.execute.return_value = mock_enrollments
        elif table_name == "engagement_log":
            mock.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = make_engagement_mock
        elif table_name == "reminder_log":
            mock.select.return_value.gte.return_value.lt.return_value.execute.return_value = mock_reminders
        return mock
    
    db.table.side_effect = table_side_effect
    
    report = build_report(db, date(2026, 9, 18))
    assert report["engagement"]["active"] == 1
    assert report["engagement"]["low_engagement"] == 1
    assert report["engagement"]["needs_followup"] == 1
    assert report["reminders"]["sent"] == 2
    assert report["reminders"]["failed"] == 1


def test_send_report_to_admin_no_phone():
    from src.reports.daily_report import send_report_to_admin
    from unittest.mock import patch
    
    with patch('src.reports.daily_report.get_settings') as mock_settings:
        mock_settings.return_value.admin_phone = ""
        mock_settings.return_value.admin_email = "test@example.com"
        
        report = {"date": "2026-09-18", "courses_today": 1, "total_enrolled": 5, "engagement": {"active": 3, "low_engagement": 1, "needs_followup": 1}, "reminders": {"sent": 4, "failed": 1}}
        result = send_report_to_admin(report)
        assert result is False


def test_send_report_to_admin_with_phone():
    from src.reports.daily_report import send_report_to_admin
    from unittest.mock import patch, MagicMock
    
    with patch('src.reports.daily_report.get_settings') as mock_settings:
        mock_settings.return_value.admin_phone = "+233548014157"
        mock_settings.return_value.admin_email = "test@example.com"
        
        with patch('src.channels.base.get_channel') as mock_get_channel:
            mock_channel = MagicMock()
            mock_channel.send.return_value = True
            mock_get_channel.return_value = mock_channel
            
            report = {"date": "2026-09-18", "courses_today": 1, "total_enrolled": 5, "engagement": {"active": 3, "low_engagement": 1, "needs_followup": 1}, "reminders": {"sent": 4, "failed": 1}}
            result = send_report_to_admin(report)
            assert result is True
            mock_channel.send.assert_called_once()