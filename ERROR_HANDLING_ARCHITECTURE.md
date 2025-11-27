# Error Handling Architecture - Backend Python

**Status**: ✅ Infrastructure Complete - Ready for Gradual Adoption
**Created**: 2025-11-27
**Location**: `backend-python/shared/`

---

## Executive Summary

The backend-python codebase now has a **standardized error handling infrastructure** that provides:

✅ **8 specialized exception classes** for different HTTP error scenarios
✅ **Centralized error codes** for programmatic error handling
✅ **Automatic exception handlers** registered in FastAPI
✅ **Decorator pattern** for automatic error conversion
✅ **Consistent JSON response format** across all errors
✅ **Backward compatibility** - legacy patterns still work

---

## Architecture Overview

### File Structure

```
backend-python/
├── shared/
│   ├── errors.py           # ✅ Implementation (existing)
│   └── exceptions.py       # 🆕 Documentation & quick reference
└── main.py                 # ✅ Exception handlers registered
```

### Exception Hierarchy

```
AppException (base)
├── ValidationError (400)         # Invalid input, missing fields
├── AuthenticationError (401)     # Login failures, invalid tokens
├── AuthorizationError (403)      # Permission denied, insufficient role
├── NotFoundError (404)           # Resource not found
├── ConflictError (409)           # Duplicate resources, conflicts
├── RateLimitError (429)          # Rate limit exceeded
├── DatabaseError (500)           # Database errors
└── ExternalServiceError (502)    # Third-party service failures
```

---

## Current State Analysis

### Legacy Error Patterns Found (4 patterns)

1. **HTTPException** (FastAPI native)
   ```python
   raise HTTPException(status_code=404, detail="Not found")
   ```

2. **ValueError** (Python builtin)
   ```python
   raise ValueError("Invalid input")
   ```

3. **CustomError** (legacy custom exceptions)
   ```python
   raise CustomError("Something failed")
   ```

4. **Error dicts** (anti-pattern)
   ```python
   return {"error": "Failed", "code": 500}
   ```

### Migration Strategy

- ✅ **NEW CODE**: Use shared/errors.py exceptions immediately
- 📋 **REFACTORING**: Replace HTTPException with specific exceptions when touching code
- 🔒 **LEGACY CODE**: Leave as-is unless actively modifying
- ⚡ **NO BREAKING CHANGES**: Both patterns work simultaneously

---

## Usage Guide

### 1. Basic Exception Raising

```python
from shared.errors import NotFoundError, ValidationError

def get_device(device_id: int):
    device = repository.get(device_id)
    if not device:
        raise NotFoundError(
            message=f"Device {device_id} not found",
            details={"device_id": device_id}
        )
    return device
```

### 2. With Error Codes

```python
from shared.errors import NotFoundError, ErrorCodes

raise NotFoundError(
    message="Organization not found",
    details={"code": ErrorCodes.ORGANIZATION_NOT_FOUND, "org_id": 99}
)
```

### 3. Using Decorator Pattern

```python
from shared.errors import handle_errors, NotFoundError

@router.get("/devices/{device_id}")
@handle_errors
async def get_device(device_id: int):
    # Any AppException raised here is automatically
    # converted to HTTPException by the decorator
    device = repository.get(device_id)
    if not device:
        raise NotFoundError("Device not found")
    return device
```

### 4. Exception Handler Integration

Exception handlers are already registered in `main.py`:

```python
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "code": exc.code,
            "details": exc.details
        }
    )
```

---

## Available Exception Classes

### ValidationError (400)
**Use for**: Invalid input, missing fields, format errors

```python
from shared.errors import ValidationError

raise ValidationError(
    message="Invalid email format",
    details={"field": "email", "value": "not-an-email"}
)
```

### AuthenticationError (401)
**Use for**: Login failures, invalid tokens, expired sessions

```python
from shared.errors import AuthenticationError

raise AuthenticationError(
    message="Invalid credentials",
    details={"username": username}
)
```

### AuthorizationError (403)
**Use for**: Permission denied, insufficient role/permissions

