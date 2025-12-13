---
description: Security patterns for PROJECT_BESAR (Enterprise)
---

# Security Patterns Reference

## Frontend Security

### CSP Headers
```typescript
// next.config.js
const securityHeaders = [
  { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self'" },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
];
```

### XSS Prevention
```typescript
import DOMPurify from 'isomorphic-dompurify';

// Sanitize HTML
export const sanitizeHtml = (dirty: string) => DOMPurify.sanitize(dirty, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
  ALLOWED_ATTR: ['href'],
});

// Sanitize input
export const sanitizeInput = (input: string) => input
  .replace(/[<>]/g, '')
  .replace(/javascript:/gi, '')
  .trim();
```

### CSRF Protection
```typescript
// API client with CSRF
apiClient.interceptors.request.use((config) => {
  config.headers['X-CSRF-Token'] = Cookies.get('csrf_token');
  return config;
});
```

### Secure Storage Rules
| Data | Storage | Reason |
|------|---------|--------|
| Access token | Memory only | XSS protection |
| Refresh token | httpOnly cookie | Not accessible by JS |
| Theme/lang | localStorage | Non-sensitive |
| PII | NEVER client-side | Compliance |

## Backend Security

### Input Validation
```python
from pydantic import BaseModel, Field, validator

class SecureInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

    @validator('name')
    def no_script_tags(cls, v):
        if '<script' in v.lower():
            raise ValueError('Invalid input')
        return v
```

### SQL Injection Prevention
```python
# WRONG - vulnerable
query = f"SELECT * FROM users WHERE id = {user_id}"

# RIGHT - parameterized
query = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
```

### CSRF Middleware
```python
async def csrf_middleware(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.cookies.get("csrf_token") != request.headers.get("X-CSRF-Token"):
            raise HTTPException(403, "CSRF validation failed")
    return await call_next(request)
```

## Dependency Security

### CI/CD Scanning
```yaml
# Required scans
- pip-audit --strict
- npm audit --audit-level=high
- trivy fs --severity CRITICAL,HIGH
- semgrep --config p/owasp-top-ten
- gitleaks detect
```

### Response Time
| Severity | Patch Within |
|----------|--------------|
| Critical | 24 hours |
| High | 7 days |
| Medium | 30 days |
| Low | 90 days |

## WAF Rules

### Rate Limiting
| Endpoint | Limit |
|----------|-------|
| /auth/login | 5/min |
| /api/* | 100/min |
| /search | 30/min |
| /upload | 10/min |

### Block Patterns
- SQL injection: `UNION SELECT`, `1=1`
- XSS: `<script>`, `javascript:`
- Path traversal: `../`, `..\\`

## Security Checklist
- [ ] JWT RS256 + key rotation
- [ ] Password: argon2/bcrypt
- [ ] MFA enabled
- [ ] tenant_id isolation
- [ ] CSP headers
- [ ] WAF configured
- [ ] Dependency scan passing
- [ ] Pentest completed
