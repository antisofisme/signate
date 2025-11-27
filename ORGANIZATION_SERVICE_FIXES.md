# Organization Service - Quick Fixes Guide

**Priority Fixes for Production Readiness**

---

## 🔴 CRITICAL FIX #1 - Race Condition in Quota Update

**File**: `/backend-python/services/organization/routes.py`
**Lines**: 532-615
**Severity**: HIGH

### Current Code (PROBLEMATIC)
```python
@router.put("/api/v1/organizations/{org_id:int}/quota", response_model=OrganizationQuotaResponse)
@handle_errors
def update_organization_quota(
    org_id: int,
    request_body: UpdateOrganizationQuotaRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    from services.auth.repositories.models import OrganizationModel

    start_time = time.time()

    # ❌ PROBLEM: No row-level lock - race condition!
    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == org_id
    ).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )

    # Update limits
    if request_body.max_devices is not None:
        org.max_devices = request_body.max_devices

    if request_body.max_users is not None:
        org.max_users = request_body.max_users

    # Update settings JSON
    settings = org.settings or {}

    if request_body.max_content_size_gb is not None:
        settings['max_content_size_gb'] = request_body.max_content_size_gb

    if request_body.max_content_items is not None:
        settings['max_content_items'] = request_body.max_content_items

    if request_body.max_playlists is not None:
        settings['max_playlists'] = request_body.max_playlists

    org.settings = settings
    db.commit()

    # ... rest of the function
```

### Fixed Code (SAFE)
```python
@router.put("/api/v1/organizations/{org_id:int}/quota", response_model=OrganizationQuotaResponse)
@handle_errors
def update_organization_quota(
    org_id: int,
    request_body: UpdateOrganizationQuotaRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    from services.auth.repositories.models import OrganizationModel

    start_time = time.time()

    try:
        # ✅ FIX: Add row-level lock to prevent race conditions
        org = db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).with_for_update().first()  # ← Row-level lock

        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization {org_id} not found"
            )

        # Update limits (now atomic)
        if request_body.max_devices is not None:
            org.max_devices = request_body.max_devices

        if request_body.max_users is not None:
            org.max_users = request_body.max_users

        # Update settings JSON
        settings = org.settings or {}

        if request_body.max_content_size_gb is not None:
            settings['max_content_size_gb'] = request_body.max_content_size_gb

        if request_body.max_content_items is not None:
            settings['max_content_items'] = request_body.max_content_items

        if request_body.max_playlists is not None:
            settings['max_playlists'] = request_body.max_playlists

        org.settings = settings

        # Commit transaction (lock released here)
        db.commit()
        db.refresh(org)

    except Exception as e:
        db.rollback()
        raise

    # Get updated quota status
    quota_response = get_organization_quota_use_case(org_id, db)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="PUT",
        path=f"/organizations/{org_id}/quota",
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="organization.update_quota",
        resource_type="organization",
        resource_id=org_id,
        details={
            "max_devices": request_body.max_devices,
            "max_users": request_body.max_users,
            "max_content_size_gb": request_body.max_content_size_gb,
            "max_content_items": request_body.max_content_items,
            "max_playlists": request_body.max_playlists,
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=org_id
    )

    return quota_response
```

**Impact**: Prevents data loss when two admins update quotas simultaneously

---

## 🟠 HIGH PRIORITY FIX #2 - Add Deprecation Warnings

**File**: `/backend-python/services/organization/domain/quota_service.py`
**Lines**: 255-267, 358-367
**Severity**: MEDIUM

### Add at Top of File
```python
import warnings
from typing import Dict, Optional
from dataclasses import dataclass
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.quota_repository import QuotaRepository
```

### Fix enforce_user_quota() - Line 255
```python
def enforce_user_quota(self, organization_id: int) -> None:
    """
    Enforce user quota - raises exception if limit reached
    Should be called before creating a new user

    .. deprecated:: 1.0
        Use :func:`enforce_user_quota_atomic` instead to prevent race conditions

    Raises:
        ValueError: If quota limit reached
    """
    warnings.warn(
        "enforce_user_quota() is deprecated, use enforce_user_quota_atomic() instead for race-condition safety",
        DeprecationWarning,
        stacklevel=2
    )

    check = self.check_user_quota(organization_id)
    if not check['allowed']:
        raise ValueError(check['message'])
```

### Fix enforce_playlist_quota() - Line 358
```python
def enforce_playlist_quota(self, organization_id: int) -> None:
    """
    Enforce playlist quota - raises exception if limit reached
    Should be called before creating a new playlist

    .. deprecated:: 1.0
        Use :func:`enforce_playlist_quota_atomic` instead to prevent race conditions

    Raises:
        ValueError: If quota limit reached
    """
    warnings.warn(
        "enforce_playlist_quota() is deprecated, use enforce_playlist_quota_atomic() instead for race-condition safety",
        DeprecationWarning,
        stacklevel=2
    )

    check = self.check_playlist_quota(organization_id)
    if not check['allowed']:
        raise ValueError(check['message'])
```

