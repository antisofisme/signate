# 🚀 PHASE 1: FOUNDATION - DETAILED IMPLEMENTATION GUIDE

**Timeline:** Week 2 (after Phase 0 preparation)
**Duration:** 5-7 days
**Risk Level:** Low
**Downtime:** < 5 minutes

---

## 📋 OVERVIEW

Phase 1 establishes the foundation for the new architecture:
- ✅ RBAC (Role-Based Access Control) system
- ✅ Session management with revocation
- ✅ Device defaults consistency
- ✅ Soft delete unique constraints

**What changes:**
- Database: 4 new tables + constraints
- Backend: New services (RBAC, Session)
- CMS: NO changes (backward compatible)
- Player: NO changes

---

## 🎯 DAY-BY-DAY PLAN

### **Day 1: Database Migrations (Local Testing)**
### **Day 2: Backend Implementation (Local Testing)**
### **Day 3: Data Migration Scripts**
### **Day 4: Staging Deployment & Testing**
### **Day 5: Production Deployment**
### **Day 6-7: Monitoring & Stabilization**

---

## 📅 DAY 1: DATABASE MIGRATIONS (Local Testing)

### Step 1.1: Setup Local Environment

```bash
# Navigate to project
cd /mnt/g/khoirul/signate

# Ensure local PostgreSQL is running
docker ps | grep postgres

# If not running, start it
cd docker
docker-compose up -d postgres
```

### Step 1.2: Verify Current Schema

```bash
# Connect to local database
docker exec -it signage-postgres psql -U signage_user -d signage_db

# List current tables
\dt

# Expected tables (before migration):
# - users
# - organizations
# - devices
# - contents
# - playlists
# - tags
# ... etc

# Exit
\q
```

### Step 1.3: Run Migration 010 (RBAC System)

```bash
# Run migration
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/010_create_roles_table.sql

# Verify success
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_name = 'roles';"

# Expected output:
#  table_name
# ------------
#  roles
# (1 row)

# Check role structure
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  \d roles"

# Verify system roles created
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT id, name, is_system_role FROM roles;"

# Expected output:
#  id |     name     | is_system_role
# ----+--------------+----------------
#   1 | SUPER_ADMIN  | t
#   2 | ADMIN        | t
#   3 | VIEWER       | t
```

### Step 1.4: Run Migration 011 (Session Management)

```bash
# Run migration
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/011_create_user_sessions_table.sql

# Verify success
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_name = 'user_sessions';"

# Check indexes created
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT indexname
  FROM pg_indexes
  WHERE tablename = 'user_sessions';"

# Expected indexes:
# - user_sessions_pkey
# - idx_sessions_token
# - idx_sessions_user
# - idx_sessions_active
```

### Step 1.5: Run Migration 012 (Device Defaults)

```bash
# Run migration
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/012_fix_device_defaults_consistency.sql

# Verify device table updated
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  \d devices" | grep DEFAULT

# Should show consistent defaults
```

### Step 1.6: Run Migration 013 (Soft Delete Constraints)

```bash
# Run migration
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/013_fix_soft_delete_unique_constraints.sql

# Verify partial unique indexes created
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT indexname, indexdef
  FROM pg_indexes
  WHERE indexname LIKE '%_active';"

# Expected indexes:
# - unique_playlist_name_per_org_active
# - unique_tag_name_per_org_active
# - unique_device_name_per_org_active
```

### Step 1.7: Test Constraint Behavior

```bash
# Test soft delete unique constraint
docker exec -it signage-postgres psql -U signage_user -d signage_db << 'EOF'
-- Create test playlist
INSERT INTO playlists (name, organization_id)
VALUES ('Test Playlist', 1);

-- Try to create duplicate (should fail)
INSERT INTO playlists (name, organization_id)
VALUES ('Test Playlist', 1);
-- ERROR: duplicate key value violates unique constraint

-- Soft delete first one
UPDATE playlists SET deleted_at = NOW() WHERE name = 'Test Playlist';

-- Now we can create same name again (should succeed)
INSERT INTO playlists (name, organization_id)
VALUES ('Test Playlist', 1);
-- SUCCESS!

-- Cleanup
DELETE FROM playlists WHERE name = 'Test Playlist';
EOF
```

