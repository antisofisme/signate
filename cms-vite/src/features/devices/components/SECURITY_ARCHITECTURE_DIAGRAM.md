# Console Interceptor Security Architecture

## Current Architecture (VULNERABLE)

```
┌─────────────────────────────────────────────────────────┐
│ PLAYER DEVICE                                            │
│                                                          │
│  Application Code                                       │
│        │                                                 │
│        ▼                                                 │
│  SharedLogger                                           │
│  ✅ Redacts fields (token, password)                   │
│  ✅ Buffers 100 logs                                    │
│  ❌ No inline secret detection                          │
│  ❌ No log signatures                                   │
│        │                                                 │
│        │ HTTP (plaintext)                               │
│        │ ❌ No authentication                            │
│        ▼                                                 │
└─────────────────────────────────────────────────────────┘
         │
         │ ⚠️ VULNERABLE: Logs sent over HTTP
         │
┌────────▼─────────────────────────────────────────────────┐
│ BACKEND API                                              │
│                                                          │
│  POST /devices/{id}/logs                                │
│  ❌ NO authentication required                          │
│  ❌ NO rate limiting                                     │
│  ✅ SQL injection safe (parameterized queries)          │
│        │                                                 │
│        ▼                                                 │
│  Database Insert                                        │
│  ❌ No XSS sanitization                                 │
│  ❌ No encryption                                        │
│        │                                                 │
└────────┼─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ DATABASE (PostgreSQL)                                    │
│                                                          │
│  device_logs table                                      │
│  ❌ Plaintext storage                                   │
│  ❌ No retention policy (kept forever)                  │
│  ✅ Multi-tenant isolation (organization_id)           │
│        │                                                 │
└────────┼─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ CMS ADMIN                                                │
│                                                          │
│  GET /devices/{id}/logs                                 │
│  ⚠️ Unknown auth status                                │
│  ❌ No XSS sanitization                                 │
│  ✅ Pagination support                                  │
│                                                          │
│  DeviceLogsViewer.tsx                                   │
│  ❌ Renders user input directly (XSS risk)              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**VULNERABILITIES:**
1. 🔴 No authentication → Anyone can inject logs
2. 🔴 No rate limiting → DoS via log flooding
3. 🔴 HTTP transport → MITM attacks
4. 🔴 No XSS sanitization → Stored XSS in CMS
5. 🟠 No encryption at rest → PII exposure in dumps
6. 🟠 No retention policy → GDPR violation

---

## Secure Architecture (AFTER IMPLEMENTATION)

```
┌─────────────────────────────────────────────────────────┐
│ PLAYER DEVICE                                            │
│                                                          │
│  Application Code                                       │
│        │                                                 │
│        ▼                                                 │
│  SharedLogger (Enhanced)                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 1: Data Sanitization                       │  │
│  │ ✅ Redacts known fields (token, password, etc)   │  │
│  │ ✅ Detects inline secrets (regex patterns)       │  │
│  │ ✅ Redacts PII (emails, IPs, phone numbers)      │  │
│  │ ✅ Limits buffer to 100 logs                     │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 2: Log Signing (Integrity)                 │  │
│  │ ✅ HMAC signature with device secret             │  │
│  │ ✅ Timestamp + nonce (replay prevention)         │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 3: Client-Side Rate Limiting               │  │
│  │ ✅ Max 100 logs/hour per device                  │  │
│  │ ✅ Auto-flush errors immediately                 │  │
│  │ ✅ Batch sends every 5 minutes                   │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        │ HTTPS/TLS 1.3 (encrypted)                      │
│        │ + Authorization: Bearer {device_token}         │
│        ▼                                                 │
└─────────────────────────────────────────────────────────┘
         │
         │ ✅ SECURE: Encrypted transport + authentication
         │
