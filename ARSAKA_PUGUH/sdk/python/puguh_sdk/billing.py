"""
PUGUH SDK - Billing Module

Subscription and billing management.
Handles plans, subscriptions, invoices, and usage tracking.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import httpx

from .exceptions import (
    PuguhError,
    BillingError,
    SubscriptionRequiredError,
    SubscriptionExpiredError,
    PaymentFailedError,
    ValidationError,
    NetworkError,
)


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class BillingInterval(str, Enum):
    """Billing interval."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Plan:
    """Subscription plan."""
    plan_id: str
    product_id: str
    name: str
    description: Optional[str] = None
    price: float = 0.0
    currency: str = "USD"
    interval: BillingInterval = BillingInterval.MONTHLY

    # Plan features/limits
    features: Optional[Dict[str, Any]] = None

    # Metadata
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Subscription:
    """Active subscription."""
    subscription_id: str
    tenant_id: str
    plan_id: str
    product_id: str
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    # Billing cycle
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at: Optional[datetime] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL)

    @property
    def is_in_trial(self) -> bool:
        """Check if subscription is in trial."""
        return self.status == SubscriptionStatus.TRIAL


@dataclass
class Invoice:
    """Billing invoice."""
    invoice_id: str
    tenant_id: str
    subscription_id: Optional[str] = None
    amount: float = 0.0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING

    # Details
    line_items: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None

    # Dates
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass
class UsageMetrics:
    """Usage metrics for a tenant."""
    tenant_id: str
    period_start: datetime
    period_end: datetime

    # Metrics by product
    metrics: Dict[str, Dict[str, int]] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

    def get_metric(self, product: str, metric: str) -> int:
        """Get specific metric value."""
        product_metrics = self.metrics.get(product, {})
        return product_metrics.get(metric, 0)


