# FINAL DEPLOYMENT PLAN - Smart TV Digital Signage System

**Production Domain**: `*.zhmhotels.online`
**Date**: 2025-11-24
**Target Server**: 192.168.5.12
**Current Readiness**: 40% → 100% (after fixes)
**Total Effort**: 4-8 hours

---

## EXECUTIVE SUMMARY

### Current Status

**Overall Readiness**: 40% production-ready
- **Backend**: 60% (Hardcoded IPs, missing PUBLIC_BASE_URL system)
- **CMS**: 70% (Hardcoded fallback, console.log issues)
- **Player**: 80% (Config system good, needs domain update)
- **Docker**: 30% (Missing resource limits, log rotation, SSL)

### Blocking Issues (MUST FIX)

| Issue | Impact | Component | Effort | Priority |
|-------|--------|-----------|--------|----------|
| Hardcoded IPs (5 locations) | HIGH | Backend | 1h | P1 |
| Missing PUBLIC_BASE_URL system | HIGH | Backend | 30m | P1 |
| No SSL/TLS configuration | CRITICAL | Docker | 1h | P1 |
| Missing resource limits | HIGH | Docker | 30m | P1 |
| Missing log rotation | HIGH | Docker | 30m | P1 |
| 69 console.log statements | MEDIUM | CMS | 2h | P2 |
| Old files not cleaned | LOW | All | 30m | P2 |

### Recommended Deployment Path

**Option 1 - Basic Production (4 hours)**: Priority 1 fixes only
- Fix all hardcodes → domain-based URLs
- Add PUBLIC_BASE_URL system
- SSL/TLS configuration
- Resource limits + log rotation
- **Result**: Functional production system, needs monitoring

**Option 2 - Production-Hardened (6 hours)**: Priority 1 + Priority 2
- Everything from Option 1
- Remove console.log statements
- Clean up old files
- Deployment verification scripts
- **Result**: Production-safe system (RECOMMENDED)

**Option 3 - Best Practices (8 hours)**: All priorities
- Everything from Option 2
- Integration tests
- Monitoring alerts configured
- Full documentation
- **Result**: Enterprise-grade system

**RECOMMENDED**: Option 2 (6 hours)

---

## PERBAIKAN (Fixes Required)

### Priority 1: CRITICAL (Blocks Production) - 3.5 hours

#### 1.1 Backend: Add PUBLIC_BASE_URL System
**Impact**: Backend generates URLs with wrong domain
**Files**: 5 files
**Effort**: 30 minutes

**Problem**: Backend hardcodes `http://192.168.5.12:8001` in 4 locations:
1. `services/content/infrastructure/storage/local_storage.py:39`
2. `services/content/repositories/content_repo.py:374`
3. `services/device/log_routes.py:283`
4. `main.py:203-204` (CORS origins)

**Solution**:

```bash
# 1. Add to backend-python/shared/config.py (line 56 after LOG_LEVEL)
```

```python
# Public URL Configuration
PUBLIC_BASE_URL: str = ""  # e.g., https://api.zhmhotels.online
```

```bash
# 2. Update backend-python/services/content/infrastructure/storage/local_storage.py
```

**OLD (line 39)**:
```python
base_url: str = "http://192.168.5.12:8001"
```

**NEW**:
```python
from shared.config import settings

base_url: str = settings.PUBLIC_BASE_URL or "http://192.168.5.12:8001"
```

```bash
# 3. Update backend-python/services/content/repositories/content_repo.py
```

**OLD (line 374)**:
```python
hls_master_playlist_url = f"http://192.168.5.12:8001/content/hls/{year}/{month}/{org_dir}/{content_uuid}/master.m3u8"
```

**NEW**:
```python
from shared.config import settings

base_url = settings.PUBLIC_BASE_URL or "http://192.168.5.12:8001"
hls_master_playlist_url = f"{base_url}/content/hls/{year}/{month}/{org_dir}/{content_uuid}/master.m3u8"
```

```bash
# 4. Update backend-python/services/device/log_routes.py
```

**OLD (line 283)**:
```python
"url": "http://192.168.5.12:8080/"
```

**NEW**:
```python
from shared.config import settings

player_url = settings.PUBLIC_BASE_URL.replace('api', 'player') if settings.PUBLIC_BASE_URL else "http://192.168.5.12:8080"
"url": player_url
```

```bash
# 5. Update backend-python/main.py CORS origins
```

**OLD (lines 203-204)**:
```python
"http://192.168.5.12:8080",
"http://192.168.5.12:3000"
```

**NEW**:
```python
"https://player.zhmhotels.online",
"https://admin.zhmhotels.online",
"http://192.168.5.12:8080",  # Keep for local dev
"http://192.168.5.12:3000"
```

**Verification**:
```bash
grep -rn "192.168.5.12" backend-python/services/ --include="*.py"
# Should only show comments and fallback values
```

---

#### 1.2 Frontend: Update Environment Variables
**Impact**: CMS/Player connect to wrong domain
**Files**: 2 files
**Effort**: 15 minutes

**Solution**:

```bash
# 1. Update /mnt/g/khoirul/signate/.env
```

**Add these lines (after line 255)**:
```env
# =============================================================================
# 25. PRODUCTION DOMAIN CONFIGURATION
# =============================================================================

# Public URLs (for production domain)
PUBLIC_API_URL=https://api.zhmhotels.online
PUBLIC_CMS_URL=https://admin.zhmhotels.online
PUBLIC_PLAYER_URL=https://player.zhmhotels.online
PUBLIC_WS_URL=wss://api.zhmhotels.online

# Backend (used for URL generation)
PUBLIC_BASE_URL=https://api.zhmhotels.online
```

