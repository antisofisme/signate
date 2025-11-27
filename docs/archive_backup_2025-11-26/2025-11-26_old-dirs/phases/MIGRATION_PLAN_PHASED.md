# 🚀 PHASED MIGRATION PLAN
**Complete System Migration: Database + Backend + CMS + Player**

**Created:** 2025-01-09
**Target:** Migrate to new database schema with zero downtime
**Timeline:** 8-10 weeks (can be shortened to 5-6 weeks for MVP)

---

## 📋 OVERVIEW

### Current Architecture (Before Migration)
```
┌─────────────────────────────────────────────────────────────┐
│ CURRENT SYSTEM (Production)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │ web-admin    │──────│ backend      │─────│ PostgreSQL │ │
│  │ (React/Next) │      │ (Node.js)    │     │ (Old)      │ │
│  └──────────────┘      └──────────────┘     └────────────┘ │
│                                                              │
│  ┌──────────────┐                                           │
│  │ player       │                                           │
│  │ (vanillaJS)  │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture (After Migration)
```
┌─────────────────────────────────────────────────────────────┐
│ NEW SYSTEM (Target)                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │ cms-vite     │──────│ backend-     │─────│ PostgreSQL │ │
│  │ (React/Vite) │      │ python       │     │ (New)      │ │
│  │              │      │ (FastAPI)    │     │ +Migrations│ │
│  └──────────────┘      └──────────────┘     └────────────┘ │
│                               │                             │
│  ┌──────────────┐            │                             │
│  │ player-vite  │────────────┘                             │
│  │ (React/Vite) │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 MIGRATION PHASES

### Phase 0: Preparation & Setup (Week 1)
### Phase 1: Foundation - Core Tables (Week 2)
### Phase 2: Content Management (Week 3-4)
### Phase 3: Security & Multi-Tenant (Week 5)
### Phase 4: Device Management (Week 6-7)
### Phase 5: Advanced Features (Week 8-9)
### Phase 6: Performance & Production (Week 10)

---

## 📅 PHASE 0: PREPARATION & SETUP

**Duration:** 1 week
**Risk Level:** None
**Downtime:** 0 minutes

### Objectives
- ✅ Backup all data
- ✅ Setup staging environment
- ✅ Document current system
- ✅ Prepare rollback plan

### Tasks

#### 1. Database Backup & Documentation
```bash
# Full production backup
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec signage-postgres pg_dump -U signage_user -d signage_db \
    > /backup/pre_migration_$(date +%Y%m%d_%H%M%S).sql

  # Verify backup
  ls -lh /backup/pre_migration_*.sql

  # Document current schema
  docker exec signage-postgres pg_dump -U signage_user -d signage_db --schema-only \
    > /backup/current_schema.sql
EOF
```

#### 2. Setup Staging Environment
```bash
# Create staging database
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -i signage-postgres psql -U postgres << SQL
    CREATE DATABASE signage_db_staging;
    GRANT ALL PRIVILEGES ON DATABASE signage_db_staging TO signage_user;
SQL

  # Copy production data to staging
  docker exec signage-postgres pg_dump -U signage_user signage_db | \
  docker exec -i signage-postgres psql -U signage_user signage_db_staging
EOF
```

#### 3. Document Current Features
```bash
# Create feature inventory
cat > /mnt/g/khoirul/signate/docs/CURRENT_FEATURES.md << 'EOF'
# Current System Features

## Web Admin (web-admin)
- [ ] User login/logout
- [ ] Device registration
- [ ] Device monitoring (online/offline)
- [ ] Content upload (image/video)
- [ ] Playlist management
- [ ] Device assignment
- [ ] Dashboard analytics

## Player (player-vanillajs)
- [ ] Device activation (6-digit code)
- [ ] Heartbeat mechanism (30s)
- [ ] Content playback
- [ ] Playlist rotation
- [ ] Speed test
- [ ] Remote logging

## Backend (backend / backend-python)
- [ ] JWT authentication
- [ ] Device API
- [ ] Content API
- [ ] Playlist API
- [ ] WebSocket for real-time updates
EOF
```

