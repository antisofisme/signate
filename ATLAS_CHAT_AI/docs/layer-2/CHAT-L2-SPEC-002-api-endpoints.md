# CHAT-L2-SPEC-002: API Endpoints

**Status**: Active
**Created**: 2026-01-25
**Complies With**: CHAT-LAW-004, CHAT-LAW-006

---

## Overview

REST API specification for ATLAS_CHAT_AI. All endpoints require tenant context.

---

## Base URL

```
Production: https://chat-api.atlas.example.com/api/v1
Development: http://localhost:8003/api/v1
```

---

## Authentication

All requests must include:
- `X-Tenant-ID`: Tenant identifier (required)
- `Authorization`: Bearer token (required for user endpoints)

```http
X-Tenant-ID: mantra
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## Endpoints

### Chat

#### POST /chat
Send a message and receive AI response (streaming).

**Request:**
```http
POST /api/v1/chat
Content-Type: application/json
Accept: text/event-stream
X-Tenant-ID: mantra
Authorization: Bearer {token}

{
  "message": "What decisions exist about authentication?",
  "session_id": "uuid-optional",
  "context": {
    "page": "/decisions"
  }
}
```

**Response (SSE Stream):**
```
event: message
data: {"content": "Based on the existing decisions"}

event: message
data: {"content": ", there are several"}

event: done
data: {"session_id": "uuid", "message_id": "uuid", "retrieved_docs": ["doc1", "doc2"]}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests"
  }
}
```

#### POST /chat/sync
Non-streaming chat (for backwards compatibility).

**Request:**
```http
POST /api/v1/chat/sync
Content-Type: application/json
X-Tenant-ID: mantra

{
  "message": "Hello",
  "session_id": "uuid-optional"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "message_id": "uuid",
    "content": "Hello! How can I help you today?",
    "retrieved_docs": [],
    "token_usage": {
      "prompt_tokens": 150,
      "completion_tokens": 25
    }
  }
}
```

---

### Sessions

#### GET /sessions
List user's chat sessions.

**Request:**
```http
GET /api/v1/sessions?limit=20&offset=0
X-Tenant-ID: mantra
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Authentication decisions",
      "started_at": "2026-01-25T10:00:00Z",
      "last_message_at": "2026-01-25T10:30:00Z",
      "message_count": 15,
      "summary": "Discussion about OAuth vs JWT..."
    }
  ],
  "meta": {
    "total": 45,
    "limit": 20,
    "offset": 0
  }
}
```

#### POST /sessions
Create a new session.

**Request:**
```http
POST /api/v1/sessions
Content-Type: application/json
X-Tenant-ID: mantra

{
  "title": "Optional title"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Optional title",
    "started_at": "2026-01-25T10:00:00Z"
  }
}
```

#### GET /sessions/{id}
Get session with messages.

**Request:**
```http
GET /api/v1/sessions/uuid?messages=true&limit=50
X-Tenant-ID: mantra
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Authentication decisions",
    "started_at": "2026-01-25T10:00:00Z",
    "message_count": 15,
    "messages": [
      {
        "id": "uuid",
        "role": "user",
        "content": "What decisions exist...",
        "created_at": "2026-01-25T10:00:00Z"
      },
      {
        "id": "uuid",
        "role": "assistant",
        "content": "Based on the existing...",
        "created_at": "2026-01-25T10:00:05Z",
        "retrieved_doc_ids": ["doc1", "doc2"]
      }
    ]
  }
}
```

#### DELETE /sessions/{id}
Soft-delete a session.

**Request:**
```http
DELETE /api/v1/sessions/uuid
X-Tenant-ID: mantra
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "deleted": true
  }
}
```

---

### Search

#### POST /search
Semantic search over knowledge base.

**Request:**
```http
POST /api/v1/search
Content-Type: application/json
X-Tenant-ID: mantra
Authorization: Bearer {token}