### Step 1.8: Verify All Migrations

```bash
# Create verification script
cat > /tmp/verify_phase1.sql << 'EOF'
-- Verification Query for Phase 1 Migrations

-- 1. Check all tables exist
SELECT
  CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'roles')
    THEN '✅' ELSE '❌' END as roles_table,
  CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions')
    THEN '✅' ELSE '❌' END as sessions_table;

-- 2. Check system roles exist
SELECT
  CASE WHEN COUNT(*) = 3 THEN '✅' ELSE '❌' END as system_roles_count
FROM roles
WHERE is_system_role = TRUE;

-- 3. Check foreign keys
SELECT
  CASE WHEN COUNT(*) > 0 THEN '✅' ELSE '❌' END as role_fk_exists
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
  AND table_name = 'users'
  AND constraint_name LIKE '%role%';

-- 4. Check partial unique indexes
SELECT
  CASE WHEN COUNT(*) >= 3 THEN '✅' ELSE '❌' END as partial_indexes_count
FROM pg_indexes
WHERE indexname LIKE '%_active';

-- Summary
SELECT
  '✅ Phase 1 Migration Complete!' as status,
  COUNT(DISTINCT table_name) as tables_created,
  (SELECT COUNT(*) FROM roles WHERE is_system_role = TRUE) as system_roles
FROM information_schema.tables
WHERE table_name IN ('roles', 'user_sessions');
EOF

# Run verification
docker exec -i signage-postgres psql -U signage_user -d signage_db < /tmp/verify_phase1.sql
```

**✅ Day 1 Complete if all checks pass!**

---

## 📅 DAY 2: BACKEND IMPLEMENTATION (Local Testing)

### Step 2.1: Create Models

```python
# backend-python/services/auth/models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.core.database import Base

class Role(Base):
    """Role model for RBAC system"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255))
    is_system_role = Column(Boolean, default=False, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))

    # JSONB permissions
    # Example: {"content.create": true, "content.read": true, "device.manage": true}
    permissions = Column(JSONB, default={})

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="role")
    organization = relationship("Organization")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class UserSession(Base):
    """User session for JWT token management"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))

    # Session info
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True)

    # Device/Client info
    device_info = Column(JSONB)  # {device_type, os, browser, etc}
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Session state
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def is_valid(self) -> bool:
        """Check if session is still valid"""
        if self.revoked_at:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, valid={self.is_valid()})>"


# Update User model
class User(Base):
    __tablename__ = "users"

    # ... existing columns ...

    # NEW: RBAC
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"))
    role = relationship("Role", back_populates="users")

    # NEW: Sessions
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    # DEPRECATED (keep for backward compatibility during migration)
    # Will be removed in Phase 3
    old_role = Column(String(20))  # 'SUPER_ADMIN', 'ADMIN', 'VIEWER'
```

### Step 2.2: Create RBAC Service

