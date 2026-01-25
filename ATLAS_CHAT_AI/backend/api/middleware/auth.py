"""
Authentication Middleware

Validates JWT tokens and API keys.
"""

from typing import Optional, Callable, Awaitable
from datetime import datetime
import jwt

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ...shared.logging import get_logger
from ...config import get_settings

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware.

    Supports:
    - JWT Bearer tokens (Authorization: Bearer <token>)
    - API Keys (X-API-Key: <key>)

    Unauthenticated requests are rejected unless path is in bypass list.
    """

    def __init__(
        self,
        app,
        jwt_secret: Optional[str] = None,
        jwt_algorithm: str = "HS256",
        bypass_paths: Optional[list] = None,
        require_auth: bool = True,
    ):
        super().__init__(app)
        self.jwt_secret = jwt_secret or get_settings().jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.require_auth = require_auth
        self.bypass_paths = bypass_paths or [
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
        ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with authentication."""
        # Skip for bypass paths
        if self._should_bypass(request.url.path):
            return await call_next(request)

        # Try to authenticate
        auth_result = await self._authenticate(request)

        if not auth_result and self.require_auth:
            return self._unauthorized_response("Authentication required")

        if auth_result:
            # Set auth info on request state
            request.state.user_id = auth_result.get("user_id")
            request.state.auth_type = auth_result.get("auth_type")
            request.state.permissions = auth_result.get("permissions", [])

        return await call_next(request)

    def _should_bypass(self, path: str) -> bool:
        """Check if path should bypass auth."""
        for bypass_path in self.bypass_paths:
            if path == bypass_path or path.startswith(f"{bypass_path}/"):
                return True
        return False

    async def _authenticate(self, request: Request) -> Optional[dict]:
        """
        Attempt to authenticate the request.

        Returns auth payload or None if not authenticated.
        """
        # Try JWT Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return await self._verify_jwt(token)

        # Try API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return await self._verify_api_key(api_key)

        return None

    async def _verify_jwt(self, token: str) -> Optional[dict]:
        """Verify JWT token and extract payload."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                logger.debug("JWT token expired")
                return None

            return {
                "user_id": payload.get("sub") or payload.get("user_id"),
                "tenant_id": payload.get("tenant_id"),
                "auth_type": "jwt",
                "permissions": payload.get("permissions", []),
            }

        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid JWT: {e}")
            return None

    async def _verify_api_key(self, api_key: str) -> Optional[dict]:
        """
        Verify API key.

        In production, this should validate against the database.
        """
        try:
            # Get container and validate key
            from ...container import _container

            if not _container or not _container._initialized:
                logger.warning("Container not initialized for API key validation")
                return None

            # Query database for API key
            # Note: In production, use proper key validation with hashing
            pool = _container._db_pool.pool

            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, tenant_id, name, permissions, rate_limit_per_minute,
                           expires_at, is_active
                    FROM api_keys
                    WHERE key_prefix = $1
                      AND is_active = TRUE
                      AND (expires_at IS NULL OR expires_at > NOW())
                    """,
                    api_key[:12] if len(api_key) >= 12 else api_key,
                )

                if not row:
                    logger.debug("API key not found or inactive")
                    return None

                # Verify full key hash (in production)
                # For now, just use prefix matching

                # Update last used
                await conn.execute(
                    "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
                    row["id"],
                )

                import json
                permissions = row["permissions"]
                if isinstance(permissions, str):
                    permissions = json.loads(permissions)

                return {
                    "user_id": f"apikey:{row['id']}",
                    "tenant_id": row["tenant_id"],
                    "auth_type": "api_key",
                    "permissions": permissions or [],
                    "api_key_name": row["name"],
                    "rate_limit": row["rate_limit_per_minute"],
                }

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return unauthorized response."""
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": message,
                },
            },
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )


def create_jwt_token(
    user_id: str,
    tenant_id: str,
    permissions: Optional[list] = None,
    expires_in_seconds: int = 3600,
    secret: Optional[str] = None,
) -> str:
    """
    Create a JWT token.

    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        permissions: List of permissions
        expires_in_seconds: Token expiration time
        secret: JWT secret (uses settings if not provided)

    Returns:
        JWT token string
    """
    import time

    secret = secret or get_settings().jwt_secret

    payload = {
        "sub": user_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "permissions": permissions or [],
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds,
    }

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt_token(token: str, secret: Optional[str] = None) -> Optional[dict]:
    """
    Decode a JWT token.

    Args:
        token: JWT token string
        secret: JWT secret (uses settings if not provided)

    Returns:
        Token payload or None if invalid
    """
    try:
        secret = secret or get_settings().jwt_secret
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
