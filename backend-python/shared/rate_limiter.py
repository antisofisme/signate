"""
Rate Limiter
Protects endpoints from brute force attacks and abuse

Features:
- In-memory rate limiting (can be upgraded to Redis)
- Configurable rate limits per endpoint
- IP-based tracking
- Automatic cleanup of old records
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from fastapi import HTTPException, Request, status
import threading
import functools
import inspect


class RateLimiter:
    """
    Simple in-memory rate limiter

    Tracks request counts per IP address and enforces limits

    For production with multiple workers, consider using Redis
    """

    def __init__(self):
        self._requests: Dict[str, list] = {}  # {identifier: [timestamps]}
        self._lock = threading.Lock()

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if rate limit is exceeded

        Args:
            identifier: Unique identifier (e.g., IP address)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, retry_after_seconds)

        Example:
            >>> limiter = RateLimiter()
            >>> is_allowed, retry_after = limiter.check_rate_limit("192.168.1.1", max_requests=5, window_seconds=60)
            >>> if not is_allowed:
            ...     print(f"Rate limit exceeded. Retry after {retry_after} seconds")
        """
        with self._lock:
            now = datetime.utcnow()
            cutoff_time = now - timedelta(seconds=window_seconds)

            # Initialize or get existing request timestamps
            if identifier not in self._requests:
                self._requests[identifier] = []

            # Remove old timestamps outside the window
            self._requests[identifier] = [
                ts for ts in self._requests[identifier]
                if ts > cutoff_time
            ]

            # Check if limit exceeded
            current_count = len(self._requests[identifier])

            if current_count >= max_requests:
                # Calculate retry_after based on oldest request
                if self._requests[identifier]:
                    oldest_request = min(self._requests[identifier])
                    retry_after = int((oldest_request + timedelta(seconds=window_seconds) - now).total_seconds())
                    return False, max(1, retry_after)  # At least 1 second
                return False, window_seconds

            # Add current request timestamp
            self._requests[identifier] = [ts for ts in self._requests[identifier]]
            self._requests[identifier].append(now)

            return True, None

    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """
        Cleanup entries older than max_age_seconds

        Call this periodically to prevent memory bloat

        Args:
            max_age_seconds: Maximum age of entries to keep (default: 1 hour)
        """
        with self._lock:
            now = datetime.utcnow()
            cutoff_time = now - timedelta(seconds=max_age_seconds)

            # Remove old entries
            identifiers_to_remove = []
            for identifier, timestamps in self._requests.items():
                # Filter out old timestamps
                filtered = [ts for ts in timestamps if ts > cutoff_time]
                if filtered:
                    self._requests[identifier] = filtered
                else:
                    identifiers_to_remove.append(identifier)

            # Remove empty entries
            for identifier in identifiers_to_remove:
                del self._requests[identifier]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request

    Checks X-Forwarded-For header (for proxies) and falls back to client.host

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as string
    """
    # Check X-Forwarded-For header (for proxies/load balancers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def rate_limit(
    max_requests: int = 5,
    window_seconds: int = 60,
    identifier_func: Callable = None
):
    """
    Rate limiting decorator for FastAPI endpoints

    Args:
        max_requests: Maximum number of requests allowed (default: 5)
        window_seconds: Time window in seconds (default: 60)
        identifier_func: Custom function to get identifier (default: uses IP address)

    Returns:
        Decorator function

    Example:
        >>> @router.post("/login")
        >>> @rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
        >>> def login(request: Request):
        ...     # Login logic here
        ...     pass

    Usage in route:
        >>> from shared.rate_limiter import rate_limit
        >>>
        >>> @router.post("/auth/login")
        >>> @rate_limit(max_requests=5, window_seconds=300)
        >>> def login(request: Request, credentials: LoginRequest):
        ...     # Your login logic
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Find Request object in args/kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request:
                    for key in ["request", "http_request"]:
                        if key in kwargs and isinstance(kwargs[key], Request):
                            request = kwargs[key]
                            break

                if not request:
                    # If no request found, skip rate limiting
                    return await func(*args, **kwargs)

                # Get identifier (default: IP address)
                if identifier_func:
                    identifier = identifier_func(request)
                else:
                    identifier = get_client_ip(request)

                # Check rate limit
                is_allowed, retry_after = _rate_limiter.check_rate_limit(
                    identifier=identifier,
                    max_requests=max_requests,
                    window_seconds=window_seconds
                )

                if not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Too many requests. Please try again in {retry_after} seconds.",
                        headers={"Retry-After": str(retry_after)}
                    )

                # Call the original function
                return await func(*args, **kwargs)

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Find Request object in args/kwargs
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request:
                    for key in ["request", "http_request"]:
                        if key in kwargs and isinstance(kwargs[key], Request):
                            request = kwargs[key]
                            break

                if not request:
                    # If no request found, skip rate limiting
                    return func(*args, **kwargs)

                # Get identifier (default: IP address)
                if identifier_func:
                    identifier = identifier_func(request)
                else:
                    identifier = get_client_ip(request)

                # Check rate limit
                is_allowed, retry_after = _rate_limiter.check_rate_limit(
                    identifier=identifier,
                    max_requests=max_requests,
                    window_seconds=window_seconds
                )

                if not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Too many requests. Please try again in {retry_after} seconds.",
                        headers={"Retry-After": str(retry_after)}
                    )

                # Call the original function
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator


def cleanup_rate_limiter():
    """
    Cleanup old rate limiter entries

    Call this periodically (e.g., via background task or cron job)
    """
    _rate_limiter.cleanup_old_entries()
