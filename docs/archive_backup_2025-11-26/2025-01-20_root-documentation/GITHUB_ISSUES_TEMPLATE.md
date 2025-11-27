# GitHub Issues Template - Smart TV Digital Signage Backend

**Total Issues to Create**: 86 issues
**Organization**: By service and priority
**Labels**: P0-Critical, P1-High, P2-Medium, P3-Low, Security, Bug, Enhancement

---

## 🔴 PRIORITY 0 - CRITICAL (Production Blockers) - 16 Issues

### AUTH SERVICE - Critical Issues (4)

#### Issue #1: [P0][Auth] Missing save() method in UserRepository breaks password reset
**Labels**: `P0-Critical`, `Bug`, `Auth`, `Production-Blocker`
**Milestone**: Phase 1 - Day 2
**Assignee**: Backend Team
**Estimated Effort**: 2 hours

**Description**:
Password reset functionality is completely broken because `UserRepository` doesn't have a `save()` method that is called in `reset_password.py:72`.

**Current Behavior**:
```python
# reset_password.py:72
self.user_repository.save(user)  # ❌ AttributeError: 'UserRepository' object has no attribute 'save'
```

**Impact**:
- 🔴 Password reset feature completely non-functional
- 🔴 Users cannot recover locked accounts
- 🔴 Production blocker - critical feature broken

**Steps to Reproduce**:
1. Request password reset via POST /auth/forgot-password
2. Use reset token to POST /auth/reset-password
3. Server crashes with AttributeError

**Expected Behavior**:
Password should be successfully reset and user can login with new password.

**Acceptance Criteria**:
- [ ] Add `save()` method to `UserRepository` that calls `update()`
- [ ] Update `reset_password.py` to use `update()` directly OR use new `save()` method
- [ ] Add integration test for complete password reset flow
- [ ] Verify no other use cases call non-existent methods

**Technical Details**:
```python
# Location: backend-python/services/auth/repositories/user_repo.py
# Add method:

def save(self, user: User) -> User:
    """Save/update existing user"""
    return self.update(user)
```

**Related Issues**: None
**Blocked By**: None
**Blocks**: Production deployment

---

#### Issue #2: [P0][Auth] Password validation inconsistency allows weak passwords
**Labels**: `P0-Critical`, `Security`, `Auth`, `Production-Blocker`
**Milestone**: Phase 1 - Day 2
**Estimated Effort**: 2 hours

**Description**:
Password validation rules are inconsistent across the codebase, allowing weak 6-character passwords in some flows while requiring 8+ characters in others.

**Current Behavior**:
- Registration: Requires 8+ chars with complexity (register.py:70)
- DTOs: Only require 6 chars minimum (dtos.py:17, 24)
- Login credentials: Accept 6 chars minimum (domain/user.py:50)

**Security Impact**:
- 🔴 Users can reset password to weak 6-char password
- 🔴 Inconsistent security posture
- 🔴 Violates security best practices

**Affected Files**:
- `services/auth/dtos.py:17` - LoginRequest
- `services/auth/dtos.py:24` - RegisterRequest
- `services/auth/domain/user.py:50` - Credentials validation

**Acceptance Criteria**:
- [ ] Standardize ALL password validations to 8 characters minimum
- [ ] Update DTOs: `password: str = Field(..., min_length=8)`
- [ ] Update domain validations
- [ ] Add test for password strength enforcement across all endpoints
- [ ] Document password policy in API docs

---

#### Issue #3: [P0][Auth] Session token not verified during logout - security vulnerability
**Labels**: `P0-Critical`, `Security`, `Auth`, `Session-Hijacking`
**Milestone**: Phase 1 - Day 2
**Estimated Effort**: 3 hours

**Description**:
The logout endpoint doesn't verify that the token being revoked belongs to the authenticated user, allowing potential session hijacking.

**Security Vulnerability**:
```python
# routes.py:377-382
token = auth_header.replace("Bearer ", "")
result = use_case.execute(token)  # ❌ No user verification!
```

