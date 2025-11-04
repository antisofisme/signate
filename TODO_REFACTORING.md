# TODO: Refactoring Existing Features with Centralized Utilities

**Status:** 🔴 NOT STARTED
**Priority:** ⭐⭐⭐ CRITICAL (Before Phase 3)
**Estimated Time:** 2-3 days

---

## 📋 Overview

Refactor existing Auth & Device features to use newly created centralized/shared utilities:
- `lib/errors/` - Error handling
- `lib/api/responseTypes.ts` - Type-safe API responses
- `lib/validation/schemas.ts` - Input validation
- `lib/notifications/toast.ts` - User feedback
- `lib/constants/app.ts` - App-wide constants
- `lib/auth/permissions.ts` - RBAC utilities

---

## 🎯 Phase 2.5: Refactor Auth Feature

### ✅ Already Using:
- ✅ `apiClient` from `lib/api/client.ts`
- ✅ `API_ENDPOINTS` from `lib/api/endpoints.ts`
- ✅ `useAuthStore` from `lib/stores/authStore.ts`

### ❌ NOT Using (Need to Refactor):

#### 1. **Error Handling** (`lib/errors/`)
**Files to update:**
- `features/auth/hooks/useAuth.ts`
- `features/auth/services/authApi.ts`
- `features/auth/components/LoginForm.tsx`
- `features/auth/components/RegisterForm.tsx`

**What to do:**
- [ ] Import `handleAPIError` from `lib/errors/errorHandler.ts`
- [ ] Wrap API calls in try-catch
- [ ] Use `handleAPIError()` to convert errors to `AppError`
- [ ] Use `getErrorMessage()` to show Indonesian error messages
- [ ] Remove hardcoded error messages in components

**Example:**
```typescript
// BEFORE
const { mutate, error } = useMutation({
  mutationFn: authApi.login,
  onError: (err) => {
    console.error('Login failed:', err);
  }
});

// AFTER
import { handleAPIError } from '@/lib/errors/errorHandler';
import { toast } from '@/lib/notifications/toast';

const { mutate } = useMutation({
  mutationFn: authApi.login,
  onError: (err) => {
    const appError = handleAPIError(err);
    toast.error(appError.message);
  }
});
```

---

#### 2. **Toast Notifications** (`lib/notifications/toast.ts`)
**Files to update:**
- `features/auth/hooks/useAuth.ts` (all mutations)
- `features/auth/components/LoginForm.tsx`
- `features/auth/components/RegisterForm.tsx`

**What to do:**
- [ ] Import `toast` from `lib/notifications/toast.ts`
- [ ] Add `toast.success()` on successful login/register/logout
- [ ] Add `toast.error()` on errors (use with handleAPIError)
- [ ] Remove inline alert/console.error

**Example:**
```typescript
// BEFORE
onSuccess: () => {
  console.log('Login successful');
}

// AFTER
import { toast } from '@/lib/notifications/toast';

onSuccess: () => {
  toast.success('Login berhasil! Selamat datang.');
}
```

---

#### 3. **Input Validation** (`lib/validation/schemas.ts`)
**Files to update:**
- `features/auth/components/LoginForm.tsx`
- `features/auth/components/RegisterForm.tsx`

**What to do:**
- [ ] Import validators from `lib/validation/schemas.ts`
- [ ] Use `validators.username()` for username field
- [ ] Use `validators.password()` for password field
- [ ] Use `validators.email()` for email field (if exists)
- [ ] Show validation errors in real-time

**Example:**
```typescript
// BEFORE
if (username.length < 3) {
  setError('Username too short');
}

// AFTER
import { validators } from '@/lib/validation/schemas';

const usernameValidation = validators.username(username);
if (!usernameValidation.valid) {
  setError(usernameValidation.error);
}
```

---

#### 4. **Response Types** (`lib/api/responseTypes.ts`)
**Files to update:**
- `features/auth/services/authApi.ts`
- `features/auth/types/auth.ts`

**What to do:**
- [ ] Import `SuccessResponse`, `ErrorResponse` from `lib/api/responseTypes.ts`
- [ ] Type API responses properly
- [ ] Remove duplicate type definitions

**Example:**
```typescript
// BEFORE
export interface LoginResponse {
  data: {
    user: User;
    token: string;
    organizations: Organization[];
  };
}

// AFTER
import type { SuccessResponse } from '@/lib/api/responseTypes';

export type LoginResponse = SuccessResponse<{
  user: User;
  token: string;
  organizations: Organization[];
}>;
```

---

#### 5. **Constants** (`lib/constants/app.ts`)
**Files to update:**
- `features/auth/components/RegisterForm.tsx`
- `features/auth/hooks/useAuth.ts`

**What to do:**
- [ ] Import `USER_ROLES` from `lib/constants/app.ts`
- [ ] Import `STORAGE_KEYS` (if using localStorage directly)
- [ ] Remove hardcoded strings

**Example:**
```typescript
// BEFORE
if (user.role === 'admin') { ... }

// AFTER
import { USER_ROLES } from '@/lib/constants/app';

if (user.role === USER_ROLES.ADMIN) { ... }
```

