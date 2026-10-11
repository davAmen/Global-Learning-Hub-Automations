"""Tests for IELTS reminder module."""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

pytestmark = pytest.mark.asyncio


def test_build_ielts_reminder_before_start():
    from src.automation.ielts_reminder import build_ielts_reminder
    from unittest.mock import patch
    
    with patch('src.automation.ielts_reminder.get_settings') as mock_settings:
        mock_settings.return_value.ielts_course_name = "IELTS Test Course"
        mock_settings.return_value.ielts_start_date = "2026-10-15"
        mock_settings.return_value.ielts_end_date = "2026-10-30"
        mock_settings.return_value.ielts_class_time = "18:00-20:00 GMT"
        mock_settings.return_value.ielts_currency = "GHS"
        mock_settings.return_value.ielts_amount = 100.0
        mock_settings.return_value.ielts_reference = "ILETS"
        mock_settings.return_value.ielts_momo_number = "+233548014157"
        mock_settings.return_value.ielts_telecel_number = "+23333206967251"
        mock_settings.return_value.ielts_proof_group_url = "https://chat.whatsapp.com/test1"
        mock_settings.return_value.ielts_class_access_group_url = "https://chat.whatsapp.com/test2"
        
        # Before start date
        message = build_ielts_reminder(date(2026, 10, 10))
        assert "STARTS IN 5 DAYS" in message
        assert "IELTS TEST COURSE" in message  # Uppercased in template
        assert "GHS 100.00" in message
        assert "ILETS" in message
        assert "+233548014157" in message
        assert "https://chat.whatsapp.com/test1" in message
        assert "https://chat.whatsapp.com/test2" in message


def test_build_ielts_reminder_during_course():
    from src.automation.ielts_reminder import build_ielts_reminder
    from unittest.mock import patch
    
    with patch('src.automation.ielts_reminder.get_settings') as mock_settings:
        mock_settings.return_value.ielts_course_name = "IELTS Test Course"
        mock_settings.return_value.ielts_start_date = "2026-10-15"
        mock_settings.return_value.ielts_end_date = "2026-10-30"
        mock_settings.return_value.ielts_class_time = "18:00-20:00 GMT"
        mock_settings.return_value.ielts_currency = "GHS"
        mock_settings.return_value.ielts_amount = 100.0
        mock_settings.return_value.ielts_reference = "ILETS"
        mock_settings.return_value.ielts_momo_number = "+233548014157"
        mock_settings.return_value.ielts_telecel_number = "+23333206967251"
        mock_settings.return_value.ielts_proof_group_url = "https://chat.whatsapp.com/test1"
        mock_settings.return_value.ielts_class_access_group_url = "https://chat.whatsapp.com/test2"
        
        # Day 1 of course
        message = build_ielts_reminder(date(2026, 10, 15))
        assert "DAY 1 OF 16" in message
        
        # Last day of course
        message = build_ielts_reminder(date(2026, 10, 30))
        assert "DAY 16 OF 16" in message


def test_build_ielts_reminder_after_course():
    from src.automation.ielts_reminder import build_ielts_reminder
    from unittest.mock import patch
    
    with patch('src.automation.ielts_reminder.get_settings') as mock_settings:
        mock_settings.return_value.ielts_course_name = "IELTS Test Course"
        mock_settings.return_value.ielts_start_date = "2026-10-15"
        mock_settings.return_value.ielts_end_date = "2026-10-30"
        mock_settings.return_value.ielts_class_time = "18:00-20:00 GMT"
        mock_settings.return_value.ielts_currency = "GHS"
        mock_settings.return_value.ielts_amount = 100.0
        mock_settings.return_value.ielts_reference = "ILETS"
        mock_settings.return_value.ielts_momo_number = "+233548014157"
        mock_settings.return_value.ielts_telecel_number = "+23333206967251"
        mock_settings.return_value.ielts_proof_group_url = "https://chat.whatsapp.com/test1"
        mock_settings.return_value.ielts_class_access_group_url = "https://chat.whatsapp.com/test2"
        
        # After course
        message = build_ielts_reminder(date(2026, 11, 1))
        assert "ENDED" in message


async def test_create_approval_for_reminder():
    from src.automation.ielts_reminder import create_approval_for_reminder
    
    db = MagicMock()
    db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])
    
    approval_id = await create_approval_for_reminder(db, "Test message", "group@g.us", "course-1")
    
    assert approval_id is not None
    db.table.return_value.insert.assert_called_once()
    call_args = db.table.return_value.insert.call_args[0][0]
    assert call_args["action_type"] == "send_message"
    assert call_args["target_group_jid"] == "group@g.us"
    assert call_args["target_course_id"] == "course-1"
    assert call_args["requested_by"] == "agent"
    assert call_args["status"] == "pending"


async def test_send_ielts_reminder_now():
    from src.automation.ielts_reminder import send_ielts_reminder_now
    from unittest.mock import patch, AsyncMock
    
    with patch('src.automation.ielts_reminder.get_db') as mock_get_db, \
         patch('src.automation.ielts_reminder.get_settings') as mock_settings, \
         patch('src.automation.ielts_reminder.get_channel') as mock_get_channel, \
         patch('src.automation.ielts_reminder.build_ielts_reminder') as mock_build:
        
        # Mock database
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{"id": "course-1"}]
        mock_get_db.return_value = mock_db
        
        # Mock settings
        mock_settings.return_value.ielts_course_name = "IELTS Test"
        mock_settings.return_value.ielts_announcement_group_jid = "group@g.us"
        
        # Mock channel
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(return_value=(True, "msg_123"))
        mock_get_channel.return_value = mock_channel
        
        # Mock build_ielts_reminder
        mock_build.return_value = "Test reminder message"
        
        result = await send_ielts_reminder_now()
        
        assert result is True
        mock_channel.send.assert_called_once_with(recipient="group@g.us", message="Test reminder message")


async def test_send_ielts_reminder_scheduled_disabled():
    from src.automation.ielts_reminder import send_ielts_reminder_scheduled
    from unittest.mock import patch
    
    with patch('src.automation.ielts_reminder.get_settings') as mock_settings:
        mock_settings.return_value.enable_ielts_reminders = False
        
        result = await send_ielts_reminder_scheduled()
        assert result is True


async def test_send_ielts_reminder_scheduled_no_course():
    from src.automation.ielts_reminder import send_ielts_reminder_scheduled
    from unittest.mock import patch
    
    with patch('src.automation.ielts_reminder.get_db') as mock_get_db, \
         patch('src.automation.ielts_reminder.get_settings') as mock_settings:
        
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        mock_get_db.return_value = mock_db
        
        mock_settings.return_value.enable_ielts_reminders = True
        mock_settings.return_value.ielts_course_name = "IELTS Test"
        
        result = await send_ielts_reminder_scheduled()
        assert result is False