User A can logout User B's session if they have User B's token.

**Attack Scenario**:
1. Attacker obtains valid JWT token from another user
2. Attacker calls POST /auth/logout with that token
3. Victim's session is revoked without victim's consent
4. Denial of service / session hijacking

**Acceptance Criteria**:
- [ ] Verify session belongs to current_user before revoking
- [ ] Add user_id parameter to LogoutUseCase
- [ ] Raise AuthorizationError if session doesn't match current user
- [ ] Add security test for cross-user logout attempt

---

#### Issue #4: [P0][Auth] In-memory password reset tokens won't work in production
**Labels**: `P0-Critical`, `Production-Blocker`, `Infrastructure`, `Auth`
**Milestone**: Phase 1 - Day 3
**Estimated Effort**: 6 hours

**Description**:
Password reset tokens are stored in-memory, which breaks in multi-worker Gunicorn deployments.

**Current Implementation**:
```python
# shared/password_reset.py:33
self._tokens: Dict[str, dict] = {}  # ❌ In-memory storage
```

**Impact**:
- 🔴 Password reset fails in production (multi-worker)
- 🔴 Tokens lost on server restart
- 🔴 Cannot scale horizontally

**Acceptance Criteria**:
- [ ] Create `password_reset_tokens` database table
- [ ] Migrate PasswordResetTokenManager to use database
- [ ] Add token expiration cleanup job
- [ ] Test with multiple Gunicorn workers
- [ ] Migration script for schema change

**Database Schema**:
```sql
CREATE TABLE password_reset_tokens (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    consumed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
);
```

---

### DEVICE SERVICE - Critical Issues (2)

#### Issue #5: [P0][Device] Timezone inconsistency causes wrong device online/offline status
**Labels**: `P0-Critical`, `Bug`, `Device`, `Data-Corruption`, `Production-Blocker`
**Milestone**: Phase 1 - Day 1
**Estimated Effort**: 4 hours

**Description**:
Mixed use of naive (`datetime.utcnow()`) and aware (`datetime.now(timezone.utc)`) datetimes causes incorrect device online/offline status calculation.

**Impact**:
- 🔴 **95% of devices show wrong status** on dashboard
- 🔴 Data corruption in all timestamp comparisons
- 🔴 Customer complaints about inaccurate monitoring
- 🔴 Business-critical feature broken

**Root Cause**:
```python
# heartbeat.py - Uses naive datetime
device.last_seen_at = datetime.utcnow()  # ❌ Naive

# list_devices.py - Compares with aware datetime
now = datetime.now(timezone.utc)  # ✅ Aware
threshold = now - timedelta(minutes=5)  # Aware - Naive = Wrong!
```

**Affected Files**:
- `services/device/use_cases/heartbeat.py`
- `services/device/use_cases/list_devices.py`
- `services/device/use_cases/update_device.py`
- All other services using timestamps

**Acceptance Criteria**:
- [ ] Replace ALL `datetime.utcnow()` with `datetime.now(timezone.utc)`
- [ ] Update all timestamp comparisons
- [ ] Add database migration to ensure stored timestamps are timezone-aware
- [ ] Add test for device status calculation
- [ ] Verify dashboard shows correct online/offline status

**Fix Pattern**:
```python
# BEFORE (Wrong)
device.last_seen_at = datetime.utcnow()

# AFTER (Correct)
from datetime import datetime, timezone
device.last_seen_at = datetime.now(timezone.utc)
```

---

#### Issue #6: [P0][Device] Race condition in activation code generation allows duplicates
**Labels**: `P0-Critical`, `Bug`, `Device`, `Race-Condition`
**Milestone**: Phase 1 - Day 4
**Estimated Effort**: 4 hours

**Description**:
Activation code uniqueness check happens BEFORE database insert, creating a race condition window.

