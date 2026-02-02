# Enterprise Security Standards for SaaS Platforms (2024-2025)

> **Version**: 1.0
> **Date**: 2025-01-28
> **Status**: Reference Document
> **Scope**: Authentication, API Security, Data Protection, Compliance, Security Headers, Monitoring

---

## Table of Contents

1. [Authentication Best Practices](#1-authentication-best-practices)
2. [API Security Standards](#2-api-security-standards)
3. [Data Protection Standards](#3-data-protection-standards)
4. [Compliance Requirements](#4-compliance-requirements)
5. [Security Headers & Configurations](#5-security-headers--configurations)
6. [Monitoring & Incident Response](#6-monitoring--incident-response)
7. [Implementation Checklist](#7-implementation-checklist)

---

## 1. Authentication Best Practices

### 1.1 Password Policies (NIST SP 800-63B 2024 Update)

The 2024 NIST guidelines represent a significant shift from complexity-based requirements to practical, evidence-based practices.

#### Requirements

| Requirement | Specification | Rationale |
|-------------|---------------|-----------|
| **Minimum Length** | 8 characters (15+ recommended) | Longer passwords provide exponentially more security |
| **Maximum Length** | At least 64 characters | Support for passphrases |
| **Character Set** | All ASCII + Unicode | No restrictions on character types |
| **Complexity Rules** | NOT required | Predictable patterns (Password123!) are easily cracked |
| **Expiration** | NOT required unless breach suspected | Frequent changes lead to weaker passwords |
| **Password Hints** | NOT allowed | Security vulnerability |
| **Knowledge-Based Auth (KBA)** | NOT allowed | "What was your first pet?" easily guessable |

#### Blocklist Requirements

```python
# MUST check against:
BLOCKED_PASSWORDS = [
    # Common passwords from breaches
    "password", "123456", "qwerty", "admin",
    # Context-specific (company name, product name)
    "companyname", "productname", "companyname2024",
    # User-specific (email prefix, username)
    # Check dynamically
]

# Implementation
def validate_password(password: str, user_context: dict) -> bool:
    # Check common breached passwords (use HaveIBeenPwned API)
    if is_breached_password(password):
        return False

    # Check context-specific patterns
    username = user_context.get("username", "").lower()
    if username and username in password.lower():
        return False

    return len(password) >= 8
```

#### Password Storage

```python
# REQUIRED: Use modern password hashing
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,      # threads
    hash_len=32,        # output length
    salt_len=16         # salt length
)

# Hash
hashed = ph.hash(password)

# Verify
try:
    ph.verify(hashed, password)
except VerifyMismatchError:
    # Invalid password
    pass
```

**Acceptable Algorithms** (in order of preference):
1. Argon2id (recommended)
2. bcrypt (cost factor >= 12)
3. PBKDF2-HMAC-SHA256 (iterations >= 600,000)

#### Account Lockout

| Event | Action |
|-------|--------|
| 10 failed attempts | Temporary lockout (15-30 minutes) |
| 25 failed attempts | Extended lockout (1-4 hours) |
| 50 failed attempts | Manual unlock required + alert |

### 1.2 Multi-Factor Authentication (MFA)

#### MFA Factor Types (Ordered by Security)

| Factor | Security Level | Use Case |
|--------|----------------|----------|
| **Hardware Security Keys (FIDO2)** | Highest | Admin accounts, high-value transactions |
| **Passkeys** | Very High | General users, modern implementations |
| **Authenticator Apps (TOTP)** | High | Standard MFA for all users |
| **Push Notifications** | Medium-High | User-friendly option |
| **SMS/Voice** | Low | Last resort only, vulnerable to SIM swapping |

#### Adaptive MFA Implementation

```python
# Risk-based authentication factors
def calculate_risk_score(login_context: dict) -> float:
    score = 0.0

    # Location risk
    if login_context["is_new_country"]:
        score += 0.4
    elif login_context["is_new_city"]:
        score += 0.2

    # Device risk
    if login_context["is_new_device"]:
        score += 0.3
    elif login_context["device_reputation"] == "suspicious":
        score += 0.5

    # Time risk
    if login_context["unusual_time"]:
        score += 0.1

    # Behavior risk
    if login_context["velocity_anomaly"]:  # Too many attempts
        score += 0.3

    return min(score, 1.0)

def get_required_auth_level(risk_score: float) -> str:
    if risk_score < 0.2:
        return "password_only"  # Low risk, trusted context
    elif risk_score < 0.5:
        return "password_plus_totp"
    elif risk_score < 0.8:
        return "password_plus_hardware_key"
    else:
        return "blocked_manual_review"
```

### 1.3 Passwordless Authentication (Passkeys/FIDO2)

#### Implementation Guidelines

```typescript
// WebAuthn Registration
const publicKeyCredentialCreationOptions: PublicKeyCredentialCreationOptions = {
  challenge: crypto.getRandomValues(new Uint8Array(32)),
  rp: {
    name: "Your SaaS Platform",
    id: "yourdomain.com"
  },
  user: {
    id: Uint8Array.from(userId, c => c.charCodeAt(0)),
    name: userEmail,
    displayName: userName
  },
  pubKeyCredParams: [
    { alg: -7, type: "public-key" },   // ES256 (recommended)
    { alg: -257, type: "public-key" }  // RS256 (fallback)
  ],
  authenticatorSelection: {
    authenticatorAttachment: "platform",  // or "cross-platform" for security keys
    userVerification: "preferred",
    residentKey: "preferred"
  },
  timeout: 60000,
  attestation: "direct"  // "none" for privacy, "direct" for enterprise
};

// Registration
const credential = await navigator.credentials.create({
  publicKey: publicKeyCredentialCreationOptions
});
```

#### Passkey Adoption Metrics (2024-2025)

- 75%+ devices are passkey-ready (Face ID, Windows Hello, etc.)
- Major adopters: Google, Apple, Microsoft, Amazon, GitHub
- NIST SP 800-63-4 formally recognizes passkeys as AAL2

### 1.4 Session Management

#### Session Token Requirements

| Parameter | Recommended Value | Maximum |
|-----------|-------------------|---------|
| **Access Token Lifetime** | 15 minutes | 1 hour |
| **Refresh Token Lifetime** | 7 days | 30 days |
| **Idle Timeout** | 15 minutes | 30 minutes |
| **Absolute Timeout** | 8 hours | 24 hours |

#### JWT Implementation

```python
# JWT Configuration
JWT_CONFIG = {
    "algorithm": "RS256",  # Use RS256 for production (asymmetric)
    "access_token_expire_minutes": 15,
    "refresh_token_expire_days": 7,
    "issuer": "https://yourdomain.com",
    "audience": "https://api.yourdomain.com"
}

# Token structure
{
    "header": {
        "alg": "RS256",
        "typ": "JWT",
        "kid": "key-2024-01"  # Key ID for rotation
    },
    "payload": {
        "sub": "user-uuid",
        "iss": "https://yourdomain.com",
        "aud": "https://api.yourdomain.com",
        "exp": 1706500000,
        "iat": 1706499100,
        "jti": "unique-token-id",  # For revocation
        "tenant_id": "tenant-uuid",
        "permissions": ["read", "write"],
        "session_id": "session-uuid"  # Link to session
    }
}
```

#### Token Storage

| Storage | Access Token | Refresh Token | Notes |
|---------|--------------|---------------|-------|
| **httpOnly Cookie** | Preferred | Required | Prevents XSS |
| **Secure flag** | Required | Required | HTTPS only |
| **SameSite=Strict** | Recommended | Required | CSRF protection |
| **localStorage** | NOT allowed | NOT allowed | XSS vulnerable |

### 1.5 Single Sign-On (SSO)

#### Protocol Selection

| Protocol | Use Case | Notes |
|----------|----------|-------|
| **SAML 2.0** | Enterprise B2B | Industry standard for large orgs |
| **OIDC** | Modern applications | OAuth 2.0 + identity layer |
| **OAuth 2.0** | API authorization | Not for authentication alone |

#### SSO Security Requirements

- Enforce MFA through IdP
- Validate SAML assertions (signature, timestamps, audience)
- Implement Just-In-Time (JIT) provisioning
- Support SCIM for user lifecycle management

---

## 2. API Security Standards

### 2.1 Rate Limiting

#### Rate Limit Tiers

| Endpoint Type | Limit | Window | Burst |
|---------------|-------|--------|-------|
| **Login/Auth** | 5 requests | 1 minute | No burst |
| **Password Reset** | 3 requests | 1 hour | No burst |
| **General API** | 100 requests | 1 minute | 20 requests |
| **Bulk Operations** | 10 requests | 1 minute | No burst |
| **Webhooks** | 1000 requests | 1 minute | 100 requests |

#### Implementation Algorithms

```python
# Token Bucket Algorithm (recommended for most cases)
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_update = now

# Sliding Window (recommended for strict limits)
class SlidingWindow:
    def __init__(self, redis_client, limit: int, window_seconds: int):
        self.redis = redis_client
        self.limit = limit
        self.window = window_seconds

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window)
        _, _, count, _ = pipe.execute()

        return count <= self.limit
```

#### Response Headers

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706500060

{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Too many requests. Please retry after 60 seconds.",
        "retry_after": 60
    }
}
```

### 2.2 API Key Management

#### Key Generation

```python
import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash for storage"""
    # Generate 32-byte random key
    raw_key = secrets.token_urlsafe(32)

    # Prefix for easy identification
    # Format: sk_live_xxxx or sk_test_xxxx
    prefix = "sk_live_" if is_production() else "sk_test_"
    api_key = f"{prefix}{raw_key}"

    # Hash for storage (never store raw key)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, key_hash
```

#### Key Properties

| Property | Requirement |
|----------|-------------|
| **Length** | 32+ characters (256+ bits entropy) |
| **Format** | `{prefix}_{environment}_{random}` |
| **Storage** | Hash only (SHA-256) |
| **Rotation** | Support concurrent keys during rotation |
| **Scopes** | Define allowed operations per key |
| **Expiration** | Optional but recommended (1 year max) |
| **IP Restrictions** | Support allowlist |

#### Key Rotation Process

```
1. Generate new key (both old and new are valid)
2. Update client to use new key
3. Monitor new key usage (24-48 hour overlap)
4. Revoke old key
5. Audit log the rotation
```

### 2.3 Request Signing

#### HMAC Signature for Webhooks

```python
import hmac
import hashlib
import time

def sign_webhook(payload: bytes, secret: str, timestamp: int = None) -> dict:
    """Sign webhook payload with HMAC-SHA256"""
    timestamp = timestamp or int(time.time())

    # Create signature base string
    signature_base = f"{timestamp}.{payload.decode('utf-8')}"

    # Generate HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        signature_base.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return {
        "X-Webhook-Timestamp": str(timestamp),
        "X-Webhook-Signature": f"sha256={signature}"
    }

def verify_webhook(
    payload: bytes,
    signature: str,
    timestamp: str,
    secret: str,
    tolerance_seconds: int = 300
) -> bool:
    """Verify webhook signature"""
    # Check timestamp freshness (prevent replay attacks)
    if abs(int(time.time()) - int(timestamp)) > tolerance_seconds:
        return False

    # Recreate expected signature
    signature_base = f"{timestamp}.{payload.decode('utf-8')}"
    expected = hmac.new(
        secret.encode('utf-8'),
        signature_base.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison (prevent timing attacks)
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### 2.4 Webhook Security

#### Webhook Best Practices

| Requirement | Implementation |
|-------------|----------------|
| **Signature** | HMAC-SHA256 on all webhooks |
| **Timestamp** | Include in signature, validate freshness (5 min) |
| **HTTPS Only** | Reject HTTP endpoints |
| **Retry Logic** | Exponential backoff with jitter |
| **Idempotency** | Include unique event ID |
| **Timeout** | 30 second timeout, async processing |

#### Webhook Payload Structure

```json
{
    "id": "evt_unique_id",
    "type": "payment.completed",
    "created": 1706500000,
    "data": {
        "object": {
            "id": "pay_123",
            "amount": 10000,
            "currency": "USD"
        }
    },
    "api_version": "2024-01",
    "livemode": true
}
```

---

## 3. Data Protection Standards

### 3.1 Encryption Standards

#### Encryption At Rest

| Algorithm | Key Size | Use Case |
|-----------|----------|----------|
| **AES-256-GCM** | 256-bit | Field-level encryption, file encryption |
| **AES-256-CBC** | 256-bit | Legacy systems only |
| **ChaCha20-Poly1305** | 256-bit | Alternative to AES (mobile/IoT) |

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64

class FieldEncryption:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 256 bits (32 bytes)")
        self.aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> dict:
        """Encrypt with AES-256-GCM"""
        nonce = os.urandom(12)  # 96-bit nonce
        ciphertext = self.aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            None  # No additional authenticated data
        )
        return {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "algorithm": "AES-256-GCM"
        }

    def decrypt(self, encrypted: dict) -> str:
        """Decrypt AES-256-GCM"""
        ciphertext = base64.b64decode(encrypted["ciphertext"])
        nonce = base64.b64decode(encrypted["nonce"])
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
```

#### Encryption In Transit

| Protocol | Status | Notes |
|----------|--------|-------|
| **TLS 1.3** | Required | Primary protocol |
| **TLS 1.2** | Acceptable | With strong cipher suites only |
| **TLS 1.1** | Deprecated | Do not use |
| **TLS 1.0** | Deprecated | Do not use |
| **SSL** | Deprecated | Do not use |

### 3.2 Key Management

#### Key Hierarchy

```
Master Key (KEK)                    <- Stored in HSM/KMS
    |
    +-- Data Encryption Key (DEK)   <- Encrypted by KEK
    |       |
    |       +-- Encrypted Data
    |
    +-- Signing Key                 <- For JWT, webhooks
    |
    +-- API Key Encryption Key      <- For stored API keys
```

#### Key Rotation Schedule

| Key Type | Rotation Frequency | Overlap Period |
|----------|-------------------|----------------|
| **Master Key (KEK)** | Annual | N/A (re-encrypt DEKs) |
| **Data Encryption Key** | Annual | Decrypt with old, encrypt with new |
| **JWT Signing Key** | 90 days | 24 hours (support both) |
| **API Keys** | On demand | 24-48 hours |

### 3.3 Data Classification

| Level | Examples | Protection |
|-------|----------|------------|
| **Critical** | Passwords, encryption keys, payment cards | Field encryption, HSM |
| **Sensitive PII** | SSN, national ID, health records | Field encryption, audit log |
| **PII** | Names, emails, phone numbers | TLS, access control |
| **Internal** | Business metrics, logs | Access control |
| **Public** | Marketing content | None required |

### 3.4 Backup Security

```yaml
# Backup security requirements
backup:
  encryption:
    algorithm: "AES-256-GCM"
    key_source: "kms"  # Use cloud KMS

  storage:
    primary: "s3://backups-primary"
    secondary: "s3://backups-secondary"  # Different region
    retention_days: 90

  access:
    principle: "least_privilege"
    audit: true

  testing:
    restore_test_frequency: "monthly"
    verification: "checksum"
```

---

## 4. Compliance Requirements

### 4.1 GDPR (EU)

#### Key Requirements

| Article | Requirement | Implementation |
|---------|-------------|----------------|
| **Art. 15** | Right to Access | Data export API |
| **Art. 17** | Right to Erasure | Data deletion workflow |
| **Art. 20** | Data Portability | JSON/CSV export |
| **Art. 25** | Privacy by Design | Default minimal data collection |
| **Art. 32** | Security Measures | Encryption, access control |
| **Art. 33** | Breach Notification | 72-hour notification process |

#### Implementation

```python
# GDPR Data Subject Rights API
@router.get("/users/{user_id}/gdpr/export")
async def export_user_data(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Article 15 & 20: Data access and portability"""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Cannot access other user's data")

    data = await user_service.export_all_data(user_id)

    # Audit the export
    await audit_service.log(
        action="GDPR_EXPORT",
        user_id=user_id,
        requested_by=current_user.id
    )

    return {
        "export_date": datetime.utcnow().isoformat(),
        "data_categories": data,
        "format": "JSON",
        "retention_note": "This export was generated on request."
    }

@router.delete("/users/{user_id}/gdpr/erase")
async def erase_user_data(
    user_id: str,
    verification: GDPRVerification,
    current_user: User = Depends(get_current_user)
):
    """Article 17: Right to erasure"""
    # Verify identity and request
    await verify_erasure_request(user_id, verification)

    # Soft delete first (30-day grace period)
    await user_service.soft_delete(user_id)

    # Schedule hard delete
    await task_queue.enqueue(
        "gdpr_hard_delete",
        user_id=user_id,
        scheduled_for=datetime.utcnow() + timedelta(days=30)
    )

    return {"status": "scheduled", "deletion_date": "30 days from now"}
```

#### Penalties

- Maximum: 20 million EUR or 4% of global annual revenue
- 2023 example: Meta fined 1.3 billion EUR for data transfers

### 4.2 SOC 2

#### Trust Service Criteria

| Criterion | Focus Area | Key Controls |
|-----------|------------|--------------|
| **Security** | Protection of system | Access control, encryption, firewalls |
| **Availability** | System uptime | Redundancy, disaster recovery |
| **Processing Integrity** | Accurate processing | Validation, error handling |
| **Confidentiality** | Data protection | Encryption, access control |
| **Privacy** | Personal information | Consent, data minimization |

#### Common Controls

```yaml
# SOC 2 Security Controls Checklist
access_control:
  - unique_user_ids: true
  - mfa_required: true
  - least_privilege: true
  - access_review_frequency: "quarterly"
  - offboarding_process: "documented"

encryption:
  - data_at_rest: "AES-256"
  - data_in_transit: "TLS 1.3"
  - key_management: "centralized"

monitoring:
  - security_logging: "all_access"
  - log_retention: "1_year"
  - alert_on_anomaly: true
  - incident_response_plan: "documented"

change_management:
  - code_review_required: true
  - testing_required: true
  - deployment_approval: true
  - rollback_capability: true
```

### 4.3 ISO 27001

#### Key Domains

| Domain | Controls |
|--------|----------|
| **A.5** | Information security policies |
| **A.6** | Organization of information security |
| **A.7** | Human resource security |
| **A.8** | Asset management |
| **A.9** | Access control |
| **A.10** | Cryptography |
| **A.12** | Operations security |
| **A.13** | Communications security |

### 4.4 Data Residency

#### Regional Requirements (2024-2025)

| Region | Requirement | Notes |
|--------|-------------|-------|
| **EU (GDPR)** | Adequate protection for transfers | SCCs or adequacy decision |
| **China (PIPL)** | Local storage for sensitive data | Government approval for transfers |
| **Russia (FZ-152)** | Local storage for citizen data | Data localization required |
| **India (DPDPA)** | Restricted transfers | Evolving requirements |
| **Saudi Arabia (PDPL)** | Local storage provisions | Effective 2024 |
| **Indonesia** | Local data centers | For specific categories |

#### Multi-Region Architecture

```yaml
# Regional deployment strategy
regions:
  us-west:
    purpose: "US customers"
    data_residency: "US"
    services: ["api", "database", "storage"]

  eu-west:
    purpose: "EU customers"
    data_residency: "EU"
    services: ["api", "database", "storage"]
    compliance: ["GDPR"]

  ap-southeast:
    purpose: "APAC customers"
    data_residency: "Singapore"
    services: ["api", "database", "storage"]

# Data routing
routing:
  strategy: "geolocation"
  fallback: "us-west"
  cross_region_replication: false  # For data residency
```

---

## 5. Security Headers & Configurations

### 5.1 HTTP Security Headers

#### Required Headers

```nginx
# Nginx configuration
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

#### Content Security Policy (CSP)

```http
Content-Security-Policy:
    default-src 'self';
    script-src 'self' 'nonce-{random}' https://cdn.example.com;
    style-src 'self' 'nonce-{random}';
    img-src 'self' data: https:;
    font-src 'self' https://fonts.gstatic.com;
    connect-src 'self' https://api.example.com wss://ws.example.com;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';
    upgrade-insecure-requests;
```

**CSP Best Practices:**
- NEVER use `unsafe-inline` or `unsafe-eval`
- Use nonces for inline scripts: `<script nonce="abc123">`
- Start with report-only mode: `Content-Security-Policy-Report-Only`
- Monitor reports and refine policy

### 5.2 Cookie Security

#### Secure Cookie Configuration

```python
# Python/FastAPI cookie settings
response.set_cookie(
    key="session_id",
    value=session_token,
    httponly=True,       # Prevent JavaScript access
    secure=True,         # HTTPS only
    samesite="strict",   # CSRF protection
    max_age=3600,        # 1 hour
    path="/",
    domain=".example.com"
)

# For refresh tokens (more restrictive)
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,
    samesite="strict",
    max_age=604800,      # 7 days
    path="/api/auth/refresh"  # Only sent to refresh endpoint
)
```

#### Cookie Prefixes

| Prefix | Requirements |
|--------|--------------|
| `__Secure-` | Must have `Secure` flag |
| `__Host-` | Must have `Secure`, no `Domain`, `Path=/` |

```http
Set-Cookie: __Host-session=abc123; Secure; HttpOnly; SameSite=Strict; Path=/
```

### 5.3 TLS Configuration

#### Recommended TLS Settings

```nginx
# Nginx TLS configuration
ssl_protocols TLSv1.3 TLSv1.2;
ssl_prefer_server_ciphers off;

# TLS 1.3 ciphers (automatic in TLS 1.3)
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;

# Session settings
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
```

#### Certificate Requirements

| Requirement | Specification |
|-------------|---------------|
| **Key Size** | RSA 2048+ or ECDSA P-256+ |
| **Signature** | SHA-256 or better |
| **Validity** | 398 days maximum |
| **Revocation** | OCSP stapling enabled |

---

## 6. Monitoring & Incident Response

### 6.1 Security Logging

#### Required Log Events

| Category | Events |
|----------|--------|
| **Authentication** | Login success/failure, MFA events, password changes |
| **Authorization** | Permission denied, privilege escalation attempts |
| **Data Access** | PII access, bulk exports, admin operations |
| **Security** | Rate limit hits, blocked IPs, suspicious patterns |
| **System** | Configuration changes, deployment events |

#### Log Format (Structured)

```json
{
    "timestamp": "2024-01-28T10:30:00.000Z",
    "level": "INFO",
    "event_type": "AUTH_LOGIN_SUCCESS",
    "correlation_id": "abc-123-def-456",
    "user_id": "user_uuid",
    "tenant_id": "tenant_uuid",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "geo": {
        "country": "US",
        "city": "San Francisco"
    },
    "metadata": {
        "mfa_method": "totp",
        "session_id": "sess_123"
    }
}
```

#### Log Retention

| Log Type | Retention | Archive |
|----------|-----------|---------|
| **Security/Audit** | 7 years | Required (compliance) |
| **Application** | 90 days | Optional |
| **Debug** | 7 days | Not archived |

### 6.2 SIEM Integration

#### Key Metrics to Monitor

```yaml
# SIEM alert rules
alerts:
  - name: "Brute Force Detection"
    condition: "failed_logins > 10 per user per 5 minutes"
    severity: "HIGH"
    action: "block_ip, notify_security"

  - name: "Impossible Travel"
    condition: "login from two locations > 500km apart within 1 hour"
    severity: "CRITICAL"
    action: "suspend_session, require_verification"

  - name: "Mass Data Export"
    condition: "data_export > 10000 records per user per hour"
    severity: "MEDIUM"
    action: "notify_security, rate_limit"

  - name: "Privilege Escalation"
    condition: "permission_change to admin_role"
    severity: "HIGH"
    action: "require_approval, notify_security"
```

### 6.3 Incident Response (NIST SP 800-61r3)

#### Incident Response Lifecycle

```
1. PREPARATION
   - Establish IR team
   - Define communication channels
   - Create playbooks
   - Conduct training/exercises

2. DETECTION & ANALYSIS
   - Monitor alerts
   - Triage incidents
   - Determine scope and impact
   - Document findings

3. CONTAINMENT, ERADICATION, RECOVERY
   - Contain (isolate affected systems)
   - Eradicate (remove threat)
   - Recover (restore normal operations)
   - Verify integrity

4. POST-INCIDENT ACTIVITY
   - Lessons learned
   - Update playbooks
   - Improve detection
   - Report to stakeholders
```

#### Incident Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **P1 Critical** | Active breach, data exfiltration | 15 minutes | Ransomware, active attacker |
| **P2 High** | Security control bypass | 1 hour | Auth bypass, injection |
| **P3 Medium** | Potential vulnerability | 4 hours | Suspicious activity |
| **P4 Low** | Security improvement | 24 hours | Policy violation |

#### Response Timeline Requirements

| Severity | Detection | Containment | Eradication | Recovery |
|----------|-----------|-------------|-------------|----------|
| **Critical** | Immediate | 1 hour | 4 hours | 24 hours |
| **High** | 1 hour | 4 hours | 24 hours | 72 hours |
| **Medium** | 4 hours | 24 hours | 72 hours | 1 week |
| **Low** | 24 hours | 1 week | 2 weeks | 1 month |

---

## 7. Implementation Checklist

### 7.1 Authentication Checklist

- [ ] Password policy follows NIST guidelines (length, no complexity, no expiration)
- [ ] Password hashing uses Argon2id or bcrypt
- [ ] MFA available for all users
- [ ] MFA required for admin/sensitive operations
- [ ] Adaptive MFA based on risk score
- [ ] Passkey support implemented
- [ ] Session tokens use httpOnly secure cookies
- [ ] JWT uses RS256 with key rotation
- [ ] Account lockout after failed attempts
- [ ] SSO integration (SAML/OIDC) for enterprise

### 7.2 API Security Checklist

- [ ] Rate limiting on all endpoints
- [ ] Stricter limits on auth endpoints
- [ ] API keys use secure generation (32+ chars)
- [ ] API keys stored as hashes only
- [ ] API key rotation supported
- [ ] Webhook signatures use HMAC-SHA256
- [ ] Request replay protection (timestamps)
- [ ] Input validation on all endpoints
- [ ] Output encoding to prevent injection

### 7.3 Data Protection Checklist

- [ ] Data classification defined
- [ ] Field-level encryption for PII (AES-256-GCM)
- [ ] TLS 1.3 for all communications
- [ ] Key management in KMS/HSM
- [ ] Key rotation schedule defined
- [ ] Backup encryption enabled
- [ ] Data masking for unauthorized access
- [ ] Audit logging for PII access

### 7.4 Compliance Checklist

- [ ] GDPR: Data export endpoint
- [ ] GDPR: Data deletion workflow
- [ ] GDPR: Consent management
- [ ] GDPR: Breach notification process
- [ ] SOC 2: Access controls documented
- [ ] SOC 2: Change management process
- [ ] SOC 2: Security monitoring
- [ ] Data residency requirements met
- [ ] Retention policies defined

### 7.5 Security Headers Checklist

- [ ] HSTS enabled (1 year, includeSubDomains, preload)
- [ ] CSP configured (no unsafe-inline)
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy configured
- [ ] Cookies use httpOnly, Secure, SameSite
- [ ] TLS 1.3 preferred, 1.2 minimum
- [ ] Strong cipher suites only

### 7.6 Monitoring Checklist

- [ ] Security events logged (structured format)
- [ ] Log retention meets compliance (7 years audit)
- [ ] SIEM integration configured
- [ ] Alert rules for security events
- [ ] Incident response plan documented
- [ ] IR team and escalation defined
- [ ] Regular security drills/exercises
- [ ] Breach notification process tested

---

## References

### Sources

#### Authentication
- [NIST Password Guidelines 2025](https://drata.com/blog/nist-password-guidelines)
- [MFA Best Practices - Cloud Security Alliance](https://cloudsecurityalliance.org/blog/2025/07/02/mfa-made-easy-8-best-practices-for-seamless-authentication-journeys)
- [SaaS Authentication - Descope](https://www.descope.com/blog/post/saas-auth)
- [Passkeys - FIDO Alliance](https://fidoalliance.org/passkeys/)
- [FIDO2 Enterprise Security - TerraZone](https://terrazone.io/fido2-complete-guide-passwordless-security/)

#### API Security
- [API Rate Limiting - Tyk](https://tyk.io/learning-center/api-rate-limiting/)
- [API Key Security - GitGuardian](https://blog.gitguardian.com/api-key-security-7/)
- [HMAC Webhook Security - Webhooks.fyi](https://webhooks.fyi/security/hmac)
- [Rate Limiting Best Practices - Cloudflare](https://developers.cloudflare.com/waf/rate-limiting-rules/best-practices/)

#### Data Protection
- [AES-256 Encryption - Kiteworks](https://www.kiteworks.com/risk-compliance-glossary/aes-256-encryption/)
- [CISA AES Transition](https://www.cisa.gov/sites/default/files/2024-05/23_0918_fpic_AES-Transition-WhitePaper_Final_508C_24_0513.pdf)
- [Google Cloud Encryption](https://docs.cloud.google.com/docs/security/encryption/default-encryption)

#### Compliance
- [SOC 2 vs ISO 27001 vs GDPR - CloudEagle](https://www.cloudeagle.ai/blogs/iso-27001-vs-soc-2-vs-gdpr-key-differences-explained)
- [SOC 2 Compliance - Imperva](https://www.imperva.com/learn/data-security/soc-2-compliance/)
- [Data Residency for SaaS - Alation](https://www.alation.com/blog/data-residency-by-design-global-compliance/)
- [GDPR and ISO 27001 - Vanta](https://www.vanta.com/collection/iso-27001/how-gdpr-and-iso-27001-work-together)

#### Security Headers
- [HTTP Security Headers - OWASP](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html)
- [TLS Cheat Sheet - OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html)
- [CSP - MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)
- [Cookie Security - MDN](https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/Cookies)

#### Monitoring & Incident Response
- [NIST SP 800-61r3](https://csrc.nist.gov/pubs/sp/800/61/r3/final)
- [SIEM Overview - Splunk](https://www.splunk.com/en_us/blog/learn/siem-security-information-event-management.html)
- [SIEM - IBM](https://www.ibm.com/think/topics/siem)
- [Incident Response Guide - VMRay](https://www.vmray.com/incident-response-steps/)

---

**Related Project Documents:**
- `ATLAS_PANDAWA/docs/CORE-SEC-01-security-auth.md` - Authentication implementation details
- `ATLAS_PANDAWA/docs/CORE-SEC-02-data-protection.md` - Data protection implementation
- `ATLAS_PANDAWA/docs/CORE-SEC-03-authorization-approval-audit.md` - Authorization and audit
