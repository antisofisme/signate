# CHAT-L1-ARCH-001: Core Interfaces

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-001, CHAT-LAW-002

---

## Context

Untuk memenuhi CHAT-LAW-001 (Modular) dan CHAT-LAW-002 (Interface-First), kita perlu mendefinisikan semua interface yang akan digunakan dalam sistem.

---

## Decision

Definisikan 7 kategori interface utama:

### 1. Storage Interfaces

```python
# core/interfaces/storage.py

class VectorStore(ABC):
    """Interface untuk vector database operations"""

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    async def upsert(
        self,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """Insert or update a vector"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete a vector by ID"""
        pass

    @abstractmethod
    async def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        """Delete vectors matching filter, return count"""
        pass


class MemoryStore(ABC):
    """Interface untuk persistent chat storage"""

    @abstractmethod
    async def create_session(self, session: ChatSession) -> str:
        pass

    @abstractmethod
    async def get_session(self, session_id: str, tenant_id: str) -> Optional[ChatSession]:
        pass

    @abstractmethod
    async def update_session(self, session: ChatSession) -> bool:
        pass

    @abstractmethod
    async def list_sessions(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ChatSession]:
        pass

    @abstractmethod
    async def save_message(self, message: ChatMessage) -> str:
        pass

    @abstractmethod
    async def get_messages(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        pass
```

### 2. AI Provider Interfaces

```python
# core/interfaces/ai_providers.py

class EmbeddingProvider(ABC):
    """Interface untuk embedding generation"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Embed single text"""
        pass

    @abstractmethod
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Embed multiple texts"""
        pass


class LLMProvider(ABC):
    """Interface untuk LLM completion"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stop: Optional[List[str]] = None
    ) -> GenerationResult:
        """Generate completion"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """Stream completion token by token"""
        pass


class Reranker(ABC):
    """Interface untuk reranking search results"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5
    ) -> List[RankedDocument]:
        """Rerank documents by relevance to query"""
        pass
```

### 3. RAG Interfaces

```python
# core/interfaces/rag.py

class RAGStrategy(ABC):
    """Interface untuk RAG retrieval strategy"""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        context: RetrievalContext
    ) -> RetrievalResult:
        """Retrieve relevant documents for query"""
        pass


class DocumentChunker(ABC):
    """Interface untuk document chunking"""

    @abstractmethod
    def chunk(
        self,
        document: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Split document into chunks"""
        pass

    @property
    @abstractmethod
    def chunk_size(self) -> int:
        pass

    @property
    @abstractmethod
    def chunk_overlap(self) -> int:
        pass


class QueryProcessor(ABC):
    """Interface untuk query preprocessing"""

    @abstractmethod
    async def process(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ProcessedQuery:
        """Process and potentially rewrite query"""
        pass
```

### 4. Memory Interfaces

```python
# core/interfaces/memory.py

class WorkingMemory(ABC):
    """Interface untuk current session memory"""

    @abstractmethod
    def add(self, message: ChatMessage) -> None:
        pass

    @abstractmethod
    def get_recent(self, limit: int = 10) -> List[ChatMessage]:
        pass

    @abstractmethod
    def get_token_count(self) -> int:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class EpisodicMemory(ABC):
    """Interface untuk session-based memory"""

    @abstractmethod
    async def save_session(self, session: ChatSession) -> str:
        pass

    @abstractmethod
    async def search_sessions(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[SessionSummary]:
        pass

    @abstractmethod
    async def get_session_messages(
        self,
        session_id: str,
        tenant_id: str
    ) -> List[ChatMessage]:
        pass


class SemanticMemory(ABC):
    """Interface untuk user facts/knowledge"""

    @abstractmethod
    async def add_fact(self, fact: UserFact) -> str:
        pass

    @abstractmethod
    async def get_relevant_facts(
        self,
        tenant_id: str,
        user_id: str,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[UserFact]:
        pass

    @abstractmethod
    async def update_fact_confidence(
        self,
        fact_id: str,
        new_confidence: float
    ) -> bool:
        pass


class TemporalMemory(ABC):
    """Interface untuk time-based summaries"""

    @abstractmethod
    async def get_summary(
        self,
        tenant_id: str,
        user_id: str,
        period_type: str,  # 'day', 'week', 'month'
        period_start: date
    ) -> Optional[TimeSummary]:
        pass

    @abstractmethod
    async def create_summary(
        self,
        summary: TimeSummary
    ) -> str:
        pass
```

