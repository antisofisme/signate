# Shared Components Code Review Checklist

**Purpose:** Standard checklist for reviewing shared utilities before deployment
**Last Updated:** 2025-11-27

---

## Pre-Review Setup

- [ ] Pull latest code from main branch
- [ ] Read recent git commit messages
- [ ] Check for open issues related to shared components
- [ ] Review previous audit reports

---

## 1. Functionality Review

### Authentication & Authorization (`shared/auth.py`)

- [ ] JWT token creation includes all required fields (sub, username, role, organization_id)
- [ ] Token expiration is enforced correctly
- [ ] Token type validation works (access, refresh, device)
- [ ] Password hashing uses bcrypt with proper rounds
- [ ] Password verification doesn't leak timing information
- [ ] Role hierarchy is consistent with RBAC design
- [ ] Device token validation includes organization_id check
- [ ] Session validation doesn't add excessive DB queries
- [ ] WebSocket authentication works correctly

**Test Commands:**
```bash
# Test JWT token creation
python3 -c "from shared.auth import create_access_token; print(create_access_token({'sub': '1', 'username': 'test', 'role': 'admin'}))"

# Test password hashing
python3 -c "from shared.auth import get_password_hash, verify_password; h = get_password_hash('test123'); print(verify_password('test123', h))"
```

---

### Middleware (`shared/middleware.py`)

- [ ] No duplicate authentication functions (use shared.auth instead)
- [ ] Permission checking logic is correct (single, any, all)
- [ ] Role-based access control works as expected
- [ ] Organization access validation prevents cross-tenant access
- [ ] Resource ownership validation is thorough
- [ ] Error responses are consistent with shared.errors

**Test Commands:**
```bash
# Check for duplicate get_current_user
grep -n "def get_current_user" backend-python/shared/*.py

# Verify no services import middleware auth
grep -r "from shared.middleware import get_current_user" backend-python/services/
```

---

### Error Handling (`shared/errors.py`)

- [ ] All custom exceptions inherit from AppException
- [ ] Error codes are unique and descriptive
- [ ] Error handler decorator works for both sync and async
- [ ] Error responses don't leak sensitive information
- [ ] Stack traces are logged but not exposed to clients
- [ ] HTTP status codes are appropriate for each error type

**Test Commands:**
```bash
# Test error handler decorator
python3 -c "
from shared.errors import handle_errors, ValidationError
@handle_errors
def test_func():
    raise ValidationError('Test error', details={'field': 'email'})
try:
    test_func()
except Exception as e:
    print(e)
"
```

---

### Rate Limiting (`shared/rate_limiter.py`)

- [ ] Redis connection is tested on startup
- [ ] In-memory fallback works when Redis unavailable
- [ ] Rate limit enforcement is correct (requests/window)
- [ ] IP extraction handles X-Forwarded-For correctly
- [ ] Cleanup mechanism prevents memory leaks
- [ ] Rate limit decorator works with both sync and async routes
- [ ] Error messages include retry-after header

**Test Commands:**
```bash
# Test rate limiting (5 requests should succeed, 6th should fail)
for i in {1..6}; do
  curl -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "wrong"}'
done
```

---

### Logging (`shared/logging.py`)

- [ ] All loggers use structured logging format
- [ ] Request logging includes duration and status code
- [ ] Error logging includes stack traces
- [ ] Audit logging persists to database when configured
- [ ] Performance logging captures slow queries
- [ ] No sensitive data is logged (passwords, tokens)

**Test Commands:**
```bash
# Check log output format
docker logs signage-backend --tail 50 | grep "INFO\|ERROR\|WARNING"
```

---

### Responses (`shared/responses.py`)

- [ ] All response helpers return consistent format
- [ ] Timestamps are in ISO 8601 format with UTC timezone
- [ ] Pagination responses include all required fields
- [ ] Error responses match error handler output
- [ ] No Pydantic validation errors on response models

**Test Commands:**
```bash
# Test response format
python3 -c "
from shared.responses import success_response, error_response
print(success_response({'id': 1}, 'Success'))
print(error_response('Error message', 'ERROR_CODE'))
"
```

---

### Configuration (`shared/config.py`)

- [ ] All required environment variables are documented
- [ ] Defaults are safe (DEBUG=False in production)
- [ ] Secrets are loaded from environment, not hardcoded
- [ ] CORS origins are parsed correctly
- [ ] Configuration validates on startup
- [ ] No unused configuration fields

**Test Commands:**
```bash
# Check environment variables loaded
python3 -c "from shared.config import settings; print(settings.DATABASE_URL[:20])"

# Verify CORS origins parsing
python3 -c "from shared.config import settings; print(settings.get_cors_origins_list())"
```

---

## 2. Clean Code Review

### Code Organization

- [ ] Functions have single responsibility
- [ ] No functions longer than 50 lines
- [ ] No nested conditionals deeper than 3 levels
- [ ] Helper functions are properly named
- [ ] Constants are defined at module level
- [ ] No magic numbers or strings

---