```python
# backend-python/services/auth/rbac_service.py

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .models import Role, User
from app.core.exceptions import NotFoundError, ValidationError

class RBACService:
    """Role-Based Access Control Service"""

    def __init__(self, db: Session):
        self.db = db

    def create_role(
        self,
        name: str,
        permissions: Dict[str, bool],
        organization_id: Optional[int] = None,
        description: str = ""
    ) -> Role:
        """Create new role"""

        # Validate
        if not name:
            raise ValidationError("Role name is required")

        # Check duplicate
        existing = self.db.query(Role).filter(
            and_(
                Role.name == name,
                Role.organization_id == organization_id
            )
        ).first()

        if existing:
            raise ValidationError(f"Role '{name}' already exists")

        # Create role
        role = Role(
            name=name,
            description=description,
            permissions=permissions,
            organization_id=organization_id,
            is_system_role=(organization_id is None)
        )

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def get_role(self, role_id: int) -> Role:
        """Get role by ID"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise NotFoundError(f"Role {role_id} not found")
        return role

    def list_roles(
        self,
        organization_id: Optional[int] = None,
        include_system_roles: bool = True
    ) -> List[Role]:
        """List all roles"""
        query = self.db.query(Role)

        if organization_id:
            if include_system_roles:
                # Include system roles + organization roles
                query = query.filter(
                    (Role.organization_id == organization_id) |
                    (Role.is_system_role == True)
                )
            else:
                # Only organization roles
                query = query.filter(Role.organization_id == organization_id)
        else:
            # Only system roles
            query = query.filter(Role.is_system_role == True)

        return query.all()

    def assign_role(self, user_id: int, role_id: int) -> User:
        """Assign role to user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        role = self.get_role(role_id)

        # Validate organization match
        if role.organization_id and role.organization_id != user.organization_id:
            raise ValidationError("Role organization mismatch")

        user.role_id = role_id
        self.db.commit()
        self.db.refresh(user)

        return user

    def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has specific permission

        Args:
            user: User object
            permission: Permission string (e.g., 'content.create')

        Returns:
            True if user has permission, False otherwise

        Examples:
            check_permission(user, 'content.create')
            check_permission(user, 'device.manage')
        """
        if not user.role:
            return False

        permissions = user.role.permissions or {}

        # Check exact permission
        if permissions.get(permission):
            return True

        # Check wildcard permission (e.g., 'content.*' grants 'content.create')
        parts = permission.split('.')
        if len(parts) == 2:
            wildcard = f"{parts[0]}.*"
            if permissions.get(wildcard):
                return True

        # Check super wildcard
        if permissions.get('*'):
            return True

        return False

    def migrate_old_roles(self):
        """
        Migrate users from old string-based roles to new RBAC system

        This function:
        1. Maps old role strings to new Role IDs
        2. Updates users.role_id
        3. Keeps old_role for backward compatibility
        """
        # Get system roles
        super_admin_role = self.db.query(Role).filter(
            Role.name == "SUPER_ADMIN",
            Role.is_system_role == True
        ).first()

        admin_role = self.db.query(Role).filter(
            Role.name == "ADMIN",
            Role.is_system_role == True
        ).first()

        viewer_role = self.db.query(Role).filter(
            Role.name == "VIEWER",
            Role.is_system_role == True
        ).first()

        if not all([super_admin_role, admin_role, viewer_role]):
            raise ValidationError("System roles not found. Run migration 010 first.")

        # Map old roles to new roles
        role_mapping = {
            "SUPER_ADMIN": super_admin_role.id,
            "ADMIN": admin_role.id,
            "VIEWER": viewer_role.id
        }

        # Update users
        migrated_count = 0
        users = self.db.query(User).filter(User.role_id.is_(None)).all()

        for user in users:
            old_role = getattr(user, 'old_role', None) or user.role  # Fallback to 'role' column

            if old_role in role_mapping:
                user.role_id = role_mapping[old_role]
                migrated_count += 1

        self.db.commit()

        return {
            "migrated_count": migrated_count,
            "total_users": len(users)
        }
```

### Step 2.3: Create Session Service

