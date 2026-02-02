"""
Billing Module

Payment and subscription management following Clean Architecture.
Supports pluggable payment gateways (Midtrans, Stripe, etc.)
"""

from .api.routes import router as billing_router
from .api.dependencies import init_billing_dependencies

__all__ = [
    "billing_router",
    "init_billing_dependencies",
]
