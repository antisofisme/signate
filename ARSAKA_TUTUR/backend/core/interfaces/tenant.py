"""
Tenant interfaces for multi-tenant management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from ..entities import TenantConfig, KnowledgeSourceConfig, Document


@dataclass
class SyncResult:
    """Result from knowledge source sync."""
    source_id: str
    status: str  # "success", "partial", "failed"
    documents_total: int = 0
    documents_processed: int = 0
    documents_failed: int = 0
    vectors_created: int = 0
    vectors_updated: int = 0
    vectors_deleted: int = 0
    error_message: Optional[str] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


class TenantRegistry(ABC):
    """
    Interface for tenant management.

    Implementations: PostgresTenantRegistry
    """

    @abstractmethod
    async def register(self, config: TenantConfig) -> str:
        """
        Register a new tenant.

        Args:
            config: TenantConfig with settings

        Returns:
            Tenant ID
        """
        pass

    @abstractmethod
    async def get_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """
        Get tenant configuration.

        Args:
            tenant_id: Tenant ID

        Returns:
            TenantConfig or None
        """
        pass

    @abstractmethod
    async def update_config(self, config: TenantConfig) -> bool:
        """
        Update tenant configuration.

        Args:
            config: TenantConfig with updates

        Returns:
            True if updated
        """
        pass

    @abstractmethod
    async def deactivate(self, tenant_id: str) -> bool:
        """
        Deactivate a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if deactivated
        """
        pass

    @abstractmethod
    async def list_tenants(
        self,
        active_only: bool = True
    ) -> List[TenantConfig]:
        """
        List all tenants.

        Args:
            active_only: Only active tenants

        Returns:
            List of TenantConfig
        """
        pass


class KnowledgeSource(ABC):
    """
    Interface for tenant knowledge sources.

    Implementations: DatabaseKnowledgeSource, APIKnowledgeSource, FileKnowledgeSource
    """

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Get source type (database, api, file)."""
        pass

    @abstractmethod
    async def connect(self, config: KnowledgeSourceConfig) -> bool:
        """
        Connect to knowledge source.

        Args:
            config: KnowledgeSourceConfig with connection details

        Returns:
            True if connected
        """
        pass

    @abstractmethod
    async def fetch_documents(
        self,
        config: KnowledgeSourceConfig,
        since: Optional[str] = None
    ) -> List[Document]:
        """
        Fetch documents from source.

        Args:
            config: KnowledgeSourceConfig
            since: Only documents modified since (ISO timestamp)

        Returns:
            List of Document
        """
        pass

    @abstractmethod
    async def sync(
        self,
        config: KnowledgeSourceConfig
    ) -> SyncResult:
        """
        Sync knowledge from source to vector store.

        Args:
            config: KnowledgeSourceConfig

        Returns:
            SyncResult with statistics
        """
        pass

    @abstractmethod
    async def test_connection(
        self,
        config: KnowledgeSourceConfig
    ) -> bool:
        """
        Test connection to knowledge source.

        Args:
            config: KnowledgeSourceConfig

        Returns:
            True if connection successful
        """
        pass