#### 4. Setup Feature Flags
```typescript
// cms-vite/src/config/features.ts
export const FEATURES = {
  // Phase 1: Foundation
  RBAC_SYSTEM: false,
  SESSION_MANAGEMENT: false,

  // Phase 2: Content
  CONTENT_ANALYTICS: false,
  PLAYBACK_LOGS: false,

  // Phase 3: Security
  ROW_LEVEL_SECURITY: false,

  // Phase 4: Device
  DEVICE_GROUPS: false,
  DEVICE_LOGS: false,

  // Phase 5: Advanced
  CONTENT_VERSIONS: false,
  AUDIT_LOGS: false,
} as const
```

### Deliverables
- ✅ Full database backup
- ✅ Staging environment ready
- ✅ Current features documented
- ✅ Feature flags implemented
- ✅ Rollback plan documented

---

## 📅 PHASE 1: FOUNDATION - CORE TABLES

**Duration:** 1 week
**Risk Level:** Low
**Downtime:** < 5 minutes (for migration execution)

### Objectives
- ✅ Create roles table (RBAC system)
- ✅ Create user_sessions table
- ✅ Fix device defaults
- ✅ Fix soft delete constraints
- ✅ **NO frontend changes** (backend preparation only)

### Database Migrations
```
010_create_roles_table.sql
011_create_user_sessions_table.sql
012_fix_device_defaults_consistency.sql
013_fix_soft_delete_unique_constraints.sql
```

### Backend Changes (backend-python)

#### 1.1. Update Models
```python
# backend-python/services/auth/models.py

# ADD: Role model
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    is_system_role = Column(Boolean, default=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    permissions = Column(JSONB)

    # Relationships
    users = relationship("User", back_populates="role")

# UPDATE: User model
class User(Base):
    # ADD:
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")

    # DEPRECATE (but keep for backward compatibility):
    # old_role = Column(String(20))  # Keep this temporarily

# ADD: Session model
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String(255), unique=True)
    device_info = Column(JSONB)
    ip_address = Column(String(45))
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime, nullable=True)
```

#### 1.2. Create RBAC Service
```python
# backend-python/services/auth/rbac_service.py

from typing import List, Optional
from sqlalchemy.orm import Session
from .models import Role, User

class RBACService:
    def __init__(self, db: Session):
        self.db = db

    def create_role(
        self,
        name: str,
        permissions: dict,
        organization_id: Optional[int] = None
    ) -> Role:
        """Create new role"""
        role = Role(
            name=name,
            permissions=permissions,
            organization_id=organization_id,
            is_system_role=(organization_id is None)
        )
        self.db.add(role)
        self.db.commit()
        return role

    def assign_role(self, user_id: int, role_id: int):
        """Assign role to user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.role_id = role_id
            self.db.commit()

    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        if not user.role:
            return False

        permissions = user.role.permissions or {}
        return permissions.get(permission, False)

    def migrate_old_roles(self):
        """Migrate from old string roles to new RBAC"""
        # Create system roles if not exist
        system_roles = {
            "SUPER_ADMIN": ["*"],  # All permissions
            "ADMIN": ["content.*", "device.*", "playlist.*"],
            "VIEWER": ["content.read", "device.read", "playlist.read"]
        }

        for role_name, permissions in system_roles.items():
            existing = self.db.query(Role).filter(
                Role.name == role_name,
                Role.is_system_role == True
            ).first()

            if not existing:
                self.create_role(
                    name=role_name,
                    permissions={p: True for p in permissions},
                    organization_id=None
                )
```

