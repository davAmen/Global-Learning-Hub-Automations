"""WhatsApp channel - Phase 1 ACTIVE.

Uses the WhatsApp Business Cloud API (Meta).
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

    def send(self, student, message: str) -> bool:
        settings = get_settings()
        if not (settings.whatsapp_token and settings.whatsapp_phone_id):
            logger.error("WhatsApp not configured.")
            return False

        url = f"https://graph.facebook.com/v20.0/{settings.whatsapp_phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": student.phone,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            logger.info(f"WhatsApp sent to {student.phone}")
            return True
        except httpx.HTTPError as exc:
            logger.error(f"WhatsApp send failed for {student.phone}: {exc}")
            return False
