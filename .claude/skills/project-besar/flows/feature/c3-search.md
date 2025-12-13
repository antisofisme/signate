---
description: Create search feature with Meilisearch for PROJECT_BESAR
---

# Flow C3: Create Search Feature

## Pre-requisites
- [ ] Searchable entity identified
- [ ] Search fields defined
- [ ] Facets identified

## Step 1: Create Index Service
Location: `modules/{module}/backend/app/services/search/{entity}_indexer.py`

```python
from meilisearch import Client

class {Entity}Indexer:
    def __init__(self):
        self.client = Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        self.index = self.client.index('{entities}')

    async def index_entity(self, entity: {Entity}):
        doc = {
            'id': str(entity.id),
            'tenant_id': str(entity.tenant_id),
            'name': entity.name,
            # Add searchable fields
        }
        await self.index.add_documents([doc])

    async def search(self, query: str, tenant_id: str, filters: dict = None):
        return await self.index.search(
            query,
            filter=f"tenant_id = {tenant_id}",
            facets=['status', 'category'],
            limit=20
        )
```

## Step 2: Sync on Changes
```python
# In service after create/update
await indexer.index_entity(entity)

# Or via event consumer
@event_handler("{module}.{entity}.created")
async def handle_created(self, event):
    await self.indexer.index_entity(event['data'])
```

## Step 3: Create Search API
```python
@router.get("/search/{entities}")
async def search_{entities}(
    q: str,
    tenant_id: UUID = Depends(get_tenant_id),
    indexer: {Entity}Indexer = Depends()
):
    results = await indexer.search(q, str(tenant_id))
    return results
```

## Step 4: Create Frontend Search
```typescript
const { data, isLoading } = useSearch{Entity}(debouncedQuery);

<SearchInput
  value={query}
  onChange={setQuery}
  placeholder="Search {entities}..."
/>

{data?.hits.map(hit => <SearchResult key={hit.id} item={hit} />)}
```

## Checklist Before Complete
- [ ] Index configured with searchable fields
- [ ] tenant_id filter enforced
- [ ] Sync on create/update/delete
- [ ] Faceted search works
- [ ] Frontend debounced