```python
# backend-python/services/auth/session_service.py

from typing import Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import secrets
from .models import UserSession, User
from app.core.exceptions import NotFoundError, UnauthorizedError

class SessionService:
    """User session management service"""

    DEFAULT_SESSION_DAYS = 30
    DEFAULT_REFRESH_DAYS = 90

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: int,
        device_info: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_days: int = DEFAULT_SESSION_DAYS
    ) -> UserSession:
        """
        Create new session for user

        Returns:
            UserSession with session_token and refresh_token
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # Generate tokens
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)

        # Create session
        session = UserSession(
            user_id=user_id,
            organization_id=user.organization_id,
            session_token=session_token,
            refresh_token=refresh_token,
            device_info=device_info or {},
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            last_activity_at=datetime.utcnow()
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def validate_session(self, session_token: str) -> UserSession:
        """
        Validate session token

        Raises:
            UnauthorizedError if session invalid
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()

        if not session:
            raise UnauthorizedError("Invalid session token")

        if not session.is_valid():
            raise UnauthorizedError("Session expired or revoked")

        # Update last activity
        session.last_activity_at = datetime.utcnow()
        self.db.commit()

        return session

    def refresh_session(self, refresh_token: str) -> UserSession:
        """
        Refresh session using refresh token

        Returns:
            New session with new tokens
        """
        old_session = self.db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()

        if not old_session or not old_session.is_valid():
            raise UnauthorizedError("Invalid refresh token")

        # Revoke old session
        old_session.revoked_at = datetime.utcnow()

        # Create new session
        new_session = self.create_session(
            user_id=old_session.user_id,
            device_info=old_session.device_info,
            ip_address=old_session.ip_address,
            user_agent=old_session.user_agent
        )

        self.db.commit()

        return new_session

    def revoke_session(self, session_token: str):
        """Revoke specific session (logout)"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()

        if session and not session.revoked_at:
            session.revoked_at = datetime.utcnow()
            self.db.commit()

    def revoke_all_sessions(self, user_id: int, except_session: Optional[str] = None):
        """
        Revoke all sessions for user (logout all devices)

        Args:
            user_id: User ID
            except_session: Optional session token to keep active
        """
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None)
        )

        if except_session:
            query = query.filter(UserSession.session_token != except_session)

        query.update({"revoked_at": datetime.utcnow()})
        self.db.commit()

    def list_user_sessions(self, user_id: int, active_only: bool = True):
        """List all sessions for user"""
        query = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        )

        if active_only:
            query = query.filter(
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.utcnow()
            )

        return query.order_by(UserSession.last_activity_at.desc()).all()

    def cleanup_expired_sessions(self):
        """Cleanup expired sessions (run as cron job)"""
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        deleted_count = self.db.query(UserSession).filter(
            (UserSession.expires_at < datetime.utcnow()) |
            (UserSession.revoked_at < cutoff_date)
        ).delete()

        self.db.commit()

        return {"deleted_count": deleted_count}
```

### Step 2.4: Create API Endpoints

```python
# backend-python/services/auth/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .rbac_service import RBACService
from .session_service import SessionService
from .schemas import RoleCreate, RoleResponse, SessionResponse
from app.core.deps import get_db, get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# ============================================================================
# RBAC ENDPOINTS
# ============================================================================

@router.post("/roles", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new role (ADMIN only)"""
    rbac = RBACService(db)

    # Check permission
    if not rbac.check_permission(current_user, "role.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create roles"
        )

    role = rbac.create_role(
        name=role_data.name,
        permissions=role_data.permissions,
        organization_id=current_user.organization_id,
        description=role_data.description
    )

    return role


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available roles"""
    rbac = RBACService(db)

    # Super admin sees all, others see their org + system roles
    if rbac.check_permission(current_user, "*"):
        roles = rbac.list_roles(include_system_roles=True)
    else:
        roles = rbac.list_roles(
            organization_id=current_user.organization_id,
            include_system_roles=True
        )

    return roles


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@router.get("/sessions", response_model=List[SessionResponse])
async def list_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List current user's active sessions"""
    session_service = SessionService(db)
    sessions = session_service.list_user_sessions(current_user.id, active_only=True)
    return sessions


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke specific session"""
    # Implementation...
    return {"message": "Session revoked"}


@router.delete("/sessions")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from all devices"""
    session_service = SessionService(db)
    session_service.revoke_all_sessions(current_user.id)
    return {"message": "All sessions revoked"}


# ============================================================================
# MIGRATION ENDPOINT (Admin only)
# ============================================================================

@router.post("/migrate-roles")
async def migrate_old_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Migrate from old role system to RBAC (SUPER_ADMIN only)"""
    rbac = RBACService(db)

    if not rbac.check_permission(current_user, "*"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SUPER_ADMIN can run migration"
        )

    result = rbac.migrate_old_roles()
    return result
```

