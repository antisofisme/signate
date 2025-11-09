"""
Verify Session Use Case
Verify session is valid and active
"""

from typing import Optional
from ..repositories.session_repo import SessionRepository
from ..repositories.models import UserSession
from shared.errors import AuthenticationError


class VerifySessionUseCase:
    """Verify session validity"""

    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository

    def execute(self, token: str) -> UserSession:
        """
        Verify session by token

        Args:
            token: JWT access token

        Returns:
            UserSession model if valid

        Raises:
            AuthenticationError: If session invalid, expired, or revoked
        """
        session = self.session_repository.verify_session(token)

        if not session:
            raise AuthenticationError(
                message="Session tidak valid atau sudah expired"
            )

        # Update last activity
        self.session_repository.update_last_activity(session.id)

        return session
