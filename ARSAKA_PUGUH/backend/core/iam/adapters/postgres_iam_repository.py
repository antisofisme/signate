"""
PostgreSQL IAM Repository Implementation

Concrete implementation of IIAMRepository for PostgreSQL.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..interfaces import IIAMRepository
from ..domain import Role, Permission, ServiceAccount, ServiceAccountStatus
from ..exceptions import (
    RoleNotFoundError,
    RoleNameExistsError,
    SystemRoleError,
    RoleInUseError,
    UserNotFoundError,
    RoleAlreadyAssignedError,
    RoleNotAssignedError,
)


class PostgresIAMRepository(IIAMRepository):
    """PostgreSQL implementation of IAM repository."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    # =========================================================================
    # User Operations
    # =========================================================================

    async def list_users(
        self,
        tenant_id: UUID,
        role_id: Optional[UUID] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[dict], int]:
        """List users in a tenant via tenant_members."""
        async with self._session_factory() as session:
            # Build base query joining users with tenant_members
            base_query = """
                SELECT
                    u.id,
                    u.email,
                    u.full_name,
                    u.avatar_url,
                    u.is_verified,
                    u.last_login_at,
                    u.created_at,
                    tm.role as membership_role,
                    tm.joined_at
                FROM users u
                INNER JOIN tenant_members tm ON u.id = tm.user_id
                WHERE tm.tenant_id = :tenant_id
            """
            params = {"tenant_id": str(tenant_id)}

            # Add role filter if provided
            if role_id:
                base_query += """
                    AND u.id IN (
                        SELECT user_id FROM user_roles
                        WHERE role_id = :role_id AND tenant_id = :tenant_id
                    )
                """
                params["role_id"] = str(role_id)

            # Add search filter if provided
            if search:
                base_query += """
                    AND (
                        u.email ILIKE :search
                        OR u.full_name ILIKE :search
                    )
                """
                params["search"] = f"%{search}%"

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            # Add pagination
            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY u.created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            users = [
                {
                    "id": str(row.id),
                    "email": row.email,
                    "full_name": row.full_name,
                    "avatar_url": row.avatar_url,
                    "is_verified": row.is_verified,
                    "last_login_at": row.last_login_at.isoformat() if row.last_login_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "membership_role": row.membership_role,
                    "joined_at": row.joined_at.isoformat() if row.joined_at else None,
                }
                for row in rows
            ]

            return users, total

    async def get_user(self, tenant_id: UUID, user_id: UUID) -> Optional[dict]:
        """Get user by ID with tenant membership check."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    u.id,
                    u.email,
                    u.full_name,
                    u.avatar_url,
                    u.is_verified,
                    u.last_login_at,
                    u.created_at,
                    tm.role as membership_role,
                    tm.joined_at
                FROM users u
                INNER JOIN tenant_members tm ON u.id = tm.user_id
                WHERE u.id = :user_id AND tm.tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"user_id": str(user_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return {
                "id": str(row.id),
                "email": row.email,
                "full_name": row.full_name,
                "avatar_url": row.avatar_url,
                "is_verified": row.is_verified,
                "last_login_at": row.last_login_at.isoformat() if row.last_login_at else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "membership_role": row.membership_role,
                "joined_at": row.joined_at.isoformat() if row.joined_at else None,
            }

    async def get_user_roles(self, tenant_id: UUID, user_id: UUID) -> List[Role]:
        """Get roles assigned to a user in a tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    r.id,
                    r.tenant_id,
                    r.name,
                    r.display_name,
                    r.description,
                    r.is_system,
                    r.created_at,
                    r.updated_at
                FROM roles r
                INNER JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = :user_id AND ur.tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"user_id": str(user_id), "tenant_id": str(tenant_id)}
            )
            rows = result.fetchall()

            return [
                Role(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    name=row.name,
                    display_name=row.display_name,
                    description=row.description,
                    is_system=row.is_system,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in rows
            ]

    # =========================================================================
    # Role Operations
    # =========================================================================

    async def list_roles(self, tenant_id: UUID) -> List[Role]:
        """List all roles in a tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    id, tenant_id, name, display_name, description,
                    is_system, created_at, updated_at
                FROM roles
                WHERE tenant_id = :tenant_id
                ORDER BY is_system DESC, name ASC
            """
            result = await session.execute(text(query), {"tenant_id": str(tenant_id)})
            rows = result.fetchall()

            return [
                Role(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    name=row.name,
                    display_name=row.display_name,
                    description=row.description,
                    is_system=row.is_system,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in rows
            ]

    async def get_role(self, tenant_id: UUID, role_id: UUID) -> Optional[Role]:
        """Get role by ID."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    id, tenant_id, name, display_name, description,
                    is_system, created_at, updated_at
                FROM roles
                WHERE id = :role_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"role_id": str(role_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return Role(
                id=row.id,
                tenant_id=row.tenant_id,
                name=row.name,
                display_name=row.display_name,
                description=row.description,
                is_system=row.is_system,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def get_role_permissions(self, role_id: UUID) -> List[Permission]:
        """Get permissions assigned to a role."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    p.id, p.resource, p.action, p.description, p.created_at
                FROM permissions p
                INNER JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = :role_id
                ORDER BY p.resource, p.action
            """
            result = await session.execute(text(query), {"role_id": str(role_id)})
            rows = result.fetchall()

            return [
                Permission(
                    id=row.id,
                    resource=row.resource,
                    action=row.action,
                    description=row.description,
                    created_at=row.created_at,
                )
                for row in rows
            ]

    # =========================================================================
    # Permission Operations
    # =========================================================================

    async def list_permissions(self) -> List[Permission]:
        """List all available permissions."""
        async with self._session_factory() as session:
            query = """
                SELECT id, resource, action, description, created_at
                FROM permissions
                ORDER BY resource, action
            """
            result = await session.execute(text(query))
            rows = result.fetchall()

            return [
                Permission(
                    id=row.id,
                    resource=row.resource,
                    action=row.action,
                    description=row.description,
                    created_at=row.created_at,
                )
                for row in rows
            ]

    async def get_permission_matrix(self, tenant_id: UUID) -> dict:
        """Get permission matrix showing all roles and their permissions."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    r.id as role_id,
                    r.name as role_name,
                    r.display_name as role_display_name,
                    COALESCE(
                        array_agg(DISTINCT p.resource || '.' || p.action)
                        FILTER (WHERE p.id IS NOT NULL),
                        ARRAY[]::text[]
                    ) as permissions
                FROM roles r
                LEFT JOIN role_permissions rp ON r.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE r.tenant_id = :tenant_id
                GROUP BY r.id, r.name, r.display_name
                ORDER BY r.is_system DESC, r.name
            """
            result = await session.execute(text(query), {"tenant_id": str(tenant_id)})
            rows = result.fetchall()

            return {
                "roles": [
                    {
                        "id": str(row.role_id),
                        "name": row.role_name,
                        "display_name": row.role_display_name,
                        "permissions": list(row.permissions) if row.permissions else [],
                    }
                    for row in rows
                ]
            }

    # =========================================================================
    # Service Account Operations
    # =========================================================================

    async def list_service_accounts(
        self,
        tenant_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[ServiceAccount], int]:
        """List service accounts in a tenant."""
        async with self._session_factory() as session:
            # Count total
            count_query = """
                SELECT COUNT(*) FROM service_accounts
                WHERE tenant_id = :tenant_id
            """
            result = await session.execute(
                text(count_query), {"tenant_id": str(tenant_id)}
            )
            total = result.scalar() or 0

            # Get paginated list
            offset = (page - 1) * limit
            query = """
                SELECT
                    id, tenant_id, name, description, client_id, status,
                    last_used_at, created_by, created_at, updated_at
                FROM service_accounts
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            result = await session.execute(
                text(query),
                {"tenant_id": str(tenant_id), "limit": limit, "offset": offset}
            )
            rows = result.fetchall()

            accounts = [
                ServiceAccount(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    name=row.name,
                    description=row.description,
                    client_id=row.client_id,
                    status=ServiceAccountStatus(row.status),
                    last_used_at=row.last_used_at,
                    created_by=row.created_by,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in rows
            ]

            return accounts, total

    async def get_service_account(
        self, tenant_id: UUID, account_id: UUID
    ) -> Optional[ServiceAccount]:
        """Get service account by ID."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    id, tenant_id, name, description, client_id, status,
                    last_used_at, created_by, created_at, updated_at
                FROM service_accounts
                WHERE id = :account_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"account_id": str(account_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return ServiceAccount(
                id=row.id,
                tenant_id=row.tenant_id,
                name=row.name,
                description=row.description,
                client_id=row.client_id,
                status=ServiceAccountStatus(row.status),
                last_used_at=row.last_used_at,
                created_by=row.created_by,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )

    async def get_user_stats(self, tenant_id: UUID) -> dict:
        """Get user statistics for tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN u.is_verified = true THEN 1 END) as active,
                    COUNT(CASE WHEN u.is_verified = false THEN 1 END) as inactive
                FROM users u
                INNER JOIN tenant_members tm ON u.id = tm.user_id
                WHERE tm.tenant_id = :tenant_id
            """
            result = await session.execute(text(query), {"tenant_id": str(tenant_id)})
            row = result.fetchone()

            return {
                "total": row.total or 0,
                "active": row.active or 0,
                "inactive": row.inactive or 0,
            }

    # =========================================================================
    # Role Write Operations
    # =========================================================================

    async def create_role(
        self,
        tenant_id: UUID,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
    ) -> Role:
        """Create a new role in a tenant."""
        async with self._session_factory() as session:
            # Check if name exists
            if await self.role_name_exists(tenant_id, name):
                raise RoleNameExistsError(name)

            role_id = uuid4()
            now = datetime.utcnow()

            # Insert role
            insert_query = """
                INSERT INTO roles (id, tenant_id, name, display_name, description, is_system, created_at, updated_at)
                VALUES (:id, :tenant_id, :name, :display_name, :description, false, :created_at, :updated_at)
            """
            await session.execute(
                text(insert_query),
                {
                    "id": str(role_id),
                    "tenant_id": str(tenant_id),
                    "name": name,
                    "display_name": display_name,
                    "description": description,
                    "created_at": now,
                    "updated_at": now,
                }
            )

            # Assign permissions if provided
            if permission_ids:
                for perm_id in permission_ids:
                    perm_query = """
                        INSERT INTO role_permissions (role_id, permission_id, created_at)
                        VALUES (:role_id, :permission_id, :created_at)
                    """
                    await session.execute(
                        text(perm_query),
                        {
                            "role_id": str(role_id),
                            "permission_id": str(perm_id),
                            "created_at": now,
                        }
                    )

            await session.commit()

            return Role(
                id=role_id,
                tenant_id=tenant_id,
                name=name,
                display_name=display_name,
                description=description,
                is_system=False,
                created_at=now,
                updated_at=now,
            )

    async def update_role(
        self,
        tenant_id: UUID,
        role_id: UUID,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permission_ids: Optional[List[UUID]] = None,
    ) -> Role:
        """Update an existing role."""
        async with self._session_factory() as session:
            # Get existing role
            role = await self.get_role(tenant_id, role_id)
            if not role:
                raise RoleNotFoundError(str(role_id))

            # Check if system role
            if role.is_system:
                raise SystemRoleError("update")

            # Check name uniqueness if changing
            if name and name != role.name:
                if await self.role_name_exists(tenant_id, name, exclude_role_id=role_id):
                    raise RoleNameExistsError(name)

            now = datetime.utcnow()

            # Build update query
            update_fields = ["updated_at = :updated_at"]
            params = {"role_id": str(role_id), "tenant_id": str(tenant_id), "updated_at": now}

            if name is not None:
                update_fields.append("name = :name")
                params["name"] = name
            if display_name is not None:
                update_fields.append("display_name = :display_name")
                params["display_name"] = display_name
            if description is not None:
                update_fields.append("description = :description")
                params["description"] = description

            update_query = f"""
                UPDATE roles
                SET {', '.join(update_fields)}
                WHERE id = :role_id AND tenant_id = :tenant_id
            """
            await session.execute(text(update_query), params)

            # Update permissions if provided
            if permission_ids is not None:
                # Delete existing permissions
                delete_perms = """
                    DELETE FROM role_permissions WHERE role_id = :role_id
                """
                await session.execute(text(delete_perms), {"role_id": str(role_id)})

                # Insert new permissions
                for perm_id in permission_ids:
                    insert_perm = """
                        INSERT INTO role_permissions (role_id, permission_id, created_at)
                        VALUES (:role_id, :permission_id, :created_at)
                    """
                    await session.execute(
                        text(insert_perm),
                        {
                            "role_id": str(role_id),
                            "permission_id": str(perm_id),
                            "created_at": now,
                        }
                    )

            await session.commit()

            # Return updated role
            return Role(
                id=role_id,
                tenant_id=tenant_id,
                name=name if name is not None else role.name,
                display_name=display_name if display_name is not None else role.display_name,
                description=description if description is not None else role.description,
                is_system=role.is_system,
                created_at=role.created_at,
                updated_at=now,
            )

    async def delete_role(self, tenant_id: UUID, role_id: UUID) -> bool:
        """Delete a role (soft delete)."""
        async with self._session_factory() as session:
            # Get existing role
            role = await self.get_role(tenant_id, role_id)
            if not role:
                raise RoleNotFoundError(str(role_id))

            # Check if system role
            if role.is_system:
                raise SystemRoleError("delete")

            # Check if role is in use
            user_count = await self.get_role_user_count(tenant_id, role_id)
            if user_count > 0:
                raise RoleInUseError(str(role_id), user_count)

            # Delete role permissions first
            delete_perms = """
                DELETE FROM role_permissions WHERE role_id = :role_id
            """
            await session.execute(text(delete_perms), {"role_id": str(role_id)})

            # Delete role
            delete_role = """
                DELETE FROM roles WHERE id = :role_id AND tenant_id = :tenant_id
            """
            await session.execute(
                text(delete_role),
                {"role_id": str(role_id), "tenant_id": str(tenant_id)}
            )

            await session.commit()
            return True

    async def role_name_exists(
        self, tenant_id: UUID, name: str, exclude_role_id: Optional[UUID] = None
    ) -> bool:
        """Check if role name exists in tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT COUNT(*) FROM roles
                WHERE tenant_id = :tenant_id AND name = :name
            """
            params = {"tenant_id": str(tenant_id), "name": name}

            if exclude_role_id:
                query += " AND id != :exclude_role_id"
                params["exclude_role_id"] = str(exclude_role_id)

            result = await session.execute(text(query), params)
            count = result.scalar() or 0
            return count > 0

    async def get_role_user_count(self, tenant_id: UUID, role_id: UUID) -> int:
        """Get count of users assigned to a role."""
        async with self._session_factory() as session:
            query = """
                SELECT COUNT(*) FROM user_roles
                WHERE tenant_id = :tenant_id AND role_id = :role_id
            """
            result = await session.execute(
                text(query),
                {"tenant_id": str(tenant_id), "role_id": str(role_id)}
            )
            return result.scalar() or 0

    # =========================================================================
    # User-Role Assignment Operations
    # =========================================================================

    async def assign_role_to_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID,
    ) -> bool:
        """Assign a role to a user."""
        async with self._session_factory() as session:
            # Check if user exists in tenant
            if not await self.user_exists_in_tenant(tenant_id, user_id):
                raise UserNotFoundError(str(user_id))

            # Check if role exists
            role = await self.get_role(tenant_id, role_id)
            if not role:
                raise RoleNotFoundError(str(role_id))

            # Check if already assigned
            if await self.user_has_role(tenant_id, user_id, role_id):
                raise RoleAlreadyAssignedError(str(user_id), str(role_id))

            now = datetime.utcnow()

            # Insert user_role
            insert_query = """
                INSERT INTO user_roles (user_id, role_id, tenant_id, assigned_by, created_at)
                VALUES (:user_id, :role_id, :tenant_id, :assigned_by, :created_at)
            """
            await session.execute(
                text(insert_query),
                {
                    "user_id": str(user_id),
                    "role_id": str(role_id),
                    "tenant_id": str(tenant_id),
                    "assigned_by": str(assigned_by),
                    "created_at": now,
                }
            )

            await session.commit()
            return True

    async def revoke_role_from_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> bool:
        """Revoke a role from a user."""
        async with self._session_factory() as session:
            # Check if user exists in tenant
            if not await self.user_exists_in_tenant(tenant_id, user_id):
                raise UserNotFoundError(str(user_id))

            # Check if role exists
            role = await self.get_role(tenant_id, role_id)
            if not role:
                raise RoleNotFoundError(str(role_id))

            # Check if assigned
            if not await self.user_has_role(tenant_id, user_id, role_id):
                raise RoleNotAssignedError(str(user_id), str(role_id))

            # Delete user_role
            delete_query = """
                DELETE FROM user_roles
                WHERE user_id = :user_id AND role_id = :role_id AND tenant_id = :tenant_id
            """
            await session.execute(
                text(delete_query),
                {
                    "user_id": str(user_id),
                    "role_id": str(role_id),
                    "tenant_id": str(tenant_id),
                }
            )

            await session.commit()
            return True

    async def user_has_role(
        self, tenant_id: UUID, user_id: UUID, role_id: UUID
    ) -> bool:
        """Check if user has a specific role."""
        async with self._session_factory() as session:
            query = """
                SELECT COUNT(*) FROM user_roles
                WHERE user_id = :user_id AND role_id = :role_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {
                    "user_id": str(user_id),
                    "role_id": str(role_id),
                    "tenant_id": str(tenant_id),
                }
            )
            count = result.scalar() or 0
            return count > 0

    async def user_exists_in_tenant(self, tenant_id: UUID, user_id: UUID) -> bool:
        """Check if user exists in tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT COUNT(*) FROM tenant_members
                WHERE tenant_id = :tenant_id AND user_id = :user_id
            """
            result = await session.execute(
                text(query),
                {"tenant_id": str(tenant_id), "user_id": str(user_id)}
            )
            count = result.scalar() or 0
            return count > 0