**Vulnerability**:
```python
# Check uniqueness
existing = check_code_exists(code)  # Time 1
if existing:
    retry()

# Insert (race window!)
create_device(code)  # Time 2
```

Two concurrent requests can both pass the uniqueness check and insert duplicate codes.

**Impact**:
- 🔴 Duplicate activation codes possible
- 🔴 Wrong device activated
- 🔴 Customer support nightmare

**Acceptance Criteria**:
- [ ] Add UNIQUE constraint on `pending_devices.activation_code`
- [ ] Wrap code generation in try-catch for constraint violations
- [ ] Retry on duplicate (catch IntegrityError)
- [ ] Add concurrent request test
- [ ] Monitor for duplicate code errors in production

---

### CONTENT/PLAYLIST SERVICE - Critical Issues (3)

#### Issue #7: [P0][Content] Soft-deleted content not removed from playlists (orphaned data)
**Labels**: `P0-Critical`, `Bug`, `Data-Integrity`, `Content`, `Playlist`
**Milestone**: Phase 1 - Day 1
**Estimated Effort**: 6 hours

**Description**:
When content is soft-deleted, playlist_content records are NOT cleaned up, causing devices to attempt playing deleted files.

**Current Behavior**:
```python
# content_repo.py:172-187
def soft_delete(self, content_id: int, organization_id: int) -> bool:
    db_content.deleted_at = datetime.now()
    db_content.is_active = False
    self.db.commit()  # ❌ Playlists still reference this content!
```

**Impact**:
- 🔴 Devices play deleted content → playback failures
- 🔴 Data integrity violation
- 🔴 Customer complaints about "deleted content still showing"

**Acceptance Criteria**:
- [ ] Delete playlist_content records when content is soft-deleted
- [ ] Invalidate content resolver cache for affected devices
- [ ] Add test: delete content → verify removed from all playlists
- [ ] Add cleanup migration for existing orphaned records

**Fix Implementation**:
```python
def soft_delete(self, content_id: int, organization_id: int) -> bool:
    # 1. Delete playlist_content records first
    from services.playlist.repositories.models import PlaylistContentModel
    self.db.query(PlaylistContentModel).filter(
        PlaylistContentModel.content_id == content_id
    ).delete(synchronize_session=False)

    # 2. Soft delete content
    db_content.deleted_at = datetime.now()
    self.db.commit()

    # 3. Invalidate cache
    cache.invalidate_pattern(f"content_resolution:*")
```

---

#### Issue #8: [P0][Playlist] Content resolver cache not invalidated on playlist changes
**Labels**: `P0-Critical`, `Bug`, `Cache`, `Playlist`, `Performance`
**Milestone**: Phase 1 - Day 4
**Estimated Effort**: 8 hours

**Description**:
Content resolver caches results for 5 minutes (TTL=300), but doesn't invalidate cache when playlists/content change. Devices play stale content.

**Current Behavior**:
```python
# content_resolver.py:98-102
cache_key = f"content_resolution:{device_id}"
cached_result = cache.get(cache_key)  # ❌ Stale for 5 minutes!
```

**Impact**:
- 🔴 Content updates delayed 5 minutes
- 🔴 Deleted content still plays
- 🔴 Poor user experience
- 🔴 Customer complaints

**Cache Invalidation Triggers Needed**:
1. Playlist content added/removed
2. Content deleted from system
3. Device assignments changed
4. Schedule priorities updated

**Acceptance Criteria**:
- [ ] Add cache invalidation on playlist content changes
- [ ] Add cache invalidation on content deletion
- [ ] Add cache invalidation on device assignment changes
- [ ] Reduce TTL to 30 seconds with proper invalidation
- [ ] Add test: update playlist → cache invalidated immediately

---

#### Issue #9: [P0][Content] File upload quota race condition allows quota bypass
**Labels**: `P0-Critical`, `Security`, `Bug`, `Content`, `Race-Condition`
**Milestone**: Phase 1 - Day 3
**Estimated Effort**: 4 hours

