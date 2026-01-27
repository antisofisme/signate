"""
Tenant Loader Service for Auth

Simple service to load user's tenants and projects for JWT token creation.
Used by LoginUseCase to populate tenant context.
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ProjectInfo:
    """Project info for login response."""
    project_id: str
    name: str
    slug: str
    is_default: bool


@dataclass
class TenantInfo:
    """Tenant info for login response."""
    tenant_id: str
    name: str
    slug: str
    role: str
    projects: List[dict]


class TenantLoaderService:
    """Service to load user's tenants and projects for login."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_tenants(self, user_id: str) -> List[TenantInfo]:
        """Load user's tenants with their projects.

        Args:
            user_id: User's UUID string

        Returns:
            List of TenantInfo with projects
        """
        # Get user's tenant memberships with tenant details
        result = await self._session.execute(
            text("""
                SELECT
                    t.tenant_id,
                    t.name,
                    t.slug,
                    m.role
                FROM tenant_memberships m
                INNER JOIN tenants t ON m.tenant_id = t.tenant_id
                WHERE m.user_id = :user_id
                  AND m.status = 'active'
                  AND t.is_deleted = FALSE
                ORDER BY t.name
            """),
            {"user_id": user_id}
        )
        tenant_rows = result.fetchall()

        tenants = []
        for row in tenant_rows:
            # Get projects for this tenant
            projects = await self._get_tenant_projects(str(row.tenant_id))

            tenants.append(TenantInfo(
                tenant_id=str(row.tenant_id),
                name=row.name,
                slug=row.slug,
                role=row.role,
                projects=projects,
            ))

        return tenants

    async def _get_tenant_projects(self, tenant_id: str) -> List[dict]:
        """Get projects for a tenant.

        Args:
            tenant_id: Tenant's UUID string

        Returns:
            List of project dicts
        """
        result = await self._session.execute(
            text("""
                SELECT
                    project_id,
                    name,
                    slug,
                    is_default
                FROM projects
                WHERE tenant_id = :tenant_id
                ORDER BY is_default DESC, name
            """),
            {"tenant_id": tenant_id}
        )
        rows = result.fetchall()

        return [
            {
                "project_id": str(row.project_id),
                "name": row.name,
                "slug": row.slug,
                "is_default": row.is_default,
            }
            for row in rows
        ]
