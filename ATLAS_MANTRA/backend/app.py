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
from core.runtime.config import get_config


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

    yield

    # Shutdown
    print(f"[{datetime.utcnow().isoformat()}] ATLAS_MANTRA shutting down...")


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
| INT | Intent & Direction | F-01, F-02, F-03, F-04 |
| ARCH | Architecture & Boundaries | F-05, F-06, F-07, F-08 |
| CTL | Control, Policy & Risk | F-09, F-10, F-11, F-12 |
| EVO | Execution & Evolution | F-13, F-14, F-15, F-16 |

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
