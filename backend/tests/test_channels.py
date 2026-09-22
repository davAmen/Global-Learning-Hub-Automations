"""Tests for channel adapters."""

import pytest
from unittest.mock import MagicMock, patch
from src.channels.base import get_channel


def test_get_channel_whatsapp():
    ch = get_channel("whatsapp")
    assert ch.name == "whatsapp"


def test_get_channel_telegram():
    ch = get_channel("telegram")
    assert ch.name == "telegram"


def test_get_channel_invalid():
    with pytest.raises(ValueError):
        get_channel("carrier_pigeon")
