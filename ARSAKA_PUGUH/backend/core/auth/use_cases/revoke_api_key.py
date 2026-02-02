"""
Revoke API Key Use Case

Revokes an API key, making it permanently unusable.
Prefer revocation over deletion for audit trail.

Source: SDK_INTEGRATION_GUIDE.md - Service Account Authentication
"""

from dataclasses import dataclass
from uuid import UUID

from ..interfaces.api_key_repository import IApiKeyRepository
from ..exceptions import ApiKeyNotFoundError, ValidationError


@dataclass
class RevokeApiKeyRequest:
    """Revoke API key request."""
    key_id: UUID
    tenant_id: UUID  # For authorization
    revoked_by_user_id: UUID


@dataclass
class RevokeApiKeyResult:
    """Revoke API key result."""
    key_id: str
    name: str
    revoked: bool
    message: str


class RevokeApiKeyUseCase:
    """Revoke an API key."""

    def __init__(
        self,
        api_key_repo: IApiKeyRepository,
        event_bus=None,
    ):
        self._repo = api_key_repo
        self._events = event_bus

    async def execute(self, request: RevokeApiKeyRequest) -> RevokeApiKeyResult:
        """Execute revoke API key.

        Args:
            request: Revoke request

        Returns:
            RevokeApiKeyResult

        Raises:
            ApiKeyNotFoundError: If key not found or not owned by tenant
        """
        # 1. Get the API key
        api_key = await self._repo.get_by_id(request.key_id)

        if not api_key:
            raise ApiKeyNotFoundError(str(request.key_id))

        # 2. Verify tenant ownership
        if api_key.tenant_id != request.tenant_id:
            raise ApiKeyNotFoundError(str(request.key_id))

        # 3. Check if already revoked
        if api_key.status.value == "revoked":
            return RevokeApiKeyResult(
                key_id=str(api_key.key_id),
                name=api_key.name,
                revoked=True,
                message="API key was already revoked",
            )

        # 4. Revoke the key
        await self._repo.revoke(
            key_id=request.key_id,
            revoked_by_user_id=request.revoked_by_user_id,
        )

        return RevokeApiKeyResult(
            key_id=str(api_key.key_id),
            name=api_key.name,
            revoked=True,
            message="API key has been revoked successfully",
        )


class DeleteApiKeyUseCase:
    """Permanently delete an API key.

    WARNING: This removes the key from the database.
    Prefer RevokeApiKeyUseCase for audit trail.
    """

    def __init__(
        self,
        api_key_repo: IApiKeyRepository,
        event_bus=None,
    ):
        self._repo = api_key_repo
        self._events = event_bus

    async def execute(
        self,
        key_id: UUID,
        tenant_id: UUID,
    ) -> bool:
        """Delete API key permanently.

        Args:
            key_id: API key UUID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            True if deleted, False if not found

        Raises:
            ApiKeyNotFoundError: If key not found or not owned by tenant
        """
        # 1. Get the API key
        api_key = await self._repo.get_by_id(key_id)

        if not api_key:
            raise ApiKeyNotFoundError(str(key_id))

        # 2. Verify tenant ownership
        if api_key.tenant_id != tenant_id:
            raise ApiKeyNotFoundError(str(key_id))

        # 3. Delete the key
        await self._repo.delete(key_id)

        return True