#### 1.3. Update Session Management
```python
# backend-python/services/auth/session_service.py

from datetime import datetime, timedelta
from typing import Optional
from .models import UserSession
import secrets

class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: int,
        device_info: dict,
        ip_address: str,
        expires_in_days: int = 30
    ) -> UserSession:
        """Create new session"""
        session_token = secrets.token_urlsafe(32)

        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            created_at=datetime.utcnow()
        )

        self.db.add(session)
        self.db.commit()
        return session

    def validate_session(self, session_token: str) -> Optional[UserSession]:
        """Validate session token"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.utcnow()
        ).first()

        return session

    def revoke_session(self, session_token: str):
        """Revoke specific session (logout)"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()

        if session:
            session.revoked_at = datetime.utcnow()
            self.db.commit()

    def revoke_all_sessions(self, user_id: int):
        """Revoke all sessions for user (logout all devices)"""
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None)
        ).update({"revoked_at": datetime.utcnow()})
        self.db.commit()
```

### Frontend Changes (cms-vite)

#### 1.4. NO CHANGES YET
```
✅ Backend changes only in Phase 1
✅ Frontend will be updated in Phase 2
✅ Reason: Establish stable foundation first
```

### Player Changes (player-vite)

#### 1.5. NO CHANGES YET
```
✅ Player not affected by RBAC changes
✅ Player will be updated in Phase 4 (Device Management)
```

### Testing Checklist

```bash
# 1. Run migrations on staging
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/staging

  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/010_create_roles_table.sql

  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/011_create_user_sessions_table.sql

  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/012_fix_device_defaults_consistency.sql

  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/013_fix_soft_delete_unique_constraints.sql
EOF

# 2. Verify tables created
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -it signage-postgres psql -U signage_user -d signage_db_staging -c "
    SELECT table_name FROM information_schema.tables
    WHERE table_name IN ('roles', 'user_sessions');"
EOF

# 3. Test RBAC service
cd /mnt/g/khoirul/signate/backend-python
python3 -m pytest tests/test_rbac_service.py -v

# 4. Test session service
python3 -m pytest tests/test_session_service.py -v

# 5. Verify old CMS still works (backward compatibility)
curl http://192.168.5.12:8001/api/v1/users
# Should still return users even though new tables exist
```

### Deployment Steps

```bash
# PRODUCTION DEPLOYMENT

# 1. Backup production database
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec signage-postgres pg_dump -U signage_user -d signage_db \
    > /backup/pre_phase1_$(date +%Y%m%d_%H%M%S).sql
EOF

# 2. Put maintenance mode (optional - if want to be safe)
# Create maintenance page or use feature flag

# 3. Run migrations (< 5 minutes downtime)
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/prototipe2

  for migration in 010 011 012 013; do
    docker exec -i signage-postgres psql -U signage_user -d signage_db \
      < database/fix-database/migrations/${migration}_*.sql
  done
EOF

# 4. Deploy new backend code
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/prototipe2

  # Sync new backend code
  # (already synced in prep phase)

  # Rebuild backend container
  docker-compose -f docker/docker-compose.yml up -d --build backend-api

  # Wait for backend to be healthy
  sleep 10
  docker logs signage-backend --tail 50
EOF

# 5. Verify deployment
curl http://192.168.5.12:8001/health
curl http://192.168.5.12:8001/api/v1/users

# 6. Run data migration (migrate old roles to new RBAC)
ssh gzjbbk@192.168.5.12 << 'EOF'
  docker exec -it signage-backend python3 -c "
from app.services.auth.rbac_service import RBACService
from app.core.database import get_db

db = next(get_db())
rbac = RBACService(db)
rbac.migrate_old_roles()
print('✅ Old roles migrated to RBAC system')
"
EOF

# 7. Remove maintenance mode
# Enable backend again

# 8. Monitor logs for 1 hour
ssh gzjbbk@192.168.5.12 'docker logs -f signage-backend'
```

### Rollback Plan

```bash
# IF SOMETHING GOES WRONG:

# 1. Restore database backup
ssh gzjbbk@192.168.5.12 << 'EOF'
  # Stop backend to prevent data corruption
  docker stop signage-backend

  # Restore database
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < /backup/pre_phase1_*.sql

  # Restart backend
  docker start signage-backend
EOF

# 2. Verify rollback
curl http://192.168.5.12:8001/health
curl http://192.168.5.12:8001/api/v1/users
```

