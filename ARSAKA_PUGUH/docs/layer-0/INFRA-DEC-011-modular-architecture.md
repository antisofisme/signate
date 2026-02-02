# INFRA-DEC-011: Modular Architecture & Clean Design

**VERSION**: Layer 0 DRAFT
**STATUS**: DRAFT
**DATE**: 2026-01-26

---

## Overview

This document defines the modular architecture principles for ARSAKA_PUGUH SaaS transformation:
- Clean Architecture layers
- Interface-based design for external services
- Dependency injection pattern
- Centralized configuration
- Easy provider replacement (e.g., Midtrans → Stripe)

---

## Architecture Principles

### Clean Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  (React Pages, FastAPI Routes)                                   │
│  - NO business logic here                                        │
│  - Only UI rendering & HTTP handling                             │
│  - Receives DTOs, returns DTOs                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        USE CASE LAYER                            │
│  (Application Services)                                          │
│  - Business logic orchestration                                  │
│  - Input validation                                              │
│  - Cross-service coordination                                    │
│  - Transaction boundaries                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                              │
│  (Entities, Value Objects, Domain Events)                        │
│  - Core business rules                                           │
│  - NO external dependencies                                      │
│  - Framework agnostic                                            │
│  - Pure Python/TypeScript                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                          │
│  (Repositories, External Services, Database)                     │
│  - Implements interfaces defined in Domain                       │
│  - Easily replaceable (swap Midtrans → Stripe)                   │
│  - Adapters for external services                                │
│  - Database access                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Dependency Inversion**: High-level modules don't depend on low-level modules. Both depend on abstractions (interfaces).

2. **Single Responsibility**: Each module/class has one reason to change.

3. **Open/Closed**: Open for extension, closed for modification. Add new adapters without changing existing code.

4. **Interface Segregation**: Many specific interfaces are better than one general interface.

5. **No Vendor Lock-in**: Business logic doesn't know about specific external providers.

---

## 1. Module Structure

### Backend Module Organization

```
backend/core/
├── auth/                           # Auth module
│   ├── __init__.py
│   ├── interfaces/                 # Abstract contracts
│   │   ├── __init__.py
│   │   ├── auth_provider.py        # IAuthProvider
│   │   └── oauth_provider.py       # IOAuthProvider
│   ├── adapters/                   # Implementations
│   │   ├── __init__.py
│   │   ├── local_auth.py           # LocalAuthAdapter
│   │   ├── google_oauth.py         # GoogleOAuthAdapter
│   │   └── github_oauth.py         # GitHubOAuthAdapter
│   ├── use_cases/                  # Business logic
│   │   ├── __init__.py
│   │   ├── register.py             # RegisterUseCase
│   │   ├── login.py                # LoginUseCase
│   │   ├── verify_email.py         # VerifyEmailUseCase
│   │   └── reset_password.py       # ResetPasswordUseCase
│   ├── domain/                     # Domain entities
│   │   ├── __init__.py
│   │   ├── user.py                 # User entity
│   │   └── events.py               # UserRegistered, etc.
│   └── repositories/               # Data access
│       ├── __init__.py
│       └── user_repository.py      # IUserRepository, UserRepository
│
├── payment/                        # Payment module
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   └── payment_gateway.py      # IPaymentGateway
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── midtrans.py             # MidtransAdapter
│   │   └── stripe.py               # StripeAdapter (stub)
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── create_checkout.py      # CreateCheckoutUseCase
│   │   ├── handle_webhook.py       # HandleWebhookUseCase
│   │   └── cancel_subscription.py  # CancelSubscriptionUseCase
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── subscription.py         # Subscription entity
│   │   ├── invoice.py              # Invoice entity
│   │   └── events.py               # PaymentReceived, etc.
│   └── repositories/
│       ├── __init__.py
│       ├── subscription_repository.py
│       └── invoice_repository.py
│
├── tenant/                         # Tenant module
│   ├── __init__.py
│   ├── interfaces/
│   │   └── tenant_service.py       # ITenantService
│   ├── use_cases/
│   │   ├── create_tenant.py
│   │   ├── invite_member.py
│   │   └── update_tenant.py
│   ├── domain/
│   │   ├── tenant.py
│   │   └── membership.py
│   └── repositories/
│       ├── tenant_repository.py
│       └── membership_repository.py
│
├── project/                        # Project module
│   ├── __init__.py
│   ├── use_cases/
│   │   ├── create_project.py
│   │   └── update_project.py
│   ├── domain/
│   │   └── project.py
│   └── repositories/
│       └── project_repository.py
│
├── decision/                       # Existing decision module
│   └── ... (already implemented)
│
├── workflow/                       # Existing workflow module
│   └── ... (already implemented)
│
└── shared/                         # Shared utilities
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py             # Environment settings
    │   └── providers.py            # Provider registry
    ├── events/
    │   ├── __init__.py
    │   └── event_bus.py            # Domain event bus
    ├── errors/
    │   ├── __init__.py
    │   └── exceptions.py           # Standardized errors
    └── di/
        ├── __init__.py
        └── container.py            # Dependency injection container
```

