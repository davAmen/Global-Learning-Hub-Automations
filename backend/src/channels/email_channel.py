"""Email channel - NOT WIRED in Phase 1.

Exists for the channel-adapter interface. Do not wire without updating
DECISIONS.md first.
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from src.channels.base import Channel
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmailChannel(Channel):
    name = "email"

    def send(self, student, message: str) -> bool:
        settings = get_settings()
        if not (settings.smtp_host and settings.smtp_username and settings.smtp_password):
            logger.error("Email not configured.")
            return False
        msg = MIMEText(message)
        msg["Subject"] = "Global Learning Hub - Reminder"
        msg["From"] = settings.smtp_username
        msg["To"] = student.email or ""
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            logger.info(f"Email sent to {student.email}")
            return True
        except Exception as exc:
            logger.error(f"Email send failed for {student.email}: {exc}")
            return False
