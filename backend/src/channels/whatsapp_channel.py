"""WhatsApp channel - Phase 1 ACTIVE.

Uses the WasenderAPI (wasenderapi.com).
All credentials come from the environment - never hardcoded.
"""

from __future__ import annotations

import httpx

from src.channels.base import Channel
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppChannel(Channel):
    name = "whatsapp"

    def send(self, student, message: str) -> tuple[bool, str | None]:
        """Send a message. Returns (success, external_message_id)."""
        settings = get_settings()
        if not settings.wasender_api_key:
            logger.error("WasenderAPI not configured (missing WASENDER_API_KEY).")
            return False, None

        url = f"{settings.wasender_base_url}/api/send-message"
        headers = {
            "Authorization": f"Bearer {settings.wasender_api_key}",
            "Content-Type": "application/json",
        }
        to_number = student.phone.strip()
        if not to_number.startswith("+"):
            to_number = "+" + to_number.lstrip("+")
        payload = {
            "to": to_number,
            "text": message,
        }
        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=15)
            if r.status_code != 200:
                logger.error(f"WasenderAPI error {r.status_code}: {r.text}")
            r.raise_for_status()
            data = r.json()
            external_msg_id = str(data.get("data", {}).get("msgId")) if data.get("success") else None
            logger.info(f"WasenderAPI sent to {student.phone}, msg_id={external_msg_id}")
            return True, external_msg_id
        except httpx.HTTPError as exc:
            logger.error(f"WasenderAPI send failed for {student.phone}: {exc}")
            return False, None