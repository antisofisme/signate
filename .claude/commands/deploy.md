---
description: Deployment workflow for PROJECT_BESAR
---

# Deploy Command

Workflow deployment ke staging/production.

## Pre-Deployment

1. **Verify Tests**
   ```bash
   # All tests must pass
   cd PROJECT_BESAR/backend && pytest
   cd PROJECT_BESAR/frontend && bun test
   ```

2. **Build Images**
   ```bash
   # Backend
   docker build -t project-besar-api:latest ./backend

   # Frontend
   docker build -t project-besar-web:latest ./frontend
   ```

3. **Migration Check**
   ```bash
   # Verify migrations
   alembic check
   alembic history
   ```

## Staging Deployment

```bash
# Push to staging
docker push registry/project-besar-api:staging
docker push registry/project-besar-web:staging

# Deploy
kubectl apply -f k8s/staging/

# Verify
kubectl get pods -n staging
```

## Production Deployment

```bash
# Tag release
git tag v1.x.x
docker tag project-besar-api:latest project-besar-api:v1.x.x

# Push to production
docker push registry/project-besar-api:v1.x.x

# Run migrations first
kubectl exec -it api-pod -- alembic upgrade head

# Deploy
kubectl set image deployment/api api=project-besar-api:v1.x.x

# Verify
kubectl rollout status deployment/api
```

## Post-Deployment

- [ ] Smoke test critical paths
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Update release notes

## Rollback

```bash
# Quick rollback
kubectl rollout undo deployment/api

# Database rollback (if needed)
kubectl exec -it api-pod -- alembic downgrade -1
```
