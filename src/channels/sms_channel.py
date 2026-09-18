"""SMS channel - NOT WIRED in Phase 1.

Exists for the channel-adapter interface. Do not wire without updating
DECISIONS.md first.
"""

from __future__ import annotations

from src.channels.base import Channel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SMSChannel(Channel):
    name = "sms"

    def send(self, student, message: str) -> bool:
        logger.error("SMS channel is not wired in Phase 1.")
        return False
