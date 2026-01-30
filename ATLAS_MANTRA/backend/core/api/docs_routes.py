"""
Document Generation API Routes

Endpoints for generating documents from MANTRA decisions:
- List available document types
- Generate specific document type
- Get generation status
- Download generated documents

Per MANTRA LAW: Documents are READ-ONLY outputs from decisions.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ..docs import (
    DocumentType,
    AudienceType,
    OutputFormat,
    DocumentConfig,
    GeneratedDocument,
    generate_document,
    list_available_documents,
    get_document_meta,
    DOCUMENT_TYPES,
)
from ..repositories.decision_repository import DecisionRepository

logger = logging.getLogger(__name__)

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/docs", tags=["documents"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DocumentTypeInfo(BaseModel):
    """Information about a document type."""
    type: str
    name: str
    description: str
    phase: str
    primary_audience: str
    secondary_audiences: List[str]
    domains: List[str]
    tags: List[str]


class GenerateRequest(BaseModel):
    """Request to generate a document."""
    doc_type: str = Field(..., description="Document type (PRD, TECH_SPEC, etc.)")
    title: Optional[str] = Field(None, description="Custom title")
    version: str = Field("1.0.0", description="Document version")
    output_format: str = Field("MARKDOWN", description="Output format")

    # Filters
    scope_filter: Optional[str] = Field(None, description="Filter by scope path")
    domain_filter: Optional[str] = Field(None, description="Filter by domain")
    tag_filter: Optional[List[str]] = Field(None, description="Filter by tags")
    max_decisions: Optional[int] = Field(None, description="Max decisions to include")

    # Styling
    company_name: Optional[str] = Field(None, description="Company name for header")
    include_toc: bool = Field(True, description="Include table of contents")
    include_metadata: bool = Field(True, description="Include metadata header")


class GeneratedDocumentResponse(BaseModel):
    """Response with generated document."""
    doc_id: str
    doc_type: str
    title: str
    version: str
    output_format: str
    content: str
    word_count: int
    section_count: int
    decision_count: int
    generated_at: str
    source_decisions: List[str]


class DocumentStatsResponse(BaseModel):
    """Statistics about document generation."""
    total_document_types: int
    document_types_by_phase: Dict[str, int]
    document_types_by_audience: Dict[str, int]


# ============================================================================
# Dependencies
# ============================================================================

def get_repository():
    """Get decision repository."""
    from factory.container import Container
    return Container.get_decision_repository()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/types", response_model=List[DocumentTypeInfo])
async def list_document_types():
    """
    List all available document types.

    Returns information about each document type including:
    - Name and description
    - Target audience
    - Applicable domains and tags
    """
    types_info = []

    for doc_type, meta in DOCUMENT_TYPES.items():
        types_info.append(DocumentTypeInfo(
            type=doc_type.value,
            name=meta.name,
            description=meta.description,
            phase=meta.phase,
            primary_audience=meta.primary_audience.value,
            secondary_audiences=[a.value for a in meta.secondary_audiences],
            domains=meta.domains,
            tags=meta.tags,
        ))

    return types_info


@router.get("/types/{doc_type}", response_model=DocumentTypeInfo)
async def get_document_type(doc_type: str):
    """
    Get information about a specific document type.

    Args:
        doc_type: Document type identifier (e.g., PRD, TECH_SPEC)
    """
    try:
        dtype = DocumentType(doc_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {doc_type}. Valid types: {[t.value for t in DocumentType]}"
        )

    meta = DOCUMENT_TYPES.get(dtype)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"Document type {doc_type} not found in registry"
        )

    return DocumentTypeInfo(
        type=dtype.value,
        name=meta.name,
        description=meta.description,
        phase=meta.phase,
        primary_audience=meta.primary_audience.value,
        secondary_audiences=[a.value for a in meta.secondary_audiences],
        domains=meta.domains,
        tags=meta.tags,
    )


@router.post("/generate", response_model=GeneratedDocumentResponse)
async def generate_doc(
    request: GenerateRequest,
    repository: DecisionRepository = Depends(get_repository),
):
    """
    Generate a document from decisions.

    Args:
        request: Generation configuration

    Returns:
        Generated document with content
    """
    # Validate document type
    try:
        doc_type = DocumentType(request.doc_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {request.doc_type}"
        )

    # Validate output format
    try:
        output_format = OutputFormat(request.output_format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: {request.output_format}"
        )

    # Load decisions from repository
    try:
        stored_decisions = await repository.find_all_async(
            limit=request.max_decisions or 1000,
            offset=0
        )

        # Convert to dict format for generators
        decisions = []
        for sd in stored_decisions:
            d = sd.decision
            decisions.append({
                "decision_id": d.decision_id,
                "code": d.decision_code,
                "domain_id": d.domain_id.value if hasattr(d.domain_id, 'value') else d.domain_id,
                "aspect_id": d.aspect_id.value if hasattr(d.aspect_id, 'value') else d.aspect_id,
                "version": d.version,
                "statement": d.statement,
                "rationale": d.rationale,
                "constraints": [
                    {"id": c.constraint_id, "type": c.type.value, "rule": c.statement}
                    for c in (d.constraints or [])
                ],
                "invariants": d.invariants or [],
                "tags": d.tags or [],
                "impact": d.blast_radius.value if hasattr(d.blast_radius, 'value') else "IMPORTANT",
                "summary": d.statement[:100] if d.statement else "",
                "scope_path": getattr(d, 'scope_path', '*'),
                "depends_on": d.related_decisions or [],
                "authored_by": getattr(d, 'created_by', 'system'),
            })

    except Exception as e:
        logger.error(f"Failed to load decisions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load decisions: {str(e)}"
        )

    if not decisions:
        raise HTTPException(
            status_code=404,
            detail="No decisions found to generate document from"
        )

    # Build config
    config = DocumentConfig(
        doc_type=doc_type,
        title=request.title,
        version=request.version,
        output_format=output_format,
        scope_filter=request.scope_filter,
        domain_filter=request.domain_filter,
        tag_filter=request.tag_filter,
        max_decisions=request.max_decisions,
        company_name=request.company_name,
        include_toc=request.include_toc,
        include_metadata=request.include_metadata,
    )

    # Generate document
    try:
        doc = generate_document(doc_type, decisions, config)
    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Document generation failed: {str(e)}"
        )

    return GeneratedDocumentResponse(
        doc_id=doc.doc_id,
        doc_type=doc.doc_type.value,
        title=doc.title,
        version=doc.version,
        output_format=doc.output_format.value,
        content=doc.raw_content,
        word_count=doc.word_count,
        section_count=doc.section_count,
        decision_count=doc.decision_count,
        generated_at=doc.generated_at.isoformat(),
        source_decisions=doc.source_decisions,
    )


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats():
    """
    Get statistics about document generation capabilities.
    """
    by_phase: Dict[str, int] = {}
    by_audience: Dict[str, int] = {}

    for meta in DOCUMENT_TYPES.values():
        phase = meta.phase
        by_phase[phase] = by_phase.get(phase, 0) + 1

        audience = meta.primary_audience.value
        by_audience[audience] = by_audience.get(audience, 0) + 1

    return DocumentStatsResponse(
        total_document_types=len(DOCUMENT_TYPES),
        document_types_by_phase=by_phase,
        document_types_by_audience=by_audience,
    )


@router.get("/preview/{doc_type}")
async def preview_document_structure(
    doc_type: str,
    scope_filter: Optional[str] = Query(None, description="Filter by scope"),
    domain_filter: Optional[str] = Query(None, description="Filter by domain"),
):
    """
    Preview what a document would contain (without generating).

    Returns metadata about the document structure.
    """
    try:
        dtype = DocumentType(doc_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type: {doc_type}"
        )

    meta = DOCUMENT_TYPES.get(dtype)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"Document type {doc_type} not configured"
        )

    return {
        "doc_type": doc_type,
        "name": meta.name,
        "phase": meta.phase,
        "audience": meta.primary_audience.value,
        "will_include": {
            "rationale": meta.include_rationale,
            "constraints": meta.include_constraints,
            "examples": meta.include_examples,
        },
        "filters": {
            "domains": meta.domains if scope_filter is None else [domain_filter] if domain_filter else meta.domains,
            "scopes": meta.scopes if scope_filter is None else [scope_filter],
            "tags": meta.tags,
        },
        "simplified_language": meta.simplify_language,
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = ["router"]
