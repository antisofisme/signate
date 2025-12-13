---
description: Security checklist for PROJECT_BESAR
---

# Security Checklist

## Pre-Production Security Gate

### Authentication ✓
- [ ] JWT algorithm RS256 (not HS256)
- [ ] Key rotation mechanism
- [ ] Access token: 1 hour expiry
- [ ] Refresh token: 7 days, httpOnly cookie
- [ ] Password hashing: argon2 or bcrypt
- [ ] MFA implementation
- [ ] Account lockout: 5 failed attempts
- [ ] Session timeout: 30 min idle

### Authorization ✓
- [ ] RBAC fully implemented
- [ ] Permission check on ALL endpoints
- [ ] tenant_id isolation verified
- [ ] No privilege escalation possible
- [ ] No IDOR vulnerabilities

### Frontend ✓
- [ ] CSP header configured
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] No dangerouslySetInnerHTML
- [ ] Input sanitization (DOMPurify)
- [ ] CSRF token on mutations
- [ ] No tokens in localStorage
- [ ] Secure cookie flags

### Backend ✓
- [ ] All inputs validated (Pydantic)
- [ ] No SQL string formatting
- [ ] Parameterized queries only
- [ ] File upload validation
- [ ] Rate limiting enabled
- [ ] Error messages don't leak info
- [ ] Logging without sensitive data

### Data Protection ✓
- [ ] TLS 1.3 in transit
- [ ] AES-256 at rest
- [ ] PII fields encrypted
- [ ] Backup encryption
- [ ] Key management (vault)

### Dependencies ✓
- [ ] pip-audit: 0 critical/high
- [ ] npm audit: 0 critical/high
- [ ] trivy scan: passed
- [ ] No banned packages
- [ ] All licenses approved

### Infrastructure ✓
- [ ] WAF configured (Cloudflare/AWS)
- [ ] DDoS protection active
- [ ] Rate limiting rules
- [ ] Bot protection
- [ ] Geo restrictions (if needed)
- [ ] Security headers

### Monitoring ✓
- [ ] Security event logging
- [ ] Failed login alerts
- [ ] Rate limit alerts
- [ ] Anomaly detection
- [ ] Audit trail complete

### Testing ✓
- [ ] SAST scan (Semgrep) passed
- [ ] Secret scan (Gitleaks) passed
- [ ] DAST scan (ZAP) passed
- [ ] Penetration test completed
- [ ] All findings remediated

## Quick Commands

```bash
# Frontend
npm audit --audit-level=high
npx eslint --ext .ts,.tsx src/ --rule 'security/*'

# Backend
pip-audit --strict
bandit -r app/ -ll
semgrep --config p/security-audit .

# Secrets
gitleaks detect --source .
trufflehog filesystem .

# Container
trivy fs --severity CRITICAL,HIGH .
trivy image your-image:tag

# Full scan
./scripts/security-scan.sh
```

## Severity Response

| Level | Time | Action |
|-------|------|--------|
| Critical | 24h | Hotfix deploy |
| High | 7 days | Priority fix |
| Medium | 30 days | Sprint backlog |
| Low | 90 days | Quarterly |
