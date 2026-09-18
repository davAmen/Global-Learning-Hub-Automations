"""Telegram channel - backup to WhatsApp (operator's @DavidAmenuku20).

Posting via the Bot API requires a bot token from @BotFather.
Secrets come from the environment - never hardcoded.
"""

from __future__ import annotations

import httpx

from src.channels.base import Channel
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TelegramChannel(Channel):
    name = "telegram"

    def send(self, student, message: str) -> bool:
        settings = get_settings()
        token = settings.telegram_bot_token
        chat_id = settings.telegram_admin_chat_id
        if not (token and chat_id):
            logger.error("Telegram not configured.")
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            r = httpx.post(url, json={"chat_id": chat_id, "text": message}, timeout=15)
            r.raise_for_status()
            logger.info("Telegram backup post sent.")
            return True
        except httpx.HTTPError as exc:
            logger.error(f"Telegram send failed: {exc}")
            return False