### Step 2.5: Create Schemas

```python
# backend-python/services/auth/schemas.py

from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    permissions: Dict[str, bool]

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_system_role: bool
    permissions: Dict[str, bool]

    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    device_info: Optional[Dict]
    ip_address: Optional[str]
    last_activity_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True
```

### Step 2.6: Update Main App

```python
# backend-python/main.py

from fastapi import FastAPI
from app.services.auth.routes import router as auth_router

app = FastAPI(title="Signage API")

# Include routers
app.include_router(auth_router)

# ... other routers ...
```

### Step 2.7: Test Backend Locally

```bash
# Start backend
cd /mnt/g/khoirul/signate/backend-python
python3 main.py

# In another terminal, test endpoints
# 1. List roles
curl http://localhost:8001/api/v1/auth/roles

# 2. Create custom role (need auth token)
curl -X POST http://localhost:8001/api/v1/auth/roles \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Content Manager",
    "description": "Can manage content only",
    "permissions": {
      "content.create": true,
      "content.read": true,
      "content.update": true,
      "content.delete": true
    }
  }'

# 3. Run migration
curl -X POST http://localhost:8001/api/v1/auth/migrate-roles \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"

# Expected response:
# {"migrated_count": 5, "total_users": 5}
```

**✅ Day 2 Complete if backend tests pass!**

---

## 📅 DAY 3: DATA MIGRATION SCRIPTS

### Step 3.1: Create Migration Script

```python
# backend-python/scripts/migrate_phase1_data.py

"""
Phase 1 Data Migration Script

This script migrates existing data to work with new Phase 1 schema:
1. Migrate old roles to RBAC system
2. Verify data integrity
"""

import sys
sys.path.append('/mnt/g/khoirul/signate/backend-python')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.services.auth.rbac_service import RBACService
from app.services.auth.models import Role, User

def migrate_roles(db: Session):
    """Migrate old string-based roles to RBAC"""
    rbac = RBACService(db)

    print("🚀 Starting role migration...")

    # Migrate old roles
    result = rbac.migrate_old_roles()

    print(f"✅ Migrated {result['migrated_count']} out of {result['total_users']} users")

    return result

def verify_migration(db: Session):
    """Verify migration completed successfully"""

    print("\n🔍 Verifying migration...")

    # Check all users have role_id
    users_without_role = db.query(User).filter(User.role_id.is_(None)).count()

    if users_without_role > 0:
        print(f"⚠️ WARNING: {users_without_role} users still without role_id")
        return False

    # Check system roles exist
    system_roles = db.query(Role).filter(Role.is_system_role == True).count()

    if system_roles < 3:
        print(f"⚠️ WARNING: Only {system_roles} system roles found (expected 3)")
        return False

    print("✅ Migration verified successfully!")
    print(f"  - All users have role_id")
    print(f"  - {system_roles} system roles exist")

    return True

def rollback_migration(db: Session):
    """Rollback migration if something goes wrong"""

    print("\n🔄 Rolling back migration...")

    # Clear role_id from all users
    db.query(User).update({"role_id": None})
    db.commit()

    print("✅ Rollback complete")

def main():
    """Main migration runner"""

    db = SessionLocal()

    try:
        # Run migration
        result = migrate_roles(db)

        # Verify
        success = verify_migration(db)

        if not success:
            print("\n❌ Migration verification failed!")
            rollback = input("Rollback migration? (yes/no): ")

            if rollback.lower() == 'yes':
                rollback_migration(db)

            sys.exit(1)

        print("\n✅ Phase 1 data migration complete!")

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("Rolling back...")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    main()
```