```bash
# 2. Update cms-vite/.env.production (create if not exists)
```

```env
# CMS Production Environment Variables
VITE_API_URL=https://api.zhmhotels.online
VITE_WS_URL=wss://api.zhmhotels.online
VITE_PLAYER_URL=https://player.zhmhotels.online
```

```bash
# 3. Update player-vite/.env.production (create if not exists)
```

```env
# Player Production Environment Variables
VITE_API_BASE_URL=https://api.zhmhotels.online
VITE_WS_BASE_URL=wss://api.zhmhotels.online
```

**Verification**:
```bash
# Check files exist
ls -lh cms-vite/.env.production player-vite/.env.production

# Check content
grep VITE_API_URL cms-vite/.env.production
grep VITE_API_BASE_URL player-vite/.env.production
```

---

#### 1.3 Docker: Add SSL/TLS Configuration
**Impact**: HTTPS required for production
**Files**: docker-compose.yml, nginx configs
**Effort**: 1 hour

**Solution**:

```bash
# 1. Create SSL certificates directory
mkdir -p /mnt/g/khoirul/signate/docker/ssl

# 2. Generate self-signed cert (or use Let's Encrypt)
# For testing - use self-signed:
cd /mnt/g/khoirul/signate/docker/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout zhmhotels.key \
  -out zhmhotels.crt \
  -subj "/CN=*.zhmhotels.online/O=ZHM Hotels/C=ID" \
  -addext "subjectAltName=DNS:*.zhmhotels.online,DNS:zhmhotels.online"

# For production - use Let's Encrypt (on server):
# certbot certonly --standalone -d api.zhmhotels.online -d admin.zhmhotels.online -d player.zhmhotels.online
# Then copy certs to docker/ssl/
```

```bash
# 3. Create Nginx reverse proxy config
# Create docker/nginx-proxy.conf
```

```nginx
# Nginx Reverse Proxy for Production
# Handles SSL termination and routing to containers

# API Backend (api.zhmhotels.online)
server {
    listen 443 ssl http2;
    server_name api.zhmhotels.online;

    ssl_certificate /etc/nginx/ssl/zhmhotels.crt;
    ssl_certificate_key /etc/nginx/ssl/zhmhotels.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 500M;

    location / {
        proxy_pass http://backend-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://backend-api:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}

# CMS Admin (admin.zhmhotels.online)
server {
    listen 443 ssl http2;
    server_name admin.zhmhotels.online;

    ssl_certificate /etc/nginx/ssl/zhmhotels.crt;
    ssl_certificate_key /etc/nginx/ssl/zhmhotels.key;

    location / {
        proxy_pass http://cms-frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Player (player.zhmhotels.online)
server {
    listen 443 ssl http2;
    server_name player.zhmhotels.online;

    ssl_certificate /etc/nginx/ssl/zhmhotels.crt;
    ssl_certificate_key /etc/nginx/ssl/zhmhotels.key;

    location / {
        proxy_pass http://player:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name api.zhmhotels.online admin.zhmhotels.online player.zhmhotels.online;
    return 301 https://$host$request_uri;
}
```

```bash
# 4. Update docker/docker-compose.yml - Add nginx-proxy service
# Add after line 235 (after player service)
```

```yaml
  # ============================================
  # Nginx Reverse Proxy (SSL Termination)
  # ============================================
  nginx-proxy:
    container_name: signage-nginx-proxy
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx-proxy.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - signage-network
    depends_on:
      - backend-api
      - cms-frontend
      - player
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 5s
      retries: 3
```

**Verification**:
```bash
# Check SSL cert
openssl x509 -in docker/ssl/zhmhotels.crt -text -noout | grep "CN="

# Test nginx config
docker run --rm -v $(pwd)/docker/nginx-proxy.conf:/etc/nginx/conf.d/default.conf nginx:alpine nginx -t
```

---

#### 1.4 Docker: Add Resource Limits
**Impact**: Prevent OOM kills, service crashes
**Files**: docker-compose.yml
**Effort**: 30 minutes

**Solution**:

```bash
# Update docker/docker-compose.yml
# Add resource limits to ALL services (11 services)
```

**Add to backend-api service (after line 150)**:
```yaml
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

**Add to celery-worker service (after line 193)**:
```yaml
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '4.0'
        reservations:
          memory: 1G
          cpus: '1.0'
```

**Add to postgres service (after line 27)**:
```yaml
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
```

**Add to redis service (after line 46)**:
```yaml
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

**Add to remaining services** (clamav, pgbouncer, cms-frontend, player, prometheus, grafana, postgres-exporter):
```yaml
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

**Verification**:
```bash
# Count resource limits
grep -c "resources:" docker/docker-compose.yml
# Should be 11 (one per service)
```

---

#### 1.5 Docker: Add Log Rotation
**Impact**: Prevent disk full after weeks
**Files**: docker-compose.yml
**Effort**: 30 minutes

**Solution**:

```bash
# Add logging config to ALL services in docker/docker-compose.yml
# Add after each service's healthcheck section
```

**Template (add to all 12 services)**:
```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
        labels: "production"
```

**Example for backend-api (after line 150)**:
```yaml
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)\" || exit 1"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
        labels: "production"
