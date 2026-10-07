"""Paystack payment provider adapter.

Paystack API documentation: https://paystack.com/docs/api
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


class PaystackProvider(PaymentProvider):
    """Paystack payment provider."""

    name = "paystack"

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.paystack.co",
                headers={
                    "Authorization": f"Bearer {self._settings.paystack_secret_key}",
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
        """Initialize a Paystack transaction."""
        client = await self._get_client()

        payload = {
            "amount": request.amount_minor,  # Paystack expects amount in kobo/pesewas
            "currency": request.currency,
            "reference": request.reference,
            "email": request.customer_email,
            "callback_url": request.callback_url or f"{self._settings.app_base_url}/payment/callback",
            "metadata": {
                "customer_name": request.customer_name,
                "customer_phone": request.customer_phone,
                **(request.metadata or {}),
            },
        }

        response = await client.post("/transaction/initialize", json=payload)
        response.raise_for_status()
        data = response.json()

        if not data.get("status"):
            raise RuntimeError(f"Paystack initialization failed: {data.get('message')}")

        auth_data = data["data"]
        return PaymentInitResponse(
            authorization_url=auth_data["authorization_url"],
            access_code=auth_data["access_code"],
            reference=request.reference,
            provider_payment_id=auth_data.get("id"),
        )

    async def verify_payment(self, reference: str) -> PaymentVerification:
        """Verify a Paystack transaction."""
        client = await self._get_client()

        response = await client.get(f"/transaction/verify/{reference}")
        response.raise_for_status()
        data = response.json()

        if not data.get("status"):
            return PaymentVerification(
                is_verified=False,
                status="failed",
                amount_minor=0,
                currency="GHS",
                reference=reference,
                raw_response=data,
            )

        txn = data["data"]
        gateway_response = txn.get("gateway_response", "").lower()
        is_success = txn.get("status") == "success" and gateway_response in ("successful", "approved")

        return PaymentVerification(
            is_verified=is_success,
            status="success" if is_success else "failed",
            amount_minor=txn.get("amount", 0),
            currency=txn.get("currency", "GHS"),
            reference=reference,
            provider_payment_id=str(txn.get("id")) if txn.get("id") else None,
            provider_reference=txn.get("reference"),
            provider_fees_minor=txn.get("fees"),
            paid_at=txn.get("paid_at"),
            raw_response=txn,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify Paystack webhook signature."""
        # Paystack uses HMAC SHA512
        secret = self._settings.paystack_webhook_secret.encode()
        expected = hmac.new(secret, payload, hashlib.sha512).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid Paystack webhook signature")

        data = json.loads(payload)
        event = data.get("event", "")
        txn_data = data.get("data", {})

        return WebhookEvent(
            event_type=event,
            reference=txn_data.get("reference", ""),
            provider_payment_id=str(txn_data.get("id")) if txn_data.get("id") else "",
            is_verified=txn_data.get("status") == "success",
            raw_payload=data,
        )

    async def refund_payment(self, reference: str, amount_minor: Optional[int] = None, reason: Optional[str] = None) -> PaymentVerification:
        """Initiate a refund on Paystack."""
        client = await self._get_client()

        payload = {"transaction": reference}
        if amount_minor:
            payload["amount"] = amount_minor
        if reason:
            payload["reason"] = reason

        response = await client.post("/refund", json=payload)
        response.raise_for_status()
        data = response.json()

        if not data.get("status"):
            raise RuntimeError(f"Paystack refund failed: {data.get('message')}")

        refund_data = data["data"]
        return PaymentVerification(
            is_verified=refund_data.get("status") == "success",
            status="refunded" if refund_data.get("status") == "success" else "failed",
            amount_minor=amount_minor or 0,
            currency="GHS",
            reference=reference,
            provider_payment_id=str(refund_data.get("id")) if refund_data.get("id") else None,
            provider_reference=reference,
            raw_response=refund_data,
        )