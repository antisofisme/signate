# MANTRA Nomad Jobs Documentation

This document describes the Nomad job architecture for ARSAKA_MANTRA on VPS (31.97.111.175).

## Overview

MANTRA uses **6 Nomad jobs** to deploy all services in the `mantra` namespace.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MANTRA Namespace                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────────┐  ┌──────────────────┐   │
│  │ mantra-postgres │  │ mantra-qdrant-       │  │ mantra-redis     │   │
│  │                 │  │ meilisearch          │  │                  │   │
│  │ • PostgreSQL    │  │ • Qdrant (Vector)    │  │ • Redis (Cache)  │   │
│  │   Port 5434     │  │   Ports 6335-6336    │  │   Port 6380      │   │
│  │                 │  │ • Meilisearch (Text) │  │                  │   │
│  │                 │  │   Port 7700          │  │                  │   │
│  └────────┬────────┘  └──────────┬───────────┘  └────────┬─────────┘   │
│           │                      │                       │             │
│           └──────────────┬───────┴───────────────────────┘             │
│                          │                                             │
│                          ▼                                             │
│  ┌─────────────────────────────────────────┐                           │
│  │            mantra-backend               │                           │
│  │                                         │                           │
│  │  • FastAPI Backend (Port 8002)          │                           │
│  │  • Connects to all data services        │                           │
│  └─────────────────┬───────────────────────┘                           │
│                    │                                                   │
│       ┌────────────┴────────────┐                                      │
│       │                         │                                      │
│       ▼                         ▼                                      │
│  ┌─────────────────┐  ┌──────────────────────────────────────────┐    │
│  │ mantra-frontend │  │      mantra-rabbitmq-mcp-workers         │    │
│  │                 │  │                                          │    │
│  │ • React Frontend│  │  • RabbitMQ (Message Queue)              │    │
│  │   Port 3001     │  │    Ports 5672, 15672                     │    │
│  │                 │  │  • MCP Server (Port 8004)                │    │
│  │                 │  │  • Workers (validation, sync)            │    │
│  └─────────────────┘  └──────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Job Inventory

| Job Name | Services | Ports | Purpose |
|----------|----------|-------|---------|
| `mantra-postgres` | PostgreSQL | 5434 | Primary database |
| `mantra-redis` | Redis | 6380 | Cache layer |
| `mantra-qdrant-meilisearch` | Qdrant, Meilisearch | 6335-6336, 7700 | Search infrastructure |
| `mantra-backend` | FastAPI | 8002 | API server |
| `mantra-frontend` | React | 3001 | Web UI |
| `mantra-rabbitmq-mcp-workers` | RabbitMQ, MCP, Workers | 5672, 15672, 8004 | Async processing |

## Job Details

### 1. mantra-postgres
**File**: `nomad/mantra-postgres.nomad`

PostgreSQL database for persistent storage.

```bash
# Deploy
nomad job run -namespace=mantra mantra-postgres.nomad

# Status
nomad job status -namespace=mantra mantra-postgres
```

**Consul KV**:
- `mantra/db_password` - Database password

### 2. mantra-redis
**File**: `nomad/mantra-redis.nomad`

Redis cache for session and query caching.

```bash
# Deploy
nomad job run -namespace=mantra mantra-redis.nomad
```

### 3. mantra-qdrant-meilisearch
**File**: `nomad/mantra-qdrant-meilisearch.nomad`

Combined search infrastructure.

| Group | Service | Port | Function |
|-------|---------|------|----------|
| qdrant | Qdrant | 6335 (HTTP), 6336 (gRPC) | Vector similarity search |
| meilisearch | Meilisearch | 7700 | Full-text search |

```bash
# Deploy
nomad job run -namespace=mantra mantra-qdrant-meilisearch.nomad

# Status
nomad job status -namespace=mantra mantra-qdrant-meilisearch
```

**Consul KV**:
- `mantra/meilisearch_api_key` - Meilisearch master key

**Grouping Rationale**:
- Both are search-focused services
- Similar resource profiles (low CPU, moderate memory)
- Both used by backend for search operations
- Independent scaling requirements

### 4. mantra-backend
**File**: `nomad/mantra-backend.nomad`

FastAPI backend API server.

```bash
# Deploy
nomad job run -namespace=mantra mantra-backend.nomad
```

**Docker Image**: `arsaka-mantra-api:v1.5.0`

**Consul KV**:
- `mantra/db_password` - Database password
- `mantra/openai_api_key` - OpenAI API key
- `mantra/deepseek_api_key` - DeepSeek API key (optional)
- `mantra/feature_redis_enhanced` - Enable enhanced Redis caching
- `mantra/feature_meilisearch` - Enable Meilisearch
- `mantra/feature_rabbitmq` - Enable RabbitMQ

### 5. mantra-frontend
**File**: `nomad/mantra-frontend.nomad`

React frontend dashboard.

```bash
# Deploy
nomad job run -namespace=mantra mantra-frontend.nomad
```

