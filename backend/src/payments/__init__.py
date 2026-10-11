"""Payment provider package.

Provides provider-neutral payment processing with support for:
- Paystack (paystack.com)
- SeefCash (seefcash.com)
- Mock provider for testing

Usage:
    from src.payments import payment_registry, PaymentInitRequest
    
    provider = payment_registry.get("paystack")
    response = await provider.initialize_payment(request)
"""

from src.payments.base import (
    PaymentProvider,
    PaymentProviderRegistry,
    PaymentInitRequest,
    PaymentInitResponse,
    PaymentVerification,
    WebhookEvent,
    payment_registry,
)

# Import and register providers
def _register_providers():
    """Register available payment providers based on configuration."""
    from src.config import get_settings
    settings = get_settings()

    # Register mock provider (always available for testing)
    from src.payments.mock import MockPaymentProvider
    payment_registry.register(MockPaymentProvider())

    # Register Paystack if configured
    if settings.paystack_secret_key and settings.paystack_public_key:
        from src.payments.paystack import PaystackProvider
        payment_registry.register(PaystackProvider())

    # Register SeefCash if configured
    if settings.seefcash_secret_key:
        from src.payments.seefcash import SeefCashProvider
        payment_registry.register(SeefCashProvider())

# Register and register providers
def _register_providers():
    """Register available payment providers based on configuration."""
    from src.config import get_settings
    settings = get_settings()

    # Register mock provider (always available for testing)
    from src.payments.mock import MockPaymentProvider
    payment_registry.register(MockPaymentProvider())

    # Register Paystack if configured
    if settings.paystack_secret_key and settings.paystack_public_key:
        from src.payments.paystack import PaystackProvider
        payment_registry.register(PaystackProvider())

    # Register SeefCash if configured
    if settings.seefcash_secret_key:
        from src.payments.seefcash import SeefCashProvider
        payment_registry.register(SeefCashProvider())

    # Register Stripe if configured
    if settings.stripe_secret_key:
        from src.payments.stripe import StripeProvider
        payment_registry.register(StripeProvider())

# Register on import
_register_providers()

__all__ = [
    "PaymentProvider",
    "PaymentProviderRegistry",
    "PaymentInitRequest",
    "PaymentInitResponse",
    "PaymentVerification",
    "WebhookEvent",
    "payment_registry",
]