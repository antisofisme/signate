# CHAT-L1-ARCH-002: Tech Stack Selection

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-005

---

## Context

Memilih tech stack yang:
1. Production-ready untuk 2025-2026
2. Dapat diganti (no vendor lock-in)
3. Cost-effective
4. Self-hostable
5. **Memory-efficient** (target: < 1.5GB RAM)

---

## Decision

### Lean Stack (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                       LEAN STACK                             │
│                  Total RAM: 500MB - 1.2GB                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    PostgreSQL 15+                       │ │
│  │  + pg_trgm (fuzzy text search)                         │ │
│  │  + Full-Text Search (keyword search)                   │ │
│  │  + JSONB (graph-like relationships)                    │ │
│  │  + pgvector (optional vector backup)                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌──────────────┐    ┌──────┴───────┐                       │
│  │    Qdrant    │    │    Redis     │                       │
│  │   (Vectors)  │    │ (Cache +     │                       │
│  │              │    │  Job Queue)  │                       │
│  └──────────────┘    └──────────────┘                       │
│                                                              │
│  Services: 3  │  RAM: ~1GB  │  VPS: $5-10/mo               │
└─────────────────────────────────────────────────────────────┘
```

### Primary Stack

| Component | Selection | RAM | Rationale |
|-----------|-----------|-----|-----------|
| **Backend** | FastAPI | - | Async, typed, existing expertise |
| **Primary DB** | PostgreSQL 15+ | 200-500 MB | ACID, extensions, existing |
| **Vector DB** | Qdrant | 200-500 MB | Self-hosted, Rust performance |
| **Cache + Queue** | Redis | 50-200 MB | Cache + Streams for job queue |
| **Full-Text** | PostgreSQL FTS | 0 | Built-in, no extra service |
| **Fuzzy Search** | pg_trgm | 0 | Extension, typo-tolerant |
| **Relationships** | PostgreSQL JSONB | 0 | Graph-like without graph DB |
| **Embedding** | OpenAI | - | text-embedding-3-small |
| **LLM** | OpenAI/DeepSeek | - | Multi-provider |
| **Streaming** | SSE | - | Browser native |

### Extended Stack (Scale-Up Only)

Tambahkan HANYA jika benar-benar butuh:

| Condition | Add | Why |
|-----------|-----|-----|
| 100k+ documents, faceted search | Meilisearch | PostgreSQL FTS lambat di scale ini |
| Complex graph (5+ hop traversal) | ArangoDB | JSONB tidak efisien untuk deep traversal |
| 10k+ jobs/second | RabbitMQ | Redis Streams bottleneck |
| Multi-region file storage | MinIO | Local filesystem tidak distributed |

---

## Stack Details

### 1. PostgreSQL Extensions

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- Fuzzy search
CREATE EXTENSION IF NOT EXISTS pgvector;      -- Vector backup (optional)

-- Full-Text Search setup
ALTER TABLE documents ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
    ) STORED;

CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);

-- Trigram index for fuzzy search
CREATE INDEX idx_documents_trgm ON documents USING GIN(content gin_trgm_ops);
```

**Hybrid Search Query:**
```sql
-- Combine FTS + Trigram for robust search
SELECT id, content,
    ts_rank(search_vector, query) AS fts_score,
    similarity(content, $1) AS trgm_score
FROM documents,
    plainto_tsquery('english', $1) query
WHERE search_vector @@ query
   OR content % $1
ORDER BY (ts_rank(search_vector, query) + similarity(content, $1)) DESC
LIMIT 10;
```

### 2. Vector Database: Qdrant

```yaml
# docker-compose.yml
qdrant:
  image: qdrant/qdrant:v1.12.0
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
  environment:
    QDRANT__LOG_LEVEL: INFO
  deploy:
    resources:
      limits:
        memory: 512M
```

**Why Qdrant**:
- Single Docker container
- Rust performance (low memory)
- Rich filtering
- Free and open source

### 3. Redis: Cache + Job Queue

```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  deploy:
    resources:
      limits:
        memory: 256M
```