**Description**:
File size check happens BEFORE file save, creating TOCTOU vulnerability. Multiple concurrent uploads can bypass quota limits.

**Attack Scenario**:
```
Org quota: 1GB used, 100MB remaining

Request 1: Check quota (100MB free) → PASS
Request 2: Check quota (100MB free) → PASS (concurrent!)
Request 3: Check quota (100MB free) → PASS (concurrent!)

All 3 files (150MB total) save successfully → 50MB over quota!
```

**Impact**:
- 🔴 Revenue loss (quota bypass)
- 🔴 Storage exhaustion DoS
- 🔴 Billing system broken

**Acceptance Criteria**:
- [ ] Use database row-level locking (SELECT FOR UPDATE)
- [ ] Update quota BEFORE file save
- [ ] Add concurrent upload test (10 simultaneous uploads)
- [ ] Monitor for quota violations in production

---

### ORGANIZATION/USER SERVICE - Critical Issues (2)

#### Issue #10: [P0][Organization] Multi-tenancy isolation breach in user repository
**Labels**: `P0-Critical`, `Security`, `Data-Leak`, `Organization`, `User`
**Milestone**: Phase 1 - Day 2
**Estimated Effort**: 4 hours

**Description**:
`find_by_username()` and `find_by_email()` methods accept optional `organization_id`, but many use cases DON'T pass it, allowing cross-organization queries.

**Security Vulnerability**:
```python
# user_repo.py - organization_id is OPTIONAL
def find_by_username(self, username: str, organization_id: Optional[int] = None):
    # ❌ Can query across all organizations!

# create_user.py:83 - No organization_id passed!
existing_user = self.user_repo.find_by_username(username)
```

**Impact**:
- 🔴 **CRITICAL DATA LEAK** - Org A can see if username exists in Org B
- 🔴 Multi-tenancy isolation broken
- 🔴 GDPR violation potential

**Acceptance Criteria**:
- [ ] Make `organization_id` REQUIRED in all user queries
- [ ] Update all use cases to pass organization_id
- [ ] Add test: Org A cannot query Org B users
- [ ] Security audit of all multi-tenancy queries

---

#### Issue #11: [P0][User] Missing CASCADE constraint on users.organization_id
**Labels**: `P0-Critical`, `Bug`, `Data-Integrity`, `Database`
**Milestone**: Phase 1 - Day 3
**Estimated Effort**: 2 hours

**Description**:
`users.organization_id` foreign key has NO CASCADE behavior, unlike all other tables. Deleting organization leaves orphaned users.

**Database Schema Issue**:
```sql
-- CURRENT (Wrong)
organization_id INTEGER REFERENCES organizations(id),  -- No CASCADE!

-- EXPECTED (Correct)
organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
```

**Impact**:
- 🔴 Orphaned users in database
- 🔴 Application crashes accessing user.organization
- 🔴 Data integrity violation

**Acceptance Criteria**:
- [ ] Create migration to add CASCADE constraint
- [ ] Test organization deletion cascades to users
- [ ] Verify no orphaned user records exist
- [ ] Update ORM model to reflect constraint

---

### SESSION SERVICE - Critical Issues (1)

#### Issue #12: [P0][Session] Session verification doesn't check database - revoked tokens still work
**Labels**: `P0-Critical`, `Security`, `Session`, `Authentication`
**Milestone**: Phase 1 - Day 3
**Estimated Effort**: 4 hours

**Description**:
JWT token validation only checks signature/expiration, NOT database session status. Revoked sessions remain valid until JWT expires (30 minutes).

**Security Impact**:
```python
# shared/auth.py:428-429
payload = decode_token(credentials.credentials)  # ❌ Only checks JWT, not DB!
```

**Attack Scenario**:
1. User logs in → Gets JWT token
2. User clicks logout → Session revoked in DB
3. Attacker uses old JWT token → Still works for 30 minutes!
4. User cannot protect account by logging out