### Step 3.2: Run Migration Script

```bash
# Run migration script
cd /mnt/g/khoirul/signate/backend-python
python3 scripts/migrate_phase1_data.py

# Expected output:
# 🚀 Starting role migration...
# ✅ Migrated 5 out of 5 users
#
# 🔍 Verifying migration...
# ✅ Migration verified successfully!
#   - All users have role_id
#   - 3 system roles exist
#
# ✅ Phase 1 data migration complete!
```

**✅ Day 3 Complete if migration successful!**

---

## 📅 DAY 4: STAGING DEPLOYMENT & TESTING

### Step 4.1: Deploy to Staging

```bash
# Sync code to staging server
cd /mnt/g/khoirul/signage
sshpass -p 'Password@2021' rsync -avz \
  --exclude 'node_modules' \
  --exclude '.git' \
  --exclude '__pycache__' \
  . gzjbbk@192.168.5.12:/home/gzjbbk/staging/
```

### Step 4.2: Run Migrations on Staging

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/staging

  # Backup staging database first
  docker exec signage-postgres pg_dump -U signage_user -d signage_db_staging \
    > /backup/staging_pre_phase1_$(date +%Y%m%d_%H%M%S).sql

  # Run migrations
  for migration in 010 011 012 013; do
    echo "Running migration ${migration}..."
    docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
      < database/fix-database/migrations/${migration}_*.sql
  done

  echo "✅ Migrations complete!"
EOF
```

### Step 4.3: Deploy Backend to Staging

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/staging

  # Rebuild backend container
  docker-compose -f docker/docker-compose.staging.yml up -d --build backend-api

  # Wait for backend to start
  sleep 15

  # Check health
  curl http://localhost:8001/health
EOF
```

### Step 4.4: Run Data Migration on Staging

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/staging

  # Run migration script
  docker exec signage-backend python3 scripts/migrate_phase1_data.py
EOF
```

### Step 4.5: Test on Staging

```bash
# Test 1: List roles
ssh gzjbbk@192.168.5.12 'curl http://localhost:8001/api/v1/auth/roles'

# Test 2: Verify old endpoints still work (backward compatibility)
ssh gzjbbk@192.168.5.12 'curl http://localhost:8001/api/v1/users'

# Test 3: Check database
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -it signage-postgres psql -U signage_user -d signage_db_staging -c "
    SELECT u.username, r.name as role_name
    FROM users u
    LEFT JOIN roles r ON r.id = u.role_id
    LIMIT 5;"
EOF
```

**✅ Day 4 Complete if all staging tests pass!**

---

## 📅 DAY 5: PRODUCTION DEPLOYMENT

**⚠️ PRODUCTION DEPLOYMENT - BE CAREFUL!**

### Step 5.1: Pre-Deployment Checklist

```bash
# Checklist:
✅ Staging tests passed
✅ Backup plan ready
✅ Rollback procedure tested
✅ Team notified
✅ Maintenance window scheduled (optional)
```

### Step 5.2: Production Backup

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  # Full backup
  docker exec signage-postgres pg_dump -U signage_user -d signage_db \
    > /backup/prod_pre_phase1_$(date +%Y%m%d_%H%M%S).sql

  # Verify backup
  ls -lh /backup/prod_pre_phase1_*.sql

  # Test restore (to test database)
  docker exec signage-postgres createdb -U postgres signage_db_test
  docker exec -i signage-postgres psql -U signage_user -d signage_db_test \
    < /backup/prod_pre_phase1_*.sql

  # Cleanup test
  docker exec signage-postgres dropdb -U postgres signage_db_test

  echo "✅ Backup verified!"
EOF
```

