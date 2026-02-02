"""
List API Keys Use Case

Lists API keys for a tenant with pagination.
Does not return sensitive data (hashes).

Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from ..interfaces.api_key_repository import IApiKeyRepository
from ..domain.api_key import ApiKey


@dataclass
class ApiKeyInfo:
    """API key info (without sensitive data)."""
    key_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    key_prefix: str  # For display (e.g., "pk_live_a1b2")
    environment: str
    scopes: List[str]
    status: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    usage_count: int
    created_at: str
    created_by_user_id: str


@dataclass
class ListApiKeysRequest:
    """List API keys request."""
    tenant_id: UUID
    include_revoked: bool = False
    limit: int = 50
    offset: int = 0


@dataclass
class ListApiKeysResult:
    """List API keys result."""
    api_keys: List[ApiKeyInfo]
    total: int
    limit: int
    offset: int
    has_more: bool


class ListApiKeysUseCase:
    """List API keys for a tenant."""

    def __init__(self, api_key_repo: IApiKeyRepository):
        self._repo = api_key_repo

    async def execute(self, request: ListApiKeysRequest) -> ListApiKeysResult:
        """Execute list API keys.

        Args:
            request: List request with filters

        Returns:
            ListApiKeysResult with API key infos (no secrets)
        """
        # 1. Fetch keys
        api_keys = await self._repo.list_by_tenant(
            tenant_id=request.tenant_id,
            include_revoked=request.include_revoked,
            limit=request.limit + 1,  # Fetch one extra to check has_more
            offset=request.offset,
        )

        # 2. Check if there are more
        has_more = len(api_keys) > request.limit
        if has_more:
            api_keys = api_keys[:request.limit]

        # 3. Get total count
        total = await self._repo.count_by_tenant(request.tenant_id)
        if request.include_revoked:
            # Count all including revoked
            total = len(api_keys) + request.offset + (1 if has_more else 0)

        # 4. Convert to result
        key_infos = [self._to_info(key) for key in api_keys]

        return ListApiKeysResult(
            api_keys=key_infos,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
        )

    def _to_info(self, api_key: ApiKey) -> ApiKeyInfo:
        """Convert API key to info (without sensitive data)."""
        return ApiKeyInfo(
            key_id=str(api_key.key_id),
            tenant_id=str(api_key.tenant_id),
            name=api_key.name,
            description=api_key.description,
            key_prefix=api_key.key_prefix,
            environment=api_key.environment.value,
            scopes=api_key.scopes,
            status=api_key.status.value,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            usage_count=api_key.usage_count,
            created_at=api_key.created_at.isoformat(),
            created_by_user_id=str(api_key.created_by_user_id),
        )


class GetApiKeyUseCase:
    """Get single API key by ID."""

    def __init__(self, api_key_repo: IApiKeyRepository):
        self._repo = api_key_repo

    async def execute(
        self,
        key_id: UUID,
        tenant_id: UUID,
    ) -> Optional[ApiKeyInfo]:
        """Get API key by ID.

        Args:
            key_id: API key UUID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            ApiKeyInfo if found and belongs to tenant, None otherwise
        """
        api_key = await self._repo.get_by_id(key_id)

        if not api_key:
            return None

        # Verify tenant ownership
        if api_key.tenant_id != tenant_id:
            return None

        return ApiKeyInfo(
            key_id=str(api_key.key_id),
            tenant_id=str(api_key.tenant_id),
            name=api_key.name,
            description=api_key.description,
            key_prefix=api_key.key_prefix,
            environment=api_key.environment.value,
            scopes=api_key.scopes,
            status=api_key.status.value,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            usage_count=api_key.usage_count,
            created_at=api_key.created_at.isoformat(),
            created_by_user_id=str(api_key.created_by_user_id),
        )
