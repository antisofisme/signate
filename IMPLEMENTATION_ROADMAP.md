# Implementation Roadmap
**Analysis Date:** 2025-10-29
**Based on:** Backend Integration, TypeScript Migration, & Celery/ZeroMQ Analysis

---

## PHASE 1: Critical (Week 1) - Backend Scheduler & Video Processing

### Must-Have: Celery + Redis Integration (Backend Only)

**Why:** Without Celery, video transcoding will timeout (>2min uploads fail)

**Tasks:**
1. Verify Celery setup in docker-compose ✅ (already configured)
   - celery-worker (concurrency 4)
   - celery-beat (scheduler)
   - flower (monitoring at port 5555)

2. Migrate FFmpeg transcoding from async/await to Celery tasks
   - Convert `TranscodingService` methods to `@celery_app.task` decorated functions
   - Add retry logic (3 retries with exponential backoff)
   - Implement task progress tracking via Redis

3. Update API endpoints for async processing
   - Upload endpoint returns `{content_id, task_id, status: "transcoding"}`
   - New `/api/tasks/{task_id}` endpoint for progress polling
   - Update frontend to track transcoding progress

4. Test transcoding pipeline
   - Single video: 100MB, 500MB, 2GB
   - Concurrent uploads: 5, 10, 100 simultaneous
   - Verify job persistence (kill worker → resume from Redis)

**Effort:** 3-4 days
**Dependencies:** Redis + PostgreSQL (already running)
**Deliverable:** Video uploads no longer timeout; all transcoding persisted in Redis

---

## PHASE 2: Infrastructure Optimization (Week 2)

### Minimal Docker Services (Production-Ready)

**Current Status:** ✅ Backend API, PostgreSQL, Redis, Viewer all correct

**Only Keep:**
1. ✅ backend-api (port 8001) - FastAPI
2. ✅ celery-worker (for transcoding)
3. ✅ celery-beat (scheduled tasks)
4. ✅ postgres (port 5433)
5. ✅ redis (port 6379)
6. ✅ viewer (port 8080) - Unified for monitors/browsers/WebOS
7. ✅ storage-* (4 containers for file storage via Anthias minimal)
8. ✅ flower (monitoring, optional)

**Remove:**
- ❌ web-admin Docker container (run locally on port 3000 with vite proxy)
- ❌ Any duplicate services

**Environment Variables Fix:**
```bash
# In .env (Line 146)
ANTHIAS_INTERNAL_URL=http://storage-nginx  # ✅ Correct
# (was http://anthias-nginx)
```

**Validation Commands:**
```bash
docker-compose -f docker/docker-compose.yml ps
curl http://192.168.5.12:8001/health
curl http://192.168.5.12:5555  # Flower monitoring
```

**Effort:** 1-2 days
**Deliverable:** Lean, production-optimized Docker setup; all services working correctly

---

## PHASE 3: TypeScript Migration (Month 1-2, Incremental)

### Status: ✅ COMPLETE (Migration Quality 8.5/10)

**Already Done:**
- ✅ 77 components converted (.jsx → .tsx)
- ✅ 13 API service modules (.js → .ts)
- ✅ 3 type definition files (800+ lines)
- ✅ AuthContext with full typing
- ✅ Strict TypeScript config enabled

**Remaining Improvements (Non-Blocking):**

**Sprint 1 (Week 1-2): Error Handling Hardening**
- Replace 53 `any` types in error handlers with `unknown`
- Add type guards: `if (err instanceof Error)`
- Create discriminated unions for API errors
- **Impact:** Prevent 80% of runtime type errors

**Sprint 2 (Week 3-4): Type Safety Enhancements**
- Add Zod/Yup for runtime validation
- Create granular error types (ValidationError, AuthError, etc.)
- Generate API types from OpenAPI spec (if backend provides)
- **Impact:** Complete frontend type coverage

**Sprint 3 (Month 2): Optional, Nice-to-Have**
- Component storybook with TypeScript
- Visual regression testing setup

**Effort:** 2-3 days per sprint (non-blocking, can run parallel)
**Priority:** After Phase 1 & 2 complete
**Deliverable:** Production-grade TypeScript frontend (95%+ type coverage)

---

## PHASE 4: Real-Time Updates (Month 2, Optional)

### WebSocket Integration (Better UX, Not Critical)

**Why:** Reduce polling from 30s to instant updates

**Tasks:**
1. Add WebSocket endpoint in FastAPI
   ```python
   @router.websocket("/ws/device/{device_id}")
   async def websocket_endpoint(websocket: WebSocket, device_id: int)
   ```