### 5. Extraction Interfaces

```python
# core/interfaces/extraction.py

class FactExtractor(ABC):
    """Interface untuk extracting facts from conversations"""

    @abstractmethod
    async def extract(
        self,
        messages: List[ChatMessage],
        existing_facts: List[UserFact]
    ) -> List[ExtractedFact]:
        """Extract new facts from conversation"""
        pass


class Summarizer(ABC):
    """Interface untuk conversation summarization"""

    @abstractmethod
    async def summarize(
        self,
        messages: List[ChatMessage],
        max_length: int = 500
    ) -> str:
        """Create summary of conversation"""
        pass

    @abstractmethod
    async def summarize_incremental(
        self,
        previous_summary: str,
        new_messages: List[ChatMessage],
        max_length: int = 500
    ) -> str:
        """Update existing summary with new messages"""
        pass
```

### 6. Tenant Interfaces

```python
# core/interfaces/tenant.py

class TenantRegistry(ABC):
    """Interface untuk tenant management"""

    @abstractmethod
    async def register(self, config: TenantConfig) -> str:
        pass

    @abstractmethod
    async def get_config(self, tenant_id: str) -> Optional[TenantConfig]:
        pass

    @abstractmethod
    async def update_config(self, config: TenantConfig) -> bool:
        pass

    @abstractmethod
    async def list_tenants(self) -> List[TenantConfig]:
        pass


class KnowledgeSource(ABC):
    """Interface untuk tenant knowledge sources"""

    @abstractmethod
    async def sync(self, tenant_id: str) -> SyncResult:
        """Sync knowledge from source to vector store"""
        pass

    @abstractmethod
    async def get_documents(
        self,
        tenant_id: str,
        filters: Optional[Dict] = None
    ) -> List[Document]:
        pass
```

### 7. Context Assembly Interface

```python
# core/interfaces/context.py

class ContextAssembler(ABC):
    """Interface untuk building LLM context"""

    @abstractmethod
    async def assemble(
        self,
        tenant_id: str,
        user_id: str,
        session_id: str,
        current_query: str,
        working_memory: WorkingMemory,
        retrieved_docs: List[Document],
        user_facts: List[UserFact]
    ) -> AssembledContext:
        """Assemble full context for LLM"""
        pass

    @abstractmethod
    def estimate_tokens(self, context: AssembledContext) -> int:
        """Estimate token count of context"""
        pass
```

---

## Consequences

### Positive
- Semua komponen dapat di-mock untuk testing
- Implementasi dapat diganti tanpa mengubah business logic
- Clear contracts antar komponen
- Dependency injection mudah

### Negative
- Boilerplate code lebih banyak
- Perlu maintain interface + implementasi
- Learning curve untuk developers baru

---

## Lean Stack Interfaces

Untuk Lean Stack (PostgreSQL + Qdrant + Redis), interface tambahan yang diperlukan:

### 8. Job Queue Interface (Redis Streams)

```python
# core/interfaces/queue.py

class JobQueue(ABC):
    """Interface untuk job queue (Redis Streams, RabbitMQ, etc.)"""

    @abstractmethod
    async def publish(
        self,
        queue: str,
        job: Dict[str, Any]
    ) -> str:
        """Add job to queue, returns job ID"""
        pass

    @abstractmethod
    async def consume(
        self,
        queue: str,
        group: str,
        consumer: str
    ) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """Consume jobs from queue, yields (job_id, job_data)"""
        pass

    @abstractmethod
    async def ack(self, queue: str, group: str, job_id: str) -> None:
        """Acknowledge job completion"""
        pass

    @abstractmethod
    async def retry(
        self,
        queue: str,
        job_id: str,
        delay_seconds: int = 0
    ) -> bool:
        """Retry failed job"""
        pass
```