### Success Criteria
- ✅ All 4 migrations executed successfully
- ✅ Tables created: `roles`, `user_sessions`
- ✅ Old CMS still works (backward compatible)
- ✅ Backend API responses unchanged
- ✅ No errors in logs for 24 hours
- ✅ Performance unchanged (check with monitoring)

### Deliverables
- ✅ 4 database tables created
- ✅ RBAC service implemented
- ✅ Session service implemented
- ✅ Data migration script (old roles → new RBAC)
- ✅ Backward compatibility maintained
- ✅ Production deployment successful

---

## 📅 PHASE 2: CONTENT MANAGEMENT

**Duration:** 2 weeks
**Risk Level:** Medium
**Downtime:** < 5 minutes

### Objectives
- ✅ Add content analytics (playback logs)
- ✅ Performance optimization (composite indexes)
- ✅ Update CMS to show analytics
- ✅ Update player to send playback logs

### Database Migrations
```
014_add_content_playback_logs.sql
015_add_composite_indexes.sql
```

### Backend Changes (backend-python)

#### 2.1. Create Playback Logging Service
```python
# backend-python/services/content/playback_service.py

from datetime import datetime
from sqlalchemy.orm import Session
from app.models import ContentPlaybackLog

class PlaybackService:
    def __init__(self, db: Session):
        self.db = db

    def log_playback(
        self,
        content_id: int,
        device_id: int,
        organization_id: int,
        duration_played: int,
        quality: str = "auto"
    ):
        """Log content playback"""
        log = ContentPlaybackLog(
            content_id=content_id,
            device_id=device_id,
            organization_id=organization_id,
            duration_played=duration_played,
            quality=quality,
            played_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()

    def get_content_stats(self, content_id: int):
        """Get content performance statistics"""
        from sqlalchemy import func

        stats = self.db.query(
            func.count(ContentPlaybackLog.id).label('total_plays'),
            func.count(func.distinct(ContentPlaybackLog.device_id)).label('unique_devices'),
            func.avg(ContentPlaybackLog.duration_played).label('avg_duration')
        ).filter(
            ContentPlaybackLog.content_id == content_id
        ).first()

        return {
            "total_plays": stats.total_plays or 0,
            "unique_devices": stats.unique_devices or 0,
            "avg_duration": float(stats.avg_duration or 0)
        }
```

#### 2.2. Add Analytics Endpoints
```python
# backend-python/services/content/routes.py

from fastapi import APIRouter, Depends
from .playback_service import PlaybackService
from app.core.deps import get_db

router = APIRouter(prefix="/api/v1/contents", tags=["contents"])

@router.post("/{content_id}/playback")
async def log_playback(
    content_id: int,
    device_id: int,
    duration_played: int,
    db: Session = Depends(get_db)
):
    """Log content playback (called by player)"""
    service = PlaybackService(db)
    service.log_playback(
        content_id=content_id,
        device_id=device_id,
        organization_id=...,  # Get from session
        duration_played=duration_played
    )
    return {"status": "logged"}

@router.get("/{content_id}/analytics")
async def get_content_analytics(
    content_id: int,
    db: Session = Depends(get_db)
):
    """Get content analytics"""
    service = PlaybackService(db)
    stats = service.get_content_stats(content_id)
    return stats
```

### Frontend Changes (cms-vite)