**Docker Image**: `mantra-frontend:v1.0.0`

### 6. mantra-rabbitmq-mcp-workers
**File**: `nomad/mantra-rabbitmq-mcp-workers.nomad`

Combined async processing infrastructure.

| Group | Service | Port | Function |
|-------|---------|------|----------|
| rabbitmq | RabbitMQ | 5672 (AMQP), 15672 (Management) | Message broker |
| mcp | MCP Server | 8004 | Claude CLI integration |
| workers | Validation Worker, Sync Worker | - | Background processing |

```bash
# Deploy
nomad job run -namespace=mantra mantra-rabbitmq-mcp-workers.nomad

# Status
nomad job status -namespace=mantra mantra-rabbitmq-mcp-workers
```

**Docker Images**:
- `rabbitmq:3.12-management-alpine`
- `mantra-mcp-server:v1.0.0`
- `arsaka-mantra-api:v1.5.0` (for workers)

**Consul KV**:
- `mantra/rabbitmq_password` - RabbitMQ password

**Grouping Rationale**:
- All part of async/event processing pipeline
- Workers consume events from RabbitMQ
- MCP Server connects to backend (stateless)
- Strong dependencies and shared lifecycle

## Deployment Order

For fresh deployment, follow this order:

```bash
# 1. Data layer (no dependencies)
nomad job run -namespace=mantra mantra-postgres.nomad
nomad job run -namespace=mantra mantra-redis.nomad
nomad job run -namespace=mantra mantra-qdrant-meilisearch.nomad

# Wait for data layer to be healthy
sleep 30

# 2. Application layer (depends on data)
nomad job run -namespace=mantra mantra-backend.nomad

# Wait for backend to be healthy
sleep 15

# 3. Presentation & processing (depends on backend)
nomad job run -namespace=mantra mantra-frontend.nomad
nomad job run -namespace=mantra mantra-rabbitmq-mcp-workers.nomad
```

## Quick Reference Commands

```bash
# List all jobs
nomad job status -namespace=mantra

# Check specific job
nomad job status -namespace=mantra mantra-backend

# View logs
nomad alloc logs -namespace=mantra <alloc-id>

# Force restart
nomad job eval -force-reschedule -namespace=mantra mantra-backend

# Stop job
nomad job stop -namespace=mantra mantra-backend
```

## Feature Flags

Control service features via Consul KV:

```bash
# Enable Meilisearch
consul kv put mantra/feature_meilisearch true

# Enable RabbitMQ
consul kv put mantra/feature_rabbitmq true

# Check current flags
consul kv get mantra/feature_meilisearch
consul kv get mantra/feature_rabbitmq
```

## Migration Notes

### From Previous Structure (v1.4.x)

Old jobs that were replaced:

| Old Job | New Job |
|---------|---------|
| `mantra-qdrant` | `mantra-qdrant-meilisearch` |
| `mantra-services` (meilisearch) | `mantra-qdrant-meilisearch` |
| `mantra-services` (rabbitmq) | `mantra-rabbitmq-mcp-workers` |
| `mantra-mcp` | `mantra-rabbitmq-mcp-workers` |

To migrate:

```bash
# Stop old jobs
nomad job stop -namespace=mantra mantra-qdrant
nomad job stop -namespace=mantra mantra-services
nomad job stop -namespace=mantra mantra-mcp

# Deploy new combined jobs
nomad job run -namespace=mantra mantra-qdrant-meilisearch.nomad
nomad job run -namespace=mantra mantra-rabbitmq-mcp-workers.nomad
```

## Data Persistence

All stateful services use persistent volumes:

| Service | Volume Path |
|---------|-------------|
| PostgreSQL | `/opt/arsaka-mantra/data/postgres` |
| Redis | `/opt/arsaka-mantra/data/redis` |
| Qdrant | `/opt/arsaka-mantra/data/qdrant` |
| Meilisearch | `/opt/arsaka-mantra/data/meilisearch` |
| RabbitMQ | `/opt/arsaka-mantra/data/rabbitmq` |

## Troubleshooting

### Service not starting

1. Check job status:
   ```bash
   nomad job status -namespace=mantra <job-name>
   ```

2. Get allocation ID and check logs:
   ```bash
   nomad alloc logs -namespace=mantra <alloc-id>
   ```

3. Check if Docker image exists:
   ```bash
   docker images | grep mantra
   ```

### Port conflicts

Check if ports are in use:
```bash
ss -tlnp | grep -E '(5434|6380|6335|6336|7700|8002|3001|5672|8004)'
```

### Consul KV issues

Verify keys are set:
```bash
consul kv get -recurse mantra/
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.5.0 | 2026-01 | Combined Nomad jobs, added Meilisearch/RabbitMQ integration |
| 1.4.0 | 2025-12 | Initial semantic search with Qdrant |
| 1.0.0 | 2025-11 | Basic PostgreSQL + Redis deployment |
