# ARSAKA_MANTRA Backend

**TYPE**: Decision Matrix Constitutional Law System
**ARCHITECTURE**: Clean Architecture + FastAPI
**GOVERNING LAW**: MANTRA-LAW-001

---

## Architecture Overview

This backend implements the 3 core services defined in Layer 1 specifications:

| Service | Specification | Purpose |
|---------|---------------|---------|
| Validator | MANTRA-L1-IMPL-VALIDATOR-001 | Validates decision entries against schema |
| Decision Store | MANTRA-L1-IMPL-DECISION-STORE-001 | Immutable storage of validated decisions |
| Public Read API | MANTRA-L1-IMPL-PUBLIC-READ-API-001 | Read-only access to stored decisions |

---

## Folder Structure

```
backend/
├── core/                    # CORE (Permanent, cannot break)
│   ├── api/                 # HTTP routing (FastAPI)
│   │   ├── __init__.py
│   │   ├── routes.py        # API route definitions
│   │   └── dependencies.py  # Request dependencies
│   ├── domain/              # Business logic
│   │   ├── __init__.py
│   │   ├── decision.py      # Decision aggregate
│   │   ├── schema.py        # MANTRA-SCHEMA-001 implementation
│   │   └── events.py        # Domain events
│   ├── repositories/        # Data access abstractions
│   │   ├── __init__.py
│   │   └── decision_repository.py
│   ├── use_cases/           # Business orchestration
│   │   ├── __init__.py
│   │   ├── validate_decision.py
│   │   ├── store_decision.py
│   │   └── read_decision.py
│   └── runtime/             # Configuration
│       ├── __init__.py
│       └── config.py
├── infrastructure/          # Infrastructure layer
│   ├── database/
│   │   ├── __init__.py
│   │   └── postgres.py
│   └── logging/
│       ├── __init__.py
│       └── logger.py
├── migrations/              # Database schemas
│   ├── 001_initial_schema.sql
│   └── 002_immutability_triggers.sql
├── shared/                  # Shared utilities
│   ├── __init__.py
│   └── exceptions.py
├── tests/                   # Test suite
│   └── __init__.py
├── app.py                   # FastAPI entry point
├── requirements.txt         # Python dependencies
└── Dockerfile               # Container build
```

---

## Core Principles

### 1. AI Authority = ZERO

Per MANTRA-LAW-001 §6:
- AI MUST NOT validate decisions
- AI MUST NOT approve decisions
- AI MUST NOT trigger storage
- AI output is NEVER authoritative

### 2. Decision Immutability

Per MANTRA-LAW-001 §10:
- Stored decisions MUST NOT be modified
- Stored decisions MUST NOT be deleted
- All modifications are INVALID

### 3. Schema Compliance

Per MANTRA-SCHEMA-001:
- All decisions MUST validate against JSON schema
- Invalid decisions MUST be rejected
- Validation is synchronous and atomic

---

## Services

### Validator Service

Validates decision entries against MANTRA-SCHEMA-001.

**Endpoint**: `POST /api/v1/validate`

**Input**: Decision entry JSON
**Output**: Validation result (valid/invalid with errors)

**Guarantees**:
- Synchronous validation
- Atomic operation
- No partial validation

### Decision Store Service

Stores validated decisions immutably.

**Endpoint**: `POST /api/v1/decisions`

**Input**: Pre-validated decision entry
**Output**: Storage confirmation with decision ID

**Guarantees**:
- Write-once semantics
- Append-only storage
- Audit trail

### Public Read API

Read-only access to stored decisions.

**Endpoint**: `GET /api/v1/decisions`
**Endpoint**: `GET /api/v1/decisions/{id}`

**Output**: Decision entries (read-only)

**Guarantees**:
- Read-only access
- No modification capability
- Eventual consistency acceptable

---

## Running the Backend

### Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

### Docker

```bash
# Build
docker build -t arsaka-mantra-api .

# Run
docker run -p 8001:8001 arsaka-mantra-api
```

---

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection | postgresql://... |
| LOG_LEVEL | Logging level | INFO |
| API_PREFIX | API route prefix | /api/v1 |

---

## Compliance

This implementation complies with:
- MANTRA-LAW-001 (Constitutional Law)
- MANTRA-SCHEMA-001 (JSON Schema)
- MANTRA-L1-IMPL-VALIDATOR-001 (Validator Specification)
- MANTRA-L1-IMPL-DECISION-STORE-001 (Store Specification)
- MANTRA-L1-IMPL-PUBLIC-READ-API-001 (Read API Specification)
- MANTRA-L2-IMPL-RUNTIME-TOPOLOGY-001 (Runtime Topology)
- MANTRA-L2-IMPL-DATA-FLOW-001 (Data Flow)
- MANTRA-L2-IMPL-FAILURE-SURFACES-001 (Failure Surfaces)

---

**END OF README**
