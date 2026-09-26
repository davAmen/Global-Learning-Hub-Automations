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
    def send(self, student, message: str) -> bool:
        """Send a message. Return True on success, False on failure."""
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
    enrollment_id: UUID | str,
) -> bool:
    """Log a pending student-message attempt before contacting its channel."""
    attempt_id = str(uuid4())
    recipient = getattr(student, "name", "student")

    try:
        db.table("reminder_log").insert(
            {
                "id": attempt_id,
                "enrollment_id": str(enrollment_id),
                "channel": channel.name,
                "message": message,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "delivery_status": "pending",
            }
        ).execute()
    except Exception:
        logger.exception("Could not record the send attempt; message was not sent.")
        return False

    logger.info(f"Attempting {channel.name} message to {recipient}.")
    try:
        sent = channel.send(student, message)
    except Exception:
        logger.exception(f"{channel.name} send raised an error for {recipient}.")
        sent = False

    try:
        db.table("reminder_log").update(
            {"delivery_status": "sent" if sent else "failed"}
        ).eq("id", attempt_id).execute()
    except Exception:
        logger.exception(
            f"Could not update the send status for attempt {attempt_id}; it remains pending."
        )

    if sent:
        logger.info(f"Message sent to {recipient} via {channel.name}.")
    else:
        logger.error(f"Message failed for {recipient} via {channel.name}.")
    return sent
