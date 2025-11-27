# Security Implementation Guide - Quick Start

This guide provides **immediately implementable** security improvements for your digital signage system. Each section includes copy-paste ready code that can be integrated into your existing codebase.

## Priority 1: Critical Security Fixes (Implement TODAY)

### 1. Add Rate Limiting to Prevent Brute Force

```bash
# Install required package
pip install slowapi redis
```

Create new file: `backend/app/core/middleware/rate_limiter.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
import redis
import hashlib
import json
from datetime import datetime

# Initialize Redis connection
redis_client = redis.Redis(host='192.168.5.12', port=6379, db=0, decode_responses=True)

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri="redis://192.168.5.12:6379"
)

class LoginRateLimiter:
    """Prevent brute force attacks on login"""

    def __init__(self):
        self.redis = redis_client
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes

    def check_and_update(self, identifier: str) -> tuple[bool, int]:
        """Check if login attempt is allowed"""
        key = f"login_attempts:{identifier}"

        # Get current attempts
        attempts = self.redis.get(key)
        if not attempts:
            attempts = 0
        else:
            attempts = int(attempts)

        # Check if locked out
        if attempts >= self.max_attempts:
            ttl = self.redis.ttl(key)
            if ttl > 0:
                return False, ttl

        # Increment attempts
        self.redis.incr(key)
        self.redis.expire(key, self.lockout_duration)

        return attempts < self.max_attempts, 0

    def reset(self, identifier: str):
        """Reset attempts on successful login"""
        key = f"login_attempts:{identifier}"
        self.redis.delete(key)

# Global instance
login_limiter = LoginRateLimiter()
```

Update `backend/app/api/auth.py`:

```python
from app.core.middleware.rate_limiter import limiter, login_limiter
from fastapi import Request
import hashlib

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # 5 attempts per minute per IP
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    # Check rate limit by username
    username_hash = hashlib.sha256(login_data.username.encode()).hexdigest()[:16]
    allowed, retry_after = login_limiter.check_and_update(username_hash)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after} seconds",
            headers={"Retry-After": str(retry_after)}
        )

    # Your existing login logic...
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        # Failed login - attempts already incremented
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Successful login - reset attempts
    login_limiter.reset(username_hash)

    # Continue with token generation...
```

Update `backend/app/main.py`:

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.middleware.rate_limiter import limiter

# Add rate limiting to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 2. Add Security Headers

Create `backend/app/core/middleware/security_headers.py`:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS in production
        if not request.url.hostname in ["localhost", "127.0.0.1"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Basic CSP
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http://192.168.5.12:*;"
        )

        return response
```

Add to `backend/app/main.py`:

```python
from app.core.middleware.security_headers import SecurityHeadersMiddleware

# Add after CORS middleware
app.add_middleware(SecurityHeadersMiddleware)
```

### 3. Strengthen Password Requirements

Create `backend/app/core/security/password_validator.py`:

```python
import re
from typing import Tuple, List

class PasswordValidator:
    """Validate password strength"""

    MIN_LENGTH = 8  # Start with 8, increase to 12 later
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def validate(cls, password: str) -> Tuple[bool, List[str]]:
        """Validate password and return errors"""
        errors = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters")

        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain an uppercase letter")

        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain a lowercase letter")

        if cls.REQUIRE_NUMBERS and not re.search(r"\d", password):
            errors.append("Password must contain a number")

        if cls.REQUIRE_SPECIAL and not re.search(f"[{re.escape(cls.SPECIAL_CHARS)}]", password):
            errors.append("Password must contain a special character")

        # Check common passwords
        common_passwords = ["password", "admin123", "12345678", "qwerty"]
        if password.lower() in common_passwords:
            errors.append("Password is too common")

        return len(errors) == 0, errors
```

Update password hashing in `backend/app/core/security/password.py`:

```python
import bcrypt
from app.core.security.password_validator import PasswordValidator

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with validation"""

    # Validate password strength
    is_valid, errors = PasswordValidator.validate(password)
    if not is_valid:
        raise ValueError(f"Weak password: {', '.join(errors)}")

    # Use higher cost factor for better security
    salt = bcrypt.gensalt(rounds=12)  # Increased from default 10
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
```

### 4. Fix JWT Security

Update `backend/.env`:

```env
# Generate a strong secret: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=YOUR_GENERATED_32_CHARACTER_SECRET_HERE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

Update `backend/app/core/config.py`:

```python
from pydantic import field_validator

class Settings(BaseSettings):
    # ... existing fields ...

    JWT_SECRET: str = Field(..., min_length=32)  # Enforce minimum length

    @field_validator('JWT_SECRET')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        if v == "your_super_secret_jwt_key_change_this_in_production":
            raise ValueError("Please change the default JWT secret!")
        return v
```

### 5. Add Input Validation

Create `backend/app/core/security/validators.py`:

```python
import re
import html
from typing import Any
from fastapi import HTTPException, status

class InputValidator:
    """Validate and sanitize user inputs"""

    # Dangerous SQL patterns
    SQL_BLACKLIST = [
        r"(\bDROP\b|\bDELETE\b|\bUNION\b|\bINSERT\b|\bUPDATE\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"('|\"|;)"
    ]

    # XSS patterns
    XSS_BLACKLIST = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe"
    ]

    @classmethod
    def sanitize_string(cls, value: str, field_name: str = "input") -> str:
        """Sanitize string input"""
        if not value:
            return value

        # Check for SQL injection attempts
        for pattern in cls.SQL_BLACKLIST:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid characters in {field_name}"
                )

        # Check for XSS attempts
        for pattern in cls.XSS_BLACKLIST:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid HTML in {field_name}"
                )

        # HTML escape for safety
        return html.escape(value.strip())

    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email format"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format")
        return email.lower()

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate uploaded filename"""
        # Remove path components
        filename = filename.replace("../", "").replace("..\\", "")

        # Only allow safe characters
        if not re.match(r'^[\w\-. ]+$', filename):
            raise ValueError("Invalid filename")

        return filename
