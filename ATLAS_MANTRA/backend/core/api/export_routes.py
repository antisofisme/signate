"""
Export API Routes

REST API endpoints for exporting MANTRA documents to external platforms.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from enum import Enum

from ..export import (
    ExportTarget,
    ExportConfig,
    ExportResult,
    ConfluenceExporter,
    NotionExporter,
    GitHubWikiExporter,
)
from ..docs import DocumentGenerator, DocumentType

router = APIRouter(prefix="/api/v1/export", tags=["export"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ExportTargetEnum(str, Enum):
    """Export target platforms."""
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GITHUB_WIKI = "github_wiki"


class ExportRequest(BaseModel):
    """Request to export a document."""
    # Content source
    doc_type: Optional[str] = Field(None, description="Document type to generate and export")
    content: Optional[str] = Field(None, description="Direct markdown content to export")
    title: str = Field(..., description="Document title")

    # Target configuration
    target: ExportTargetEnum = Field(..., description="Export target platform")

    # Authentication (required based on target)
    api_key: Optional[str] = Field(None, description="API key (Notion)")
    api_token: Optional[str] = Field(None, description="API token (Confluence, GitHub)")

    # Confluence-specific
    confluence_base_url: Optional[str] = Field(None, description="Confluence base URL")
    confluence_email: Optional[str] = Field(None, description="Confluence user email")
    space_key: Optional[str] = Field(None, description="Confluence space key")

    # Notion-specific
    parent_page_id: Optional[str] = Field(None, description="Notion parent page ID")
    database_id: Optional[str] = Field(None, description="Notion database ID")

    # GitHub-specific
    repo_owner: Optional[str] = Field(None, description="GitHub repository owner")
    repo_name: Optional[str] = Field(None, description="GitHub repository name")

    # Document generation options (if using doc_type)
    domain_filter: Optional[str] = None
    scope_filter: Optional[str] = None
    max_decisions: int = 100


class ExportResponse(BaseModel):
    """Response from export operation."""
    success: bool
    target: str
    url: Optional[str] = None
    page_id: Optional[str] = None
    error: Optional[str] = None
    exported_at: str


class ValidateConfigRequest(BaseModel):
    """Request to validate export configuration."""
    target: ExportTargetEnum
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    confluence_base_url: Optional[str] = None
    confluence_email: Optional[str] = None
    space_key: Optional[str] = None
    parent_page_id: Optional[str] = None
    database_id: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None


class ValidateConfigResponse(BaseModel):
    """Response from configuration validation."""
    valid: bool
    error: Optional[str] = None


class ListPagesRequest(BaseModel):
    """Request to list pages from target."""
    target: ExportTargetEnum
    api_key: Optional[str] = None
    api_token: Optional[str] = None
    confluence_base_url: Optional[str] = None
    confluence_email: Optional[str] = None
    space_key: Optional[str] = None
    parent_page_id: Optional[str] = None
    database_id: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None


class PageInfo(BaseModel):
    """Information about a page in the target platform."""
    id: str
    title: str
    url: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


def _build_export_config(request: ExportRequest | ValidateConfigRequest | ListPagesRequest) -> ExportConfig:
    """Build ExportConfig from request."""
    target_map = {
        ExportTargetEnum.CONFLUENCE: ExportTarget.CONFLUENCE,
        ExportTargetEnum.NOTION: ExportTarget.NOTION,
        ExportTargetEnum.GITHUB_WIKI: ExportTarget.GITHUB_WIKI,
    }

    extra: dict[str, Any] = {}
    if hasattr(request, 'confluence_base_url') and request.confluence_base_url:
        extra["base_url"] = request.confluence_base_url
    if hasattr(request, 'confluence_email') and request.confluence_email:
        extra["email"] = request.confluence_email

    return ExportConfig(
        target=target_map[request.target],
        api_key=getattr(request, 'api_key', None),
        api_token=getattr(request, 'api_token', None),
        space_key=getattr(request, 'space_key', None),
        parent_page_id=getattr(request, 'parent_page_id', None),
        database_id=getattr(request, 'database_id', None),
        repo_owner=getattr(request, 'repo_owner', None),
        repo_name=getattr(request, 'repo_name', None),
        extra=extra,
    )


def _get_exporter(target: ExportTargetEnum):
    """Get the appropriate exporter for the target."""
    exporters = {
        ExportTargetEnum.CONFLUENCE: ConfluenceExporter,
        ExportTargetEnum.NOTION: NotionExporter,
        ExportTargetEnum.GITHUB_WIKI: GitHubWikiExporter,
    }
    return exporters[target]()


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/validate", response_model=ValidateConfigResponse)
async def validate_export_config(request: ValidateConfigRequest):
    """
    Validate export configuration for a target platform.

    Tests connection and authentication without creating any content.
    """
    exporter = _get_exporter(request.target)
    config = _build_export_config(request)

    is_valid, error = await exporter.validate_config(config)

    return ValidateConfigResponse(valid=is_valid, error=error)


@router.post("/", response_model=ExportResponse)
async def export_document(request: ExportRequest):
    """
    Export a document to an external platform.

    Either provide:
    - `content`: Direct markdown content to export
    - `doc_type`: Generate a document from MANTRA decisions first

    The document will be exported to the specified target platform
    (Confluence, Notion, or GitHub Wiki).
    """
    # Validate that we have content or can generate it
    if not request.content and not request.doc_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'content' or 'doc_type' is required"
        )

    content = request.content

    # Generate document if doc_type is specified
    if request.doc_type:
        try:
            doc_type = DocumentType(request.doc_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type: {request.doc_type}"
            )

        generator = DocumentGenerator()
        generated = generator.generate(
            doc_type=doc_type,
            decisions=[],  # Will be fetched based on filters
            title=request.title,
            domain_filter=request.domain_filter,
            scope_filter=request.scope_filter,
            max_decisions=request.max_decisions,
        )
        content = generated.content

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content to export"
        )

    # Build config and export
    exporter = _get_exporter(request.target)
    config = _build_export_config(request)

    result = await exporter.export_document(content, request.title, config)

    return ExportResponse(
        success=result.success,
        target=result.target.value,
        url=result.url,
        page_id=result.page_id,
        error=result.error,
        exported_at=result.exported_at.isoformat(),
    )


@router.put("/{page_id}", response_model=ExportResponse)
async def update_exported_document(page_id: str, request: ExportRequest):
    """
    Update an existing exported document.

    Requires the page_id from the original export.
    """
    if not request.content and not request.doc_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'content' or 'doc_type' is required"
        )

    content = request.content

    # Generate document if doc_type is specified
    if request.doc_type:
        try:
            doc_type = DocumentType(request.doc_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type: {request.doc_type}"
            )

        generator = DocumentGenerator()
        generated = generator.generate(
            doc_type=doc_type,
            decisions=[],
            title=request.title,
            domain_filter=request.domain_filter,
            scope_filter=request.scope_filter,
            max_decisions=request.max_decisions,
        )
        content = generated.content

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content to export"
        )

    exporter = _get_exporter(request.target)
    config = _build_export_config(request)

    result = await exporter.update_document(page_id, content, request.title, config)

    return ExportResponse(
        success=result.success,
        target=result.target.value,
        url=result.url,
        page_id=result.page_id,
        error=result.error,
        exported_at=result.exported_at.isoformat(),
    )


@router.delete("/{page_id}", response_model=ExportResponse)
async def delete_exported_document(
    page_id: str,
    target: ExportTargetEnum,
    api_key: Optional[str] = None,
    api_token: Optional[str] = None,
    confluence_base_url: Optional[str] = None,
    confluence_email: Optional[str] = None,
    space_key: Optional[str] = None,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
):
    """
    Delete an exported document from the target platform.

    Note: Some platforms (like Notion) archive instead of truly deleting.
    """
    # Build config manually from query params
    extra: dict[str, Any] = {}
    if confluence_base_url:
        extra["base_url"] = confluence_base_url
    if confluence_email:
        extra["email"] = confluence_email

    config = ExportConfig(
        target=ExportTarget(target.value),
        api_key=api_key,
        api_token=api_token,
        space_key=space_key,
        repo_owner=repo_owner,
        repo_name=repo_name,
        extra=extra,
    )

    exporter = _get_exporter(target)
    result = await exporter.delete_document(page_id, config)

    return ExportResponse(
        success=result.success,
        target=result.target.value,
        page_id=result.page_id,
        error=result.error,
        exported_at=result.exported_at.isoformat(),
    )


@router.post("/pages", response_model=list[PageInfo])
async def list_target_pages(request: ListPagesRequest):
    """
    List existing pages in the target platform.

    Useful for finding parent pages or seeing existing content.
    """
    exporter = _get_exporter(request.target)
    config = _build_export_config(request)

    pages = await exporter.list_pages(config, request.parent_page_id)

    return [
        PageInfo(
            id=page.get("id", ""),
            title=page.get("title", ""),
            url=page.get("url"),
        )
        for page in pages
    ]


@router.get("/targets")
async def list_export_targets():
    """
    List available export targets with their required configuration.
    """
    return {
        "targets": [
            {
                "id": "confluence",
                "name": "Atlassian Confluence",
                "required": ["api_token", "confluence_base_url", "confluence_email", "space_key"],
                "optional": ["parent_page_id"],
            },
            {
                "id": "notion",
                "name": "Notion",
                "required": ["api_key"],
                "optional": ["parent_page_id", "database_id"],
                "note": "Either parent_page_id or database_id is required",
            },
            {
                "id": "github_wiki",
                "name": "GitHub Wiki",
                "required": ["api_token", "repo_owner", "repo_name"],
                "note": "Wiki must be initialized on GitHub first",
            },
        ]
    }
