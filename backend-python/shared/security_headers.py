"""
Security Headers Middleware
Adds security headers to all HTTP responses to prevent common attacks
"""

from fastapi import Request
from fastapi.responses import Response
from typing import Callable
import json


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses
    Prevents: XSS, clickjacking, MIME sniffing, etc.
    """
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check if this is a media/video streaming endpoint
        path = scope.get("path", "")
        is_media_endpoint = (
            path.startswith("/content/videos/") or
            path.startswith("/content/images/") or
            path.endswith(".m3u8") or
            path.endswith(".ts")
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))

                # Security headers - different CSP for media endpoints
                if is_media_endpoint:
                    # Relaxed CSP for media files - allow embedding and playback
                    csp_policy = b"default-src 'self'; media-src 'self' blob: http: https:;"
                else:
                    # Strict CSP for API/pages
                    csp_policy = b"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' ws: wss:; media-src 'self' blob:; frame-ancestors 'none';"

                security_headers = {
                    # Prevent MIME type sniffing
                    b"x-content-type-options": b"nosniff",

                    # Content Security Policy
                    b"content-security-policy": csp_policy,

                    # Control referrer information
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                }

                # Additional security headers for non-media endpoints
                if not is_media_endpoint:
                    security_headers[b"x-frame-options"] = b"DENY"
                    security_headers[b"x-xss-protection"] = b"1; mode=block"
                    security_headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                    security_headers[b"permissions-policy"] = b"geolocation=(), microphone=(), camera=()"

                # Cache control: Allow caching for media files, strict for others
                if is_media_endpoint:
                    # Allow caching for video/image streaming with 1 hour max-age
                    security_headers[b"cache-control"] = b"public, max-age=3600, immutable"
                else:
                    # Prevent browser from caching sensitive data (API responses, etc.)
                    security_headers[b"cache-control"] = b"no-store, no-cache, must-revalidate, proxy-revalidate"
                    security_headers[b"pragma"] = b"no-cache"
                    security_headers[b"expires"] = b"0"

                # Add security headers to response
                for header, value in security_headers.items():
                    headers[header] = value

                # Convert back to list format
                message["headers"] = [(k, v) for k, v in headers.items()]

            await send(message)

        await self.app(scope, receive, send_wrapper)


def configure_security_headers(app):
    """
    Configure security headers for the FastAPI app
    This should be called in main.py
    """
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Additional security configurations
    
    # Disable server header to avoid version disclosure
    @app.middleware("http")
    async def remove_server_header(request: Request, call_next):
        response = await call_next(request)
        # Remove server header that might expose version info
        if "server" in response.headers:
            del response.headers["server"]
        return response
    
    # Add request size limit (100MB default, configurable)
    MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100MB
    
    @app.middleware("http") 
    async def limit_request_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > MAX_REQUEST_SIZE:
                    return Response(
                        content=json.dumps({"detail": "Request too large"}),
                        status_code=413,
                        media_type="application/json"
                    )
            except ValueError:
                pass
        
        return await call_next(request)