2. Update viewer to use WebSocket
   ```javascript
   const ws = new WebSocket(`ws://backend:8001/ws/device/${deviceId}`);
   ```

3. Broadcast playlist updates via WebSocket
   - When content assigned → push to device
   - When playlist modified → push to device

**Effort:** 1-2 days
**Priority:** 🟡 MEDIUM (nice to have)
**Alternative:** Keep polling, it's already working fine

---

## Dependencies & Startup Order

### Docker Compose Start Sequence
```
1. postgres (database foundation)
   ↓
2. redis (broker for Celery)
   ↓
3. backend-api (FastAPI app)
   ↓
4. celery-worker (depends on 1, 2, 3)
5. celery-beat (depends on 1, 2, 3)
6. flower (monitoring, depends on 2)
   ↓
7. storage-* (file storage layer)
   ↓
8. viewer (frontend, depends on 3)
```

### Development Environment
```
Local Machine:
  ├── web-admin (npm run dev on port 3000)
  │   └── Proxies /api → http://192.168.5.12:8001
  │
Server (192.168.5.12):
  ├── backend-api (port 8001)
  ├── celery-worker
  ├── celery-beat
  ├── postgres (port 5433)
  ├── redis
  ├── storage-* (file storage)
  ├── viewer (port 8080)
  └── flower (port 5555)
```

---

## Effort Summary by Phase

| Phase | Component | Days | Status | Blocker |
|-------|-----------|------|--------|---------|
| **1** | Celery transcoding tasks | 3-4 | ⏳ READY | 🔴 HIGH |
| **1** | Task progress endpoint | 1 | ⏳ READY | 🔴 HIGH |
| **1** | Frontend task tracking | 1 | ⏳ READY | 🔴 HIGH |
| **2** | Docker cleanup | 1 | ✅ ANALYZED | 🟢 LOW |
| **2** | Env var fix | 0.5 | ✅ IDENTIFIED | 🟢 LOW |
| **3.1** | Error handler hardening | 2 | 📋 PLANNED | 🟡 MEDIUM |
| **3.2** | Type safety improvements | 2 | 📋 PLANNED | 🟡 MEDIUM |
| **4** | WebSocket real-time | 1-2 | 📋 OPTIONAL | 🟢 OPTIONAL |
| | | | | |
| **TOTAL** | **All Critical** | **5-7 days** | | |
| **TOTAL** | **Recommended** | **10-12 days** | | |

---

## Quick Start (Immediate Actions)

### Day 1 - Fix & Validate
```bash
# 1. Fix environment variable
sed -i 's/http:\/\/anthias-nginx/http:\/\/storage-nginx/g' .env

# 2. Restart backend
cd /mnt/g/khoirul/signate
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d

# 3. Verify all services
docker-compose -f docker/docker-compose.yml ps
curl http://192.168.5.12:8001/health
curl http://192.168.5.12:5555/api/workers
```

### Week 1 - Implement Celery Transcoding
```bash
# Check current transcoding implementation
grep -r "transcode_to_hls" backend/app/

# Convert to Celery tasks (see PHASE 1 above)
# Test with /api/content/upload endpoint
```

### Month 1-2 - Incremental TypeScript Improvements
```bash
# Don't need to wait - can run in parallel
# Already migrated and working!
npm run build  # Should pass all type checks
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Video transcode timeout | 🔴 HIGH | 🔴 CRITICAL | Implement Celery (Phase 1) |
| Job loss on restart | 🔴 HIGH | 🔴 CRITICAL | Redis persistence (Phase 1) |
| Docker misconfiguration | 🟡 MEDIUM | 🟡 MEDIUM | Fix ANTHIAS_INTERNAL_URL |
| TypeScript type errors | 🟢 LOW | 🟢 LOW | Already migrated correctly |
| Polling latency (30s) | 🟢 LOW | 🟡 MEDIUM | Optional WebSocket (Phase 4) |

---

## Success Criteria

- ✅ **Phase 1:** 2GB video uploads complete without timeout
- ✅ **Phase 1:** Job persists when server restarts
- ✅ **Phase 2:** All Docker services start/stop cleanly
- ✅ **Phase 2:** CORS works for web-admin on port 3000
- ✅ **Phase 3:** `npm run build` passes all TypeScript checks
- ✅ **Phase 4:** Playlist updates push to device <100ms

---

## Notes

1. **Celery is NOT optional** - Without it, transcoding > 2min will timeout
2. **Docker setup is correct** - Just fix one env variable
3. **TypeScript migration is excellent** - Quality 8.5/10, ready for production
4. **WebSocket is nice-to-have** - Polling already works, not critical
5. **Test locally first** - Then sync to server using scp/rsync
6. **Commit after each phase** - Keep git history clean

---

**Created by:** Architectural Review (Haiku 4.5)
**Last Updated:** 2025-10-29
