"""
Local Auth Adapter

Implementation of IAuthProvider for email/password authentication.
Uses bcrypt for password hashing.

Source: INFRA-DEC-008-auth-flow.md
"""

import bcrypt
from typing import Optional

from ..interfaces.auth_provider import IAuthProvider


class LocalAuthAdapter(IAuthProvider):
    """Local authentication using email/password with bcrypt."""

    def __init__(self, bcrypt_rounds: int = 12):
        """Initialize local auth adapter.

        Args:
            bcrypt_rounds: Number of bcrypt rounds (default 12)
        """
        self._bcrypt_rounds = bcrypt_rounds

    async def hash_password(self, password: str) -> str:
        """Hash password using bcrypt.

        Args:
            password: Plaintext password

        Returns:
            Bcrypt hash string
        """
        salt = bcrypt.gensalt(rounds=self._bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash.

        Args:
            password: Plaintext password
            hashed: Stored bcrypt hash

        Returns:
            True if password matches
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            # Invalid hash format or other error
            return False
