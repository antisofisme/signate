# Firebird API - Quick Wins Pattern Reference

This document shows the exact migration pattern used for all 8 Firebird endpoints.

---

## Pattern Template

### Before (Old Pattern)
```python
from fastapi import APIRouter, Depends, HTTPException, status
import logging

logger = logging.getLogger(__name__)

@router.get("/api/firebird/configs/{config_id}")
async def get_firebird_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration not found"
        )

    return config
```

### After (Quick Wins Pattern)
```python
from fastapi import APIRouter, Depends, Request, status
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException
from app.schemas.common import success_response

logger = StructuredLogger(__name__)

@router.get("/api/firebird/configs/{config_id}")
async def get_firebird_config(
    request: Request,  # ← ADD THIS
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)  # ← ADD THIS

    logger.info(  # ← ADD THIS
        "Getting Firebird configuration",
        request_id=request_id,
        config_id=config_id,
        user_id=current_user.id
    )

    config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

    if not config:
        raise NotFoundException(  # ← CHANGE THIS
            message=f"Configuration not found",
            resource_type="FirebirdConfig",
            resource_id=config_id
        )

    config_response = FirebirdConfigResponse.model_validate(config)  # ← ADD THIS

    logger.info(  # ← ADD THIS
        "Configuration retrieved successfully",
        request_id=request_id,
        config_id=config_id
    )

    return success_response(  # ← CHANGE THIS
        data=config_response.model_dump(),
        request_id=request_id
    )
```

---

## 7-Step Migration Checklist

### Step 1: Update Imports
```python
# Remove
import logging
from fastapi import APIRouter, Depends, HTTPException, status

# Add
from fastapi import APIRouter, Depends, Request, status
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException, InternalServerException
from app.schemas.common import success_response

# Change logger
# OLD: logger = logging.getLogger(__name__)
# NEW: logger = StructuredLogger(__name__)
```

### Step 2: Add Request Parameter
```python
# Add as FIRST parameter (after self if method)
async def endpoint(
    request: Request,  # ← ADD HERE
    # ... other parameters
):
```

### Step 3: Add Request ID Tracking
```python
# Add as FIRST line in function body
request_id = get_request_id(request)
```

### Step 4: Add Start Logging
```python
logger.info(
    "Operation starting",  # Clear, descriptive message
    request_id=request_id,  # Always include
    # Add relevant context
    config_id=config_id,
    user_id=current_user.id
)
```

### Step 5: Replace HTTPException
```python
# 404 Not Found
raise HTTPException(status_code=404, detail="Not found")
# ↓
raise NotFoundException(message="Not found", resource_type="Type", resource_id=id)

# 400 Bad Request
raise HTTPException(status_code=400, detail="Invalid")
# ↓
raise BadRequestException(message="Invalid", details={...})

# 500 Internal Error
raise HTTPException(status_code=500, detail="Failed")
# ↓
raise InternalServerException(message="Failed", details={...})
```

### Step 6: Add Success Logging
```python
logger.info(
    "Operation completed successfully",
    request_id=request_id,
    # Add relevant metrics
    config_id=result.id,
    rows_affected=count
)
```

### Step 7: Wrap Response
```python
# For Pydantic models
response_model = ResponseSchema.model_validate(result)
return success_response(
    data=response_model.model_dump(),
    request_id=request_id
)

# For dict/list responses
return success_response(
    data={"key": "value"},
    request_id=request_id
)
```

---

## Exception Mapping Guide

| HTTP Status | Old Exception | New Exception | Use Case |
|-------------|---------------|---------------|----------|
| 404 | `HTTPException(404)` | `NotFoundException` | Resource not found |
| 400 | `HTTPException(400)` | `BadRequestException` | Invalid input, duplicate key, inactive resource |
| 500 | `HTTPException(500)` | `InternalServerException` | Database errors, unexpected failures |

---

## Real Examples from Firebird API

