# Configuration Migration Guide
## From Hardcoded to Environment-Based Configuration

**Version:** 1.0.0
**Date:** October 27, 2025

---

## Overview

This guide provides step-by-step instructions for migrating the Smart TV Digital Signage system from hardcoded configuration values to a unified environment-based configuration system.

---

## Pre-Migration Checklist

- [ ] Backup current configuration files
- [ ] Document all current hardcoded values
- [ ] Test current system functionality
- [ ] Prepare rollback plan
- [ ] Notify team of migration schedule
- [ ] Review new configuration architecture

---

## Phase 1: Backend Migration

### Step 1.1: Update Configuration Module

**File:** `backend/app/core/config.py`

```python
# OLD (Hardcoded)
class Settings:
    API_BASE_URL = "http://192.168.5.12:8001"
    DATABASE_URL = "postgresql://user:pass@localhost/db"

# NEW (Environment-based)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_BASE_URL: str = Field(env="API_BASE_URL")
    DATABASE_URL: str = Field(env="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )
```

### Step 1.2: Update Database Connection

**File:** `backend/app/database.py`

```python
# OLD
engine = create_engine(
    "postgresql://signage_user:password@192.168.5.12:5433/signage_db"
)

# NEW
from app.core.config import settings
engine = create_engine(settings.DATABASE_URL)
```

### Step 1.3: Update API Endpoints

**Files to update:**
- `backend/app/api/devices.py`
- `backend/app/api/content.py`
- `backend/app/api/playlists.py`

Replace all hardcoded URLs with `settings.API_BASE_URL`

### Step 1.4: Test Backend Changes

```bash
# Set environment variables
export DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/test_db
export API_BASE_URL=http://localhost:8001

# Run tests
pytest backend/tests/

# Start backend
uvicorn app.main:app --reload
```

---

## Phase 2: Frontend Migration (Web Admin)

### Step 2.1: Create Configuration Module

**File:** `web-admin/src/config/index.js`

```javascript
// NEW configuration module
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8001',
    timeout: import.meta.env.VITE_API_TIMEOUT || 30000
  },
  features: {
    multiTenancy: import.meta.env.VITE_FEATURE_MULTI_TENANCY === 'true'
  }
};
```

### Step 2.2: Update API Service

**File:** `web-admin/src/services/api.js`

```javascript
// OLD
const API_BASE_URL = 'http://192.168.5.12:8001'

// NEW
import { config } from '../config'
const API_BASE_URL = config.api.baseUrl
```

### Step 2.3: Update Vite Configuration

**File:** `web-admin/vite.config.js`

```javascript
// Add environment variable loading
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    // ... other config
    define: {
      'process.env': env
    }
  }
})
```

### Step 2.4: Test Frontend Changes

```bash
# Create .env file
echo "VITE_API_URL=http://localhost:8001" > web-admin/.env

# Start development server
npm run dev

# Build for production
npm run build
```

---

## Phase 3: Viewer Migration

### Step 3.1: Add Configuration Loader

**File:** `viewer/js/config/loader.js`

Copy the `viewer-config-loader.js` file provided and include it in `viewer/index.html`:

```html
<script src="js/config/loader.js"></script>
```

### Step 3.2: Update Shell Configuration

**File:** `viewer/js/shell/config.js`

```javascript
// OLD
window.ShellState = {
    API_BASE_URL: 'http://192.168.5.12:8001',
    HEARTBEAT_INTERVAL: 30000
}

// NEW
window.ShellState = {
    API_BASE_URL: null, // Will be set by config loader
    HEARTBEAT_INTERVAL: null
}

// Wait for config to load
document.addEventListener('DOMContentLoaded', function() {
    window.ViewerConfig.init().then(config => {
        window.ShellState.API_BASE_URL = config.apiUrl;
        window.ShellState.HEARTBEAT_INTERVAL = config.heartbeatInterval;
    });
});
```

### Step 3.3: Update Player Configuration

**File:** `viewer/js/player/config.js`

Similar changes as Shell configuration.

### Step 3.4: Add Meta Tags for Configuration

**File:** `viewer/index.html`

```html
<head>
  <!-- Configuration meta tags -->
  <meta name="viewer-api-url" content="${VIEWER_API_URL}">
  <meta name="viewer-heartbeat-interval" content="${VIEWER_HEARTBEAT_INTERVAL}">
  <meta name="viewer-cache-enabled" content="${VIEWER_CACHE_ENABLED}">
</head>
```

---

## Phase 4: Docker Migration

### Step 4.1: Update Docker Compose

**File:** `docker/docker-compose.yml`

