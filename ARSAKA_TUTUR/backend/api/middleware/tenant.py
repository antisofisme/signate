"""
Tenant middleware - extracts and validates X-Tenant-ID header.
"""

from typing import Callable, Optional
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ...core.entities import RequestContext
from ...shared.logging import get_logger
from ...shared.exceptions import TenantNotFoundError

logger = get_logger(__name__)

# Header name
TENANT_HEADER = "X-Tenant-ID"
REQUEST_ID_HEADER = "X-Request-ID"

# Paths that don't require tenant (exact match or specific prefixes)
TENANT_EXEMPT_PATHS_EXACT = [
    "/",
    "/health",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
]
TENANT_EXEMPT_PREFIXES = [
    "/docs/",
    "/openapi",
    "/redoc/",
]


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant from request.

    Sets `request.state.context` with RequestContext.
    """

    def __init__(self, app, tenant_service=None):
        super().__init__(app)
        self.tenant_service = tenant_service

    async def dispatch(self, request: Request, call_next: Callable):
        # Generate request ID
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())

        # Check if path is exempt
        if self._is_exempt(request.url.path):
            request.state.context = RequestContext(request_id=request_id)
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response

        # Get tenant ID from header
        tenant_id = request.headers.get(TENANT_HEADER)
        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "code": "MISSING_TENANT",
                        "message": f"Missing required header: {TENANT_HEADER}",
                    }
                },
                headers={REQUEST_ID_HEADER: request_id},
            )

        # Validate tenant
        tenant_config = None
        if self.tenant_service:
            try:
                tenant_config = await self.tenant_service.get_tenant(tenant_id)
            except TenantNotFoundError:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": {
                            "code": "TENANT_NOT_FOUND",
                            "message": f"Tenant '{tenant_id}' not found or inactive",
                        }
                    },
                    headers={REQUEST_ID_HEADER: request_id},
                )

        # Create request context
        context = RequestContext(
            request_id=request_id,
            tenant_id=tenant_id,
            tenant_config=tenant_config,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )

        # Set context on request state
        request.state.context = context

        logger.debug(f"Request {request_id} for tenant {tenant_id}: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Add request ID to response
        response.headers[REQUEST_ID_HEADER] = request_id

        return response

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from tenant requirement."""
        # Check exact matches first
        if path in TENANT_EXEMPT_PATHS_EXACT:
            return True
        # Check prefix matches
        for prefix in TENANT_EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP from request."""
        # Check forwarded headers first (for proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return None