#### 2.3. Create Content Analytics Components
```typescript
// cms-vite/src/features/contents/components/ContentAnalytics.tsx

import { useQuery } from '@tanstack/react-query'
import { contentApi } from '../api'
import { Card } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'

interface ContentAnalyticsProps {
  contentId: number
}

export function ContentAnalytics({ contentId }: ContentAnalyticsProps) {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['content-analytics', contentId],
    queryFn: () => contentApi.getAnalytics(contentId),
  })

  if (isLoading) return <div>Loading analytics...</div>

  return (
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <h3>Total Plays</h3>
        <p className="text-3xl font-bold">{analytics?.total_plays || 0}</p>
      </Card>

      <Card>
        <h3>Unique Devices</h3>
        <p className="text-3xl font-bold">{analytics?.unique_devices || 0}</p>
      </Card>

      <Card>
        <h3>Avg Duration</h3>
        <p className="text-3xl font-bold">
          {Math.round(analytics?.avg_duration || 0)}s
        </p>
      </Card>
    </div>
  )
}
```

#### 2.4. Update Content List Page
```typescript
// cms-vite/src/features/contents/pages/ContentListPage.tsx

import { FEATURES } from '@/config/features'
import { ContentAnalytics } from '../components/ContentAnalytics'

export function ContentListPage() {
  const [selectedContent, setSelectedContent] = useState<number | null>(null)

  return (
    <div>
      <ContentList onSelect={setSelectedContent} />

      {FEATURES.CONTENT_ANALYTICS && selectedContent && (
        <ContentAnalytics contentId={selectedContent} />
      )}
    </div>
  )
}
```

#### 2.5. Add API Client
```typescript
// cms-vite/src/features/contents/api/content-api.ts

import { apiClient } from '@/lib/api-client'

export const contentApi = {
  getAnalytics: async (contentId: number) => {
    const { data } = await apiClient.get(`/contents/${contentId}/analytics`)
    return data
  },

  logPlayback: async (contentId: number, deviceId: number, duration: number) => {
    await apiClient.post(`/contents/${contentId}/playback`, {
      device_id: deviceId,
      duration_played: duration
    })
  }
}
```

### Player Changes (player-vite)

#### 2.6. Add Playback Logging
```typescript
// player-vite/src/services/playback-logger.ts

import { apiClient } from './api-client'

export class PlaybackLogger {
  private deviceId: number
  private playbackStartTime: number = 0

  constructor(deviceId: number) {
    this.deviceId = deviceId
  }

  onPlaybackStart(contentId: number) {
    this.playbackStartTime = Date.now()
    console.log(`Started playing content ${contentId}`)
  }

  async onPlaybackEnd(contentId: number) {
    const duration = Math.round((Date.now() - this.playbackStartTime) / 1000)

    try {
      await apiClient.post(`/contents/${contentId}/playback`, {
        device_id: this.deviceId,
        duration_played: duration
      })
      console.log(`Logged playback: ${duration}s`)
    } catch (error) {
      console.error('Failed to log playback:', error)
    }
  }
}
```

#### 2.7. Integrate into Player
```typescript
// player-vite/src/app/Player.tsx

import { PlaybackLogger } from '../services/playback-logger'

export function Player() {
  const deviceId = useDeviceStore((state) => state.deviceId)
  const logger = useMemo(() => new PlaybackLogger(deviceId), [deviceId])

  const handleContentPlay = (content: Content) => {
    logger.onPlaybackStart(content.id)

    // Start playback...
  }

  const handleContentEnd = (content: Content) => {
    logger.onPlaybackEnd(content.id)

    // Next content...
  }

  return (
    <video
      onPlay={() => handleContentPlay(currentContent)}
      onEnded={() => handleContentEnd(currentContent)}
    />
  )
}
```

### Testing Checklist

```bash
# Backend Tests
pytest tests/test_playback_service.py -v
pytest tests/test_content_analytics.py -v

# Frontend Tests
cd cms-vite
npm run test -- ContentAnalytics.test.tsx

# Player Tests
cd player-vite
npm run test -- playback-logger.test.ts

# Integration Tests
# 1. Start player
# 2. Play content for 30 seconds
# 3. Check CMS analytics
# 4. Verify playback logged in database
```

### Deployment Steps

