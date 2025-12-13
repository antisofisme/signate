---
description: Update API documentation for PROJECT_BESAR
---

# Flow F2: Update API Documentation

## Steps

### 1. Update OpenAPI Spec
FastAPI auto-generates at `/openapi.json`

```python
@router.post(
    "/resources",
    response_model=ResourceResponse,
    responses={
        201: {"description": "Created"},
        400: {"description": "Validation error"},
    },
    summary="Create resource",
    description="Creates a new resource."
)
async def create_resource(data: ResourceCreate):
    """
    Create a new resource.

    - **name**: Resource name (required)
    - **type**: Resource type
    """
    ...
```

### 2. Update API.md

```markdown
## POST /api/v1/resources

### Description
Creates a new resource.

### Auth
Required. Bearer token.

### Permissions
- `module.resource.create`

### Request
\`\`\`json
{ "name": "string" }
\`\`\`

### Response
**201 Created**
\`\`\`json
{ "success": true, "data": { "id": "uuid", "name": "string" } }
\`\`\`
```

### 3. Update CHANGELOG.md

```markdown
## [1.2.0] - 2024-01-15

### Added
- POST /api/v1/resources

### Changed
- GET /api/v1/resources - Added pagination

### Breaking
- POST /api/v1/resources requires tenant_id
```

## Checklist
- [ ] OpenAPI spec updated
- [ ] API.md updated
- [ ] CHANGELOG updated
- [ ] Breaking changes documented
