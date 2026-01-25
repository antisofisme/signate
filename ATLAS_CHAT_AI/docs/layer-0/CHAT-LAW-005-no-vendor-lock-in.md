# CHAT-LAW-005: No Vendor Lock-in

**Status**: IMMUTABLE
**Created**: 2026-01-25
**Category**: Architecture

---

## Statement

> Sistem TIDAK BOLEH tightly coupled ke vendor tertentu.
> Migrasi ke vendor lain HARUS dapat dilakukan tanpa rewrite business logic.

---

## Rationale

Vendor landscape berubah cepat:
- Pricing berubah (OpenAI semakin mahal/murah)
- Performance berubah (DeepSeek mungkin lebih cepat)
- Features berubah (Qdrant vs Pinecone vs Weaviate)
- Vendor tutup atau berubah kebijakan

Dengan no vendor lock-in, kita bebas memilih yang terbaik kapan saja.

---

## Affected Components

| Component | Current Vendor | Potential Alternatives |
|-----------|----------------|------------------------|
| Vector DB | Qdrant | Pinecone, Weaviate, Milvus, pgvector |
| Embeddings | OpenAI | Cohere, Voyage, Local models |
| LLM | OpenAI/DeepSeek | Claude, Gemini, Llama, Mistral |
| Reranker | Cohere | Cross-encoder, ColBERT, Jina |
| Object Storage | Local/S3 | R2, GCS, Azure Blob |

---

## Implementation Rules

### Rule 1: Vendor code ONLY in adapters

```
src/
├── core/
│   ├── interfaces/
│   │   └── vector_store.py      # No vendor imports
│   └── services/
│       └── rag_service.py       # Uses VectorStore interface
│
├── infrastructure/
│   └── adapters/
│       ├── qdrant_adapter.py    # Qdrant-specific code HERE
│       ├── pinecone_adapter.py  # Pinecone-specific code HERE
│       └── openai_adapter.py    # OpenAI-specific code HERE
```

### Rule 2: Configuration-driven selection

```python
# config.py
VECTOR_STORE = os.getenv("VECTOR_STORE", "qdrant")  # qdrant | pinecone | weaviate
EMBEDDER = os.getenv("EMBEDDER", "openai")          # openai | cohere | local
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | deepseek | claude

# container.py
def create_vector_store(config: Config) -> VectorStore:
    match config.vector_store:
        case "qdrant":
            return QdrantAdapter(config.qdrant_url)
        case "pinecone":
            return PineconeAdapter(config.pinecone_api_key)
        case "weaviate":
            return WeaviateAdapter(config.weaviate_url)
        case _:
            raise ValueError(f"Unknown vector store: {config.vector_store}")
```

### Rule 3: Data portability

```python
# Export format harus vendor-agnostic
class VectorExport:
    id: str
    content: str
    embedding: List[float]  # Standard float array
    metadata: dict          # JSON-compatible

# Bisa di-import ke vendor manapun
async def migrate_vectors(
    source: VectorStore,
    target: VectorStore,
    batch_size: int = 100
):
    async for batch in source.export_all(batch_size):
        await target.import_batch(batch)
```

---

## Constraints

### REQUIREMENT
- Semua vendor SDK HARUS wrapped dalam adapter class
- Adapter HARUS implement interface yang sama
- Data export HARUS dalam format portable (JSON, Parquet)
- Config HARUS support environment variables

### PROHIBITION
- DILARANG import vendor SDK di core/ directory
- DILARANG menggunakan vendor-specific features yang tidak portable
- DILARANG menyimpan data dalam format proprietary
- DILARANG hardcode API keys atau endpoints

### LIMITATION
- Vendor-specific optimizations boleh, tapi di adapter only
- Vendor-specific features yang tidak portable harus optional

---

## Migration Checklist

Ketika migrasi dari Vendor A ke Vendor B:

1. [ ] Implement adapter B dengan interface yang sama
2. [ ] Test adapter B dengan unit tests yang sama
3. [ ] Export data dari A dalam format portable
4. [ ] Import data ke B
5. [ ] Update config (VECTOR_STORE=B)
6. [ ] Restart service
7. [ ] Verify functionality
8. [ ] Remove adapter A (optional)

**Effort should be: < 1 day for any migration**

---

## Anti-Patterns to Avoid

```python
# WRONG - Direct vendor usage
from qdrant_client import QdrantClient
client = QdrantClient(url="...")
results = client.search(collection="docs", query_vector=vec)

# WRONG - Vendor-specific in business logic
def search_documents(query: str):
    # Qdrant-specific code in service layer!
    from qdrant_client.models import Filter, FieldCondition
    filter = Filter(must=[FieldCondition(...)])
    return qdrant.search(..., query_filter=filter)

# CORRECT - Use interface
async def search_documents(
    query: str,
    vector_store: VectorStore  # Interface
):
    embedding = await embedder.embed(query)
    return await vector_store.search(
        query_vector=embedding,
        top_k=5,
        filters={"tenant_id": tenant_id}  # Generic filter format
    )
```

---

## Invariants

1. Core business logic TIDAK BOLEH mengimport vendor SDK
2. Semua vendor-specific code ada di infrastructure/adapters/
3. Adapter switch TIDAK BOLEH memerlukan perubahan di tests
4. Data HARUS bisa di-export dan di-import antar vendor