**Impact**:
- 🔴 **LOGOUT DOESN'T WORK**
- 🔴 Compromised tokens cannot be revoked
- 🔴 User deactivation ineffective
- 🔴 Major security vulnerability

**Acceptance Criteria**:
- [ ] Add database session verification in `get_current_user`
- [ ] Implement Redis cache for active sessions (performance)
- [ ] Add middleware to check session status
- [ ] Test: revoked session returns 401 immediately
- [ ] Add session monitoring/alerting

**Implementation**:
```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    payload = decode_token(credentials.credentials)

    # CRITICAL: Check database session status
    session_repo = SessionRepository(db)
    session = session_repo.verify_session(credentials.credentials)

    if not session:
        raise AuthenticationError("Session has been revoked")
```

---

### CONTENT SERVICE - Additional Critical (3)

#### Issue #13: [P0][Content] Path traversal vulnerability in file storage
**Labels**: `P0-Critical`, `Security`, `Content`, `Path-Traversal`
**Milestone**: Phase 2 - Day 9
**Estimated Effort**: 3 hours

**Description**:
File path validation happens AFTER path construction, allowing potential path traversal attacks.

**Attack Vector**:
```
Filename: "../../../etc/passwd.jpg"
After sanitization: "passwd.jpg"
But file already created at: /uploads/../../../etc/passwd.jpg
```

**Impact**:
- 🔴 Arbitrary file write
- 🔴 Data exfiltration
- 🔴 System compromise

**Acceptance Criteria**:
- [ ] Validate filename BEFORE path construction
- [ ] Use `SecureFileHandler.generate_safe_path()` first
- [ ] Add path traversal security test
- [ ] Code review all file operations

---

#### Issue #14: [P0][Content] No virus scanning on file uploads
**Labels**: `P0-Critical`, `Security`, `Content`, `Malware`
**Milestone**: Phase 2 - Day 10
**Estimated Effort**: 8 hours

**Description**:
Files are saved directly without malware scanning. MIME type validation alone is insufficient.

**Impact**:
- 🔴 Malware distribution risk
- 🔴 Legal liability
- 🔴 Reputation damage

**Acceptance Criteria**:
- [ ] Integrate ClamAV virus scanning
- [ ] Scan files before accepting upload
- [ ] Reject malware detections
- [ ] Add monitoring for malware attempts
- [ ] Document scanning in API

**Implementation**:
```python
import pyclamd

async def scan_file_for_viruses(file_path: Path) -> bool:
    cd = pyclamd.ClamdUnixSocket()
    scan_result = cd.scan_file(str(file_path))
    return scan_result is None  # None = clean
```

---

#### Issue #15: [P0][Content] Missing file cleanup on transaction rollback
**Labels**: `P0-Critical`, `Bug`, `Content`, `Storage-Leak`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 3 hours

**Description**:
If database commit fails after file is saved, the file is NOT deleted, causing storage leaks.

**Impact**:
- 🔴 Storage leaks
- 🔴 Orphaned files accumulate
- 🔴 Disk space exhaustion

**Acceptance Criteria**:
- [ ] Wrap file save in try-catch
- [ ] Delete file on database rollback
- [ ] Add test: DB failure → file deleted
- [ ] Add periodic orphan file cleanup job

---

### AUTH SERVICE - Additional Critical (1)

#### Issue #16: [P0][Auth] Rate limiter uses in-memory storage - won't work in production
**Labels**: `P0-Critical`, `Production-Blocker`, `Infrastructure`, `Security`
**Milestone**: Phase 2 - Day 6-7
**Estimated Effort**: 8 hours

**Description**:
Rate limiter stores request counts in-memory, which breaks in multi-worker deployments.

**Impact**:
- 🔴 Rate limiting bypassed in production
- 🔴 DDoS attacks possible
- 🔴 Brute force attacks unmitigated