```

**Verification**:
```bash
# Count logging configs
grep -c "logging:" docker/docker-compose.yml
# Should be 12 (all services including nginx-proxy)
```

---

### Priority 2: HIGH (Should Fix) - 2.5 hours

#### 2.1 CMS: Replace Console.log with Logger
**Impact**: Production logging leaks data, no log levels
**Files**: 4 files, 69 console.log statements
**Effort**: 2 hours

**Problem**: Console.log in production code
- `cms-vite/src/features/auth/hooks/useAuth.ts` - Logs reset tokens!
- `cms-vite/src/features/devices/api/deviceApi.ts` - 20+ logs
- `cms-vite/src/features/devices/api/logsApi.ts` - 15+ logs
- `cms-vite/src/lib/api/client.ts` - 3 logs

**Solution**:

```bash
# 1. Create cms-vite/src/shared/utils/logger.ts
```

```typescript
/**
 * Production-safe Logger
 * - Debug logs only in development
 * - Structured logging with timestamps
 * - No sensitive data in production
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogContext {
  component?: string;
  action?: string;
  [key: string]: any;
}

class Logger {
  private isDev = import.meta.env.DEV;

  private formatMessage(level: LogLevel, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const contextStr = context ? ` | ${JSON.stringify(context)}` : '';
    return `[${timestamp}] [${level.toUpperCase()}] ${message}${contextStr}`;
  }

  debug(message: string, data?: any) {
    if (this.isDev) {
      console.log(`[DEBUG] ${message}`, data);
    }
  }

  info(message: string, context?: LogContext) {
    console.info(this.formatMessage('info', message, context));
  }

  warn(message: string, context?: LogContext) {
    console.warn(this.formatMessage('warn', message, context));
  }

  error(message: string, error?: Error, context?: LogContext) {
    console.error(this.formatMessage('error', message, context), error);
  }
}

export const logger = new Logger();
```

```bash
# 2. Replace console.log in auth hooks (REMOVE SENSITIVE DATA!)
# cms-vite/src/features/auth/hooks/useAuth.ts
```

**OLD (line 45)**:
```typescript
console.log('Reset Token (DEV ONLY):', data.reset_token);
```

**NEW**:
```typescript
import { logger } from '@shared/utils/logger';

logger.debug('Reset token received'); // No token value!
```

```bash
# 3. Replace console.log in device API
# cms-vite/src/features/devices/api/deviceApi.ts
```

**OLD**:
```typescript
console.log('[DeviceAPI] Fetching:', url);
console.log('[DeviceAPI] Response:', response.data);
```

**NEW**:
```typescript
import { logger } from '@shared/utils/logger';

logger.debug('[DeviceAPI] Fetching', { url });
logger.debug('[DeviceAPI] Response received', { count: response.data?.length });
```

```bash
# 4. Replace console.log in logs API
# cms-vite/src/features/devices/api/logsApi.ts
```

**OLD**:
```typescript
console.log('[LogsAPI] Fetching device logs:', url);
console.log('[LogsAPI] Response:', response.data);
```

**NEW**:
```typescript
import { logger } from '@shared/utils/logger';

logger.debug('[LogsAPI] Fetching device logs', { deviceId });
logger.debug('[LogsAPI] Logs received', { count: response.data?.logs?.length });
```

```bash
# 5. Replace console in API client
# cms-vite/src/lib/api/client.ts
```

**OLD (lines 88, 96, 101)**:
```typescript
console.warn('[API] 401 Unauthorized - Logging out...');
console.error('[API] 403 Forbidden - No permission');
console.error('[API] Network error:', error.message);
```

**NEW**:
```typescript
import { logger } from '@shared/utils/logger';

logger.warn('[API] 401 Unauthorized - Logging out');
logger.error('[API] 403 Forbidden', undefined, { endpoint: error.config?.url });
logger.error('[API] Network error', error);
```

**Verification**:
```bash
# Check no console.log remains
grep -rn "console.log" cms-vite/src/ --include="*.ts" --include="*.tsx" | grep -v "node_modules"
# Should only show logger.ts and dev-only code

# Build production bundle and check size
cd cms-vite
npm run build
# Debug logs should be tree-shaken (removed) in production
```

---

#### 2.2 Cleanup: Delete Old Files
**Impact**: Reduce confusion, reduce bundle size
**Files**: 10 files (118KB)
**Effort**: 30 minutes

**Solution**:

```bash
# Priority 1 - CMS Old Files
rm /mnt/g/khoirul/signate/cms-vite/src/features/pms/pages/PMSConfigPage.old.tsx
rm /mnt/g/khoirul/signate/cms-vite/src/features/schedules/pages/SchedulesPage.old.tsx
rm /mnt/g/khoirul/signate/cms-vite/src/features/templates/pages/TemplatesPage.old.tsx
rm /mnt/g/khoirul/signate/cms-vite/src/features/translations/pages/TranslationsPage.old.tsx
rm /mnt/g/khoirul/signate/cms-vite/src/features/widgets/pages/WidgetsPage.old.tsx

# Priority 2 - Backend/Player Backups
rm /mnt/g/khoirul/signate/backend-python/tasks/content_tasks.py.backup
rm /mnt/g/khoirul/signate/player-vite/src/player/components/device-info-popup.ts.backup

# Priority 3 - Clarify Docker Compose Files (rename, don't delete)
cd /mnt/g/khoirul/signate/docker
mv docker-compose.yml docker-compose.production.yml
mv docker-compose.old.yml docker-compose.development.yml
ln -s docker-compose.production.yml docker-compose.yml

# Priority 4 - Delete redundant .env files
rm docker/.env.example docker/.env.local docker/.env.production
rm -rf docker/envs/

# Verify
ls -lh cms-vite/src/features/*/pages/*.old.tsx  # Should be empty
ls -lh backend-python/tasks/*.backup  # Should be empty
ls -lh docker/*.yml  # Should show 3 files (2 real + 1 symlink)
```

---

### Priority 3: MEDIUM (Nice to Have) - 2 hours

#### 3.1 Create Deployment Verification Scripts
**Impact**: Verify deployment succeeded
**Files**: 3 new scripts
**Effort**: 1 hour

**Solution**:

```bash
# 1. Create scripts/validate-env.sh
mkdir -p /mnt/g/khoirul/signate/scripts
```

```bash
#!/bin/bash
# scripts/validate-env.sh
# Validates required environment variables

REQUIRED_VARS=(
  "DATABASE_URL"
  "REDIS_URL"
  "SECRET_KEY"
  "JWT_SECRET"
  "ENCRYPTION_KEY"
  "CORS_ORIGINS"
  "PUBLIC_BASE_URL"
  "PUBLIC_API_URL"
  "PUBLIC_CMS_URL"
  "PUBLIC_PLAYER_URL"
)

MISSING=()

for var in "${REQUIRED_VARS[@]}"; do
  if ! grep -q "^${var}=" .env 2>/dev/null; then
    MISSING+=("$var")
  fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
  echo "✅ All required environment variables are set"
  exit 0
else
  echo "❌ Missing required environment variables:"
  printf '  - %s\n' "${MISSING[@]}"
  exit 1
fi
```

```bash
# 2. Create scripts/verify-deployment.sh
```

```bash
#!/bin/bash
# scripts/verify-deployment.sh
# Verifies all services are healthy

SERVER_HOST="192.168.5.12"

echo "Checking service health..."

SERVICES=(
  "postgres:5433"
  "redis:6379"
  "backend-api:8001/health"
  "cms-frontend:3000"
  "player:8080"
  "nginx-proxy:443"
)

FAILED=()

for service in "${SERVICES[@]}"; do
  IFS=: read -r name endpoint <<< "$service"

  if docker ps | grep -q "$name"; then
    if [[ "$endpoint" =~ "/health" ]]; then
      # HTTP health check
      port="${endpoint%%/*}"
      path="/${endpoint#*/}"
      if curl -sf "http://${SERVER_HOST}:${port}${path}" > /dev/null; then
        echo "✅ $name is healthy"
      else
        echo "❌ $name is unhealthy"
        FAILED+=("$name")
      fi
    else
      # TCP port check
      if nc -z ${SERVER_HOST} "$endpoint" 2>/dev/null; then
        echo "✅ $name is running"
      else
        echo "❌ $name is not accessible"
        FAILED+=("$name")
      fi
    fi
  else
    echo "❌ $name is not running"
    FAILED+=("$name")
  fi
