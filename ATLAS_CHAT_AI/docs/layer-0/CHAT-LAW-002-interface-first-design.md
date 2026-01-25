# CHAT-LAW-002: Interface-First Design

**Status**: IMMUTABLE
**Created**: 2026-01-25
**Category**: Architecture

---

## Statement

> Semua modul dan komponen HARUS diakses melalui abstract interface.
> Implementasi konkret HANYA boleh di-instantiate di composition root.

---

## Rationale

Interface-first design memungkinkan:
1. **Testability** - Mock any dependency
2. **Flexibility** - Swap implementations
3. **Clarity** - Contract jelas antara komponen
4. **Decoupling** - Komponen tidak saling tahu detail internal

---

## Core Interfaces

### Storage Interfaces

```python
class VectorStore(ABC):
    """Interface untuk semua vector database"""

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        filters: Optional[dict] = None
    ) -> List[SearchResult]:
        pass

    @abstractmethod
    async def upsert(
        self,
        id: str,
        vector: List[float],
        payload: dict
    ) -> bool:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass


class MemoryStore(ABC):
    """Interface untuk persistent storage (sessions, messages)"""

    @abstractmethod
    async def save_session(self, session: ChatSession) -> str:
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        pass

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> str:
        pass
```

### AI Interfaces

```python
class EmbeddingProvider(ABC):
    """Interface untuk embedding generation"""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass


class LLMProvider(ABC):
    """Interface untuk LLM calls"""

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        pass


class Reranker(ABC):
    """Interface untuk reranking search results"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int
    ) -> List[RankedDocument]:
        pass
```

### RAG Interfaces

```python
class RAGStrategy(ABC):
    """Interface untuk RAG pipeline"""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        context: RetrievalContext
    ) -> List[Document]:
        pass


class DocumentChunker(ABC):
    """Interface untuk document chunking"""

    @abstractmethod
    def chunk(
        self,
        document: str,
        metadata: dict
    ) -> List[Chunk]:
        pass
```

---

## Constraints

### REQUIREMENT
- Setiap interface HARUS memiliki minimal satu implementasi
- Interface HARUS di-define di module `core/interfaces/`
- Semua method interface HARUS async (untuk consistency)

### PROHIBITION
- DILARANG menambahkan vendor-specific method ke interface
- DILARANG menggunakan `isinstance()` untuk check implementasi konkret
- DILARANG type hint dengan implementasi konkret di function signature

### LIMITATION
- Interface method signature TIDAK BOLEH diubah setelah release
- Perubahan interface memerlukan versi baru (v2, v3, dst)

---

## Composition Root

```python
# main.py atau container.py - SATU-SATUNYA tempat instantiate konkret

def create_container(config: Config) -> Container:
    """Composition root - wire all dependencies"""

    # Choose implementations based on config
    if config.vector_store == "qdrant":
        vector_store = QdrantVectorStore(config.qdrant_url)
    elif config.vector_store == "pinecone":
        vector_store = PineconeVectorStore(config.pinecone_api_key)

    if config.embedder == "openai":
        embedder = OpenAIEmbedder(config.openai_api_key)
    elif config.embedder == "local":
        embedder = LocalEmbedder(config.model_path)

    # Assemble orchestrator with interfaces
    orchestrator = ChatOrchestrator(
        vector_store=vector_store,
        embedder=embedder,
        llm=create_llm(config),
        memory=create_memory(config),
    )

    return Container(orchestrator=orchestrator)
```

---

## Invariants

1. Tidak ada `import QdrantClient` di luar infrastructure layer
2. Semua dependency injection melalui constructor
3. Interface files tidak boleh import dari implementations
