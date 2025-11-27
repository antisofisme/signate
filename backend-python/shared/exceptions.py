"""
=============================================================================
STANDARD ERROR HANDLING INFRASTRUCTURE
=============================================================================

This module provides standardized exception classes for consistent error
handling across the backend-python codebase.

ARCHITECTURE OVERVIEW
---------------------

The error handling system follows a hierarchical structure:

    AppException (base)
    ├── ValidationError (400)
    ├── AuthenticationError (401)
    ├── AuthorizationError (403)
    ├── NotFoundError (404)
    ├── ConflictError (409)
    ├── RateLimitError (429)
    ├── DatabaseError (500)
    └── ExternalServiceError (502)

ERROR HANDLING PATTERNS
-----------------------

There are 4 legacy error patterns currently in use across the codebase:
1. raise HTTPException (FastAPI native)
2. raise ValueError (Python builtin)
3. raise CustomError (legacy custom exceptions)
4. return error dict (anti-pattern)

RECOMMENDED PATTERN (Use shared/errors.py exceptions):
------------------------------------------------------

    from shared.errors import NotFoundError, ValidationError

    def my_use_case(device_id: int):
        device = repository.get(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device {device_id} not found",
                details={"device_id": device_id}
            )
        return device

EXCEPTION HANDLER INTEGRATION
------------------------------

All custom exceptions are automatically caught by FastAPI exception handlers
registered in main.py:

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

AVAILABLE EXCEPTION CLASSES
----------------------------

See shared/errors.py for full implementation:

1. ValidationError(message, details=None)
   - HTTP 400 - Bad Request
   - Use for: Invalid input, missing fields, format errors
   - Example: ValidationError("Invalid email format", {"field": "email"})

2. AuthenticationError(message, details=None)
   - HTTP 401 - Unauthorized
   - Use for: Login failures, invalid tokens, expired sessions
   - Example: AuthenticationError("Invalid credentials")

3. AuthorizationError(message, details=None)
   - HTTP 403 - Forbidden
   - Use for: Permission denied, insufficient role/permissions
   - Example: AuthorizationError("Insufficient permissions", {"required": "admin"})

4. NotFoundError(message, details=None)
   - HTTP 404 - Not Found
   - Use for: Resource not found, invalid IDs
   - Example: NotFoundError("Device not found", {"device_id": 123})

5. ConflictError(message, details=None)
   - HTTP 409 - Conflict
   - Use for: Duplicate resources, constraint violations
   - Example: ConflictError("Username already exists", {"username": "admin"})

6. RateLimitError(message, details=None)
   - HTTP 429 - Too Many Requests
   - Use for: Rate limit exceeded, quota exhausted
   - Example: RateLimitError("Rate limit exceeded", {"retry_after": 60})

7. DatabaseError(message, details=None)
   - HTTP 500 - Internal Server Error
   - Use for: Database connection issues, query failures
   - Example: DatabaseError("Failed to connect to database")

8. ExternalServiceError(message, details=None)
   - HTTP 502 - Bad Gateway
   - Use for: Third-party service failures, PMS integration errors
   - Example: ExternalServiceError("PMS API unavailable")

ERROR CODES
-----------

Use centralized error codes from shared/errors.ErrorCodes:

    from shared.errors import ErrorCodes, NotFoundError

    raise NotFoundError(
        message="Organization not found",
        details={"code": ErrorCodes.ORGANIZATION_NOT_FOUND}
    )

Available error codes:
- INVALID_CREDENTIALS, TOKEN_EXPIRED, TOKEN_INVALID
- ACCESS_DENIED, INSUFFICIENT_PERMISSIONS
- INVALID_INPUT, MISSING_FIELD, INVALID_FORMAT
- NOT_FOUND, ALREADY_EXISTS, DUPLICATE_RESOURCE
- ACTIVATION_CODE_EXPIRED, ACTIVATION_CODE_INVALID
- DATABASE_ERROR, EXTERNAL_SERVICE_ERROR

ERROR HANDLER DECORATOR
-----------------------

For automatic error conversion in routes:

    from shared.errors import handle_errors

    @router.get("/devices/{device_id}")
    @handle_errors
    async def get_device(device_id: int):
        # Any AppException raised here is automatically
        # converted to HTTPException
        device = repository.get(device_id)
        if not device:
            raise NotFoundError("Device not found")
        return device

MIGRATION STRATEGY
------------------

This infrastructure is ready for gradual adoption:

1. NEW CODE: Use shared/errors.py exceptions immediately
2. REFACTORING: Replace HTTPException with specific exceptions
3. LEGACY CODE: Leave as-is unless touching that code
4. NO BREAKING CHANGES: Both patterns work simultaneously

EXAMPLE MIGRATION
-----------------

Before (HTTPException):
    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

After (shared/errors):
    if not device:
        raise NotFoundError(
            message="Device not found",
            details={"device_id": device_id}
        )

BEST PRACTICES
--------------

1. ✅ Use specific exception classes (NotFoundError vs AppException)
2. ✅ Provide descriptive messages for end users
3. ✅ Include details dict with context (IDs, field names, etc.)
4. ✅ Use ErrorCodes for programmatic error handling
5. ✅ Let exception handlers convert to HTTPException
6. ❌ Don't catch and re-raise as HTTPException (let handlers do it)
7. ❌ Don't return error dicts (raise exceptions instead)
8. ❌ Don't use generic Exception (use specific AppException subclasses)

RESPONSE FORMAT
---------------

All custom exceptions are converted to consistent JSON responses:

    {
        "message": "User-friendly error message",
        "code": "ERROR_CODE_CONSTANT",
        "details": {
            "field": "value",
            "context": "additional info"
        }
    }

STATUS CODE MAPPING
-------------------

400 - ValidationError (bad input)
401 - AuthenticationError (not authenticated)
403 - AuthorizationError (not authorized)
404 - NotFoundError (resource not found)
409 - ConflictError (duplicate/conflict)
429 - RateLimitError (too many requests)
500 - DatabaseError (server error)
502 - ExternalServiceError (upstream error)

IMPLEMENTATION STATUS
---------------------

✅ Exception classes defined (shared/errors.py)
✅ Exception handlers registered (main.py)
✅ Error codes centralized (shared/errors.ErrorCodes)
✅ Decorator available (shared/errors.handle_errors)
📋 Gradual adoption in progress (services can migrate at their own pace)

For full implementation details, see:
- shared/errors.py (exception classes)
- main.py (exception handlers)
- Backend system architect specialization (this agent)

=============================================================================
"""

