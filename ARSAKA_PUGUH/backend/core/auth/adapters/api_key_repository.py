"""
PostgreSQL API Key Repository

Implementation of IApiKeyRepository for PostgreSQL database.
Handles all API key CRUD operations.

Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..interfaces.api_key_repository import IApiKeyRepository
from ..domain.api_key import ApiKey, ApiKeyStatus, ApiKeyEnvironment


class PostgresApiKeyRepository(IApiKeyRepository):
    """PostgreSQL implementation of API key repository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: Async database session
        """
        self._session = session

    async def create(self, api_key: ApiKey) -> ApiKey:
        """Create a new API key."""
        await self._session.execute(
            text("""
                INSERT INTO api_keys (
                    key_id, tenant_id, created_by_user_id,
                    key_prefix, key_hash, name, description,
                    environment, scopes, status,
                    expires_at, created_at, updated_at
                ) VALUES (
                    :key_id, :tenant_id, :created_by_user_id,
                    :key_prefix, :key_hash, :name, :description,
                    :environment, :scopes, :status,
                    :expires_at, :created_at, :updated_at
                )
            """),
            {
                "key_id": str(api_key.key_id),
                "tenant_id": str(api_key.tenant_id),
                "created_by_user_id": str(api_key.created_by_user_id),
                "key_prefix": api_key.key_prefix,
                "key_hash": api_key.key_hash,
                "name": api_key.name,
                "description": api_key.description,
                "environment": api_key.environment.value,
                "scopes": api_key.scopes,  # PostgreSQL array
                "status": api_key.status.value,
                "expires_at": api_key.expires_at,
                "created_at": api_key.created_at,
                "updated_at": api_key.updated_at,
            }
        )
        await self._session.commit()

        return api_key

    async def get_by_id(self, key_id: UUID) -> Optional[ApiKey]:
        """Get API key by ID."""
        result = await self._session.execute(
            text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE key_id = :key_id
            """),
            {"key_id": str(key_id)}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_api_key(row)

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        """Get API key by hash (for validation)."""
        result = await self._session.execute(
            text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE key_hash = :key_hash
            """),
            {"key_hash": key_hash}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_api_key(row)

    async def get_by_prefix(self, key_prefix: str) -> Optional[ApiKey]:
        """Get API key by prefix."""
        result = await self._session.execute(
            text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE key_prefix = :key_prefix
            """),
            {"key_prefix": key_prefix}
        )
        row = result.fetchone()

        if not row:
            return None

        return self._row_to_api_key(row)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_revoked: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ApiKey]:
        """List API keys for a tenant."""
        if include_revoked:
            query = text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)
        else:
            query = text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE tenant_id = :tenant_id
                  AND status = 'active'
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

        result = await self._session.execute(
            query,
            {
                "tenant_id": str(tenant_id),
                "limit": limit,
                "offset": offset,
            }
        )
        rows = result.fetchall()

        return [self._row_to_api_key(row) for row in rows]

    async def list_by_user(
        self,
        user_id: UUID,
        include_revoked: bool = False,
    ) -> List[ApiKey]:
        """List API keys created by a user."""
        if include_revoked:
            query = text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE created_by_user_id = :user_id
                ORDER BY created_at DESC
            """)
        else:
            query = text("""
                SELECT key_id, tenant_id, created_by_user_id,
                       key_prefix, key_hash, name, description,
                       environment, scopes, status,
                       revoked_at, revoked_by_user_id,
                       expires_at, last_used_at, last_used_ip,
                       usage_count, created_at, updated_at
                FROM api_keys
                WHERE created_by_user_id = :user_id
                  AND status = 'active'
                ORDER BY created_at DESC
            """)

        result = await self._session.execute(
            query,
            {"user_id": str(user_id)}
        )
        rows = result.fetchall()

        return [self._row_to_api_key(row) for row in rows]

    async def update(self, api_key: ApiKey) -> ApiKey:
        """Update API key."""
        await self._session.execute(
            text("""
                UPDATE api_keys SET
                    name = :name,
                    description = :description,
                    scopes = :scopes,
                    updated_at = :updated_at
                WHERE key_id = :key_id
            """),
            {
                "key_id": str(api_key.key_id),
                "name": api_key.name,
                "description": api_key.description,
                "scopes": api_key.scopes,
                "updated_at": datetime.utcnow(),
            }
        )
        await self._session.commit()

        return api_key

    async def update_usage(
        self,
        key_id: UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Update API key usage statistics."""
        await self._session.execute(
            text("""
                UPDATE api_keys SET
                    last_used_at = NOW(),
                    last_used_ip = :ip_address,
                    usage_count = usage_count + 1,
                    updated_at = NOW()
                WHERE key_id = :key_id
            """),
            {
                "key_id": str(key_id),
                "ip_address": ip_address,
            }
        )
        await self._session.commit()

    async def revoke(
        self,
        key_id: UUID,
        revoked_by_user_id: UUID,
    ) -> None:
        """Revoke an API key."""
        await self._session.execute(
            text("""
                UPDATE api_keys SET
                    status = 'revoked',
                    revoked_at = NOW(),
                    revoked_by_user_id = :revoked_by_user_id,
                    updated_at = NOW()
                WHERE key_id = :key_id
            """),
            {
                "key_id": str(key_id),
                "revoked_by_user_id": str(revoked_by_user_id),
            }
        )
        await self._session.commit()

    async def delete(self, key_id: UUID) -> None:
        """Permanently delete an API key."""
        await self._session.execute(
            text("DELETE FROM api_keys WHERE key_id = :key_id"),
            {"key_id": str(key_id)}
        )
        await self._session.commit()

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count active API keys for a tenant."""
        result = await self._session.execute(
            text("""
                SELECT COUNT(*) FROM api_keys
                WHERE tenant_id = :tenant_id
                  AND status = 'active'
            """),
            {"tenant_id": str(tenant_id)}
        )
        count = result.scalar()
        return count or 0

    def _row_to_api_key(self, row) -> ApiKey:
        """Convert database row to ApiKey entity."""
        return ApiKey(
            key_id=UUID(str(row.key_id)),
            tenant_id=UUID(str(row.tenant_id)),
            created_by_user_id=UUID(str(row.created_by_user_id)),
            key_prefix=row.key_prefix,
            key_hash=row.key_hash,
            name=row.name,
            description=row.description,
            environment=ApiKeyEnvironment(row.environment),
            scopes=list(row.scopes) if row.scopes else [],
            status=ApiKeyStatus(row.status),
            revoked_at=row.revoked_at,
            revoked_by_user_id=UUID(str(row.revoked_by_user_id)) if row.revoked_by_user_id else None,
            expires_at=row.expires_at,
            last_used_at=row.last_used_at,
            last_used_ip=row.last_used_ip,
            usage_count=row.usage_count or 0,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