### Example 1: Create Endpoint (POST)
```python
@router.post("/api/firebird/configs", status_code=201)
async def create_firebird_config(
    request: Request,
    config_data: FirebirdConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Creating Firebird configuration",
        request_id=request_id,
        config_key=config_data.config_key,
        user_id=current_user.id
    )

    try:
        # Check if exists
        existing = db.query(FirebirdConfig).filter(
            FirebirdConfig.config_key == config_data.config_key
        ).first()

        if existing:
            raise BadRequestException(
                message=f"Configuration with key '{config_data.config_key}' already exists",
                details={"config_key": config_data.config_key}
            )

        # Business logic here (PRESERVED 100%)
        encrypted_api_key = firebird_service.encrypt_api_key(config_data.api_key)
        new_config = FirebirdConfig(
            config_key=config_data.config_key,
            api_endpoint=config_data.api_endpoint,
            api_key=encrypted_api_key,
            refresh_interval=config_data.refresh_interval,
            is_active=config_data.is_active,
            notes=config_data.notes
        )

        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        logger.info(
            "Firebird configuration created successfully",
            request_id=request_id,
            config_id=new_config.id,
            config_key=new_config.config_key
        )

        config_response = FirebirdConfigResponse.model_validate(new_config)
        return success_response(
            data=config_response.model_dump(),
            request_id=request_id
        )

    except BadRequestException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create Firebird configuration",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to create configuration: {str(e)}",
            details={"config_key": config_data.config_key}
        )
```

### Example 2: List Endpoint (GET)
```python
@router.get("/api/firebird/configs")
async def list_firebird_configs(
    request: Request,
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Listing Firebird configurations",
        request_id=request_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    try:
        query = db.query(FirebirdConfig)

        if is_active is not None:
            query = query.filter(FirebirdConfig.is_active == is_active)

        total = query.count()
        configs = query.order_by(FirebirdConfig.id).offset(skip).limit(limit).all()

        config_list = [FirebirdConfigResponse.model_validate(c) for c in configs]

        logger.info(
            "Firebird configurations retrieved",
            request_id=request_id,
            total=total,
            returned=len(configs)
        )

        return success_response(
            data={
                "total": total,
                "configs": [c.model_dump() for c in config_list]
            },
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to list configurations",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to retrieve configurations: {str(e)}"
        )
```

### Example 3: Delete Endpoint (DELETE)
```python
@router.delete("/api/firebird/configs/{config_id}", status_code=200)
async def delete_firebird_config(
    request: Request,
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    request_id = get_request_id(request)

    logger.info(
        "Deleting Firebird configuration",
        request_id=request_id,
        config_id=config_id
    )

    try:
        config = db.query(FirebirdConfig).filter(FirebirdConfig.id == config_id).first()

        if not config:
            raise NotFoundException(
                message=f"Configuration with ID {config_id} not found",
                resource_type="FirebirdConfig",
                resource_id=config_id
            )

        config_key = config.config_key

        # Business logic (PRESERVED)
        firebird_service.remove_pool(config_id)
        db.delete(config)
        db.commit()

        logger.info(
            "Configuration deleted successfully",
            request_id=request_id,
            config_id=config_id,
            config_key=config_key
        )

        return success_response(
            data={
                "message": f"Configuration '{config_key}' deleted successfully",
                "config_id": config_id
            },
            request_id=request_id
        )

    except NotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete configuration",
            request_id=request_id,
            config_id=config_id,
            error=str(e),
            exc_info=True
        )
        raise InternalServerException(
            message=f"Failed to delete configuration: {str(e)}",
            details={"config_id": config_id}
        )
```

---

## Key Principles

1. **Always add `request: Request` as first parameter**
2. **Always call `request_id = get_request_id(request)` at start**
3. **Log at start and end of operation with request_id**
4. **Replace all HTTPException with custom exceptions**
5. **Wrap all responses in `success_response()`**
6. **Preserve 100% of business logic**
7. **Use structured logging with context**

---

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Your actual data here
  },
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "uuid-here",
    "version": "1.0.0"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {
      "resource_type": "FirebirdConfig",
      "resource_id": 123
    }
  },
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "uuid-here",
    "version": "1.0.0"
  }
}
```

---

## Common Pitfalls to Avoid

❌ **DON'T**: Forget to add `request: Request`
✅ **DO**: Add as first parameter

❌ **DON'T**: Use old `HTTPException`
✅ **DO**: Use custom exceptions (NotFoundException, BadRequestException, etc.)

❌ **DON'T**: Return raw models or dicts
✅ **DO**: Wrap in `success_response()`

❌ **DON'T**: Use print() or old logger
✅ **DO**: Use StructuredLogger with request_id

❌ **DON'T**: Modify business logic
✅ **DO**: Preserve 100% of existing logic

---

## Migration Verification

After migration, verify:
- [ ] All endpoints have `request: Request` parameter
- [ ] All endpoints call `get_request_id(request)`
- [ ] No `HTTPException` remains (replaced with custom exceptions)
- [ ] All responses use `success_response()`
- [ ] All logging uses StructuredLogger with request_id
- [ ] Business logic unchanged
- [ ] Syntax is valid (python3 -m py_compile)

---

**This pattern was successfully applied to all 8 Firebird endpoints with 100% business logic preservation.**
