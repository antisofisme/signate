# CHAT-L3-OPS-004: Tenant Onboarding Guide

**Status**: Active
**Created**: 2026-01-25

---

## Overview

Step-by-step guide to onboard a new project as a tenant of ARSAKA_TUTUR.

---

## Prerequisites

Before onboarding:
- [ ] Tenant has decided on AI provider (OpenAI, DeepSeek, etc.)
- [ ] System prompt is drafted
- [ ] Knowledge sources identified
- [ ] API keys available

---

## Step 1: Create Tenant Configuration

### Option A: Using Script

```bash
python scripts/seed_tenant.py \
  --id=pandawa \
  --name="ARSAKA_PANDAWA" \
  --llm-provider=openai \
  --llm-model=gpt-4o-mini \
  --embedding-provider=openai \
  --rag-strategy=hybrid \
  --prompt-file=/config/pandawa_prompt.txt
```

### Option B: Using API

```bash
curl -X POST http://localhost:8003/api/v1/admin/tenants \
  -H "Authorization: Bearer $ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "pandawa",
    "name": "ARSAKA_PANDAWA",
    "description": "Enterprise Hospitality Platform",
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4o-mini"
    },
    "embedding_config": {
      "provider": "openai",
      "model": "text-embedding-3-small"
    },
    "rag_config": {
      "strategy": "hybrid",
      "reranker_enabled": true
    },
    "system_prompt": "You are a hospitality assistant...",
    "persona_name": "Hospitality Assistant"
  }'
```

### Option C: Using CMS

1. Navigate to `/admin/tenants/new`
2. Fill in tenant details
3. Upload system prompt
4. Configure AI settings
5. Click "Create Tenant"

---

## Step 2: Create Qdrant Collections

```bash
python scripts/init_qdrant.py --tenant=pandawa
```

Or manually:

```bash
# Documents collection
curl -X PUT http://localhost:6333/collections/pandawa_documents \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {"size": 1536, "distance": "Cosine"}
  }'

# Sessions collection
curl -X PUT http://localhost:6333/collections/pandawa_sessions \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {"size": 1536, "distance": "Cosine"}
  }'

# Facts collection
curl -X PUT http://localhost:6333/collections/pandawa_facts \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {"size": 1536, "distance": "Cosine"}
  }'
```

Verify:
```bash
curl http://localhost:6333/collections | jq '.result.collections[].name'
# Should include: pandawa_documents, pandawa_sessions, pandawa_facts
```

---

## Step 3: Configure Knowledge Sources

### Database Source

```bash
curl -X POST http://localhost:8003/api/v1/admin/knowledge-sources \
  -H "Authorization: Bearer $ADMIN_API_KEY" \
  -H "X-Tenant-ID: pandawa" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "database",
    "source_name": "reservations",
    "connection_config": {
      "connection_string": "postgresql://user:pass@pandawa-db:5432/pandawa",
      "table": "reservations",
      "fields": ["reservation_number", "guest_name", "room_type", "check_in", "check_out"],
      "filter": "status = '\''confirmed'\''"
    },
    "chunking_strategy": "fixed",
    "chunk_size": 500,
    "sync_interval": 5
  }'
```

### API Source

```bash
curl -X POST http://localhost:8003/api/v1/admin/knowledge-sources \
  -H "Authorization: Bearer $ADMIN_API_KEY" \
  -H "X-Tenant-ID: pandawa" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "api",
    "source_name": "room_rates",
    "connection_config": {
      "url": "https://api.pandawa.com/rates",
      "method": "GET",
      "headers": {"Authorization": "Bearer {{api_key}}"}
    },
    "sync_interval": 60
  }'
```

---

## Step 4: Initial Knowledge Sync

### Trigger Manual Sync

```bash
curl -X POST http://localhost:8003/api/v1/admin/embed \
  -H "Authorization: Bearer $ADMIN_API_KEY" \
  -H "X-Tenant-ID: pandawa" \
  -d '{
    "source": "reservations",
    "full_reindex": true
  }'
```

### Monitor Sync Progress

```bash
curl http://localhost:8003/api/v1/admin/embed/JOB_ID \
  -H "Authorization: Bearer $ADMIN_API_KEY" \
  -H "X-Tenant-ID: pandawa"
```

