"""Channel adapter base class.

Every delivery channel implements this exact interface. The scheduler never
imports a concrete channel - it only calls channel.send(student, message).
"""

from __future__ import annotations

import abc
from typing import Optional


class Channel(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def send(
        self,
        recipient: str,
        message: str,
        *,
        retries: int = 3,
        backoff: float = 2.0,
    ) -> tuple[bool, Optional[str]]:
        """
        Send a message asynchronously.
        
        Args:
            recipient: Phone number in E.164 format or group JID
            message: Message text
            retries: Number of retry attempts
            backoff: Exponential backoff factor
            
        Returns:
            Tuple of (success, external_message_id)
        """
        raise NotImplementedError

    # Backward compatibility
    def send_sync(self, student, message: str) -> tuple[bool, Optional[str]]:
        """Synchronous wrapper for backward compatibility."""
        import asyncio
        return asyncio.run(self.send(recipient=student.phone, message=message))


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