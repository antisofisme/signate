# Quick Wins - Developer Cheat Sheet

Quick reference for using the 4 Quick Wins in your FastAPI endpoints.

---

## 🚀 Quick Start

```python
from fastapi import APIRouter, Request
from app.schemas.common import success_response, paginated_response
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id

router = APIRouter()
logger = StructuredLogger(__name__)
```

---

## 1️⃣ Success Responses

### Simple Success Response
```python
@router.get("/example")
async def example(request: Request):
    request_id = get_request_id(request)

    return success_response(
        data={"message": "Hello World"},
        request_id=request_id
    )
```

**Output**:
```json
{
  "success": true,
  "data": {"message": "Hello World"},
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "uuid-here",
    "version": "1.0.0"
  }
}
```

### Paginated Response
```python
@router.get("/devices")
async def list_devices(
    request: Request,
    page: int = 1,
    page_size: int = 20
):
    request_id = get_request_id(request)
    devices, total = get_devices_from_db(page, page_size)

    return paginated_response(
        data=devices,
        total=total,
        page=page,
        page_size=page_size,
        request_id=request_id
    )
```

---

## 2️⃣ Error Handling

### Not Found (404)
```python
if not device:
    raise NotFoundException(
        message="Device not found",
        resource_type="Device",
        resource_id=device_id
    )
```

### Validation Error (422)
```python
if not email or "@" not in email:
    raise ValidationException(
        message="Invalid email format",
        field="email",
        details={"pattern": "must contain @"}
    )
```

### Conflict (409)
```python
if existing_device:
    raise ConflictException(
        message="Device with this name already exists",
        field="name",
        details={"existing_id": existing_device.id}
    )
```

### Unauthorized (401)
```python
if not token:
    raise UnauthorizedException(
        message="Authentication token required"
    )
```

### Forbidden (403)
```python
if not user.has_permission("delete"):
    raise ForbiddenException(
        message="You don't have permission to delete devices"
    )
```

### Bad Request (400)
```python
if invalid_data:
    raise BadRequestException(
        message="Invalid request data",
        details={"field": "value must be positive"}
    )
```

---

## 3️⃣ Request ID Tracking

### Get Request ID
```python
from app.middleware.request_id import get_request_id

@router.get("/example")
async def example(request: Request):
    request_id = get_request_id(request)
    # Use request_id in logs, responses, etc.
```

### Include in Responses
```python
return success_response(
    data={"device_id": 123},
    request_id=request_id  # Always pass this
)
```

### Check Response Headers
```bash
curl -v http://192.168.5.12:8001/api/devices
# Look for: X-Request-ID: uuid-here
```

---

## 4️⃣ Structured Logging

### Basic Logging
```python
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)

# Info
logger.info(
    "Device created",
    request_id=request_id,
    device_id=device.id,
    user_id=current_user.id
)

# Warning
logger.warning(
    "High memory usage",
    memory_mb=1024,
    threshold_mb=800,
    request_id=request_id
)

# Error
logger.error(
    "Failed to connect to database",
    database="postgresql",
    error=str(e),
    request_id=request_id,
    exc_info=True  # Include traceback
)
```

### Log Output (JSON)
```json
{
  "timestamp": "2025-10-27T10:30:00Z",
  "level": "INFO",
  "logger": "app.api.devices",
  "message": "Device created",
  "request_id": "uuid-here",
  "device_id": 123,
  "user_id": 456
}
```

---

## 📋 Complete Endpoint Example

```python
from fastapi import APIRouter, Request, HTTPException
from app.schemas.common import success_response
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import StructuredLogger
from app.middleware.request_id import get_request_id

router = APIRouter()
logger = StructuredLogger(__name__)

@router.post("/devices")
async def create_device(
    request: Request,
    data: DeviceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new device"""
    request_id = get_request_id(request)

    # Log the request
    logger.info(
        "Creating device",
        request_id=request_id,
        user_id=current_user.id,
        device_name=data.name
    )

    # Validate
    if not data.name:
        raise ValidationException(
            message="Device name is required",
            field="name"
        )

    # Check for duplicates
    existing = db.query(Device).filter(Device.name == data.name).first()
    if existing:
        raise ConflictException(
            message="Device with this name already exists",
            field="name",
            details={"existing_id": existing.id}
        )

    # Create device
    try:
        device = Device(**data.dict())
        db.add(device)
        db.commit()
        db.refresh(device)

        # Log success
        logger.info(
            "Device created successfully",
            request_id=request_id,
            device_id=device.id,
            device_name=device.name,
            user_id=current_user.id
        )

        # Return standardized response
        return success_response(
            data=device.to_dict(),
            request_id=request_id
        )

    except Exception as e:
        # Log error
        logger.error(
            "Failed to create device",
            request_id=request_id,
            device_name=data.name,
            error=str(e),
            exc_info=True
        )
        raise
```

---

## 🔍 Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Device not found",
    "field": null,
    "details": {
      "resource_type": "Device",
      "resource_id": 999
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

## 📊 Available Exception Types

| Exception | Status | Use Case |
|-----------|--------|----------|
| `NotFoundException` | 404 | Resource not found |
| `ValidationException` | 422 | Validation failed |
| `UnauthorizedException` | 401 | Auth required |
| `ForbiddenException` | 403 | No permission |
| `ConflictException` | 409 | Duplicate/conflict |
| `BadRequestException` | 400 | Invalid request |
| `InternalServerException` | 500 | Server error |
| `DatabaseException` | 500 | DB operation failed |
| `ExternalServiceException` | 503 | External API failed |

---

## ⚙️ Configuration

### Environment Variables (.env)
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json (production) or text (development)
DEBUG=True      # Enable demo endpoints
```

---

## 🧪 Testing Commands

```bash
# Test request ID
curl -v http://192.168.5.12:8001/api/demo/request-id

# Test success response
curl http://192.168.5.12:8001/api/demo/success | jq

# Test paginated response
curl "http://192.168.5.12:8001/api/demo/paginated?page=1&page_size=5" | jq

# Test error handling
curl http://192.168.5.12:8001/api/demo/error-not-found | jq

# Test all features
curl http://192.168.5.12:8001/api/demo/all-features | jq
```

---

## 📚 Documentation

- **Detailed Guide**: `backend/QUICK_WINS_IMPLEMENTATION.md`
- **Summary**: `QUICK_WINS_SUMMARY.md`
- **API Docs**: http://192.168.5.12:8001/docs
- **This Cheat Sheet**: Keep handy while coding!

---

## 💡 Best Practices

### ✅ DO
- Always use `get_request_id(request)` and pass to responses
- Use custom exceptions instead of returning error dicts
- Use `StructuredLogger` for all logging
- Include request_id in all logs
- Add meaningful context to logs

### ❌ DON'T
- Don't return `{"error": "message"}` directly
- Don't use `print()` for logging
- Don't forget to include request_id
- Don't expose database details in errors
- Don't skip error handling

---

**Quick Reference Version**: 1.0.0
**Last Updated**: 2025-10-27