┌────────▼─────────────────────────────────────────────────┐
│ API GATEWAY (Nginx)                                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 4: Network Security                         │  │
│  │ ✅ TLS 1.3 termination                           │  │
│  │ ✅ HSTS enforcement (force HTTPS)                │  │
│  │ ✅ Rate limiting (IP-based, 100 req/min)         │  │
│  │ ✅ DDoS protection                               │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ BACKEND API (FastAPI)                                    │
│                                                          │
│  POST /devices/{id}/logs                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 5: API Security                             │  │
│  │ ✅ Device token verification (401 if invalid)    │  │
│  │ ✅ Device ID match check (403 if mismatch)       │  │
│  │ ✅ HMAC signature verification                   │  │
│  │ ✅ Per-device rate limiting (100 logs/hour)      │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 6: Input Validation                         │  │
│  │ ✅ Pydantic DTOs (type checking)                 │  │
│  │ ✅ XSS sanitization (HTML escape)                │  │
│  │ ✅ Length limits (10KB message max)              │  │
│  │ ✅ Null byte removal                             │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 7: Data Processing                          │  │
│  │ ✅ Field encryption (AES-256)                    │  │
│  │   - stack_trace encrypted                         │  │
│  │   - user_agent encrypted                          │  │
│  │ ✅ Organization ID enforcement                   │  │
│  │ ✅ Set expiration (NOW + 30 days)                │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
└────────┼─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ DATABASE (PostgreSQL)                                    │
│                                                          │
│  device_logs table                                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 8: Data at Rest                             │  │
│  │ ✅ Encrypted fields (stack_trace, user_agent)    │  │
│  │ ✅ Sanitized message (HTML escaped)              │  │
│  │ ✅ Multi-tenant isolation (organization_id)      │  │
│  │ ✅ Expiration timestamp (expires_at)             │  │
│  │ ✅ Indexed for efficient cleanup                 │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 9: Data Lifecycle                           │  │
│  │ ✅ Auto-deletion after 30 days (cron job)        │  │
│  │ ✅ GDPR erasure endpoint (on demand)             │  │
│  │ ✅ Audit trail (who deleted, when)               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└────────┬─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│ CMS ADMIN (React)                                        │
│                                                          │
│  GET /devices/{id}/logs                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 10: Admin Authorization                     │  │
│  │ ✅ JWT authentication required                   │  │
│  │ ✅ Organization ID match check                   │  │
│  │ ✅ Role-based access control (RBAC)              │  │
│  │ ✅ Rate limiting (60 req/min)                    │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 11: Backend Decryption                      │  │
│  │ ✅ Decrypt encrypted fields                      │  │
│  │ ✅ Return sanitized data                         │  │
│  └──────────────────────────────────────────────────┘  │
│        │                                                 │
│        ▼                                                 │
│  DeviceLogsViewer.tsx                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ LAYER 12: Frontend Security                       │  │
│  │ ✅ DOMPurify sanitization (defense in depth)     │  │
│  │ ✅ No direct HTML rendering                      │  │
│  │ ✅ CSP headers (prevent inline scripts)          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Security Layers Summary

| Layer | Location | Protection | Status |
|-------|----------|------------|--------|
| **1. Data Sanitization** | Player Client | Redacts secrets & PII | ⚠️ Partial |
| **2. Log Signing** | Player Client | Prevents forgery (HMAC) | ❌ Missing |
| **3. Client Rate Limit** | Player Client | Prevents flooding | ⚠️ Basic only |
| **4. Network Security** | Nginx Gateway | TLS, HSTS, DDoS | ❌ Missing |
| **5. API Security** | Backend Routes | Auth, rate limits | ❌ Missing |
| **6. Input Validation** | Backend Routes | XSS, length limits | ❌ Missing |
| **7. Data Processing** | Backend Logic | Encryption, org filter | ❌ Missing |
| **8. Data at Rest** | Database | Encryption, isolation | ⚠️ Partial |
| **9. Data Lifecycle** | Database Cron | Retention, GDPR erase | ❌ Missing |
| **10. Admin Authorization** | Backend Routes | JWT, RBAC, org filter | ⚠️ Unknown |
| **11. Backend Decryption** | Backend Routes | Field decryption | ❌ Missing |
| **12. Frontend Security** | CMS React | DOMPurify, CSP | ❌ Missing |

**Current:** 2/12 layers complete (17%)
**After Phase 1:** 6/12 layers complete (50%)
**After All Phases:** 12/12 layers complete (100%)

---

## Attack Surface Analysis

### BEFORE Implementation

```
┌─────────────────────────────────────────────────┐
│ ATTACK SURFACE                                   │
│                                                  │
│ ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ Log Injection (No Auth)      │
│ ⬛⬛⬛⬛⬛⬛⬛⬛⬛  DoS via Flooding            │
│ ⬛⬛⬛⬛⬛⬛⬛⬛    Stored XSS                  │
│ ⬛⬛⬛⬛⬛⬛⬛      Cross-Org Access            │
│ ⬛⬛⬛⬛⬛⬛        MITM Attacks               │
│ ⬛⬛⬛⬛⬛          Credential Leakage          │
│ ⬛⬛⬛⬛            Log Forgery                │
│ ⬛⬛⬛              PII Exposure               │
│ ⬛⬛                Database Dump Leaks        │
│ ⬛                  GDPR Violations            │
│                                                  │
│ TOTAL RISK: 🔴 CRITICAL (58 / 100)              │
└─────────────────────────────────────────────────┘
```

