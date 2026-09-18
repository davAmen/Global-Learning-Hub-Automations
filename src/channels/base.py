"""Channel adapter base class.

Every delivery channel implements this exact interface. The scheduler never
imports a concrete channel - it only calls channel.send(student, message).
"""

from __future__ import annotations

import abc


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