```yaml
# OLD
services:
  backend-api:
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - API_BASE_URL=http://192.168.5.12:8001

# NEW
services:
  backend-api:
    env_file:
      - ../.env
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - API_BASE_URL=${API_BASE_URL}
```

### Step 4.2: Create .env File

```bash
# Copy template
cp docker/.env.example .env

# Edit configuration
nano .env
```

### Step 4.3: Rebuild Containers

```bash
# Stop existing services
docker-compose down

# Rebuild with new configuration
docker-compose build --no-cache

# Start services
docker-compose up -d
```

---

## Phase 5: Testing & Validation

### Step 5.1: Run Validation Script

```bash
cd docker
chmod +x validate-config.sh
./validate-config.sh
```

### Step 5.2: Test Each Component

1. **Backend API**
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/api/devices
   ```

2. **Web Admin**
   - Open http://localhost:3000
   - Login and verify API connections
   - Check all CRUD operations

3. **Viewer**
   - Open http://localhost:8080
   - Check device registration
   - Verify playlist loading
   - Monitor heartbeat logs

### Step 5.3: Check Logs

```bash
# Backend logs
docker-compose logs -f backend-api

# All service logs
docker-compose logs -f
```

---

## Migration Timeline

### Week 1: Preparation
- Day 1-2: Audit current configuration
- Day 3-4: Setup test environment
- Day 5: Create migration scripts

### Week 2: Backend Migration
- Day 1-2: Update configuration module
- Day 3-4: Update all services
- Day 5: Testing and fixes

### Week 3: Frontend Migration
- Day 1-2: Web Admin migration
- Day 3-4: Viewer migration
- Day 5: Integration testing

### Week 4: Deployment
- Day 1: Deploy to staging
- Day 2-3: Staging testing
- Day 4: Production deployment
- Day 5: Monitoring and fixes

---

## Rollback Plan

If issues occur during migration:

### Quick Rollback

```bash
# Restore old configuration
cp .env.backup .env

# Revert to previous Docker images
docker-compose down
git checkout previous-version
docker-compose up -d
```

### Database Rollback

```bash
# Restore database backup
docker-compose exec postgres psql -U signage_user signage_db < backup.sql
```

---

## Common Issues & Solutions

### Issue 1: Environment Variables Not Loading

**Symptom:** Services using default values instead of .env

**Solution:**
```bash
# Check .env file location
ls -la .env

# Verify Docker Compose is reading env file
docker-compose config

# Check environment in container
docker-compose exec backend-api env
```

### Issue 2: CORS Errors

**Symptom:** Frontend cannot connect to API

**Solution:**
```bash
# Update CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:3000,http://192.168.5.12:3000

# Restart backend
docker-compose restart backend-api
```

### Issue 3: Database Connection Failed

**Symptom:** Backend cannot connect to PostgreSQL

**Solution:**
```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB

# Check DATABASE_URL format
echo $DATABASE_URL
```

### Issue 4: Viewer Not Loading Configuration

**Symptom:** Viewer using hardcoded values

**Solution:**
1. Clear browser cache
2. Check meta tags in HTML
3. Verify config endpoint: `curl http://localhost:8001/api/viewer/config`
4. Check browser console for errors

---

## Post-Migration Tasks

1. **Update Documentation**
   - Update README with new setup instructions
   - Document all environment variables
   - Update deployment guides

2. **Team Training**
   - Conduct training session on new configuration system
   - Share this migration guide
   - Create troubleshooting documentation

3. **Monitoring Setup**
   - Set up alerts for configuration errors
   - Monitor service health
   - Track performance metrics

4. **Security Review**
   - Audit all secrets management
   - Review CORS settings
   - Check file permissions

5. **Automation**
   - Create CI/CD pipeline updates
   - Automate configuration validation
   - Set up automated backups

---

## Success Criteria

Migration is considered successful when:

- [ ] All hardcoded values replaced with environment variables
- [ ] All services start without errors
- [ ] Configuration validation passes
- [ ] All tests pass
- [ ] No regression in functionality
- [ ] Documentation is updated
- [ ] Team is trained on new system

---

## Support

For issues during migration:

1. Check this guide first
2. Review UNIFIED_ENV_ARCHITECTURE.md
3. Check service logs
4. Run validation script
5. Contact DevOps team

---

## Appendix: Quick Commands

```bash
# Validate configuration
./validate-config.sh

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend-api

# Check service status
docker-compose ps

# Execute command in container
docker-compose exec backend-api bash

# View environment variables
docker-compose exec backend-api env

# Test API endpoint
curl http://localhost:8001/health

# Backup database
docker-compose exec postgres pg_dump -U signage_user signage_db > backup.sql

# Restore database
docker-compose exec postgres psql -U signage_user signage_db < backup.sql
```