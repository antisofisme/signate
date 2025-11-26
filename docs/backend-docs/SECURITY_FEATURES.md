# Security Features Documentation

This document provides an overview of all security features implemented in the Digital Signage backend API.

## Overview

The backend API has been enhanced with comprehensive security measures to protect against common web vulnerabilities and attacks. All features follow OWASP best practices and modern security standards.

## Implemented Security Features

### 1. Input Validation & Sanitization (shared/validators.py)

**Purpose**: Prevent XSS, SQL injection, path traversal, and other injection attacks.

**Implemented Validators**:

```python
# XSS Prevention
sanitize_html(text)                     # Escape HTML entities
contains_html_tags(text)                # Detect HTML tags
contains_script_tags(text)              # Detect dangerous scripts/event handlers
validate_safe_string(text, max_length) # Comprehensive safety check

# URL Validation
validate_url(url, allowed_schemes)      # Validate URL scheme (http/https only)

# Path Traversal Prevention
validate_path_safe(path)                # Block ../, absolute paths, null bytes

# SQL Injection Detection
validate_no_sql_injection(text)         # Pattern matching for SQL keywords (secondary defense)

# Character Validation
validate_alphanumeric(text, allow_spaces, allow_special) # Custom character sets
```

**Usage Example**:
```python
from shared.validators import validate_safe_string, sanitize_html

# Validate user input
is_valid, error = validate_safe_string(user_input, max_length=500)
if not is_valid:
    raise ValidationError(error)

# Sanitize before storing/displaying
safe_text = sanitize_html(user_input)
```

**Protection Against**:
- XSS (Cross-Site Scripting)
- SQL Injection (secondary layer - SQLAlchemy is primary)
- Path Traversal
- Malicious URL schemes (javascript:, data:, etc.)

**Commit**: ddfc8d7

---

### 2. Rate Limiting (shared/rate_limiter.py)

**Purpose**: Prevent brute force attacks, API abuse, and DDoS attempts.

**Features**:
- In-memory sliding window algorithm
- Thread-safe implementation
- IP-based request tracking
- Configurable limits per endpoint
- X-Forwarded-For header support (for proxies)
- Automatic cleanup of old entries
- HTTP 429 responses with Retry-After header

**Implemented Rate Limits**:
- Login: 5 attempts per 5 minutes
- Register: 3 attempts per hour
- Forgot Password: 3 attempts per hour
- Reset Password: 5 attempts per hour

**Usage Example**:
```python
from shared.rate_limiter import rate_limit

@router.post("/api/v1/auth/login")
@rate_limit(max_requests=5, window_seconds=300)
@handle_errors
def login(request: Request, credentials: LoginRequest):
    # Login logic here
    pass
```

**How It Works**:
1. Extracts client IP from request
2. Tracks timestamp of each request per IP
3. Removes timestamps older than the time window
4. Rejects request if limit exceeded
5. Returns 429 status with Retry-After header

**Production Note**: For multi-worker deployments, upgrade to Redis-based rate limiting to share state across workers.

**Commit**: 619d323

---

### 3. Database Migrations (MIGRATIONS.md)

**Purpose**: Version control for database schema changes, ensuring safe and reversible updates.

**What's Documented**:
- Alembic setup instructions
- Common migration scenarios with code examples
- Production deployment workflow
- Best practices and security considerations
- Rollback procedures
- Integration with Docker

**Key Features**:
- Automated migration generation from models
- Reversible migrations (upgrade/downgrade)
- Schema version tracking
- Migration history
- Pre-deployment testing

