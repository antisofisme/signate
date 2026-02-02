# Server-side AI Arbitration - Deployment Guide

## Overview

MANTRA mendukung AI arbitration untuk kasus validasi yang ambigu:
- **Borderline quality** (score 50-80)
- **Near-duplicate** (similarity 85-95%)
- **Medium-severity conflict**

**PENTING**: AI TIDAK dipanggil untuk setiap validasi! Hanya saat diperlukan.

## Supported AI Providers

| Provider | Model Default | Cost/call | Speed |
|----------|--------------|-----------|-------|
| **Anthropic** | claude-3-haiku | ~$0.003 | Fast |
| **OpenAI** | gpt-4o-mini | ~$0.003 | Fast |
| **DeepSeek** | deepseek-chat | ~$0.001 | Fast |
| **Groq** | llama-3.1-70b | ~$0.0005 | Very Fast |
| **xAI** | grok-beta | ~$0.003 | Fast |
| **OpenRouter** | multi-model | varies | varies |

## Two Modes

### Mode A: DELEGATED (Default - Recommended for MCP/CLI)
```
User's AI Assistant (Claude Code, Cursor, etc.)
         │
         ▼
    MANTRA API
         │
         ▼
Returns arbitration_context
         │
         ▼
User's AI evaluates & submits verdict
         │
         ▼
MANTRA applies verdict

Cost: $0 for MANTRA (user pays via existing AI subscription)
```

### Mode B: SERVER (For Chat UI)
```
Browser/Chat UI (no local AI)
         │
         ▼
    MANTRA API
         │
         ▼
MANTRA's AI evaluates (calls AI provider)
         │
         ▼
Returns result with AI verdict

Cost: MANTRA pays per AI call (~$0.003)
```

## Configuration

### Environment Variables

```bash
# Provider selection
AI_PROVIDER=anthropic  # anthropic, openai, deepseek, groq, xai, openrouter

# API Keys (set one based on provider)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk_...
XAI_API_KEY=xai-...
OPENROUTER_API_KEY=sk-or-...

# Or use generic key
AI_API_KEY=your-api-key

# Optional settings
AI_MODEL=claude-3-haiku-20240307  # Override default model
AI_MAX_TOKENS=500
AI_TEMPERATURE=0.3
AI_TIMEOUT=30
```

### Docker Example

```dockerfile
# In docker-compose.yml or docker run
environment:
  - AI_PROVIDER=anthropic
  - ANTHROPIC_API_KEY=sk-ant-xxx
```

## API Usage

### Get Available Providers

```bash
curl http://31.97.111.175:8002/api/v1/ai/providers
```

Response:
```json
{
  "providers": [
    {"id": "anthropic", "name": "Anthropic", "default_model": "claude-3-haiku-20240307", "models": ["claude-3-haiku-...", "claude-3-sonnet-..."]},
    {"id": "openai", "name": "Openai", "default_model": "gpt-4o-mini", "models": ["gpt-4o-mini", "gpt-4o"]},
    {"id": "deepseek", "name": "Deepseek", "default_model": "deepseek-chat", "models": ["deepseek-chat"]},
    {"id": "groq", "name": "Groq", "default_model": "llama-3.1-70b-versatile", "models": ["llama-3.1-70b-...", "mixtral-..."]},
    {"id": "xai", "name": "Xai", "default_model": "grok-beta", "models": ["grok-beta", "grok-2"]},
    {"id": "openrouter", "name": "Openrouter", "default_model": "anthropic/claude-3-haiku", "models": ["anthropic/...", "openai/..."]}
  ],
  "current_provider": "anthropic",
  "is_configured": true
}
```

### Validation with Arbitration Mode

**DELEGATED Mode** (Default):
```bash
curl -X POST http://31.97.111.175:8002/api/v1/validate/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "record": {...},
    "arbitration_mode": "DELEGATED"
  }'
```

Response (if borderline):
```json
{
  "result": "INVALID",
  "arbitration_required": true,
  "arbitration_contexts": [
    {
      "arbitration_type": "QUALITY",
      "prompt_template": "Evaluate this ADR...",
      "expected_verdicts": ["APPROVE", "REJECT", "NEEDS_IMPROVEMENT"],
      "instructions": "..."
    }
  ]
}
```

Client AI then submits verdict:
```bash
curl -X POST http://31.97.111.175:8002/api/v1/validate/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "record": {...},
    "arbitration_verdicts": [
      {
        "arbitration_type": "QUALITY",
        "verdict": "APPROVE",
        "confidence": 0.85,
        "reason": "Clear enough for implementation"
      }
    ]
  }'
```

**SERVER Mode**:
```bash
curl -X POST http://31.97.111.175:8002/api/v1/validate/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "record": {...},
    "arbitration_mode": "SERVER"
  }'
```

Response (AI already evaluated):
```json
{
  "result": "READY",
  "arbitration_required": false,
  "ai_verdicts": {
    "QUALITY": {
      "verdict": "APPROVE",
      "confidence": 0.85,
      "reason": "Statement provides clear implementation guidance",
      "source": "SERVER_AI",
      "provider": "Anthropic"
    }
  }
}
```

**SKIP Mode** (No AI):
```bash
curl -X POST http://31.97.111.175:8002/api/v1/validate/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "record": {...},
    "arbitration_mode": "SKIP"
  }'
```

## When AI is Called

AI arbitration is ONLY triggered when:

| Condition | Threshold | AI Type |
|-----------|-----------|---------|
| Quality borderline | Score 50-80 | QualityArbiter |
| Near duplicate | Similarity 85-95% | DuplicateClassifier |
| Medium conflict | Severity = MEDIUM | ConflictArbiter |

**NOT triggered:**
- Quality < 50 (auto-reject)
- Quality > 80 (auto-approve)
- Exact duplicate (auto-block)
- Critical conflict (auto-block)

## Cost Estimation

Assuming 30% of validations need arbitration:

| Mode | Cost per 1000 validations |
|------|---------------------------|
| DELEGATED | $0.00 (user's AI) |
| SERVER (Anthropic Haiku) | ~$0.90 |
| SERVER (Groq) | ~$0.15 |
| SERVER (DeepSeek) | ~$0.30 |

## Deployment

### Files to Deploy

```
core/use_cases/ai_arbiter/
├── __init__.py (updated)
├── ai_client.py (NEW)
├── base.py (updated)
├── quality_arbiter.py
├── duplicate_classifier.py
├── conflict_arbiter.py

core/api/routes.py (updated)
core/use_cases/enhanced_validation.py (updated)
```

### Deploy Commands

```bash
# Copy to VPS
scp -r core/use_cases/ai_arbiter yuda@31.97.111.175:/tmp/
scp core/api/routes.py yuda@31.97.111.175:/tmp/
scp core/use_cases/enhanced_validation.py yuda@31.97.111.175:/tmp/

# On VPS
docker cp /tmp/ai_arbiter mantra-backend:/app/core/use_cases/
docker cp /tmp/routes.py mantra-backend:/app/core/api/
docker cp /tmp/enhanced_validation.py mantra-backend:/app/core/use_cases/

# Set API key and restart
docker exec mantra-backend sh -c 'echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> /app/.env'
docker restart mantra-backend
```

## Security Notes

1. **API keys should be in environment variables**, not in code
2. **Rate limiting** recommended for SERVER mode to prevent abuse
3. **Cost monitoring** - track AI calls per day/user
4. **Fallback** - if AI fails, validation continues without AI verdict