```

Update your Pydantic schemas to use validation:

```python
from pydantic import BaseModel, field_validator
from app.core.security.validators import InputValidator

class DeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = None

    @field_validator('device_name')
    def sanitize_device_name(cls, v):
        if v:
            return InputValidator.sanitize_string(v, "device_name")
        return v

class ContentUploadRequest(BaseModel):
    title: str
    description: Optional[str] = None

    @field_validator('title', 'description')
    def sanitize_text(cls, v):
        if v:
            return InputValidator.sanitize_string(v)
        return v
```

## Priority 2: Enhanced Device Security

### 6. Secure Device Activation

Update `backend/app/utils/device_utils.py`:

```python
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from app.core.config import settings

def generate_secure_activation_code(length: int = 6) -> tuple[str, str]:
    """Generate cryptographically secure activation code with verification"""

    # Use secrets for cryptographic randomness
    code = ''.join([str(secrets.randbelow(10)) for _ in range(length)])

    # Create HMAC for verification
    timestamp = int(datetime.utcnow().timestamp())
    message = f"{code}:{timestamp}"

    verification = hmac.new(
        settings.JWT_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # Use first 16 chars for brevity

    return code, verification

def verify_activation_code(code: str, verification: str, max_age_minutes: int = 10) -> bool:
    """Verify activation code with HMAC"""

    # Check codes from last max_age_minutes
    current_time = int(datetime.utcnow().timestamp())

    for minutes_ago in range(max_age_minutes + 1):
        timestamp = current_time - (minutes_ago * 60)
        message = f"{code}:{timestamp}"

        expected = hmac.new(
            settings.JWT_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]

        if hmac.compare_digest(verification, expected):
            return True

    return False
```

## Priority 3: Audit Logging

### 7. Add Security Event Logging

Create `backend/app/core/security/audit_logger.py`:

```python
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class SecurityEvent(str, Enum):
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILED = "login.failed"
    LOGOUT = "logout"
    RATE_LIMIT = "rate_limit.exceeded"
    INVALID_TOKEN = "token.invalid"
    PERMISSION_DENIED = "permission.denied"
    DEVICE_ACTIVATED = "device.activated"
    SUSPICIOUS_ACTIVITY = "security.suspicious"

class SecurityLogger:
    """Log security events for monitoring"""

    def __init__(self):
        self.redis = redis_client

    def log_event(
        self,
        event: SecurityEvent,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a security event"""

        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {}
        }

        # Store in Redis list (last 10000 events)
        self.redis.lpush("security_events", json.dumps(event_data))
        self.redis.ltrim("security_events", 0, 9999)

        # Also log to file/database in production
        print(f"SECURITY: {json.dumps(event_data)}")

# Global instance
security_logger = SecurityLogger()
```

Update login endpoint to use logging:

```python
from app.core.security.audit_logger import security_logger, SecurityEvent

@router.post("/login")
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    # ... existing code ...

    if not user or not verify_password(login_data.password, user.password_hash):
        # Log failed attempt
        security_logger.log_event(
            SecurityEvent.LOGIN_FAILED,
            user_id=user.id if user else None,
            ip_address=request.client.host,
            details={"username": login_data.username}
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Log successful login
    security_logger.log_event(
        SecurityEvent.LOGIN_SUCCESS,
        user_id=user.id,
        ip_address=request.client.host
    )

    # ... rest of login logic ...
```

## Priority 4: Frontend Security (React)

### 8. Add XSS Protection in React

Update `web-admin/src/utils/sanitizer.js`:

```javascript
// Install: npm install dompurify
import DOMPurify from 'dompurify';

export const sanitizeHTML = (dirty) => {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target']
  });
};

export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;

  // Remove any HTML tags
  return input.replace(/<[^>]*>?/gm, '');
};

export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const validatePassword = (password) => {
  const errors = [];

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain an uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain a lowercase letter');
  }
  if (!/\d/.test(password)) {
    errors.push('Password must contain a number');
  }
  if (!/[!@#$%^&*]/.test(password)) {
    errors.push('Password must contain a special character');
  }

  return { isValid: errors.length === 0, errors };
};
```

### 9. Secure API Client

Update `web-admin/src/services/api.js`:

```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001';

// Create axios instance with security configurations
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for CSRF
});

// Token refresh logic
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add CSRF token if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refreshToken');

      if (refreshToken) {
        try {
          const response = await api.post('/api/auth/refresh', {
            refresh_token: refreshToken
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('token', access_token);
          localStorage.setItem('refreshToken', refresh_token);

          processQueue(null, access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }
    }

    // Handle rate limiting
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      console.error(`Rate limited. Retry after ${retryAfter} seconds`);
      // Show user-friendly message
      if (window.showToast) {
        window.showToast('Too many requests. Please wait a moment.', 'error');
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### 10. Content Security Policy for React

Add to `web-admin/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <!-- Security Headers -->
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">

    <!-- Content Security Policy -->
    <meta http-equiv="Content-Security-Policy" content="
      default-src 'self';
      script-src 'self' 'unsafe-inline' 'unsafe-eval';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      font-src 'self' data:;
      connect-src 'self' http://192.168.5.12:* ws://192.168.5.12:*;
      frame-ancestors 'none';
    ">

    <title>Digital Signage Admin</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

## Testing Your Security Implementation

### Quick Security Test Script

Create `backend/tests/test_security.py`:

```python
import pytest
from fastapi.testclient import TestClient
import time

def test_rate_limiting(client: TestClient):
    """Test that rate limiting works"""

    # Attempt 10 rapid login attempts
    for i in range(10):
        response = client.post("/api/auth/login", json={
            "username": "test",
            "password": "wrong"
        })

    # Should be rate limited
    assert response.status_code == 429
    assert "too many" in response.json()["detail"].lower()

def test_password_complexity(client: TestClient):
    """Test password requirements"""

    weak_passwords = ["pass", "12345678", "password", "Password1"]

    for pwd in weak_passwords:
        # This should fail validation
        with pytest.raises(ValueError):
            from app.core.security.password import hash_password
            hash_password(pwd)

def test_sql_injection_prevention(client: TestClient):
    """Test SQL injection is blocked"""

    payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--"
    ]

    for payload in payloads:
        response = client.get(f"/api/devices?name={payload}")
        # Should not return SQL error
        assert "sql" not in response.text.lower()
        assert "syntax" not in response.text.lower()

def test_xss_prevention(client: TestClient):
    """Test XSS is prevented"""

    xss_payload = "<script>alert('XSS')</script>"

    response = client.post("/api/devices", json={
        "device_name": xss_payload,
        "ip_address": "192.168.1.1"
    })

    # Should be sanitized or rejected
    if response.status_code == 200:
        assert "<script>" not in response.json()["device_name"]

def test_jwt_security(client: TestClient):
    """Test JWT cannot use 'none' algorithm"""

    import jwt

    # Create token with 'none' algorithm
    token = jwt.encode({"user_id": 1}, "", algorithm="none")

    response = client.get(
        "/api/devices",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
```

Run tests:

```bash
cd backend
pytest tests/test_security.py -v
```

## Monitoring Security Events

### View Security Logs

Create `backend/scripts/monitor_security.py`:

```python
import redis
import json
from datetime import datetime

redis_client = redis.Redis(host='192.168.5.12', port=6379, decode_responses=True)

def monitor_security_events():
    """Monitor security events in real-time"""

    print("Monitoring security events...")
    print("-" * 50)

    while True:
        # Get latest event
        event = redis_client.blpop("security_events", timeout=1)

        if event:
            _, data = event
            event_data = json.loads(data)

            timestamp = event_data['timestamp']
            event_type = event_data['event']
            user_id = event_data.get('user_id', 'N/A')
            ip = event_data.get('ip_address', 'N/A')

            print(f"[{timestamp}] {event_type} - User: {user_id}, IP: {ip}")

            # Alert on suspicious events
            if event_type in ['login.failed', 'rate_limit.exceeded']:
                print(f"⚠️  ALERT: {event_type} from {ip}")

if __name__ == "__main__":
    monitor_security_events()
```

Run monitor:

```bash
python scripts/monitor_security.py
```

## Deployment Checklist

Before deploying to production:

- [ ] Change all default passwords and secrets
- [ ] Generate new JWT secret (32+ characters)
- [ ] Enable HTTPS with valid certificate
- [ ] Set DEBUG=False in production
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up log monitoring
- [ ] Configure database backups
- [ ] Test disaster recovery plan
- [ ] Document security procedures

## Next Steps

1. **Week 1**: Implement Priority 1 fixes (rate limiting, headers, passwords)
2. **Week 2**: Add multi-tenant support if needed
3. **Week 3**: Enhance device security
4. **Week 4**: Set up monitoring and alerts
5. **Week 5**: Conduct security audit and penetration testing

## Support

For security questions or to report vulnerabilities, contact your security team immediately. Do not post security issues in public forums or repositories.