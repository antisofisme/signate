"""
API Key Repository Interface

Abstract contract for API key data access.
Implementations handle actual database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..domain.api_key import ApiKey


class IApiKeyRepository(ABC):
    """Interface for API key data access."""

    @abstractmethod
    async def create(self, api_key: ApiKey) -> ApiKey:
        """
        Create a new API key.

        Args:
            api_key: ApiKey entity to create

        Returns:
            Created API key
        """
        pass

    @abstractmethod
    async def get_by_id(self, key_id: UUID) -> Optional[ApiKey]:
        """
        Get API key by ID.

        Args:
            key_id: API key UUID

        Returns:
            ApiKey if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        """
        Get API key by hash (for validation).

        Args:
            key_hash: SHA-256 hash of the full key

        Returns:
            ApiKey if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_prefix(self, key_prefix: str) -> Optional[ApiKey]:
        """
        Get API key by prefix.

        Args:
            key_prefix: Key prefix (first 12 chars)

        Returns:
            ApiKey if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        include_revoked: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ApiKey]:
        """
        List API keys for a tenant.

        Args:
            tenant_id: Tenant UUID
            include_revoked: Include revoked keys
            limit: Max results
            offset: Pagination offset

        Returns:
            List of API keys
        """
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UUID,
        include_revoked: bool = False,
    ) -> List[ApiKey]:
        """
        List API keys created by a user.

        Args:
            user_id: User UUID
            include_revoked: Include revoked keys

        Returns:
            List of API keys
        """
        pass

    @abstractmethod
    async def update(self, api_key: ApiKey) -> ApiKey:
        """
        Update API key.

        Args:
            api_key: ApiKey entity with updated fields

        Returns:
            Updated API key
        """
        pass

    @abstractmethod
    async def update_usage(
        self,
        key_id: UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Update API key usage statistics.

        Args:
            key_id: API key UUID
            ip_address: Client IP address
        """
        pass

    @abstractmethod
    async def revoke(
        self,
        key_id: UUID,
        revoked_by_user_id: UUID,
    ) -> None:
        """
        Revoke an API key.

        Args:
            key_id: API key UUID
            revoked_by_user_id: User performing revocation
        """
        pass

    @abstractmethod
    async def delete(self, key_id: UUID) -> None:
        """
        Permanently delete an API key.

        Note: Usually prefer revoke over delete for audit trail.

        Args:
            key_id: API key UUID
        """
        pass

    @abstractmethod
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """
        Count active API keys for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Count of active keys
        """
        pass