**Job Queue dengan Redis Streams:**
```python
import redis.asyncio as redis

class RedisJobQueue:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def publish(self, queue: str, job: dict) -> str:
        """Add job to queue"""
        job_id = await self.redis.xadd(
            f"queue:{queue}",
            {"data": json.dumps(job)}
        )
        return job_id

    async def consume(self, queue: str, group: str, consumer: str):
        """Consume jobs from queue"""
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(f"queue:{queue}", group, mkstream=True)
        except redis.ResponseError:
            pass  # Group exists

        while True:
            messages = await self.redis.xreadgroup(
                group, consumer,
                {f"queue:{queue}": ">"},
                count=1, block=5000
            )
            for stream, msgs in messages:
                for msg_id, data in msgs:
                    yield msg_id, json.loads(data[b"data"])

    async def ack(self, queue: str, group: str, msg_id: str):
        """Acknowledge job completion"""
        await self.redis.xack(f"queue:{queue}", group, msg_id)
```

### 4. Graph-like Relationships (PostgreSQL)

```sql
-- Entity storage
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(200) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- person, project, technology, company
    name VARCHAR(500) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entities_tenant_user ON entities(tenant_id, user_id);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_name_trgm ON entities USING GIN(name gin_trgm_ops);

-- Relationships between entities
CREATE TABLE entity_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    from_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    to_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,  -- works_on, knows, uses, manages
    properties JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    source_session_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(from_entity_id, to_entity_id, relation_type)
);

CREATE INDEX idx_relations_from ON entity_relations(from_entity_id);
CREATE INDEX idx_relations_to ON entity_relations(to_entity_id);
CREATE INDEX idx_relations_type ON entity_relations(relation_type);
```

**Graph Queries (SQL):**
```sql
-- Find all entities user is connected to (1 hop)
SELECT e.*, r.relation_type
FROM entities e
JOIN entity_relations r ON r.to_entity_id = e.id
WHERE r.from_entity_id = (
    SELECT id FROM entities
    WHERE tenant_id = $1 AND user_id = $2 AND entity_type = 'user'
);

-- Find entities through 2 hops (user -> project -> technology)
WITH user_projects AS (
    SELECT to_entity_id AS project_id
    FROM entity_relations
    WHERE from_entity_id = $1 AND relation_type = 'works_on'
)
SELECT e.*, 'uses' AS relation
FROM entities e
JOIN entity_relations r ON r.to_entity_id = e.id
WHERE r.from_entity_id IN (SELECT project_id FROM user_projects)
AND e.entity_type = 'technology';
```

### 5. File Storage (Local + Upgrade Path)

```python
# Simple local storage - upgrade to MinIO/S3 later if needed
from pathlib import Path
import aiofiles

class LocalFileStorage:
    def __init__(self, base_path: str = "/data/uploads"):
        self.base_path = Path(base_path)

    async def put(
        self,
        tenant_id: str,
        file_id: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        path = self.base_path / tenant_id / file_id
        path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(path, 'wb') as f:
            await f.write(data)

        return str(path)

    async def get(self, tenant_id: str, file_id: str) -> bytes:
        path = self.base_path / tenant_id / file_id
        async with aiofiles.open(path, 'rb') as f:
            return await f.read()

    async def delete(self, tenant_id: str, file_id: str) -> bool:
        path = self.base_path / tenant_id / file_id
        if path.exists():
            path.unlink()
            return True
        return False
```

---

## Embedding & LLM Providers

### Embedding: OpenAI text-embedding-3-small

```python
EMBEDDING_PROVIDERS = {
    "openai": {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "cost_per_1m": 0.02
    },
    "openai-large": {
        "model": "text-embedding-3-large",
        "dimensions": 3072,
        "cost_per_1m": 0.13
    },
    "local": {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimensions": 384,
        "cost_per_1m": 0  # Free, but need resources
    }
}
```

### LLM Providers (Multi-provider)

