"""
PostgreSQL Project Membership Repository Implementation
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain import ProjectMembership, ProjectRole
from ..interfaces import IProjectMembershipRepository


class PostgresMembershipRepository(IProjectMembershipRepository):
    """PostgreSQL implementation of project membership repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _row_to_membership(self, row) -> ProjectMembership:
        """Convert database row to ProjectMembership entity"""
        return ProjectMembership(
            project_id=row.project_id,
            user_id=row.user_id,
            role=ProjectRole(row.role),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, membership: ProjectMembership) -> ProjectMembership:
        """Add a member to a project"""
        now = datetime.utcnow()
        query = text("""
            INSERT INTO project_memberships (
                project_id, user_id, role, created_at, updated_at
            ) VALUES (
                :project_id, :user_id, :role, :created_at, :updated_at
            )
            ON CONFLICT (project_id, user_id) DO UPDATE
            SET role = :role, updated_at = :updated_at
            RETURNING *
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": membership.project_id,
                "user_id": membership.user_id,
                "role": membership.role.value,
                "created_at": now,
                "updated_at": now,
            },
        )
        await self.session.commit()

        row = result.fetchone()
        return self._row_to_membership(row)

    async def get(self, project_id: UUID, user_id: UUID) -> Optional[ProjectMembership]:
        """Get membership for user in project"""
        query = text("""
            SELECT * FROM project_memberships
            WHERE project_id = :project_id
            AND user_id = :user_id
        """)

        result = await self.session.execute(
            query,
            {"project_id": project_id, "user_id": user_id},
        )
        row = result.fetchone()

        if row:
            return self._row_to_membership(row)
        return None

    async def list_by_project(self, project_id: UUID) -> List[ProjectMembership]:
        """List all members of a project"""
        query = text("""
            SELECT * FROM project_memberships
            WHERE project_id = :project_id
            ORDER BY created_at ASC
        """)

        result = await self.session.execute(query, {"project_id": project_id})
        rows = result.fetchall()

        return [self._row_to_membership(row) for row in rows]

    async def list_by_user(self, user_id: UUID, tenant_id: UUID) -> List[ProjectMembership]:
        """List all project memberships for a user within tenant"""
        query = text("""
            SELECT pm.* FROM project_memberships pm
            JOIN projects p ON pm.project_id = p.project_id
            WHERE pm.user_id = :user_id
            AND p.tenant_id = :tenant_id
            AND p.is_deleted = false
            ORDER BY pm.created_at ASC
        """)

        result = await self.session.execute(
            query,
            {"user_id": user_id, "tenant_id": tenant_id},
        )
        rows = result.fetchall()

        return [self._row_to_membership(row) for row in rows]

    async def update_role(
        self, project_id: UUID, user_id: UUID, new_role: ProjectRole
    ) -> Optional[ProjectMembership]:
        """Update member's role"""
        query = text("""
            UPDATE project_memberships
            SET role = :role, updated_at = :updated_at
            WHERE project_id = :project_id
            AND user_id = :user_id
            RETURNING *
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "user_id": user_id,
                "role": new_role.value,
                "updated_at": datetime.utcnow(),
            },
        )
        await self.session.commit()

        row = result.fetchone()
        if row:
            return self._row_to_membership(row)
        return None

    async def delete(self, project_id: UUID, user_id: UUID) -> bool:
        """Remove member from project"""
        query = text("""
            DELETE FROM project_memberships
            WHERE project_id = :project_id
            AND user_id = :user_id
        """)

        result = await self.session.execute(
            query,
            {"project_id": project_id, "user_id": user_id},
        )
        await self.session.commit()

        return result.rowcount > 0

    async def has_access(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user has any access to project"""
        query = text("""
            SELECT EXISTS(
                SELECT 1 FROM project_memberships
                WHERE project_id = :project_id
                AND user_id = :user_id
            ) as has_access
        """)

        result = await self.session.execute(
            query,
            {"project_id": project_id, "user_id": user_id},
        )
        row = result.fetchone()
        return row.has_access if row else False

    async def count_admins(self, project_id: UUID) -> int:
        """Count admins in project (for preventing last admin removal)"""
        query = text("""
            SELECT COUNT(*) as count FROM project_memberships
            WHERE project_id = :project_id
            AND role = 'admin'
        """)

        result = await self.session.execute(query, {"project_id": project_id})
        row = result.fetchone()
        return row.count if row else 0
