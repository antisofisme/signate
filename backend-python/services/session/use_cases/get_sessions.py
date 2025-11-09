"""
Get Sessions Use Case
Retrieve user sessions with filtering
"""

from typing import List, Dict, Any, Optional
from ..repositories.session_repo import SessionRepository
from ..repositories.models import UserSession


class GetSessionsUseCase:
    """Get user sessions"""

    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository

    def get_user_sessions(
        self,
        user_id: int,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> Dict[str, Any]:
        """
        Get all sessions for user

        Args:
            user_id: User ID
            include_revoked: Include revoked sessions
            include_expired: Include expired sessions

        Returns:
            Dict with sessions and statistics
        """
        sessions = self.session_repository.get_user_sessions(
            user_id=user_id,
            include_revoked=include_revoked,
            include_expired=include_expired
        )

        # Get stats
        stats = self.session_repository.get_session_stats(user_id=user_id)

        return {
            "sessions": sessions,
            "total": stats["total"],
            "active": stats["active"],
            "expired": stats["expired"],
            "revoked": stats["revoked"]
        }

    def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """
        Get only active sessions for user

        Args:
            user_id: User ID

        Returns:
            List of active sessions
        """
        return self.session_repository.get_active_sessions(user_id)

    def get_session_stats(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """
        Get session statistics

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Dict with statistics
        """
        return self.session_repository.get_session_stats(user_id)

    def get_sessions_by_ip(self, ip_address: str, limit: int = 10) -> List[UserSession]:
        """
        Get sessions by IP address

        Args:
            ip_address: IP address
            limit: Maximum results

        Returns:
            List of sessions
        """
        return self.session_repository.get_sessions_by_ip(ip_address, limit)

    def get_sessions_by_type(
        self,
        session_type: str,
        user_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[UserSession]:
        """
        Get sessions by type

        Args:
            session_type: Session type
            user_id: Optional user ID filter
            active_only: Only active sessions

        Returns:
            List of sessions
        """
        return self.session_repository.get_sessions_by_type(
            session_type=session_type,
            user_id=user_id,
            active_only=active_only
        )