---

#### 6. **RBAC Permissions** (`lib/auth/permissions.ts`)
**Files to update:**
- `features/auth/components/` (any component checking roles)
- `shared/components/layout/Sidebar.tsx` (menu items based on role)

**What to do:**
- [ ] Import `isAdmin`, `isManagerOrAbove`, `canPerformAction` from `lib/auth/permissions.ts`
- [ ] Replace manual role checks with permission functions
- [ ] Hide/disable UI elements based on permissions

**Example:**
```typescript
// BEFORE
{user?.role === 'admin' && <AdminButton />}

// AFTER
import { isAdmin } from '@/lib/auth/permissions';

{isAdmin(user) && <AdminButton />}
```

---

## 🎯 Phase 2.5: Create Missing Auth Components

**Files that DON'T exist yet:**
- [ ] `features/auth/components/LoginForm.tsx` - Create with validation + toast
- [ ] `features/auth/components/RegisterForm.tsx` - Create with validation + toast
- [ ] `features/auth/components/OrgSelector.tsx` - Organization selector modal
- [ ] `pages/auth/LoginPage.tsx` - Login page using LoginForm
- [ ] `pages/auth/RegisterPage.tsx` - Register page using RegisterForm
- [ ] `pages/auth/SelectOrganizationPage.tsx` - Org selection page

---

## 🎯 Phase 2.5: Device Feature (If Exists)

**Check if these exist:**
- [ ] `features/devices/services/deviceApi.ts`
- [ ] `features/devices/hooks/useDevices.ts`
- [ ] `features/devices/components/DeviceTable.tsx`

**If they exist, apply same refactoring:**
- [ ] Add error handling with `handleAPIError`
- [ ] Add toast notifications
- [ ] Use response types
- [ ] Add permission checks (only admin/manager can activate devices)

---

## ✅ Acceptance Criteria

After refactoring is complete:
- [ ] All API errors show Indonesian messages via toast
- [ ] All successful actions show success toast
- [ ] All form inputs use centralized validators
- [ ] All API responses properly typed with `SuccessResponse`/`ErrorResponse`
- [ ] All hardcoded role strings replaced with `USER_ROLES` constants
- [ ] All permission checks use `lib/auth/permissions.ts` functions
- [ ] No console.log/console.error in production code (use toast)
- [ ] Code consistency across all features

---

## 📝 Testing Checklist

After refactoring:
- [ ] Login with correct credentials → Success toast + redirect
- [ ] Login with wrong credentials → Error toast with Indonesian message
- [ ] Register with invalid username → Validation error shown
- [ ] Register with weak password → Validation error shown
- [ ] Logout → Success toast + redirect to login
- [ ] Select organization (if multiple) → Success toast + redirect to dashboard
- [ ] Network error → User-friendly error toast (not technical error)
- [ ] 401 Unauthorized → Auto-logout + redirect to login

---

---

## 🎯 Backend: Refactor with Shared Utilities

### ✅ Already Using:
- ✅ `shared.database` - Database session
- ✅ `shared.config` - Settings from .env
- ✅ `shared.api_routes` - Centralized API route definitions

### ❌ NOT Using (Need to Refactor):

#### 1. **Error Handling** (`shared/errors.py`)
**Files to update:**
- `services/auth/routes.py`
- `services/device/routes.py`
- `services/auth/use_cases/login.py`
- `services/auth/use_cases/register.py`
- `services/device/use_cases/activate_device.py`

**What to do:**
- [ ] Import custom exceptions from `shared.errors`:
  ```python
  from shared.errors import (
      ValidationError, AuthenticationError, NotFoundError,
      PermissionDenied, handle_errors, ErrorCodes
  )
  ```
- [ ] Replace `raise HTTPException` with custom exceptions
- [ ] Use `@handle_errors` decorator on route functions to auto-convert
- [ ] Use `ErrorCodes` constants instead of hardcoded error codes

**Example:**
```python
# BEFORE
@router.post("/login")
def login(request: LoginRequest):
    try:
        result = use_case.execute(...)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

# AFTER
from shared.errors import AuthenticationError, handle_errors

@router.post("/login")
@handle_errors
def login(request: LoginRequest):
    # Use case will raise AuthenticationError
    result = use_case.execute(...)
    # @handle_errors decorator converts to HTTPException automatically
```

**In use cases:**
```python
# BEFORE (use_cases/login.py)
if not user:
    raise Exception("Invalid credentials")

# AFTER
from shared.errors import AuthenticationError, ErrorCodes

if not user:
    raise AuthenticationError(
        message="Invalid username or password",
        code=ErrorCodes.INVALID_CREDENTIALS
    )
```

---

#### 2. **Standardized Responses** (`shared/responses.py`)
**Files to update:**
- `services/auth/routes.py`
- `services/device/routes.py`
- `services/auth/dtos.py` (response models)

**What to do:**
- [ ] Import response formatters:
  ```python
  from shared.responses import (
      success_response, error_response, paginated_response
  )
  ```