---

## 2. Interface Definitions

### Auth Provider Interface

```python
# backend/core/auth/interfaces/auth_provider.py

from abc import ABC, abstractmethod
from typing import Optional
from ..domain.user import User

class IAuthProvider(ABC):
    """Interface for authentication providers."""

    @abstractmethod
    async def authenticate(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user with email/password.

        Returns User if successful, None if failed.
        """
        pass

    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""
        pass

    @abstractmethod
    async def verify_password(
        self,
        password: str,
        hashed: str
    ) -> bool:
        """Verify password against hash."""
        pass
```

### OAuth Provider Interface

```python
# backend/core/auth/interfaces/oauth_provider.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class OAuthUser:
    """User info from OAuth provider."""
    provider_id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]

class IOAuthProvider(ABC):
    """Interface for OAuth providers (Google, GitHub, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'google', 'github')."""
        pass

    @abstractmethod
    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str
    ) -> str:
        """Generate OAuth authorization URL."""
        pass

    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        redirect_uri: str
    ) -> str:
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    async def get_user_info(
        self,
        access_token: str
    ) -> OAuthUser:
        """Get user info from OAuth provider."""
        pass
```

### Payment Gateway Interface

```python
# backend/core/payment/interfaces/payment_gateway.py

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class CheckoutResult:
    """Result of creating a checkout session."""
    checkout_id: str
    checkout_url: Optional[str]
    snap_token: Optional[str]  # Midtrans-specific
    expires_at: datetime

@dataclass
class WebhookEvent:
    """Normalized webhook event."""
    event_type: str  # 'payment.success', 'payment.failed', etc.
    order_id: str
    amount_cents: int
    currency: str
    provider_transaction_id: str
    raw_payload: dict

class IPaymentGateway(ABC):
    """Interface for payment gateways (Midtrans, Stripe, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'midtrans', 'stripe')."""
        pass

    @abstractmethod
    async def create_checkout(
        self,
        order_id: str,
        amount_cents: int,
        currency: str,
        customer_email: str,
        customer_name: str,
        item_name: str,
        success_url: str,
        cancel_url: str
    ) -> CheckoutResult:
        """Create a checkout session."""
        pass

    @abstractmethod
    async def verify_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        """Verify and parse webhook payload.

        Raises WebhookVerificationError if invalid.
        """
        pass

    @abstractmethod
    async def get_transaction(
        self,
        transaction_id: str
    ) -> dict:
        """Get transaction details from provider."""
        pass

    @abstractmethod
    async def refund_transaction(
        self,
        transaction_id: str,
        amount_cents: Optional[int] = None
    ) -> dict:
        """Refund a transaction (full or partial)."""
        pass
```

### Tenant Service Interface

```python
# backend/core/tenant/interfaces/tenant_service.py

from abc import ABC, abstractmethod
from typing import Optional, List
from ..domain.tenant import Tenant
from ..domain.membership import TenantMembership

class ITenantService(ABC):
    """Interface for tenant management."""

    @abstractmethod
    async def create_tenant(
        self,
        name: str,
        owner_user_id: str
    ) -> Tenant:
        """Create a new tenant with default project."""
        pass

    @abstractmethod
    async def get_tenant(
        self,
        tenant_id: str
    ) -> Optional[Tenant]:
        """Get tenant by ID."""
        pass

    @abstractmethod
    async def get_user_tenants(
        self,
        user_id: str
    ) -> List[TenantMembership]:
        """Get all tenants a user belongs to."""
        pass

    @abstractmethod
    async def invite_member(
        self,
        tenant_id: str,
        email: str,
        role: str,
        invited_by: str
    ) -> TenantMembership:
        """Invite a user to tenant."""
        pass

    @abstractmethod
    async def remove_member(
        self,
        tenant_id: str,
        user_id: str
    ) -> None:
        """Remove a member from tenant."""
        pass
```

---

## 3. Adapter Implementations