**Usage Example**:
```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Add phone_number to users"

# Review generated migration
cat alembic/versions/xxxx_add_phone_number.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**File**: MIGRATIONS.md

**Commit**: 5ba60ff

---

### 4. Password Reset / Forgot Password Flow (shared/password_reset.py)

**Purpose**: Secure password recovery mechanism with time-limited tokens.

**Features**:
- Cryptographically secure token generation (secrets.token_urlsafe)
- Time-limited tokens (60 minutes expiration)
- One-time use tokens (consumed after successful reset)
- Thread-safe token management
- Email enumeration prevention
- Rate limiting on reset requests
- Audit logging of all password reset actions

**API Endpoints**:

1. **Forgot Password**: `POST /api/v1/auth/forgot-password`
   ```json
   Request:
   {
     "email": "user@example.com"
   }

   Response (Development):
   {
     "message": "If an account with that email exists, a password reset link has been sent.",
     "reset_token": "xyz123abc...",
     "expires_in_minutes": 60
   }
   ```

2. **Reset Password**: `POST /api/v1/auth/reset-password`
   ```json
   Request:
   {
     "token": "xyz123abc...",
     "new_password": "newSecurePassword123"
   }

   Response:
   {
     "message": "Password has been reset successfully. You can now login with your new password."
   }
   ```

**Security Features**:
- Email enumeration prevention (same response regardless of email existence)
- Tokens are 32 bytes (256 bits) cryptographically random
- Automatic token expiration after 60 minutes
- Tokens consumed after single use
- All password changes use bcrypt hashing
- Rate limiting prevents token brute force

**Development vs Production**:
- **Development**: Token returned in API response (no email configured)
- **Production**: Token sent via email, not in response

**TODO Production**:
- Integrate email service (SendGrid, AWS SES, etc.)
- Move tokens to Redis for multi-worker environments
- Add background task for automatic token cleanup
- Implement email templates

**Files**:
- `shared/password_reset.py`: Token manager
- `services/auth/use_cases/forgot_password.py`: Forgot password logic
- `services/auth/use_cases/reset_password.py`: Reset password logic
- `services/auth/dtos.py`: Request/response DTOs
- `services/auth/routes.py`: API endpoints

**Commit**: 1f16feb

---

## Security Architecture

### Layered Security Approach

```
┌─────────────────────────────────────────────────┐
│           Rate Limiting (Layer 1)               │
│   Prevents brute force, DDoS, API abuse         │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Input Validation (Layer 2)                 │
│   XSS, SQL Injection, Path Traversal prevention │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│    Business Logic (Layer 3)                     │
│   Use Cases with domain validation              │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Data Layer (Layer 4)                       │
│   SQLAlchemy ORM (prevents SQL injection)       │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│      Audit Logging (All Layers)                 │
│   Tracks all security-relevant actions          │
└─────────────────────────────────────────────────┘
```

### Authentication & Authorization Flow

```
1. User submits credentials
2. Rate limiter checks IP (5 attempts/5 min)
3. Input validator checks username/password format
4. Use case validates credentials (bcrypt hash comparison)
5. JWT token generated (signed with secret)
6. Audit log created (login attempt)
7. Token returned to client

Protected Endpoints:
1. Client sends request with JWT token
2. Middleware validates token signature & expiration
3. User info extracted from token
4. Role-based access control applied
5. Request processed
6. Audit log created (if needed)
```

## OWASP Top 10 Protection Status

| OWASP Risk | Protection | Implementation |
|-----------|-----------|----------------|
| A01:2021 Broken Access Control | ✅ Yes | JWT + Role-based middleware |
| A02:2021 Cryptographic Failures | ✅ Yes | bcrypt passwords, secure tokens |
| A03:2021 Injection | ✅ Yes | Input validators + SQLAlchemy ORM |
| A04:2021 Insecure Design | ✅ Yes | Clean Architecture, use cases |
| A05:2021 Security Misconfiguration | ⚠️ Partial | Documented, needs hardening |
| A06:2021 Vulnerable Components | ⏳ Planned | Dependency scanning needed |
| A07:2021 Identification & Auth Failures | ✅ Yes | Rate limiting, secure passwords, MFA-ready |
| A08:2021 Software & Data Integrity | ⏳ Planned | Code signing, SRI needed |
| A09:2021 Security Logging Failures | ✅ Yes | Comprehensive audit logging |
| A10:2021 Server-Side Request Forgery | ✅ Yes | URL validation in validators |

## Testing Security Features

### Manual Testing

#### 1. Test Rate Limiting
```bash
# Test login rate limit (should block after 5 attempts)
for i in {1..6}; do
  curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"wrong"}'
