"""
Password Reset Token Manager
Handles secure token generation and validation for password resets

Features:
- Secure random token generation
- Time-limited tokens (default: 1 hour)
- In-memory storage (can be upgraded to Redis/Database)
- Automatic cleanup of expired tokens

TODO Production: Move to database table with proper email integration
"""

import secrets
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class PasswordResetTokenManager:
    """
    Manages password reset tokens

    In-memory implementation for development. For production with
    multiple workers, use Redis or database table.
    """

    def __init__(self, token_lifetime_minutes: int = 60):
        """
        Args:
            token_lifetime_minutes: How long tokens are valid (default: 1 hour)
        """
        self._tokens: Dict[str, dict] = {}  # {token: {user_id, email, expires_at}}
        self._lock = threading.Lock()
        self._token_lifetime_minutes = token_lifetime_minutes

    def generate_token(self, user_id: int, email: str) -> str:
        """
        Generate a secure password reset token

        Args:
            user_id: User ID requesting reset
            email: User email address

        Returns:
            Secure random token (32 bytes = 64 hex chars)

        Example:
            >>> manager = PasswordResetTokenManager()
            >>> token = manager.generate_token(user_id=1, email="user@example.com")
            >>> print(len(token))
            64
        """
        with self._lock:
            # Generate cryptographically secure random token
            token = secrets.token_urlsafe(32)

            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(minutes=self._token_lifetime_minutes)

            # Store token data
            self._tokens[token] = {
                "user_id": user_id,
                "email": email,
                "expires_at": expires_at,
                "created_at": datetime.utcnow()
            }

            return token

    def validate_token(self, token: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validate a password reset token

        Args:
            token: Token to validate

        Returns:
            Tuple of (is_valid, user_id, error_message)
            - is_valid: True if token is valid and not expired
            - user_id: User ID if valid, None otherwise
            - error_message: Error description if invalid

        Example:
            >>> manager = PasswordResetTokenManager()
            >>> token = manager.generate_token(1, "user@example.com")
            >>> is_valid, user_id, error = manager.validate_token(token)
            >>> print(is_valid, user_id)
            True 1
        """
        with self._lock:
            # Check if token exists
            if token not in self._tokens:
                return False, None, "Invalid or expired reset token"

            token_data = self._tokens[token]

            # Check if token has expired
            if datetime.utcnow() > token_data["expires_at"]:
                # Remove expired token
                del self._tokens[token]
                return False, None, "Reset token has expired"

            return True, token_data["user_id"], None

    def consume_token(self, token: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validate and consume a token (one-time use)

        After successful validation, the token is removed and cannot be used again.

        Args:
            token: Token to validate and consume

        Returns:
            Tuple of (is_valid, user_id, error_message)
        """
        with self._lock:
            # Validate first
            is_valid, user_id, error = self.validate_token(token)

            if is_valid:
                # Remove token after successful validation (one-time use)
                del self._tokens[token]

            return is_valid, user_id, error

    def invalidate_user_tokens(self, user_id: int) -> int:
        """
        Invalidate all tokens for a specific user

        Useful when user changes password or logs out from all devices.

        Args:
            user_id: User ID whose tokens should be invalidated

        Returns:
            Number of tokens invalidated
        """
        with self._lock:
            tokens_to_remove = [
                token for token, data in self._tokens.items()
                if data["user_id"] == user_id
            ]

            for token in tokens_to_remove:
                del self._tokens[token]

            return len(tokens_to_remove)

    def cleanup_expired_tokens(self):
        """
        Remove all expired tokens

        Call this periodically (e.g., via background task) to prevent memory bloat.
        """
        with self._lock:
            now = datetime.utcnow()

            expired_tokens = [
                token for token, data in self._tokens.items()
                if now > data["expires_at"]
            ]

            for token in expired_tokens:
                del self._tokens[token]

            return len(expired_tokens)

    def get_token_info(self, token: str) -> Optional[dict]:
        """
        Get information about a token (for debugging/admin purposes)

        Args:
            token: Token to query

        Returns:
            Token data dictionary or None if not found
        """
        with self._lock:
            return self._tokens.get(token)

    def count_active_tokens(self) -> int:
        """Get count of active (non-expired) tokens"""
        with self._lock:
            now = datetime.utcnow()
            return sum(
                1 for data in self._tokens.values()
                if now <= data["expires_at"]
            )


# Global instance
_password_reset_manager = PasswordResetTokenManager(token_lifetime_minutes=60)


def get_password_reset_manager() -> PasswordResetTokenManager:
    """
    Get the global password reset token manager instance

    Returns:
        PasswordResetTokenManager instance
    """
    return _password_reset_manager


def cleanup_expired_reset_tokens():
    """
    Cleanup expired password reset tokens

    Call this periodically (e.g., via background task or cron job)
    """
    return _password_reset_manager.cleanup_expired_tokens()
