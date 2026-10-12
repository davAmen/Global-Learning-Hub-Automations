"""Channel adapter base class.

Every delivery channel implements this exact interface. The scheduler never
imports a concrete channel - it only calls channel.send(student, message).
"""

from __future__ import annotations

import abc
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.utils.logger import get_logger

logger = get_logger(__name__)


class Channel(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def send(self, student, message: str) -> bool | None:
        """Return True if accepted, False if rejected, or None if outcome is unknown."""
        raise NotImplementedError


def get_channel(name: str) -> Channel:
    """Return the channel instance for the given name."""
    from src.channels.whatsapp_channel import WhatsAppChannel
    from src.channels.telegram_channel import TelegramChannel
    from src.channels.email_channel import EmailChannel
    from src.channels.sms_channel import SMSChannel

    channels = {
        "whatsapp": WhatsAppChannel,
        "telegram": TelegramChannel,
        "email": EmailChannel,
        "sms": SMSChannel,
    }
    if name not in channels:
        raise ValueError(f"Channel '{name}' is not configured.")
    return channels[name]()


def send_and_log(
    db: Any,
    channel: Channel,
    student: Any,
    message: str,
    enrollment_id: UUID | str | None,
    *,
    idempotency_key: str,
) -> bool:
    """Claim and log one idempotent send attempt before contacting its channel."""
    attempt_id = str(uuid4())

    try:
        db.table("reminder_log").insert(
            {
                "id": attempt_id,
                "enrollment_id": str(enrollment_id) if enrollment_id is not None else None,
                "channel": channel.name,
                "message": message,
                "idempotency_key": idempotency_key,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "delivery_status": "pending",
            }
        ).execute()
    except Exception as exc:
        logger.error(
            "Could not claim/log send attempt %s (%s); message was not sent.",
            attempt_id,
            type(exc).__name__,
        )
        return False

    logger.info("Attempting %s message (attempt %s).", channel.name, attempt_id)
    try:
        outcome = channel.send(student, message)
    except Exception as exc:
        logger.error("%s send raised %s (attempt %s).", channel.name, type(exc).__name__, attempt_id)
        outcome = None

    delivery_status = (
        "sent" if outcome is True else "failed" if outcome is False else "pending"
    )

    try:
        db.table("reminder_log").update(
            {"delivery_status": delivery_status}
        ).eq("id", attempt_id).execute()
    except Exception as exc:
        logger.error(
            "Could not update send status for attempt %s (%s); it remains pending.",
            attempt_id,
            type(exc).__name__,
        )

    if outcome is True:
        logger.info("Provider accepted %s attempt %s.", channel.name, attempt_id)
    elif outcome is False:
        logger.error("%s attempt %s failed.", channel.name, attempt_id)
    else:
        logger.warning("%s attempt %s has an unknown outcome; do not retry automatically.", channel.name, attempt_id)
    return outcome is True
