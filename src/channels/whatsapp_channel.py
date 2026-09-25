"""WhatsApp Business Cloud API channel."""

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
        if student is None or not getattr(student, "phone", None):
            logger.error("WhatsApp recipient has no phone number.")
            return False

        url = (
            f"https://graph.facebook.com/{settings.whatsapp_graph_version}/"
            f"{settings.whatsapp_phone_id}/messages"
        )
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
            response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            logger.info("WhatsApp request accepted for %s", student.phone)
            return True
        except httpx.HTTPError as exc:
            logger.error("WhatsApp send failed for %s: %s", student.phone, exc)
            return False
