"""SeefCash payment provider adapter.

SeefCash API documentation: (assumed similar to standard mobile money APIs)
Note: This is a template implementation. Adjust based on actual SeefCash API documentation.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import httpx
from datetime import datetime, timezone
from typing import Optional

from src.payments.base import (
    PaymentProvider,
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentVerification,
    WebhookEvent,
)
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SeefCashProvider(PaymentProvider):
    """SeefCash payment provider."""

    name = "seefcash"

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.seefcash.com",  # Adjust based on actual API
                headers={
                    "Authorization": f"Bearer {self._settings.seefcash_secret_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def initialize_payment(self, request: PaymentInitRequest) -> PaymentInitResponse:
        """Initialize a SeefCash mobile money payment."""
        client = await self._get_client()

        payload = {
            "amount": request.amount_minor / 100,  # SeefCash may expect major units
            "currency": request.currency,
            "reference": request.reference,
            "phone": request.customer_phone,
            "email": request.customer_email,
            "name": request.customer_name,
            "callback_url": request.callback_url or f"{self._settings.app_base_url}/payment/callback",
            "metadata": request.metadata,
        }

        response = await client.post("/v1/payments/initialize", json=payload)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"SeefCash initialization failed: {data.get('message')}")

        return PaymentInitResponse(
            authorization_url=data.get("authorization_url", ""),
            access_code=data.get("access_code"),
            reference=request.reference,
            provider_payment_id=data.get("transaction_id"),
        )

    async def verify_payment(self, reference: str) -> PaymentVerification:
        """Verify a SeefCash transaction."""
        client = await self._get_client()

        response = await client.get(f"/v1/payments/verify/{reference}")
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            return PaymentVerification(
                is_verified=False,
                status="failed",
                amount_minor=0,
                currency="GHS",
                reference=reference,
                raw_response=data,
            )

        txn = data["data"]
        is_success = txn.get("status") == "success"

        return PaymentVerification(
            is_verified=is_success,
            status="success" if is_success else "failed",
            amount_minor=int(txn.get("amount", 0) * 100),  # Convert to minor units
            currency=txn.get("currency", "GHS"),
            reference=reference,
            provider_payment_id=txn.get("transaction_id"),
            provider_reference=txn.get("reference"),
            provider_fees_minor=txn.get("fees"),
            paid_at=txn.get("paid_at"),
            raw_response=txn,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify SeefCash webhook signature."""
        secret = self._settings.seefcash_webhook_secret.encode()
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid SeefCash webhook signature")

        data = json.loads(payload)
        event = data.get("event", "")
        txn_data = data.get("data", {})

        return WebhookEvent(
            event_type=event,
            reference=txn_data.get("reference", ""),
            provider_payment_id=txn_data.get("transaction_id", ""),
            is_verified=txn_data.get("status") == "success",
            raw_payload=data,
        )

    async def refund_payment(self, reference: str, amount_minor: Optional[int] = None, reason: Optional[str] = None) -> PaymentVerification:
        """Initiate a refund on SeefCash."""
        client = await self._get_client()

        payload = {"reference": reference}
        if amount_minor:
            payload["amount"] = amount_minor / 100
        if reason:
            payload["reason"] = reason

        response = await client.post("/v1/refunds", json=payload)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"SeefCash refund failed: {data.get('message')}")

        refund_data = data["data"]
        return PaymentVerification(
            is_verified=refund_data.get("status") == "success",
            status="refunded" if refund_data.get("status") == "success" else "failed",
            amount_minor=amount_minor or 0,
            currency="GHS",
            reference=reference,
            provider_payment_id=refund_data.get("transaction_id"),
            provider_reference=reference,
            raw_response=refund_data,
        )