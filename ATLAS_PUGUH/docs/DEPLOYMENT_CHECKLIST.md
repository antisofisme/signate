# ATLAS_PUGUH Deployment Checklist

Pre-deployment checklist for production releases.

## Pre-Deployment

### 1. Code Review
- [ ] All changes reviewed and approved
- [ ] No console.log/print statements in production code
- [ ] No hardcoded credentials or secrets
- [ ] No TODO comments for critical features

### 2. Database
- [ ] All migrations tested locally
- [ ] Migrations tested on staging
- [ ] Backup created before migration
- [ ] Rollback scripts available
- [ ] Data migration scripts tested (011_data_migration.sql)

### 3. Environment Variables
- [ ] All required env vars documented
- [ ] Production values set correctly
- [ ] Secrets stored in secure vault
- [ ] No development values in production

Required variables:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/atlas_puguh

# JWT
JWT_SECRET_KEY=<secure-random-string>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Midtrans (Payment)
MIDTRANS_SERVER_KEY=<production-key>
MIDTRANS_CLIENT_KEY=<production-key>
MIDTRANS_IS_PRODUCTION=true
MIDTRANS_WEBHOOK_SECRET=<webhook-secret>

# OAuth
GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<client-secret>
GITHUB_CLIENT_ID=<client-id>
GITHUB_CLIENT_SECRET=<client-secret>

# CORS
CORS_ORIGINS=https://admin-puguh.atlashub.com
```

### 4. Security
- [ ] HTTPS enforced
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Webhook signatures verified
- [ ] Input sanitization active
- [ ] SQL injection protection verified
- [ ] XSS protection headers set

### 5. Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing (critical paths)
- [ ] Load testing completed
- [ ] Security scan completed

## Deployment Steps

### 1. Prepare
```bash
# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### 2. Database Migration
```bash
# SSH to server
ssh deploy@vps-production

# Apply migrations
cd /opt/atlas_puguh
psql -f backend/migrations/011_data_migration.sql
```

### 3. Deploy Backend
```bash
# Update Nomad job
nomad job plan nomad/puguh-backend.nomad
nomad job run nomad/puguh-backend.nomad

# Verify deployment
nomad job status puguh-backend
```

### 4. Deploy Frontend
```bash
# Build frontend
cd frontend
bun run build

# Deploy to CDN/server
rsync -avz dist/ deploy@vps:/opt/atlas_puguh/frontend/

# Or via Nomad
nomad job run nomad/puguh-frontend.nomad
```

### 5. Verify Deployment

Health checks:
```bash
# Backend health
curl https://api-puguh.atlashub.com/health

# Frontend
curl https://admin-puguh.atlashub.com
```

## Post-Deployment

### 1. Monitoring
- [ ] Check error rates in logs
- [ ] Verify metrics dashboard
- [ ] Monitor memory/CPU usage
- [ ] Check database connections

### 2. Verification
- [ ] Login flow works
- [ ] Registration flow works
- [ ] OAuth login works
- [ ] Payment flow works (test transaction)
- [ ] Project creation works
- [ ] API endpoints responding

### 3. Documentation
- [ ] Changelog updated
- [ ] API docs updated
- [ ] User guide updated
- [ ] Release notes published

## Rollback Procedure

### 1. Quick Rollback
```bash
# Rollback to previous version
nomad job revert puguh-backend <previous-version>
nomad job revert puguh-frontend <previous-version>
```

### 2. Database Rollback
```bash
# Run rollback script
psql -f backend/migrations/rollback/011_rollback.sql
```

### 3. Verify Rollback
```bash
# Check health
curl https://api-puguh.atlashub.com/health
```

## Emergency Contacts

| Role | Contact |
|------|---------|
| DevOps Lead | devops@atlashub.com |
| Backend Lead | backend@atlashub.com |
| Database Admin | dba@atlashub.com |
| Security Team | security@atlashub.com |

## Known Issues

Document any known issues that may affect deployment:

1. _None currently documented_

---

*Checklist version: 1.0.0*
*Last updated: January 2026*