### AFTER Phase 1 (Critical Fixes)

```
┌─────────────────────────────────────────────────┐
│ ATTACK SURFACE                                   │
│                                                  │
│ ✅ Log Injection ELIMINATED (auth required)     │
│ ✅ DoS MITIGATED (rate limiting)                │
│ ✅ Stored XSS ELIMINATED (sanitization)         │
│ ✅ Cross-Org Access ELIMINATED (authz)          │
│ ⬛⬛⬛⬛⬛⬛        MITM Attacks               │
│ ⬛⬛⬛⬛⬛          Credential Leakage          │
│ ⬛⬛⬛⬛            Log Forgery                │
│ ⬛⬛⬛              PII Exposure               │
│ ⬛⬛                Database Dump Leaks        │
│ ⬛                  GDPR Violations            │
│                                                  │
│ TOTAL RISK: 🟡 MEDIUM (23 / 100)                │
└─────────────────────────────────────────────────┘
```

### AFTER All Phases (Complete)

```
┌─────────────────────────────────────────────────┐
│ ATTACK SURFACE                                   │
│                                                  │
│ ✅ Log Injection ELIMINATED                     │
│ ✅ DoS ELIMINATED                               │
│ ✅ Stored XSS ELIMINATED                        │
│ ✅ Cross-Org Access ELIMINATED                  │
│ ✅ MITM ELIMINATED (HTTPS enforced)             │
│ ✅ Credential Leakage MITIGATED (enhanced regex)│
│ ✅ Log Forgery ELIMINATED (HMAC signatures)     │
│ ✅ PII Exposure MITIGATED (redaction)           │
│ ✅ Database Dump Leaks MITIGATED (encryption)   │
│ ✅ GDPR Violations ELIMINATED (retention)       │
│                                                  │
│ TOTAL RISK: 🟢 LOW (5 / 100)                    │
└─────────────────────────────────────────────────┘
```

---

## Data Flow Security Checkpoints

### Log Submission Flow

```
Player Device
     │
     ├─ Checkpoint 1: Client Sanitization
     │  ✅ Redact sensitive fields
     │  ✅ Redact inline secrets (regex)
     │  ✅ Limit buffer size (100)
     │
     ├─ Checkpoint 2: Client Authentication
     │  ✅ Attach device_token header
     │  ✅ Check rate limit (100/hour)
     │
     ▼
HTTPS/TLS
     │
     ├─ Checkpoint 3: Network Encryption
     │  ✅ TLS 1.3 encryption
     │  ✅ Certificate validation
     │
     ▼
API Gateway (Nginx)
     │
     ├─ Checkpoint 4: Gateway Filtering
     │  ✅ IP-based rate limit
     │  ✅ DDoS protection
     │  ✅ HSTS enforcement
     │
     ▼
Backend API
     │
     ├─ Checkpoint 5: Authentication
     │  ✅ Verify device_token
     │  ✅ Match device_id
     │
     ├─ Checkpoint 6: Authorization
     │  ✅ Check organization_id
     │  ✅ Verify device exists
     │
     ├─ Checkpoint 7: Rate Limiting
     │  ✅ Per-device quota check
     │  ✅ Reject if exceeded
     │
     ├─ Checkpoint 8: Input Validation
     │  ✅ XSS sanitization
     │  ✅ Length validation
     │  ✅ Type checking (Pydantic)
     │
     ├─ Checkpoint 9: Data Processing
     │  ✅ Encrypt sensitive fields
     │  ✅ Set expiration timestamp
     │
     ▼
Database
     │
     ├─ Checkpoint 10: Storage
     │  ✅ Encrypted stack_trace
     │  ✅ Encrypted user_agent
     │  ✅ Sanitized message
     │
     └─ Checkpoint 11: Lifecycle
        ✅ Auto-delete after 30 days
        ✅ GDPR erasure support
```

### Log Retrieval Flow

