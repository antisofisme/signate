# GUIDE-001: Quick Start

**TYPE**: Getting Started Guide
**AUDIENCE**: Developers integrating ARSAKA_TUTUR

---

## Overview

Get ARSAKA_TUTUR running and send your first message in 10 minutes.

---

## Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- Python 3.11+ (for SDK)

---

## Step 1: Start Services

```bash
git clone https://github.com/your-org/atlas-chat-ai.git
cd atlas-chat-ai

# Create environment file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start all services
docker-compose up -d
```

Verify services are running:
```bash
curl http://localhost:8003/health
# Expected: {"status": "healthy", ...}
```

---

## Step 2: Create a Tenant

```bash
# Using the seed script
python scripts/seed_tenant.py \
  --id=my-project \
  --name="My Project" \
  --prompt="You are a helpful assistant for My Project."
```

Or via API:
```bash
curl -X POST http://localhost:8003/api/v1/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-project",
    "name": "My Project",
    "system_prompt": "You are a helpful assistant for My Project.",
    "persona_name": "Assistant"
  }'
```

---

## Step 3: Send Your First Message

```bash
curl -X POST http://localhost:8003/api/v1/chat/sync \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: my-project" \
  -d '{"message": "Hello! What can you help me with?"}'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "session_id": "uuid-here",
    "message_id": "uuid-here",
    "content": "Hello! I'm your assistant for My Project. I can help you with..."
  }
}
```

---

## Step 4: Add Knowledge (Optional)

To make AI aware of your project's data:

```bash
# 1. Configure knowledge source
curl -X POST http://localhost:8003/api/v1/admin/knowledge-sources \
  -H "X-Tenant-ID: my-project" \
  -d '{
    "source_type": "database",
    "source_name": "my-data",
    "connection_config": {
      "connection_string": "postgresql://...",
      "table": "my_table",
      "fields": ["title", "content"]
    }
  }'

# 2. Trigger embedding
curl -X POST http://localhost:8003/api/v1/admin/embed \
  -H "X-Tenant-ID: my-project" \
  -d '{"source": "my-data"}'
```

Now chat can reference your data:
```bash
curl -X POST http://localhost:8003/api/v1/chat/sync \
  -H "X-Tenant-ID: my-project" \
  -d '{"message": "What data do we have about X?"}'
```

---

## Step 5: Use the SDK

### Python

```bash
pip install atlas-chat-sdk
```

```python
from atlas_chat import ChatClient

client = ChatClient(
    base_url="http://localhost:8003",
    tenant_id="my-project"
)

# Simple chat
response = await client.chat("Hello!")
print(response.content)

# With session persistence
session = await client.create_session()
response1 = await client.chat("My name is Alice", session_id=session.id)
response2 = await client.chat("What's my name?", session_id=session.id)
# AI remembers: "Your name is Alice"
```

### TypeScript

```bash
npm install @atlas/chat-sdk
```

```typescript
import { ChatClient } from '@atlas/chat-sdk';

const client = new ChatClient({
  baseUrl: 'http://localhost:8003',
  tenantId: 'my-project'
});

const response = await client.chat('Hello!');
console.log(response.content);
```

---

## Next Steps

| Task | Guide |
|------|-------|
| Configure memory extraction | CHAT-L1-ARCH-003 |
| Set up monitoring | CHAT-L3-OPS-002 |
| Add more knowledge sources | CHAT-L3-OPS-004 |
| Customize system prompt | Admin CMS |

---

## Troubleshooting

### "Tenant not found"
- Ensure X-Tenant-ID header is set
- Verify tenant exists: `curl http://localhost:8003/api/v1/admin/tenants`

### "Empty response"
- Check if knowledge is embedded
- Verify OpenAI API key is valid

### "Connection refused"
- Ensure all Docker containers are running: `docker-compose ps`
- Check logs: `docker-compose logs chat-api`

---

## Support

- Documentation: `/docs/`
- Issues: GitHub Issues
- Slack: #atlas-chat-ai

---

**You're ready to go!**