```python
from shared.errors import AuthorizationError

raise AuthorizationError(
    message="Insufficient permissions",
    details={"required_role": "admin", "user_role": "viewer"}
)
```

### NotFoundError (404)
**Use for**: Resource not found, invalid IDs

```python
from shared.errors import NotFoundError

raise NotFoundError(
    message="Device not found",
    details={"device_id": 123, "organization_id": 1}
)
```

### ConflictError (409)
**Use for**: Duplicate resources, constraint violations

```python
from shared.errors import ConflictError

raise ConflictError(
    message="Username already exists",
    details={"username": "admin", "suggestion": "Try admin2"}
)
```

### RateLimitError (429)
**Use for**: Rate limit exceeded, quota exhausted

```python
from shared.errors import RateLimitError

raise RateLimitError(
    message="Rate limit exceeded",
    details={"retry_after": 60, "limit": 100}
)
```

### DatabaseError (500)
**Use for**: Database connection issues, query failures

```python
from shared.errors import DatabaseError

raise DatabaseError(
    message="Failed to connect to database",
    details={"host": "localhost", "database": "signage_db"}
)
```

### ExternalServiceError (502)
**Use for**: Third-party service failures, PMS integration errors

```python
from shared.errors import ExternalServiceError

raise ExternalServiceError(
    message="PMS API is unavailable",
    details={"service": "PMS", "endpoint": "/api/bookings"}
)
```

---

## Centralized Error Codes

Use error codes from `shared.errors.ErrorCodes`:

```python
from shared.errors import ErrorCodes

class ErrorCodes:
    # Authentication & Authorization
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    ACCESS_DENIED = "ACCESS_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_EXPIRED = "SESSION_EXPIRED"

    # Validation
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Resources
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"

    # Business Logic
    ACTIVATION_CODE_EXPIRED = "ACTIVATION_CODE_EXPIRED"
    ACTIVATION_CODE_INVALID = "ACTIVATION_CODE_INVALID"
    DEVICE_ALREADY_ACTIVATED = "DEVICE_ALREADY_ACTIVATED"
    ORGANIZATION_NOT_FOUND = "ORGANIZATION_NOT_FOUND"

    # System
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
```

---

## Response Format

All custom exceptions are converted to consistent JSON responses:

```json
{
  "message": "User-friendly error message",
  "code": "ERROR_CODE_CONSTANT",
  "details": {
    "field": "value",
    "context": "additional info"
  }
}
```

**Example Response**:

```json
{
  "message": "Device not found",
  "code": "NOT_FOUND",
  "details": {
    "device_id": 123,
    "organization_id": 1
  }
}
```

---

## Status Code Mapping

| HTTP Code | Exception Class | Use Case |
|-----------|----------------|----------|
| 400 | ValidationError | Bad input, validation failures |
| 401 | AuthenticationError | Not authenticated, invalid tokens |
| 403 | AuthorizationError | Not authorized, permission denied |
| 404 | NotFoundError | Resource not found |
| 409 | ConflictError | Duplicate resource, constraint violation |
| 429 | RateLimitError | Rate limit exceeded |
| 500 | DatabaseError | Server error, database issues |
| 502 | ExternalServiceError | Third-party service unavailable |

---

## Best Practices

### ✅ DO

1. **Use specific exception classes**
   ```python
   raise NotFoundError("Device not found")  # ✅ Good
   ```

2. **Provide descriptive messages**
   ```python
   raise ValidationError(
       message="Email format is invalid",
       details={"field": "email", "format": "user@example.com"}
   )
   ```

3. **Include context in details**
   ```python
   raise NotFoundError(
       message="Organization not found",
       details={"organization_id": org_id, "user_id": user_id}
   )
   ```

4. **Use centralized error codes**
   ```python
   raise AuthenticationError(
       message="Invalid credentials",
       details={"code": ErrorCodes.INVALID_CREDENTIALS}
   )
   ```

5. **Let exception handlers convert to HTTPException**
   ```python
   # Handler automatically converts to HTTPException
   raise NotFoundError("Device not found")
   ```

### ❌ DON'T

1. **Don't use generic AppException**
   ```python
   raise AppException("Error")  # ❌ Bad - use specific class
   ```

