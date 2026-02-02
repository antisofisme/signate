"""
Dependency Injection Container.

Composition root for all services and adapters.
"""

from typing import Optional
from dataclasses import dataclass, field

from .config import Settings, get_settings
from .shared.logging import get_logger

# Infrastructure - Database
from .infrastructure.database.connection import DatabasePool
from .infrastructure.database.repositories import (
    TenantRepository,
    SessionRepository,
    MessageRepository,
    FactRepository,
    UserRepository,
    AuditRepository,
)

# Infrastructure - Adapters (Phase 2)
from .infrastructure.adapters.storage.qdrant_adapter import QdrantAdapter
from .infrastructure.adapters.ai.openai_adapter import OpenAIEmbeddingAdapter, OpenAILLMAdapter
from .infrastructure.adapters.rag import VanillaRAGStrategy, HybridRAGStrategy
from .infrastructure.cache.redis_cache import RedisCache

# Infrastructure - Memory Adapters (Phase 3)
from .infrastructure.adapters.memory import (
    InMemoryWorkingMemory,
    PostgresEpisodicMemory,
    PostgresSemanticMemory,
    PostgresTemporalMemory,
)
from .infrastructure.adapters.memory.inmemory_working import WorkingMemoryManager
from .infrastructure.adapters.extraction import LLMFactExtractor, LLMSummarizer

# Core Services (Phase 2)
from .core.services.embedding_service import EmbeddingService
from .core.services.rag_orchestrator import RAGOrchestrator
from .core.services.chat_orchestrator import ChatOrchestrator

# Core Services (Phase 3)
from .core.services.memory_manager import MemoryManager

# Core Interfaces
from .core.interfaces import VectorStore, EmbeddingProvider, LLMProvider, RAGStrategy, ICache

logger = get_logger(__name__)


