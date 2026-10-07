"""Mock payment provider for testing and development.

This provider simulates payment flows without connecting to any external service.
Use only in development and testing environments.
"""

from __future__ import annotations

import asyncio
import secrets
from datetime import datetime, timezone
from typing import Optional

from src.payments.base import (
    PaymentProvider,
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentVerification,
    WebhookEvent,
)


class MockPaymentProvider(PaymentProvider):
    """Mock payment provider for testing."""

    name = "mock"

    def __init__(self, auto_verify: bool = True, delay_seconds: float = 0.5):
        self.auto_verify = auto_verify
        self.delay_seconds = delay_seconds
        self._payments: dict[str, dict] = {}

    async def initialize_payment(self, request: PaymentInitRequest) -> PaymentInitResponse:
        """Simulate payment initialization."""
        await asyncio.sleep(self.delay_seconds)

        provider_payment_id = f"mock_{secrets.token_hex(8)}"
        auth_url = f"https://mock-payment.example.com/pay/{provider_payment_id}?reference={request.reference}"

        # Store pending payment
        self._payments[request.reference] = {
            "provider_payment_id": provider_payment_id,
            "amount_minor": request.amount_minor,
            "currency": request.currency,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": request.metadata,
        }

        return PaymentInitResponse(
            authorization_url=auth_url,
            access_code=secrets.token_hex(16),
            reference=request.reference,
            provider_payment_id=provider_payment_id,
        )

    async def verify_payment(self, reference: str) -> PaymentVerification:
        """Simulate payment verification."""
        await asyncio.sleep(self.delay_seconds)

        if reference not in self._payments:
            return PaymentVerification(
                is_verified=False,
                status="not_found",
                amount_minor=0,
                currency="GHS",
                reference=reference,
            )

        payment = self._payments[reference]

        if self.auto_verify and payment["status"] == "pending":
            payment["status"] = "success"
            payment["paid_at"] = datetime.now(timezone.utc).isoformat()

        return PaymentVerification(
            is_verified=payment["status"] == "success",
            status=payment["status"],
            amount_minor=payment["amount_minor"],
            currency=payment["currency"],
            reference=reference,
            provider_payment_id=payment["provider_payment_id"],
            provider_reference=reference,
            provider_fees_minor=0,
            paid_at=payment.get("paid_at"),
            raw_response=payment,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Mock webhook verification (always succeeds in mock)."""
        import json
        data = json.loads(payload)
        return WebhookEvent(
            event_type=data.get("event", "charge.success"),
            reference=data.get("reference", ""),
            provider_payment_id=data.get("provider_payment_id", ""),
            is_verified=True,
            raw_payload=data,
        )

    async def refund_payment(self, reference: str, amount_minor: Optional[int] = None, reason: Optional[str] = None) -> PaymentVerification:
        """Simulate refund."""
        await asyncio.sleep(self.delay_seconds)

        if reference not in self._payments:
            return PaymentVerification(
                is_verified=False,
                status="not_found",
                amount_minor=0,
                currency="GHS",
                reference=reference,
            )

        payment = self._payments[reference]
        payment["status"] = "refunded"

        return PaymentVerification(
            is_verified=True,
            status="refunded",
            amount_minor=amount_minor or payment["amount_minor"],
            currency=payment["currency"],
            reference=reference,
            provider_payment_id=payment["provider_payment_id"],
            provider_reference=reference,
            raw_response={**payment, "refund_reason": reason},
        )

    # Test helper methods
    def set_payment_status(self, reference: str, status: str) -> None:
        """Manually set payment status for testing."""
        if reference in self._payments:
            self._payments[reference]["status"] = status
            if status == "success":
                self._payments[reference]["paid_at"] = datetime.now(timezone.utc).isoformat()

    def get_payment(self, reference: str) -> Optional[dict]:
        """Get payment record for testing."""
        return self._payments.get(reference)