# API Standardization Quick Reference

**Last Updated:** October 28, 2025
**Current Progress:** 63.0% (104/165 endpoints)

## Quick Wins Pattern Checklist

Use this checklist when migrating endpoints to the standardized pattern:

### ✅ Step 1: Import Required Modules
```python
from fastapi import APIRouter, Depends, Request, Query
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, InternalServerException
from app.schemas.common import success_response, paginated_response
from app.middleware.request_id import get_request_id
```

### ✅ Step 2: Use Structured Logger
```python
# ❌ OLD WAY
logger = logging.getLogger(__name__)

# ✅ NEW WAY
logger = StructuredLogger(__name__)
```

### ✅ Step 3: Extract Request ID
```python
@router.get("/endpoint")
def my_endpoint(
    request: Request,  # Add Request parameter
    db: Session = Depends(get_db)
):
    request_id = get_request_id(request)  # Extract request ID

    logger.info(
        "Processing request",
        request_id=request_id,  # Include in logs
        user_id=user.id
    )
```

### ✅ Step 4: Use Page-Based Pagination (List Endpoints)
```python
# ❌ OLD WAY - skip/limit
@router.get("/items")
def list_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    items = db.query(Model).offset(skip).limit(limit).all()
    total = db.query(Model).count()
    return {"total": total, "items": items}

# ✅ NEW WAY - page/limit
@router.get("/items")
def list_items(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(100, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    request_id = get_request_id(request)

    # Calculate offset from page
    offset = (page - 1) * limit

    # Get total and items
    total = db.query(Model).count()
    items = db.query(Model).offset(offset).limit(limit).all()

    # Calculate total pages
    import math
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    return paginated_response(
        data=[item.to_dict() for item in items],
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )
```

### ✅ Step 5: Use Exception Classes
```python
# ❌ OLD WAY
from fastapi import HTTPException, status

if not item:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found"
    )

# ✅ NEW WAY
from app.core.exceptions import NotFoundException

if not item:
    raise NotFoundException(
        message="Item not found",
        resource_type="Item",
        resource_id=item_id
    )
```

### ✅ Step 6: Wrap Single Resource Responses
```python
# ❌ OLD WAY
@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

# ✅ NEW WAY
@router.get("/items/{item_id}")
def get_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    request_id = get_request_id(request)

    logger.info("Fetching item", request_id=request_id, item_id=item_id)

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise NotFoundException(
            message=f"Item with ID {item_id} not found",
            resource_type="Item",
            resource_id=item_id
        )

    logger.info("Item fetched successfully", request_id=request_id, item_id=item_id)

    return success_response(
        data=item.to_dict(),
        request_id=request_id
    )
```

### ✅ Step 7: Wrap Create Responses
```python
# ❌ OLD WAY
@router.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item_data: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**item_data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# ✅ NEW WAY
@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Creating item",
        request_id=request_id,
        user_id=current_user.id,
        item_name=item_data.name
    )

    try:
        item = Item(**item_data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)

        logger.info(
            "Item created successfully",
            request_id=request_id,
            item_id=item.id
        )

        return success_response(
            data=item.to_dict(),
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create item",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to create item: {str(e)}",
            details={"item_name": item_data.name}
        )
```

---

## Exception Classes Reference

### NotFoundException (404)
```python
raise NotFoundException(
    message="Resource not found",
    resource_type="Device",  # Type of resource
    resource_id=device_id    # ID of resource
)
```

### ConflictException (409)
```python
raise ConflictException(
    message="Resource already exists",
    field="email",           # Field causing conflict
    details={"email": "user@example.com"}
)
```

### BadRequestException (400)
```python
raise BadRequestException(
    message="Invalid input",
    details={"field": "duration", "reason": "must be positive"}
)
```

### ValidationException (422)
```python
raise ValidationException(
    message="Validation failed",
    field="email",
    details={"pattern": "^[a-z]+@[a-z]+\.[a-z]+$"}
)
```

### InternalServerException (500)
```python
raise InternalServerException(
    message="Unexpected error occurred",
    details={"operation": "database_query"}
)
```

---

## Response Format Examples

