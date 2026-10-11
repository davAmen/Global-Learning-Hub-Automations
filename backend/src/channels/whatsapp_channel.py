"""WhatsApp channel - Phase 1 ACTIVE.

Uses the WasenderAPI (wasenderapi.com).
All credentials come from the environment - never hardcoded.
"""

from __future__ import annotations

import asyncio
import httpx
import re
from typing import Optional

from src.channels.base import Channel
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")  # E.164 format


class WasenderAPIError(Exception):
    """WasenderAPI specific error."""
    def __init__(self, message: str, status_code: int, response: dict):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class WhatsAppChannel(Channel):
    name = "whatsapp"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._settings = get_settings()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def validate_recipient(self, recipient: str) -> str:
        """Validate and normalize recipient (phone number or group JID)."""
        if not recipient:
            raise ValueError("Recipient is required")
        
        # Check if it's a group JID (contains @g.us or @s.whatsapp.net)
        if "@g.us" in recipient or "@s.whatsapp.net" in recipient or "@lid" in recipient:
            return recipient.strip()
        
        # Otherwise treat as phone number
        if not recipient:
            raise ValueError("Recipient is required")
        
        # Remove spaces, dashes, parentheses
        cleaned = re.sub(r"[\s\-\(\)]", "", recipient)
        
        # Ensure starts with +
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned.lstrip("+")
        
        if not PHONE_REGEX.match(cleaned):
            raise ValueError(f"Invalid phone number format: {recipient}")
        
        return cleaned

    async def send(
        self,
        recipient: str,
        message: str,
        *,
        retries: int = 3,
        backoff: float = 2.0,
    ) -> tuple[bool, Optional[str]]:
        """
        Send a message via WasenderAPI.
        
        Args:
            recipient: Phone number in E.164 format or group JID
            message: Message text
            retries: Number of retry attempts
            backoff: Exponential backoff factor
            
        Returns:
            Tuple of (success, external_message_id)
        """
        settings = self._settings
        if not settings.wasender_api_key:
            logger.error("WasenderAPI not configured (missing WASENDER_API_KEY).")
            return False, None

        # Validate recipient
        try:
            to_number = self.validate_recipient(recipient)
        except ValueError as e:
            logger.error(f"Invalid recipient {recipient}: {e}")
            return False, None

        url = f"{settings.wasender_base_url}/api/send-message"
        headers = {
            "Authorization": f"Bearer {settings.wasender_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": to_number,
            "text": message,
        }

        client = await self._get_client()
        
        for attempt in range(retries):
            try:
                r = await client.post(url, headers=headers, json=payload, timeout=15)
                
                if r.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(r.headers.get("Retry-After", backoff * (attempt + 1)))
                    logger.warning(f"Rate limited, waiting {retry_after}s before retry {attempt + 1}/{retries}")
                    await asyncio.sleep(retry_after)
                    continue
                
                if r.status_code >= 500:
                    # Server error - retry
                    logger.warning(f"Server error {r.status_code}, retry {attempt + 1}/{retries}")
                    await asyncio.sleep(backoff * (attempt + 1))
                    continue
                
                if r.status_code != 200:
                    logger.error(f"WasenderAPI error {r.status_code}: {r.text}")
                    r.raise_for_status()
                
                data = r.json()
                if not data.get("success"):
                    logger.error(f"WasenderAPI returned success=false: {data}")
                    return False, None
                
                external_msg_id = str(data.get("data", {}).get("msgId")) if data.get("data") else None
                logger.info(f"WasenderAPI sent to {to_number}, msg_id={external_msg_id}")
                return True, external_msg_id
                
            except httpx.TimeoutException:
                logger.warning(f"Timeout sending to {to_number}, attempt {attempt + 1}/{retries}")
                await asyncio.sleep(backoff * (attempt + 1))
            except httpx.HTTPError as exc:
                logger.error(f"WasenderAPI HTTP error for {to_number}: {exc}")
                if attempt == retries - 1:
                    return False, None
                await asyncio.sleep(backoff * (attempt + 1))
            except Exception as exc:
                logger.error(f"Unexpected error sending to {to_number}: {exc}")
                return False, None
        
        logger.error(f"Failed to send to {to_number} after {retries} attempts")
        return False, None

    # Sync wrapper for backward compatibility
    def send_sync(self, student, message: str) -> tuple[bool, Optional[str]]:
        """Synchronous send for backward compatibility."""
        return asyncio.run(self.send(recipient=student.phone, message=message))