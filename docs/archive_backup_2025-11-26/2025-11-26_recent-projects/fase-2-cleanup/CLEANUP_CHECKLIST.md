# Cleanup Checklist - Pre-Deployment

**Date**: 2025-11-24
**Based on**: FASE_2_AGENT_6_ARCHITECTURE_CLEANUP_REVIEW.md

---

## Priority 1: MUST DO BEFORE DEPLOYMENT (2 hours)

### 1. Delete Old CMS Files (5 files, 58KB)

```bash
# Verify files are not imported anywhere
grep -r "PMSConfigPage.old" cms-vite/src
grep -r "SchedulesPage.old" cms-vite/src
grep -r "TemplatesPage.old" cms-vite/src
grep -r "TranslationsPage.old" cms-vite/src
grep -r "WidgetsPage.old" cms-vite/src

# If no matches, safe to delete
rm cms-vite/src/features/pms/pages/PMSConfigPage.old.tsx
rm cms-vite/src/features/schedules/pages/SchedulesPage.old.tsx
rm cms-vite/src/features/templates/pages/TemplatesPage.old.tsx
rm cms-vite/src/features/translations/pages/TranslationsPage.old.tsx
rm cms-vite/src/features/widgets/pages/WidgetsPage.old.tsx

# Commit
git add -A
git commit -m "chore: Remove old CMS page files"
```

- [ ] Verified files not imported
- [ ] Deleted 5 old CMS files
- [ ] Committed changes

### 2. Clarify Docker Compose Files

```bash
cd docker/

# Rename for clarity
mv docker-compose.yml docker-compose.production.yml
mv docker-compose.old.yml docker-compose.development.yml

# Create symlink (default to production)
ln -s docker-compose.production.yml docker-compose.yml

# Update README
cat >> README.md << 'EOF'
# Docker Compose Files

- `docker-compose.yml` → Symlink to production
- `docker-compose.production.yml` → Production setup (monitoring, security)
- `docker-compose.development.yml` → Development setup (storage services)

Usage:
  Production:  docker-compose up -d
  Development: docker-compose -f docker-compose.development.yml up -d
EOF

# Commit
git add -A
git commit -m "docs: Clarify docker-compose file naming"
```

- [ ] Renamed compose files
- [ ] Created symlink
- [ ] Updated docker/README.md
- [ ] Committed changes

### 3. Add Resource Limits to Docker Compose

```bash
cd docker/

# Edit docker-compose.production.yml
# Add to each service (see FASE_2_AGENT_6 report section 5)
```

**Add these limits**:

```yaml
# backend-api
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '2.0'
    reservations:
      memory: 512M

# celery-worker
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '4.0'

# postgres
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'

# clamav
deploy:
  resources:
    limits:
      memory: 1G

# All other services
deploy:
  resources:
    limits:
      memory: 512M
```

- [ ] Added resource limits
- [ ] Tested locally
- [ ] Committed changes

### 4. Add Log Rotation to Docker Compose

```bash
# Edit docker-compose.production.yml
# Add to ALL services
```

**Add logging config**:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"
    labels: "production"
```

- [ ] Added log rotation to all services
- [ ] Tested locally
- [ ] Committed changes

### 5. Merge Duplicate Template Types

```bash
cd cms-vite/src/features/templates/types/

# 1. Compare files
diff template.ts template.types.ts

# 2. Merge: Keep template.types.ts (has UI metadata)
# Copy missing types from template.ts if any

# 3. Find all imports
grep -r "from.*template\.ts" ../../

# 4. Update imports to use template.types.ts
# 5. Delete template.ts
rm template.ts

# 6. Test build
cd ../../../..
npm run build

