"""Tests for channel adapters."""

import pytest
import httpx
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
        assert attempt["idempotency_key"] == "reminder:enrollment-1:2026-09-18"
        return True

    channel.send.side_effect = send

    assert send_and_log(
        db,
        channel,
        student,
        "Sample reminder",
        "enrollment-1",
        idempotency_key="reminder:enrollment-1:2026-09-18",
    ) is True

    channel.send.assert_called_once_with(student, "Sample reminder")
    db.table.return_value.update.assert_called_once_with({"delivery_status": "sent"})


def test_send_and_log_does_not_send_when_attempt_cannot_be_logged(caplog):
    db = MagicMock()
    db.table.return_value.insert.return_value.execute.side_effect = RuntimeError(
        "synthetic-private-database-detail"
    )
    channel = MagicMock()
    channel.name = "whatsapp"
    student = SimpleNamespace(name="Sample Student", phone="+15555550101")

    assert send_and_log(
        db,
        channel,
        student,
        "Sample reminder",
        "enrollment-1",
        idempotency_key="reminder:enrollment-1:2026-09-18",
    ) is False

    channel.send.assert_not_called()
    assert "RuntimeError" in caplog.text
    assert "synthetic-private-database-detail" not in caplog.text


def test_send_and_log_keeps_uncertain_provider_result_pending():
    db = MagicMock()
    channel = MagicMock()
    channel.name = "whatsapp"
    channel.send.return_value = None

    assert send_and_log(
        db,
        channel,
        SimpleNamespace(phone="+15555550101"),
        "Sample reminder",
        "enrollment-1",
        idempotency_key="reminder:enrollment-1:2026-09-18",
    ) is False

    db.table.return_value.update.assert_called_once_with({"delivery_status": "pending"})


def test_send_and_log_does_not_resend_when_unique_key_is_already_claimed(caplog):
    db = MagicMock()
    db.table.return_value.insert.return_value.execute.side_effect = [
        None,
        RuntimeError("duplicate idempotency key"),
    ]
    channel = MagicMock()
    channel.name = "whatsapp"
    channel.send.return_value = True
    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    key = "reminder:enrollment-1:2026-09-18"

    assert send_and_log(db, channel, student, "Sample reminder", "enrollment-1", idempotency_key=key)
    assert not send_and_log(db, channel, student, "Sample reminder", "enrollment-1", idempotency_key=key)

    assert channel.send.call_count == 1
    assert "Synthetic Learner" not in caplog.text
    assert db.table.return_value.insert.call_args.args[0]["idempotency_key"] == key


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


def test_whatsapp_uses_a_configured_approved_template_and_api_version():
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    settings = SimpleNamespace(
        whatsapp_token="test-token",
        whatsapp_phone_id="test-phone-id",
        whatsapp_api_version="v26.0",
        whatsapp_template_name="class_reminder",
        whatsapp_template_language="en_GB",
    )
    response = MagicMock()
    response.json.return_value = {"messages": [{"id": "wamid.synthetic"}]}

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post", return_value=response
    ) as post:
        assert WhatsAppChannel().send(student, "Your class is today at 09:00.") is True

    assert post.call_args.args[0] == (
        "https://graph.facebook.com/v26.0/test-phone-id/messages"
    )
    payload = post.call_args.kwargs["json"]
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "class_reminder"
    assert payload["template"]["language"] == {"code": "en_GB"}
    assert payload["template"]["components"][0]["parameters"] == [
        {"type": "text", "text": "Your class is today at 09:00."}
    ]


def test_whatsapp_fails_closed_without_template_or_supported_api_version():
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    settings = SimpleNamespace(
        whatsapp_token="test-token",
        whatsapp_phone_id="test-phone-id",
        whatsapp_api_version="",
        whatsapp_template_name="",
        whatsapp_template_language="en_US",
    )

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post"
    ) as post:
        assert WhatsAppChannel().send(student, "Do not send free-form text") is False

    post.assert_not_called()


def test_whatsapp_requires_provider_message_id_even_for_http_success():
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    settings = SimpleNamespace(
        whatsapp_token="test-token",
        whatsapp_phone_id="test-phone-id",
        whatsapp_api_version="v26.0",
        whatsapp_template_name="class_reminder",
        whatsapp_template_language="en_US",
    )
    response = MagicMock()
    response.json.return_value = {"messages": []}

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post", return_value=response
    ):
        assert WhatsAppChannel().send(student, "Hello") is None


@pytest.mark.parametrize("body", [{"messages": [None]}, {"messages": [{}]}, {}])
def test_whatsapp_unreadable_acceptance_response_is_unknown(body):
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    settings = SimpleNamespace(
        whatsapp_token="test-token",
        whatsapp_phone_id="test-phone-id",
        whatsapp_api_version="v26.0",
        whatsapp_template_name="class_reminder",
        whatsapp_template_language="en_US",
    )
    response = MagicMock()
    response.json.return_value = body

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post", return_value=response
    ):
        assert WhatsAppChannel().send(student, "Hello") is None


def test_whatsapp_timeout_is_unknown_not_a_definite_failure():
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    settings = SimpleNamespace(
        whatsapp_token="test-token",
        whatsapp_phone_id="test-phone-id",
        whatsapp_api_version="v26.0",
        whatsapp_template_name="class_reminder",
        whatsapp_template_language="en_US",
    )

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post", side_effect=httpx.ReadTimeout("timeout")
    ):
        assert WhatsAppChannel().send(student, "Hello") is None


def test_whatsapp_provider_server_error_is_unknown():
    from src.channels.whatsapp_channel import WhatsAppChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    settings = SimpleNamespace(
        whatsapp_token="test-token",
        whatsapp_phone_id="test-phone-id",
        whatsapp_api_version="v26.0",
        whatsapp_template_name="class_reminder",
        whatsapp_template_language="en_US",
    )
    response = httpx.Response(
        503, request=httpx.Request("POST", "https://graph.facebook.com/test/messages")
    )

    with patch("src.channels.whatsapp_channel.get_settings", return_value=settings), patch(
        "src.channels.whatsapp_channel.httpx.post", return_value=response
    ):
        assert WhatsAppChannel().send(student, "Hello") is None


def test_telegram_never_sends_a_student_reminder_to_the_admin_chat():
    from src.channels.telegram_channel import TelegramChannel

    student = SimpleNamespace(name="Synthetic Learner", phone="+15555550101")
    with patch("src.channels.telegram_channel.httpx.post") as post:
        assert TelegramChannel().send(student, "Student-specific reminder") is False

    post.assert_not_called()


def test_configuration_does_not_allow_telegram_as_a_student_reminder_channel():
    from pydantic import ValidationError
    from src.config import Settings

    with pytest.raises(ValidationError):
        Settings(_env_file=None, active_channel="telegram")


def test_telegram_timeout_is_unknown_not_a_definite_failure():
    from src.channels.telegram_channel import TelegramChannel

    settings = SimpleNamespace(
        telegram_bot_token="test-token",
        telegram_admin_chat_id="test-chat",
    )

    with patch("src.channels.telegram_channel.get_settings", return_value=settings), patch(
        "src.channels.telegram_channel.httpx.post", side_effect=httpx.ReadTimeout("timeout")
    ):
        assert TelegramChannel().send(None, "Daily report") is None