```
CMS Admin
     │
     ├─ Checkpoint 1: Admin Authentication
     │  ✅ Verify JWT token
     │  ✅ Check token expiration
     │
     ▼
Backend API
     │
     ├─ Checkpoint 2: Authorization
     │  ✅ Verify organization_id match
     │  ✅ Check RBAC permissions
     │
     ├─ Checkpoint 3: Rate Limiting
     │  ✅ 60 requests/minute
     │
     ├─ Checkpoint 4: Query Validation
     │  ✅ Validate filters
     │  ✅ Limit max results (500)
     │
     ├─ Checkpoint 5: Data Retrieval
     │  ✅ Filter by organization_id
     │  ✅ Decrypt encrypted fields
     │
     ▼
CMS Frontend
     │
     ├─ Checkpoint 6: Output Sanitization
     │  ✅ DOMPurify sanitization
     │  ✅ No direct HTML rendering
     │
     └─ Checkpoint 7: Audit Logging
        ✅ Log who accessed logs
        ✅ Log when accessed
```

---

## Threat Model

### Threat Actors

**1. External Attacker (Internet)**
- **Goal:** DoS, data theft, credential harvesting
- **Attack Vectors:** Log flooding, SQL injection, XSS
- **Mitigation:** Authentication, rate limiting, input validation

**2. Malicious Insider (Org Admin)**
- **Goal:** Access competitor's data, steal logs
- **Attack Vectors:** Cross-org API access
- **Mitigation:** Organization ID filtering, audit logs

**3. Compromised Device**
- **Goal:** Inject fake logs, pollute data
- **Attack Vectors:** Log forgery, spam
- **Mitigation:** HMAC signatures, rate limiting

**4. Regulatory Authority (GDPR)**
- **Goal:** Verify compliance
- **Attack Vectors:** Audit, data subject requests
- **Mitigation:** Retention policy, GDPR erasure endpoint

---

## Compliance Mapping

### GDPR Requirements

```
┌────────────────────────────────────────────────┐
│ GDPR Article 5 - Principles                    │
├────────────────────────────────────────────────┤
│ (a) Lawful, fair, transparent                  │
│     ✅ Documented in privacy policy            │
├────────────────────────────────────────────────┤
│ (b) Purpose limitation                         │
│     ✅ Only used for debugging                 │
├────────────────────────────────────────────────┤
│ (c) Data minimization                          │
│     ✅ Redact PII, only collect necessary data │
├────────────────────────────────────────────────┤
│ (d) Accuracy                                   │
│     ✅ Logs are immutable, accurate            │
├────────────────────────────────────────────────┤
│ (e) Storage limitation                         │
│     ✅ 30-day retention, auto-deletion         │
├────────────────────────────────────────────────┤
│ (f) Integrity and confidentiality              │
│     ✅ Encryption, authentication, authz       │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ GDPR Chapter III - Data Subject Rights         │
├────────────────────────────────────────────────┤
│ Art. 15 - Right to Access                      │
│     ✅ CMS provides log viewing                │
├────────────────────────────────────────────────┤
│ Art. 17 - Right to Erasure                     │
│     ✅ GDPR erasure endpoint                   │
├────────────────────────────────────────────────┤
│ Art. 32 - Security of Processing               │
│     ✅ Encryption, pseudonymization            │
├────────────────────────────────────────────────┤
│ Art. 33 - Breach Notification                  │
│     ✅ Audit logs, monitoring                  │
└────────────────────────────────────────────────┘
```

---

## Quick Reference: Security Controls

### Authentication & Authorization
- ✅ Device token required for log submission
- ✅ JWT required for log viewing
- ✅ Organization ID filtering (multi-tenancy)
- ✅ RBAC for admin actions

### Rate Limiting
- ✅ IP-based: 100 req/min (API gateway)
- ✅ Device-based: 100 logs/hour per device
- ✅ Admin-based: 60 req/min for viewing

### Data Protection
- ✅ Sensitive field redaction (client-side)
- ✅ Inline secret detection (regex patterns)
- ✅ XSS sanitization (backend + frontend)
- ✅ Field encryption (stack_trace, user_agent)

### Compliance
- ✅ 30-day retention policy (auto-deletion)
- ✅ GDPR erasure endpoint (on-demand deletion)
- ✅ Audit trail (who accessed, when)
- ✅ Privacy by design (redaction by default)

---

## Recommended Reading Order

1. **This Document** (5 min) - Visual overview
2. **SECURITY_AUDIT_SUMMARY.md** (10 min) - Executive summary
3. **CONSOLE_INTERCEPTOR_SECURITY_AUDIT.md** (45 min) - Full analysis
4. **SECURITY_IMPLEMENTATION_GUIDE.md** (30 min) - Code implementation

Total: **90 minutes** to full understanding

---

**Version:** 1.0
**Last Updated:** 2025-01-22
**Maintained By:** Security Team