### Dead Code Detection

```bash
# Check for unused imports
pylint --disable=all --enable=unused-import backend-python/shared/*.py

# Check for undefined names
pylint --disable=all --enable=undefined-variable backend-python/shared/*.py

# Check for unreachable code
pylint --disable=all --enable=unreachable backend-python/shared/*.py
```

- [ ] No unused imports
- [ ] No unreachable code blocks
- [ ] No commented-out code
- [ ] All functions are exported and used
- [ ] No duplicate function definitions

---

### Documentation

- [ ] All public functions have docstrings
- [ ] Docstrings follow Google/NumPy style
- [ ] Type hints on all function signatures
- [ ] Complex logic has inline comments
- [ ] Module-level docstring explains purpose
- [ ] README documents shared utilities

---

## 3. Security Review

### Authentication Security

- [ ] Password hashing uses bcrypt (not MD5/SHA1)
- [ ] JWT secret key is loaded from environment
- [ ] JWT algorithm is HS256 or RS256 (not HS1 or none)
- [ ] Token expiration is enforced
- [ ] Session revocation is checked
- [ ] No hardcoded credentials

**Security Scan:**
```bash
# Check for hardcoded secrets
grep -rn "password\s*=\s*['\"]" backend-python/shared/
grep -rn "secret\s*=\s*['\"]" backend-python/shared/

# Check for weak algorithms
grep -rn "MD5\|SHA1\|DES" backend-python/shared/
```

---

### Authorization Security

- [ ] Permission checks are enforced on all protected routes
- [ ] Role hierarchy prevents privilege escalation
- [ ] Organization isolation is enforced
- [ ] No user can access other organization's data
- [ ] Admin privileges are properly scoped

**Test Commands:**
```bash
# Test cross-organization access (should fail)
TOKEN="<user_token_org_1>"
curl http://localhost:8001/api/v1/organizations/2/devices \
  -H "Authorization: Bearer $TOKEN"
# Should return 403 Forbidden
```

---

### Input Validation

- [ ] All inputs are validated (Pydantic models)
- [ ] SQL injection is prevented (parameterized queries)
- [ ] XSS is prevented (no raw HTML rendering)
- [ ] CSRF protection is enabled for state-changing operations
- [ ] File uploads are validated and scanned

---

### Rate Limiting Security

- [ ] Login endpoints have rate limiting (5 requests/5 minutes)
- [ ] Registration endpoints have rate limiting (3 requests/hour)
- [ ] Password reset has rate limiting (3 requests/hour)
- [ ] API endpoints have reasonable limits
- [ ] Rate limiting uses IP address (proxy-aware)

---

## 4. Consistency Review

### Import Consistency

```bash
# Check all services use shared.auth (not middleware)
grep -r "from shared.auth import get_current_user" backend-python/services/ | wc -l
# Should be 19+

grep -r "from shared.middleware import get_current_user" backend-python/services/ | wc -l
# Should be 0
```

- [ ] All services import from shared.auth (not middleware)
- [ ] All services use shared.errors classes (not HTTPException)
- [ ] All services use shared.responses formatters
- [ ] All services use shared.logging loggers

---

### Error Handling Consistency

```bash
# Check for HTTPException usage in shared/
grep -rn "raise HTTPException" backend-python/shared/

# Check for proper error code usage
grep -rn "ErrorCodes\." backend-python/shared/
```

- [ ] All custom exceptions use ErrorCodes enum
- [ ] No bare `except:` clauses
- [ ] Error messages are user-friendly (not technical)
- [ ] Error details don't leak implementation info

---

### Response Format Consistency

- [ ] All responses include `success` field
- [ ] All responses include `timestamp` field
- [ ] Error responses follow standardized format
- [ ] Pagination responses include all required fields

---

## 5. Performance Review

### Database Queries

- [ ] No N+1 query problems
- [ ] Queries use proper indexes
- [ ] Bulk operations use bulk insert/update
- [ ] Connection pooling is configured
- [ ] No DB queries in hot paths (use cache)

**Performance Test:**
```bash
# Test authentication endpoint latency
time curl http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Should be < 50ms
```

---

### Caching

- [ ] Redis is used for session cache
- [ ] Rate limiter uses Redis (not in-memory in production)
- [ ] Cache TTLs are appropriate
- [ ] Cache invalidation is correct
- [ ] No cache stampede on cold start

---

### Resource Management

- [ ] Database connections are properly closed
- [ ] File handles are closed in finally blocks
- [ ] Redis connections use connection pooling
- [ ] Memory cleanup is performed (rate limiter)

---

## 6. Integration Review

### Service Integration

```bash
# Check which services use each shared module
echo "=== shared.auth usage ==="
grep -r "from shared.auth import" backend-python/services/ | cut -d: -f1 | sort | uniq

echo "=== shared.errors usage ==="
grep -r "from shared.errors import" backend-python/services/ | cut -d: -f1 | sort | uniq

echo "=== shared.rate_limiter usage ==="
grep -r "from shared.rate_limiter import" backend-python/services/ | cut -d: -f1 | sort | uniq
```