2. **Don't catch and re-raise as HTTPException**
   ```python
   # ❌ Bad - let handlers do the conversion
   try:
       raise NotFoundError("Not found")
   except NotFoundError as e:
       raise HTTPException(status_code=404, detail=str(e))
   ```

3. **Don't return error dicts**
   ```python
   return {"error": "Failed", "code": 500}  # ❌ Anti-pattern
   ```

4. **Don't use generic Exception**
   ```python
   raise Exception("Something failed")  # ❌ Bad
   ```

---

## Migration Examples

### Before (HTTPException)

```python
from fastapi import HTTPException

def get_device(device_id: int):
    device = repository.get(device_id)
    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )
    return device
```

### After (shared/errors)

```python
from shared.errors import NotFoundError

def get_device(device_id: int):
    device = repository.get(device_id)
    if not device:
        raise NotFoundError(
            message="Device not found",
            details={"device_id": device_id}
        )
    return device
```

---

## Implementation Checklist

### Infrastructure (✅ Complete)

- ✅ Exception classes defined (`shared/errors.py`)
- ✅ Exception handlers registered (`main.py`)
- ✅ Error codes centralized (`shared/errors.ErrorCodes`)
- ✅ Decorator available (`shared/errors.handle_errors`)
- ✅ Documentation created (`shared/exceptions.py`)

### Adoption (📋 In Progress)

- 📋 New code uses shared/errors exceptions
- 📋 Gradual migration of existing HTTPException usage
- 📋 Service-by-service adoption as code is touched
- 📋 No breaking changes - both patterns work

### Future Enhancements (💡 Optional)

- 💡 Add logging integration to exception handlers
- 💡 Add Sentry/error tracking integration
- 💡 Add request ID to error responses for tracing
- 💡 Add retry-after headers for rate limit errors
- 💡 Create error response schemas for OpenAPI docs

---

## Testing Error Handling

### Test Exception Raising

```python
import pytest
from shared.errors import NotFoundError, ValidationError

def test_device_not_found():
    with pytest.raises(NotFoundError) as exc_info:
        get_device(999)  # Non-existent device

    assert exc_info.value.status_code == 404
    assert "Device not found" in exc_info.value.message
    assert exc_info.value.details["device_id"] == 999
```

### Test API Response

```python
from fastapi.testclient import TestClient

def test_device_not_found_response(client: TestClient):
    response = client.get("/api/v1/devices/999")

    assert response.status_code == 404
    assert response.json() == {
        "message": "Device not found",
        "code": "NOT_FOUND",
        "details": {"device_id": 999}
    }
```

---

## Resources

### Documentation Files

- **`shared/errors.py`** - Exception class implementation
- **`shared/exceptions.py`** - Comprehensive documentation & examples
- **`main.py`** - Exception handler registration
- **`ERROR_HANDLING_ARCHITECTURE.md`** - This document

### Related Patterns

- **Clean Architecture** - Use cases raise domain exceptions
- **Repository Pattern** - Repositories raise NotFoundError
- **Service Layer** - Services raise business logic exceptions
- **API Routes** - Routes handle exceptions via decorators/handlers

### Next Steps

1. ✅ Read `shared/exceptions.py` for detailed usage guide
2. 📋 Use shared/errors exceptions in new code
3. 📋 Gradually migrate existing code when touching it
4. 📋 Add tests for error scenarios
5. 📋 Document service-specific error codes as needed

---

## Summary

The error handling infrastructure is **complete and ready for use**:

✅ **8 exception classes** cover all HTTP error scenarios
✅ **Centralized error codes** for consistent error handling
✅ **Automatic conversion** to HTTPException via handlers
✅ **Decorator pattern** for route-level error handling
✅ **Consistent JSON format** for all error responses
✅ **Backward compatible** - no breaking changes

**Services can adopt this pattern gradually** as they create new code or refactor existing code. Both legacy and new patterns work simultaneously.

For questions or improvements, consult the **Backend System Architect** specialization.

---

**Status**: ✅ Infrastructure Complete - Ready for Gradual Adoption
**Last Updated**: 2025-11-27
