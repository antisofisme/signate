# Auth & Session API - Critical Bugs to Fix

**Priority**: 🔴 HIGH
**Found**: 2025-11-14
**Status**: Needs immediate attention

---

## Bug #1: Duplicate Username Returns 500

**Severity**: 🔴 **CRITICAL**
**Endpoint**: `POST /api/v1/auth/register`
**File**: `/mnt/g/khoirul/signate/backend-python/services/auth/use_cases/register.py`

### Problem
When trying to register a user with an existing username, the database throws an `IntegrityError` which is not caught, resulting in a 500 Internal Server Error instead of a proper 400/409 validation error.

### Current Behavior
```bash
curl -X POST http://192.168.5.12:8001/api/v1/auth/register \
  -d '{"username":"admin","email":"new@email.com","password":"Test123","organization_id":1}'

# Returns: 500 Internal Server Error
{
  "detail": "Internal Server Error"
}
```

### Expected Behavior
```json
{
  "success": false,
  "message": "Username already exists",
  "error_code": "DUPLICATE_USERNAME",
  "status_code": 400
}
```

### Fix Required
```python
# File: backend-python/services/auth/use_cases/register.py

from sqlalchemy.exc import IntegrityError
from shared.errors import ValidationError

class RegisterUseCase:
    def execute(self, username, email, password, full_name, organization_id):
        # Validate inputs...

        try:
            user = self.user_repository.create(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                organization_id=organization_id
            )
        except IntegrityError as e:
            error_msg = str(e).lower()
            if "users_username_key" in error_msg or "username" in error_msg:
                raise ValidationError("Username already exists")
            elif "users_email_key" in error_msg or "email" in error_msg:
                raise ValidationError("Email already exists")
            else:
                raise ValidationError("Registration failed due to duplicate data")

        return user
```

---

## Bug #2: Revoked Token Returns 500

**Severity**: 🔴 **CRITICAL**
**Affected**: All authenticated endpoints
**File**: `/mnt/g/khoirul/signate/backend-python/shared/errors.py`

### Problem
When trying to use a revoked token (after logout), the `get_current_user` dependency tries to raise an error with code `ErrorCodes.SESSION_REVOKED`, but this constant doesn't exist in the `ErrorCodes` class.

### Error Log
```
AttributeError: type object 'ErrorCodes' has no attribute 'SESSION_REVOKED'
File "/app/shared/auth.py", line 457, in get_current_user
  code=ErrorCodes.SESSION_REVOKED
       ^^^^^^^^^^^^^^^^^^^^^^^^^^
```

### Current Behavior
```bash
# 1. Login
TOKEN=$(curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.data.token')

# 2. Logout
curl -X POST http://192.168.5.12:8001/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# 3. Try to use revoked token
curl -X POST http://192.168.5.12:8001/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Returns: 500 Internal Server Error
{
  "detail": "Internal Server Error"
}
```

### Expected Behavior
```json
{
  "success": false,
  "message": "Session has been revoked. Please login again.",
  "error_code": "SESSION_REVOKED",
  "status_code": 401
}
```

### Fix Required
```python
# File: backend-python/shared/errors.py

class ErrorCodes:
    """Standardized error codes for API responses"""

    # Existing codes...
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # ADD THESE:
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # ...
```

### Also Check
Make sure the error handling in `shared/auth.py` properly uses this code:

```python
# File: backend-python/shared/auth.py

def get_current_user(...):
    # ... existing code ...

    # Check if session is revoked
    if session and session.revoked_at:
        raise AuthenticationError(
            message="Session has been revoked. Please login again.",
            code=ErrorCodes.SESSION_REVOKED  # This should now work
        )

    # Check if session is expired
    if session and session.expires_at < datetime.now():
        raise AuthenticationError(
            message="Session has expired. Please login again.",
            code=ErrorCodes.SESSION_EXPIRED
        )
```

---

## Testing After Fixes

### Test Bug #1 Fix (Duplicate Username)
```bash
# 1. Register new user
curl -X POST http://192.168.5.12:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser123",
    "email":"test123@example.com",
    "password":"TestPassword123",
    "full_name":"Test User",
    "organization_id":1
  }'

# Should return 201

# 2. Try to register same username
curl -X POST http://192.168.5.12:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"testuser123",
    "email":"different@example.com",
    "password":"TestPassword123",
    "full_name":"Different User",
    "organization_id":1
  }'

# Should return 400 with proper error message
```

### Test Bug #2 Fix (Revoked Token)
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.data.token')

# 2. Logout (revoke session)
curl -X POST http://192.168.5.12:8001/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Should return 200

# 3. Try to use revoked token again
curl -X POST http://192.168.5.12:8001/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Should return 401 with SESSION_REVOKED error code (NOT 500)
```

---

## Deployment Steps

1. **Make code changes**
   - Edit `backend-python/services/auth/use_cases/register.py`
   - Edit `backend-python/shared/errors.py`

2. **Test locally** (if possible)
   ```bash
   cd /mnt/g/khoirul/signate/backend-python
   pytest tests/test_auth.py  # If tests exist
   ```

3. **Sync to server**
   ```bash
   cd /mnt/g/khoirul/signate
   sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
     backend-python/services/auth/ \
     gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/auth/

   sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
     backend-python/shared/ \
     gzjbbk@192.168.5.12:/home/gzjbbk/signage/backend-python/shared/
   ```

4. **Restart backend**
   ```bash
   sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
     "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"
   ```

5. **Verify fixes**
   - Run the test commands above
   - Check logs: `docker logs signage-backend-python --tail 50`
   - Should see no more 500 errors for these cases

6. **Clear Redis** (to reset rate limits for testing)
   ```bash
   sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
     "docker exec signage-redis redis-cli FLUSHALL"
   ```

---

## Additional Recommendations

### Add More Error Codes
While fixing `errors.py`, consider adding these as well:

```python
class ErrorCodes:
    # Authentication
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"

    # Authorization
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    FORBIDDEN = "FORBIDDEN"

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DUPLICATE_USERNAME = "DUPLICATE_USERNAME"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    INVALID_INPUT = "INVALID_INPUT"

    # Resources
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
```

### Add Email Validation
In `register.py`, also validate email format:

```python
import re

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# In RegisterUseCase.execute():
if not validate_email(email):
    raise ValidationError("Invalid email format")
```

---

**Last Updated**: 2025-11-14
**Priority**: Fix before production deployment
**Estimated Time**: 30-60 minutes