### Midtrans Adapter

```python
# backend/core/payment/adapters/midtrans.py

import hashlib
import httpx
from typing import Optional
from ..interfaces.payment_gateway import (
    IPaymentGateway,
    CheckoutResult,
    WebhookEvent
)
from ...shared.config import settings
from ...shared.errors import WebhookVerificationError

class MidtransAdapter(IPaymentGateway):
    """Midtrans payment gateway implementation."""

    def __init__(self):
        self.server_key = settings.MIDTRANS_SERVER_KEY
        self.client_key = settings.MIDTRANS_CLIENT_KEY
        self.is_production = settings.MIDTRANS_IS_PRODUCTION

        self.snap_url = (
            "https://app.midtrans.com/snap/v1/transactions"
            if self.is_production
            else "https://app.sandbox.midtrans.com/snap/v1/transactions"
        )

    @property
    def provider_name(self) -> str:
        return "midtrans"

    async def create_checkout(
        self,
        order_id: str,
        amount_cents: int,
        currency: str,
        customer_email: str,
        customer_name: str,
        item_name: str,
        success_url: str,
        cancel_url: str
    ) -> CheckoutResult:
        """Create Midtrans Snap checkout."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.snap_url,
                json={
                    "transaction_details": {
                        "order_id": order_id,
                        "gross_amount": amount_cents  # IDR doesn't use cents
                    },
                    "customer_details": {
                        "email": customer_email,
                        "first_name": customer_name
                    },
                    "item_details": [{
                        "id": order_id,
                        "price": amount_cents,
                        "quantity": 1,
                        "name": item_name
                    }],
                    "callbacks": {
                        "finish": success_url
                    }
                },
                auth=(self.server_key, "")
            )
            response.raise_for_status()
            data = response.json()

            return CheckoutResult(
                checkout_id=order_id,
                checkout_url=data.get("redirect_url"),
                snap_token=data.get("token"),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )

    async def verify_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> WebhookEvent:
        """Verify Midtrans webhook signature."""
        import json
        data = json.loads(payload)

        # Verify signature
        expected_signature = self._generate_signature(
            data["order_id"],
            data["status_code"],
            data["gross_amount"]
        )

        if signature != expected_signature:
            raise WebhookVerificationError("Invalid Midtrans signature")

        # Map status to event type
        status_map = {
            "settlement": "payment.success",
            "capture": "payment.pending",
            "pending": "payment.pending",
            "deny": "payment.failed",
            "cancel": "payment.cancelled",
            "expire": "payment.expired",
            "refund": "payment.refunded"
        }

        return WebhookEvent(
            event_type=status_map.get(data["transaction_status"], "payment.unknown"),
            order_id=data["order_id"],
            amount_cents=int(float(data["gross_amount"])),
            currency="IDR",
            provider_transaction_id=data["transaction_id"],
            raw_payload=data
        )

    def _generate_signature(
        self,
        order_id: str,
        status_code: str,
        gross_amount: str
    ) -> str:
        """Generate Midtrans signature."""
        data = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        return hashlib.sha512(data.encode()).hexdigest()

    async def get_transaction(self, transaction_id: str) -> dict:
        """Get transaction from Midtrans."""
        base_url = (
            "https://api.midtrans.com/v2"
            if self.is_production
            else "https://api.sandbox.midtrans.com/v2"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/{transaction_id}/status",
                auth=(self.server_key, "")
            )
            response.raise_for_status()
            return response.json()

    async def refund_transaction(
        self,
        transaction_id: str,
        amount_cents: Optional[int] = None
    ) -> dict:
        """Refund a Midtrans transaction."""
        base_url = (
            "https://api.midtrans.com/v2"
            if self.is_production
            else "https://api.sandbox.midtrans.com/v2"
        )

        body = {}
        if amount_cents:
            body["refund_amount"] = amount_cents

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/{transaction_id}/refund",
                json=body,
                auth=(self.server_key, "")
            )
            response.raise_for_status()
            return response.json()
```

### Stripe Adapter (Stub)

```python
# backend/core/payment/adapters/stripe.py

from ..interfaces.payment_gateway import (
    IPaymentGateway,
    CheckoutResult,
    WebhookEvent
)

class StripeAdapter(IPaymentGateway):
    """Stripe payment gateway implementation (stub for future use)."""

    @property
    def provider_name(self) -> str:
        return "stripe"

    async def create_checkout(self, **kwargs) -> CheckoutResult:
        raise NotImplementedError("Stripe adapter not implemented yet")

    async def verify_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        raise NotImplementedError("Stripe adapter not implemented yet")

    async def get_transaction(self, transaction_id: str) -> dict:
        raise NotImplementedError("Stripe adapter not implemented yet")

    async def refund_transaction(self, transaction_id: str, amount_cents=None) -> dict:
        raise NotImplementedError("Stripe adapter not implemented yet")
```

