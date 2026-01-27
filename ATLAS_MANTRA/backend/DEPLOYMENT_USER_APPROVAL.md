# User Approval Flow - Deployment Guide

## Overview

Fitur User Approval Flow memastikan bahwa setiap decision harus di-approve oleh user sebelum disimpan ke database. Ini penting karena:

1. **Immutability**: Decisions tidak bisa diubah setelah disimpan (MANTRA-LAW-001)
2. **Accountability**: User bertanggung jawab atas approval
3. **Review**: User bisa review quality, risk, dan warnings sebelum approve

## Files Changed

```
core/api/routes.py              - New /decisions/approve endpoint
core/use_cases/enhanced_validation.py  - approval_summary generation
```

## Deployment Steps

### 1. SSH ke VPS

```bash
ssh yuda@31.97.111.175
```

### 2. Start Container (jika belum running)

```bash
# Check if running
docker ps | grep mantra

# If not running, start it
docker run -d --name mantra-backend \
  -p 31.97.111.175:8002:8001 \
  --network host \
  atlas-mantra-api:v1.0.4

# Or if exists but stopped
docker start mantra-backend
```

### 3. Deploy Updated Files

```bash
# From local machine, copy files to VPS
scp ATLAS_MANTRA/backend/core/api/routes.py yuda@31.97.111.175:/tmp/
scp ATLAS_MANTRA/backend/core/use_cases/enhanced_validation.py yuda@31.97.111.175:/tmp/

# On VPS, copy into container
docker cp /tmp/routes.py mantra-backend:/app/core/api/routes.py
docker cp /tmp/enhanced_validation.py mantra-backend:/app/core/use_cases/enhanced_validation.py

# Restart container
docker restart mantra-backend
```

### 4. Verify

```bash
curl http://31.97.111.175:8002/api/v1/health
```

## API Usage

### Step 1: Validate Decision

```bash
curl -X POST http://31.97.111.175:8002/api/v1/validate/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "record": {
      "group_id": "ARCH",
      "feature_id": "F05",
      "statement": "Use PostgreSQL for all relational database storage requirements",
      "rationale": "PostgreSQL provides ACID compliance, robust JSON support, and excellent performance for complex queries",
      "constraints": [],
      "invariants": ["All tables must have primary key"],
      "scope": "ORGANIZATION",
      "blast_radius": "HIGH",
      "version": "1.0.0"
    }
  }'
```

**Response includes:**
```json
{
  "result": "READY",
  "proposal_id": "abc123-...",
  "decision_id": "def456-...",
  "requires_user_approval": true,
  "approval_summary": {
    "can_approve": true,
    "quality": {
      "score": 75,
      "grade": "GOOD",
      "top_suggestions": ["..."]
    },
    "risk": {
      "level": "LOW",
      "affected_count": 0
    },
    "approval_message": "This decision is ready for approval..."
  }
}
```

### Step 2: Review approval_summary

User (or AI assistant) reviews:
- `can_approve`: Is approval possible?
- `quality.score`: Is quality acceptable?
- `risk.level`: What's the impact?
- `action_items`: Any blockers or warnings?

### Step 3: Approve Decision

```bash
curl -X POST http://31.97.111.175:8002/api/v1/decisions/approve \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "abc123-...",
    "approved_by": "john.doe"
  }'
```

**Response:**
```json
{
  "result": "STORED",
  "decision_id": "def456-...",
  "decision_code": "ARCH-F05-001-v1.0.0",
  "stored_at": "2026-01-27T..."
}
```

## Error Scenarios

### Proposal Expired
```json
{
  "detail": "Proposal abc123 not found or expired. Please run /validate/enhanced again..."
}
```
→ Proposals expire after 30 minutes. Re-validate to get new proposal.

### Decision Blocked
```json
{
  "result": "BLOCKED",
  "error_message": "Decision cannot be stored. Validation result: BLOCKED"
}
```
→ Fix blocking issues first (quality too low, duplicate, conflict).

### Acknowledgment Required
```json
{
  "result": "BLOCKED",
  "error_message": "This decision has warnings that must be acknowledged..."
}
```
→ Include `acknowledgments` in request:
```json
{
  "proposal_id": "...",
  "approved_by": "john.doe",
  "acknowledgments": ["Near duplicate acknowledged", "Quality warnings reviewed"]
}
```

## Integration with AI Assistant (Mode A)

When using Claude Code or other AI assistants via MCP:

```
AI: "I'll validate this decision first..."
    → Calls POST /validate/enhanced

AI: "The decision has quality score 75/100 (GOOD).
     Risk level is LOW with 0 affected decisions.

     Shall I approve and store this decision?"

User: "Yes, approve it"

AI: "Approving decision..."
    → Calls POST /decisions/approve

AI: "Decision stored successfully!
     Decision Code: ARCH-F05-001-v1.0.0"
```

## Security Notes

1. **proposal_id** is required - prevents arbitrary storage
2. **approved_by** creates audit trail
3. **30 minute expiration** ensures fresh validation
4. **Acknowledgments** ensure user reviewed warnings
