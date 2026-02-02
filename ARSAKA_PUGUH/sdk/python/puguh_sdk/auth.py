"""
PUGUH SDK - Auth Module

Authentication operations for PUGUH Platform.
Handles user registration, login, token management, and OAuth flows.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum
import httpx

from .exceptions import (
    PuguhError,
    AuthError,
    ValidationError,
    NetworkError,
)


class AuthProvider(str, Enum):
    """Authentication provider types."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # seconds


@dataclass
class UserContext:
    """
    User context extracted from validated token.

    Contains user identity, tenant context, roles, and subscriptions.
    This is what your app receives after validating a PUGUH token.
    """
    user_id: str
    email: str
    display_name: str

    # Tenant context
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    tenant_plan: Optional[str] = None

    # Project context (optional)
    project_id: Optional[str] = None
    project_name: Optional[str] = None

    # Roles (both platform and product roles)
    roles: List[str] = None
    is_owner: bool = False

    # Subscriptions by product
    subscriptions: dict = None

    # Token metadata
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.subscriptions is None:
            self.subscriptions = {}

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_subscription(self, product: str) -> bool:
        """Check if user has active subscription to product."""
        sub = self.subscriptions.get(product)
        return sub is not None and sub.get("status") == "active"

    def is_admin(self, product: Optional[str] = None) -> bool:
        """Check if user is admin (platform or product-specific)."""
        if product:
            return f"{product}:admin" in self.roles
        return "admin" in self.roles or "owner" in self.roles