---

## 4. Dependency Injection

### Container Setup

```python
# backend/core/shared/di/container.py

from typing import Dict, Type, Any
from functools import lru_cache

class DIContainer:
    """Simple dependency injection container."""

    _instances: Dict[Type, Any] = {}
    _factories: Dict[Type, callable] = {}

    @classmethod
    def register(cls, interface: Type, factory: callable):
        """Register a factory for an interface."""
        cls._factories[interface] = factory

    @classmethod
    def resolve(cls, interface: Type) -> Any:
        """Resolve an interface to its implementation."""
        if interface not in cls._instances:
            if interface not in cls._factories:
                raise ValueError(f"No factory registered for {interface}")
            cls._instances[interface] = cls._factories[interface]()
        return cls._instances[interface]

    @classmethod
    def reset(cls):
        """Reset container (for testing)."""
        cls._instances.clear()


# Convenience function
def inject(interface: Type) -> Any:
    """Inject a dependency."""
    return DIContainer.resolve(interface)
```

### Provider Registry

```python
# backend/core/shared/config/providers.py

from typing import Dict, Type
from ..di.container import DIContainer

# Auth providers
from ...auth.interfaces.auth_provider import IAuthProvider
from ...auth.interfaces.oauth_provider import IOAuthProvider
from ...auth.adapters.local_auth import LocalAuthAdapter
from ...auth.adapters.google_oauth import GoogleOAuthAdapter
from ...auth.adapters.github_oauth import GitHubOAuthAdapter

# Payment providers
from ...payment.interfaces.payment_gateway import IPaymentGateway
from ...payment.adapters.midtrans import MidtransAdapter
from ...payment.adapters.stripe import StripeAdapter

from .settings import settings


class ProviderRegistry:
    """Centralized provider configuration.

    Change active providers here to swap implementations.
    """

    # Available auth providers
    AUTH_PROVIDERS: Dict[str, Type[IAuthProvider]] = {
        "local": LocalAuthAdapter,
    }

    # Available OAuth providers
    OAUTH_PROVIDERS: Dict[str, Type[IOAuthProvider]] = {
        "google": GoogleOAuthAdapter,
        "github": GitHubOAuthAdapter,
    }

    # Available payment gateways
    PAYMENT_GATEWAYS: Dict[str, Type[IPaymentGateway]] = {
        "midtrans": MidtransAdapter,
        "stripe": StripeAdapter,
    }

    # Active selections (change here to swap)
    ACTIVE_PAYMENT_GATEWAY = settings.PAYMENT_GATEWAY  # "midtrans"

    @classmethod
    def setup(cls):
        """Register all providers with DI container."""
        # Auth
        DIContainer.register(
            IAuthProvider,
            lambda: LocalAuthAdapter()
        )

        # OAuth (multiple providers)
        for name, provider_class in cls.OAUTH_PROVIDERS.items():
            if getattr(settings, f"{name.upper()}_OAUTH_ENABLED", False):
                DIContainer.register(
                    f"oauth_{name}",
                    lambda pc=provider_class: pc()
                )

        # Payment Gateway (single active)
        gateway_class = cls.PAYMENT_GATEWAYS[cls.ACTIVE_PAYMENT_GATEWAY]
        DIContainer.register(
            IPaymentGateway,
            lambda gc=gateway_class: gc()
        )


def setup_providers():
    """Initialize provider registry on startup."""
    ProviderRegistry.setup()
```

### Usage in Use Cases

