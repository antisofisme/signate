"""
PostgreSQL Tenant Repository

Implementation of ITenantRepository for PostgreSQL database.

Source: INFRA-DEC-007-identity-model.md
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.tenant_repository import ITenantRepository
from ..domain.tenant import Tenant, TenantStatus, TenantPlan
from ..exceptions import TenantSlugExistsError
import json


class PostgresTenantRepository(ITenantRepository):
    """PostgreSQL implementation of tenant repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session
        """
        self._session = session

    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        # Check if slug exists
        if await self.slug_exists(tenant.slug):
            raise TenantSlugExistsError(tenant.slug)

        await self._session.execute(
            text("""
                INSERT INTO tenants (
                    tenant_id, name, slug, owner_user_id,
                    plan, status, settings, billing_email,
                    is_deleted, created_at, updated_at
                ) VALUES (
                    :tenant_id, :name, :slug, :owner_user_id,
                    :plan, :status, :settings, :billing_email,
                    :is_deleted, :created_at, :updated_at
                )
            """),
            {
                "tenant_id": str(tenant.tenant_id),
                "name": tenant.name,
                "slug": tenant.slug,
                "owner_user_id": str(tenant.owner_user_id),
                "plan": tenant.plan.value,
                "status": tenant.status.value,
                "settings": json.dumps(tenant.settings),
                "billing_email": tenant.billing_email,
                "is_deleted": tenant.is_deleted,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at,
            }
        )
        await self._session.commit()

        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await self._session.execute(
            text("""
                SELECT tenant_id, name, slug, owner_user_id,
                       plan, status, settings, billing_email,
                       is_deleted, deleted_at, created_at, updated_at
                FROM tenants
                WHERE tenant_id = :tenant_id
            """),
            {"tenant_id": str(tenant_id)}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_tenant(row)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        result = await self._session.execute(
            text("""
                SELECT tenant_id, name, slug, owner_user_id,
                       plan, status, settings, billing_email,
                       is_deleted, deleted_at, created_at, updated_at
                FROM tenants
                WHERE LOWER(slug) = LOWER(:slug)
                  AND is_deleted = FALSE
            """),
            {"slug": slug}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_tenant(row)

    async def list_by_user(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[Tenant]:
        """List tenants that user is a member of."""
        status_filter = "" if include_inactive else "AND t.status != 'suspended' AND t.is_deleted = FALSE"

        result = await self._session.execute(
            text(f"""
                SELECT t.tenant_id, t.name, t.slug, t.owner_user_id,
                       t.plan, t.status, t.settings, t.billing_email,
                       t.is_deleted, t.deleted_at, t.created_at, t.updated_at
                FROM tenants t
                INNER JOIN tenant_memberships m ON t.tenant_id = m.tenant_id
                WHERE m.user_id = :user_id
                  AND m.status = 'active'
                  {status_filter}
                ORDER BY t.name
            """),
            {"user_id": str(user_id)}
        )
        rows = result.fetchall()

        return [self._row_to_tenant(row) for row in rows]

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        include_inactive: bool = False
    ) -> List[Tenant]:
        """List all tenants (admin only)."""
        status_filter = "" if include_inactive else "WHERE status != 'suspended' AND is_deleted = FALSE"

        result = await self._session.execute(
            text(f"""
                SELECT tenant_id, name, slug, owner_user_id,
                       plan, status, settings, billing_email,
                       is_deleted, deleted_at, created_at, updated_at
                FROM tenants
                {status_filter}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset}
        )
        rows = result.fetchall()

        return [self._row_to_tenant(row) for row in rows]

    async def count_all(self, include_inactive: bool = False) -> int:
        """Count all tenants."""
        status_filter = "" if include_inactive else "WHERE status != 'suspended' AND is_deleted = FALSE"

        result = await self._session.execute(
            text(f"SELECT COUNT(*) FROM tenants {status_filter}")
        )
        return result.scalar() or 0

    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant."""
        await self._session.execute(
            text("""
                UPDATE tenants SET
                    name = :name,
                    settings = :settings,
                    billing_email = :billing_email,
                    updated_at = :updated_at
                WHERE tenant_id = :tenant_id
            """),
            {
                "tenant_id": str(tenant.tenant_id),
                "name": tenant.name,
                "settings": json.dumps(tenant.settings),
                "billing_email": tenant.billing_email,
                "updated_at": datetime.utcnow(),
            }
        )
        await self._session.commit()

        return tenant

    async def update_status(self, tenant_id: UUID, status: str) -> None:
        """Update tenant status."""
        await self._session.execute(
            text("""
                UPDATE tenants SET
                    status = :status,
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
            """),
            {"tenant_id": str(tenant_id), "status": status}
        )
        await self._session.commit()

    async def update_plan(self, tenant_id: UUID, plan: str) -> None:
        """Update tenant subscription plan."""
        await self._session.execute(
            text("""
                UPDATE tenants SET
                    plan = :plan,
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
            """),
            {"tenant_id": str(tenant_id), "plan": plan}
        )
        await self._session.commit()

    async def soft_delete(self, tenant_id: UUID) -> None:
        """Soft delete tenant."""
        await self._session.execute(
            text("""
                UPDATE tenants SET
                    is_deleted = TRUE,
                    deleted_at = NOW(),
                    updated_at = NOW()
                WHERE tenant_id = :tenant_id
            """),
            {"tenant_id": str(tenant_id)}
        )
        await self._session.commit()

    async def slug_exists(
        self,
        slug: str,
        exclude_tenant_id: Optional[UUID] = None
    ) -> bool:
        """Check if slug exists."""
        if exclude_tenant_id:
            result = await self._session.execute(
                text("""
                    SELECT 1 FROM tenants
                    WHERE LOWER(slug) = LOWER(:slug)
                      AND tenant_id != :exclude_id
                      AND is_deleted = FALSE
                """),
                {"slug": slug, "exclude_id": str(exclude_tenant_id)}
            )
        else:
            result = await self._session.execute(
                text("""
                    SELECT 1 FROM tenants
                    WHERE LOWER(slug) = LOWER(:slug)
                      AND is_deleted = FALSE
                """),
                {"slug": slug}
            )
        return result.scalar() is not None

    def _row_to_tenant(self, row) -> Tenant:
        """Convert database row to Tenant entity."""
        settings = row.settings
        if isinstance(settings, str):
            settings = json.loads(settings)
        elif settings is None:
            settings = {}

        return Tenant(
            tenant_id=UUID(str(row.tenant_id)),
            name=row.name,
            slug=row.slug,
            owner_user_id=UUID(str(row.owner_user_id)),
            plan=TenantPlan(row.plan),
            status=TenantStatus(row.status),
            settings=settings,
            billing_email=row.billing_email,
            is_deleted=row.is_deleted,
            deleted_at=row.deleted_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