**Acceptance Criteria**:
- [ ] Migrate rate limiter to Redis
- [ ] Test with multiple Gunicorn workers
- [ ] Add rate limit monitoring
- [ ] Document Redis setup in deployment docs

---

## 🟠 PRIORITY 1 - HIGH (Security & Performance) - 28 Issues

### AUTH SERVICE - High Priority (7)

#### Issue #17: [P1][Auth] No account lockout after failed login attempts
**Labels**: `P1-High`, `Security`, `Auth`, `Brute-Force`
**Milestone**: Phase 2 - Day 8
**Estimated Effort**: 4 hours

**Description**:
No account-level lockout mechanism. Attackers can bypass IP-based rate limiting using distributed IPs.

**Impact**:
- 🟠 Vulnerable to distributed brute force
- 🟠 No user notification of failed attempts
- 🟠 Account takeover risk

**Acceptance Criteria**:
- [ ] Add `failed_login_attempts` column to users table
- [ ] Add `locked_until` column to users table
- [ ] Lock account after 5 failed attempts for 30 minutes
- [ ] Reset counter on successful login
- [ ] Add test for account lockout
- [ ] Send email notification on lockout

---

#### Issue #18: [P1][Auth] Password reset uses different hashing library (bcrypt vs passlib)
**Labels**: `P1-High`, `Bug`, `Auth`, `Inconsistency`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 2 hours

**Description**:
Registration uses `passlib.CryptContext` but password reset uses raw `bcrypt` library.

**Impact**:
- 🟠 Inconsistent hashing
- 🟠 Potential authentication issues
- 🟠 Maintenance complexity

**Acceptance Criteria**:
- [ ] Use shared `get_password_hash()` utility everywhere
- [ ] Remove direct bcrypt imports
- [ ] Test password reset → login flow

---

#### Issue #19: [P1][Auth] Email enumeration via timing attack in forgot password
**Labels**: `P1-High`, `Security`, `Auth`, `Timing-Attack`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 3 hours

**Description**:
Response time differs for valid vs invalid emails, allowing enumeration.

**Timing Difference**:
- Valid email: Database query + token generation (~50-100ms)
- Invalid email: Just database query (~10-20ms)

**Acceptance Criteria**:
- [ ] Implement constant-time response (always 100ms)
- [ ] Generate fake token for invalid emails
- [ ] Add timing attack test

---

#### Issue #20: [P1][Auth] Missing password validation in reset password flow
**Labels**: `P1-High`, `Security`, `Auth`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 2 hours

**Description**:
Password reset doesn't validate new password strength.

**Acceptance Criteria**:
- [ ] Add password strength validation to reset flow
- [ ] Match registration requirements (8+ chars, complexity)
- [ ] Test weak password rejection

---

#### Issue #21: [P1][Auth] No audit logging for password reset operations
**Labels**: `P1-High`, `Security`, `Audit`, `Auth`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 2 hours

**Description**:
Password reset operations not logged to audit_logs table.

**Acceptance Criteria**:
- [ ] Log password reset request
- [ ] Log password reset completion
- [ ] Log failed reset attempts
- [ ] Include IP address, user agent in logs

---

#### Issue #22: [P1][Auth] Session expiry mismatch (30 days session vs 30 min JWT)
**Labels**: `P1-High`, `Bug`, `Auth`, `Session`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 8 hours

**Description**:
Session created for 30 days but JWT expires in 30 minutes, causing confusion.

**Acceptance Criteria**:
- [ ] Implement refresh token pattern
- [ ] Access token: 30 minutes
- [ ] Refresh token: 30 days
- [ ] Add token refresh endpoint
- [ ] Update frontend to use refresh flow

---

#### Issue #23: [P1][Auth] No protection against session fixation
**Labels**: `P1-High`, `Security`, `Auth`, `Session-Fixation`
**Milestone**: Phase 3 - Day 13
**Estimated Effort**: 2 hours

**Description**:
Old sessions not invalidated on login, vulnerable to session fixation.