```python
# backend/core/payment/use_cases/create_checkout.py

from dataclasses import dataclass
from ..interfaces.payment_gateway import IPaymentGateway, CheckoutResult
from ..repositories.subscription_repository import ISubscriptionRepository
from ..repositories.invoice_repository import IInvoiceRepository
from ...shared.di.container import inject


@dataclass
class CreateCheckoutRequest:
    tenant_id: str
    plan_id: str
    user_email: str
    user_name: str


class CreateCheckoutUseCase:
    """Create a checkout session for subscription upgrade."""

    def __init__(
        self,
        payment_gateway: IPaymentGateway = None,
        subscription_repo: ISubscriptionRepository = None,
        invoice_repo: IInvoiceRepository = None
    ):
        # Inject dependencies if not provided (for testing)
        self.payment = payment_gateway or inject(IPaymentGateway)
        self.subscriptions = subscription_repo or inject(ISubscriptionRepository)
        self.invoices = invoice_repo or inject(IInvoiceRepository)

    async def execute(self, request: CreateCheckoutRequest) -> CheckoutResult:
        """Execute the use case."""
        # 1. Get plan details
        plan = await self.subscriptions.get_plan(request.plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {request.plan_id}")

        # 2. Create invoice
        invoice = await self.invoices.create(
            tenant_id=request.tenant_id,
            plan_id=request.plan_id,
            amount_cents=plan.price_cents,
            currency=plan.currency
        )

        # 3. Create checkout via payment gateway
        # Note: Business logic doesn't know if it's Midtrans or Stripe
        checkout = await self.payment.create_checkout(
            order_id=invoice.invoice_number,
            amount_cents=plan.price_cents,
            currency=plan.currency,
            customer_email=request.user_email,
            customer_name=request.user_name,
            item_name=f"{plan.name} Plan - Monthly",
            success_url=f"/billing/success?invoice={invoice.invoice_id}",
            cancel_url=f"/billing/cancel?invoice={invoice.invoice_id}"
        )

        # 4. Update invoice with checkout info
        await self.invoices.update(
            invoice.invoice_id,
            provider_checkout_id=checkout.checkout_id
        )

        return checkout
```

---

## 5. FastAPI Integration

### Route Handler

```python
# backend/api/routes/billing.py

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel

from ...core.payment.use_cases.create_checkout import (
    CreateCheckoutUseCase,
    CreateCheckoutRequest
)
from ...core.payment.use_cases.handle_webhook import HandleWebhookUseCase
from ..dependencies import get_current_user, get_current_tenant

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequestDTO(BaseModel):
    plan_id: str


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequestDTO,
    current_user = Depends(get_current_user),
    current_tenant = Depends(get_current_tenant)
):
    """Create a checkout session for plan upgrade."""
    use_case = CreateCheckoutUseCase()  # Dependencies auto-injected

    result = await use_case.execute(CreateCheckoutRequest(
        tenant_id=current_tenant.tenant_id,
        plan_id=request.plan_id,
        user_email=current_user.email,
        user_name=current_user.display_name
    ))

    return {
        "success": True,
        "data": {
            "snap_token": result.snap_token,
            "redirect_url": result.checkout_url
        }
    }


@router.post("/webhooks/midtrans")
async def midtrans_webhook(request: Request):
    """Handle Midtrans webhook (public endpoint)."""
    payload = await request.body()
    signature = request.headers.get("X-Midtrans-Signature", "")

    use_case = HandleWebhookUseCase()

    try:
        await use_case.execute(payload, signature)
        return {"success": True}
    except Exception as e:
        # Log error but return 200 to prevent Midtrans retry storm
        print(f"Webhook error: {e}")
        return {"success": True}
```

---

## 6. Testing with Mocks

### Unit Test Example

```python
# backend/tests/unit/test_create_checkout.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from core.payment.use_cases.create_checkout import (
    CreateCheckoutUseCase,
    CreateCheckoutRequest
)
from core.payment.interfaces.payment_gateway import CheckoutResult


@pytest.fixture
def mock_payment_gateway():
    """Create mock payment gateway."""
    gateway = AsyncMock()
    gateway.create_checkout.return_value = CheckoutResult(
        checkout_id="test-checkout-123",
        checkout_url="https://test.com/checkout",
        snap_token="snap-token-123",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    return gateway


@pytest.fixture
def mock_subscription_repo():
    """Create mock subscription repository."""
    repo = AsyncMock()
    repo.get_plan.return_value = MagicMock(
        plan_id="pro",
        name="Pro",
        price_cents=99000000,
        currency="IDR"
    )
    return repo


@pytest.fixture
def mock_invoice_repo():
    """Create mock invoice repository."""
    repo = AsyncMock()
    repo.create.return_value = MagicMock(
        invoice_id="inv-123",
        invoice_number="INV-2024-00001"
    )
    return repo


@pytest.mark.asyncio
async def test_create_checkout_success(
    mock_payment_gateway,
    mock_subscription_repo,
    mock_invoice_repo
):
    """Test successful checkout creation."""
    # Arrange
    use_case = CreateCheckoutUseCase(
        payment_gateway=mock_payment_gateway,
        subscription_repo=mock_subscription_repo,
        invoice_repo=mock_invoice_repo
    )

    request = CreateCheckoutRequest(
        tenant_id="tenant-123",
        plan_id="pro",
        user_email="test@example.com",
        user_name="Test User"
    )

    # Act
    result = await use_case.execute(request)

    # Assert
    assert result.snap_token == "snap-token-123"
    assert result.checkout_url == "https://test.com/checkout"

    # Verify gateway was called with correct params
    mock_payment_gateway.create_checkout.assert_called_once()
    call_args = mock_payment_gateway.create_checkout.call_args
    assert call_args.kwargs["order_id"] == "INV-2024-00001"
    assert call_args.kwargs["amount_cents"] == 99000000
```

