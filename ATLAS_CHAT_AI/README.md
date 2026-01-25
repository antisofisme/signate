# ATLAS_CHAT_AI

Advanced AI Chat System with RAG, Memory Management, and Multi-Tenant Support.

## Overview

ATLAS_CHAT_AI adalah sistem chat AI yang dapat di-attach ke berbagai project ATLAS (MANTRA, PUGUH, PANDAWA, dll). Dibangun dengan arsitektur modular yang memudahkan penggantian komponen.

## Key Features

- **RAG (Retrieval-Augmented Generation)**: Semantic search over knowledge bases
- **4-Layer Memory System**: Working, Episodic, Semantic, Temporal
- **Multi-Tenant**: Isolated data and configuration per tenant
- **Modular Architecture**: Swappable components (Vector DB, LLM, Embedder)
- **Streaming Responses**: Real-time SSE streaming
- **CMS**: Admin interface for tenant management

## Documentation

Documentation is organized in layers following constitutional law pattern:

| Layer | Purpose | Path |
|-------|---------|------|
| **Layer 0** | Immutable Laws | `docs/layer-0/` |
| **Layer 1** | Architecture Decisions | `docs/layer-1/` |
| **Layer 2** | Implementation Specs | `docs/layer-2/` |
| **Layer 3** | Operational Guidelines | `docs/layer-3/` |

### Quick Links

- [Why CHAT_AI?](docs/value/VALUE-001-why-chat-ai.md)
- [Quick Start Guide](docs/guides/GUIDE-001-quick-start.md)
- [Constitutional Laws](docs/layer-0/README.md)
- [Architecture Decisions](docs/layer-1/README.md)
- [Database Schema](docs/layer-2/CHAT-L2-SPEC-001-database-schema.md)
- [API Endpoints](docs/layer-2/CHAT-L2-SPEC-002-api-endpoints.md)
- [Deployment Guide](docs/layer-3/CHAT-L3-OPS-001-deployment.md)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11 + FastAPI |
| Vector Database | Qdrant |
| Primary Database | PostgreSQL 15+ |
| Cache | Redis |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | OpenAI, DeepSeek, Claude, Groq |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- OpenAI API Key

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/atlas-chat-ai.git
cd atlas-chat-ai
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Run Migrations

```bash
python scripts/migrate.py
```

### 4. Create Tenant

```bash
python scripts/seed_tenant.py --id=mantra --name="ATLAS_MANTRA"
```

### 5. Test

```bash
curl -X POST http://localhost:8003/api/v1/chat/sync \
  -H "X-Tenant-ID: mantra" \
  -d '{"message": "Hello"}'
```

## Project Structure

```
ATLAS_CHAT_AI/
├── docs/                    # Documentation (Layer 0-3)
├── backend/                 # FastAPI Backend
│   ├── core/               # Domain layer (interfaces, entities, services)
│   ├── infrastructure/     # Adapters, repositories, external clients
│   ├── api/                # HTTP routes, middleware
│   └── workers/            # Background jobs
├── cms/                     # Admin CMS (optional)
├── sdk/                     # Client SDKs
├── docker/                  # Docker configs
├── nomad/                   # Nomad job files
└── scripts/                 # Utility scripts
```

## Core Laws

1. **Modular Architecture**: All components are swappable
2. **Interface-First Design**: Access through abstract interfaces
3. **Memory Hierarchy**: 4-layer memory system
4. **Multi-Tenant Isolation**: Absolute data isolation
5. **No Vendor Lock-in**: Can migrate vendors anytime
6. **Append-Only History**: Chat history is immutable

See [Layer 0 Documentation](docs/layer-0/README.md) for complete laws.

## Contributing

1. Read the [Layer 0 Laws](docs/layer-0/README.md) - all code must comply
2. Follow the [Project Structure](docs/layer-1/CHAT-L1-ARCH-006-project-structure.md)
3. Write tests for new features
4. Submit PR with description referencing relevant decisions

## License

[Your License Here]
