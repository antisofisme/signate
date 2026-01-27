# ATLAS_MANTRA

**Decision Matrix Constitutional Law System**

## Overview

ATLAS_MANTRA is a constitutional governance framework for enterprise decision management. It implements a 4-layer governance architecture with immutable decisions and strict human authority.

## Constitutional Principles

Per **MANTRA-LAW-001**:

| Principle | Value |
|-----------|-------|
| AI Authority | **ZERO** |
| Decision Authority | **HUMAN ONLY** |
| Immutability | **ENFORCED** |

## Architecture

```
ATLAS_MANTRA/
├── docs/                    # Constitutional Law & Specifications
│   ├── layer-0/            # Constitutional Law (LOCKED)
│   ├── layer-1/            # Implementation Specifications (FROZEN)
│   ├── layer-2/            # Technical Architecture (FROZEN)
│   └── layer-3/            # Operational Guidelines (Boundary FROZEN)
│
├── backend/                 # FastAPI Implementation
│   ├── core/               # Core business logic
│   │   ├── api/           # HTTP routing
│   │   ├── domain/        # Decision aggregate
│   │   ├── repositories/  # Data access
│   │   ├── use_cases/     # Business operations
│   │   └── runtime/       # Configuration
│   ├── infrastructure/    # Infrastructure layer
│   └── migrations/        # Database schemas
│
├── frontend/               # React + Vite UI
│   └── src/
│       ├── components/    # UI components
│       ├── pages/         # Page components
│       └── shared/        # Shared utilities
│
├── docker/                 # Docker configurations
│   └── docker-compose.yml
│
└── nomad/                  # Nomad job definitions
    ├── mantra-backend.nomad
    └── mantra-postgres.nomad
```

## Layer Hierarchy

| Layer | Purpose | Status |
|-------|---------|--------|
| Layer 0 | Constitutional Law | **LOCKED** |
| Layer 1 | Implementation Specifications | **FROZEN** |
| Layer 2 | Technical Architecture | **FROZEN** |
| Layer 3 | Operational Guidelines | **Boundary FROZEN** |

**Precedence**: Layer 0 > Layer 1 > Layer 2 > Layer 3

## Core Services

Implemented per Layer 1 specifications:

| Service | Endpoint | Specification |
|---------|----------|---------------|
| Validator | `POST /api/v1/validate` | MANTRA-L1-IMPL-VALIDATOR-001 |
| Decision Store | `POST /api/v1/decisions` | MANTRA-L1-IMPL-DECISION-STORE-001 |
| Public Read API | `GET /api/v1/decisions` | MANTRA-L1-IMPL-PUBLIC-READ-API-001 |

## Decision Taxonomy

**4 Groups × 4 Features = 16 Decision Categories**

### Group Mapping (Code → MANTRA-LAW-001)

| Code | Law Ref | Full Name | Scope | Question Answered |
|------|---------|-----------|-------|-------------------|
| **INT** | GROUP-1, §3.2 | Intent & Direction | WHY / WHAT | "Mengapa kita melakukan ini?" |
| **ARCH** | GROUP-2, §3.3 | Architecture & Boundaries | HOW / WHERE | "Bagaimana strukturnya?" |
| **CTL** | GROUP-3, §3.4 | Control, Policy & Risk | CAN / MUST NOT | "Apa yang boleh/dilarang?" |
| **EVO** | GROUP-4, §3.5 | Execution & Evolution | CHANGE SAFELY | "Bagaimana berubah aman?" |

### Feature Mapping

| Group | Feature | Label |
|-------|---------|-------|
| **INT** | F01 | Vision & Outcome |
| | F02 | Problem Statement |
| | F03 | Scope & Non-Goals |
| | F04 | Principles & Values |
| **ARCH** | F05 | Domain & Bounded Context |
| | F06 | Service & Module Boundary |
| | F07 | Data Ownership & Sovereignty |
| | F08 | Integration & Contract Model |
| **CTL** | F09 | Policy & Rules |
| | F10 | Approval & Authority Model |
| | F11 | Security & Compliance Posture |
| | F12 | Risk & Blast Radius |
| **EVO** | F13 | Decision Lifecycle |
| | F14 | Reversibility & Exit Strategy |
| | F15 | Environment & Promotion Rules |
| | F16 | Anti-Drift & Consistency |

### Decision Code Format

Format: `{GROUP}-{FEATURE}-{SEQ}-v{VERSION}`

Example: `INT-F01-001-v1.0.0`

## Validation Rules

47 validation rules across 3 levels:

| Level | Rules | Scope |
|-------|-------|-------|
| Level 1 (Schema) | S-001 to S-022 | Structural conformance |
| Level 2 (Consistency) | D-001 to D-014 | Semantic conformance |
| Level 3 (Law Compliance) | L-001 to L-011 | Authority conformance |

## Quick Start

### Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

### Docker

```bash
cd docker
cp .env.example .env
docker-compose up -d
```

Access:
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Frontend**: http://localhost:3000

### Nomad

```bash
# Create namespace
nomad namespace apply mantra

# Deploy
nomad job run nomad/mantra-postgres.nomad
nomad job run nomad/mantra-backend.nomad
```

## API Examples

### Validate a Decision

```bash
curl -X POST http://localhost:8001/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "record": {
      "decision_id": "550e8400-e29b-41d4-a716-446655440000",
      "group_id": "INT",
      "feature_id": "F01",
      "statement": "All authentication must use MFA",
      "rationale": "Security requirement",
      "constraints": [],
      "invariants": [],
      "scope": "ORGANIZATION",
      "blast_radius": "HIGH",
      "status": "PROPOSED",
      "version": "1.0.0"
    }
  }'
```

### Get Decision Matrix

```bash
curl http://localhost:8001/api/v1/matrix
```

## Compliance

This implementation complies with:

- MANTRA-LAW-001 (Constitutional Law)
- MANTRA-SCHEMA-001 (JSON Schema v1)
- MANTRA-SPEC-001 (Validator Specification)
- MANTRA-L1-IMPL-* (Layer 1 Implementation Specifications)
- MANTRA-L2-IMPL-* (Layer 2 Architecture Specifications)
- MANTRA-LAYER-3-BOUNDARY-001 (Operational Boundaries)

## License

Proprietary. Human decision authority required for all usage.

---

**ATLAS_MANTRA** - Constitutional Governance for Enterprise Decisions