### Step 5.3: Run Production Migrations

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/signate

  echo "🚀 Starting production migration..."
  echo "Downtime starts now!"

  # Run migrations (< 5 minutes)
  for migration in 010 011 012 013; do
    echo "Running migration ${migration}..."
    docker exec -i signage-postgres psql -U signage_user -d signage_db \
      < database/fix-database/migrations/${migration}_*.sql || exit 1
  done

  echo "✅ Database migrations complete!"
EOF
```

### Step 5.4: Deploy Production Backend

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/signate

  # Sync latest code
  # (already synced in prep)

  # Rebuild backend
  docker-compose -f docker/docker-compose.yml up -d --build backend-api

  # Wait for backend
  sleep 20

  # Check health
  curl http://192.168.5.12:8001/health
EOF
```

### Step 5.5: Run Production Data Migration

```bash
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/signate

  # Run migration
  docker exec signage-backend python3 scripts/migrate_phase1_data.py

  echo "✅ Data migration complete!"
  echo "Downtime ends now!"
EOF
```

### Step 5.6: Verify Production

```bash
# Test 1: API health
curl http://192.168.5.12:8001/health

# Test 2: List roles
curl http://192.168.5.12:8001/api/v1/auth/roles

# Test 3: Old CMS still works
curl http://192.168.5.12:8001/api/v1/users | jq '.[:3]'

# Test 4: Database check
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
    SELECT
      COUNT(*) as total_users,
      COUNT(*) FILTER (WHERE role_id IS NOT NULL) as users_with_role
    FROM users;"
EOF

# Expected: total_users = users_with_role
```

**✅ Day 5 Complete if production verified!**

---

## 📅 DAY 6-7: MONITORING & STABILIZATION

### Step 6.1: Monitor Logs

```bash
# Monitor backend logs
ssh gzjbbk@192.168.5.12 'docker logs -f signage-backend --tail 100'

# Look for:
# ✅ No errors
# ✅ API requests successful
# ✅ Database queries working
```

### Step 6.2: Monitor Performance

```bash
# Check database performance
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
    SELECT * FROM v_connection_stats;"  # If migration 020 ran

  # Check slow queries
  docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
    SELECT query, calls, total_time
    FROM pg_stat_statements
    ORDER BY total_time DESC
    LIMIT 10;"  # If pg_stat_statements enabled
EOF
```

### Step 6.3: User Feedback

```bash
# Collect feedback:
# - Test login/logout
# - Test CMS features
# - Check player still works
# - Monitor error reports
```

**✅ Phase 1 COMPLETE if stable for 48 hours!**

---

## 🎯 SUCCESS CRITERIA

- ✅ All 4 migrations executed successfully
- ✅ RBAC system working
- ✅ Session management working
- ✅ All users migrated to new role system
- ✅ Old CMS still works (backward compatible)
- ✅ No errors in logs for 48 hours
- ✅ Performance unchanged

---

## 🔄 ROLLBACK PROCEDURE

**If something goes wrong:**

```bash
# 1. Stop backend
ssh gzjbbk@192.168.5.12 'docker stop signage-backend'

# 2. Restore database
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < /backup/prod_pre_phase1_*.sql
EOF

# 3. Restart backend (old version)
ssh gzjbbk@192.168.5.12 'docker start signage-backend'

# 4. Verify
curl http://192.168.5.12:8001/health
```

---

## ✅ COMPLETION CHECKLIST

- [ ] Day 1: Local migrations successful
- [ ] Day 2: Backend implementation complete
- [ ] Day 3: Data migration script working
- [ ] Day 4: Staging deployment successful
- [ ] Day 5: Production deployment successful
- [ ] Day 6-7: Stable for 48 hours

**Once all checked, proceed to Phase 2!**

---

## 📞 NEED HELP?

If you encounter issues:
1. Check logs: `docker logs signage-backend`
2. Check database: `docker exec -it signage-postgres psql -U signage_user -d signage_db`
3. Run verification script: `/tmp/verify_phase1.sql`
4. Rollback if needed: Use rollback procedure above

---

**Phase 1 Complete! Ready for Phase 2: Content Management** 🚀
