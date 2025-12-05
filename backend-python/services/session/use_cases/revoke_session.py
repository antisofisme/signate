"""
Revoke Session Use Case
Revoke user sessions (logout)
"""

from typing import Dict, Any
import logging
from ..repositories.session_repo import SessionRepository
from shared.errors import NotFoundError
from shared.cache import cache

logger = logging.getLogger(__name__)


class RevokeSessionUseCase:
    """Revoke user sessions"""

    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository

    def revoke_by_id(self, session_id: int) -> Dict[str, Any]:
        """
        Revoke specific session by ID

        Args:
            session_id: Session ID

        Returns:
            Dict with success status

        Raises:
            NotFoundError: If session not found

        Note:
            Cache invalidation is not possible here since we don't have the original token.
            The revoked session may still be valid in cache for up to 30 seconds.
            For immediate invalidation, use revoke_by_token or logout endpoint.
        """
        success = self.session_repository.revoke_session(session_id)

        if not success:
            raise NotFoundError(
                message=f"Session with ID {session_id} not found"
            )

        logger.info(f"Session {session_id} revoked (cache not invalidated - no token)")
        return {
            "success": True,
            "sessions_revoked": 1,
            "message": "Session revoked successfully"
        }

    def revoke_by_token(self, token: str) -> Dict[str, Any]:
        """
        Revoke session by access token

        Args:
            token: JWT access token

        Returns:
            Dict with success status

        Raises:
            NotFoundError: If session not found
        """
        success = self.session_repository.revoke_session_by_token(token)

        if not success:
            raise NotFoundError(
                message="Session not found"
            )

        # Invalidate cache immediately
        cache.invalidate_session(token)
        logger.info("Session revoked and cache invalidated")

        return {
            "success": True,
            "sessions_revoked": 1,
            "message": "Logged out successfully"
        }

    def revoke_all_user_sessions(self, user_id: int) -> Dict[str, Any]:
        """
        Revoke all sessions for user (logout from all devices)

        Args:
            user_id: User ID

        Returns:
            Dict with number of sessions revoked
        """
        count = self.session_repository.revoke_all_user_sessions(user_id)

        # Invalidate all session caches for this user
        # Note: This uses pattern matching and may be heavy for large deployments
        if count > 0:
            cache.invalidate_user_sessions(user_id)
            logger.info(f"Revoked {count} sessions for user {user_id}, cache invalidated")

        return {
            "success": True,
            "sessions_revoked": count,
            "message": f"Logged out from {count} device(s)"
        }
