---
description: Flow untuk security audit dan hardening
---

# Flow E4: Security Audit & Hardening

## Kapan Digunakan
- Security audit berkala
- Pre-production checklist
- Post-incident hardening
- Vulnerability remediation

## Severity Response Time
| Severity | Fix Within | Action |
|----------|------------|--------|
| Critical | 24 hours | Hotfix, immediate deploy |
| High | 7 days | Priority sprint |
| Medium | 30 days | Regular sprint |
| Low | 90 days | Quarterly |

---

## Step 1: Frontend Security Audit

### 1.1 CSP & Headers
```bash
# Check security headers
curl -I https://domain.com | grep -E "(Content-Security|X-Frame|X-Content-Type|Referrer)"
```

Required headers:
- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 1.2 XSS Prevention
```bash
# Search dangerous patterns
grep -r "dangerouslySetInnerHTML" src/
grep -r "innerHTML" src/
grep -r "eval(" src/
```

Fix: Use DOMPurify
```typescript
import DOMPurify from 'isomorphic-dompurify';
const safe = DOMPurify.sanitize(dirty);
```

### 1.3 Secure Storage
```bash
# Should NOT find tokens in localStorage
grep -r "localStorage.setItem" src/ | grep -E "(token|user|password)"
```

Rules:
- Access token: Memory only
- Refresh token: httpOnly cookie
- PII: NEVER client-side

### 1.4 CSRF Protection
```typescript
// Verify in API client
config.headers['X-CSRF-Token'] = Cookies.get('csrf_token');
```

---

## Step 2: Backend Security Audit

### 2.1 Authentication
- [ ] JWT algorithm: RS256 (not HS256)
- [ ] Access token expiry: 1 hour
- [ ] Refresh token: httpOnly cookie
- [ ] Password hashing: argon2/bcrypt
- [ ] Account lockout: 5 failed attempts

### 2.2 Authorization
```python
# Every endpoint MUST have:
@router.get("/items/{id}")
@require_auth
@require_permission("items.view")
async def get_item(id: UUID, ctx: AuthContext = Depends()):
    return await service.get(id, tenant_id=ctx.tenant_id)  # WAJIB
```

### 2.3 Input Validation
```bash
# Should NOT find raw request access
grep -r "request.json()" app/
grep -r "request.body" app/
```

All inputs via Pydantic:
```python
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
```

### 2.4 SQL Injection
```bash
# Should NOT find string formatting in queries
grep -r "f\"SELECT\|f\"INSERT\|f\"UPDATE" app/
```

---

## Step 3: Dependency Security

### 3.1 Python
```bash
pip install pip-audit safety
pip-audit --strict
safety check --full-report
```

### 3.2 Node
```bash
npm audit --audit-level=high
npx better-npm-audit audit
```

### 3.3 Container
```bash
trivy image project-besar-api:latest
trivy fs --severity CRITICAL,HIGH .
```

---

## Step 4: SAST Scanning

### 4.1 Semgrep
```bash
semgrep --config p/owasp-top-ten .
semgrep --config p/security-audit .
semgrep --config p/secrets .
```

### 4.2 Secret Scanning
```bash
gitleaks detect --source . --verbose
trufflehog filesystem . --only-verified
```

### 4.3 Python Security
```bash
bandit -r app/ -ll
```

---

## Step 5: WAF & Infrastructure

### 5.1 WAF Rules Check
- [ ] OWASP Core Rule Set enabled
- [ ] Rate limiting active
- [ ] Bot protection enabled
- [ ] Geo restrictions (if needed)

### 5.2 Rate Limits
| Endpoint | Limit |
|----------|-------|
| /auth/login | 5/min |
| /api/* | 100/min |
| /search | 30/min |
| /upload | 10/min |

### 5.3 TLS Check
```bash
testssl --severity HIGH https://api.domain.com
```

---

## Step 6: Penetration Testing

### 6.1 Automated
```bash
# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.domain.com -r zap-report.html

# Nuclei
nuclei -u https://staging.domain.com \
  -t cves/ -t vulnerabilities/ \
  -severity critical,high
```

### 6.2 Manual Testing
- [ ] Authentication bypass
- [ ] Tenant isolation breach
- [ ] Privilege escalation
- [ ] IDOR vulnerabilities
- [ ] File upload bypass

---

## Step 7: Remediation

### Fix Examples

**SQL Injection**
```python
# BAD
query = f"SELECT * FROM users WHERE id = {id}"

# GOOD
select(User).where(User.id == id, User.tenant_id == tenant_id)
```

**XSS**
```typescript
// BAD
<div dangerouslySetInnerHTML={{__html: userInput}} />

// GOOD
<div>{DOMPurify.sanitize(userInput)}</div>
```

**CSRF**
```python
# Add middleware
if request.cookies.get("csrf_token") != request.headers.get("X-CSRF-Token"):
    raise HTTPException(403, "CSRF validation failed")
```

### Verification
```bash
# Re-run all scans after fix
semgrep --config p/security-audit .
pip-audit && npm audit
```

---

## Checklist Summary

### Frontend
- [ ] CSP headers
- [ ] No dangerouslySetInnerHTML
- [ ] No tokens in localStorage
- [ ] CSRF implementation
- [ ] Input sanitization

### Backend
- [ ] JWT RS256 + rotation
- [ ] All endpoints auth + permission
- [ ] tenant_id on ALL queries
- [ ] Pydantic validation
- [ ] No SQL string formatting

### Dependencies
- [ ] pip-audit clean
- [ ] npm audit clean
- [ ] trivy scan passed
- [ ] No critical CVEs

### Infrastructure
- [ ] WAF enabled
- [ ] Rate limiting
- [ ] TLS 1.3
- [ ] Security headers

### Testing
- [ ] SAST passed
- [ ] Secret scan passed
- [ ] Pentest completed
- [ ] All findings fixed
