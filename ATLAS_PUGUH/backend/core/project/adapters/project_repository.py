"""
PostgreSQL Project Repository Implementation
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain import Project, ProjectEnvironment
from ..interfaces import IProjectRepository


class PostgresProjectRepository(IProjectRepository):
    """PostgreSQL implementation of project repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _row_to_project(self, row) -> Project:
        """Convert database row to Project entity"""
        return Project(
            project_id=row.project_id,
            tenant_id=row.tenant_id,
            name=row.name,
            slug=row.slug,
            description=row.description,
            environment=ProjectEnvironment(row.environment),
            settings=row.settings or {},
            is_active=row.is_active,
            is_deleted=row.is_deleted,
            deleted_at=row.deleted_at,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, project: Project) -> Project:
        """Create a new project"""
        now = datetime.utcnow()
        query = text("""
            INSERT INTO projects (
                project_id, tenant_id, name, slug, description,
                environment, settings, is_active, is_deleted,
                created_by, created_at, updated_at
            ) VALUES (
                :project_id, :tenant_id, :name, :slug, :description,
                :environment, :settings::jsonb, :is_active, :is_deleted,
                :created_by, :created_at, :updated_at
            )
            RETURNING *
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project.project_id,
                "tenant_id": project.tenant_id,
                "name": project.name,
                "slug": project.slug,
                "description": project.description,
                "environment": project.environment.value,
                "settings": "{}",  # JSON serialization handled separately
                "is_active": project.is_active,
                "is_deleted": False,
                "created_by": project.created_by,
                "created_at": now,
                "updated_at": now,
            },
        )
        await self.session.commit()

        row = result.fetchone()
        return self._row_to_project(row)

    async def get_by_id(self, project_id: UUID, tenant_id: UUID) -> Optional[Project]:
        """Get project by ID within tenant"""
        query = text("""
            SELECT * FROM projects
            WHERE project_id = :project_id
            AND tenant_id = :tenant_id
            AND is_deleted = false
        """)

        result = await self.session.execute(
            query,
            {"project_id": project_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()

        if row:
            return self._row_to_project(row)
        return None

    async def get_by_slug(self, slug: str, tenant_id: UUID) -> Optional[Project]:
        """Get project by slug within tenant"""
        query = text("""
            SELECT * FROM projects
            WHERE slug = :slug
            AND tenant_id = :tenant_id
            AND is_deleted = false
        """)

        result = await self.session.execute(
            query,
            {"slug": slug, "tenant_id": tenant_id},
        )
        row = result.fetchone()

        if row:
            return self._row_to_project(row)
        return None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Project]:
        """List all projects for a tenant"""
        if include_deleted:
            query = text("""
                SELECT * FROM projects
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
        else:
            query = text("""
                SELECT * FROM projects
                WHERE tenant_id = :tenant_id
                AND is_deleted = false
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

        result = await self.session.execute(
            query,
            {"tenant_id": tenant_id, "limit": limit, "offset": offset},
        )
        rows = result.fetchall()

        return [self._row_to_project(row) for row in rows]

    async def update(self, project: Project) -> Project:
        """Update an existing project"""
        query = text("""
            UPDATE projects
            SET name = :name,
                slug = :slug,
                description = :description,
                environment = :environment,
                settings = :settings::jsonb,
                is_active = :is_active,
                updated_at = :updated_at
            WHERE project_id = :project_id
            AND tenant_id = :tenant_id
            AND is_deleted = false
            RETURNING *
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project.project_id,
                "tenant_id": project.tenant_id,
                "name": project.name,
                "slug": project.slug,
                "description": project.description,
                "environment": project.environment.value,
                "settings": "{}",
                "is_active": project.is_active,
                "updated_at": datetime.utcnow(),
            },
        )
        await self.session.commit()

        row = result.fetchone()
        if row:
            return self._row_to_project(row)
        return project

    async def delete(self, project_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete a project"""
        query = text("""
            UPDATE projects
            SET is_deleted = true,
                is_active = false,
                deleted_at = :deleted_at,
                updated_at = :updated_at
            WHERE project_id = :project_id
            AND tenant_id = :tenant_id
            AND is_deleted = false
        """)

        now = datetime.utcnow()
        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "tenant_id": tenant_id,
                "deleted_at": now,
                "updated_at": now,
            },
        )
        await self.session.commit()

        return result.rowcount > 0

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count active projects for a tenant"""
        query = text("""
            SELECT COUNT(*) as count FROM projects
            WHERE tenant_id = :tenant_id
            AND is_deleted = false
        """)

        result = await self.session.execute(query, {"tenant_id": tenant_id})
        row = result.fetchone()
        return row.count if row else 0

    async def slug_exists(
        self, slug: str, tenant_id: UUID, exclude_id: Optional[UUID] = None
    ) -> bool:
        """Check if slug exists in tenant"""
        if exclude_id:
            query = text("""
                SELECT EXISTS(
                    SELECT 1 FROM projects
                    WHERE slug = :slug
                    AND tenant_id = :tenant_id
                    AND project_id != :exclude_id
                    AND is_deleted = false
                ) as exists
            """)
            result = await self.session.execute(
                query,
                {"slug": slug, "tenant_id": tenant_id, "exclude_id": exclude_id},
            )
        else:
            query = text("""
                SELECT EXISTS(
                    SELECT 1 FROM projects
                    WHERE slug = :slug
                    AND tenant_id = :tenant_id
                    AND is_deleted = false
                ) as exists
            """)
            result = await self.session.execute(
                query,
                {"slug": slug, "tenant_id": tenant_id},
            )

        row = result.fetchone()
        return row.exists if row else False
