# Error Handling Quick Reference

## Import Statement

```python
from shared.errors import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    ErrorCodes,
    handle_errors
)
```

---

## Common Patterns

### 1. Resource Not Found (404)

```python
device = repository.get(device_id)
if not device:
    raise NotFoundError(
        message=f"Device {device_id} not found",
        details={"device_id": device_id}
    )
```

### 2. Validation Error (400)

```python
if not is_valid_email(email):
    raise ValidationError(
        message="Invalid email format",
        details={"field": "email", "value": email}
    )
```

### 3. Duplicate Resource (409)

```python
existing = repository.get_by_username(username)
if existing:
    raise ConflictError(
        message=f"Username '{username}' already exists",
        details={"username": username}
    )
```

### 4. Permission Denied (403)

```python
if not user.has_permission("admin"):
    raise AuthorizationError(
        message="Insufficient permissions",
        details={"required_role": "admin", "user_role": user.role}
    )
```

### 5. Invalid Credentials (401)

```python
if not verify_password(password, user.password_hash):
    raise AuthenticationError(
        message="Invalid credentials",
        details={"code": ErrorCodes.INVALID_CREDENTIALS}
    )
```

### 6. Rate Limit Exceeded (429)

```python
if rate_limiter.is_exceeded(user_id):
    raise RateLimitError(
        message="Too many requests",
        details={"retry_after": 60, "limit": 100}
    )
```

### 7. Database Error (500)

```python
try:
    db.execute(query)
except SQLAlchemyError as e:
    raise DatabaseError(
        message="Database query failed",
        details={"error": str(e)}
    )
```

### 8. External Service Error (502)

```python
response = requests.get(pms_api_url)
if response.status_code != 200:
    raise ExternalServiceError(
        message="PMS API is unavailable",
        details={"service": "PMS", "status": response.status_code}
    )
```

---

## Use Case Pattern

```python
from shared.errors import NotFoundError, ValidationError

class GetDeviceUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, device_id: int, organization_id: int):
        # Validation
        if device_id <= 0:
            raise ValidationError(
                message="Invalid device ID",
                details={"device_id": device_id}
            )

        # Business logic
        device = self.repository.get(device_id, organization_id)
        if not device:
            raise NotFoundError(
                message=f"Device {device_id} not found",
                details={"device_id": device_id}
            )

        return device
```

---

## Route Pattern with Decorator

```python
from fastapi import APIRouter
from shared.errors import handle_errors, NotFoundError

router = APIRouter()

@router.get("/devices/{device_id}")
@handle_errors
async def get_device(device_id: int):
    # Errors are automatically converted to HTTPException
    device = use_case.execute(device_id)
    return device
```

---

## Status Codes

| Code | Exception | Usage |
|------|-----------|-------|
| 400 | ValidationError | Invalid input |
| 401 | AuthenticationError | Login failed |
| 403 | AuthorizationError | Permission denied |
| 404 | NotFoundError | Resource not found |
| 409 | ConflictError | Duplicate resource |
| 429 | RateLimitError | Rate limit exceeded |
| 500 | DatabaseError | Database error |
| 502 | ExternalServiceError | External API failed |

---

## Error Codes

```python
from shared.errors import ErrorCodes

# Common error codes
ErrorCodes.INVALID_CREDENTIALS
ErrorCodes.TOKEN_EXPIRED
ErrorCodes.ACCESS_DENIED
ErrorCodes.NOT_FOUND
ErrorCodes.ALREADY_EXISTS
ErrorCodes.VALIDATION_ERROR
ErrorCodes.DATABASE_ERROR
```

---

## Response Format

All exceptions produce consistent JSON:

```json
{
  "message": "Device not found",
  "code": "NOT_FOUND",
  "details": {
    "device_id": 123
  }
}
```

---

## Don't Do This

❌ **Don't catch and re-raise as HTTPException**
```python
# Bad - handlers already do this
try:
    raise NotFoundError("Not found")
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
```

❌ **Don't return error dicts**
```python
# Bad - use exceptions instead
return {"error": "Failed", "code": 500}
```

❌ **Don't use generic Exception**
```python
# Bad - use specific exception classes
raise Exception("Something failed")
```

---

## For More Details

See `shared/exceptions.py` for comprehensive documentation and examples.
