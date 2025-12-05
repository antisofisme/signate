"""
Session Repository
Data access layer for UserSession model
"""

from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone
import hashlib
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from .models import UserSession
from services.auth.repositories.models import UserModel, OrganizationModel
from services.rbac.repositories.models import Role


class SessionRepository:
    """Repository for UserSession model with CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash JWT token using SHA256 for storage

        Args:
            token: JWT token string

        Returns:
            SHA256 hash (64 chars hex)
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def create_session(
        self,
        user_id: int,
        organization_id: int,
        access_token: str,
        refresh_token: Optional[str],
        ip_address: str,
        user_agent: Optional[str],
        device_info: Optional[dict],
        session_type: str = "web",
        expires_in_minutes: int = 30
    ) -> UserSession:
        """
        Create new user session

        Args:
            user_id: User ID
            organization_id: Organization ID
            access_token: JWT access token (will be hashed)
            refresh_token: JWT refresh token (will be hashed) or None
            ip_address: Client IP address
            user_agent: Client User-Agent header
            device_info: Device information (browser, OS, etc.)
            session_type: Session type (web, api, mobile, device)
            expires_in_minutes: Token expiration in minutes

        Returns:
            Created UserSession model
        """
        session = UserSession(
            user_id=user_id,
            organization_id=organization_id,
            session_token=self.hash_token(access_token),
            refresh_token=self.hash_token(refresh_token) if refresh_token else None,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info or {},
            session_type=session_type,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def find_by_token(self, token: str) -> Optional[UserSession]:
        """
        Find session by access token hash

        Args:
            token: JWT access token (will be hashed for lookup)

        Returns:
            UserSession model or None if not found
        """
        token_hash = self.hash_token(token)
        return self.db.query(UserSession).filter(
            UserSession.session_token == token_hash
        ).first()

    def find_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """
        Find session by refresh token hash

        Args:
            refresh_token: JWT refresh token (will be hashed for lookup)

        Returns:
            UserSession model or None if not found
        """
        token_hash = self.hash_token(refresh_token)
        return self.db.query(UserSession).filter(
            UserSession.refresh_token == token_hash
        ).first()

    def verify_session(self, token: str) -> Optional[UserSession]:
        """
        Verify session by token and check if active

        Args:
            token: JWT access token

        Returns:
            UserSession model if valid and active, None otherwise
        """
        session = self.find_by_token(token)

        if not session:
            return None

        # Check if session is active (not revoked and not expired)
        if not session.is_active:
            return None

        return session

    def update_last_activity(self, session_id: int) -> bool:
        """
        Update session last activity timestamp

        Args:
            session_id: Session ID

        Returns:
            True if updated, False if not found
        """
        session = self.db.query(UserSession).filter(UserSession.id == session_id).first()
        if not session:
            return False

        session.last_activity_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def revoke_session(self, session_id: int) -> bool:
        """
        Revoke session (logout)

        Args:
            session_id: Session ID

        Returns:
            True if revoked, False if not found
        """
        session = self.db.query(UserSession).filter(UserSession.id == session_id).first()
        if not session:
            return False

        session.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def revoke_session_by_token(self, token: str) -> bool:
        """
        Revoke session by access token

        Args:
            token: JWT access token

        Returns:
            True if revoked, False if not found
        """
        session = self.find_by_token(token)
        if not session:
            return False

        session.revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def revoke_all_user_sessions(self, user_id: int) -> int:
        """
        Revoke all sessions for a user (logout from all devices)

        Args:
            user_id: User ID

        Returns:
            Number of sessions revoked
        """
        sessions = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None)
            )
        ).all()

        count = 0
        now = datetime.now(timezone.utc)
        for session in sessions:
            session.revoked_at = now
            count += 1

        self.db.commit()
        return count

    def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """
        Get all active sessions for user

        Args:
            user_id: User ID

        Returns:
            List of active UserSession models
        """
        now = datetime.now(timezone.utc)
        return self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now
            )
        ).order_by(UserSession.last_activity_at.desc()).all()

    def get_user_sessions(
        self,
        user_id: int,
        include_revoked: bool = False,
        include_expired: bool = False
    ) -> List[UserSession]:
        """
        Get all sessions for user with filters

        Args:
            user_id: User ID
            include_revoked: Include revoked sessions
            include_expired: Include expired sessions

        Returns:
            List of UserSession models
        """
        query = self.db.query(UserSession).filter(UserSession.user_id == user_id)

        if not include_revoked:
            query = query.filter(UserSession.revoked_at.is_(None))

        if not include_expired:
            query = query.filter(UserSession.expires_at > datetime.now(timezone.utc))

        return query.order_by(UserSession.last_activity_at.desc()).all()

    def cleanup_expired_sessions(self, days_old: int = 30) -> int:
        """
        Delete expired sessions older than specified days

        Args:
            days_old: Delete sessions expired more than this many days ago

        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        sessions = self.db.query(UserSession).filter(
            UserSession.expires_at < cutoff_date
        ).all()

        count = len(sessions)
        for session in sessions:
            self.db.delete(session)

        self.db.commit()
        return count

    def cleanup_old_sessions(self, days_old: int = 7) -> dict:
        """
        Clean up old sessions (both expired and revoked)

        Deletes sessions that are:
        - Expired AND older than days_old days
        - Revoked AND older than days_old days

        Args:
            days_old: Delete sessions older than this many days (default: 7)

        Returns:
            Dictionary with cleanup statistics:
            - expired_deleted: Number of expired sessions deleted
            - revoked_deleted: Number of revoked sessions deleted
            - total_deleted: Total sessions deleted
        """
        from sqlalchemy import or_

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        # Find sessions to delete:
        # 1. Expired sessions older than cutoff
        # 2. Revoked sessions older than cutoff
        sessions_to_delete = self.db.query(UserSession).filter(
            or_(
                # Expired sessions: expires_at < cutoff_date
                UserSession.expires_at < cutoff_date,
                # Revoked sessions: revoked_at < cutoff_date
                and_(
                    UserSession.revoked_at.isnot(None),
                    UserSession.revoked_at < cutoff_date
                )
            )
        ).all()

        expired_count = 0
        revoked_count = 0

        for session in sessions_to_delete:
            if session.revoked_at is not None:
                revoked_count += 1
            else:
                expired_count += 1
            self.db.delete(session)

        self.db.commit()

        return {
            "expired_deleted": expired_count,
            "revoked_deleted": revoked_count,
            "total_deleted": expired_count + revoked_count,
            "cutoff_date": cutoff_date.isoformat()
        }

    def get_session_stats(self, user_id: Optional[int] = None) -> dict:
        """
        Get session statistics

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Dictionary with session statistics
        """
        query = self.db.query(UserSession)
        if user_id:
            query = query.filter(UserSession.user_id == user_id)

        total = query.count()

        now = datetime.now(timezone.utc)
        active = query.filter(
            and_(
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now
            )
        ).count()

        expired = query.filter(UserSession.expires_at <= now).count()
        revoked = query.filter(UserSession.revoked_at.isnot(None)).count()

        return {
            "total": total,
            "active": active,
            "expired": expired,
            "revoked": revoked
        }

    def get_sessions_by_ip(self, ip_address: str, limit: int = 10) -> List[UserSession]:
        """
        Get recent sessions from specific IP address

        Args:
            ip_address: IP address to search
            limit: Maximum number of results

        Returns:
            List of UserSession models
        """
        return self.db.query(UserSession).filter(
            UserSession.ip_address == ip_address
        ).order_by(UserSession.created_at.desc()).limit(limit).all()

    def get_sessions_by_type(
        self,
        session_type: str,
        user_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[UserSession]:
        """
        Get sessions by type

        Args:
            session_type: Session type (web, api, mobile, device)
            user_id: Optional user ID filter
            active_only: Only return active sessions

        Returns:
            List of UserSession models
        """
        query = self.db.query(UserSession).filter(UserSession.session_type == session_type)

        if user_id:
            query = query.filter(UserSession.user_id == user_id)

        if active_only:
            now = datetime.now(timezone.utc)
            query = query.filter(
                and_(
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > now
                )
            )

        return query.order_by(UserSession.last_activity_at.desc()).all()

    def update_token(self, old_token: str, new_token: str) -> bool:
        """
        Update session token with new token (for token refresh)

        Args:
            old_token: Current JWT access token
            new_token: New JWT access token

        Returns:
            True if updated, False if session not found
        """
        session = self.find_by_token(old_token)
        if not session:
            return False

        # Update token hash and last activity
        session.session_token = self.hash_token(new_token)
        session.last_activity_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def get_all_active_sessions(
        self,
        organization_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
        include_revoked: bool = True,
        include_expired: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all sessions with user and organization info

        Args:
            organization_id: Filter by organization (None = all orgs for super admin)
            skip: Pagination offset
            limit: Pagination limit
            include_revoked: Include revoked sessions (default True for admin view)
            include_expired: Include expired sessions

        Returns:
            Tuple of (list of session dicts with user/org info, total count)
        """
        now = datetime.now(timezone.utc)

        # Base query for sessions
        query = self.db.query(
            UserSession,
            UserModel.username,
            UserModel.email,
            UserModel.full_name,
            Role.name.label('role_name'),
            OrganizationModel.name.label('organization_name')
        ).join(
            UserModel, UserSession.user_id == UserModel.id
        ).join(
            Role, UserModel.role_id == Role.id
        ).outerjoin(
            OrganizationModel, UserSession.organization_id == OrganizationModel.id
        )

        # Apply filters based on parameters
        if not include_revoked:
            query = query.filter(UserSession.revoked_at.is_(None))

        if not include_expired:
            query = query.filter(UserSession.expires_at > now)

        # Filter by organization if specified
        if organization_id is not None:
            query = query.filter(UserSession.organization_id == organization_id)

        # Get total count
        total = query.count()

        # Get paginated results
        results = query.order_by(
            UserSession.last_activity_at.desc()
        ).offset(skip).limit(limit).all()

        # Convert to dict with user/org info
        sessions = []
        for session, username, email, full_name, role_name, org_name in results:
            # Determine status
            is_active = session.revoked_at is None and session.expires_at > now
            status = "active" if is_active else ("revoked" if session.revoked_at else "expired")

            session_dict = {
                "id": session.id,
                "user_id": session.user_id,
                "organization_id": session.organization_id,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "device_info": session.device_info,
                "session_type": session.session_type,
                "created_at": session.created_at,
                "last_activity_at": session.last_activity_at,
                "expires_at": session.expires_at,
                "revoked_at": session.revoked_at,
                "status": status,
                # User info
                "username": username,
                "email": email,
                "full_name": full_name,
                "role": role_name,
                # Organization info
                "organization_name": org_name
            }
            sessions.append(session_dict)

        return sessions, total