---

## 7. Swapping Providers

### Example: Switch from Midtrans to Stripe

```python
# Step 1: Implement StripeAdapter (already has stub)
# backend/core/payment/adapters/stripe.py

import stripe
from ..interfaces.payment_gateway import IPaymentGateway, CheckoutResult, WebhookEvent

class StripeAdapter(IPaymentGateway):
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @property
    def provider_name(self) -> str:
        return "stripe"

    async def create_checkout(self, **kwargs) -> CheckoutResult:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": kwargs["price_id"],
                "quantity": 1
            }],
            success_url=kwargs["success_url"],
            cancel_url=kwargs["cancel_url"]
        )
        return CheckoutResult(
            checkout_id=session.id,
            checkout_url=session.url,
            snap_token=None,  # Stripe doesn't use snap
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )

    # ... implement other methods


# Step 2: Change settings
# .env
PAYMENT_GATEWAY=stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx


# Step 3: That's it! No code changes in use cases.
# The CreateCheckoutUseCase automatically uses Stripe.
```

---

## 8. Guard Rails

### GR-ARCH-1: No Direct Provider Import in Use Cases
```python
# WRONG
from ..adapters.midtrans import MidtransAdapter

class SomeUseCase:
    def __init__(self):
        self.payment = MidtransAdapter()  # ❌ Direct import

# CORRECT
from ..interfaces.payment_gateway import IPaymentGateway
from ...shared.di.container import inject

class SomeUseCase:
    def __init__(self, payment: IPaymentGateway = None):
        self.payment = payment or inject(IPaymentGateway)  # ✅ Interface
```

### GR-ARCH-2: Business Logic in Use Cases, Not Routes
```python
# WRONG (business logic in route)
@router.post("/checkout")
async def create_checkout(request: Request):
    plan = await db.get_plan(request.plan_id)
    if plan.price > tenant.balance:  # ❌ Business logic in route
        raise HTTPException(400, "Insufficient balance")
    # ...

# CORRECT (route calls use case)
@router.post("/checkout")
async def create_checkout(request: Request):
    use_case = CreateCheckoutUseCase()
    return await use_case.execute(request)  # ✅ Delegate to use case
```

### GR-ARCH-3: Domain Entities Are Pure
```python
# WRONG (domain entity with framework dependency)
from sqlalchemy import Column, String
from ..database import Base

class User(Base):  # ❌ SQLAlchemy dependency
    __tablename__ = "users"
    id = Column(String, primary_key=True)

# CORRECT (pure domain entity)
from dataclasses import dataclass

@dataclass
class User:  # ✅ Pure Python
    user_id: str
    email: str
    display_name: str
```

### GR-ARCH-4: Repositories Abstract Database Access
```python
# WRONG (direct SQL in use case)
class SomeUseCase:
    async def execute(self):
        result = await db.execute("SELECT * FROM users")  # ❌ Direct SQL

# CORRECT (use repository)
class SomeUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.users = user_repo

    async def execute(self):
        user = await self.users.get_by_id(user_id)  # ✅ Repository
```

---

## 9. Checklist: Modular Architecture DRAFT

- ✅ Clean Architecture layers defined
- ✅ Interface definitions for Auth, OAuth, Payment
- ✅ Adapter implementations (Midtrans, Local Auth)
- ✅ Dependency injection pattern
- ✅ Provider registry for centralized config
- ✅ Use case examples with DI
- ✅ FastAPI route integration
- ✅ Unit testing with mocks
- ✅ Provider swap example
- ✅ Guard rails defined (4 rules)

**Status**: DRAFT - Ready for review before implementation.

**Dependencies**:
- INFRA-DEC-008: Auth Flow (for auth interfaces)
- INFRA-DEC-010: Payment & Billing (for payment interfaces)
