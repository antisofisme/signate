# 🚀 PHASE 3: SECURITY & ROW-LEVEL SECURITY - IMPLEMENTATION GUIDE

**Timeline:** Week 5 (after Phase 2)
**Duration:** 5-7 days
**Risk Level:** High
**Downtime:** < 10 minutes

---

## 📋 OVERVIEW

Phase 3 adds enterprise-grade security with Row-Level Security (RLS):
- ✅ PostgreSQL Row-Level Security policies
- ✅ Multi-tenant data isolation
- ✅ Audit logging for all data access
- ✅ Security testing suite

**What changes:**
- Database: RLS policies on all tables
- Backend: RLS context setting
- CMS: No changes (transparent)
- Player: No changes (transparent)

---

## 🎯 WEEK-BY-WEEK PLAN

### **Week 5: Security Hardening (Days 1-7)**

---

## 📅 WEEK 5: SECURITY IMPLEMENTATION

### Day 1: Database RLS Policies

```bash
# Step 1: Run Migration 016 (RLS Policies)
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/016_add_row_level_security.sql

# Verify RLS enabled
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT schemaname, tablename, rowsecurity
  FROM pg_tables
  WHERE schemaname = 'public'
    AND rowsecurity = true;"

# Expected: 10+ tables with RLS enabled
```

**Migration File:**
```sql
-- database/fix-database/migrations/016_add_row_level_security.sql

-- ============================================================================
-- MIGRATION 016: Row-Level Security (RLS) Policies
-- ============================================================================
-- Purpose: Enable multi-tenant data isolation using PostgreSQL RLS
-- Impact: All queries automatically filtered by organization_id
-- Risk: High - Test thoroughly before production deployment
-- ============================================================================

BEGIN;

-- Step 1: Enable RLS on all multi-tenant tables
-- ============================================================================

ALTER TABLE contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_speed_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_playback_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_organizations ENABLE ROW LEVEL SECURITY;

-- Step 2: Create function to get current organization_id from session
-- ============================================================================

CREATE OR REPLACE FUNCTION current_organization_id()
RETURNS INTEGER AS $$
DECLARE
  org_id INTEGER;
BEGIN
  -- Get organization_id from session variable
  org_id := current_setting('app.current_organization_id', true)::INTEGER;

  IF org_id IS NULL THEN
    RAISE EXCEPTION 'No organization context set. Call SET LOCAL app.current_organization_id = ?';
  END IF;

  RETURN org_id;
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Step 3: Create RLS policies for each table
-- ============================================================================

-- Contents: Users can only see their organization's content
CREATE POLICY contents_isolation ON contents
  FOR ALL
  USING (organization_id = current_organization_id());

-- Devices: Users can only see their organization's devices
CREATE POLICY devices_isolation ON devices
  FOR ALL
  USING (organization_id = current_organization_id());

-- Playlists: Users can only see their organization's playlists
CREATE POLICY playlists_isolation ON playlists
  FOR ALL
  USING (organization_id = current_organization_id());

-- Playlist Items: Inherited from playlist's organization
CREATE POLICY playlist_items_isolation ON playlist_items
  FOR ALL
  USING (
    playlist_id IN (
      SELECT id FROM playlists WHERE organization_id = current_organization_id()
    )
  );

-- Device Logs: Users can only see logs from their organization's devices
CREATE POLICY device_logs_isolation ON device_logs
  FOR ALL
  USING (
    device_id IN (
      SELECT id FROM devices WHERE organization_id = current_organization_id()
    )
  );

-- Device Speed Tests: Same as device logs
CREATE POLICY device_speed_tests_isolation ON device_speed_tests
  FOR ALL
  USING (
    device_id IN (
      SELECT id FROM devices WHERE organization_id = current_organization_id()
    )
  );

-- Content Playback Logs: Direct organization_id check
CREATE POLICY content_playback_logs_isolation ON content_playback_logs
  FOR ALL
  USING (organization_id = current_organization_id());

-- User Organizations: Users can only see their own organization memberships
CREATE POLICY user_organizations_isolation ON user_organizations
  FOR ALL
  USING (organization_id = current_organization_id());

-- Step 4: Create superadmin bypass policy
-- ============================================================================

CREATE OR REPLACE FUNCTION is_superadmin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN current_setting('app.is_superadmin', true)::BOOLEAN = true;
EXCEPTION
  WHEN OTHERS THEN
    RETURN false;
END;
$$ LANGUAGE plpgsql STABLE;

-- Superadmin can see all data
CREATE POLICY contents_superadmin ON contents
  FOR ALL
  USING (is_superadmin());

CREATE POLICY devices_superadmin ON devices
  FOR ALL
  USING (is_superadmin());

CREATE POLICY playlists_superadmin ON playlists
  FOR ALL
  USING (is_superadmin());

-- Step 5: Create audit log for RLS policy violations
-- ============================================================================

CREATE TABLE IF NOT EXISTS rls_violations (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  organization_id INTEGER,
  table_name TEXT NOT NULL,
  action TEXT NOT NULL,
  attempted_at TIMESTAMP DEFAULT NOW(),
  details JSONB
);

CREATE INDEX idx_rls_violations_user ON rls_violations(user_id);
CREATE INDEX idx_rls_violations_org ON rls_violations(organization_id);
CREATE INDEX idx_rls_violations_time ON rls_violations(attempted_at DESC);

COMMIT;

-- ============================================================================
-- ROLLBACK PROCEDURE
-- ============================================================================
-- To disable RLS:
-- BEGIN;
-- ALTER TABLE contents DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE devices DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE playlists DISABLE ROW LEVEL SECURITY;
-- ... (repeat for all tables)
-- COMMIT;
-- ============================================================================
```

