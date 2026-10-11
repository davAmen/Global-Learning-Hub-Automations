"""Tests for channel adapters."""

import pytest
import httpx
from unittest.mock import MagicMock, patch, AsyncMock
from src.channels.base import get_channel, Channel
from src.channels.whatsapp_channel import WhatsAppChannel, WasenderAPIError
from src.channels.telegram_channel import TelegramChannel
from src.channels.email_channel import EmailChannel
from src.channels.sms_channel import SMSChannel

pytestmark = pytest.mark.asyncio


def test_get_channel_whatsapp():
    ch = get_channel("whatsapp")
    assert ch.name == "whatsapp"


def test_get_channel_telegram():
    ch = get_channel("telegram")
    assert ch.name == "telegram"


def test_get_channel_email():
    ch = get_channel("email")
    assert ch.name == "email"


def test_get_channel_sms():
    ch = get_channel("sms")
    assert ch.name == "sms"


def test_get_channel_invalid():
    with pytest.raises(ValueError):
        get_channel("carrier_pigeon")


async def test_whatsapp_channel_validate_recipient_phone():
    ch = WhatsAppChannel()
    # Valid E.164
    assert ch.validate_recipient("+233548014157") == "+233548014157"
    # Without +
    assert ch.validate_recipient("233548014157") == "+233548014157"
    # With spaces/dashes
    assert ch.validate_recipient("+233 548 014 157") == "+233548014157"
    assert ch.validate_recipient("+233-548-014-157") == "+233548014157"


async def test_whatsapp_channel_validate_recipient_group():
    ch = WhatsAppChannel()
    # Group JID
    assert ch.validate_recipient("120363418173591450@g.us") == "120363418173591450@g.us"
    assert ch.validate_recipient("12345@s.whatsapp.net") == "12345@s.whatsapp.net"
    assert ch.validate_recipient("12345@lid") == "12345@lid"


async def test_whatsapp_channel_validate_recipient_invalid():
    ch = WhatsAppChannel()
    with pytest.raises(ValueError):
        ch.validate_recipient("")
    with pytest.raises(ValueError):
        ch.validate_recipient("invalid")


async def test_whatsapp_channel_send_success():
    # Patch settings before creating channel
    with patch('src.channels.whatsapp_channel.get_settings') as mock_settings:
        mock_settings.return_value.wasender_api_key = "test_key"
        mock_settings.return_value.wasender_base_url = "https://www.wasenderapi.com"
        ch = WhatsAppChannel()
        
        # Mock the HTTP client
        with patch.object(ch, '_get_client', new_callable=AsyncMock) as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "data": {"msgId": "msg_123"}}
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            
            ok, msg_id = await ch.send(recipient="+233548014157", message="Test message")
            assert ok is True
            assert msg_id == "msg_123"


async def test_whatsapp_channel_send_failure():
    with patch('src.channels.whatsapp_channel.get_settings') as mock_settings:
        mock_settings.return_value.wasender_api_key = "test_key"
        mock_settings.return_value.wasender_base_url = "https://www.wasenderapi.com"
        ch = WhatsAppChannel()
        
        with patch.object(ch, '_get_client', new_callable=AsyncMock) as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
    
            ok, msg_id = await ch.send(recipient="+233548014157", message="Test message")
            assert ok is False
            assert msg_id is None


async def test_whatsapp_channel_send_rate_limited():
    with patch('src.channels.whatsapp_channel.get_settings') as mock_settings:
        mock_settings.return_value.wasender_api_key = "test_key"
        mock_settings.return_value.wasender_base_url = "https://www.wasenderapi.com"
        ch = WhatsAppChannel()
        
        with patch.object(ch, '_get_client', new_callable=AsyncMock) as mock_client:
            # First call: rate limited (429)
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429
            mock_response_429.headers = {"Retry-After": "1"}
            
            # Second call: success
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"success": True, "data": {"msgId": "msg_123"}}
            
            mock_client.return_value.post = AsyncMock(side_effect=[mock_response_429, mock_response_200])
            
            ok, msg_id = await ch.send(recipient="+233548014157", message="Test message", retries=2)
            assert ok is True
            assert msg_id == "msg_123"


def test_telegram_channel_not_configured():
    ch = TelegramChannel()
    # Should return False when not configured
    assert ch.send(None, "test") is False


def test_email_channel_not_configured():
    ch = EmailChannel()
    assert ch.send(None, "test") is False


def test_sms_channel_not_configured():
    ch = SMSChannel()
    assert ch.send(None, "test") is False


class TestChannelInterface:
    """Test that all channels implement the Channel interface."""
    
    def test_all_channels_have_name(self):
        for name in ["whatsapp", "telegram", "email", "sms"]:
            ch = get_channel(name)
            assert hasattr(ch, 'name')
            assert ch.name == name
    
    def test_all_channels_have_send_method(self):
        for name in ["whatsapp", "telegram", "email", "sms"]:
            ch = get_channel(name)
            assert hasattr(ch, 'send')
            assert callable(ch.send)
    
    def test_all_channels_have_send_sync_method(self):
        for name in ["whatsapp", "telegram", "email", "sms"]:
            ch = get_channel(name)
            assert hasattr(ch, 'send_sync')
            assert callable(ch.send_sync)