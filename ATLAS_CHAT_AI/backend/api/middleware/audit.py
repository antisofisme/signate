"""
Audit Middleware

Logs all API requests for audit trail.
"""

from typing import Callable, Awaitable, Optional
import time
import asyncio
import json
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ...shared.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware.

    Logs requests to audit_logs table asynchronously.
    Does not block requests - logging happens in background.
    """

    def __init__(
        self,
        app,
        bypass_paths: Optional[list] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        super().__init__(app)
        self.bypass_paths = bypass_paths or [
            "/health",
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with audit logging."""
        # Skip for bypass paths
        if self._should_bypass(request.url.path):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Get request info
        request_info = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else None,
            "ip_address": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent"),
        }

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            status = "success" if status_code < 400 else "failure"
        except Exception as e:
            status_code = 500
            status = "error"
            raise
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Get auth info from request state
            tenant_id = getattr(request.state, "tenant_id", None)
            user_id = getattr(request.state, "user_id", None)
            request_id = getattr(request.state, "request_id", None)
            auth_type = getattr(request.state, "auth_type", None)

            # Create audit entry
            audit_entry = {
                "tenant_id": tenant_id,
                "actor_type": auth_type or "anonymous",
                "actor_id": user_id or "anonymous",
                "action": f"{request.method} {request.url.path}",
                "resource_type": self._extract_resource_type(request.url.path),
                "resource_id": self._extract_resource_id(request.url.path),
                "request_id": request_id,
                "ip_address": request_info["ip_address"],
                "details": {
                    **request_info,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
                "status": status,
            }

            # Log asynchronously
            asyncio.create_task(self._log_audit(audit_entry))

        return response

    def _should_bypass(self, path: str) -> bool:
        """Check if path should bypass audit."""
        for bypass_path in self.bypass_paths:
            if path.startswith(bypass_path):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def _extract_resource_type(self, path: str) -> str:
        """Extract resource type from path."""
        # /api/v1/chat -> chat
        # /api/v1/sessions/123 -> sessions
        parts = path.strip("/").split("/")

        # Skip api/v1 prefix
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            return parts[2]

        return parts[0] if parts else "root"

    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path if present."""
        parts = path.strip("/").split("/")

        # Skip api/v1 prefix and look for ID-like patterns
        if len(parts) >= 4 and parts[0] == "api" and parts[1].startswith("v"):
            # /api/v1/sessions/123 -> 123
            # /api/v1/sessions/123/messages -> 123
            potential_id = parts[3]
            # Check if it looks like an ID (UUID or numeric)
            if self._is_id_like(potential_id):
                return potential_id

        return None

    def _is_id_like(self, value: str) -> bool:
        """Check if value looks like an ID."""
        # UUID pattern
        if len(value) == 36 and value.count("-") == 4:
            return True
        # Numeric
        if value.isdigit():
            return True
        # Short UUID
        if len(value) == 32 and all(c in "0123456789abcdef" for c in value.lower()):
            return True
        return False

    async def _log_audit(self, entry: dict) -> None:
        """Log audit entry to database."""
        try:
            from ...container import _container

            if not _container or not _container._initialized:
                # Container not ready, just log to file
                logger.info("AUDIT", extra=entry)
                return

            # Insert into audit_logs table
            pool = _container._db_pool.pool

            async with pool.acquire() as conn:
                # Serialize dict to JSON string for JSONB column
                details_json = json.dumps(entry.get("details") or {})

                await conn.execute(
                    """
                    INSERT INTO audit_logs (
                        tenant_id, actor_type, actor_id, action,
                        resource_type, resource_id, request_id,
                        ip_address, details, status, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
                    )
                    """,
                    entry.get("tenant_id"),
                    entry.get("actor_type"),
                    entry.get("actor_id"),
                    entry.get("action"),
                    entry.get("resource_type"),
                    entry.get("resource_id"),
                    entry.get("request_id"),
                    entry.get("ip_address"),
                    details_json,
                    entry.get("status"),
                    datetime.now(timezone.utc),
                )

        except Exception as e:
            # Don't let audit failures break requests
            logger.warning(f"Failed to log audit entry: {e}")
            logger.info("AUDIT_FALLBACK", extra=entry)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Adds unique request ID to each request.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Add request ID."""
        import uuid

        # Check for existing request ID from header
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set on request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response
