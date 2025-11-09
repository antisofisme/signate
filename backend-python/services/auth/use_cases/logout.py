"""
Logout Use Case
Handles user logout and session revocation

Phase 1 Day 3 - Session Management Integration
"""

from typing import Dict, Any
import hashlib


class LogoutUseCase:
    """Logout use case - revokes user session"""

    def __init__(self, session_repository):
        """
        Initialize logout use case

        Args:
            session_repository: SessionRepository instance for session management
        """
        self.session_repository = session_repository

    def execute(self, token: str) -> Dict[str, Any]:
        """
        Execute logout use case

        Revokes the session associated with the provided JWT token.
        This invalidates the token and prevents further use until re-login.

        Args:
            token: JWT access token to revoke

        Returns:
            Dict with success status and message:
            {
                "revoked": bool,
                "message": str
            }
        """
        # Revoke session by token (repository will hash it automatically)
        revoked = self.session_repository.revoke_session_by_token(token)

        return {
            "revoked": revoked,
            "message": "Logged out successfully" if revoked else "Session not found or already revoked"
        }