@dataclass
class User:
    """User profile data."""
    user_id: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    email_verified: bool = False
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class AuthClient:
    """
    Authentication client for PUGUH Platform.

    Handles:
    - User registration and login
    - Token refresh and validation
    - Password reset flow
    - OAuth integration (Google, GitHub)

    Example:
        ```python
        from puguh_sdk import PuguhClient

        client = PuguhClient(base_url="https://api.puguh.io")

        # Register new user
        user = await client.auth.register(
            email="user@example.com",
            password="secure_password",
            display_name="John Doe"
        )

        # Login
        tokens = await client.auth.login(
            email="user@example.com",
            password="secure_password"
        )

        # Validate token (in your backend)
        user_context = await client.auth.validate_token(tokens.access_token)
        print(user_context.tenant_id, user_context.roles)
        ```
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize auth client.

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

        if response.status_code == 401:
            raise AuthError(message, error_code, details)
        elif response.status_code == 422:
            raise ValidationError(message, details)
        else:
            raise PuguhError(message, error_code, details, response.status_code)

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> User:
        """
        Register a new user account.

        Args:
            email: User email address
            password: User password (min 8 characters)
            display_name: User display name

        Returns:
            Created user profile

        Raises:
            ValidationError: If input validation fails
            AuthError: If email already exists
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "display_name": display_name,
                }
            )

            if response.status_code not in (200, 201):
                self._handle_error(response)

            data = response.json()
            user_data = data.get("data", data)

            return User(
                user_id=user_data["user_id"],
                email=user_data["email"],
                display_name=user_data["display_name"],
                avatar_url=user_data.get("avatar_url"),
                email_verified=user_data.get("email_verified", False),
                created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00"))
                    if user_data.get("created_at") else None,
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def login(
        self,
        email: str,
        password: str,
        tenant_id: Optional[str] = None,
    ) -> TokenPair:
        """
        Login with email and password.

        Args:
            email: User email address
            password: User password
            tenant_id: Optional tenant ID to set context

        Returns:
            Token pair (access_token + refresh_token)

        Raises:
            AuthError: If credentials are invalid
            NetworkError: If network request fails
        """
        try:
            payload = {
                "email": email,
                "password": password,
            }
            if tenant_id:
                payload["tenant_id"] = tenant_id

            response = await self._client.post(
                "/api/v1/auth/login",
                json=payload
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            token_data = data.get("data", data)

            return TokenPair(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> TokenPair:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            AuthError: If refresh token is invalid or expired
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            token_data = data.get("data", data)

            return TokenPair(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def validate_token(
        self,
        access_token: str,
    ) -> UserContext:
        """
        Validate access token and get user context.

        Use this in your backend middleware to validate tokens
        from PUGUH and extract user/tenant information.

        Args:
            access_token: JWT access token to validate

        Returns:
            UserContext with user identity, tenant, roles, and subscriptions

        Raises:
            AuthError: If token is invalid or expired
            NetworkError: If network request fails

        Example:
            ```python
            # In your FastAPI middleware
            async def validate_puguh_token(request: Request):
                token = request.headers.get("Authorization", "").replace("Bearer ", "")
                user_context = await puguh.auth.validate_token(token)
                request.state.user = user_context
                return user_context
            ```
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/validate",
                json={"access_token": access_token}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            user_data = data.get("data", data)

            return UserContext(
                user_id=user_data["user_id"],
                email=user_data["email"],
                display_name=user_data.get("display_name", ""),
                tenant_id=user_data.get("tenant_id"),
                tenant_name=user_data.get("tenant_name"),
                tenant_plan=user_data.get("tenant_plan"),
                project_id=user_data.get("project_id"),
                project_name=user_data.get("project_name"),
                roles=user_data.get("roles", []),
                is_owner=user_data.get("is_owner", False),
                subscriptions=user_data.get("subscriptions", {}),
                issued_at=datetime.fromtimestamp(user_data["iat"])
                    if user_data.get("iat") else None,
                expires_at=datetime.fromtimestamp(user_data["exp"])
                    if user_data.get("exp") else None,
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def logout(
        self,
        access_token: str,
    ) -> bool:
        """
        Logout and invalidate token.

        Args:
            access_token: Token to invalidate

        Returns:
            True if logout successful

        Raises:
            AuthError: If token is invalid
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/logout",
                json={"access_token": access_token}
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def verify_email(
        self,
        token: str,
    ) -> bool:
        """
        Verify email address using verification token.

        Args:
            token: Email verification token (from email link)

        Returns:
            True if verification successful

        Raises:
            AuthError: If token is invalid or expired
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/verify-email",
                json={"token": token}
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def forgot_password(
        self,
        email: str,
    ) -> bool:
        """
        Request password reset email.

        Args:
            email: Email address for password reset

        Returns:
            True if reset email sent (always returns true for security)

        Raises:
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/forgot-password",
                json={"email": email}
            )

            # Always return success for security (don't reveal if email exists)
            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Reset password using reset token.

        Args:
            token: Password reset token (from email link)
            new_password: New password (min 8 characters)

        Returns:
            True if password reset successful

        Raises:
            AuthError: If token is invalid or expired
            ValidationError: If new password doesn't meet requirements
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": token,
                    "new_password": new_password,
                }
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    def get_oauth_url(
        self,
        provider: AuthProvider,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """
        Get OAuth authorization URL for social login.

        Args:
            provider: OAuth provider (google, github)
            redirect_uri: Callback URL after OAuth
            state: Optional state parameter for CSRF protection

        Returns:
            OAuth authorization URL to redirect user to

        Example:
            ```python
            # Generate OAuth URL
            oauth_url = client.auth.get_oauth_url(
                provider=AuthProvider.GOOGLE,
                redirect_uri="https://myapp.com/callback",
                state="random_state_string"
            )

            # Redirect user to oauth_url
            return RedirectResponse(oauth_url)
            ```
        """
        base_url = str(self._client.base_url).rstrip("/")
        url = f"{base_url}/api/v1/auth/oauth/{provider.value}?redirect_uri={redirect_uri}"
        if state:
            url += f"&state={state}"
        return url

    async def exchange_oauth_code(
        self,
        provider: AuthProvider,
        code: str,
        redirect_uri: str,
    ) -> TokenPair:
        """
        Exchange OAuth authorization code for tokens.

        Args:
            provider: OAuth provider (google, github)
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect_uri used in get_oauth_url

        Returns:
            Token pair (access_token + refresh_token)

        Raises:
            AuthError: If code is invalid or exchange fails
            NetworkError: If network request fails

        Example:
            ```python
            # In your OAuth callback handler
            @app.get("/callback")
            async def oauth_callback(code: str, state: str):
                tokens = await client.auth.exchange_oauth_code(
                    provider=AuthProvider.GOOGLE,
                    code=code,
                    redirect_uri="https://myapp.com/callback"
                )
                # Store tokens and redirect to app
            ```
        """
        try:
            response = await self._client.post(
                f"/api/v1/auth/oauth/{provider.value}/callback",
                json={
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            token_data = data.get("data", data)

            return TokenPair(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def get_me(self) -> User:
        """
        Get current authenticated user profile.

        Returns:
            User profile

        Raises:
            AuthError: If not authenticated
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get("/api/v1/auth/me")

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            user_data = data.get("data", data)

            return User(
                user_id=user_data["user_id"],
                email=user_data["email"],
                display_name=user_data["display_name"],
                avatar_url=user_data.get("avatar_url"),
                auth_provider=AuthProvider(user_data.get("auth_provider", "local")),
                email_verified=user_data.get("email_verified", False),
                created_at=datetime.fromisoformat(user_data["created_at"].replace("Z", "+00:00"))
                    if user_data.get("created_at") else None,
                last_login_at=datetime.fromisoformat(user_data["last_login_at"].replace("Z", "+00:00"))
                    if user_data.get("last_login_at") else None,
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")
