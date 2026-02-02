"""
CSRF Protection Middleware

Implements Double Submit Cookie pattern for CSRF protection.
Required for cookie-based authentication.

Pattern:
1. Server sets CSRF token in a non-httpOnly cookie (JS-readable)
2. Client reads cookie and sends token in X-CSRF-Token header
3. Server validates header matches cookie

Why this works:
- Attacker site cannot read cookies from our domain (Same-Origin Policy)
- Attacker can make browser send cookies, but cannot read them
- Without reading the cookie, attacker cannot set the header

Combined with:
- SameSite=Strict on auth cookies (already implemented)
- Origin/Referer header validation

Source: OWASP CSRF Prevention Cheat Sheet
"""

import secrets
from typing import Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection using Double Submit Cookie pattern.

    Safe methods (GET, HEAD, OPTIONS) are allowed without CSRF token.
    State-changing methods (POST, PUT, PATCH, DELETE) require token.
    """

    # Methods that don't change state (safe methods)
    SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}

    # Paths to exclude from CSRF protection (public APIs, webhooks, auth)
    EXCLUDED_PATHS: Set[str] = {
        "/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        # Auth endpoints (user doesn't have CSRF token yet)
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/refresh",
        # Webhook endpoints would go here
    }

    # Paths with API key auth (don't need CSRF)
    API_KEY_PATHS: Set[str] = {
        "/api/v1/products/",  # Products accessed via API key
    }

    def __init__(
        self,
        app,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_secure: bool = True,
        cookie_samesite: str = "strict",
        enabled: bool = True,
    ):
        """Initialize CSRF middleware.

        Args:
            app: FastAPI application
            cookie_name: Name of CSRF cookie
            header_name: Name of CSRF header
            cookie_secure: Set Secure flag on cookie
            cookie_samesite: SameSite attribute (strict, lax, none)
            enabled: Enable/disable CSRF protection
        """
        super().__init__(app)
        self._cookie_name = cookie_name
        self._header_name = header_name
        self._cookie_secure = cookie_secure
        self._cookie_samesite = cookie_samesite
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply CSRF protection."""
        # Skip if disabled
        if not self._enabled:
            return await call_next(request)

        # Skip excluded paths
        path = request.url.path
        if self._is_excluded_path(path):
            return await call_next(request)

        # Skip if API key authentication is used
        if self._has_api_key_auth(request):
            return await call_next(request)

        # Safe methods: ensure CSRF token cookie exists
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            return self._ensure_csrf_cookie(request, response)

        # State-changing methods: validate CSRF token
        if not self._validate_csrf_token(request):
            return self._csrf_error_response()

        # Origin validation (additional protection)
        if not self._validate_origin(request):
            return self._origin_error_response()

        # CSRF validation passed
        response = await call_next(request)
        return self._ensure_csrf_cookie(request, response)

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from CSRF protection."""
        if path in self.EXCLUDED_PATHS:
            return True

        # Check API key paths
        for api_path in self.API_KEY_PATHS:
            if path.startswith(api_path):
                return True

        return False

    def _has_api_key_auth(self, request: Request) -> bool:
        """Check if request uses API key authentication."""
        # API key in header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return True

        # API key in Authorization header (Bearer token format for API keys)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("ApiKey "):
            return True

        return False

    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token from header matches cookie.

        The token must be:
        1. Present in cookie
        2. Present in header
        3. Both must match

        Returns:
            True if valid, False otherwise
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self._cookie_name)
        if not cookie_token:
            return False

        # Get token from header
        header_token = request.headers.get(self._header_name)
        if not header_token:
            return False

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(cookie_token, header_token)

    def _validate_origin(self, request: Request) -> bool:
        """Validate Origin/Referer header.

        Checks that request comes from same origin.
        This is additional protection on top of CSRF token.

        Returns:
            True if valid, False otherwise
        """
        # Get Origin header (preferred)
        origin = request.headers.get("Origin")

        # Fall back to Referer header
        if not origin:
            referer = request.headers.get("Referer")
            if referer:
                # Extract origin from referer URL
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                origin = f"{parsed.scheme}://{parsed.netloc}"

        # If no origin info, reject (could be same-site but safer to reject)
        if not origin:
            # Allow for same-site requests that don't send Origin
            # Some browsers don't send Origin for same-site POST
            return True  # Be lenient here, CSRF token is primary protection

        # Get expected origin from Host header
        host = request.headers.get("Host", "")
        scheme = "https" if self._cookie_secure else "http"
        expected_origin = f"{scheme}://{host}"

        # Compare origins
        return origin == expected_origin

    def _ensure_csrf_cookie(self, request: Request, response: Response) -> Response:
        """Ensure CSRF token cookie is set.

        Generates new token if not present.
        Token is NOT httpOnly so JavaScript can read it.
        """
        # Check if token already exists
        existing_token = request.cookies.get(self._cookie_name)
        if existing_token:
            return response

        # Generate new token
        token = secrets.token_urlsafe(32)

        # Set cookie (NOT httpOnly - JS needs to read it)
        response.set_cookie(
            key=self._cookie_name,
            value=token,
            httponly=False,  # JS must be able to read this
            secure=self._cookie_secure,
            samesite=self._cookie_samesite,
            path="/",
            max_age=86400 * 7,  # 7 days
        )

        return response

    def _csrf_error_response(self) -> JSONResponse:
        """Return CSRF validation error response."""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {
                    "code": "CSRF_VALIDATION_FAILED",
                    "message": "CSRF token validation failed. Please refresh the page and try again.",
                }
            }
        )

    def _origin_error_response(self) -> JSONResponse:
        """Return origin validation error response."""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_ORIGIN",
                    "message": "Request origin validation failed.",
                }
            }
        )


# ============================================================================
# Frontend Integration Guide
# ============================================================================
#
# Frontend must:
# 1. Read CSRF token from cookie on page load
# 2. Include token in X-CSRF-Token header for all state-changing requests
#
# Example (JavaScript):
#
# function getCsrfToken() {
#     const cookies = document.cookie.split(';');
#     for (const cookie of cookies) {
#         const [name, value] = cookie.trim().split('=');
#         if (name === 'csrf_token') {
#             return value;
#         }
#     }
#     return null;
# }
#
# // Axios interceptor
# axios.interceptors.request.use((config) => {
#     if (!['GET', 'HEAD', 'OPTIONS'].includes(config.method.toUpperCase())) {
#         const csrfToken = getCsrfToken();
#         if (csrfToken) {
#             config.headers['X-CSRF-Token'] = csrfToken;
#         }
#     }
#     return config;
# });
#
# ============================================================================
