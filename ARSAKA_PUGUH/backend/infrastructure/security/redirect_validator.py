"""
Redirect URL Validator

Prevents open redirect vulnerabilities by validating redirect URLs
against an allowlist of trusted domains.

Open Redirect Attack:
- Attacker crafts URL: https://oursite.com/login?redirect=https://evil.com
- User logs in and gets redirected to evil.com
- Attacker can steal credentials or phish

Prevention:
1. Validate against allowlist of trusted domains
2. Only allow relative paths (same-origin)
3. Reject URLs with authentication credentials

Source: OWASP Open Redirect Prevention Cheat Sheet
"""

import os
import re
from typing import List, Optional, Set
from urllib.parse import urlparse, urljoin


class RedirectValidator:
    """
    Validates redirect URLs to prevent open redirect attacks.

    Usage:
        validator = RedirectValidator(
            allowed_hosts=["app.example.com", "*.example.com"],
            default_redirect="/dashboard"
        )

        # Returns safe URL or default
        safe_url = validator.get_safe_redirect(user_provided_url)
    """

    # Dangerous URL schemes that could be exploited
    BLOCKED_SCHEMES: Set[str] = {"javascript", "data", "vbscript", "file"}

    def __init__(
        self,
        allowed_hosts: Optional[List[str]] = None,
        default_redirect: str = "/",
        allow_relative: bool = True,
    ):
        """Initialize validator.

        Args:
            allowed_hosts: List of allowed hostnames (supports wildcards: *.example.com)
            default_redirect: Default redirect URL if validation fails
            allow_relative: Allow relative URLs (recommended for same-origin)
        """
        self._allowed_hosts = set(allowed_hosts or [])
        self._default_redirect = default_redirect
        self._allow_relative = allow_relative

        # Add allowed hosts from environment
        env_hosts = os.getenv("ALLOWED_REDIRECT_HOSTS", "")
        if env_hosts:
            self._allowed_hosts.update(h.strip() for h in env_hosts.split(","))

        # Compile wildcard patterns
        self._host_patterns = []
        for host in self._allowed_hosts:
            if "*" in host:
                # Convert wildcard to regex
                pattern = host.replace(".", r"\.").replace("*", r"[^.]+")
                self._host_patterns.append(re.compile(f"^{pattern}$", re.IGNORECASE))

    def is_safe_url(self, url: Optional[str], current_host: Optional[str] = None) -> bool:
        """Check if URL is safe for redirect.

        Args:
            url: URL to validate
            current_host: Current request host (for relative URLs)

        Returns:
            True if URL is safe, False otherwise
        """
        if not url:
            return False

        # Strip whitespace and handle URL-encoded strings
        url = url.strip()

        # Block empty or whitespace-only URLs
        if not url:
            return False

        # Block javascript: and other dangerous schemes
        lower_url = url.lower().strip()
        for scheme in self.BLOCKED_SCHEMES:
            if lower_url.startswith(f"{scheme}:"):
                return False

        # Block URLs with credentials (//user:pass@host)
        if re.match(r"^//[^/]*@", url):
            return False

        try:
            parsed = urlparse(url)
        except Exception:
            return False

        # Handle relative URLs (no scheme or netloc)
        if not parsed.scheme and not parsed.netloc:
            if self._allow_relative:
                # Relative URL starting with / is safe
                if url.startswith("/"):
                    # Block protocol-relative URLs (//example.com)
                    if url.startswith("//"):
                        return False
                    # Block path traversal attempts
                    if ".." in url:
                        return False
                    return True
            return False

        # Absolute URL - check against allowlist
        if parsed.scheme not in ("http", "https"):
            return False

        host = parsed.netloc.lower()

        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        # Check exact match
        if host in self._allowed_hosts:
            return True

        # Check current host
        if current_host and host == current_host.lower():
            return True

        # Check wildcard patterns
        for pattern in self._host_patterns:
            if pattern.match(host):
                return True

        return False

    def get_safe_redirect(
        self,
        url: Optional[str],
        current_host: Optional[str] = None
    ) -> str:
        """Get safe redirect URL.

        Args:
            url: User-provided URL to validate
            current_host: Current request host

        Returns:
            Safe URL or default redirect
        """
        if self.is_safe_url(url, current_host):
            return url  # type: ignore
        return self._default_redirect

    def sanitize_url(self, url: Optional[str]) -> Optional[str]:
        """Sanitize URL by removing dangerous parts.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL or None if unsafe
        """
        if not url:
            return None

        # Strip whitespace
        url = url.strip()

        # Remove credentials from URL
        try:
            parsed = urlparse(url)
            if parsed.username or parsed.password:
                # Rebuild URL without credentials
                netloc = parsed.hostname or ""
                if parsed.port:
                    netloc = f"{netloc}:{parsed.port}"
                url = parsed._replace(netloc=netloc).geturl()
            return url
        except Exception:
            return None


# ============================================================================
# Singleton Instance for Dependency Injection
# ============================================================================

_default_validator: Optional[RedirectValidator] = None


def get_redirect_validator() -> RedirectValidator:
    """Get the default redirect validator instance.

    Configured from environment variables:
    - ALLOWED_REDIRECT_HOSTS: Comma-separated list of allowed hosts

    Returns:
        Configured RedirectValidator instance
    """
    global _default_validator

    if _default_validator is None:
        # Default allowed hosts from environment
        allowed_hosts = [
            "localhost",
            "127.0.0.1",
            "*.arsaka.io",
            "*.atlas.io",
        ]

        _default_validator = RedirectValidator(
            allowed_hosts=allowed_hosts,
            default_redirect="/app/dashboard",
            allow_relative=True,
        )

    return _default_validator


def validate_redirect_url(
    url: Optional[str],
    current_host: Optional[str] = None
) -> str:
    """Convenience function to validate redirect URL.

    Args:
        url: User-provided URL
        current_host: Current request host

    Returns:
        Safe redirect URL
    """
    return get_redirect_validator().get_safe_redirect(url, current_host)


# ============================================================================
# FastAPI Dependency
# ============================================================================

from fastapi import Query, Request


async def get_validated_redirect(
    request: Request,
    redirect_url: Optional[str] = Query(None, alias="redirect"),
    return_url: Optional[str] = Query(None, alias="return_url"),
) -> str:
    """FastAPI dependency for validated redirect URL.

    Checks both 'redirect' and 'return_url' query parameters.

    Usage:
        @router.get("/login")
        async def login(redirect_to: str = Depends(get_validated_redirect)):
            # redirect_to is guaranteed safe
            ...
    """
    # Check both parameter names
    url = redirect_url or return_url

    # Get current host
    current_host = request.headers.get("host", "").split(":")[0]

    return validate_redirect_url(url, current_host)
