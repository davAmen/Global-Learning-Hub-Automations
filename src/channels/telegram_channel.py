"""Telegram channel - administrator report destination only.

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

    def send(self, student, message: str) -> bool | None:
        if student is not None:
            logger.error(
                "Telegram learner reminder blocked: only an administrator chat is configured."
            )
            return False

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
            response_data = r.json()
            result = response_data.get("result") if isinstance(response_data, dict) else None
            if (
                not isinstance(response_data, dict)
                or response_data.get("ok") is not True
                or not isinstance(result, dict)
                or not result.get("message_id")
            ):
                logger.warning("Telegram response did not confirm acceptance with a message ID.")
                return None
            logger.info("Telegram administrator report accepted by provider.")
            return True
        except httpx.HTTPStatusError as exc:
            logger.error("Telegram request failed with HTTP status %s.", exc.response.status_code)
            return None if exc.response.status_code >= 500 else False
        except httpx.HTTPError as exc:
            logger.warning("Telegram request outcome is unknown (%s).", type(exc).__name__)
            return None
        except ValueError:
            logger.warning("Telegram returned an unreadable response; outcome is unknown.")
            return None
