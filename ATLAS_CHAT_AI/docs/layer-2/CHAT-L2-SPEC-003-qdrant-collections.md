# CHAT-L2-SPEC-003: Qdrant Collections

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-004, CHAT-LAW-005

---

## Overview

Qdrant vector store schema and collection configuration for ATLAS_CHAT_AI.

---

## Collection Naming

Per CHAT-LAW-004 (multi-tenant isolation), each tenant has separate collections:

```
{tenant_id}_documents    # Knowledge base documents
{tenant_id}_sessions     # Session embeddings
{tenant_id}_facts        # User fact embeddings
```

Example:
- `mantra_documents`
- `mantra_sessions`
- `pandawa_documents`

---

## Collection Schemas

### 1. Documents Collection

Stores embeddings of knowledge base documents (decisions, reservations, etc.).

```python
collection_config = {
    "collection_name": "{tenant_id}_documents",
    "vectors_config": {
        "size": 1536,           # OpenAI text-embedding-3-small
        "distance": "Cosine"    # Cosine similarity
    },
    "optimizers_config": {
        "memmap_threshold": 20000,   # Use mmap for large collections
        "indexing_threshold": 10000  # Build index after N vectors
    },
    "wal_config": {
        "wal_capacity_mb": 32,
        "wal_segments_ahead": 0
    },
    "on_disk_payload": False  # Keep payload in memory for speed
}
```

**Payload Schema:**
```python
document_payload = {
    # Required fields
    "id": "doc-uuid",                    # Unique document ID
    "tenant_id": "mantra",               # Tenant (for extra safety)
    "source": "decisions",               # Knowledge source name
    "content": "The full text...",       # Document content

    # Metadata (varies by source)
    "metadata": {
        "decision_code": "CTL-F11-001",
        "group_id": "CTL",
        "feature_id": "F11",
        "scope": "APPLICATION",
        "blast_radius": "HIGH",
        "tags": ["SECURITY", "API"],
        "created_at": "2026-01-25T10:00:00Z"
    },

    # Chunking info
    "chunk_index": 0,                    # Chunk number (0 if not chunked)
    "chunk_total": 1,                    # Total chunks for this document
    "parent_id": "original-doc-uuid",    # Parent document ID if chunked

    # Timestamps
    "indexed_at": "2026-01-25T10:00:00Z"
}
```

**Index Configuration:**
```python
payload_indexes = [
    # Keyword filters
    {"field_name": "source", "field_schema": "keyword"},
    {"field_name": "metadata.group_id", "field_schema": "keyword"},
    {"field_name": "metadata.scope", "field_schema": "keyword"},
    {"field_name": "metadata.tags", "field_schema": "keyword"},  # Array

    # Date filters
    {"field_name": "indexed_at", "field_schema": "datetime"},
    {"field_name": "metadata.created_at", "field_schema": "datetime"},
]
```

### 2. Sessions Collection

Stores embeddings of session summaries for similarity search.

```python
collection_config = {
    "collection_name": "{tenant_id}_sessions",
    "vectors_config": {
        "size": 1536,
        "distance": "Cosine"
    }
}
```

**Payload Schema:**
```python
session_payload = {
    "session_id": "uuid",
    "user_id": "user-123",
    "title": "Authentication discussion",
    "summary": "The summary text...",
    "topics": ["authentication", "jwt", "oauth"],
    "message_count": 20,
    "started_at": "2026-01-20T10:00:00Z",
    "last_message_at": "2026-01-20T11:00:00Z"
}
```

**Index Configuration:**
```python
payload_indexes = [
    {"field_name": "user_id", "field_schema": "keyword"},
    {"field_name": "topics", "field_schema": "keyword"},
    {"field_name": "started_at", "field_schema": "datetime"},
]
```

### 3. Facts Collection

Stores embeddings of user facts for semantic memory retrieval.

```python
collection_config = {
    "collection_name": "{tenant_id}_facts",
    "vectors_config": {
        "size": 1536,
        "distance": "Cosine"
    }
}
```

**Payload Schema:**
```python
fact_payload = {
    "fact_id": "uuid",
    "user_id": "user-123",
    "fact_type": "preference",
    "content": "Prefers TypeScript over JavaScript",
    "confidence": 0.95,
    "source_session_id": "uuid",
    "created_at": "2026-01-20T10:00:00Z",
    "is_active": True
}
```

**Index Configuration:**
```python
payload_indexes = [
    {"field_name": "user_id", "field_schema": "keyword"},
    {"field_name": "fact_type", "field_schema": "keyword"},
    {"field_name": "confidence", "field_schema": "float"},
    {"field_name": "is_active", "field_schema": "bool"},
]
```

---

## Search Operations

### Basic Similarity Search

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

async def search_documents(
    tenant_id: str,
    query_embedding: List[float],
    top_k: int = 5,
    source_filter: Optional[str] = None
) -> List[SearchResult]:

    filters = []

    # Always filter by source if specified
    if source_filter:
        filters.append(
            FieldCondition(
                key="source",
                match=MatchValue(value=source_filter)
            )
        )

    results = client.search(
        collection_name=f"{tenant_id}_documents",
        query_vector=query_embedding,
        limit=top_k,
        query_filter=Filter(must=filters) if filters else None,
        score_threshold=0.5  # Minimum similarity
    )

    return [
        SearchResult(
            id=r.id,
            score=r.score,
            content=r.payload["content"],
            metadata=r.payload["metadata"]
        )
        for r in results
    ]
