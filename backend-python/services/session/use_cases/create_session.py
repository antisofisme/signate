"""
Create Session Use Case
Create new user session (called during login)
"""

from typing import Optional, Dict
from ..repositories.session_repo import SessionRepository
from ..repositories.models import UserSession


class CreateSessionUseCase:
    """Create new user session"""

    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository

    def execute(
        self,
        user_id: int,
        organization_id: int,
        access_token: str,
        refresh_token: Optional[str],
        ip_address: str,
        user_agent: Optional[str],
        device_info: Optional[Dict],
        session_type: str = "web",
        expires_in_minutes: int = 30
    ) -> UserSession:
        """
        Create new session

        Args:
            user_id: User ID
            organization_id: Organization ID
            access_token: JWT access token (will be hashed)
            refresh_token: JWT refresh token (will be hashed)
            ip_address: Client IP address
            user_agent: User-Agent header
            device_info: Device information dict
            session_type: Session type (web, api, mobile, device)
            expires_in_minutes: Token expiration

        Returns:
            Created UserSession model
        """
        return self.session_repository.create_session(
            user_id=user_id,
            organization_id=organization_id,
            access_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            session_type=session_type,
            expires_in_minutes=expires_in_minutes
        )
