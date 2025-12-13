---
description: Performance optimization for PROJECT_BESAR
---

# Flow E3: Performance Optimization

## SLA Targets (Standard #26)
| Metric | Target |
|--------|--------|
| API response (p95) | < 200ms |
| Database query (p95) | < 50ms |
| Page load (LCP) | < 2.5s |
| TTI | < 3.8s |

## Steps

### 1. Profile
```bash
# Backend
py-spy record -o profile.svg --pid <PID>

# Database
EXPLAIN (ANALYZE, BUFFERS) SELECT ...

# Frontend
npx lighthouse http://localhost:3000 --view
```

### 2. Identify Bottleneck

| Bottleneck | Solution |
|------------|----------|
| Slow DB query | Add index, optimize query |
| N+1 queries | Eager loading |
| No caching | Add Redis cache |
| Large payload | Pagination, compression |
| Large bundle | Code splitting |
| Re-renders | Memoization |

### 3. Implement Fix

```python
# Add index
op.create_index('ix_table_column', 'table', ['column'])

# Add caching
@cache.cached(ttl=300, key="entity:{id}")
async def get_entity(id):
    ...

# Eager loading
select(Entity).options(selectinload(Entity.relation))
```

### 4. Measure Improvement
Compare before/after metrics against SLA targets.

## Checklist
- [ ] Baseline measured
- [ ] Bottleneck identified
- [ ] Fix implemented
- [ ] Improvement measured
- [ ] SLA met