@dataclass
class Container:
    """
    DI Container - composition root for all dependencies.

    Usage:
        container = Container()
        await container.init()

        # Use services
        tenant_repo = container.tenant_repository

        # Cleanup
        await container.close()
    """
    settings: Settings = field(default_factory=get_settings)

    # Infrastructure - Database
    _db_pool: Optional[DatabasePool] = None

    # Infrastructure - External Services (Phase 2)
    _redis_cache: Optional[RedisCache] = None
    _vector_store: Optional[QdrantAdapter] = None
    _embedding_provider: Optional[OpenAIEmbeddingAdapter] = None
    _llm_provider: Optional[OpenAILLMAdapter] = None

    # Repositories
    _tenant_repository: Optional[TenantRepository] = None
    _session_repository: Optional[SessionRepository] = None
    _message_repository: Optional[MessageRepository] = None
    _fact_repository: Optional[FactRepository] = None
    _user_repository: Optional[UserRepository] = None
    _audit_repository: Optional[AuditRepository] = None

    # Core Services (Phase 2)
    _embedding_service: Optional[EmbeddingService] = None
    _rag_orchestrator: Optional[RAGOrchestrator] = None
    _chat_orchestrator: Optional[ChatOrchestrator] = None

    # RAG Strategies
    _vanilla_rag: Optional[VanillaRAGStrategy] = None
    _hybrid_rag: Optional[HybridRAGStrategy] = None

    # Memory Adapters (Phase 3)
    _working_memory_manager: Optional[WorkingMemoryManager] = None
    _episodic_memory: Optional[PostgresEpisodicMemory] = None
    _semantic_memory: Optional[PostgresSemanticMemory] = None
    _temporal_memory: Optional[PostgresTemporalMemory] = None

    # Extraction Adapters (Phase 3)
    _fact_extractor: Optional[LLMFactExtractor] = None
    _summarizer: Optional[LLMSummarizer] = None

    # Memory Manager (Phase 3)
    _memory_manager: Optional[MemoryManager] = None

    # State
    _initialized: bool = False

    async def init(self) -> None:
        """Initialize all services and connections."""
        if self._initialized:
            return

        logger.info("Initializing container...")

        # =====================================================================
        # Phase 1: Database & Repositories
        # =====================================================================
        self._db_pool = DatabasePool(self.settings.database)
        await self._db_pool.connect()

        self._tenant_repository = TenantRepository(self._db_pool)
        self._message_repository = MessageRepository(self._db_pool)
        self._session_repository = SessionRepository(self._db_pool)
        # Wire up message repository for MemoryStore interface
        self._session_repository.set_message_repository(self._message_repository)
        self._fact_repository = FactRepository(self._db_pool)
        self._user_repository = UserRepository(self._db_pool)
        self._audit_repository = AuditRepository(self._db_pool)

        # =====================================================================
        # Phase 2: External Services (Vector Store, Cache, AI Providers)
        # =====================================================================

        # Redis Cache
        self._redis_cache = RedisCache(
            host=self.settings.redis.host,
            port=self.settings.redis.port,
            db=self.settings.redis.db,
            password=self.settings.redis.password,
        )
        await self._redis_cache.connect()
        logger.info("Redis cache connected")

        # Qdrant Vector Store
        self._vector_store = QdrantAdapter(
            host=self.settings.qdrant.host,
            port=self.settings.qdrant.port,
            api_key=self.settings.qdrant.api_key,
            prefer_grpc=self.settings.qdrant.prefer_grpc,
        )
        await self._vector_store.connect()
        logger.info("Qdrant vector store connected")

        # OpenAI Embedding Provider
        self._embedding_provider = OpenAIEmbeddingAdapter(
            config=self.settings.openai,
        )
        logger.info(f"Embedding provider initialized: {self.settings.openai.embedding_model}")

        # OpenAI LLM Provider
        self._llm_provider = OpenAILLMAdapter(
            config=self.settings.openai,
            model=self.settings.openai.default_model,
        )
        logger.info(f"LLM provider initialized: {self.settings.openai.default_model}")

        # =====================================================================
        # Phase 2: Core Services
        # =====================================================================

        # Embedding Service (with caching)
        self._embedding_service = EmbeddingService(
            embedding_provider=self._embedding_provider,
            cache=self._redis_cache,
            cache_ttl=86400 * 7,  # 7 days
        )

        # RAG Strategies
        self._vanilla_rag = VanillaRAGStrategy(
            vector_store=self._vector_store,
            embedding_provider=self._embedding_provider,
        )

        self._hybrid_rag = HybridRAGStrategy(
            vector_store=self._vector_store,
            embedding_provider=self._embedding_provider,
            db_pool=self._db_pool.pool if self._db_pool else None,
        )

        # RAG Orchestrator
        self._rag_orchestrator = RAGOrchestrator(
            embedding_service=self._embedding_service,
            vector_store=self._vector_store,
            default_strategy=self._vanilla_rag,
            strategies={
                "vanilla": self._vanilla_rag,
                "hybrid": self._hybrid_rag,
            },
        )
        logger.info("RAG orchestrator initialized")

        # Chat Orchestrator (uses session repository as memory store)
        self._chat_orchestrator = ChatOrchestrator(
            memory_store=self._session_repository,  # SessionRepository implements MemoryStore
            llm_provider=self._llm_provider,
            rag_orchestrator=self._rag_orchestrator,
        )
        logger.info("Chat orchestrator initialized")

        # =====================================================================
        # Phase 3: Memory System
        # =====================================================================

        # Working Memory Manager (in-memory, per-session)
        self._working_memory_manager = WorkingMemoryManager(
            max_messages=100,
            max_tokens=8000,
            max_sessions=1000,
        )
        logger.info("Working memory manager initialized")

        # Episodic Memory (session summaries)
        self._episodic_memory = PostgresEpisodicMemory(
            db_pool=self._db_pool,
            vector_store=self._vector_store,
            vector_dimensions=self.settings.openai.embedding_dimensions,
        )
        logger.info("Episodic memory initialized")

        # Semantic Memory (user facts)
        self._semantic_memory = PostgresSemanticMemory(
            db_pool=self._db_pool,
            vector_store=self._vector_store,
            vector_dimensions=self.settings.openai.embedding_dimensions,
        )
        logger.info("Semantic memory initialized")

        # Temporal Memory (time-based summaries)
        self._temporal_memory = PostgresTemporalMemory(
            db_pool=self._db_pool,
            vector_store=self._vector_store,
            vector_dimensions=self.settings.openai.embedding_dimensions,
        )
        logger.info("Temporal memory initialized")

        # Fact Extractor (LLM-based)
        self._fact_extractor = LLMFactExtractor(
            llm_provider=self._llm_provider,
            temperature=0.1,
        )

        # Summarizer (LLM-based)
        self._summarizer = LLMSummarizer(
            llm_provider=self._llm_provider,
            temperature=0.3,
        )

        # Memory Manager (coordinates all 4 layers)
        self._memory_manager = MemoryManager(
            working_memory_manager=self._working_memory_manager,
            episodic_memory=self._episodic_memory,
            semantic_memory=self._semantic_memory,
            temporal_memory=self._temporal_memory,
            embedding_provider=self._embedding_provider,
            fact_extractor=self._fact_extractor,
            summarizer=self._summarizer,
        )
        logger.info("Memory manager initialized")

        self._initialized = True
        logger.info("Container fully initialized (Phase 1 + Phase 2 + Phase 3)")

    async def close(self) -> None:
        """Close all connections and cleanup."""
        if not self._initialized:
            return

        logger.info("Closing container...")

        # Close Qdrant
        if self._vector_store:
            await self._vector_store.close()

        # Close Redis
        if self._redis_cache:
            await self._redis_cache.close()

        # Close database pool
        if self._db_pool:
            await self._db_pool.close()

        self._initialized = False
        logger.info("Container closed")

    def _ensure_initialized(self) -> None:
        """Ensure container is initialized."""
        if not self._initialized:
            raise RuntimeError("Container not initialized. Call init() first.")

    # =========================================================================
    # Properties - Lazy access to services
    # =========================================================================

    @property
    def db_pool(self) -> DatabasePool:
        """Get database pool."""
        self._ensure_initialized()
        return self._db_pool

    @property
    def tenant_repository(self) -> TenantRepository:
        """Get tenant repository."""
        self._ensure_initialized()
        return self._tenant_repository

    @property
    def session_repository(self) -> SessionRepository:
        """Get session repository."""
        self._ensure_initialized()
        return self._session_repository

    @property
    def message_repository(self) -> MessageRepository:
        """Get message repository."""
        self._ensure_initialized()
        return self._message_repository

    @property
    def fact_repository(self) -> FactRepository:
        """Get fact repository."""
        self._ensure_initialized()
        return self._fact_repository

    @property
    def user_repository(self) -> UserRepository:
        """Get user repository."""
        self._ensure_initialized()
        return self._user_repository

    @property
    def audit_repository(self) -> AuditRepository:
        """Get audit repository."""
        self._ensure_initialized()
        return self._audit_repository

    # =========================================================================
    # Phase 2: External Services
    # =========================================================================

    @property
    def redis_cache(self) -> RedisCache:
        """Get Redis cache."""
        self._ensure_initialized()
        return self._redis_cache

    @property
    def vector_store(self) -> QdrantAdapter:
        """Get Qdrant vector store."""
        self._ensure_initialized()
        return self._vector_store

    @property
    def embedding_provider(self) -> OpenAIEmbeddingAdapter:
        """Get embedding provider."""
        self._ensure_initialized()
        return self._embedding_provider

    @property
    def llm_provider(self) -> OpenAILLMAdapter:
        """Get LLM provider."""
        self._ensure_initialized()
        return self._llm_provider

    # =========================================================================
    # Phase 2: Core Services
    # =========================================================================

    @property
    def embedding_service(self) -> EmbeddingService:
        """Get embedding service with caching."""
        self._ensure_initialized()
        return self._embedding_service

    @property
    def rag_orchestrator(self) -> RAGOrchestrator:
        """Get RAG orchestrator."""
        self._ensure_initialized()
        return self._rag_orchestrator

    @property
    def chat_orchestrator(self) -> ChatOrchestrator:
        """Get chat orchestrator."""
        self._ensure_initialized()
        return self._chat_orchestrator

    @property
    def vanilla_rag(self) -> VanillaRAGStrategy:
        """Get vanilla RAG strategy."""
        self._ensure_initialized()
        return self._vanilla_rag

    @property
    def hybrid_rag(self) -> HybridRAGStrategy:
        """Get hybrid RAG strategy."""
        self._ensure_initialized()
        return self._hybrid_rag

    # =========================================================================
    # Phase 3: Memory System
    # =========================================================================

    @property
    def working_memory_manager(self) -> WorkingMemoryManager:
        """Get working memory manager."""
        self._ensure_initialized()
        return self._working_memory_manager

    @property
    def episodic_memory(self) -> PostgresEpisodicMemory:
        """Get episodic memory (session summaries)."""
        self._ensure_initialized()
        return self._episodic_memory

    @property
    def semantic_memory(self) -> PostgresSemanticMemory:
        """Get semantic memory (user facts)."""
        self._ensure_initialized()
        return self._semantic_memory

    @property
    def temporal_memory(self) -> PostgresTemporalMemory:
        """Get temporal memory (time-based summaries)."""
        self._ensure_initialized()
        return self._temporal_memory

    @property
    def fact_extractor(self) -> LLMFactExtractor:
        """Get LLM fact extractor."""
        self._ensure_initialized()
        return self._fact_extractor

    @property
    def summarizer(self) -> LLMSummarizer:
        """Get LLM summarizer."""
        self._ensure_initialized()
        return self._summarizer

    @property
    def memory_manager(self) -> MemoryManager:
        """Get memory manager (coordinates all 4 layers)."""
        self._ensure_initialized()
        return self._memory_manager

    # =========================================================================
    # Health Checks
    # =========================================================================

    async def health_check(self) -> dict:
        """Check health of all services."""
        results = {
            "database": False,
            "redis": False,
            "qdrant": False,
        }

        # Check database
        try:
            if self._db_pool:
                results["database"] = await self._db_pool.health_check()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check Redis
        try:
            if self._redis_cache:
                results["redis"] = await self._redis_cache.health_check()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        # Check Qdrant
        try:
            if self._vector_store:
                results["qdrant"] = await self._vector_store.health_check()
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")

        return results


# Global container instance
_container: Optional[Container] = None


async def get_container() -> Container:
    """Get global container instance."""
    global _container
    if _container is None:
        _container = Container()
        await _container.init()
    return _container


async def close_container() -> None:
    """Close global container."""
    global _container
    if _container is not None:
        await _container.close()
        _container = None