class BillingClient:
    """
    Billing and subscription management client.

    Handles:
    - Viewing available plans
    - Managing subscriptions
    - Viewing invoices
    - Tracking usage

    Example:
        ```python
        from puguh_sdk import PuguhClient

        client = PuguhClient(
            base_url="https://api.puguh.io",
            access_token="user_jwt_token"
        )

        # Get available plans
        plans = await client.billing.get_plans(product="mantra")

        # Create subscription
        sub = await client.billing.create_subscription(
            tenant_id="tenant_uuid",
            plan_id="plan_pro",
            product="mantra"
        )

        # Check usage
        usage = await client.billing.get_usage(tenant_id="tenant_uuid")
        print(f"API calls: {usage.get_metric('mantra', 'api_calls')}")
        ```
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize billing client.

        Args:
            http_client: Shared HTTP client from PuguhClient
        """
        self._client = http_client

    def _handle_error(self, response: httpx.Response):
        """Handle error response and raise appropriate exception."""
        try:
            data = response.json()
            error_code = data.get("error", {}).get("code", "UNKNOWN_ERROR")
            message = data.get("error", {}).get("message", "An error occurred")
            details = data.get("error", {}).get("details", {})
        except Exception:
            error_code = "UNKNOWN_ERROR"
            message = response.text or f"HTTP {response.status_code}"
            details = {}

        if error_code == "SUBSCRIPTION_REQUIRED":
            raise SubscriptionRequiredError(details.get("product", "unknown"), message)
        elif error_code == "SUBSCRIPTION_EXPIRED":
            raise SubscriptionExpiredError(details.get("product", "unknown"), message)
        elif error_code == "PAYMENT_FAILED":
            raise PaymentFailedError(message)
        elif response.status_code == 422:
            raise ValidationError(message, details)
        elif response.status_code == 402:
            raise BillingError(message, error_code, details)
        else:
            raise PuguhError(message, error_code, details, response.status_code)

    def _parse_plan(self, data: dict) -> Plan:
        """Parse plan from API response."""
        return Plan(
            plan_id=data["plan_id"],
            product_id=data["product_id"],
            name=data["name"],
            description=data.get("description"),
            price=float(data.get("price", 0)),
            currency=data.get("currency", "USD"),
            interval=BillingInterval(data.get("interval", "monthly")),
            features=data.get("features", {}),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at") else None,
        )

    def _parse_subscription(self, data: dict) -> Subscription:
        """Parse subscription from API response."""
        return Subscription(
            subscription_id=data["subscription_id"],
            tenant_id=data["tenant_id"],
            plan_id=data["plan_id"],
            product_id=data["product_id"],
            status=SubscriptionStatus(data.get("status", "active")),
            current_period_start=datetime.fromisoformat(data["current_period_start"].replace("Z", "+00:00"))
                if data.get("current_period_start") else None,
            current_period_end=datetime.fromisoformat(data["current_period_end"].replace("Z", "+00:00"))
                if data.get("current_period_end") else None,
            trial_end=datetime.fromisoformat(data["trial_end"].replace("Z", "+00:00"))
                if data.get("trial_end") else None,
            cancel_at=datetime.fromisoformat(data["cancel_at"].replace("Z", "+00:00"))
                if data.get("cancel_at") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at") else None,
        )

    def _parse_invoice(self, data: dict) -> Invoice:
        """Parse invoice from API response."""
        return Invoice(
            invoice_id=data["invoice_id"],
            tenant_id=data["tenant_id"],
            subscription_id=data.get("subscription_id"),
            amount=float(data.get("amount", 0)),
            currency=data.get("currency", "USD"),
            status=PaymentStatus(data.get("status", "pending")),
            line_items=data.get("line_items", []),
            description=data.get("description"),
            due_date=datetime.fromisoformat(data["due_date"].replace("Z", "+00:00"))
                if data.get("due_date") else None,
            paid_at=datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00"))
                if data.get("paid_at") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at") else None,
        )

    # -------------------------------------------------------------------------
    # Plans
    # -------------------------------------------------------------------------

    async def get_plans(
        self,
        product: Optional[str] = None,
    ) -> List[Plan]:
        """
        Get available subscription plans.

        Args:
            product: Filter by product (e.g., "mantra")

        Returns:
            List of available plans

        Raises:
            NetworkError: If network request fails
        """
        try:
            params = {}
            if product:
                params["product"] = product

            response = await self._client.get(
                "/api/v1/billing/plans",
                params=params
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            plans_data = data.get("data", [])
            return [self._parse_plan(p) for p in plans_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def get_plan(self, plan_id: str) -> Plan:
        """
        Get specific plan by ID.

        Args:
            plan_id: Plan ID

        Returns:
            Plan details

        Raises:
            BillingError: If plan not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(f"/api/v1/billing/plans/{plan_id}")

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            plan_data = data.get("data", data)
            return self._parse_plan(plan_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Subscriptions
    # -------------------------------------------------------------------------

    async def get_subscription(
        self,
        tenant_id: str,
        product: Optional[str] = None,
    ) -> Optional[Subscription]:
        """
        Get current subscription for tenant.

        Args:
            tenant_id: Tenant UUID
            product: Filter by product

        Returns:
            Current subscription or None

        Raises:
            NetworkError: If network request fails
        """
        try:
            params = {"tenant_id": tenant_id}
            if product:
                params["product"] = product

            response = await self._client.get(
                "/api/v1/billing/subscriptions",
                params=params
            )

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            sub_data = data.get("data")

            if not sub_data:
                return None

            # If list, return first matching
            if isinstance(sub_data, list):
                if len(sub_data) == 0:
                    return None
                return self._parse_subscription(sub_data[0])

            return self._parse_subscription(sub_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def list_subscriptions(self, tenant_id: str) -> List[Subscription]:
        """
        List all subscriptions for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of subscriptions

        Raises:
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                "/api/v1/billing/subscriptions",
                params={"tenant_id": tenant_id}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            subs_data = data.get("data", [])
            return [self._parse_subscription(s) for s in subs_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def create_subscription(
        self,
        tenant_id: str,
        plan_id: str,
        product: str,
        trial_days: Optional[int] = None,
    ) -> Subscription:
        """
        Create a new subscription.

        Args:
            tenant_id: Tenant UUID
            plan_id: Plan to subscribe to
            product: Product code (e.g., "mantra")
            trial_days: Optional trial period

        Returns:
            Created subscription

        Raises:
            BillingError: If subscription creation fails
            NetworkError: If network request fails
        """
        try:
            payload = {
                "tenant_id": tenant_id,
                "plan_id": plan_id,
                "product": product,
            }
            if trial_days is not None:
                payload["trial_days"] = trial_days

            response = await self._client.post(
                "/api/v1/billing/subscriptions",
                json=payload
            )

            if response.status_code not in (200, 201):
                self._handle_error(response)

            data = response.json()
            sub_data = data.get("data", data)
            return self._parse_subscription(sub_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def upgrade_subscription(
        self,
        subscription_id: str,
        plan_id: str,
    ) -> Subscription:
        """
        Upgrade/downgrade subscription to different plan.

        Args:
            subscription_id: Current subscription ID
            plan_id: New plan ID

        Returns:
            Updated subscription

        Raises:
            BillingError: If upgrade fails
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/billing/subscriptions/{subscription_id}/change-plan",
                json={"plan_id": plan_id}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            sub_data = data.get("data", data)
            return self._parse_subscription(sub_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> Subscription:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            at_period_end: Cancel at end of billing period (True) or immediately (False)

        Returns:
            Canceled subscription

        Raises:
            BillingError: If cancellation fails
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/billing/subscriptions/{subscription_id}/cancel",
                json={"at_period_end": at_period_end}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            sub_data = data.get("data", data)
            return self._parse_subscription(sub_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def reactivate_subscription(
        self,
        subscription_id: str,
    ) -> Subscription:
        """
        Reactivate a canceled subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            Reactivated subscription

        Raises:
            BillingError: If reactivation fails
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/billing/subscriptions/{subscription_id}/reactivate"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            sub_data = data.get("data", data)
            return self._parse_subscription(sub_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Invoices
    # -------------------------------------------------------------------------

    async def get_invoices(
        self,
        tenant_id: str,
        limit: int = 10,
    ) -> List[Invoice]:
        """
        Get invoices for tenant.

        Args:
            tenant_id: Tenant UUID
            limit: Max number of invoices to return

        Returns:
            List of invoices

        Raises:
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                "/api/v1/billing/invoices",
                params={
                    "tenant_id": tenant_id,
                    "limit": limit,
                }
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            invoices_data = data.get("data", [])
            return [self._parse_invoice(i) for i in invoices_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def get_invoice(self, invoice_id: str) -> Invoice:
        """
        Get specific invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice details

        Raises:
            BillingError: If invoice not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                f"/api/v1/billing/invoices/{invoice_id}"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            invoice_data = data.get("data", data)
            return self._parse_invoice(invoice_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Usage
    # -------------------------------------------------------------------------

    async def get_usage(
        self,
        tenant_id: str,
        product: Optional[str] = None,
    ) -> UsageMetrics:
        """
        Get usage metrics for tenant.

        Args:
            tenant_id: Tenant UUID
            product: Filter by product

        Returns:
            Usage metrics

        Raises:
            NetworkError: If network request fails
        """
        try:
            params = {"tenant_id": tenant_id}
            if product:
                params["product"] = product

            response = await self._client.get(
                "/api/v1/billing/usage",
                params=params
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            usage_data = data.get("data", data)

            return UsageMetrics(
                tenant_id=usage_data.get("tenant_id", tenant_id),
                period_start=datetime.fromisoformat(usage_data["period_start"].replace("Z", "+00:00"))
                    if usage_data.get("period_start") else datetime.now(),
                period_end=datetime.fromisoformat(usage_data["period_end"].replace("Z", "+00:00"))
                    if usage_data.get("period_end") else datetime.now(),
                metrics=usage_data.get("metrics", {}),
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")
