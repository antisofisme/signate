# CHAT-L3-OPS-001: Deployment Guide

**Status**: Active
**Created**: 2026-01-25

---

## Overview

Step-by-step guide to deploy ARSAKA_TUTUR in various environments.

---

## Prerequisites

### Required Services
- PostgreSQL 15+
- Qdrant 1.12+
- Redis 7+

### Required API Keys
- OpenAI API Key (for embeddings and LLM)
- Cohere API Key (optional, for reranking)

### Server Requirements

| Environment | CPU | Memory | Storage |
|-------------|-----|--------|---------|
| Development | 2 cores | 4 GB | 20 GB |
| Staging | 4 cores | 8 GB | 50 GB |
| Production | 8 cores | 16 GB | 100 GB |

---

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/your-org/atlas-chat-ai.git
cd atlas-chat-ai
```

### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Dependencies

```bash
docker-compose up -d postgres qdrant redis
```

### 4. Run Migrations

```bash
cd backend
python -m pip install -r requirements.txt
python scripts/migrate.py
```

### 5. Start API

```bash
uvicorn api.main:app --reload --port 8003
```

### 6. Verify

```bash
curl http://localhost:8003/health
# Expected: {"status": "healthy", ...}
```

---

## Docker Deployment

### 1. Build Images

```bash
# Backend
docker build -t atlas-chat-api:latest ./backend

# CMS (if applicable)
docker build -t atlas-chat-cms:latest ./cms
```

### 2. Create Network

```bash
docker network create atlas-chat-network
```

### 3. Start Stack

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Run Migrations

```bash
docker-compose exec chat-api python scripts/migrate.py
```

### 5. Create Initial Tenant

```bash
docker-compose exec chat-api python scripts/seed_tenant.py \
  --id=mantra \
  --name="ARSAKA_MANTRA" \
  --prompt-file=/config/mantra_prompt.txt
```

---

## Nomad Deployment

### 1. Prerequisites

- Nomad cluster running
- Consul for service discovery
- Vault for secrets (recommended)

### 2. Store Secrets in Consul

```bash
consul kv put chat/database_url "postgresql://user:pass@db:5432/chat"
consul kv put chat/openai_api_key "sk-..."
consul kv put chat/jwt_secret "your-jwt-secret"
```

### 3. Deploy Qdrant

```bash
nomad job run nomad/chat-qdrant.nomad
```

### 4. Deploy API

```bash
nomad job run nomad/chat-api.nomad
```

### 5. Deploy Workers

```bash
nomad job run nomad/chat-worker.nomad
```

### 6. Verify Deployment

```bash
# Check job status
nomad job status chat-api

# Check allocations
nomad alloc status <alloc-id>

# Test endpoint
curl http://chat-api.service.consul:8003/health
```

---

## Database Setup

### Create Database

```sql
CREATE DATABASE atlas_chat;
CREATE USER chat_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE atlas_chat TO chat_user;

-- Connect to atlas_chat
\c atlas_chat

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO chat_user;
```

### Run Migrations

```bash
# Using psql
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_chat_tables.sql
psql $DATABASE_URL -f migrations/003_memory_tables.sql
psql $DATABASE_URL -f migrations/004_sync_tables.sql

# Or using script
python scripts/migrate.py --direction=up
```

### Verify Schema

```sql
\dt
-- Should show: tenants, chat_sessions, chat_messages, user_facts, etc.
```

---

## Qdrant Setup

### Create Collections

```bash
python scripts/init_qdrant.py --tenant=mantra
```

Or manually:

```bash
curl -X PUT http://localhost:6333/collections/mantra_documents \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

### Initial Embedding

```bash
python scripts/embed_knowledge.py \
  --tenant=mantra \
  --source=decisions \
  --batch-size=100
```

---

## SSL/TLS Configuration

### Using Traefik (Recommended)

```yaml
# traefik.yml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /acme/acme.json
      httpChallenge:
        entryPoint: web
```

### Nomad Service Tags

```hcl
service {
  tags = [
    "traefik.enable=true",
    "traefik.http.routers.chat-api.rule=Host(`chat.atlas.example.com`)",
    "traefik.http.routers.chat-api.entrypoints=websecure",
    "traefik.http.routers.chat-api.tls.certresolver=letsencrypt"
  ]
}
```

---

## Environment-Specific Notes

### Development
- Use `APP_DEBUG=true`
- Enable SQL logging with `DATABASE_ECHO=true`
- Use local Qdrant and Redis

### Staging
- Mirror production config as closely as possible
- Use separate API keys with lower quotas
- Enable all logging

### Production
- Set `APP_DEBUG=false`
- Use managed services where possible
- Enable rate limiting
- Configure alerts

---

## Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] Database migrations applied
- [ ] Qdrant collections created
- [ ] At least one tenant configured
- [ ] Initial knowledge embedded
- [ ] SSL certificates valid
- [ ] Logs flowing to aggregator
- [ ] Alerts configured
- [ ] Backup schedule verified
