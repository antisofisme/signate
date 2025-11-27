# Audit Logging Action Items - Other Services

## Status Summary

| Service | Audit Coverage | Database Persistence | Priority |
|---------|---------------|---------------------|----------|
| Playlist | ✅ 100% (10/10) | ✅ Fixed | Complete |
| Content | ✅ 100% (5/5) | ✅ Working | Complete |
| Organization | ✅ 100% (4/4) | ✅ Working | Complete |
| **Menu** | ⚠️ ~80% | ❌ **Console only** | **High** |
| **Schedule** | ⚠️ ~70% | ❌ **Console only** | **High** |
| Device | 🔍 Not audited | 🔍 Not audited | Medium |
| Auth | 🔍 Not audited | 🔍 Not audited | Medium |

---

## Action Items

### 1. Fix Menu Service Audit Logging (High Priority)

**Issue**: Audit logger not persisting to database

**File**: `/backend-python/services/menu/routes.py`

**Current Code** (line ~73):
```python
def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()
```

**Fix Required**:
```python
def get_audit_log_repository(db: Session = Depends(get_db)):
    """Get audit log repository instance"""
    from services.audit.repositories.audit_log_repo import AuditLogRepository
    return AuditLogRepository(db)


def get_create_audit_log_use_case(audit_repo = Depends(get_audit_log_repository)):
    """Get create audit log use case"""
    from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase
    return CreateAuditLogUseCase(audit_repo)


def get_audit_logger(create_audit_use_case = Depends(get_create_audit_log_use_case)) -> AuditLogger:
    """Get audit logger with database persistence"""
    return AuditLogger(create_audit_log_use_case=create_audit_use_case)
```

**Expected Actions to Log**:
- menu.create
- menu.update
- menu.delete
- menu.add_item
- menu.remove_item
- menu.reorder_items
- menu.import (Excel/CSV)

**Estimate**: 15 minutes

---

### 2. Fix Schedule Service Audit Logging (High Priority)

**Issue**: Audit logger not persisting to database

**File**: `/backend-python/services/schedule/routes.py`

**Current Code** (line ~75):
```python
def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    return AuditLogger()
```

**Fix Required**: Same as Menu service (see above)

**Expected Actions to Log**:
- schedule.create
- schedule.update
- schedule.delete
- schedule.activate
- schedule.deactivate

**Estimate**: 15 minutes

---

### 3. Add Audit Logging to Device Service (Medium Priority)

**Issue**: No audit logging implemented

**File**: `/backend-python/services/device/routes.py`

**Actions to Log**:
- device.register (new device activation)
- device.update (name, tags, location)
- device.delete
- device.assign_tag
- device.unassign_tag
- device.send_command (reboot, clear_cache, etc.)

**Estimate**: 30 minutes

---

### 4. Add Audit Logging to Auth Service (Medium Priority)

**Issue**: No audit logging for critical auth operations

**File**: `/backend-python/services/auth/routes.py`

**Actions to Log**:
- auth.login (successful)
- auth.login.failed (security event)
- auth.logout
- auth.password_change
- auth.password_reset
- auth.token_refresh
- user.create
- user.update
- user.delete

**Security Note**: Login failures are critical security events and MUST be logged.

**Estimate**: 45 minutes

---

## Pattern to Follow

### Step 1: Add Dependencies (All Services)

```python
def get_audit_log_repository(db: Session = Depends(get_db)):
    """Get audit log repository instance"""
    from services.audit.repositories.audit_log_repo import AuditLogRepository
    return AuditLogRepository(db)


def get_create_audit_log_use_case(audit_repo = Depends(get_audit_log_repository)):
    """Get create audit log use case"""
    from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase
    return CreateAuditLogUseCase(audit_repo)


def get_audit_logger(create_audit_use_case = Depends(get_create_audit_log_use_case)) -> AuditLogger:
    """Get audit logger with database persistence"""
    return AuditLogger(create_audit_log_use_case=create_audit_use_case)
```

### Step 2: Add to Write Endpoints

```python
@router.post("/resource", status_code=status.HTTP_201_CREATED)
def create_resource(
    request_body: ResourceCreateRequest,
    use_case: CreateResourceUseCase = Depends(get_create_resource_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger),  # Add this
):
    """Create new resource"""
    try:
        resource = use_case.execute(...)
        
        # Add audit logging AFTER successful operation
        audit_logger.log_action(
            user_id=current_user.id,
            action="resource.create",  # Use consistent naming: service.action
            resource_type="resource",
            resource_id=resource.id,
            details={"key": "value"},  # Relevant metadata
            organization_id=current_user.organization_id,
        )
        
        return success_response(data=resource.to_dict())
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

### Step 3: Verify Database Persistence

```bash
# After making changes, test that logs are written to DB
docker exec signage-postgres psql -U signage_user -d signage_db -c \
  "SELECT user_id, action, resource_type, resource_id, recorded_at 
   FROM audit_logs 
   WHERE action LIKE 'service.%' 
   ORDER BY recorded_at DESC 
   LIMIT 10;"
```

---

## Testing Checklist

For each service after fixing:

- [ ] Create operation logged
- [ ] Update operation logged
- [ ] Delete operation logged
- [ ] Bulk operations logged
- [ ] Assignment operations logged
- [ ] Database entry created in `audit_logs` table
- [ ] Multi-tenant isolation (organization_id filtered)
- [ ] Details JSON contains relevant data
- [ ] No sensitive data in details (passwords, tokens)

---

## Compliance Requirements

All services MUST log write operations to meet:

- **SOC 2 Type II** - CC6.3: Audit logging required
- **GDPR Article 30** - Records of processing activities
- **HIPAA §164.312(b)** - Audit controls
- **ISO 27001 A.12.4.1** - Event logging

**Critical Actions** (MUST be logged):
1. Authentication events (login, logout, failed login)
2. Authorization changes (role/permission changes)
3. Data access (especially sensitive data)
4. Data modifications (create, update, delete)
5. Configuration changes
6. Administrative actions

---

## Priority Order

1. **High**: Menu, Schedule (already have audit calls, just need DB persistence)
2. **Medium**: Device (critical for device management)
3. **Medium**: Auth (critical for security)
4. **Low**: Read-only services (analytics, reporting)

---

## Estimated Time

- Menu: 15 min
- Schedule: 15 min
- Device: 30 min
- Auth: 45 min
- Testing all: 30 min

**Total**: ~2.5 hours for complete audit logging coverage

---

Generated: 2025-11-27
Author: Backend Architect Agent