**Impact**: Developers will get warnings when using non-atomic methods

---

## 🟡 MEDIUM PRIORITY FIX #3 - Improve Email Validation

**File**: `/backend-python/services/organization/dtos.py`
**Lines**: 33-37, 56-60
**Severity**: MEDIUM

### Add at Top of File
```python
import re
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
```

### Fix CreateOrganizationRequest Validator (Line 33)
```python
@validator('contact_email')
def validate_email(cls, v):
    if not v:
        return v

    # RFC 5322 compliant regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, v):
        raise ValueError('Invalid email format. Example: user@example.com')

    return v.lower()  # Normalize to lowercase
```

### Fix UpdateOrganizationRequest Validator (Line 56)
```python
@validator('contact_email')
def validate_email(cls, v):
    if not v:
        return v

    # RFC 5322 compliant regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, v):
        raise ValueError('Invalid email format. Example: user@example.com')

    return v.lower()  # Normalize to lowercase
```

**Impact**: Better email validation prevents invalid emails

---

## 🟢 LOW PRIORITY FIX #4 - Standardize Device Counting

**File**: `/backend-python/services/organization/repositories/organization_repo.py`
**Lines**: 112-119
**Severity**: MEDIUM

### Current Code
```python
def count_devices(self, org_id: int) -> int:
    """Count devices in organization"""
    from services.device.repositories.device_repo import DeviceModel

    return self.db.query(func.count(DeviceModel.id)).filter(
        DeviceModel.organization_id == org_id
    ).scalar() or 0
```

### Fixed Code
```python
def count_devices(self, org_id: int, active_only: bool = False) -> int:
    """
    Count devices in organization

    Args:
        org_id: Organization ID
        active_only: Only count devices with status 'active' (default: all)

    Returns:
        Number of devices
    """
    from services.device.repositories.device_repo import DeviceModel

    query = self.db.query(func.count(DeviceModel.id)).filter(
        DeviceModel.organization_id == org_id
    )

    if active_only:
        query = query.filter(DeviceModel.status == 'active')

    return query.scalar() or 0
```

**Impact**: Consistent with user counting behavior

---

## 🟢 LOW PRIORITY FIX #5 - Fix Indonesian Comment

**File**: `/backend-python/services/organization/repositories/organization_repo.py`
**Line**: 85
**Severity**: LOW

### Current Code
```python
# Note: PIN tidak bisa diubah setelah dibuat (security)
```

### Fixed Code
```python
# Note: PIN cannot be changed after creation (security)
```

**Impact**: Code consistency (English codebase)

---

## 🟢 LOW PRIORITY FIX #6 - Improve Query Parameter Description

**File**: `/backend-python/services/organization/routes.py`
**Line**: 116
**Severity**: LOW

### Current Code
```python
active_only: bool = Query(False, description="Show all organizations (set true for active only)")
```

### Fixed Code
```python
active_only: bool = Query(False, description="Filter to active organizations only (default: show all)")
```

**Impact**: Clearer API documentation

---

## Testing Commands

After applying fixes, test with:

```bash
# Test organization quota update (concurrent requests)
# Terminal 1
curl -X PUT "http://192.168.5.12:8001/api/v1/organizations/1/quota" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_devices": 50}'

# Terminal 2 (run simultaneously)
curl -X PUT "http://192.168.5.12:8001/api/v1/organizations/1/quota" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"max_users": 25}'

# Verify final state
curl -X GET "http://192.168.5.12:8001/organizations/1/quota" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Deployment Checklist

- [ ] Apply Critical Fix #1 (Race condition)
- [ ] Apply High Priority Fix #2 (Deprecation warnings)
- [ ] Apply Medium Priority Fix #3 (Email validation)
- [ ] Run manual tests on quota update
- [ ] Check logs for deprecation warnings
- [ ] Verify email validation with test cases
- [ ] Update API documentation if needed
- [ ] Create backup before deployment
- [ ] Deploy to staging first
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Monitor error logs for 24 hours

---

## Files to Commit

```bash
# After making changes
git add backend-python/services/organization/routes.py
git add backend-python/services/organization/domain/quota_service.py
git add backend-python/services/organization/dtos.py
git add backend-python/services/organization/repositories/organization_repo.py

git commit -m "fix(organization): Address critical race condition and improve validation

- Add row-level locking to quota update endpoint (CRITICAL)
- Add deprecation warnings to non-atomic quota methods
- Improve email validation with proper regex
- Standardize device counting with active_only parameter
- Fix Indonesian comment to English
- Improve query parameter description clarity

Resolves race condition that could cause data loss during concurrent
quota updates by multiple admins."

git push origin feature/api-integration
```

---

**Last Updated**: 2025-11-27
**Priority**: Apply fixes in order (Critical → High → Medium → Low)
