"""Tests for the scheduler module."""

from datetime import date, time
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from uuid import uuid4


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


def test_already_sent_course_true():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = [{"id": "x"}]
    from src.automation.scheduler import already_sent_course
    assert already_sent_course(db, str(uuid4()), date(2026, 9, 18)) is True


def test_already_sent_course_false():
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = []
    from src.automation.scheduler import already_sent_course
    assert already_sent_course(db, str(uuid4()), date(2026, 9, 18)) is False


def test_classes_today():
    db = MagicMock()
    course_id = str(uuid4())
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
        "id": course_id,
        "name": "Test Course",
        "start_date": date.today().isoformat(),
        "class_time": "09:00:00",
        "timezone": "GMT",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00"
    }]
    from src.automation.scheduler import classes_today
    courses = classes_today(db)
    assert len(courses) == 1
    assert courses[0].name == "Test Course"


def test_active_enrollments():
    db = MagicMock()
    enrollment_id = str(uuid4())
    student_id = str(uuid4())
    course_id = str(uuid4())
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
        "id": enrollment_id,
        "student_id": student_id,
        "course_id": course_id,
        "status": "active",
        "enrolled_at": "2026-01-01T00:00:00"
    }]
    from src.automation.scheduler import active_enrollments
    enrollments = active_enrollments(db, uuid4())
    assert len(enrollments) == 1
    assert enrollments[0].status == "active"


def test_build_reminder_queue():
    db = MagicMock()
    course_id = str(uuid4())
    enrollment_id = str(uuid4())
    student_id = str(uuid4())
    
    # Track which query is being made
    query_type = []
    
    def table_side_effect(table_name):
        mock = MagicMock()
        if table_name == "courses":
            mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
                "id": course_id,
                "name": "Test Course",
                "start_date": date.today().isoformat(),
                "class_time": "09:00:00",
                "timezone": "GMT",
                "is_active": True,
                "created_at": "2026-01-01T00:00:00"
            }]
        elif table_name == "enrollments":
            mock.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [{
                "id": enrollment_id,
                "student_id": student_id,
                "course_id": course_id,
                "status": "active",
                "enrolled_at": "2026-01-01T00:00:00"
            }]
        elif table_name == "reminder_log":
            mock.select.return_value.eq.return_value.gte.return_value.lt.return_value.execute.return_value.data = []
        return mock
    
    db.table.side_effect = table_side_effect
    
    from src.automation.scheduler import build_reminder_queue
    queue = build_reminder_queue(db)
    assert len(queue) == 1


def test_parse_course_time():
    from src.automation.scheduler import parse_course_time
    
    # Test ISO format
    assert parse_course_time("09:00:00") == time(9, 0)
    assert parse_course_time("18:30:00") == time(18, 30)
    
    # Test fallback formats
    assert parse_course_time("9:00") == time(9, 0)
    assert parse_course_time("6:00 PM") == time(18, 0)
    
    # Test invalid format returns default
    assert parse_course_time("invalid") == time(9, 0)


def test_get_gmt_now():
    from src.automation.scheduler import get_gmt_now
    now = get_gmt_now()
    assert now.tzinfo is not None


def test_get_gmt_date():
    from src.automation.scheduler import get_gmt_date
    d = get_gmt_date()
    assert isinstance(d, date)