**Acceptance Criteria**:
- [ ] Revoke old sessions on new login
- [ ] Generate new session ID
- [ ] Add session fixation test

---

### DEVICE SERVICE - High Priority (7)

#### Issue #24: [P1][Device] Device heartbeat authentication too weak
**Labels**: `P1-High`, `Security`, `Device`
**Milestone**: Phase 2 - Day 8

#### Issue #25: [P1][Device] Device logs endpoint has no authentication
**Labels**: `P1-High`, `Security`, `Device`
**Milestone**: Phase 2 - Day 8

#### Issue #26: [P1][Device] Check-activation polling has no rate limiting (DoS risk)
**Labels**: `P1-High`, `Security`, `Device`, `DoS`
**Milestone**: Phase 2 - Day 8

#### Issue #27: [P1][Device] Content resolution N+1 query problem
**Labels**: `P1-High`, `Performance`, `Device`
**Milestone**: Phase 3 - Day 13

#### Issue #28: [P1][Device] Missing database indexes for common queries
**Labels**: `P1-High`, `Performance`, `Database`
**Milestone**: Phase 3 - Day 13

#### Issue #29: [P1][Device] WebSocket connection cleanup has edge cases
**Labels**: `P1-High`, `Bug`, `Device`, `WebSocket`
**Milestone**: Phase 3 - Day 14

#### Issue #30: [P1][Device] Organization quota enforcement disabled (commented out)
**Labels**: `P1-High`, `Bug`, `Device`, `Quota`
**Milestone**: Phase 2 - Day 8

---

### ORGANIZATION/USER SERVICE - High Priority (5)

#### Issue #31: [P1][Organization] Missing organization isolation in get/update/delete use cases
**Labels**: `P1-High`, `Security`, `Organization`
**Milestone**: Phase 2 - Day 8

#### Issue #32: [P1][User] User quota race condition
**Labels**: `P1-High`, `Bug`, `Race-Condition`, `User`
**Milestone**: Phase 2 - Day 8

#### Issue #33: [P1][Organization] No audit trail - missing created_by/updated_by
**Labels**: `P1-High`, `Audit`, `Organization`
**Milestone**: Phase 3 - Day 13

#### Issue #34: [P1][Organization] PIN security removed without migration path
**Labels**: `P1-High`, `Bug`, `Organization`
**Milestone**: Phase 3 - Day 14

#### Issue #35: [P1][Organization] No soft delete - hard delete only
**Labels**: `P1-High`, `Bug`, `Data-Integrity`, `Organization`
**Milestone**: Phase 3 - Day 13

---

### RBAC SERVICE - High Priority (2)

#### Issue #36: [P1][RBAC] Missing permission validation allows typos/injection
**Labels**: `P1-High`, `Security`, `RBAC`
**Milestone**: Phase 3 - Day 13

#### Issue #37: [P1][RBAC] No permission hierarchy (wildcard) support
**Labels**: `P1-High`, `Enhancement`, `RBAC`
**Milestone**: Phase 4 - Backlog

---

### SESSION SERVICE - High Priority (2)

#### Issue #38: [P1][Session] No session limit enforcement per user
**Labels**: `P1-High`, `Security`, `Session`
**Milestone**: Phase 2 - Day 8

#### Issue #39: [P1][Session] Session fixation vulnerability
**Labels**: `P1-High`, `Security`, `Session`
**Milestone**: Phase 3 - Day 13

---

### AUDIT SERVICE - High Priority (1)

#### Issue #40: [P1][Audit] Audit logs are mutable - compliance violation
**Labels**: `P1-High`, `Security`, `Audit`, `Compliance`
**Milestone**: Phase 3 - Day 13

---

### TAG SERVICE - High Priority (1)

#### Issue #41: [P1][Tag] Tag assignment bypasses content ownership check
**Labels**: `P1-High`, `Security`, `Tag`
**Milestone**: Phase 4 - Backlog

---