### Single Resource Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Example Item",
    "created_at": "2025-10-28T10:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "version": "1.0.0"
  }
}
```

### Paginated List Response
```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"}
  ],
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "version": "1.0.0",
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Device with ID 123 not found",
    "field": null,
    "details": {
      "resource_type": "Device",
      "resource_id": 123
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00.123Z",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "version": "1.0.0"
  }
}
```

---

## Structured Logging Examples

### Basic Log
```python
logger.info(
    "Processing request",
    request_id=request_id,
    user_id=current_user.id,
    device_id=device_id
)
```

### Log with Complex Data
```python
logger.info(
    "Content uploaded successfully",
    request_id=request_id,
    content_id=content.id,
    file_size=file_size,
    mime_type=mime_type,
    duration=duration,
    transcoding_enabled=transcode_on_upload
)
```

### Error Logging
```python
logger.error(
    "Failed to process request",
    request_id=request_id,
    error=str(e),
    exc_info=True  # Include stack trace
)
```

### Warning Logging
```python
logger.warning(
    "Resource not found",
    request_id=request_id,
    resource_type="Device",
    resource_id=device_id
)
```

---

## Common Patterns

### Pattern 1: List with Filters
```python
@router.get("/items")
def list_items(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Listing items",
        request_id=request_id,
        page=page,
        limit=limit,
        status=status,
        category=category
    )

    # Build query
    query = db.query(Item)

    # Apply filters
    if status:
        query = query.filter(Item.status == status)
    if category:
        query = query.filter(Item.category == category)

    # Get total
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    # Calculate total pages
    import math
    total_pages = math.ceil(total / limit) if limit > 0 else 0

    logger.info(
        "Items listed successfully",
        request_id=request_id,
        total=total,
        returned=len(items),
        page=page,
        total_pages=total_pages
    )

    return paginated_response(
        data=[item.to_dict() for item in items],
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )
```

### Pattern 2: Create with Validation
```python
@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Creating item",
        request_id=request_id,
        user_id=current_user.id,
        item_name=item_data.name
    )

    # Check for duplicates
    existing = db.query(Item).filter(Item.name == item_data.name).first()
    if existing:
        raise ConflictException(
            message=f"Item with name '{item_data.name}' already exists",
            field="name",
            details={"name": item_data.name, "existing_id": existing.id}
        )

    try:
        # Create item
        item = Item(**item_data.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)

        logger.info(
            "Item created successfully",
            request_id=request_id,
            item_id=item.id,
            item_name=item.name
        )

        return success_response(
            data=item.to_dict(),
            request_id=request_id
        )
    except ConflictException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create item",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to create item: {str(e)}",
            details={"item_name": item_data.name}
        )
```

### Pattern 3: Update Resource
```python
@router.put("/items/{item_id}")
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Updating item",
        request_id=request_id,
        item_id=item_id,
        user_id=current_user.id
    )

    # Get item
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise NotFoundException(
            message=f"Item with ID {item_id} not found",
            resource_type="Item",
            resource_id=item_id
        )

    # Track updates
    updates = {}

    # Update fields
    if item_data.name is not None:
        item.name = item_data.name
        updates['name'] = item_data.name
    if item_data.status is not None:
        item.status = item_data.status
        updates['status'] = item_data.status

    db.commit()
    db.refresh(item)

    logger.info(
        "Item updated successfully",
        request_id=request_id,
        item_id=item_id,
        updates=updates
    )

    return success_response(
        data=item.to_dict(),
        request_id=request_id
    )
```

### Pattern 4: Delete Resource
```python
@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Deleting item",
        request_id=request_id,
        item_id=item_id,
        user_id=current_user.id
    )

    # Check if exists
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise NotFoundException(
            message=f"Item with ID {item_id} not found",
            resource_type="Item",
            resource_id=item_id
        )

    # Delete
    db.delete(item)
    db.commit()

    logger.info(
        "Item deleted successfully",
        request_id=request_id,
        item_id=item_id
    )

    return success_response(
        data={"message": f"Item {item_id} deleted successfully"},
        request_id=request_id
    )
```

---

## Migration Checklist

When migrating an endpoint, check off each item:

- [ ] Import `StructuredLogger` instead of `logging.getLogger`
- [ ] Import exception classes (NotFoundException, etc.)
- [ ] Import `success_response`, `paginated_response`
- [ ] Import `get_request_id`
- [ ] Add `request: Request` parameter
- [ ] Extract `request_id = get_request_id(request)`
- [ ] Use `logger.info()` with structured fields
- [ ] Convert `skip/limit` to `page/limit` (list endpoints)
- [ ] Calculate `offset = (page - 1) * limit`
- [ ] Calculate `total_pages = math.ceil(total / limit)`
- [ ] Replace `HTTPException` with exception classes
- [ ] Wrap response in `success_response()` or `paginated_response()`
- [ ] Include `request_id` in response
- [ ] Update docstring with Args, Returns, Raises
- [ ] Test endpoint with new response format

---

## Testing Checklist

After migration, verify:

- [ ] Syntax check passes: `python3 -m py_compile app/api/filename.py`
- [ ] Import check passes: No circular imports
- [ ] Response format matches standardized structure
- [ ] Pagination works correctly (page/limit)
- [ ] Request ID appears in logs and responses
- [ ] Exceptions return correct status codes
- [ ] Frontend can parse new response format
- [ ] No breaking changes (or documented if breaking)

---

## Quick Reference URLs

### Documentation
- Full Migration Report: `/API_STANDARDIZATION_SPRINT1_PART2_COMPLETE.md`
- Exception Classes: `backend/app/core/exceptions.py`
- Response Schemas: `backend/app/schemas/common.py`
- Structured Logger: `backend/app/core/logging.py`

### Examples (Already Migrated)
- Devices API: `backend/app/api/devices.py`
- Client API: `backend/app/api/client.py`
- Firebird API: `backend/app/api/firebird.py`
- Content API: `backend/app/api/content.py`
- Playlists API: `backend/app/api/playlists.py`
- Tags API: `backend/app/api/tags.py`

---

**Last Updated:** October 28, 2025
**Maintained By:** Backend Development Team
