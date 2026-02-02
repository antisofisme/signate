"""
PostgreSQL User Repository

Implementation of IUserRepository for PostgreSQL database.
Handles all user CRUD operations.

Source: INFRA-DEC-007-identity-model.md
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.user_repository import IUserRepository
from ..domain.user import User, UserStatus, AuthProvider
from ..exceptions import EmailExistsError, OAuthAlreadyLinkedError, CannotUnlinkError


class PostgresUserRepository(IUserRepository):
    """PostgreSQL implementation of user repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session
        """
        self._session = session

    async def create(self, user: User) -> User:
        """Create a new user."""
        # Check if email exists
        if await self.email_exists(user.email):
            raise EmailExistsError(user.email)

        await self._session.execute(
            text("""
                INSERT INTO users (
                    user_id, email, password_hash, auth_provider,
                    oauth_provider_id, display_name, avatar_url,
                    status, email_verified_at, created_at, updated_at
                ) VALUES (
                    :user_id, :email, :password_hash, :auth_provider,
                    :oauth_provider_id, :display_name, :avatar_url,
                    :status, :email_verified_at, :created_at, :updated_at
                )
            """),
            {
                "user_id": str(user.user_id),
                "email": user.email,
                "password_hash": user.password_hash,
                "auth_provider": user.auth_provider.value,
                "oauth_provider_id": user.oauth_provider_id,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "status": user.status.value,
                "email_verified_at": user.email_verified_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        )
        await self._session.commit()

        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self._session.execute(
            text("""
                SELECT user_id, email, password_hash, auth_provider,
                       oauth_provider_id, display_name, avatar_url,
                       status, email_verified_at, created_at, updated_at,
                       last_login_at
                FROM users
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id)}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_user(row)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        result = await self._session.execute(
            text("""
                SELECT user_id, email, password_hash, auth_provider,
                       oauth_provider_id, display_name, avatar_url,
                       status, email_verified_at, created_at, updated_at,
                       last_login_at
                FROM users
                WHERE LOWER(email) = LOWER(:email)
            """),
            {"email": email}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_user(row)

    async def get_by_oauth(self, provider: str, provider_id: str) -> Optional[User]:
        """Get user by OAuth provider ID."""
        result = await self._session.execute(
            text("""
                SELECT user_id, email, password_hash, auth_provider,
                       oauth_provider_id, display_name, avatar_url,
                       status, email_verified_at, created_at, updated_at,
                       last_login_at
                FROM users
                WHERE auth_provider = :provider
                  AND oauth_provider_id = :provider_id
            """),
            {"provider": provider, "provider_id": provider_id}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_user(row)

    async def update(self, user: User) -> User:
        """Update user."""
        await self._session.execute(
            text("""
                UPDATE users SET
                    display_name = :display_name,
                    avatar_url = :avatar_url,
                    status = :status,
                    email_verified_at = :email_verified_at,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """),
            {
                "user_id": str(user.user_id),
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "status": user.status.value,
                "email_verified_at": user.email_verified_at,
                "updated_at": datetime.utcnow(),
            }
        )
        await self._session.commit()

        return user

    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        """Update user's password hash."""
        await self._session.execute(
            text("""
                UPDATE users SET
                    password_hash = :password_hash,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id), "password_hash": password_hash}
        )
        await self._session.commit()

    async def update_status(self, user_id: UUID, status: str) -> None:
        """Update user's status."""
        await self._session.execute(
            text("""
                UPDATE users SET
                    status = :status,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id), "status": status}
        )
        await self._session.commit()

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        await self._session.execute(
            text("""
                UPDATE users SET
                    last_login_at = NOW(),
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id)}
        )
        await self._session.commit()

    async def verify_email(self, user_id: UUID) -> None:
        """Mark user's email as verified."""
        await self._session.execute(
            text("""
                UPDATE users SET
                    email_verified_at = NOW(),
                    status = 'active',
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id)}
        )
        await self._session.commit()

    async def link_oauth(
        self,
        user_id: UUID,
        provider: str,
        provider_id: str
    ) -> None:
        """Link OAuth provider to existing user."""
        # Check if already linked to another user
        result = await self._session.execute(
            text("""
                SELECT user_id FROM users
                WHERE auth_provider = :provider
                  AND oauth_provider_id = :provider_id
                  AND user_id != :user_id
            """),
            {
                "provider": provider,
                "provider_id": provider_id,
                "user_id": str(user_id),
            }
        )
        if result.fetchone():
            raise OAuthAlreadyLinkedError(provider)

        await self._session.execute(
            text("""
                UPDATE users SET
                    oauth_provider_id = :provider_id,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {
                "user_id": str(user_id),
                "provider_id": provider_id,
            }
        )
        await self._session.commit()

    async def unlink_oauth(self, user_id: UUID, provider: str) -> None:
        """Unlink OAuth provider from user."""
        # Get user to check if can unlink
        user = await self.get_by_id(user_id)
        if not user:
            return

        if not user.can_unlink_oauth(provider):
            raise CannotUnlinkError(provider)

        await self._session.execute(
            text("""
                UPDATE users SET
                    oauth_provider_id = NULL,
                    auth_provider = 'local',
                    updated_at = NOW()
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id)}
        )
        await self._session.commit()

    async def email_exists(self, email: str) -> bool:
        """Check if email exists."""
        result = await self._session.execute(
            text("SELECT 1 FROM users WHERE LOWER(email) = LOWER(:email)"),
            {"email": email}
        )
        return result.scalar() is not None

    def _row_to_user(self, row) -> User:
        """Convert database row to User entity."""
        return User(
            user_id=UUID(str(row.user_id)),
            email=row.email,
            auth_provider=AuthProvider(row.auth_provider),
            password_hash=row.password_hash,
            oauth_provider_id=row.oauth_provider_id,
            display_name=row.display_name,
            avatar_url=row.avatar_url,
            status=UserStatus(row.status),
            email_verified_at=row.email_verified_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_login_at=row.last_login_at,
        )

    # =========================================================================
    # Account Lockout Methods (brute force protection)
    # =========================================================================

    async def is_account_locked(self, user_id: UUID) -> bool:
        """Check if account is locked using database function."""
        result = await self._session.execute(
            text("SELECT is_account_locked(:user_id)"),
            {"user_id": str(user_id)}
        )
        return result.scalar() or False

    async def get_lockout_info(self, user_id: UUID) -> Optional[dict]:
        """Get account lockout information."""
        result = await self._session.execute(
            text("""
                SELECT
                    failed_login_attempts,
                    locked_until,
                    last_failed_login_at,
                    last_failed_login_ip
                FROM users
                WHERE user_id = :user_id
            """),
            {"user_id": str(user_id)}
        )
        row = result.fetchone()

        if not row:
            return None

        if not row.locked_until:
            return None

        return {
            "failed_attempts": row.failed_login_attempts or 0,
            "locked_until": row.locked_until.isoformat() if row.locked_until else None,
            "last_failed_at": row.last_failed_login_at.isoformat() if row.last_failed_login_at else None,
            "last_failed_ip": row.last_failed_login_ip,
        }

    async def record_failed_login(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None
    ) -> dict:
        """Record a failed login attempt using database function."""
        result = await self._session.execute(
            text("SELECT * FROM record_failed_login(:user_id, :ip_address)"),
            {
                "user_id": str(user_id),
                "ip_address": ip_address,
            }
        )
        row = result.fetchone()
        await self._session.commit()

        if row:
            return {
                "is_locked": row.is_locked,
                "lock_duration_minutes": row.lock_duration_minutes,
                "attempts": row.attempts,
            }
        return {"is_locked": False, "lock_duration_minutes": 0, "attempts": 0}

    async def reset_failed_logins(self, user_id: UUID) -> None:
        """Reset failed login counter using database function."""
        await self._session.execute(
            text("SELECT reset_failed_logins(:user_id)"),
            {"user_id": str(user_id)}
        )
        await self._session.commit()

    async def admin_unlock_account(self, user_id: UUID) -> bool:
        """Manually unlock an account using database function."""
        result = await self._session.execute(
            text("SELECT admin_unlock_account(:user_id)"),
            {"user_id": str(user_id)}
        )
        await self._session.commit()
        return result.scalar() or False
