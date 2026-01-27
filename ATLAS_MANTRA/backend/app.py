"""
ATLAS_MANTRA FastAPI Application

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
from core.runtime.config import get_config
from factory.container import Container


# ============================================================================
# Application Setup
# ============================================================================

config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"[{datetime.utcnow().isoformat()}] ATLAS_MANTRA starting...")
    print(f"  - Host: {config.host}")
    print(f"  - Port: {config.port}")
    print(f"  - CORS: {config.cors_origins_list}")
    print(f"  - Docs: {'enabled' if config.enable_docs else 'disabled'}")
    print(f"  - Semantic Search: {'enabled' if config.enable_semantic_search else 'disabled'}")
    print(f"  - Vector Store: {config.vector_store}")
    print(f"  - Cache: {config.cache}")
    print(f"  - Embedding: {config.embedding_service}")

    # Initialize all services (repository, vector store, cache, embedding)
    await Container.initialize()
    print(f"  - Container initialized")

    yield

    # Shutdown
    print(f"[{datetime.utcnow().isoformat()}] ATLAS_MANTRA shutting down...")
    await Container.close_all()


app = FastAPI(
    title="ATLAS_MANTRA",
    description="""
## Decision Matrix Constitutional Law System

ATLAS_MANTRA provides a constitutional governance framework for decision management.

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


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "ATLAS_MANTRA",
        "version": "1.0.0",
        "description": "Decision Matrix Constitutional Law System",
        "governing_law": "MANTRA-LAW-001",
        "api_docs": "/docs" if config.enable_docs else None,
        "health": "/api/v1/health",
        "endpoints": {
            "validate": "POST /api/v1/validate",
            "decisions": "GET/POST /api/v1/decisions",
            "matrix": "GET /api/v1/matrix",
            "ai_chat": "POST /api/v1/ai/chat",
            "ai_hints": "POST /api/v1/ai/hints",
            "api_keys": "GET/POST /api-keys",
            "semantic_search": "POST /api/v1/search/semantic",
            "check_alignment": "POST /api/v1/search/check-alignment",
            "rebuild_index": "POST /api/v1/search/rebuild-index",
            "search_stats": "GET /api/v1/search/stats",
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
