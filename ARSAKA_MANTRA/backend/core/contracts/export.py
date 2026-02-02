"""
Export Module Contract

Defines the interface for document generation and integrations.
Teams implementing export must conform to this contract.

Owner: Docs & Export Team
Dependencies: Domain models (read-only)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, BinaryIO
from enum import Enum


# =============================================================================
# DATA TRANSFER OBJECTS
# =============================================================================

class ExportFormat(str, Enum):
    """Export format options."""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    YAML = "yaml"


class DocumentType(str, Enum):
    """Type of document to generate."""
    ADR = "adr"                     # Architecture Decision Record
    DECISION_LOG = "decision_log"  # Decision changelog
    SUMMARY = "summary"            # Executive summary
    FULL_SPEC = "full_spec"        # Full specification
    COMPLIANCE = "compliance"       # Compliance report
    MATRIX = "matrix"              # Decision matrix view


class IntegrationType(str, Enum):
    """External integration type."""
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GITHUB = "github"
    GITLAB = "gitlab"
    JIRA = "jira"


@dataclass
class ExportRequest:
    """Request to export decisions."""
    # What to export
    decision_ids: Optional[List[str]] = None  # Specific decisions
    domain_ids: Optional[List[str]] = None    # All in domains
    query: Optional[str] = None               # Search-based export
    # How to export
    format: ExportFormat = ExportFormat.MARKDOWN
    document_type: DocumentType = DocumentType.ADR
    # Options
    include_rationale: bool = True
    include_constraints: bool = True
    include_dependencies: bool = False
    include_metadata: bool = False
    # Metadata
    user_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class ExportResult:
    """Result of export operation."""
    success: bool
    request_id: str
    format: ExportFormat
    document_type: DocumentType
    # Content
    content: Optional[str] = None          # Text content (markdown, html, etc.)
    binary_content: Optional[bytes] = None # Binary content (pdf)
    # Metadata
    decisions_exported: int = 0
    export_time_ms: float = 0.0
    generated_at: datetime = field(default_factory=datetime.utcnow)
    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "request_id": self.request_id,
            "format": self.format.value,
            "document_type": self.document_type.value,
            "content": self.content,
            "has_binary": self.binary_content is not None,
            "decisions_exported": self.decisions_exported,
            "export_time_ms": self.export_time_ms,
            "generated_at": self.generated_at.isoformat(),
            "errors": self.errors,
            "warnings": self.warnings,
        }


@dataclass
class IntegrationRequest:
    """Request to sync with external system."""
    integration_type: IntegrationType
    # What to sync
    decision_ids: Optional[List[str]] = None
    domain_ids: Optional[List[str]] = None
    # Where to sync
    target_space: Optional[str] = None     # Confluence space, Notion database, etc.
    target_path: Optional[str] = None      # Path within target
    # Options
    create_if_missing: bool = True
    update_existing: bool = True
    # Credentials (should be from env/secrets in production)
    credentials: Optional[Dict[str, str]] = None


@dataclass
class IntegrationResult:
    """Result of integration operation."""
    success: bool
    integration_type: IntegrationType
    # Results
    created: List[str] = field(default_factory=list)   # IDs of created items
    updated: List[str] = field(default_factory=list)   # IDs of updated items
    skipped: List[str] = field(default_factory=list)   # IDs of skipped items
    failed: List[str] = field(default_factory=list)    # IDs of failed items
    # External references
    external_urls: Dict[str, str] = field(default_factory=dict)  # decision_id -> url
    # Errors
    errors: List[str] = field(default_factory=list)
    sync_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "integration_type": self.integration_type.value,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "external_urls": self.external_urls,
            "errors": self.errors,
            "sync_time_ms": self.sync_time_ms,
        }


# =============================================================================
# DOCUMENT GENERATOR CONTRACT
# =============================================================================

class DocumentGeneratorContract(ABC):
    """
    Document Generator Contract

    Responsibilities:
    - Generate various document types from decisions
    - Support multiple output formats
    - Handle templates and styling
    """

    @abstractmethod
    async def generate(
        self,
        decisions: List[Dict[str, Any]],
        document_type: DocumentType,
        format: ExportFormat,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate document from decisions.

        Args:
            decisions: List of decision records
            document_type: Type of document to generate
            format: Output format
            options: Generation options

        Returns:
            Generated document content
        """
        pass

    @abstractmethod
    async def generate_adr(
        self,
        decision: Dict[str, Any],
        format: ExportFormat = ExportFormat.MARKDOWN,
    ) -> str:
        """
        Generate Architecture Decision Record for a single decision.

        Args:
            decision: Decision record
            format: Output format

        Returns:
            ADR content
        """
        pass

    @abstractmethod
    async def generate_matrix(
        self,
        decisions: List[Dict[str, Any]],
        group_by: str = "domain_id",
        format: ExportFormat = ExportFormat.MARKDOWN,
    ) -> str:
        """
        Generate decision matrix view.

        Args:
            decisions: List of decisions
            group_by: How to group (domain_id, aspect_id, impact)
            format: Output format

        Returns:
            Matrix content
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[ExportFormat]:
        """Get list of supported export formats."""
        pass

    @abstractmethod
    def get_supported_types(self) -> List[DocumentType]:
        """Get list of supported document types."""
        pass


# =============================================================================
# INTEGRATION ADAPTER CONTRACT
# =============================================================================

class IntegrationAdapterContract(ABC):
    """
    Integration Adapter Contract

    Responsibilities:
    - Sync decisions to external systems
    - Handle authentication and API calls
    - Map decision format to external format
    """

    @property
    @abstractmethod
    def integration_type(self) -> IntegrationType:
        """Get the integration type this adapter handles."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to external system.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def sync(
        self,
        decisions: List[Dict[str, Any]],
        target: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> IntegrationResult:
        """
        Sync decisions to external system.

        Args:
            decisions: Decisions to sync
            target: Target location (space, database, repo)
            options: Sync options

        Returns:
            IntegrationResult with sync details
        """
        pass

    @abstractmethod
    async def get_existing(
        self,
        target: str,
    ) -> Dict[str, str]:
        """
        Get existing decision mappings in external system.

        Args:
            target: Target location

        Returns:
            Dict mapping decision_id to external_id
        """
        pass


