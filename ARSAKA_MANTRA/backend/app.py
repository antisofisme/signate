"""
ARSAKA_MANTRA FastAPI Application

Decision Matrix Constitutional Law System

Per MANTRA-LAW-001:
- AI Authority = ZERO
- Decisions are human-only
- Stored decisions are immutable
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from core.api.routes import router as api_router
from core.api.ai_routes import router as ai_router
from core.api.api_key_routes import router as api_key_router
from core.api.search_routes import router as search_router
from core.api.docs_routes import router as docs_router
from core.api.validation_routes import router as validation_router
from core.api.analytics_routes import router as analytics_router
from core.api.retrieval_routes import router as retrieval_router
from core.api.export_routes import router as export_router
from core.api.jobs_routes import router as jobs_router
from core.api.monitoring_routes import router as monitoring_router
from core.api.draft_routes import router as draft_router
from core.runtime.config import get_config
from core.ai import close_arsaka_tutur_client
from factory.container import Container


# ============================================================================
# Application Setup
# ============================================================================

config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"[{datetime.utcnow().isoformat()}] ARSAKA_MANTRA starting...")
    print(f"  - Host: {config.host}")
    print(f"  - Port: {config.port}")
    print(f"  - CORS: {config.cors_origins_list}")
    print(f"  - Docs: {'enabled' if config.enable_docs else 'disabled'}")
    print(f"  - Semantic Search: {'enabled' if config.enable_semantic_search else 'disabled'}")
    print(f"  - Vector Store: {config.vector_store}")
    print(f"  - Cache: {config.cache}")
    print(f"  - Embedding: {config.embedding_service}")
    print(f"  - Message Queue: {'enabled' if config.feature_rabbitmq_enabled else 'disabled'}")
    print(f"  - Text Search: {'enabled' if config.feature_meilisearch_enabled else 'disabled'}")
    print(f"  - Redis Enhanced: {'enabled' if config.feature_redis_enhanced_cache else 'disabled'}")
    print(f"  - ARSAKA_TUTUR: {config.arsaka_tutur_url}")

    # Initialize all services (repository, vector store, cache, embedding)
    await Container.initialize()

    # Check service connection status
    if config.feature_rabbitmq_enabled:
        queue = Container.get_message_queue()
        if queue:
            try:
                healthy = await queue.health_check()
                print(f"  - RabbitMQ: {'connected' if healthy else 'disconnected'}")
            except Exception:
                print(f"  - RabbitMQ: connection failed")

    if config.feature_meilisearch_enabled:
        text_search = Container.get_text_search()
        if text_search:
            try:
                healthy = await text_search.health_check()
                print(f"  - Meilisearch: {'connected' if healthy else 'disconnected'}")
            except Exception:
                print(f"  - Meilisearch: connection failed")

    print(f"  - Container initialized")

    yield

    # Shutdown
    print(f"[{datetime.utcnow().isoformat()}] ARSAKA_MANTRA shutting down...")
    await close_arsaka_tutur_client()
    await Container.close_all()


app = FastAPI(
    title="ARSAKA_MANTRA",
    description="""
## Decision Matrix Constitutional Law System

ARSAKA_MANTRA provides a constitutional governance framework for decision management.

### Architecture

The system implements 3 core services per Layer 1 specifications:

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Validator | POST /validate | Validates decisions against schema |
| Store | POST /decisions | Stores validated decisions immutably |
| Read API | GET /decisions | Read-only access to stored decisions |

### Constitutional Law

Per **MANTRA-LAW-001**:

- **AI Authority = ZERO** - AI cannot create, approve, or modify decisions
- **Human Decision Only** - All authoritative actions require human decision
- **Immutability** - Stored decisions cannot be modified or deleted

### Decision Taxonomy

4 Groups × 4 Features = 16 Decision Categories

