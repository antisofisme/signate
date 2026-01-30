"""
Export Base Protocol

Defines the interface for all export integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Protocol


class ExportTarget(str, Enum):
    """Supported export targets."""
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GITHUB_WIKI = "github_wiki"


@dataclass
class ExportConfig:
    """Configuration for an export operation."""
    target: ExportTarget
    # Authentication
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    oauth_token: Optional[str] = None
    # Target-specific settings
    space_key: Optional[str] = None  # Confluence space
    database_id: Optional[str] = None  # Notion database
    repo_owner: Optional[str] = None  # GitHub owner
    repo_name: Optional[str] = None  # GitHub repo
    # Content settings
    parent_page_id: Optional[str] = None
    create_toc: bool = True
    include_metadata: bool = True
    # Extra options
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    target: ExportTarget
    url: Optional[str] = None
    page_id: Optional[str] = None
    error: Optional[str] = None
    exported_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


class ExporterProtocol(Protocol):
    """Protocol for export integrations."""

    async def validate_config(self, config: ExportConfig) -> tuple[bool, Optional[str]]:
        """
        Validate the export configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...

    async def export_document(
        self,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """
        Export a document to the target platform.

        Args:
            content: Markdown content to export
            title: Document title
            config: Export configuration

        Returns:
            ExportResult with success status and URL
        """
        ...

    async def update_document(
        self,
        page_id: str,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """
        Update an existing document.

        Args:
            page_id: ID of the page to update
            content: New markdown content
            title: New title
            config: Export configuration

        Returns:
            ExportResult with success status
        """
        ...

    async def delete_document(
        self,
        page_id: str,
        config: ExportConfig,
    ) -> ExportResult:
        """
        Delete a document from the target platform.

        Args:
            page_id: ID of the page to delete
            config: Export configuration

        Returns:
            ExportResult with success status
        """
        ...

    async def list_pages(
        self,
        config: ExportConfig,
        parent_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        List pages in the target location.

        Args:
            config: Export configuration
            parent_id: Optional parent page ID

        Returns:
            List of page info dictionaries
        """
        ...


class BaseExporter(ABC):
    """Base class for exporters with common functionality."""

    def __init__(self):
        self._session = None

    @abstractmethod
    async def validate_config(self, config: ExportConfig) -> tuple[bool, Optional[str]]:
        """Validate configuration."""
        pass

    @abstractmethod
    async def export_document(
        self,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Export document."""
        pass

    @abstractmethod
    async def update_document(
        self,
        page_id: str,
        content: str,
        title: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Update document."""
        pass

    @abstractmethod
    async def delete_document(
        self,
        page_id: str,
        config: ExportConfig,
    ) -> ExportResult:
        """Delete document."""
        pass

    @abstractmethod
    async def list_pages(
        self,
        config: ExportConfig,
        parent_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """List pages."""
        pass

    def _convert_markdown_to_target_format(self, markdown: str, target: ExportTarget) -> str:
        """
        Convert markdown to target-specific format.

        This is a basic implementation - override in subclasses for better conversion.
        """
        # Basic conversion - most platforms accept markdown or have converters
        return markdown

    def _create_error_result(self, target: ExportTarget, error: str) -> ExportResult:
        """Create an error result."""
        return ExportResult(
            success=False,
            target=target,
            error=error,
        )