# Commit
git add -A
git commit -m "refactor: Merge duplicate template type definitions"
```

- [ ] Compared both files
- [ ] Merged types
- [ ] Updated imports
- [ ] Deleted template.ts
- [ ] Build successful
- [ ] Committed changes

---

## Priority 2: PRODUCTION HARDENING (4 hours)

### 6. Create Logger Utility for CMS

```bash
# Create cms-vite/src/shared/utils/logger.ts
```

**File contents**:

```typescript
/**
 * Production-safe logger utility
 * Debug logs are tree-shaken in production builds
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  level: LogLevel;
  enabledInProduction: boolean;
}

const config: LoggerConfig = {
  level: import.meta.env.DEV ? 'debug' : 'info',
  enabledInProduction: false,
};

const logger = {
  debug: (message: string, ...data: any[]) => {
    if (import.meta.env.DEV) {
      console.log(`[DEBUG] ${message}`, ...data);
    }
  },

  info: (message: string, ...data: any[]) => {
    console.info(`[INFO] ${message}`, ...data);
  },

  warn: (message: string, ...data: any[]) => {
    console.warn(`[WARN] ${message}`, ...data);
  },

  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error);
  },
};

export default logger;
```

- [ ] Created logger.ts
- [ ] Tested in dev mode
- [ ] Committed changes

### 7. Replace console.log Statements

```bash
cd cms-vite/src

# Files to update (69 console.log statements in 4 files):
# - features/auth/hooks/useAuth.ts
# - features/devices/api/deviceApi.ts
# - features/devices/api/logsApi.ts
# - (check for more)

# Replace pattern:
# console.log(...) → logger.debug(...)
# console.error(...) → logger.error(...)
# console.warn(...) → logger.warn(...)

# Add import:
# import logger from '@/shared/utils/logger';

# Build and verify no console.log in production
npm run build
grep -r "console.log" dist/ && echo "FOUND console.log in build!" || echo "Clean build!"
```

- [ ] Replaced console.log in useAuth.ts
- [ ] Replaced console.log in deviceApi.ts
- [ ] Replaced console.log in logsApi.ts
- [ ] Verified production build clean
- [ ] Committed changes

### 8. Centralize .env Files

```bash
# Keep only:
# - /.env (master)
# - /.env.example
# - /backend-python/.env.local (optional overrides)
# - /cms-vite/.env.local (optional overrides)
# - /player-vite/.env.local (optional overrides)

# Delete redundant files:
rm docker/.env.example
rm docker/.env.local
rm docker/.env.production
rm -rf docker/envs/

# Update .gitignore
cat >> .gitignore << 'EOF'
# Environment files
.env.local
.env.*.local
EOF

git add -A
git commit -m "chore: Centralize .env files, remove redundant copies"
```

- [ ] Deleted redundant .env files
- [ ] Updated .gitignore
- [ ] Documented .env hierarchy
- [ ] Committed changes

### 9. Create Deployment Scripts

```bash
mkdir -p scripts/

# Create scripts/validate-env.sh
# Create scripts/verify-deployment.sh
# Create scripts/smoke-test.sh
# (See FASE_2_AGENT_6 report section 7 for script contents)

chmod +x scripts/*.sh

git add scripts/
git commit -m "feat: Add deployment validation and verification scripts"
```

- [ ] Created validate-env.sh
- [ ] Created verify-deployment.sh
- [ ] Created smoke-test.sh
- [ ] Made scripts executable
- [ ] Tested scripts locally
- [ ] Committed changes

### 10. Create Deployment Documentation

```bash
# Create docs/deployment/DEPLOYMENT_MANUAL.md
# Create docs/deployment/DEPLOYMENT_CHECKLIST.md
# Create docs/deployment/ROLLBACK_PROCEDURE.md
# (See FASE_2_AGENT_6 report section 7 for templates)

git add docs/deployment/
git commit -m "docs: Add deployment and rollback documentation"
```

- [ ] Created DEPLOYMENT_MANUAL.md
- [ ] Created DEPLOYMENT_CHECKLIST.md
- [ ] Created ROLLBACK_PROCEDURE.md
- [ ] Committed changes

---

## Priority 3: NICE-TO-HAVE (2 hours)

### 11. Delete Backup Files

```bash
# Backend backup
rm backend-python/tasks/content_tasks.py.backup

# Player backup
rm player-vite/src/player/components/device-info-popup.ts.backup

# Archived (optional - can delete entire _archived/ folder)
# rm -rf _archived/

git add -A
git commit -m "chore: Remove backup files"
```

- [ ] Deleted backend backup
- [ ] Deleted player backup
- [ ] Considered deleting _archived/ folder
- [ ] Committed changes

### 12. Convert Backend TODOs to GitHub Issues

```bash
# List all TODOs
grep -rn "TODO\|FIXME" backend-python/ --include="*.py"

# For each TODO:
# 1. Create GitHub issue
# 2. Link issue in code: # TODO: Description (Issue #XX)
# 3. Or remove if completed
```

- [ ] Created GitHub issues for TODOs
- [ ] Linked issues in code
- [ ] Removed completed TODOs
- [ ] Committed changes

### 13. Create ARCHITECTURE.md

```bash
# Create docs/ARCHITECTURE.md
# High-level system diagram
# Component relationships
# Data flow diagrams
# (Use Mermaid for diagrams)
```

- [ ] Created ARCHITECTURE.md
- [ ] Added system diagrams
- [ ] Documented data flows
- [ ] Committed changes

### 14. Final Verification

```bash
# Run all verification scripts
./scripts/validate-env.sh
./scripts/verify-deployment.sh
./scripts/smoke-test.sh

# Build all components
cd backend-python && docker build -t signage-backend .
cd ../cms-vite && npm run build
cd ../player-vite && npm run build

# Check for issues
grep -r "console.log" cms-vite/dist/ || echo "✅ No console.log in CMS build"
grep -r "TODO" backend-python/ --include="*.py" | wc -l
find . -name "*.old" -o -name "*.backup" -o -name "*.bak" | wc -l
```

- [ ] All scripts pass
- [ ] All builds successful
- [ ] No console.log in production
- [ ] TODOs converted or documented
- [ ] No old/backup files remaining

---

## Final Checklist

- [ ] **Priority 1 completed** (2 hours) - MUST DO BEFORE DEPLOYMENT
- [ ] **Priority 2 completed** (4 hours) - Production hardening
- [ ] **Priority 3 completed** (2 hours) - Nice-to-have improvements
- [ ] **All changes committed** to Git
- [ ] **Changes tested** locally
- [ ] **Documentation updated**
- [ ] **Ready for deployment** to production

---

## Deployment Commands

After checklist completion:

```bash
# On local machine
git push origin feature/api-integration

# On server (192.168.5.12)
cd /home/gzjbbk/signate
git pull origin feature/api-integration

# Validate environment
./scripts/validate-env.sh

# Deploy
docker-compose down
docker-compose up -d --build

# Verify deployment
./scripts/verify-deployment.sh

# Run smoke tests
./scripts/smoke-test.sh

# Monitor logs
docker-compose logs -f --tail=100
```

---

**Total Estimated Time**: 8 hours
**Current State**: B+ (85/100)
**Target State**: A (95/100)

**Next Steps**: Start with Priority 1 items (2 hours, blocking deployment)