### 9. File Storage Interface (Local/S3)

```python
# core/interfaces/file_storage.py

class FileStorage(ABC):
    """Interface untuk file storage (Local, MinIO, S3)"""

    @abstractmethod
    async def put(
        self,
        tenant_id: str,
        file_id: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file, returns path/URL"""
        pass

    @abstractmethod
    async def get(self, tenant_id: str, file_id: str) -> bytes:
        """Download file as bytes"""
        pass

    @abstractmethod
    async def delete(self, tenant_id: str, file_id: str) -> bool:
        """Delete file"""
        pass

    @abstractmethod
    async def exists(self, tenant_id: str, file_id: str) -> bool:
        """Check if file exists"""
        pass
```

### 10. Text Search Interface (PostgreSQL FTS)

```python
# core/interfaces/text_search.py

class TextSearch(ABC):
    """Interface untuk full-text search (PostgreSQL FTS, Meilisearch)"""

    @abstractmethod
    async def search(
        self,
        tenant_id: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[TextSearchResult]:
        """Full-text search with optional filters"""
        pass

    @abstractmethod
    async def index_document(
        self,
        tenant_id: str,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Add/update document in search index"""
        pass
```

---

## Scale-Up Interfaces (Add When Needed)

Interfaces untuk extended stack (hanya implement jika scale up):

### Graph Store (ArangoDB/Neo4j) - Add at 100k+ entities

```python
# core/interfaces/graph.py (OPTIONAL)

class GraphStore(ABC):
    """Interface untuk graph database - add when need 5+ hop traversals"""

    @abstractmethod
    async def add_vertex(self, collection: str, data: Dict) -> str:
        pass

    @abstractmethod
    async def add_edge(self, collection: str, from_id: str, to_id: str, data: Dict) -> str:
        pass

    @abstractmethod
    async def traverse(self, start: str, edges: List[str], depth: int) -> List[Dict]:
        pass
```

### Advanced Queue (RabbitMQ/Kafka) - Add at 10k+ jobs/sec

```python
# core/interfaces/advanced_queue.py (OPTIONAL)

class AdvancedQueue(ABC):
    """Interface untuk advanced queue - add when Redis Streams bottleneck"""

    @abstractmethod
    async def publish(self, exchange: str, routing_key: str, body: Dict) -> bool:
        pass

    @abstractmethod
    async def consume(self, queue: str, callback: Callable) -> None:
        pass

    @abstractmethod
    async def declare_queue(self, queue: str, dlx: Optional[str] = None) -> bool:
        pass
```

---

## Implementation Notes

- Semua interface di-define di `core/interfaces/`
- Setiap interface harus punya minimal satu implementasi
- Interface tidak boleh import dari implementasi
- Gunakan `typing.Protocol` untuk duck typing jika diperlukan

### Lean Stack Adapters (Required)

```
infrastructure/adapters/
├── storage/
│   ├── qdrant_adapter.py        # VectorStore
│   └── postgres_memory.py       # MemoryStore
├── queue/
│   └── redis_queue_adapter.py   # JobQueue (Redis Streams)
├── search/
│   └── postgres_fts_adapter.py  # TextSearch (PostgreSQL FTS)
├── files/
│   └── local_storage_adapter.py # FileStorage (Local)
└── ai/
    ├── openai_adapter.py        # LLMProvider, EmbeddingProvider
    └── deepseek_adapter.py      # LLMProvider
```

### Scale-Up Adapters (Optional)

```
infrastructure/adapters/
├── search/
│   └── meilisearch_adapter.py   # TextSearch (scale-up)
├── graph/
│   └── arangodb_adapter.py      # GraphStore (scale-up)
├── queue/
│   └── rabbitmq_adapter.py      # AdvancedQueue (scale-up)
└── files/
    └── minio_adapter.py         # FileStorage (scale-up)
```
