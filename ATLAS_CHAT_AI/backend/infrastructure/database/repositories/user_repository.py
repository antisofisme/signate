"""
User repository.
"""

from typing import Optional, List
from uuid import UUID

from .base_repository import BaseRepository
from ....core.entities import User, UserProfile
from ....shared.logging import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self, pool):
        super().__init__(pool, "users")

    def _row_to_entity(self, row) -> User:
        """Convert database row to User."""
        return User(
            id=row["id"],
            tenant_id=row["tenant_id"],
            external_user_id=row["external_user_id"],
            profile=UserProfile(
                display_name=row["display_name"],
                email=row["email"],
                avatar_url=row["avatar_url"],
                timezone=row["timezone"] or "UTC",
                language=row["language"] or "en",
            ),
            role=row["role"],
            custom_permissions=row["custom_permissions"] or [],
            is_active=row["is_active"],
            last_seen_at=row["last_seen_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create(self, user: User) -> str:
        """Create a new user."""
        query = """
            INSERT INTO users (
                id, tenant_id, external_user_id,
                email, display_name, avatar_url, timezone, language,
                role, custom_permissions, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """

        result = await self._fetchval(
            query,
            user.id, user.tenant_id, user.external_user_id,
            user.profile.email, user.profile.display_name,
            user.profile.avatar_url, user.profile.timezone, user.profile.language,
            user.role, user.custom_permissions, user.is_active
        )

        logger.info(f"Created user: {result} for tenant: {user.tenant_id}")
        return str(result)

    async def get_by_id(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[User]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = $1 AND tenant_id = $2"
        row = await self._fetchrow(query, user_id, tenant_id)
        return self._row_to_entity(row) if row else None

    async def get_by_external_id(
        self,
        external_user_id: str,
        tenant_id: str
    ) -> Optional[User]:
        """Get user by external ID."""
        query = """
            SELECT * FROM users
            WHERE external_user_id = $1 AND tenant_id = $2
        """
        row = await self._fetchrow(query, external_user_id, tenant_id)
        return self._row_to_entity(row) if row else None

    async def get_or_create(
        self,
        external_user_id: str,
        tenant_id: str,
        display_name: str,
        email: Optional[str] = None
    ) -> User:
        """Get existing user or create new one."""
        # Try to get existing user
        user = await self.get_by_external_id(external_user_id, tenant_id)
        if user:
            # Update last seen
            await self.update_last_seen(str(user.id), tenant_id)
            return user

        # Create new user
        new_user = User(
            tenant_id=tenant_id,
            external_user_id=external_user_id,
            profile=UserProfile(
                display_name=display_name,
                email=email,
            ),
        )

        await self.create(new_user)
        return new_user

    async def update(self, user: User) -> bool:
        """Update user details."""
        query = """
            UPDATE users SET
                email = $3,
                display_name = $4,
                avatar_url = $5,
                timezone = $6,
                language = $7,
                role = $8,
                custom_permissions = $9,
                is_active = $10,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
        """

        result = await self._execute(
            query,
            str(user.id), user.tenant_id,
            user.profile.email, user.profile.display_name,
            user.profile.avatar_url, user.profile.timezone, user.profile.language,
            user.role, user.custom_permissions, user.is_active
        )

        return "UPDATE 1" in result

    async def update_last_seen(
        self,
        user_id: str,
        tenant_id: str
    ) -> bool:
        """Update last seen timestamp."""
        query = """
            UPDATE users SET
                last_seen_at = NOW(),
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2
        """

        result = await self._execute(query, user_id, tenant_id)
        return "UPDATE 1" in result

    async def list_by_tenant(
        self,
        tenant_id: str,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
        role: Optional[str] = None,
    ) -> List[User]:
        """List users for tenant."""
        conditions = ["tenant_id = $1"]
        params = [tenant_id]
        param_idx = 2

        if active_only:
            conditions.append("is_active = TRUE")

        if role:
            conditions.append(f"role = ${param_idx}")
            params.append(role)
            param_idx += 1

        query = f"""
            SELECT * FROM users
            WHERE {' AND '.join(conditions)}
            ORDER BY display_name
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        rows = await self._fetch(query, *params)
        return [self._row_to_entity(row) for row in rows]

    async def update_fields(
        self,
        user_id: str,
        tenant_id: str,
        updates: dict
    ) -> bool:
        """Update specific user fields."""
        if not updates:
            return True

        # Build dynamic update query
        set_clauses = []
        params = [user_id, tenant_id]
        param_idx = 3

        field_mapping = {
            "email": "email",
            "display_name": "display_name",
            "avatar_url": "avatar_url",
            "role": "role",
            "custom_permissions": "custom_permissions",
            "is_active": "is_active",
        }

        for key, value in updates.items():
            if key in field_mapping:
                set_clauses.append(f"{field_mapping[key]} = ${param_idx}")
                params.append(value)
                param_idx += 1

        if not set_clauses:
            return True

        set_clauses.append("updated_at = NOW()")

        query = f"""
            UPDATE users SET {', '.join(set_clauses)}
            WHERE id = $1 AND tenant_id = $2
        """

        result = await self._execute(query, *params)
        return "UPDATE 1" in result

    async def soft_delete(
        self,
        user_id: str,
        tenant_id: str,
    ) -> bool:
        """Soft-delete a user."""
        return await self.deactivate(user_id, tenant_id)

    async def deactivate(
        self,
        user_id: str,
        tenant_id: str
    ) -> bool:
        """Deactivate a user."""
        query = """
            UPDATE users SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = $1 AND tenant_id = $2 AND is_active = TRUE
        """

        result = await self._execute(query, user_id, tenant_id)
        return "UPDATE 1" in result

    async def count_by_tenant(
        self,
        tenant_id: str,
        active_only: bool = True
    ) -> int:
        """Count users for tenant."""
        if active_only:
            query = """
                SELECT COUNT(*) FROM users
                WHERE tenant_id = $1 AND is_active = TRUE
            """
        else:
            query = """
                SELECT COUNT(*) FROM users
                WHERE tenant_id = $1
            """

        return await self._fetchval(query, tenant_id)

    async def get_active_today(self, tenant_id: str) -> int:
        """Count users active today."""
        query = """
            SELECT COUNT(*) FROM users
            WHERE tenant_id = $1
              AND last_seen_at >= CURRENT_DATE
              AND is_active = TRUE
        """

        return await self._fetchval(query, tenant_id)
