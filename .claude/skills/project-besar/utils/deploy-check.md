---
description: Deployment checklist for PROJECT_BESAR
---

# Deployment Checklist

## Pre-Deployment
- [ ] All tests passing
- [ ] Code review approved
- [ ] Staging deployment successful
- [ ] Environment variables configured
- [ ] Database migrations ready

## Backend Deployment
- [ ] Build Docker image
- [ ] Push to registry
- [ ] Run migrations
- [ ] Deploy new version
- [ ] Health check passing
- [ ] Rollback plan ready

## Frontend Deployment
- [ ] Build production bundle
- [ ] Assets optimized
- [ ] Environment variables set
- [ ] Deploy to CDN/server
- [ ] Cache invalidation

## Post-Deployment
- [ ] Smoke test critical paths
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify integrations working

## Rollback Procedure
```bash
# Backend
docker pull previous-version
docker-compose up -d

# Database (if needed)
alembic downgrade -1

# Frontend
# Redeploy previous build
```

## Health Checks
```bash
# API health
curl https://api.domain.com/health

# Database connection
curl https://api.domain.com/health/db

# Redis connection
curl https://api.domain.com/health/redis
```

## Monitoring
- [ ] Application logs
- [ ] Error tracking (Sentry)
- [ ] Performance metrics
- [ ] Database slow queries
- [ ] API response times

## Emergency Contacts
- DevOps: [contact]
- Backend Lead: [contact]
- Frontend Lead: [contact]
