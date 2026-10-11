"""Payment provider adapter interface.

Provider-neutral interface for payment processing. Each provider (Paystack, SeefCash, etc.)
implements this interface. The system uses the adapter to initiate payments, verify
webhooks, and check payment status.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class PaymentInitRequest:
    """Request to initialize a payment."""
    amount_minor: int  # Amount in minor units (cents/pesewas)
    currency: str  # ISO 4217 currency code
    reference: str  # Unique reference for this payment
    customer_email: str
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
    metadata: Optional[dict] = None
    callback_url: Optional[str] = None
    cancel_url: Optional[str] = None


@dataclass(frozen=True)
class PaymentInitResponse:
    """Response from payment initialization."""
    authorization_url: str  # URL to redirect user for payment
    reference: str  # Payment reference
    access_code: Optional[str] = None  # Provider-specific access code
    provider_payment_id: Optional[str] = None  # Provider's internal ID


@dataclass(frozen=True)
class PaymentVerification:
    """Result of payment verification."""
    is_verified: bool
    status: str  # 'success', 'failed', 'pending', 'cancelled'
    amount_minor: int
    currency: str
    reference: str
    provider_payment_id: Optional[str] = None
    provider_reference: Optional[str] = None
    provider_fees_minor: Optional[int] = None
    paid_at: Optional[str] = None  # ISO 8601 timestamp
    raw_response: Optional[dict] = None


@dataclass(frozen=True)
class WebhookEvent:
    """Parsed webhook event from provider."""
    event_type: str  # 'charge.success', 'charge.failed', etc.
    reference: str
    provider_payment_id: str
    is_verified: bool
    raw_payload: dict


class PaymentProvider(abc.ABC):
    """Abstract base class for payment providers."""

    name: str  # e.g., 'paystack', 'seefcash'

    @abc.abstractmethod
    async def initialize_payment(self, request: PaymentInitRequest) -> PaymentInitResponse:
        """
        Initialize a payment and return authorization URL.

        Args:
            request: Payment initialization request

        Returns:
            PaymentInitResponse with authorization URL and reference
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def verify_payment(self, reference: str) -> PaymentVerification:
        """
        Verify a payment status by reference.

        Args:
            reference: Payment reference from initialization

        Returns:
            PaymentVerification with verification result
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """
        Verify and parse a webhook event from the provider.

        Args:
            payload: Raw webhook payload
            signature: Provider's signature header

        Returns:
            Parsed WebhookEvent

        Raises:
            ValueError: If signature verification fails
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def refund_payment(self, reference: str, amount_minor: Optional[int] = None, reason: Optional[str] = None) -> PaymentVerification:
        """
        Initiate a refund for a payment.

        Args:
            reference: Payment reference
            amount_minor: Amount to refund (None = full refund)
            reason: Refund reason

        Returns:
            PaymentVerification with refund status
        """
        raise NotImplementedError


class PaymentProviderRegistry:
    """Registry for payment providers."""

    def __init__(self):
        self._providers: dict[str, PaymentProvider] = {}

    def register(self, provider: PaymentProvider) -> None:
        """Register a payment provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> PaymentProvider:
        """Get a payment provider by name."""
        if name not in self._providers:
            raise ValueError(f"Payment provider '{name}' not registered")
        return self._providers[name]

    def get_default(self) -> PaymentProvider:
        """Get the default payment provider (first registered)."""
        if not self._providers:
            raise RuntimeError("No payment providers registered")
        return next(iter(self._providers.values()))


# Global registry instance
payment_registry = PaymentProviderRegistry()