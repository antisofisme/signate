"""
PUGUH SDK - Main Client

Unified client for PUGUH Platform API.
Provides access to auth, tenant, project, billing, and core services.
"""

from typing import Optional, Callable
import httpx

from .auth import AuthClient
from .tenant import TenantClient
from .project import ProjectClient
from .billing import BillingClient
from .exceptions import (
    PuguhError,
    AuthError,
    RateLimitError,
    NetworkError,
)


class PuguhClient:
    """
    Main client for PUGUH Platform.

    Provides unified access to all PUGUH services:
    - auth: Authentication and user management
    - tenants: Multi-tenant organization management
    - projects: Project management within tenants
    - billing: Subscription and billing management

    Authentication Methods:
    1. User token (access_token): For end-user sessions
    2. API key (api_key): For service-to-service communication

    Example:
        ```python
        from puguh_sdk import PuguhClient

        # For user context (frontend apps)
        client = PuguhClient(
            base_url="https://api.puguh.io",
            access_token="user_jwt_token"
        )

        # For service context (backend services)
        client = PuguhClient(
            base_url="https://api.puguh.io",
            api_key="pk_live_xxxxxxxxxxxx"
        )

        # Use services
        tenants = await client.tenants.list()
        plans = await client.billing.get_plans()
        ```
    """

    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        on_token_refresh: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Initialize PUGUH client.

        Args:
            base_url: PUGUH API base URL (e.g., "https://api.puguh.io")
            access_token: JWT access token for user authentication
            api_key: API key for service authentication (format: pk_live_xxx)
            timeout: Request timeout in seconds
            max_retries: Max retry attempts on failure
            retry_delay: Initial retry delay in seconds
            on_token_refresh: Callback when token is refreshed
            on_error: Callback when error occurs
        """
        self.base_url = base_url.rstrip("/")
        self._access_token = access_token
        self._api_key = api_key
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._on_token_refresh = on_token_refresh
        self._on_error = on_error

        # Current context
        self._tenant_id: Optional[str] = None
        self._project_id: Optional[str] = None
        self._user_id: Optional[str] = None  # For impersonation

        # Build headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "puguh-sdk-python/1.0.0",
        }

        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif api_key:
            headers["X-API-Key"] = api_key

        # Create HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers,
        )

        # Initialize service clients
        self._auth = AuthClient(self._client)
        self._tenants = TenantClient(self._client)
        self._projects = ProjectClient(self._client)
        self._billing = BillingClient(self._client)

    @property
    def auth(self) -> AuthClient:
        """Authentication client."""
        return self._auth

    @property
    def tenants(self) -> TenantClient:
        """Tenant management client."""
        return self._tenants

    @property
    def projects(self) -> ProjectClient:
        """Project management client."""
        return self._projects

    @property
    def billing(self) -> BillingClient:
        """Billing management client."""
        return self._billing

    # -------------------------------------------------------------------------
    # Context Management
    # -------------------------------------------------------------------------

    def set_access_token(self, token: str) -> None:
        """
        Update access token.

        Use this after login or token refresh.

        Args:
            token: New JWT access token
        """
        self._access_token = token
        self._client.headers["Authorization"] = f"Bearer {token}"
        # Remove API key if using token
        if "X-API-Key" in self._client.headers:
            del self._client.headers["X-API-Key"]

    def set_api_key(self, api_key: str) -> None:
        """
        Update API key.

        Args:
            api_key: New API key
        """
        self._api_key = api_key
        self._client.headers["X-API-Key"] = api_key
        # Remove token if using API key
        if "Authorization" in self._client.headers:
            del self._client.headers["Authorization"]

    def set_tenant_context(self, tenant_id: str) -> None:
        """
        Set tenant context for subsequent requests.

        Required for service account operations that span tenants.

        Args:
            tenant_id: Tenant UUID to operate on
        """
        self._tenant_id = tenant_id
        self._client.headers["X-Tenant-ID"] = tenant_id

    def set_project_context(self, project_id: str) -> None:
        """
        Set project context for subsequent requests.

        Args:
            project_id: Project UUID to operate on
        """
        self._project_id = project_id
        self._client.headers["X-Project-ID"] = project_id

    def set_user_context(self, user_id: str) -> None:
        """
        Set user context for impersonation (admin only).

        Allows service accounts to operate on behalf of users.
        Requires appropriate admin permissions.

        Args:
            user_id: User UUID to impersonate
        """
        self._user_id = user_id
        self._client.headers["X-User-ID"] = user_id

    def clear_context(self) -> None:
        """Clear all context headers."""
        self._tenant_id = None
        self._project_id = None
        self._user_id = None

        for header in ["X-Tenant-ID", "X-Project-ID", "X-User-ID"]:
            if header in self._client.headers:
                del self._client.headers[header]

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._client.aclose()

    async def __aenter__(self) -> "PuguhClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Check if PUGUH API is healthy.

        Returns:
            True if API is healthy

        Raises:
            NetworkError: If health check fails
        """
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except httpx.RequestError as e:
            raise NetworkError(f"Health check failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Quick helpers
    # -------------------------------------------------------------------------

    async def validate_token(self, token: Optional[str] = None) -> "UserContext":
        """
        Validate token and get user context.

        Shortcut for client.auth.validate_token().

        Args:
            token: Token to validate (uses client's token if not provided)

        Returns:
            User context from token
        """
        from .auth import UserContext
        token_to_validate = token or self._access_token
        if not token_to_validate:
            raise AuthError("No token provided")
        return await self._auth.validate_token(token_to_validate)

    async def get_current_user(self) -> "User":
        """
        Get current authenticated user.

        Shortcut for client.auth.get_me().

        Returns:
            Current user profile
        """
        return await self._auth.get_me()


# =============================================================================
# Convenience function for quick setup
# =============================================================================

def create_client(
    base_url: str = "https://api.puguh.io",
    access_token: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> PuguhClient:
    """
    Create PUGUH client with default settings.

    Args:
        base_url: API base URL
        access_token: User JWT token
        api_key: Service API key
        **kwargs: Additional PuguhClient arguments

    Returns:
        Configured PuguhClient

    Example:
        ```python
        from puguh_sdk import create_client

        # User token
        client = create_client(access_token="jwt_token")

        # API key
        client = create_client(api_key="pk_live_xxx")
        ```
    """
    return PuguhClient(
        base_url=base_url,
        access_token=access_token,
        api_key=api_key,
        **kwargs
    )