```bash
# 1. Deploy database migrations
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/prototipe2
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < database/fix-database/migrations/014_add_content_playback_logs.sql

  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < database/fix-database/migrations/015_add_composite_indexes.sql
EOF

# 2. Deploy backend
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/prototipe2
  docker-compose -f docker/docker-compose.yml up -d --build backend-api
EOF

# 3. Enable feature flag
# Update cms-vite/src/config/features.ts
# CONTENT_ANALYTICS: true

# 4. Build and deploy CMS
cd /mnt/g/khoirul/signate/cms-vite
npm run build
scp -r dist/* gzjbbk@192.168.5.12:/var/www/cms/

# 5. Deploy player
cd /mnt/g/khoirul/signate/player-vite
npm run build
scp -r dist/* gzjbbk@192.168.5.12:/var/www/player/
```

### Success Criteria
- ✅ Playback logs stored in database
- ✅ CMS shows content analytics
- ✅ Player sends playback events
- ✅ Performance improved (40+ indexes working)
- ✅ No degradation in player performance

### Deliverables
- ✅ Content analytics feature complete
- ✅ 40+ performance indexes created
- ✅ CMS updated with analytics dashboard
- ✅ Player tracking implemented
- ✅ Backend API complete

---

## 📅 PHASE 3-6 SUMMARY

**Due to length constraints, I'll provide condensed versions:**

### PHASE 3: Security & Multi-Tenant (Week 5)
- Migration 016: RLS policies
- Backend: RLS middleware
- CMS: Organization switcher (super admin only)
- Player: No changes

### PHASE 4: Device Management (Week 6-7)
- Device logs & speed tests (already exists!)
- CMS: Device logs viewer
- CMS: Speed test history chart
- Player: Enhanced logging & speed test

### PHASE 5: Advanced Features (Week 8-9 - OPTIONAL)
- Migration 017-019: Device groups, versions, audit
- CMS: Optional advanced features
- Player: No changes

### PHASE 6: Performance (Week 10)
- Migration 020: PgBouncer
- Infrastructure: Connection pooling
- CMS: Performance monitoring dashboard
- Player: No changes

---

## 📊 SUMMARY TABLE

| Phase | Duration | DB Migrations | Backend Changes | CMS Changes | Player Changes | Risk | Can Skip? |
|-------|----------|---------------|-----------------|-------------|----------------|------|-----------|
| 0 | 1 week | 0 | Setup | Setup | Setup | None | ❌ No |
| 1 | 1 week | 010-013 | RBAC + Sessions | None | None | Low | ❌ No |
| 2 | 2 weeks | 014-015 | Analytics API | Analytics UI | Playback logs | Medium | ❌ No |
| 3 | 1 week | 016 | RLS middleware | Org switcher | None | High | ❌ No |
| 4 | 2 weeks | - | Device APIs | Device logs UI | Enhanced logs | Medium | ⚠️ Partial |
| 5 | 2 weeks | 017-019 | Advanced APIs | Advanced UI | None | Low | ✅ Yes |
| 6 | 1 week | 020 | None | None | None | Low | ⚠️ Recommended |

**Total: 10 weeks (full) or 7 weeks (MVP = skip Phase 5)**

---

## 🎯 QUICK START (Minimum Viable Migration)

**If you want to get started quickly:**

1. **Week 1:** Phase 0 (Prep)
2. **Week 2:** Phase 1 (Foundation)
3. **Week 3-4:** Phase 2 (Content Analytics)
4. **Week 5:** Phase 3 (Security)
5. **Week 6:** Phase 6 (Performance - just PgBouncer)

**Skip:** Phase 4-5 (can add later when needed)

---

## ✅ NEXT STEPS

Choose your approach:
1. **Full Migration (10 weeks):** Complete all phases
2. **MVP Migration (7 weeks):** Skip Phase 4-5
3. **Quick Start (6 weeks):** Phases 0,1,2,3,6 only

Would you like me to create:
- [ ] Detailed implementation guide for Phase 1?
- [ ] Test scripts for each phase?
- [ ] Deployment automation scripts?
- [ ] Monitoring & alerting setup?