### Day 2-3: Backend RLS Integration

**Create RLS Middleware:**
```python
# backend-python/shared/middleware/rls_middleware.py

from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

class RLSMiddleware:
    """Middleware to set RLS context for all database queries"""

    def __init__(self, db: Session, user):
        self.db = db
        self.user = user

    def __enter__(self):
        """Set RLS context when entering scope"""
        if self.user:
            # Set organization context
            org_id = self.get_user_organization_id()
            self.db.execute(
                f"SET LOCAL app.current_organization_id = {org_id}"
            )

            # Set superadmin flag
            is_super = self.user.role == 'superadmin'
            self.db.execute(
                f"SET LOCAL app.is_superadmin = {is_super}"
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset context when exiting scope"""
        # PostgreSQL automatically resets LOCAL variables at transaction end
        pass

    def get_user_organization_id(self) -> int:
        """Get user's organization ID"""
        # For superadmin, return default organization
        if self.user.role == 'superadmin':
            return 1  # Default org

        # For regular users, get their organization
        from app.models import UserOrganization
        user_org = self.db.query(UserOrganization).filter(
            UserOrganization.user_id == self.user.id
        ).first()

        if not user_org:
            raise HTTPException(
                status_code=403,
                detail="User not assigned to any organization"
            )

        return user_org.organization_id
```

**Update Database Dependency:**
```python
# backend-python/shared/database.py

from sqlalchemy.orm import Session
from contextlib import contextmanager
from .middleware.rls_middleware import RLSMiddleware

@contextmanager
def get_db_with_rls(user):
    """Get database session with RLS context"""
    db = SessionLocal()
    try:
        with RLSMiddleware(db, user):
            yield db
    finally:
        db.close()

# Update get_db to use RLS
def get_db_session(current_user=Depends(get_current_user)):
    """Dependency for database session with RLS"""
    with get_db_with_rls(current_user) as db:
        yield db
```

**Update All Services:**
```python
# Example: backend-python/services/content/routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.database import get_db_session  # Updated import
from shared.auth import get_current_user

router = APIRouter(prefix="/api/v1/contents", tags=["contents"])

@router.get("/")
async def list_contents(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)  # RLS automatically applied!
):
    """List contents - automatically filtered by organization"""
    from .models import Content

    # No need to filter by organization_id - RLS does it automatically!
    contents = db.query(Content).all()

    return contents
```

### Day 4: Security Testing

**Create RLS Test Suite:**
```python
# backend-python/tests/test_rls.py

import pytest
from sqlalchemy.orm import Session
from app.models import User, Organization, Content
from shared.middleware.rls_middleware import RLSMiddleware

def test_rls_isolation(db: Session):
    """Test that users can only see their organization's data"""

    # Setup: Create 2 organizations with content
    org1 = Organization(name="Org 1", pin="111111")
    org2 = Organization(name="Org 2", pin="222222")
    db.add_all([org1, org2])
    db.commit()

    # Create content for each org
    content1 = Content(title="Content 1", organization_id=org1.id)
    content2 = Content(title="Content 2", organization_id=org2.id)
    db.add_all([content1, content2])
    db.commit()

    # Create user in org1
    user1 = User(username="user1", organization_id=org1.id)
    db.add(user1)
    db.commit()

    # Test: User1 should only see content1
    with RLSMiddleware(db, user1):
        contents = db.query(Content).all()
        assert len(contents) == 1
        assert contents[0].id == content1.id

    # Test: Without RLS, should see all (for superadmin)
    user_super = User(username="super", role="superadmin")
    db.add(user_super)
    db.commit()

    with RLSMiddleware(db, user_super):
        contents = db.query(Content).all()
        assert len(contents) == 2

def test_rls_insert_restriction(db: Session):
    """Test that users can only insert data for their organization"""

    org1 = Organization(name="Org 1", pin="111111")
    org2 = Organization(name="Org 2", pin="222222")
    db.add_all([org1, org2])
    db.commit()

    user1 = User(username="user1", organization_id=org1.id)
    db.add(user1)
    db.commit()

    # Try to insert content for org2 (should fail)
    with RLSMiddleware(db, user1):
        content = Content(title="Sneaky Content", organization_id=org2.id)
        db.add(content)

        with pytest.raises(Exception):
            db.commit()

def test_rls_update_restriction(db: Session):
    """Test that users cannot update other organization's data"""

    org1 = Organization(name="Org 1", pin="111111")
    org2 = Organization(name="Org 2", pin="222222")
    db.add_all([org1, org2])
    db.commit()

    content2 = Content(title="Content 2", organization_id=org2.id)
    db.add(content2)
    db.commit()

    user1 = User(username="user1", organization_id=org1.id)
    db.add(user1)
    db.commit()

    # Try to update org2's content (should not be visible)
    with RLSMiddleware(db, user1):
        content = db.query(Content).filter(Content.id == content2.id).first()
        assert content is None  # Should not be visible!
```