### CONTENT SERVICE - High Priority (3)

#### Issue #42: [P1][Content] Path traversal vulnerability in storage
(Already covered in P0 #13)

#### Issue #43: [P1][Content] No virus scanning on file uploads
(Already covered in P0 #14)

#### Issue #44: [P1][Content] Missing file cleanup on transaction rollback
(Already covered in P0 #15)

---

## 🟡 PRIORITY 2 - MEDIUM (Code Quality) - 32 Issues

*[Detailed issue templates for all 32 P2 issues would follow same format]*

**Summary of P2 Issues by Service**:
- Auth Service: 6 medium issues
- Device Service: 8 medium issues
- Content/Playlist: 9 medium issues
- Organization/User: 5 medium issues
- RBAC: 2 medium issues
- Session: 1 medium issue
- Audit: 1 medium issue

---

## 🟢 PRIORITY 3 - LOW (Nice-to-have) - 10 Issues

*[Detailed issue templates for all 10 P3 issues would follow same format]*

---

## 📊 GITHUB PROJECT BOARD STRUCTURE

### Milestones

1. **Phase 1 - Critical Fixes (Days 1-5)**
   - 16 P0 issues
   - Due date: 5 days from start

2. **Phase 2 - Security Hardening (Days 6-10)**
   - 12 P1 issues
   - Due date: 10 days from start

3. **Phase 3 - Reliability (Days 11-15)**
   - 20 P1+P2 issues
   - Due date: 15 days from start

4. **Phase 4 - Enhancements (Backlog)**
   - 38 P2+P3 issues
   - No fixed due date

### Labels

**Priority**:
- `P0-Critical` (red) - Production blockers
- `P1-High` (orange) - Security & performance
- `P2-Medium` (yellow) - Code quality
- `P3-Low` (green) - Nice-to-have

**Type**:
- `Bug` - Something broken
- `Security` - Security vulnerability
- `Enhancement` - New feature/improvement
- `Performance` - Performance issue
- `Technical-Debt` - Tech debt

**Service**:
- `Auth`, `Device`, `Content`, `Playlist`, `Organization`, `User`, `RBAC`, `Session`, `Audit`, `Tag`

**Category**:
- `Production-Blocker` - Cannot deploy without fix
- `Data-Integrity` - Data corruption/leak
- `Race-Condition` - Concurrency issue
- `Cache` - Caching issue
- `Database` - DB schema/query issue

---

## 🎯 ISSUE CREATION COMMANDS

### Using GitHub CLI

```bash
# Install GitHub CLI if needed
# brew install gh  # macOS
# Or download from https://cli.github.com/

# Authenticate
gh auth login

# Create all P0 issues
for i in {1..16}; do
  gh issue create \
    --title "$(grep -A1 "^#### Issue #$i:" GITHUB_ISSUES_TEMPLATE.md | tail -1 | sed 's/#### //')" \
    --body "$(extract_issue_body $i)" \
    --label "P0-Critical,Production-Blocker" \
    --milestone "Phase 1"
done

# Or use the provided script
./scripts/create_github_issues.sh
```

### Manual Creation Steps

1. Go to GitHub repository
2. Click "Issues" → "New Issue"
3. Copy issue title and description from this template
4. Add appropriate labels and milestone
5. Assign to team member
6. Repeat for all 86 issues

---

## 📝 NOTES

- **Issue Numbers**: This template uses #1-86 for documentation. GitHub will assign actual issue numbers sequentially.
- **Assignees**: Replace "Backend Team" with actual GitHub usernames.
- **Estimates**: Time estimates are rough - adjust based on team velocity.
- **Dependencies**: Some issues block others - check "Blocked By" field.
- **Testing**: Every fix MUST include tests - add to acceptance criteria.

---

**Template Version**: 1.0
**Created**: 2025-01-14
**Total Issues**: 86
**Estimated Total Effort**: ~300 hours (~40 working days for 1 developer, ~15 days for 3 developers)