- [ ] Wrap return data with `success_response()`
- [ ] Use `paginated_response()` for list endpoints
- [ ] Remove custom response formatting code

**Example:**
```python
# BEFORE
@router.post("/login")
def login(request: LoginRequest):
    result = use_case.execute(...)
    return {
        "data": {
            "user": result["user"],
            "token": result["token"],
            "organizations": result["organizations"]
        }
    }

# AFTER
from shared.responses import success_response

@router.post("/login")
def login(request: LoginRequest):
    result = use_case.execute(...)
    return success_response(
        data={
            "user": result["user"],
            "token": result["token"],
            "organizations": result["organizations"]
        },
        message="Login successful"
    )
```

---

#### 3. **Input Validation** (`shared/validators.py`)
**Files to update:**
- `services/auth/use_cases/register.py`
- `services/device/use_cases/activate_device.py`
- Any use case that validates user input

**What to do:**
- [ ] Import validators:
  ```python
  from shared.validators import (
      validate_email, validate_password, validate_username,
      validate_activation_code, sanitize_string
  )
  ```
- [ ] Use validators before processing data
- [ ] Raise `ValidationError` with proper details
- [ ] Sanitize user inputs to prevent injection

**Example:**
```python
# BEFORE (use_cases/register.py)
def execute(self, username: str, password: str):
    if len(username) < 3:
        raise Exception("Username too short")
    if len(password) < 8:
        raise Exception("Password too short")
    # ... create user

# AFTER
from shared.validators import validate_username, validate_password
from shared.errors import ValidationError

def execute(self, username: str, password: str):
    # Validate username
    is_valid_username, error_msg = validate_username(username)
    if not is_valid_username:
        raise ValidationError(
            message=error_msg,
            details={"field": "username"}
        )

    # Validate password
    is_valid_password, error_msg = validate_password(password, min_length=8)
    if not is_valid_password:
        raise ValidationError(
            message=error_msg,
            details={"field": "password"}
        )

    # Sanitize inputs
    username = sanitize_string(username)

    # ... create user
```

---

#### 4. **Logging** (`shared/logging.py`)
**Files to update:**
- `services/auth/routes.py` - Log all auth attempts
- `services/device/routes.py` - Log device activations
- `services/auth/use_cases/login.py` - Audit trail
- `services/auth/use_cases/register.py` - Audit trail

**What to do:**
- [ ] Import loggers:
  ```python
  from shared.logging import (
      RequestLogger, ErrorLogger, AuditLogger, PerformanceLogger
  )
  ```
- [ ] Create logger instances
- [ ] Log requests with `RequestLogger`
- [ ] Log errors with `ErrorLogger`
- [ ] Log user actions with `AuditLogger`
- [ ] Monitor performance with `PerformanceLogger`

**Example:**
```python
# routes.py
from shared.logging import RequestLogger, AuditLogger
import time

request_logger = RequestLogger()
audit_logger = AuditLogger()

@router.post("/login")
@handle_errors
def login(request: LoginRequest):
    start_time = time.time()

    try:
        result = use_case.execute(...)

        # Log successful login
        duration_ms = (time.time() - start_time) * 1000
        request_logger.log_request(
            method="POST",
            path="/api/v1/auth/login",
            status_code=200,
            duration_ms=duration_ms,
            user_id=result["user"]["id"]
        )

        # Audit log
        audit_logger.log_action(
            user_id=result["user"]["id"],
            action="auth.login",
            resource_type="user",
            resource_id=result["user"]["id"],
            details={"ip_address": request.client.host}
        )

        return success_response(data=result)

    except Exception as e:
        # Log error
        error_logger.log_error(
            error=e,
            context={"username": request.username},
            user_id=None
        )
        raise
```

---

### Backend Refactoring Checklist:

#### Auth Service:
- [ ] `services/auth/routes.py` - Use `@handle_errors`, `success_response()`, logging
- [ ] `services/auth/use_cases/login.py` - Raise custom exceptions, audit logging
- [ ] `services/auth/use_cases/register.py` - Use validators, raise ValidationError
- [ ] `services/auth/dtos.py` - Update response models to match standard format (optional)

#### Device Service:
- [ ] `services/device/routes.py` - Use `@handle_errors`, `success_response()`, logging
- [ ] `services/device/use_cases/activate_device.py` - Use `validate_activation_code()`

#### Main App:
- [ ] `main.py` - Setup global error handler (optional, if needed)

---

### Backend Testing Checklist:

After refactoring:
- [ ] Login with valid creds → Success response with standard format
- [ ] Login with invalid creds → AuthenticationError converted to 401 with error code
- [ ] Register with weak password → ValidationError with field details
- [ ] Device activation with invalid code → ValidationError with proper message
- [ ] All endpoints log requests to console/file
- [ ] All errors logged with context
- [ ] Audit log entries created for sensitive actions

---

## 🚫 DO NOT IMPLEMENT YET

Just planning for now. Wait for approval before implementing.