# =============================================================================
# EXPORT CONTRACT
# =============================================================================

class ExportContract(ABC):
    """
    Export Contract

    Orchestrates document generation and integrations.

    Usage:
        exporter = ExportService()

        # Generate document
        result = await exporter.export(request)
        print(result.content)

        # Sync to Confluence
        sync_result = await exporter.sync_to_integration(
            integration_type=IntegrationType.CONFLUENCE,
            decision_ids=["uuid1", "uuid2"],
            target_space="ARCH",
        )
    """

    @property
    @abstractmethod
    def document_generator(self) -> DocumentGeneratorContract:
        """Get document generator component."""
        pass

    @abstractmethod
    async def export(self, request: ExportRequest) -> ExportResult:
        """
        Export decisions based on request.

        Args:
            request: ExportRequest with options

        Returns:
            ExportResult with content or binary
        """
        pass

    @abstractmethod
    async def export_to_file(
        self,
        request: ExportRequest,
        file_path: str,
    ) -> ExportResult:
        """
        Export decisions directly to a file.

        Args:
            request: ExportRequest with options
            file_path: Path to write file

        Returns:
            ExportResult (content will be None, written to file)
        """
        pass

    @abstractmethod
    async def sync_to_integration(
        self,
        integration_type: IntegrationType,
        decision_ids: Optional[List[str]] = None,
        domain_ids: Optional[List[str]] = None,
        target: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> IntegrationResult:
        """
        Sync decisions to external integration.

        Args:
            integration_type: Which integration to use
            decision_ids: Specific decisions (or all if None)
            domain_ids: Filter by domains
            target: Target location in external system
            options: Integration-specific options

        Returns:
            IntegrationResult with sync details
        """
        pass

    @abstractmethod
    def get_supported_integrations(self) -> List[IntegrationType]:
        """Get list of available integrations."""
        pass


__all__ = [
    "ExportFormat",
    "DocumentType",
    "IntegrationType",
    "ExportRequest",
    "ExportResult",
    "IntegrationRequest",
    "IntegrationResult",
    "DocumentGeneratorContract",
    "IntegrationAdapterContract",
    "ExportContract",
]