**Run Tests:**
```bash
# Run RLS test suite
pytest backend-python/tests/test_rls.py -v

# Expected output:
# test_rls_isolation PASSED
# test_rls_insert_restriction PASSED
# test_rls_update_restriction PASSED
```

### Day 5: Audit Logging

**Create Audit Service:**
```python
# backend-python/shared/services/audit_service.py

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any
import json

class AuditService:
    """Service for audit logging"""

    def __init__(self, db: Session):
        self.db = db

    def log_access(
        self,
        user_id: int,
        organization_id: int,
        table_name: str,
        action: str,
        record_id: int = None,
        details: Dict[str, Any] = None
    ):
        """Log data access for audit trail"""
        from app.models import AuditLog

        log = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            table_name=table_name,
            action=action,
            record_id=record_id,
            details=details,
            timestamp=datetime.utcnow()
        )

        self.db.add(log)
        self.db.commit()

    def log_rls_violation(
        self,
        user_id: int,
        organization_id: int,
        table_name: str,
        action: str,
        details: Dict[str, Any] = None
    ):
        """Log RLS policy violation attempt"""
        from app.models import RLSViolation

        violation = RLSViolation(
            user_id=user_id,
            organization_id=organization_id,
            table_name=table_name,
            action=action,
            details=details,
            attempted_at=datetime.utcnow()
        )

        self.db.add(violation)
        self.db.commit()

        # Alert security team
        self.send_security_alert(violation)

    def send_security_alert(self, violation):
        """Send alert for security violation"""
        # TODO: Integrate with alerting system
        print(f"[SECURITY ALERT] RLS violation: {violation.table_name} by user {violation.user_id}")
```

### Day 6-7: Integration Testing & Deployment

**Create End-to-End Test:**
```bash
#!/bin/bash
# tests/e2e_rls_test.sh

echo "=== RLS End-to-End Test ==="

# 1. Create test organizations
curl -X POST http://localhost:8001/api/v1/organizations \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name": "Test Org 1", "pin": "111111"}'

curl -X POST http://localhost:8001/api/v1/organizations \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"name": "Test Org 2", "pin": "222222"}'

# 2. Create users in each org
USER1_TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -d '{"username": "org1_user", "password": "test123"}' | jq -r '.access_token')

USER2_TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -d '{"username": "org2_user", "password": "test123"}' | jq -r '.access_token')

# 3. Create content as user1
CONTENT_ID=$(curl -X POST http://localhost:8001/api/v1/contents \
  -H "Authorization: Bearer $USER1_TOKEN" \
  -d '{"title": "Org 1 Content"}' | jq -r '.id')

# 4. Try to access as user2 (should fail)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8001/api/v1/contents/$CONTENT_ID \
  -H "Authorization: Bearer $USER2_TOKEN")

if [ "$STATUS" = "404" ]; then
  echo "✅ RLS working: User2 cannot see User1's content"
else
  echo "❌ RLS failed: User2 can see User1's content (status: $STATUS)"
  exit 1
fi

# 5. Access as superadmin (should succeed)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:8001/api/v1/contents/$CONTENT_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if [ "$STATUS" = "200" ]; then
  echo "✅ Superadmin bypass working"
else
  echo "❌ Superadmin bypass failed (status: $STATUS)"
  exit 1
fi

echo "=== All RLS tests passed! ==="
```

**Deployment to Staging:**
```bash
# Deploy to staging
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/staging

  # Backup database first
  docker exec signage-postgres pg_dump -U signage_user signage_db_staging \
    > backup_before_rls_$(date +%Y%m%d_%H%M%S).sql

  # Run migration
  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/016_add_row_level_security.sql

  # Deploy backend
  docker-compose up -d --build backend-api

  # Run RLS tests
  ./tests/e2e_rls_test.sh
EOF
```

---

## ✅ SUCCESS CRITERIA

- ✅ RLS enabled on all multi-tenant tables
- ✅ Users can only see their organization's data
- ✅ Superadmin can see all data
- ✅ Audit logging captures all access
- ✅ All tests passing
- ✅ No data leakage between organizations

---

## 🎯 DELIVERABLES

- ✅ Migration 016: RLS policies
- ✅ RLS middleware for backend
- ✅ Comprehensive test suite
- ✅ Audit logging system
- ✅ Security monitoring dashboard

**Phase 3 Complete! Ready for Phase 4.** 🚀
