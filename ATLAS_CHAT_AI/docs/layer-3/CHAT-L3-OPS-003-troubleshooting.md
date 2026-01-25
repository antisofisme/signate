# CHAT-L3-OPS-003: Troubleshooting Guide

**Status**: Active
**Created**: 2026-01-25

---

## Common Issues

### 1. Chat Returns Empty Response

**Symptoms:**
- AI responds with empty or very short messages
- No retrieved documents in response

**Diagnosis:**
```bash
# Check if documents are embedded
curl http://localhost:6333/collections/mantra_documents | jq '.result.points_count'

# Check embedding service
curl -X POST http://localhost:8003/api/v1/search \
  -H "X-Tenant-ID: mantra" \
  -d '{"query": "test", "top_k": 5}'
```

**Solutions:**
1. Re-run embedding job: `python scripts/embed_knowledge.py --tenant=mantra`
2. Check OpenAI API key is valid
3. Verify knowledge source sync is running

---

### 2. High Latency (> 2 seconds)

**Symptoms:**
- Slow first response
- Timeouts from clients

**Diagnosis:**
```bash
# Check component latencies
curl http://localhost:8003/health | jq '.checks'

# Check database slow queries
psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '1 second';"

# Check Qdrant performance
curl http://localhost:6333/metrics | grep search_duration
```

**Solutions:**
1. **Database slow:** Add indexes, optimize queries
2. **Qdrant slow:** Reduce top_k, check memory
3. **LLM slow:** Switch to faster model (gpt-4o-mini)
4. **Network:** Check connectivity between services

---

### 3. Rate Limit Errors

**Symptoms:**
- 429 Too Many Requests responses
- Some users blocked

**Diagnosis:**
```bash
# Check rate limit metrics
curl http://localhost:8003/metrics | grep rate_limited

# Check Redis for rate limit keys
redis-cli KEYS "chat:ratelimit:*"
```

**Solutions:**
1. Increase rate limit in config: `API_RATE_LIMIT_REQUESTS=100`
2. Identify abusive users from logs
3. Implement per-tenant limits

---

### 4. Memory Extraction Not Working

**Symptoms:**
- User facts not being extracted
- `/memory/facts` returns empty

**Diagnosis:**
```bash
# Check worker status
docker ps | grep fact-extractor

# Check worker logs
docker logs chat-worker --tail 100

# Check queue
redis-cli LLEN chat:queue:fact_extraction
```

**Solutions:**
1. Restart worker: `docker restart chat-worker`
2. Check Celery broker connection
3. Verify LLM can perform extraction (test manually)

---

### 5. Qdrant Connection Errors

**Symptoms:**
- Search returns errors
- "Connection refused" in logs

**Diagnosis:**
```bash
# Check Qdrant is running
curl http://localhost:6333/collections

# Check Qdrant logs
docker logs qdrant

# Check disk space
df -h
```

**Solutions:**
1. Restart Qdrant: `docker restart qdrant`
2. Free disk space if > 90% used
3. Increase Qdrant memory if OOM errors
4. Restore from snapshot if data corrupted

---

### 6. Database Connection Pool Exhausted

**Symptoms:**
- "Cannot acquire connection" errors
- Requests timing out

**Diagnosis:**
```bash
# Check active connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'atlas_chat';"

# Check pool settings
echo $DATABASE_POOL_SIZE
```

**Solutions:**
1. Increase pool size: `DATABASE_POOL_SIZE=40`
2. Check for connection leaks in code
3. Reduce pool timeout: `DATABASE_POOL_TIMEOUT=10`
4. Restart API to reset connections

---

### 7. LLM Provider Errors

**Symptoms:**
- 502 errors from API
- "LLM_ERROR" in response

**Diagnosis:**
```bash
# Test OpenAI directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check provider status
# OpenAI: https://status.openai.com
# DeepSeek: https://status.deepseek.com
```

**Solutions:**
1. Verify API key is valid
2. Check billing/quota on provider dashboard
3. Switch to backup provider temporarily
4. Implement retry with exponential backoff

---

### 8. Tenant Not Found

**Symptoms:**
- 404 "Tenant not found" errors
- New tenant not accessible

**Diagnosis:**
```bash
# Check tenant exists in database
psql -c "SELECT * FROM tenants WHERE id = 'tenant-id';"

# Check cache
redis-cli GET "chat:tenant:tenant-id"
```

**Solutions:**
1. Create tenant if missing: `python scripts/seed_tenant.py --id=tenant-id`
2. Invalidate cache: `redis-cli DEL "chat:tenant:tenant-id"`
3. Check tenant is active: `is_active = TRUE`

---

### 9. Session History Missing

**Symptoms:**
- Previous messages not showing
- Session appears empty

**Diagnosis:**
```bash
# Check session exists
psql -c "SELECT * FROM chat_sessions WHERE id = 'session-uuid';"

# Check messages
psql -c "SELECT count(*) FROM chat_messages WHERE session_id = 'session-uuid';"
```

**Solutions:**
1. Verify session_id is correct (UUID format)
2. Check tenant_id matches
3. Ensure session not soft-deleted: `is_deleted = FALSE`
4. Check if messages were redacted

---

### 10. Embedding Cache Ineffective

**Symptoms:**
- Low cache hit ratio (< 50%)
- High embedding API costs

**Diagnosis:**
```bash
# Check cache stats
redis-cli INFO stats | grep hit

# Check cache keys
redis-cli KEYS "chat:emb:*" | wc -l

# Check TTL
redis-cli TTL "chat:emb:somehash"
```

**Solutions:**
1. Increase cache TTL: `REDIS_TTL_DEFAULT=86400` (24h)
2. Check if cache is being cleared unexpectedly
3. Verify Redis persistence is enabled
4. Pre-warm cache for common queries

---

## Emergency Procedures

### Complete Outage

1. Check infrastructure: `docker-compose ps`
2. Check logs for errors: `docker-compose logs --tail 100`
3. Restart all services: `docker-compose restart`
4. Verify health: `curl http://localhost:8003/health`

### Data Recovery

1. Stop all services: `docker-compose stop`
2. Restore PostgreSQL from backup
3. Restore Qdrant from snapshot
4. Start services: `docker-compose up -d`
5. Re-sync knowledge sources

### Rollback Deployment

```bash
# Nomad
nomad job revert chat-api <previous-version>

# Docker
docker-compose pull chat-api:previous-tag
docker-compose up -d chat-api
```

---

## Diagnostic Commands

### Quick Health Check
```bash
#!/bin/bash
echo "=== Chat API Health ==="
curl -s http://localhost:8003/health | jq

echo "=== PostgreSQL ==="
psql $DATABASE_URL -c "SELECT 1" && echo "OK"

echo "=== Qdrant ==="
curl -s http://localhost:6333/collections | jq '.result.collections | length'

echo "=== Redis ==="
redis-cli PING

echo "=== Recent Errors ==="
docker logs chat-api --since 5m 2>&1 | grep ERROR | tail -5
```

### Performance Check
```bash
#!/bin/bash
echo "=== API Latency ==="
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8003/health

echo "=== Database Latency ==="
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT 1"

echo "=== Qdrant Latency ==="
time curl -s -X POST http://localhost:6333/collections/mantra_documents/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...], "limit": 5}' > /dev/null
```

---

## Contact & Escalation

| Issue Type | First Contact | Escalation |
|------------|---------------|------------|
| API Down | On-call engineer | Team lead |
| Data Loss | DBA + On-call | CTO |
| Security Incident | Security team | CISO |
| LLM Provider Issue | Check status page | Contact provider support |