### Verify Embedding

```bash
# Check vector count
curl http://localhost:6333/collections/pandawa_documents | jq '.result.points_count'

# Test search
curl -X POST http://localhost:8003/api/v1/search \
  -H "X-Tenant-ID: pandawa" \
  -d '{"query": "room availability", "top_k": 3}'
```

---

## Step 5: Test Chat

### Basic Test

```bash
curl -X POST http://localhost:8003/api/v1/chat/sync \
  -H "X-Tenant-ID: pandawa" \
  -H "Authorization: Bearer $TEST_USER_TOKEN" \
  -d '{"message": "What rooms are available?"}'
```

### Verify Response

Check that:
- [ ] Response uses correct persona
- [ ] Retrieved documents are relevant
- [ ] No cross-tenant data leakage

---

## Step 6: Integration with Client Project

### Option A: Direct API

```python
# In PANDAWA backend
import httpx

class ChatService:
    def __init__(self):
        self.base_url = "http://chat-api:8003/api/v1"
        self.tenant_id = "pandawa"

    async def chat(self, message: str, user_id: str, session_id: str = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat",
                headers={
                    "X-Tenant-ID": self.tenant_id,
                    "Authorization": f"Bearer {self._get_token(user_id)}"
                },
                json={
                    "message": message,
                    "session_id": session_id
                }
            )
            return response.json()
```

### Option B: SDK

```python
# Install SDK
pip install atlas-chat-sdk

# Use SDK
from atlas_chat import ChatClient

client = ChatClient(
    base_url="http://chat-api:8003",
    tenant_id="pandawa",
    api_key="tenant-api-key"
)

# Chat
response = await client.chat(
    message="Check room availability",
    user_id="user-123"
)
```

### Option C: Frontend Widget

```typescript
// In PANDAWA frontend
import { FloatingChat } from '@atlas/chat-widget';

function App() {
  return (
    <div>
      {/* Your app */}
      <FloatingChat
        endpoint="https://chat.atlas.example.com/api/v1"
        tenantId="pandawa"
        userToken={userToken}
      />
    </div>
  );
}
```

---

## Step 7: Configure Monitoring

### Add Tenant Dashboard

1. Go to Grafana
2. Duplicate "Chat Overview" dashboard
3. Add tenant filter: `tenant_id="pandawa"`
4. Save as "PANDAWA Chat Dashboard"

### Set Up Alerts

```yaml
# Add to alertmanager
route:
  routes:
    - match:
        tenant_id: pandawa
      receiver: pandawa-team

receivers:
  - name: pandawa-team
    slack_configs:
      - channel: '#pandawa-alerts'
```

---

## Step 8: Documentation & Handover

### Provide to Tenant Team

1. **API Documentation**
   - Endpoint reference
   - Authentication guide
   - Rate limits

2. **Integration Examples**
   - Python SDK usage
   - Frontend widget setup
   - Webhook configuration

3. **Support Contacts**
   - Slack channel for issues
   - Escalation path

### Checklist

- [ ] Tenant created in database
- [ ] Qdrant collections created
- [ ] Knowledge sources configured
- [ ] Initial sync completed
- [ ] Test chat successful
- [ ] Integration code provided
- [ ] Monitoring configured
- [ ] Documentation delivered
- [ ] Tenant team trained

---

## Tenant Configuration Template

```yaml
# tenant-config.yaml
id: pandawa
name: ARSAKA_PANDAWA
description: Enterprise Hospitality Platform

ai:
  llm:
    provider: openai
    model: gpt-4o-mini
  embedding:
    provider: openai
    model: text-embedding-3-small
  rag:
    strategy: hybrid
    reranker: true

knowledge_sources:
  - name: reservations
    type: database
    sync_interval: 5
  - name: room_rates
    type: api
    sync_interval: 60

limits:
  max_context_tokens: 8000
  max_sessions_per_user: 50
  max_messages_per_session: 100

features:
  memory_extraction: true
  temporal_memory: true
  streaming: true

system_prompt: |
  You are a hospitality assistant for ARSAKA_PANDAWA.
  Help hotel staff with reservations, guest inquiries, and room management.
  Be professional, helpful, and concise.
```
