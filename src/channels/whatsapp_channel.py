"""WhatsApp channel - Phase 1 ACTIVE.

Uses the WhatsApp Business Cloud API (Meta).
All credentials come from the environment - never hardcoded.
"""

from __future__ import annotations

import re

import httpx

from src.channels.base import Channel
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppChannel(Channel):
    name = "whatsapp"

    def send(self, student, message: str) -> bool | None:
        phone = getattr(student, "phone", None)
        if not isinstance(phone, str) or not phone.strip():
            logger.error("WhatsApp recipient is missing a phone number.")
            return False

        settings = get_settings()
        if not all(
            (
                settings.whatsapp_token,
                settings.whatsapp_phone_id,
                settings.whatsapp_api_version,
                settings.whatsapp_template_name,
                settings.whatsapp_template_language,
            )
        ):
            logger.error("WhatsApp credentials, API version, and approved template are required.")
            return False
        if not re.fullmatch(r"v\d+\.0", settings.whatsapp_api_version):
            logger.error("WhatsApp API version must use the form vNN.0.")
            return False

        url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {settings.whatsapp_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone.strip(),
            "type": "template",
            "template": {
                "name": settings.whatsapp_template_name,
                "language": {"code": settings.whatsapp_template_language},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": message}],
                    }
                ],
            },
        }
        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            response_data = r.json()
            messages = response_data.get("messages") if isinstance(response_data, dict) else None
            if (
                not isinstance(messages, list)
                or not messages
                or not isinstance(messages[0], dict)
                or not messages[0].get("id")
            ):
                logger.warning("WhatsApp response did not confirm acceptance with a message ID.")
                return None
            logger.info("WhatsApp request accepted by provider.")
            return True
        except httpx.HTTPStatusError as exc:
            logger.error("WhatsApp request failed with HTTP status %s.", exc.response.status_code)
            return None if exc.response.status_code >= 500 else False
        except httpx.HTTPError as exc:
            logger.warning("WhatsApp request outcome is unknown (%s).", type(exc).__name__)
            return None
        except ValueError:
            logger.warning("WhatsApp returned an unreadable response; outcome is unknown.")
            return None
