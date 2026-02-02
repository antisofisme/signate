# CHAT-LAW-001: Modular Architecture

**Status**: IMMUTABLE
**Created**: 2026-01-25
**Category**: Architecture

---

## Statement

> Setiap komponen dalam ARSAKA_TUTUR HARUS dapat diganti (swappable)
> tanpa mengubah komponen lain.

---

## Rationale

AI technology berkembang sangat cepat. Apa yang terbaik hari ini mungkin obsolete besok:
- Vector DB: Qdrant → mungkin ada yang lebih baik
- Embedding: OpenAI → mungkin local model lebih murah
- RAG Strategy: Hybrid → mungkin GraphRAG lebih akurat
- Reranker: Cross-encoder → mungkin ColBERT lebih cepat

Dengan arsitektur modular, kita bisa upgrade tanpa rewrite.

---

## Swappable Components

| Component | Interface | Implementations |
|-----------|-----------|-----------------|
| Vector Store | `VectorStore` | Qdrant, Pinecone, Weaviate, Milvus |
| Embedder | `EmbeddingProvider` | OpenAI, Cohere, Local (sentence-transformers) |
| LLM Provider | `LLMProvider` | OpenAI, DeepSeek, Groq, Claude, Local |
| Reranker | `Reranker` | CrossEncoder, ColBERT, Cohere, None |
| RAG Strategy | `RAGStrategy` | Vanilla, Hybrid, Corrective, Agentic |
| Chunker | `DocumentChunker` | Fixed, Semantic, Recursive |
| Memory Store | `MemoryStore` | PostgreSQL, Redis, SQLite |

---

## Constraints

### REQUIREMENT
- Setiap komponen HARUS mengimplementasi interface yang didefinisikan
- Business logic TIDAK BOLEH langsung mengakses implementasi konkret
- Konfigurasi komponen HARUS melalui environment variables atau config file

### PROHIBITION
- DILARANG import implementasi konkret di layer use case
- DILARANG hardcode nama vendor dalam business logic
- DILARANG menyimpan state vendor-specific di shared storage

### LIMITATION
- Switching komponen HANYA boleh dilakukan saat startup (bukan runtime hot-swap)
- Maksimal 1 implementasi aktif per interface per tenant

---

## Example

```python
# CORRECT - menggunakan interface
class ChatOrchestrator:
    def __init__(
        self,
        vector_store: VectorStore,      # Interface
        embedder: EmbeddingProvider,    # Interface
        llm: LLMProvider,               # Interface
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm = llm

# WRONG - langsung menggunakan implementasi
class ChatOrchestrator:
    def __init__(self):
        self.vector_store = QdrantClient(...)  # Vendor-specific!
        self.embedder = OpenAI(...)            # Vendor-specific!
```

---

## Invariants

1. Mengganti implementasi TIDAK BOLEH memerlukan perubahan di business logic
2. Semua implementasi dari interface yang sama HARUS berperilaku identik
3. Unit test HARUS dapat berjalan dengan mock implementation