{
  "query": "API authentication security",
  "top_k": 5,
  "filters": {
    "source": "decisions"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "doc-uuid",
        "score": 0.92,
        "content": "All API endpoints must use JWT...",
        "metadata": {
          "decision_code": "CTL-F11-001",
          "source": "decisions"
        }
      }
    ],
    "query_embedding_cached": true
  }
}
```

#### POST /search/sessions
Search past sessions by similarity.

**Request:**
```http
POST /api/v1/search/sessions
Content-Type: application/json
X-Tenant-ID: mantra

{
  "query": "authentication discussion",
  "top_k": 3
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "session_id": "uuid",
        "score": 0.87,
        "title": "Auth implementation",
        "summary": "Discussed OAuth vs JWT...",
        "message_count": 20,
        "last_message_at": "2026-01-20T15:00:00Z"
      }
    ]
  }
}
```

---

### Memory

#### GET /memory/facts
Get user's stored facts (semantic memory).

**Request:**
```http
GET /api/v1/memory/facts?type=preference&active_only=true
X-Tenant-ID: mantra
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "type": "preference",
      "content": "Prefers TypeScript over JavaScript",
      "confidence": 0.95,
      "source_session_id": "uuid",
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

#### DELETE /memory/facts/{id}
Deactivate a fact.

**Request:**
```http
DELETE /api/v1/memory/facts/uuid
X-Tenant-ID: mantra
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "deactivated": true
  }
}
```

#### GET /memory/timeline
Get temporal summaries.

**Request:**
```http
GET /api/v1/memory/timeline?period=week&start=2026-01-01&end=2026-01-31
X-Tenant-ID: mantra
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "period_type": "week",
      "period_start": "2026-01-20",
      "period_end": "2026-01-26",
      "summary": "Focused on authentication and RAG implementation",
      "topics": [
        {"topic": "authentication", "count": 15},
        {"topic": "RAG", "count": 12}
      ],
      "session_count": 5,
      "message_count": 87
    }
  ]
}
```

---

### Admin Endpoints

#### POST /admin/embed
Trigger re-embedding of knowledge source.

**Request:**
```http
POST /api/v1/admin/embed
Content-Type: application/json
X-Tenant-ID: mantra
Authorization: Bearer {admin-token}

{
  "source": "decisions",
  "full_reindex": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "queued",
    "estimated_documents": 150
  }
}
```

#### GET /admin/embed/{job_id}
Check embedding job status.

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "running",
    "progress": {
      "documents_total": 150,
      "documents_processed": 75,
      "vectors_created": 75
    }
  }
}
```

#### GET /admin/stats
Get tenant usage statistics.

**Request:**
```http
GET /api/v1/admin/stats
X-Tenant-ID: mantra
Authorization: Bearer {admin-token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 25,
      "active_today": 10
    },
    "sessions": {
      "total": 500,
      "today": 35
    },
    "messages": {
      "total": 5000,
      "today": 350
    },
    "vectors": {
      "decisions": 150,
      "sessions": 500
    },
    "tokens": {
      "prompt_tokens_today": 50000,
      "completion_tokens_today": 15000
    }
  }
}
```

---

### Health

#### GET /health
Health check endpoint.

**Request:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "qdrant": "ok",
    "redis": "ok"
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TENANT_NOT_FOUND` | 404 | Tenant ID not found or inactive |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | User doesn't have access |
| `SESSION_NOT_FOUND` | 404 | Session doesn't exist |
| `RATE_LIMITED` | 429 | Too many requests |
| `CONTEXT_TOO_LONG` | 400 | Message exceeds token limit |
| `LLM_ERROR` | 502 | Error from LLM provider |
| `VECTOR_STORE_ERROR` | 502 | Error from Qdrant |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /chat | 30 requests/minute per user |
| POST /search | 60 requests/minute per user |
| GET endpoints | 120 requests/minute per user |
| Admin endpoints | 10 requests/minute per admin |

---

## Request/Response Format

### Standard Success Response
```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }  // optional: pagination, timing
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }  // optional: additional context
  }
}
```
