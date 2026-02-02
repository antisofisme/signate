"""
Knowledge Management API Routes.

Endpoints for managing the knowledge base (documents, embeddings).
"""

from typing import Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies.context import get_request_context
from ...core.entities import RequestContext, Document, Chunk
from ...container import get_container
from ...shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# =========================================================================
# Request/Response Schemas
# =========================================================================

class ChunkInput(BaseModel):
    """Single chunk input."""
    content: str = Field(..., min_length=1, max_length=10000)
    chunk_index: int = Field(0, ge=0)
    metadata: dict = Field(default_factory=dict)


class IndexDocumentRequest(BaseModel):
    """Request to index a document."""
    title: str = Field(..., min_length=1, max_length=500)
    source: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = Field(None, description="Full content to auto-chunk")
    chunks: Optional[List[ChunkInput]] = Field(None, description="Pre-chunked content")
    metadata: dict = Field(default_factory=dict)

    # Chunking config (if content provided)
    chunk_size: int = Field(500, ge=100, le=2000)
    chunk_overlap: int = Field(50, ge=0, le=500)


class IndexDocumentResponse(BaseModel):
    """Response after indexing."""
    success: bool = True
    data: dict = Field(default_factory=dict)


class DeleteDocumentRequest(BaseModel):
    """Request to delete a document."""
    document_id: str = Field(..., min_length=1)


# =========================================================================
# Endpoints
# =========================================================================

@router.post("/documents", response_model=IndexDocumentResponse)
async def index_document(
    request: IndexDocumentRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Index a document into the knowledge base.

    You can either:
    1. Provide `content` and let the system chunk it automatically
    2. Provide pre-chunked `chunks` directly
    """
    container = await get_container()

    # Generate document ID
    document_id = str(uuid4())

    # Create document entity
    document = Document(
        id=document_id,
        tenant_id=ctx.tenant_id,
        title=request.title,
        source=request.source,
        metadata=request.metadata,
    )

    # Prepare chunks
    chunks: List[Chunk] = []

    if request.chunks:
        # Use pre-chunked content
        for i, chunk_input in enumerate(request.chunks):
            chunks.append(Chunk(
                id=f"{document_id}_{i}",
                document_id=document_id,
                content=chunk_input.content,
                chunk_index=chunk_input.chunk_index or i,
                metadata=chunk_input.metadata,
            ))

    elif request.content:
        # Auto-chunk the content
        chunks = _chunk_content(
            document_id=document_id,
            content=request.content,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'content' or 'chunks' must be provided"
        )

    # Index via RAG orchestrator
    count = await container.rag_orchestrator.index_document(
        tenant_id=ctx.tenant_id,
        document=document,
        chunks=chunks,
    )

    logger.info(f"Indexed document {document_id} with {count} chunks for tenant {ctx.tenant_id}")

    return IndexDocumentResponse(
        data={
            "document_id": document_id,
            "chunks_indexed": count,
            "title": request.title,
            "source": request.source,
        }
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Delete a document and all its chunks from the knowledge base.
    """
    container = await get_container()

    count = await container.rag_orchestrator.delete_document(
        tenant_id=ctx.tenant_id,
        document_id=document_id,
    )

    logger.info(f"Deleted document {document_id} ({count} chunks) for tenant {ctx.tenant_id}")

    return {
        "success": True,
        "data": {
            "document_id": document_id,
            "chunks_deleted": count,
        }
    }


@router.post("/sync")
async def sync_knowledge_source(
    source_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Trigger synchronization of a knowledge source.

    This will fetch content from the configured source and update the vector store.
    """
    # TODO: Implement knowledge source synchronization in Phase 3
    return {
        "success": True,
        "data": {
            "source_id": source_id,
            "status": "queued",
            "message": "Knowledge sync not yet implemented",
        }
    }


@router.get("/stats")
async def get_knowledge_stats(
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Get statistics about the knowledge base for this tenant.
    """
    container = await get_container()

    stats = await container.rag_orchestrator.get_collection_stats(ctx.tenant_id)

    return {
        "success": True,
        "data": stats
    }


# =========================================================================
# Helper Functions
# =========================================================================

def _chunk_content(
    document_id: str,
    content: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Chunk]:
    """
    Split content into overlapping chunks.

    Uses a simple character-based chunking strategy.
    More sophisticated strategies (semantic, recursive) can be added later.
    """
    chunks = []
    start = 0
    chunk_index = 0

    while start < len(content):
        # Find end of chunk
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(content):
            # Look for sentence ending
            for sep in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                last_sep = content[start:end].rfind(sep)
                if last_sep > chunk_size // 2:  # Only break if past halfway
                    end = start + last_sep + len(sep)
                    break

        # Extract chunk
        chunk_content = content[start:end].strip()

        if chunk_content:
            chunks.append(Chunk(
                id=f"{document_id}_{chunk_index}",
                document_id=document_id,
                content=chunk_content,
                chunk_index=chunk_index,
                metadata={
                    "start_char": start,
                    "end_char": end,
                },
            ))
            chunk_index += 1

        # Move to next chunk with overlap
        start = end - chunk_overlap

        # Prevent infinite loop
        if start >= len(content) - chunk_overlap:
            break

    return chunks