```python
LLM_PROVIDERS = {
    "openai": {
        "default_model": "gpt-4o-mini",
        "advanced_model": "gpt-4o",
    },
    "deepseek": {
        "default_model": "deepseek-chat",
        "reasoning_model": "deepseek-reasoner"
    },
    "groq": {
        "default_model": "llama-3.3-70b-versatile",
        "fast_model": "llama-3.1-8b-instant"
    }
}
```

---

## Docker Compose (Complete)

```yaml
version: '3.8'

services:
  # === CORE SERVICES (Required) ===

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: chat
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: atlas_chat
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    deploy:
      resources:
        limits:
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chat"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:v1.12.0
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__LOG_LEVEL: INFO
    deploy:
      resources:
        limits:
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    deploy:
      resources:
        limits:
          memory: 256M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # === APPLICATION ===

  chat-api:
    build: ./backend
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql://chat:${POSTGRES_PASSWORD}@postgres:5432/atlas_chat
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 512M

  chat-worker:
    build: ./backend
    command: python -m workers.main
    environment:
      - DATABASE_URL=postgresql://chat:${POSTGRES_PASSWORD}@postgres:5432/atlas_chat
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - qdrant
      - redis
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
```

**init.sql:**
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE atlas_chat TO chat;
```

---

## Resource Summary

| Service | RAM Limit | Typical Usage |
|---------|-----------|---------------|
| PostgreSQL | 512 MB | 200-400 MB |
| Qdrant | 512 MB | 200-400 MB |
| Redis | 256 MB | 50-150 MB |
| chat-api | 512 MB | 200-400 MB |
| chat-worker | 256 MB | 100-200 MB |
| **TOTAL** | **2 GB** | **~1 GB** |

**Minimum VPS**: 2 GB RAM, 2 vCPU, 40 GB SSD (~$10/month)

---

## Cost Estimates

### Infrastructure (Monthly)

| Option | Spec | Cost |
|--------|------|------|
| DigitalOcean | 2GB/2vCPU | $18 |
| Hetzner | 4GB/2vCPU | $4.5 |
| Contabo | 4GB/4vCPU | $6 |

### API Usage (Per 1000 Messages)

| Component | Cost |
|-----------|------|
| Embedding (queries) | $0.0001 |
| GPT-4o-mini (avg 500 tokens) | $0.30 |
| **Total** | **~$0.30** |

---

## Migration Paths

### Scale Up: Add Meilisearch

```bash
# When PostgreSQL FTS becomes slow (100k+ docs)
# 1. Add Meilisearch to docker-compose
# 2. Create MeilisearchAdapter implementing TextSearch interface
# 3. Update config: TEXT_SEARCH=meilisearch
# 4. Index existing documents
# 5. Restart
```

### Scale Up: Add ArangoDB

```bash
# When graph queries become complex (5+ hops)
# 1. Add ArangoDB to docker-compose
# 2. Create ArangoDBAdapter implementing GraphStore interface
# 3. Migrate entity_relations to ArangoDB
# 4. Update config: GRAPH_STORE=arangodb
# 5. Restart
```

### Scale Up: Add RabbitMQ

```bash
# When Redis Streams bottleneck (10k+ jobs/sec)
# 1. Add RabbitMQ to docker-compose
# 2. Create RabbitMQAdapter implementing MessageQueue interface
# 3. Update config: MESSAGE_QUEUE=rabbitmq
# 4. Restart workers
```

---

## Consequences

### Positive
- **Low resource usage** (~1GB RAM total)
- **Simple deployment** (3 services)
- **Low cost** ($5-10/month VPS)
- **Easy maintenance** (fewer moving parts)
- **Still modular** (can scale up when needed)

### Negative
- PostgreSQL FTS slower than dedicated search (acceptable for < 100k docs)
- No complex graph traversal (acceptable for most chat use cases)
- Redis Streams less feature-rich than RabbitMQ (acceptable for this scale)

---

## Quick Reference

```bash
# Development
docker-compose up -d

# Check health
curl http://localhost:8003/health
curl http://localhost:6333/health
redis-cli ping

# Logs
docker-compose logs -f chat-api

# Resource usage
docker stats
```
