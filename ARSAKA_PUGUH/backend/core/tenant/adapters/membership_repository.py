"""
PostgreSQL Membership Repository

Implementation of IMembershipRepository for PostgreSQL database.

Source: INFRA-DEC-007-identity-model.md
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.membership_repository import IMembershipRepository
from ..domain.membership import TenantMembership, MemberRole, MembershipStatus
from ..exceptions import AlreadyMemberError


class PostgresMembershipRepository(IMembershipRepository):
    """PostgreSQL implementation of membership repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session
        """
        self._session = session

    async def create(self, membership: TenantMembership) -> TenantMembership:
        """Create a new membership."""
        # Check if already member
        if await self.is_member(membership.user_id, membership.tenant_id):
            raise AlreadyMemberError(str(membership.user_id), str(membership.tenant_id))

        await self._session.execute(
            text("""
                INSERT INTO tenant_memberships (
                    membership_id, user_id, tenant_id,
                    role, status, invited_by_user_id,
                    invited_at, joined_at, created_at, updated_at
                ) VALUES (
                    :membership_id, :user_id, :tenant_id,
                    :role, :status, :invited_by_user_id,
                    :invited_at, :joined_at, :created_at, :updated_at
                )
            """),
            {
                "membership_id": str(membership.membership_id),
                "user_id": str(membership.user_id),
                "tenant_id": str(membership.tenant_id),
                "role": membership.role.value,
                "status": membership.status.value,
                "invited_by_user_id": str(membership.invited_by_user_id) if membership.invited_by_user_id else None,
                "invited_at": membership.invited_at,
                "joined_at": membership.joined_at,
                "created_at": membership.created_at,
                "updated_at": membership.updated_at,
            }
        )
        await self._session.commit()

        return membership

    async def get_by_id(self, membership_id: UUID) -> Optional[TenantMembership]:
        """Get membership by ID."""
        result = await self._session.execute(
            text("""
                SELECT membership_id, user_id, tenant_id,
                       role, status, invited_by_user_id,
                       invited_at, joined_at, created_at, updated_at
                FROM tenant_memberships
                WHERE membership_id = :membership_id
            """),
            {"membership_id": str(membership_id)}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_membership(row)

    async def get_by_user_and_tenant(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> Optional[TenantMembership]:
        """Get user's membership in a specific tenant."""
        result = await self._session.execute(
            text("""
                SELECT membership_id, user_id, tenant_id,
                       role, status, invited_by_user_id,
                       invited_at, joined_at, created_at, updated_at
                FROM tenant_memberships
                WHERE user_id = :user_id AND tenant_id = :tenant_id
            """),
            {"user_id": str(user_id), "tenant_id": str(tenant_id)}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_membership(row)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_inactive: bool = False
    ) -> List[TenantMembership]:
        """List all memberships for a tenant."""
        status_filter = "" if include_inactive else "AND status = 'active'"

        result = await self._session.execute(
            text(f"""
                SELECT membership_id, user_id, tenant_id,
                       role, status, invited_by_user_id,
                       invited_at, joined_at, created_at, updated_at
                FROM tenant_memberships
                WHERE tenant_id = :tenant_id
                  {status_filter}
                ORDER BY
                    CASE role
                        WHEN 'owner' THEN 1
                        WHEN 'admin' THEN 2
                        WHEN 'member' THEN 3
                        WHEN 'viewer' THEN 4
                    END,
                    created_at
            """),
            {"tenant_id": str(tenant_id)}
        )
        rows = result.fetchall()

        return [self._row_to_membership(row) for row in rows]

    async def list_by_user(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[TenantMembership]:
        """List all memberships for a user."""
        status_filter = "" if include_inactive else "AND status = 'active'"

        result = await self._session.execute(
            text(f"""
                SELECT membership_id, user_id, tenant_id,
                       role, status, invited_by_user_id,
                       invited_at, joined_at, created_at, updated_at
                FROM tenant_memberships
                WHERE user_id = :user_id
                  {status_filter}
                ORDER BY created_at
            """),
            {"user_id": str(user_id)}
        )
        rows = result.fetchall()

        return [self._row_to_membership(row) for row in rows]

    async def count_by_tenant(
        self,
        tenant_id: UUID,
        include_inactive: bool = False
    ) -> int:
        """Count members in a tenant."""
        status_filter = "" if include_inactive else "AND status = 'active'"

        result = await self._session.execute(
            text(f"""
                SELECT COUNT(*)
                FROM tenant_memberships
                WHERE tenant_id = :tenant_id
                  {status_filter}
            """),
            {"tenant_id": str(tenant_id)}
        )
        return result.scalar() or 0

    async def count_owners(self, tenant_id: UUID) -> int:
        """Count owners in a tenant."""
        result = await self._session.execute(
            text("""
                SELECT COUNT(*)
                FROM tenant_memberships
                WHERE tenant_id = :tenant_id
                  AND role = 'owner'
                  AND status = 'active'
            """),
            {"tenant_id": str(tenant_id)}
        )
        return result.scalar() or 0

    async def update(self, membership: TenantMembership) -> TenantMembership:
        """Update membership."""
        await self._session.execute(
            text("""
                UPDATE tenant_memberships SET
                    role = :role,
                    status = :status,
                    joined_at = :joined_at,
                    updated_at = :updated_at
                WHERE membership_id = :membership_id
            """),
            {
                "membership_id": str(membership.membership_id),
                "role": membership.role.value,
                "status": membership.status.value,
                "joined_at": membership.joined_at,
                "updated_at": datetime.utcnow(),
            }
        )
        await self._session.commit()

        return membership

    async def update_role(
        self,
        membership_id: UUID,
        new_role: MemberRole
    ) -> None:
        """Update membership role."""
        await self._session.execute(
            text("""
                UPDATE tenant_memberships SET
                    role = :role,
                    updated_at = NOW()
                WHERE membership_id = :membership_id
            """),
            {"membership_id": str(membership_id), "role": new_role.value}
        )
        await self._session.commit()

    async def update_status(
        self,
        membership_id: UUID,
        status: str
    ) -> None:
        """Update membership status."""
        await self._session.execute(
            text("""
                UPDATE tenant_memberships SET
                    status = :status,
                    updated_at = NOW()
                WHERE membership_id = :membership_id
            """),
            {"membership_id": str(membership_id), "status": status}
        )
        await self._session.commit()

    async def delete(self, membership_id: UUID) -> None:
        """Delete membership (hard delete)."""
        await self._session.execute(
            text("DELETE FROM tenant_memberships WHERE membership_id = :membership_id"),
            {"membership_id": str(membership_id)}
        )
        await self._session.commit()

    async def is_member(self, user_id: UUID, tenant_id: UUID) -> bool:
        """Check if user is a member of tenant."""
        result = await self._session.execute(
            text("""
                SELECT 1 FROM tenant_memberships
                WHERE user_id = :user_id
                  AND tenant_id = :tenant_id
                  AND status = 'active'
            """),
            {"user_id": str(user_id), "tenant_id": str(tenant_id)}
        )
        return result.scalar() is not None

    async def transfer_ownership(
        self,
        tenant_id: UUID,
        from_user_id: UUID,
        to_user_id: UUID
    ) -> None:
        """Transfer tenant ownership to another member."""
        # Demote current owner to admin
        await self._session.execute(
            text("""
                UPDATE tenant_memberships SET
                    role = 'admin',
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
                  AND user_id = :from_user_id
                  AND role = 'owner'
            """),
            {"tenant_id": str(tenant_id), "from_user_id": str(from_user_id)}
        )

        # Promote new owner
        await self._session.execute(
            text("""
                UPDATE tenant_memberships SET
                    role = 'owner',
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
                  AND user_id = :to_user_id
            """),
            {"tenant_id": str(tenant_id), "to_user_id": str(to_user_id)}
        )

        # Update tenant owner
        await self._session.execute(
            text("""
                UPDATE tenants SET
                    owner_user_id = :to_user_id,
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
            """),
            {"tenant_id": str(tenant_id), "to_user_id": str(to_user_id)}
        )

        await self._session.commit()

    def _row_to_membership(self, row) -> TenantMembership:
        """Convert database row to TenantMembership entity."""
        return TenantMembership(
            membership_id=UUID(str(row.membership_id)),
            user_id=UUID(str(row.user_id)),
            tenant_id=UUID(str(row.tenant_id)),
            role=MemberRole(row.role),
            status=MembershipStatus(row.status),
            invited_by_user_id=UUID(str(row.invited_by_user_id)) if row.invited_by_user_id else None,
            invited_at=row.invited_at,
            joined_at=row.joined_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
