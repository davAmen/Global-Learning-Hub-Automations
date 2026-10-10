"""Tests for channel adapters."""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from src.channels.base import get_channel, send_and_log


def test_get_channel_whatsapp():
    ch = get_channel("whatsapp")
    assert ch.name == "whatsapp"


def test_get_channel_telegram():
    ch = get_channel("telegram")
    assert ch.name == "telegram"


def test_get_channel_invalid():
    with pytest.raises(ValueError):
        get_channel("carrier_pigeon")


def test_send_and_log_records_pending_before_sending():
    db = MagicMock()
    channel = MagicMock()
    channel.name = "whatsapp"
    student = SimpleNamespace(name="Sample Student", phone="+15555550101")

    def send(student, message):
        attempt = db.table.return_value.insert.call_args.args[0]
        assert attempt["delivery_status"] == "pending"
        assert attempt["enrollment_id"] == "enrollment-1"
        return True

    channel.send.side_effect = send

    assert send_and_log(db, channel, student, "Sample reminder", "enrollment-1") is True

    channel.send.assert_called_once_with(student, "Sample reminder")
    db.table.return_value.update.assert_called_once_with({"delivery_status": "sent"})


def test_send_and_log_does_not_send_when_attempt_cannot_be_logged():
    db = MagicMock()
    db.table.return_value.insert.return_value.execute.side_effect = RuntimeError(
        "database unavailable"
    )
    channel = MagicMock()
    channel.name = "whatsapp"
    student = SimpleNamespace(name="Sample Student", phone="+15555550101")

    assert send_and_log(db, channel, student, "Sample reminder", "enrollment-1") is False

    channel.send.assert_not_called()


@pytest.mark.parametrize("phone", [None, "", "   "])
def test_whatsapp_without_phone_does_not_call_provider(phone):
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Sample Student", phone=phone)
    settings = SimpleNamespace(whatsapp_token="test-token", whatsapp_phone_id="test-phone-id")

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post"
    ) as post:
        assert WhatsAppChannel().send(student, "Hello") is False

    post.assert_not_called()
