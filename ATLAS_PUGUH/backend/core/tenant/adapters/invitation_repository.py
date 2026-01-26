"""
PostgreSQL Invitation Repository

Implementation of IInvitationRepository for PostgreSQL database.

Source: INFRA-DEC-007-identity-model.md
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.invitation_repository import IInvitationRepository
from ..domain.invitation import Invitation, InvitationStatus
from ..domain.membership import MemberRole
from ..exceptions import InvitationAlreadyPendingError


class PostgresInvitationRepository(IInvitationRepository):
    """PostgreSQL implementation of invitation repository."""

    def __init__(self, session_factory):
        """Initialize repository with session factory.

        Args:
            session_factory: Async session factory for database access
        """
        self._session_factory = session_factory

    async def create(self, invitation: Invitation) -> Invitation:
        """Create a new invitation."""
        # Check if pending invitation exists
        if await self.has_pending_invitation(invitation.email, invitation.tenant_id):
            raise InvitationAlreadyPendingError(invitation.email, str(invitation.tenant_id))

        async with self._session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO invitations (
                        invitation_id, token, email, tenant_id,
                        role, invited_by_user_id, status,
                        target_user_id, expires_at, message,
                        accepted_at, rejected_at, created_at, updated_at
                    ) VALUES (
                        :invitation_id, :token, :email, :tenant_id,
                        :role, :invited_by_user_id, :status,
                        :target_user_id, :expires_at, :message,
                        :accepted_at, :rejected_at, :created_at, :updated_at
                    )
                """),
                {
                    "invitation_id": str(invitation.invitation_id),
                    "token": invitation.token,
                    "email": invitation.email,
                    "tenant_id": str(invitation.tenant_id),
                    "role": invitation.role.value,
                    "invited_by_user_id": str(invitation.invited_by_user_id),
                    "status": invitation.status.value,
                    "target_user_id": str(invitation.target_user_id) if invitation.target_user_id else None,
                    "expires_at": invitation.expires_at,
                    "message": invitation.message,
                    "accepted_at": invitation.accepted_at,
                    "rejected_at": invitation.rejected_at,
                    "created_at": invitation.created_at,
                    "updated_at": invitation.updated_at,
                }
            )
            await session.commit()

        return invitation

    async def get_by_id(self, invitation_id: UUID) -> Optional[Invitation]:
        """Get invitation by ID."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT invitation_id, token, email, tenant_id,
                           role, invited_by_user_id, status,
                           target_user_id, expires_at, message,
                           accepted_at, rejected_at, created_at, updated_at
                    FROM invitations
                    WHERE invitation_id = :invitation_id
                """),
                {"invitation_id": str(invitation_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return self._row_to_invitation(row)

    async def get_by_token(self, token: str) -> Optional[Invitation]:
        """Get invitation by token."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT invitation_id, token, email, tenant_id,
                           role, invited_by_user_id, status,
                           target_user_id, expires_at, message,
                           accepted_at, rejected_at, created_at, updated_at
                    FROM invitations
                    WHERE token = :token
                """),
                {"token": token}
            )
            row = result.fetchone()

            if not row:
                return None

            return self._row_to_invitation(row)

    async def get_pending_by_email_and_tenant(
        self,
        email: str,
        tenant_id: UUID
    ) -> Optional[Invitation]:
        """Get pending invitation for email in tenant."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT invitation_id, token, email, tenant_id,
                           role, invited_by_user_id, status,
                           target_user_id, expires_at, message,
                           accepted_at, rejected_at, created_at, updated_at
                    FROM invitations
                    WHERE LOWER(email) = LOWER(:email)
                      AND tenant_id = :tenant_id
                      AND status = 'pending'
                      AND expires_at > NOW()
                """),
                {"email": email, "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return self._row_to_invitation(row)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Invitation]:
        """List invitations for a tenant."""
        status_filter = f"AND status = '{status}'" if status else ""

        async with self._session_factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT invitation_id, token, email, tenant_id,
                           role, invited_by_user_id, status,
                           target_user_id, expires_at, message,
                           accepted_at, rejected_at, created_at, updated_at
                    FROM invitations
                    WHERE tenant_id = :tenant_id
                      {status_filter}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {"tenant_id": str(tenant_id), "limit": limit, "offset": offset}
            )
            rows = result.fetchall()

            return [self._row_to_invitation(row) for row in rows]

    async def list_by_email(
        self,
        email: str,
        status: Optional[str] = None
    ) -> List[Invitation]:
        """List invitations for an email address."""
        status_filter = f"AND status = '{status}'" if status else ""

        async with self._session_factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT invitation_id, token, email, tenant_id,
                           role, invited_by_user_id, status,
                           target_user_id, expires_at, message,
                           accepted_at, rejected_at, created_at, updated_at
                    FROM invitations
                    WHERE LOWER(email) = LOWER(:email)
                      {status_filter}
                    ORDER BY created_at DESC
                """),
                {"email": email}
            )
            rows = result.fetchall()

            return [self._row_to_invitation(row) for row in rows]

    async def list_pending_for_user(self, user_id: UUID) -> List[Invitation]:
        """List pending invitations for a user (by their email)."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT i.invitation_id, i.token, i.email, i.tenant_id,
                           i.role, i.invited_by_user_id, i.status,
                           i.target_user_id, i.expires_at, i.message,
                           i.accepted_at, i.rejected_at, i.created_at, i.updated_at
                    FROM invitations i
                    INNER JOIN users u ON LOWER(i.email) = LOWER(u.email)
                    WHERE u.user_id = :user_id
                      AND i.status = 'pending'
                      AND i.expires_at > NOW()
                    ORDER BY i.created_at DESC
                """),
                {"user_id": str(user_id)}
            )
            rows = result.fetchall()

            return [self._row_to_invitation(row) for row in rows]

    async def count_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[str] = None
    ) -> int:
        """Count invitations for a tenant."""
        status_filter = f"AND status = '{status}'" if status else ""

        async with self._session_factory() as session:
            result = await session.execute(
                text(f"""
                    SELECT COUNT(*)
                    FROM invitations
                    WHERE tenant_id = :tenant_id
                      {status_filter}
                """),
                {"tenant_id": str(tenant_id)}
            )
            return result.scalar() or 0

    async def update(self, invitation: Invitation) -> Invitation:
        """Update invitation."""
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    UPDATE invitations SET
                        status = :status,
                        target_user_id = :target_user_id,
                        expires_at = :expires_at,
                        accepted_at = :accepted_at,
                        rejected_at = :rejected_at,
                        updated_at = :updated_at
                    WHERE invitation_id = :invitation_id
                """),
                {
                    "invitation_id": str(invitation.invitation_id),
                    "status": invitation.status.value,
                    "target_user_id": str(invitation.target_user_id) if invitation.target_user_id else None,
                    "expires_at": invitation.expires_at,
                    "accepted_at": invitation.accepted_at,
                    "rejected_at": invitation.rejected_at,
                    "updated_at": datetime.utcnow(),
                }
            )
            await session.commit()

        return invitation

    async def update_status(
        self,
        invitation_id: UUID,
        status: str
    ) -> None:
        """Update invitation status."""
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    UPDATE invitations SET
                        status = :status,
                        updated_at = NOW()
                    WHERE invitation_id = :invitation_id
                """),
                {"invitation_id": str(invitation_id), "status": status}
            )
            await session.commit()

    async def link_to_user(
        self,
        invitation_id: UUID,
        user_id: UUID
    ) -> None:
        """Link invitation to a registered user."""
        async with self._session_factory() as session:
            await session.execute(
                text("""
                    UPDATE invitations SET
                        target_user_id = :user_id,
                        updated_at = NOW()
                    WHERE invitation_id = :invitation_id
                """),
                {"invitation_id": str(invitation_id), "user_id": str(user_id)}
            )
            await session.commit()

    async def delete(self, invitation_id: UUID) -> None:
        """Delete invitation (hard delete)."""
        async with self._session_factory() as session:
            await session.execute(
                text("DELETE FROM invitations WHERE invitation_id = :invitation_id"),
                {"invitation_id": str(invitation_id)}
            )
            await session.commit()

    async def expire_old_invitations(self) -> int:
        """Expire all old pending invitations."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    UPDATE invitations SET
                        status = 'expired',
                        updated_at = NOW()
                    WHERE status = 'pending'
                      AND expires_at <= NOW()
                """)
            )
            await session.commit()
            return result.rowcount or 0

    async def has_pending_invitation(
        self,
        email: str,
        tenant_id: UUID
    ) -> bool:
        """Check if pending invitation exists."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT 1 FROM invitations
                    WHERE LOWER(email) = LOWER(:email)
                      AND tenant_id = :tenant_id
                      AND status = 'pending'
                      AND expires_at > NOW()
                """),
                {"email": email, "tenant_id": str(tenant_id)}
            )
            return result.scalar() is not None

    def _row_to_invitation(self, row) -> Invitation:
        """Convert database row to Invitation entity."""
        return Invitation(
            invitation_id=UUID(str(row.invitation_id)),
            token=row.token,
            email=row.email,
            tenant_id=UUID(str(row.tenant_id)),
            role=MemberRole(row.role),
            invited_by_user_id=UUID(str(row.invited_by_user_id)),
            status=InvitationStatus(row.status),
            target_user_id=UUID(str(row.target_user_id)) if row.target_user_id else None,
            expires_at=row.expires_at,
            message=row.message,
            accepted_at=row.accepted_at,
            rejected_at=row.rejected_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