| Group | Meaning | Features |
|-------|---------|----------|
| INT | Intent & Direction | F01, F02, F03, F04 |
| ARCH | Architecture & Boundaries | F05, F06, F07, F08 |
| CTL | Control, Policy & Risk | F09, F10, F11, F12 |
| EVO | Execution & Evolution | F13, F14, F15, F16 |

### Validation Rules

47 validation rules across 3 levels:

- **Level 1 (S-rules)**: Schema validation (22 rules)
- **Level 2 (D-rules)**: Decision consistency (14 rules)
- **Level 3 (L-rules)**: Law compliance (11 rules)
    """,
    version="1.0.0",
    docs_url="/docs" if config.enable_docs else None,
    redoc_url="/redoc" if config.enable_docs else None,
    openapi_url="/openapi.json" if config.enable_docs else None,
    lifespan=lifespan,
)


# ============================================================================
# Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Routes
# ============================================================================

app.include_router(api_router)
app.include_router(ai_router, prefix="/api/v1")
app.include_router(api_key_router)
app.include_router(search_router)  # Semantic search endpoints
app.include_router(docs_router)  # Document generation endpoints
app.include_router(validation_router)  # 3-gate validation endpoints
app.include_router(analytics_router)  # Usage analytics endpoints
app.include_router(retrieval_router)  # Enhanced retrieval endpoints
app.include_router(export_router)  # Export integration endpoints
app.include_router(jobs_router)  # Background jobs endpoints
app.include_router(monitoring_router)  # Health checks and metrics
app.include_router(draft_router, prefix="/api/v1")  # Per-field decision review


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "ARSAKA_MANTRA",
        "version": "1.0.0",
        "description": "Decision Matrix Constitutional Law System",
        "governing_law": "MANTRA-LAW-001",
        "api_docs": "/docs" if config.enable_docs else None,
        "health": "/api/v1/health",
        "endpoints": {
            "validate": "POST /api/v1/validate",
            "decisions": "GET/POST /api/v1/decisions",
            "matrix": "GET /api/v1/matrix",
            "grouped": "GET /api/v1/grouped",
            "ai_chat": "POST /api/v1/ai/chat",
            "ai_hints": "POST /api/v1/ai/hints",
            "api_keys": "GET/POST /api/v1/api-keys",
            "semantic_search": "POST /api/v1/search/semantic",
            "check_alignment": "POST /api/v1/search/check-alignment",
            "rebuild_index": "POST /api/v1/search/rebuild-index",
            "search_stats": "GET /api/v1/search/stats",
            "docs_generate": "POST /api/v1/docs/generate",
            "docs_types": "GET /api/v1/docs/types",
            "validation_pipeline": "POST /api/v1/validation/pipeline",
            "validation_gate1": "POST /api/v1/validation/gate1",
            "validation_approvals": "GET /api/v1/validation/approvals/pending",
            "analytics_track": "POST /api/v1/analytics/track/event",
            "analytics_summary": "GET /api/v1/analytics/summary",
            "retrieval": "POST /api/v1/retrieval/retrieve",
            "retrieval_triggers": "POST /api/v1/retrieval/check-triggers",
            "retrieval_hot": "GET /api/v1/retrieval/hot-decisions",
            "drafts_create": "POST /api/v1/drafts",
            "drafts_list": "GET /api/v1/drafts",
            "drafts_pending": "GET /api/v1/drafts/pending",
            "drafts_detail": "GET /api/v1/drafts/{id}",
            "drafts_review_field": "POST /api/v1/drafts/{id}/review/{field}",
            "drafts_approve_all": "POST /api/v1/drafts/{id}/approve-all",
            "drafts_finalize": "POST /api/v1/drafts/{id}/finalize",
        },
        "constitutional_notice": {
            "ai_authority": "ZERO",
            "decision_authority": "HUMAN_ONLY",
            "immutability": "ENFORCED",
        }
    }


@app.get("/health", tags=["health"])
async def health():
    """Simple health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level=config.log_level.lower(),
    )