- [ ] All services use shared utilities consistently
- [ ] No service bypasses shared authentication
- [ ] No service implements own rate limiting
- [ ] No service implements own error handling

---

### Dependency Check

```bash
# Check for circular imports
python3 -c "import sys; sys.path.insert(0, 'backend-python'); import shared.auth"
# Should not raise ImportError
```

- [ ] No circular import dependencies
- [ ] All dependencies are documented in requirements.txt
- [ ] No hidden dependencies on specific library versions

---

## 7. Testing Review

### Unit Test Coverage

```bash
# Run unit tests (if they exist)
pytest backend-python/tests/shared/ -v --cov=backend-python/shared/ --cov-report=term

# Check coverage percentage
# Target: 80%+
```

- [ ] JWT token tests (creation, validation, expiration)
- [ ] Password hashing tests (correct hash, verification)
- [ ] Permission checking tests (allow/deny scenarios)
- [ ] Rate limiting tests (within limit, exceeded limit)
- [ ] Error handling tests (all exception types)
- [ ] Response formatter tests (all helpers)

---

### Integration Test Coverage

```bash
# Run integration tests
pytest backend-python/tests/integration/ -v -k "auth or permission or rate_limit"
```

- [ ] End-to-end authentication flow
- [ ] Login with rate limiting
- [ ] Logout and session revocation
- [ ] Permission-based access control
- [ ] Cross-organization access prevention

---

## 8. Deployment Checklist

### Pre-Deployment

- [ ] All CRITICAL issues from audit report fixed
- [ ] All HIGH priority issues addressed
- [ ] Unit tests pass (80%+ coverage)
- [ ] Integration tests pass
- [ ] Performance benchmarks meet targets
- [ ] Security scan passed (no vulnerabilities)
- [ ] Code review approved by senior developer

---

### Configuration Validation

```bash
# Check production configuration
grep -E "DEBUG|ENVIRONMENT|REDIS_URL|DATABASE_URL" .env
```

- [ ] DEBUG=false in production
- [ ] ENVIRONMENT=production
- [ ] REDIS_URL points to production Redis
- [ ] DATABASE_URL points to production DB
- [ ] SECRET_KEY is strong (not default)
- [ ] CORS_ORIGINS includes only trusted domains

---

### Monitoring Setup

- [ ] Application logs are shipped to centralized logging
- [ ] Error tracking is configured (Sentry/similar)
- [ ] Performance monitoring is enabled (APM)
- [ ] Rate limit metrics are tracked
- [ ] Session metrics are tracked
- [ ] Audit log retention is configured

---

### Rollback Plan

- [ ] Previous version tagged in Git
- [ ] Database backup created
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging

---

## 9. Post-Deployment Validation

### Smoke Tests

```bash
# Test authentication flow
curl -X POST https://api.zhmhotels.online/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Test protected endpoint
TOKEN="<token from login>"
curl https://api.zhmhotels.online/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Test rate limiting
for i in {1..6}; do
  curl -X POST https://api.zhmhotels.online/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "wrong", "password": "wrong"}'
done
```

- [ ] Login works correctly
- [ ] Protected endpoints require authentication
- [ ] Rate limiting is enforced
- [ ] Error responses are consistent
- [ ] Logging is working
- [ ] Monitoring shows healthy metrics

---

### Performance Validation

```bash
# Test authentication latency
for i in {1..10}; do
  time curl -s https://api.zhmhotels.online/api/v1/auth/me \
    -H "Authorization: Bearer $TOKEN" > /dev/null
done
```

- [ ] Authentication requests < 50ms
- [ ] Protected endpoint requests < 100ms
- [ ] No memory leaks (monitor over 24 hours)
- [ ] No connection pool exhaustion
- [ ] Redis cache hit rate > 90%

---

### Security Validation

- [ ] No secrets in logs
- [ ] No stack traces exposed to clients
- [ ] HTTPS is enforced
- [ ] CORS is configured correctly
- [ ] Rate limiting prevents abuse
- [ ] Session revocation works

---

## 10. Documentation Update

- [ ] Update CHANGELOG.md with changes
- [ ] Update API documentation
- [ ] Update deployment guide
- [ ] Update monitoring runbook
- [ ] Create incident response plan
- [ ] Document known issues (if any)

---

## Review Sign-Off

| Reviewer | Role | Date | Signature | Status |
|----------|------|------|-----------|--------|
| ________ | Senior Developer | ______ | ________ | [ ] APPROVED |
| ________ | Tech Lead | ______ | ________ | [ ] APPROVED |
| ________ | Security Engineer | ______ | ________ | [ ] APPROVED |

---

## Next Review

**Scheduled Date:** _________________
**Trigger Events:**
- [ ] After major feature addition
- [ ] After security incident
- [ ] Quarterly review
- [ ] Before major deployment

---

**Template Version:** 1.0
**Last Updated:** 2025-11-27
**Maintained By:** DevOps Team