# Import all exception classes from shared/errors for convenience
from shared.errors import (
    AppException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    DatabaseError,
    ExternalServiceError,
    ErrorCodes,
    handle_errors
)

__all__ = [
    "AppException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "DatabaseError",
    "ExternalServiceError",
    "ErrorCodes",
    "handle_errors"
]


# =============================================================================
# QUICK REFERENCE EXAMPLES
# =============================================================================

def _example_validation_error():
    """Example: Validation error for invalid input"""
    raise ValidationError(
        message="Invalid email format",
        details={"field": "email", "value": "not-an-email"}
    )


def _example_not_found_error():
    """Example: Resource not found"""
    raise NotFoundError(
        message="Device not found",
        details={"device_id": 123, "organization_id": 1}
    )


def _example_authorization_error():
    """Example: Permission denied"""
    raise AuthorizationError(
        message="Insufficient permissions",
        details={"required_role": "admin", "user_role": "viewer"}
    )


def _example_conflict_error():
    """Example: Duplicate resource"""
    raise ConflictError(
        message="Username already exists",
        details={"username": "admin", "suggestion": "Try admin2"}
    )


def _example_with_error_codes():
    """Example: Using centralized error codes"""
    raise NotFoundError(
        message="Organization not found",
        details={"code": ErrorCodes.ORGANIZATION_NOT_FOUND, "org_id": 99}
    )


def _example_external_service_error():
    """Example: External service failure"""
    raise ExternalServiceError(
        message="PMS API is unavailable",
        details={
            "service": "PMS",
            "endpoint": "/api/bookings",
            "retry_after": 60
        }
    )


# Note: These are example functions for documentation only
# They are not meant to be called in production code
