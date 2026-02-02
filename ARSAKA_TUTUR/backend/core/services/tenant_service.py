"""
Tenant Service - Tenant configuration management.
"""

from typing import Optional, List

from ..entities import TenantConfig
from ..interfaces import TenantRegistry
from ...shared.logging import get_logger
from ...shared.exceptions import TenantNotFoundError

logger = get_logger(__name__)


class TenantService:
    """
    Service for tenant operations.

    Handles tenant registration, configuration, and validation.
    """

    def __init__(self, registry: TenantRegistry):
        self.registry = registry
        self._cache: dict = {}  # Simple in-memory cache

    async def get_tenant(self, tenant_id: str) -> TenantConfig:
        """
        Get tenant configuration.

        Args:
            tenant_id: Tenant ID

        Returns:
            TenantConfig

        Raises:
            TenantNotFoundError: If tenant not found or inactive
        """
        # Check cache first
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        config = await self.registry.get_config(tenant_id)
        if not config or not config.is_active:
            raise TenantNotFoundError(tenant_id)

        # Cache for future requests
        self._cache[tenant_id] = config
        return config

    async def validate_tenant(self, tenant_id: str) -> bool:
        """
        Validate tenant exists and is active.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if valid
        """
        try:
            await self.get_tenant(tenant_id)
            return True
        except TenantNotFoundError:
            return False

    async def register_tenant(self, config: TenantConfig) -> str:
        """
        Register a new tenant.

        Args:
            config: TenantConfig with settings

        Returns:
            Tenant ID
        """
        tenant_id = await self.registry.register(config)
        logger.info(f"Registered tenant: {tenant_id}")
        return tenant_id

    async def update_tenant(self, config: TenantConfig) -> bool:
        """
        Update tenant configuration.

        Args:
            config: TenantConfig with updates

        Returns:
            True if updated
        """
        # Invalidate cache
        if config.id in self._cache:
            del self._cache[config.id]

        result = await self.registry.update_config(config)
        if result:
            logger.info(f"Updated tenant: {config.id}")
        return result

    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """
        Deactivate a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if deactivated
        """
        # Invalidate cache
        if tenant_id in self._cache:
            del self._cache[tenant_id]

        result = await self.registry.deactivate(tenant_id)
        if result:
            logger.info(f"Deactivated tenant: {tenant_id}")
        return result

    async def list_tenants(self, active_only: bool = True) -> List[TenantConfig]:
        """
        List all tenants.

        Args:
            active_only: Only active tenants

        Returns:
            List of TenantConfig
        """
        return await self.registry.list_tenants(active_only)

    def clear_cache(self, tenant_id: Optional[str] = None) -> None:
        """
        Clear tenant cache.

        Args:
            tenant_id: Specific tenant to clear, or all if None
        """
        if tenant_id:
            if tenant_id in self._cache:
                del self._cache[tenant_id]
        else:
            self._cache.clear()
