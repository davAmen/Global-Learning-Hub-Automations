"""Stripe payment provider adapter.

Stripe API documentation: https://stripe.com/docs/api
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


class StripeProvider(PaymentProvider):
    """Stripe payment provider."""

    name = "stripe"

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url="https://api.stripe.com/v1",
                auth=(self._settings.stripe_secret_key, ""),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def initialize_payment(self, request: PaymentInitRequest) -> PaymentInitResponse:
        """Initialize a Stripe Checkout Session."""
        client = await self._get_client()

        # Stripe expects amount in minor units (cents)
        payload = {
            "mode": "payment",
            "success_url": request.callback_url or f"{self._settings.app_base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": request.cancel_url or f"{self._settings.app_base_url}/payment/cancel",
            "customer_email": request.customer_email,
            "line_items[0][price_data][currency]": request.currency.lower(),
            "line_items[0][price_data][unit_amount]": str(request.amount_minor),
            "line_items[0][price_data][product_data][name]": request.metadata.get("course_name", "Course Payment") if request.metadata else "Course Payment",
            "line_items[0][quantity]": "1",
            "metadata[reference]": request.reference,
            "metadata[course_id]": request.metadata.get("course_id", "") if request.metadata else "",
            "payment_intent_data[metadata][reference]": request.reference,
        }

        if request.customer_phone:
            payload["phone_number_collection[enabled]"] = "true"

        # Convert to form-encoded
        form_data = "&".join(f"{k}={v}" for k, v in payload.items())

        response = await client.post("/checkout/sessions", content=form_data)
        response.raise_for_status()
        data = response.json()

        return PaymentInitResponse(
            authorization_url=data["url"],
            access_code=data["id"],  # Stripe session ID
            reference=request.reference,
            provider_payment_id=data["id"],
        )

    async def verify_payment(self, reference: str) -> PaymentVerification:
        """Verify a Stripe payment by retrieving the Checkout Session."""
        client = await self._get_client()

        # Search for session by metadata reference
        response = await client.get("/checkout/sessions", params={"limit": 100})
        response.raise_for_status()
        data = response.json()

        session = None
        for s in data.get("data", []):
            if s.get("metadata", {}).get("reference") == reference:
                session = s
                break

        if not session:
            return PaymentVerification(
                is_verified=False,
                status="not_found",
                amount_minor=0,
                currency="GHS",
                reference=reference,
            )

        # Get payment intent for details
        pi_response = await client.get(f"/payment_intents/{session['payment_intent']}")
        pi_data = pi_response.json()

        is_success = pi_data.get("status") == "succeeded"
        amount_received = pi_data.get("amount_received", 0)
        currency = pi_data.get("currency", "ghs").upper()

        return PaymentVerification(
            is_verified=is_success,
            status="success" if is_success else pi_data.get("status", "failed"),
            amount_minor=amount_received,
            currency=currency,
            reference=reference,
            provider_payment_id=pi_data.get("id"),
            provider_reference=session.get("id"),
            provider_fees_minor=0,  # Would need to calculate from balance transactions
            paid_at=datetime.fromtimestamp(pi_data.get("created", 0), tz=timezone.utc).isoformat() if pi_data.get("created") else None,
            raw_response=pi_data,
        )

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify Stripe webhook signature."""
        # Stripe uses the Stripe-Signature header with timestamp and signatures
        # Format: t=<timestamp>,v1=<signature>,v0=<signature>
        if not signature.startswith("t="):
            raise ValueError("Invalid Stripe signature format")

        secret = self._settings.stripe_webhook_secret.encode()
        
        # Parse the signature header
        parts = {}
        for part in signature.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                parts[k] = v

        timestamp = parts.get("t", "")
        v1_signature = parts.get("v1", "")

        # Verify timestamp (within 5 minutes)
        try:
            ts = int(timestamp)
            now = int(datetime.now(timezone.utc).timestamp())
            if abs(now - ts) > 300:
                raise ValueError("Webhook timestamp too old")
        except ValueError:
            raise ValueError("Invalid timestamp in signature")

        # Verify signature
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        expected = hmac.new(secret, signed_payload, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, v1_signature):
            raise ValueError("Invalid Stripe webhook signature")

        data = json.loads(payload)
        event_type = data.get("type", "")
        event_data = data.get("data", {}).get("object", {})

        reference = event_data.get("metadata", {}).get("reference", "")
        
        return WebhookEvent(
            event_type=event_type,
            reference=reference,
            provider_payment_id=event_data.get("id", ""),
            is_verified=event_data.get("status") in ("complete", "succeeded"),
            raw_payload=data,
        )

    async def refund_payment(self, reference: str, amount_minor: Optional[int] = None, reason: Optional[str] = None) -> PaymentVerification:
        """Initiate a refund on Stripe."""
        client = await self._get_client()

        # Find payment intent by reference
        response = await client.get("/payment_intents", params={"limit": 100})
        response.raise_for_status()
        data = response.json()

        payment_intent = None
        for pi in data.get("data", []):
            if pi.get("metadata", {}).get("reference") == reference:
                payment_intent = pi
                break

        if not payment_intent:
            raise ValueError(f"Payment intent not found for reference: {reference}")

        refund_payload = {"payment_intent": payment_intent["id"]}
        if amount_minor:
            refund_payload["amount"] = str(amount_minor)
        if reason:
            refund_payload["reason"] = reason

        refund_response = await client.post("/refunds", data=refund_payload)
        refund_response.raise_for_status()
        refund_data = refund_response.json()

        return PaymentVerification(
            is_verified=refund_data.get("status") == "succeeded",
            status="refunded" if refund_data.get("status") == "succeeded" else "failed",
            amount_minor=amount_minor or 0,
            currency=refund_data.get("currency", "ghs").upper(),
            reference=reference,
            provider_payment_id=refund_data.get("id"),
            provider_reference=reference,
            raw_response=refund_data,
        )