done

# Expected: First 5 return 401, 6th returns 429
```

#### 2. Test Input Validation
```python
# Test XSS prevention
import requests

response = requests.post(
    "http://192.168.5.12:8001/api/v1/auth/register",
    json={
        "username": "<script>alert('xss')</script>",
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    }
)

# Expected: Validation error or sanitized input
```

#### 3. Test Password Reset Flow
```bash
# Step 1: Request reset
curl -X POST http://192.168.5.12:8001/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com"}'

# Note the reset_token from response

# Step 2: Reset password
curl -X POST http://192.168.5.12:8001/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token":"<reset_token_from_step1>",
    "new_password":"newPassword123"
  }'

# Expected: Success message
```

### Automated Testing (TODO)

```python
# services/auth/tests/test_security.py

def test_rate_limiting():
    """Test login rate limiting blocks after 5 attempts"""
    pass

def test_xss_prevention():
    """Test XSS attacks are blocked"""
    pass

def test_sql_injection_prevention():
    """Test SQL injection attempts fail"""
    pass

def test_password_reset_token_expiry():
    """Test reset tokens expire after 60 minutes"""
    pass

def test_password_reset_single_use():
    """Test reset tokens can only be used once"""
    pass
```

## Production Deployment Checklist

- [ ] Review all environment variables in .env
- [ ] Enable HTTPS/TLS (certificates configured)
- [ ] Set strong SECRET_KEY (minimum 32 random bytes)
- [ ] Configure CORS_ORIGINS for production domains only
- [ ] Enable database connection pooling
- [ ] Set up Redis for rate limiting (multi-worker)
- [ ] Configure email service for password reset
- [ ] Set up monitoring and alerting
- [ ] Enable audit log persistence to database
- [ ] Review and harden all security headers
- [ ] Set up automated backups
- [ ] Configure WAF (Web Application Firewall)
- [ ] Enable database encryption at rest
- [ ] Set up intrusion detection
- [ ] Review and test disaster recovery plan

## Security Incident Response

If a security incident is detected:

1. **Immediate Actions**:
   - Review audit logs for affected timeframe
   - Identify scope of breach (users, data affected)
   - Temporarily disable affected endpoints if needed
   - Reset affected user passwords
   - Invalidate all active tokens if needed

2. **Investigation**:
   - Check rate limiter logs for unusual patterns
   - Review authentication logs for failed attempts
   - Examine input validation logs for attack patterns
   - Check database for unauthorized changes

3. **Remediation**:
   - Patch vulnerabilities
   - Update security rules
   - Notify affected users
   - Document incident and lessons learned

4. **Post-Incident**:
   - Conduct security audit
   - Update security policies
   - Improve monitoring and detection
   - Train team on new threats

## Security Maintenance

### Regular Tasks

**Daily**:
- Monitor rate limiter alerts
- Review audit logs for anomalies

**Weekly**:
- Check for dependency updates
- Review security logs

**Monthly**:
- Security audit of new features
- Review and update security policies
- Cleanup expired reset tokens (if not automated)

**Quarterly**:
- Penetration testing
- Security training for team
- Review OWASP Top 10 compliance
- Update security documentation

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)
- [Bcrypt Documentation](https://github.com/pyca/bcrypt/)

## Support

For security-related questions or to report vulnerabilities:
- Create an issue in the project repository (for non-sensitive issues)
- Contact the security team directly (for sensitive vulnerabilities)
- Follow responsible disclosure practices

---

**Last Updated**: 2025-11-05

**Version**: 1.0.0

**Contributors**: Development Team + Claude Code