done

if [ ${#FAILED[@]} -eq 0 ]; then
  echo "✅ All services are healthy"
  exit 0
else
  echo "❌ Failed services:"
  printf '  - %s\n' "${FAILED[@]}"
  exit 1
fi
```

```bash
# 3. Create scripts/smoke-test.sh
```

```bash
#!/bin/bash
# scripts/smoke-test.sh
# Production smoke tests

SERVER_HOST="192.168.5.12"
API_URL="https://api.zhmhotels.online"
CMS_URL="https://admin.zhmhotels.online"
PLAYER_URL="https://player.zhmhotels.online"

echo "Running smoke tests..."

# Test 1: Backend API health
if curl -sf ${API_URL}/health > /dev/null; then
  echo "✅ Backend API health check passed"
else
  echo "❌ Backend API health check failed"
  exit 1
fi

# Test 2: Backend API docs
if curl -sf ${API_URL}/docs > /dev/null; then
  echo "✅ Backend API docs accessible"
else
  echo "❌ Backend API docs not accessible"
  exit 1
fi

# Test 3: Database connection
if docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT 1" > /dev/null 2>&1; then
  echo "✅ Database connection successful"
else
  echo "❌ Database connection failed"
  exit 1
fi

# Test 4: Redis connection
if docker exec signage-redis redis-cli ping | grep -q "PONG"; then
  echo "✅ Redis connection successful"
else
  echo "❌ Redis connection failed"
  exit 1
fi

# Test 5: CMS accessibility
if curl -sf ${CMS_URL} > /dev/null; then
  echo "✅ CMS admin accessible"
else
  echo "❌ CMS admin not accessible"
  exit 1
fi

# Test 6: Player accessibility
if curl -sf ${PLAYER_URL} > /dev/null; then
  echo "✅ Player accessible"
else
  echo "❌ Player not accessible"
  exit 1
fi

# Test 7: SSL certificates
if openssl s_client -connect api.zhmhotels.online:443 </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
  echo "✅ SSL certificate valid"
else
  echo "⚠️ SSL certificate validation failed (expected for self-signed)"
fi

echo "✅ All smoke tests passed"
```

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Verify
ls -lh scripts/*.sh
```

---

#### 3.2 Database: Update Hardcoded URLs
**Impact**: Content URLs point to old IP
**Files**: Database migration
**Effort**: 30 minutes

**Problem**: Database may contain hardcoded URLs in `contents` table

**Solution**:

```bash
# 1. Create migration file
# backend-python/migrations/046_update_hardcoded_urls.sql
```

```sql
-- Migration: 046
-- Description: Update hardcoded IPs to domain URLs
-- Date: 2025-11-24

BEGIN;

-- Update content URLs (file_url, thumbnail_url, hls_playlist_url)
UPDATE contents
SET
  file_url = REPLACE(file_url, 'http://192.168.5.12:8001', 'https://api.zhmhotels.online'),
  thumbnail_url = REPLACE(thumbnail_url, 'http://192.168.5.12:8001', 'https://api.zhmhotels.online'),
  hls_playlist_url = REPLACE(hls_playlist_url, 'http://192.168.5.12:8001', 'https://api.zhmhotels.online')
WHERE
  file_url LIKE '%192.168.5.12%'
  OR thumbnail_url LIKE '%192.168.5.12%'
  OR hls_playlist_url LIKE '%192.168.5.12%';

-- Verify changes
SELECT
  COUNT(*) as total_updated,
  COUNT(CASE WHEN file_url LIKE '%zhmhotels.online%' THEN 1 END) as file_url_updated,
  COUNT(CASE WHEN thumbnail_url LIKE '%zhmhotels.online%' THEN 1 END) as thumbnail_url_updated,
  COUNT(CASE WHEN hls_playlist_url LIKE '%zhmhotels.online%' THEN 1 END) as hls_updated
FROM contents
WHERE
  file_url LIKE '%zhmhotels.online%'
  OR thumbnail_url LIKE '%zhmhotels.online%'
  OR hls_playlist_url LIKE '%zhmhotels.online%';

COMMIT;
```

```bash
# 2. Backup database before migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/pre_migration_046_$(date +%Y%m%d_%H%M%S).sql

# 3. Upload migration
sshpass -p 'Password@2021' scp backend-python/migrations/046_*.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/

# 4. Run migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signage/backend-python/migrations/046_update_hardcoded_urls.sql"

# 5. Verify
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c \"SELECT COUNT(*) FROM contents WHERE file_url LIKE '%192.168.5.12%';\""
# Should return 0
```

---

#### 3.3 Documentation: Create Deployment Checklist
**Impact**: Ensure nothing is missed
**Files**: 1 new doc
**Effort**: 30 minutes

**Solution**:

```bash
# Create docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md
```

```markdown
# Production Deployment Checklist

## Pre-Deployment (Local)

### Environment Configuration
- [ ] `.env` updated with production domains
- [ ] `cms-vite/.env.production` created
- [ ] `player-vite/.env.production` created
- [ ] SSL certificates generated/obtained
- [ ] All hardcoded IPs replaced with domains

### Code Changes
- [ ] Backend: PUBLIC_BASE_URL system added
- [ ] Backend: All hardcoded IPs updated
- [ ] Frontend: console.log replaced with logger
- [ ] Docker: Resource limits added (11 services)
- [ ] Docker: Log rotation added (12 services)
- [ ] Docker: nginx-proxy service added
- [ ] Old files deleted (10 files)

### Build & Test
- [ ] Backend builds without errors
- [ ] CMS builds for production (`npm run build`)
- [ ] Player builds for production (`npm run build`)
- [ ] Docker compose validates (`docker-compose config`)
- [ ] Local smoke tests pass

### Git
- [ ] All changes committed
- [ ] Git branch: `feature/production-deployment`
- [ ] Changes pushed to remote

## Deployment (Server)

### Server Preparation
- [ ] DNS configured (*.zhmhotels.online → 192.168.5.12)
- [ ] Server accessible via SSH
- [ ] Server has sufficient disk space (>20GB free)
- [ ] Docker & Docker Compose installed
- [ ] Ports 80, 443 open in firewall

### Backup
- [ ] Database backed up
- [ ] Current .env backed up
- [ ] Current docker-compose.yml backed up

### File Upload
- [ ] Backend code synced to server
- [ ] CMS dist/ synced to server
- [ ] Player dist/ synced to server
- [ ] Docker configs synced to server
- [ ] SSL certificates uploaded to server

### Container Management
- [ ] Stop all containers
- [ ] Remove old containers
- [ ] Pull latest images (if using registry)
- [ ] Start with new docker-compose.yml

### Database Migration
- [ ] Migration 046 uploaded
- [ ] Migration 046 executed
- [ ] URLs verified (no 192.168.5.12 remaining)

## Post-Deployment

### Health Checks
- [ ] All containers running
- [ ] Backend health: curl https://api.zhmhotels.online/health
- [ ] CMS accessible: curl https://admin.zhmhotels.online
- [ ] Player accessible: curl https://player.zhmhotels.online
- [ ] Database responsive
- [ ] Redis responsive

### Functional Tests
- [ ] Login to CMS works
- [ ] Upload content works
- [ ] Content preview works
- [ ] Player registration works
- [ ] Player activation works
- [ ] Playlist scheduling works
- [ ] WebSocket connection works

### Monitoring
- [ ] Check logs for errors (1 hour)
- [ ] Monitor resource usage (CPU, memory, disk)
- [ ] Check SSL certificate valid
- [ ] Verify HTTPS redirects work
- [ ] Test from external network

## Rollback Procedure (If Needed)

- [ ] Stop new containers
- [ ] Restore database backup
- [ ] Restore old .env
- [ ] Restore old docker-compose.yml
- [ ] Start old containers
- [ ] Verify old system works
```

---

## DEPLOYMENT (Step-by-Step Manual Guide)

### Prerequisites Checklist

**Before starting, verify you have**:
- [ ] Local codebase at `/mnt/g/khoirul/signate/`
- [ ] Server access: `gzjbbk@192.168.5.12` (password: `Password@2021`)
- [ ] DNS configured: `*.zhmhotels.online` → `192.168.5.12`
- [ ] SSL certificates ready (self-signed for testing, Let's Encrypt for production)
- [ ] Git branch: `feature/production-deployment` (create if not exists)

**Estimated Total Time**: 4-6 hours

---

### Phase 1: Pre-Deployment Preparation (1 hour)

#### 1.1 Verify Local Environment

```bash
cd /mnt/g/khoirul/signate

# Check git status (should be clean or on feature branch)
git status

# Create feature branch if needed
git checkout -b feature/production-deployment

# Verify current structure
ls -lh backend-python/ cms-vite/ player-vite/ docker/
```

#### 1.2 Backup Production Database

```bash
# Create backups directory
mkdir -p backups/

# Backup production database
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/production_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup size (should be >1MB if data exists)
ls -lh backups/production_backup_*.sql | tail -1
```

#### 1.3 Backup Production Environment Files

```bash
# Backup .env files
sshpass -p 'Password@2021' scp gzjbbk@192.168.5.12:/home/gzjbbk/signate/.env \
  backups/production_env_backup_$(date +%Y%m%d).env

# Backup docker-compose
sshpass -p 'Password@2021' scp gzjbbk@192.168.5.12:/home/gzjbbk/signate/docker/docker-compose.yml \
  backups/production_compose_backup_$(date +%Y%m%d).yml

# Verify backups
ls -lh backups/*$(date +%Y%m%d)*
```

---

### Phase 2: Code Changes (2 hours)

#### 2.1 Backend: Add PUBLIC_BASE_URL System

```bash
# 1. Edit backend-python/shared/config.py
nano backend-python/shared/config.py
# Add after line 56 (after LOG_LEVEL):
#   PUBLIC_BASE_URL: str = ""

# 2. Update local_storage.py
nano backend-python/services/content/infrastructure/storage/local_storage.py
# Line 39: Add import and update base_url (see Priority 1.1 above)

# 3. Update content_repo.py
nano backend-python/services/content/repositories/content_repo.py
# Line 374: Update hls_master_playlist_url (see Priority 1.1 above)

# 4. Update log_routes.py
nano backend-python/services/device/log_routes.py
# Line 283: Update player URL (see Priority 1.1 above)

# 5. Update main.py CORS
nano backend-python/main.py
# Lines 203-204: Add production domains (see Priority 1.1 above)

# Verify changes
grep -n "PUBLIC_BASE_URL" backend-python/shared/config.py
grep -n "settings.PUBLIC_BASE_URL" backend-python/services/content/infrastructure/storage/local_storage.py
```

#### 2.2 Frontend: Update Environment Variables

```bash
# 1. Update root .env
nano .env
# Add production domain section (see Priority 1.2 above)

# 2. Create cms-vite/.env.production
cat > cms-vite/.env.production << 'EOF'
# CMS Production Environment Variables
VITE_API_URL=https://api.zhmhotels.online
VITE_WS_URL=wss://api.zhmhotels.online
VITE_PLAYER_URL=https://player.zhmhotels.online
EOF

# 3. Create player-vite/.env.production
cat > player-vite/.env.production << 'EOF'
# Player Production Environment Variables
VITE_API_BASE_URL=https://api.zhmhotels.online
VITE_WS_BASE_URL=wss://api.zhmhotels.online
EOF

# Verify
cat cms-vite/.env.production
cat player-vite/.env.production
```

#### 2.3 Docker: Add SSL Configuration

```bash
# 1. Create SSL directory
mkdir -p docker/ssl

# 2. Generate self-signed certificate (for testing)
cd docker/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout zhmhotels.key \
  -out zhmhotels.crt \
  -subj "/CN=*.zhmhotels.online/O=ZHM Hotels/C=ID" \
  -addext "subjectAltName=DNS:*.zhmhotels.online,DNS:zhmhotels.online"
cd ../..

# For production: Use Let's Encrypt instead (on server)
# certbot certonly --standalone -d api.zhmhotels.online -d admin.zhmhotels.online -d player.zhmhotels.online

# 3. Create nginx-proxy.conf
nano docker/nginx-proxy.conf
# Copy content from Priority 1.3 above

# 4. Update docker-compose.yml - add nginx-proxy service
nano docker/docker-compose.yml
# Add nginx-proxy service after player (see Priority 1.3 above)

# Verify SSL cert
openssl x509 -in docker/ssl/zhmhotels.crt -text -noout | grep "DNS:"
```

#### 2.4 Docker: Add Resource Limits & Log Rotation

```bash
# Edit docker-compose.yml
nano docker/docker-compose.yml

# Add resource limits to all 11 services (see Priority 1.4)
# Add log rotation to all 12 services (see Priority 1.5)

# Verify
grep -c "resources:" docker/docker-compose.yml
# Should output: 11

grep -c "logging:" docker/docker-compose.yml
# Should output: 12
```

#### 2.5 Cleanup: Delete Old Files

```bash
# Delete old CMS files
rm -f cms-vite/src/features/pms/pages/PMSConfigPage.old.tsx
rm -f cms-vite/src/features/schedules/pages/SchedulesPage.old.tsx
rm -f cms-vite/src/features/templates/pages/TemplatesPage.old.tsx
rm -f cms-vite/src/features/translations/pages/TranslationsPage.old.tsx
rm -f cms-vite/src/features/widgets/pages/WidgetsPage.old.tsx

# Delete backup files
rm -f backend-python/tasks/content_tasks.py.backup
rm -f player-vite/src/player/components/device-info-popup.ts.backup

# Rename docker-compose files for clarity
cd docker
mv docker-compose.yml docker-compose.production.yml
mv docker-compose.old.yml docker-compose.development.yml
ln -s docker-compose.production.yml docker-compose.yml
cd ..

# Delete redundant env files
rm -f docker/.env.example docker/.env.local docker/.env.production
rm -rf docker/envs/

# Verify
ls -lh docker/*.yml
# Should show docker-compose.yml (symlink), docker-compose.production.yml, docker-compose.development.yml
```

---

### Phase 3: Build & Test Locally (30 minutes)

#### 3.1 Build Backend

```bash
# No build needed for Python, just verify imports
cd backend-python
python3 -c "from shared.config import settings; print(settings.PUBLIC_BASE_URL)"
# Should not error
cd ..
```

#### 3.2 Build CMS for Production

```bash
cd cms-vite

# Install dependencies if needed
npm install

# Build for production
npm run build

# Verify build output
ls -lh dist/
# Should show index.html and assets/

# Check build size
du -sh dist/
# Should be ~2-5MB

cd ..
```

#### 3.3 Build Player for Production

```bash
cd player-vite

# Install dependencies if needed
npm install

# Build for production
npm run build

# Verify build output
ls -lh dist/
# Should show index.html and assets/

cd ..
```

#### 3.4 Validate Docker Compose

```bash
# Validate docker-compose syntax
cd docker
docker-compose config > /dev/null
# Should output nothing (means valid)

cd ..
```

---

### Phase 4: Deploy to Server (1 hour)

#### 4.1 Stop Running Services

```bash
# Stop containers on server (keep data!)
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml down"

# Verify stopped
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker ps | grep signage"
# Should be empty
```

#### 4.2 Sync Code to Server

```bash
# Sync backend
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' --exclude '*.pyc' \
  backend-python/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# Sync CMS dist
sshpass -p 'Password@2021' rsync -avz --delete \
  cms-vite/dist/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/cms-vite/dist/

# Sync Player dist
sshpass -p 'Password@2021' rsync -avz --delete \
  player-vite/dist/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/dist/

# Sync Docker configs
sshpass -p 'Password@2021' rsync -avz \
  docker/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/docker/

# Sync root .env
sshpass -p 'Password@2021' scp .env \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/.env

# Verify sync
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "ls -lh /home/gzjbbk/signate/"
```

#### 4.3 Start Services with New Configuration

```bash
# Start all services
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml up -d --build"

# Wait for services to start
sleep 60

# Check service status
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep signage"

# Check logs for errors
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend-python --tail 50"
```

---

### Phase 5: Database Migration (30 minutes)

#### 5.1 Run Migration 046 (Update URLs)

```bash
# Upload migration
sshpass -p 'Password@2021' scp backend-python/migrations/046_update_hardcoded_urls.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/

# Run migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signage/backend-python/migrations/046_update_hardcoded_urls.sql"

# Verify migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c \"SELECT COUNT(*) FROM contents WHERE file_url LIKE '%192.168.5.12%';\""
# Should return 0
```

---

### Phase 6: Verification & Testing (1 hour)

#### 6.1 Health Checks

```bash
# Backend health
curl -i https://api.zhmhotels.online/health
# Should return 200 OK

# Backend API docs
curl -i https://api.zhmhotels.online/docs
# Should return 200 OK

# CMS accessible
curl -i https://admin.zhmhotels.online
# Should return 200 OK

# Player accessible
curl -i https://player.zhmhotels.online
# Should return 200 OK

# Database connection
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c 'SELECT 1;'"
# Should return 1 row

# Redis connection
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-redis redis-cli ping"
# Should return PONG
```

#### 6.2 Functional Tests

**Test 1: Login to CMS**
```bash
# Open browser: https://admin.zhmhotels.online
# Login with: admin / admin123
# Should succeed
```

**Test 2: Upload Content**
```bash
# In CMS:
# 1. Go to Content > Upload
# 2. Upload a test image/video
# 3. Verify upload succeeds
# 4. Check preview works
```

**Test 3: Register Device**
```bash
# In Player (new browser):
# 1. Open: https://player.zhmhotels.online
# 2. Wait for activation code (6 digits)
# 3. Go to CMS > Devices
# 4. Enter activation code
# 5. Verify device shows "Active"
```

**Test 4: WebSocket Connection**
```bash
# Check WebSocket in browser console:
# Should see: [WebSocket] Connected
# Should NOT see connection errors
```

#### 6.3 SSL Certificate Verification

```bash
# Check SSL certificate
openssl s_client -connect api.zhmhotels.online:443 -servername api.zhmhotels.online </dev/null 2>/dev/null | openssl x509 -noout -text | grep "DNS:"

# For self-signed cert: Will show warning (expected)
# For Let's Encrypt: Should show valid certificate
```

#### 6.4 Monitor Logs (1 hour)

```bash
# Watch backend logs
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs -f signage-backend-python"

# Watch for errors:
# - Look for startup errors
# - Look for database connection errors
# - Look for CORS errors
# - Look for 500 errors

# Press Ctrl+C to exit after 10-15 minutes of monitoring
```

---

### Phase 7: Post-Deployment Monitoring (24 hours)

#### 7.1 Monitor Resource Usage

```bash
# Check Docker stats
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker stats --no-stream"

# Look for:
# - Memory usage < limits (should be under 80%)
# - CPU usage reasonable (< 50% average)
# - No OOM kills

# Check disk space
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "df -h"

# Should have >10GB free
```

#### 7.2 Check Log Files

```bash
# Check log file sizes (should be rotating)
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker inspect signage-backend-python | grep -A 5 LogConfig"

# Should show max-size: 10m, max-file: 5
```

#### 7.3 Performance Monitoring

```bash
# Check response times
time curl -s https://api.zhmhotels.online/health
# Should be < 1 second

# Check database performance
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c 'SELECT pg_size_pretty(pg_database_size(current_database()));'"
```

---

## ROLLBACK PROCEDURE

**If deployment fails or critical issues found:**

### Step 1: Stop New Services

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml down"
```

### Step 2: Restore Database Backup

```bash
# Find latest backup
ls -lht backups/production_backup_*.sql | head -1

# Restore database
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db" < backups/production_backup_YYYYMMDD_HHMMSS.sql
```

### Step 3: Restore Old Configuration

```bash
# Restore .env
sshpass -p 'Password@2021' scp backups/production_env_backup_YYYYMMDD.env \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/.env

# Restore docker-compose.yml
sshpass -p 'Password@2021' scp backups/production_compose_backup_YYYYMMDD.yml \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/docker/docker-compose.yml
```

### Step 4: Start Old System

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml up -d"
```

### Step 5: Verify Rollback

```bash
# Check services
curl http://192.168.5.12:8001/health
curl http://192.168.5.12:3000
curl http://192.168.5.12:8080

# Should all return 200 OK
```

---

## DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] All code changes committed to Git
- [ ] Production backups created (database + configs)
- [ ] DNS configured (*.zhmhotels.online)
- [ ] SSL certificates ready

### Code Changes
- [ ] Backend: PUBLIC_BASE_URL system added
- [ ] Backend: Hardcoded IPs replaced (5 locations)
- [ ] Frontend: Environment files created
- [ ] Docker: SSL/nginx-proxy configured
- [ ] Docker: Resource limits added (11 services)
- [ ] Docker: Log rotation added (12 services)
- [ ] Old files deleted (10 files)

### Build
- [ ] CMS production build completed
- [ ] Player production build completed
- [ ] Docker compose validated

### Deployment
- [ ] Services stopped on server
- [ ] Code synced to server
- [ ] Services started with new config
- [ ] Database migration 046 run

### Verification
- [ ] Health checks pass (6 endpoints)
- [ ] Functional tests pass (login, upload, device, websocket)
- [ ] SSL certificate valid
- [ ] Logs show no critical errors
- [ ] Resource usage within limits

### Monitoring (24 hours)
- [ ] Check logs every 4 hours
- [ ] Monitor resource usage
- [ ] Verify log rotation working
- [ ] Check user feedback

---

## TROUBLESHOOTING

### Issue: SSL Certificate Error

**Symptom**: Browser shows "Not Secure" or certificate invalid
**Solution**:
```bash
# Check certificate
openssl x509 -in docker/ssl/zhmhotels.crt -text -noout

# For production: Use Let's Encrypt
certbot certonly --standalone -d api.zhmhotels.online -d admin.zhmhotels.online -d player.zhmhotels.online
```

### Issue: CORS Error

**Symptom**: CMS cannot connect to API, CORS error in browser console
**Solution**:
```bash
# Check CORS_ORIGINS in backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-backend-python env | grep CORS_ORIGINS"

# Should include https://admin.zhmhotels.online
# If not, update .env and restart backend
```

### Issue: WebSocket Not Connecting

**Symptom**: Player shows "Connection Failed", WebSocket errors
**Solution**:
```bash
# Check nginx WebSocket config
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cat /home/gzjbbk/signate/docker/nginx-proxy.conf | grep -A 10 'location /ws'"

# Should have:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";
```

### Issue: Content URLs Still Show 192.168.5.12

**Symptom**: Content not loading, URLs in database still have old IP
**Solution**:
```bash
# Re-run migration 046
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/046_update_hardcoded_urls.sql"

# Verify
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db -c \"SELECT file_url FROM contents LIMIT 5;\""
```

### Issue: Out of Memory (OOM) Kills

**Symptom**: Services randomly restart, docker logs show OOM
**Solution**:
```bash
# Check resource limits are applied
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker inspect signage-backend-python | grep -A 5 Memory"

# Should show MemoryReservation and MemoryLimit
# If not, verify docker-compose.yml has deploy.resources
```

---

## TIMELINE SUMMARY

| Phase | Duration | Description |
|-------|----------|-------------|
| **Phase 1** | 1 hour | Pre-deployment preparation, backups |
| **Phase 2** | 2 hours | Code changes (hardcodes, configs, cleanup) |
| **Phase 3** | 30 min | Build & test locally |
| **Phase 4** | 1 hour | Deploy to server, sync files |
| **Phase 5** | 30 min | Database migration |
| **Phase 6** | 1 hour | Verification & testing |
| **Phase 7** | 24 hours | Post-deployment monitoring |
| **Total Active Work** | 6 hours | Hands-on deployment work |
| **Total with Monitoring** | 30 hours | Including overnight monitoring |

---

## SUCCESS CRITERIA

### Minimum Success (Option 1 - 4 hours)
- ✅ All services running with HTTPS
- ✅ Domain URLs working (*.zhmhotels.online)
- ✅ No hardcoded IPs in responses
- ✅ Basic functionality works (login, upload, device activation)
- ⚠️ console.log still present (not critical)
- ⚠️ Old files still present (not affecting production)

### Recommended Success (Option 2 - 6 hours)
- ✅ All from Option 1
- ✅ Production logger implemented
- ✅ Old files cleaned up
- ✅ Deployment verification scripts created
- ✅ No console.log in production build
- ✅ Resource limits + log rotation working

### Best Practices Success (Option 3 - 8 hours)
- ✅ All from Option 2
- ✅ Integration tests passing
- ✅ Monitoring alerts configured
- ✅ Full documentation complete
- ✅ CI/CD pipeline set up
- ✅ Grade A (95/100) achieved

---

## FINAL NOTES

### Critical Reminders

1. **Always backup** before making changes
2. **Test locally first** before deploying to server
3. **Monitor logs** for at least 1 hour after deployment
4. **Keep rollback files** for at least 7 days
5. **Document any issues** encountered during deployment

### Next Steps After Successful Deployment

1. **Week 1**: Monitor system performance, fix any issues
2. **Week 2**: Set up automated backups, configure monitoring alerts
3. **Week 3**: Add integration tests, improve CI/CD
4. **Month 1**: Review logs, optimize performance, plan next features

### Support

- **Architecture Questions**: See FASE_2_AGENT_6 Section 3
- **Deployment Issues**: See Troubleshooting section above
- **Database Issues**: See docs/DATABASE_CONVENTIONS.md
- **API Issues**: See http://192.168.5.12:8001/docs (or https://api.zhmhotels.online/docs)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Prepared By**: Agent 7 - Final Synthesis & Deployment Planning
**Status**: Ready for Production Deployment