```

### Filtered Search

```python
async def search_with_filters(
    tenant_id: str,
    query_embedding: List[float],
    filters: Dict[str, Any]
) -> List[SearchResult]:

    filter_conditions = []

    # Group filter
    if "group_id" in filters:
        filter_conditions.append(
            FieldCondition(
                key="metadata.group_id",
                match=MatchValue(value=filters["group_id"])
            )
        )

    # Tags filter (must have ALL specified tags)
    if "tags" in filters:
        for tag in filters["tags"]:
            filter_conditions.append(
                FieldCondition(
                    key="metadata.tags",
                    match=MatchValue(value=tag)
                )
            )

    # Scope filter
    if "scope" in filters:
        filter_conditions.append(
            FieldCondition(
                key="metadata.scope",
                match=MatchValue(value=filters["scope"])
            )
        )

    results = client.search(
        collection_name=f"{tenant_id}_documents",
        query_vector=query_embedding,
        limit=10,
        query_filter=Filter(must=filter_conditions) if filter_conditions else None
    )

    return results
```

### Hybrid Search (Vector + Payload)

```python
async def hybrid_search(
    tenant_id: str,
    query_embedding: List[float],
    text_query: str,
    top_k: int = 10
) -> List[SearchResult]:

    # 1. Vector search
    vector_results = await search_documents(
        tenant_id, query_embedding, top_k=top_k * 2
    )

    # 2. Keyword search (using Qdrant's scroll with filter)
    keyword_results = client.scroll(
        collection_name=f"{tenant_id}_documents",
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="content",
                    match=MatchText(text=text_query)  # Full-text search
                )
            ]
        ),
        limit=top_k * 2
    )

    # 3. RRF fusion
    return rrf_fusion(vector_results, keyword_results, top_k=top_k)
```

---

## Upsert Operations

### Single Document

```python
async def upsert_document(
    tenant_id: str,
    doc_id: str,
    content: str,
    embedding: List[float],
    metadata: Dict[str, Any]
):
    client.upsert(
        collection_name=f"{tenant_id}_documents",
        points=[
            PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "id": doc_id,
                    "tenant_id": tenant_id,
                    "content": content,
                    "metadata": metadata,
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
        ]
    )
```

### Batch Upsert

```python
async def batch_upsert_documents(
    tenant_id: str,
    documents: List[Document],
    embeddings: List[List[float]],
    batch_size: int = 100
):
    points = [
        PointStruct(
            id=doc.id,
            vector=emb,
            payload={
                "id": doc.id,
                "tenant_id": tenant_id,
                "content": doc.content,
                "metadata": doc.metadata,
                "indexed_at": datetime.utcnow().isoformat()
            }
        )
        for doc, emb in zip(documents, embeddings)
    ]

    # Batch upsert
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=f"{tenant_id}_documents",
            points=batch
        )
```

---

## Delete Operations

### Delete by ID

```python
async def delete_document(tenant_id: str, doc_id: str):
    client.delete(
        collection_name=f"{tenant_id}_documents",
        points_selector=PointIdsList(points=[doc_id])
    )
```

### Delete by Filter

```python
async def delete_by_source(tenant_id: str, source: str):
    """Delete all documents from a specific source"""
    client.delete(
        collection_name=f"{tenant_id}_documents",
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source)
                    )
                ]
            )
        )
    )
```

---

## Collection Management

### Create Collection

```python
async def create_tenant_collections(tenant_id: str):
    """Create all collections for a new tenant"""

    collections = [
        (f"{tenant_id}_documents", 1536),
        (f"{tenant_id}_sessions", 1536),
        (f"{tenant_id}_facts", 1536),
    ]

    for name, size in collections:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=size,
                distance=Distance.COSINE
            )
        )

        # Wait for collection to be ready
        while True:
            info = client.get_collection(name)
            if info.status == CollectionStatus.GREEN:
                break
            await asyncio.sleep(0.5)
```

### Delete Tenant Collections

```python
async def delete_tenant_collections(tenant_id: str):
    """Delete all collections for a tenant (when tenant is removed)"""
    for suffix in ["_documents", "_sessions", "_facts"]:
        try:
            client.delete_collection(f"{tenant_id}{suffix}")
        except Exception:
            pass  # Collection might not exist
```

---

## Backup & Recovery

### Snapshot Creation

```python
async def create_snapshot(tenant_id: str) -> str:
    """Create snapshot of tenant's documents collection"""
    result = client.create_snapshot(
        collection_name=f"{tenant_id}_documents"
    )
    return result.name
```

### Snapshot Recovery

```python
async def recover_from_snapshot(tenant_id: str, snapshot_name: str):
    """Recover collection from snapshot"""
    client.recover_snapshot(
        collection_name=f"{tenant_id}_documents",
        snapshot_name=snapshot_name
    )
```

---

## Performance Tuning

### Recommended Settings for Production

```python
production_config = {
    "optimizers_config": {
        "deleted_threshold": 0.2,      # Trigger optimization at 20% deleted
        "vacuum_min_vector_number": 1000,
        "default_segment_number": 4,   # Parallel search
        "memmap_threshold": 50000,     # Use disk after 50k vectors
        "indexing_threshold": 20000,   # Build HNSW after 20k vectors
        "flush_interval_sec": 5
    },
    "hnsw_config": {
        "m": 16,                       # Connections per node
        "ef_construct": 100,           # Index build quality
        "full_scan_threshold": 10000   # Use HNSW after 10k vectors
    }
}
```

### Query Performance Settings

```python
search_params = {
    "hnsw_ef": 128,    # Higher = more accurate, slower
    "exact": False     # Use approximate search
}
```
