# 🗄️ DATABASE SCHEMA REVIEW & OPTIMIZATION
**Comprehensive Multi-Tenant Digital Signage System Analysis**

Date: 2025-01-09
Reviewer: Database Architect AI
Focus: Multi-Tenant Architecture (NO Finance Features)

---

## 📊 CURRENT SCHEMA INVENTORY

### Core Tables (Phase 1 - Authentication & Multi-Tenancy)
1. **organizations** - Multi-tenant root entity
2. **users** - Admin users with role-based access
3. **audit_logs** - System-wide activity tracking

### Content Management (Phase 3)
4. **contents** - Media files (images, videos, audio) with transcoding
5. **tags** - Content categorization system
6. **content_tags** - Many-to-many junction table

### Device Management (Phase 2)
7. **devices** - TV/Monitor registration and monitoring
8. **device_tags** - Many-to-many junction table
9. **device_commands** - Remote command queue
10. **device_logs** - Remote debugging logs
11. **device_speed_tests** - Network monitoring history

### Playlist System (Phase 4)
12. **playlists** - Content playback groups
13. **playlist_contents** - Many-to-many junction table
14. **playlist_assignments** - Polymorphic (device OR tag)

### Content Distribution
15. **content_assignments** - Direct device-content mapping (Priority 1)

**Total: 15 tables** (Good for MVP, scalable architecture)

---

## ✅ SCHEMA STRENGTHS (What's GOOD)

### 1. Multi-Tenancy Design ✅
- **organization_id** present in ALL multi-tenant tables
- **CASCADE DELETE** on organization removal (clean data isolation)
- **Proper indexing** on organization_id columns
- **Row-Level Security ready** (can add RLS policies later)

**Tables with Multi-Tenancy:**
```sql
✅ users (organization_id)
✅ contents (organization_id)
✅ tags (organization_id)
✅ devices (organization_id)
✅ playlists (organization_id)
✅ device_commands (organization_id)
✅ device_logs (organization_id)
✅ device_speed_tests (organization_id)
```

### 2. Audit Trail System ✅
- **audit_logs** table for compliance and debugging
- **Soft deletes** via `deleted_at` timestamp (playlists, contents, tags)
- **User tracking**: `created_by`, `updated_by`, `assigned_by` columns
- **Timestamp tracking**: `created_at`, `updated_at` everywhere

### 3. Normalization Level ✅
- **3NF (Third Normal Form)** achieved
- No redundant data storage
- Proper use of foreign keys
- Junction tables for many-to-many relationships

### 4. Indexing Strategy ✅
**Well-indexed for common queries:**
- Organization-scoped queries (idx_*_organization)
- Status filtering (idx_devices_status, idx_playlists_is_active)
- Lookup by unique codes (idx_devices_unique_code)
- Time-based queries (idx_logs_timestamp DESC)
- Composite indexes for complex queries

### 5. Data Integrity ✅
- **Foreign key constraints** with proper ON DELETE actions
- **CHECK constraints** for enum validation (status, device_type, privacy_mode)
- **UNIQUE constraints** to prevent duplicates
- **NOT NULL constraints** on critical fields

### 6. Polymorphic Assignments ✅
**playlist_assignments** supports flexible routing:
- Assign to individual device: `device_id NOT NULL, tag_id NULL`
- Assign to tag (group): `device_id NULL, tag_id NOT NULL`
- **CHECK constraint** ensures mutually exclusive assignment

---

## ⚠️ SCHEMA ISSUES & RECOMMENDATIONS

### 🔴 CRITICAL ISSUES

#### 1. MISSING TABLE: `roles` (RBAC System)
**Current:** Users have hardcoded `role` VARCHAR(20) field
**Problem:**
- ❌ No granular permissions system
- ❌ Cannot define custom roles per organization
- ❌ No permission management UI
- ❌ Limited to basic ADMIN/USER roles

**Recommendation:** Add proper RBAC (Role-Based Access Control)

**New Tables Needed:**
```sql
-- Table: roles
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(200),
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    is_system_role BOOLEAN DEFAULT FALSE NOT NULL, -- TRUE for SUPER_ADMIN, ADMIN
    permissions JSONB NOT NULL, -- e.g., {"devices": ["read", "write"], "content": ["read"]}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT unique_role_name_per_org UNIQUE (organization_id, name)
);

-- Index for role lookup
CREATE INDEX idx_roles_organization ON roles(organization_id);

-- Migrate users table
ALTER TABLE users
    ADD COLUMN role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    ALTER COLUMN role DROP NOT NULL; -- Keep for backward compatibility

-- Create default roles
INSERT INTO roles (name, organization_id, is_system_role, permissions) VALUES
('SUPER_ADMIN', NULL, TRUE, '{"all": "*"}'),
('ADMIN', NULL, TRUE, '{"devices": ["read", "write"], "content": ["read", "write"], "users": ["read", "write"]}'),
('VIEWER', NULL, TRUE, '{"devices": ["read"], "content": ["read"]}');
```

**Benefits:**
- ✅ Organization-specific custom roles
- ✅ Fine-grained permission control
- ✅ Easier to add new permission types
- ✅ Better security and compliance

---

#### 2. INCONSISTENT PIN LENGTH (CRITICAL - Already Fixed!)
**Current State:** ✅ **FIXED** via migration 009
- organizations.organization_pin → VARCHAR(6) ✅
- Backend model updated ✅
- Player integration complete ✅

**Action:** Run migration 009 on production database ASAP

---

#### 3. MISSING TABLE: `user_sessions` (Session Management)
**Current:** JWT tokens stored client-side only
**Problem:**
- ❌ Cannot revoke tokens server-side
- ❌ No session timeout management
- ❌ Cannot see active user sessions
- ❌ No "logout all devices" functionality

**Recommendation:** Add session tracking table

```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Session identification
    session_token VARCHAR(64) NOT NULL UNIQUE, -- SHA256 of JWT
    refresh_token VARCHAR(64) UNIQUE, -- For token refresh

    -- Client metadata
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(500),
    device_info JSONB, -- Browser, OS, etc.

    -- Session lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE, -- Manual logout/revocation

    -- Session type
    session_type VARCHAR(20) DEFAULT 'web' CHECK (session_type IN ('web', 'api', 'mobile'))
);

-- Indexes
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_sessions_active ON user_sessions(user_id, revoked_at) WHERE revoked_at IS NULL;

COMMENT ON TABLE user_sessions IS 'Active user sessions for token management and security';
```

**Benefits:**
- ✅ Server-side session revocation
- ✅ "Logout all devices" feature
- ✅ Security audit trail
- ✅ Detect suspicious login patterns

---

#### 4. NO CONTENT VERSIONING SYSTEM
**Current:** Contents can be updated, but no history
**Problem:**
- ❌ Cannot rollback content changes
- ❌ No diff/comparison between versions
- ❌ Lost metadata when content updated
- ❌ Difficult to track content evolution

**Recommendation:** Add content versioning (Optional - for future Phase)

```sql
CREATE TABLE content_versions (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,

    -- Snapshot of content at this version
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,

    -- Change tracking
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    change_reason VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    CONSTRAINT unique_content_version UNIQUE (content_id, version_number)
);

-- Index for version history lookup
CREATE INDEX idx_versions_content ON content_versions(content_id, version_number DESC);

COMMENT ON TABLE content_versions IS 'Content version history for rollback and audit';
```

**Benefits:**
- ✅ Content rollback capability
- ✅ Change tracking and accountability
- ✅ Compare versions side-by-side
- ✅ Compliance for regulated industries

---

### 🟡 MEDIUM PRIORITY ISSUES

#### 5. MISSING: Playlist Scheduling System Enhancement
**Current:** `playlists.schedule` is JSONB (flexible but unstructured)
**Problem:**
- ❌ No validation for schedule format
- ❌ Difficult to query by schedule
- ❌ Cannot efficiently find "what's playing now"

**Recommendation:** Consider adding structured schedule table (Alternative approach)

```sql
CREATE TABLE playlist_schedules (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,

    -- Time-based scheduling
    day_of_week INTEGER[] CHECK (day_of_week <@ ARRAY[0,1,2,3,4,5,6]), -- 0=Sunday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,

    -- Date range
    valid_from DATE,
    valid_until DATE,

    -- Recurrence
    recurrence_type VARCHAR(20) CHECK (recurrence_type IN ('daily', 'weekly', 'monthly', 'once')),

    -- Priority within time slot
    priority INTEGER DEFAULT 0 NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for time-based queries
CREATE INDEX idx_schedules_playlist ON playlist_schedules(playlist_id);
CREATE INDEX idx_schedules_time ON playlist_schedules(start_time, end_time);
CREATE INDEX idx_schedules_active ON playlist_schedules(valid_from, valid_until);

COMMENT ON TABLE playlist_schedules IS 'Structured playlist scheduling (alternative to JSONB)';
```

**Trade-off:**
- ✅ Better query performance
- ✅ Structured data validation
- ❌ Less flexible than JSONB
- ❌ More complex schema

**Decision:** Keep JSONB for MVP, add structured table in Phase 5 if needed

---

#### 6. MISSING: Device Grouping System
**Current:** Devices can only be grouped via tags
**Problem:**
- ❌ Tags are shared with content (namespace collision)
- ❌ No hierarchical device organization (e.g., Floor 1 > Room 101)
- ❌ Cannot apply group-level settings

**Recommendation:** Add device groups table (Optional - for hotel/enterprise)

```sql
CREATE TABLE device_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(200),
    parent_group_id INTEGER REFERENCES device_groups(id) ON DELETE CASCADE, -- Hierarchical

    -- Multi-tenancy
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Group settings (inherit to child devices)
    default_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL,
    default_rotation INTEGER DEFAULT 0 CHECK (rotation IN (0, 90, 180, 270)),
    default_volume_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT unique_group_name_per_org UNIQUE (organization_id, name)
);

-- Link devices to groups
CREATE TABLE device_group_members (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,

    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_device_group UNIQUE (device_id, group_id)
);

-- Indexes
CREATE INDEX idx_groups_organization ON device_groups(organization_id);
CREATE INDEX idx_groups_parent ON device_groups(parent_group_id);
CREATE INDEX idx_group_members_device ON device_group_members(device_id);
CREATE INDEX idx_group_members_group ON device_group_members(group_id);

COMMENT ON TABLE device_groups IS 'Hierarchical device grouping for organization';
```

**Benefits:**
- ✅ Hierarchical organization (Building > Floor > Room)
- ✅ Group-level default settings
- ✅ Separate from tag system (cleaner)
- ✅ Better for hotel/enterprise deployments

**Decision:** Add in Phase 6 (Enterprise Features)

---

#### 7. MISSING: Content Analytics & Reporting
**Current:** No tracking of content playback
**Problem:**
- ❌ Cannot see which content is most viewed
- ❌ No proof of playback for ads/compliance
- ❌ No device engagement metrics
- ❌ Cannot optimize content strategy

**Recommendation:** Add playback analytics table

```sql
CREATE TABLE content_playback_logs (
    id SERIAL PRIMARY KEY,

    -- What was played
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL,

    -- Where was it played
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- When and how long
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER, -- Actual play duration

    -- Completion tracking
    completed BOOLEAN DEFAULT FALSE, -- Did it play to the end?
    skip_reason VARCHAR(50), -- If skipped: 'user_skip', 'error', 'schedule_change'

    -- Context
    source VARCHAR(50), -- 'playlist', 'direct_assignment', 'tag_assignment'

    -- Partitioning hint (for time-series optimization)
    -- CREATE PARTITIONS BY RANGE (started_at)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for analytics queries
CREATE INDEX idx_playback_content ON content_playback_logs(content_id, started_at DESC);
CREATE INDEX idx_playback_device ON content_playback_logs(device_id, started_at DESC);
CREATE INDEX idx_playback_organization ON content_playback_logs(organization_id, started_at DESC);
CREATE INDEX idx_playback_date ON content_playback_logs(started_at DESC);

COMMENT ON TABLE content_playback_logs IS 'Content playback tracking for analytics and compliance';
```

**Benefits:**
- ✅ Proof of playback (ad compliance)
- ✅ Content performance metrics
- ✅ Device engagement tracking
- ✅ Data-driven content optimization

**Decision:** Add in Phase 5 (Analytics & Reporting)

---

### 🟢 LOW PRIORITY / NICE-TO-HAVE

#### 8. MISSING: Notification System
For alerting admins about device issues, content expiration, etc.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, -- NULL = org-wide

    type VARCHAR(50) NOT NULL, -- 'device_offline', 'content_expired', 'command_failed'
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,

    -- Resource reference
    resource_type VARCHAR(50), -- 'device', 'content', 'playlist'
    resource_id INTEGER,

    -- Status
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_org ON notifications(organization_id, created_at DESC);
```

**Decision:** Phase 7 (Advanced Features)

---

#### 9. MISSING: File Upload Session Tracking
For resumable uploads, chunk tracking, etc.

```sql
CREATE TABLE upload_sessions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Upload metadata
    filename VARCHAR(255) NOT NULL,
    total_size BIGINT NOT NULL,
    uploaded_size BIGINT DEFAULT 0 NOT NULL,
    chunk_size INTEGER DEFAULT 5242880 NOT NULL, -- 5MB chunks

    -- Status
    status VARCHAR(20) DEFAULT 'uploading' CHECK (status IN ('uploading', 'completed', 'failed', 'cancelled')),
    error_message TEXT,

    -- Temporary storage
    temp_path VARCHAR(500),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL -- Auto-cleanup after 24h
);
```

**Decision:** Phase 8 (Performance Optimizations)

---

## 🗑️ TABLES TO DELETE (Not Applicable)

**NONE** - All current tables serve valid purposes for multi-tenant digital signage system.

All 15 tables are necessary and well-designed.

---

## 🔧 TABLES TO MODIFY

### 1. **users** table - Add RBAC support
```sql
-- Add role_id foreign key
ALTER TABLE users
    ADD COLUMN role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL;

-- Migrate existing roles to new system
-- UPDATE users SET role_id = (SELECT id FROM roles WHERE name = users.role);

-- Keep old role column for backward compatibility (can drop after migration)
COMMENT ON COLUMN users.role IS 'DEPRECATED - Use role_id instead';
```

---

### 2. **devices** table - Fix inconsistent defaults
**Issue:** Migration 004 changed defaults, but inconsistent with model

```sql
-- Standardize defaults (match model expectations)
ALTER TABLE devices
    ALTER COLUMN location_type SET DEFAULT 'guest_room', -- Match migration 006
    ALTER COLUMN privacy_mode SET DEFAULT 'limited', -- Match migration 006
    ALTER COLUMN supports_personalization SET DEFAULT TRUE, -- Match migration 006
    ALTER COLUMN volume_enabled SET DEFAULT TRUE; -- Match migration 006

-- Migration 004 had conflicting values - needs reconciliation
```

**Recommendation:** Run consistency check migration

---

### 3. **playlists** table - Fix soft delete constraint
**Issue:** UNIQUE constraint includes `deleted_at`, but should allow same name after delete

```sql
-- Drop existing constraint
ALTER TABLE playlists
    DROP CONSTRAINT unique_playlist_name_per_org;

-- Create partial unique index (only for non-deleted)
CREATE UNIQUE INDEX unique_playlist_name_per_org_active
    ON playlists (organization_id, name)
    WHERE deleted_at IS NULL;

COMMENT ON INDEX unique_playlist_name_per_org_active IS
    'Allows same playlist name to be reused after soft delete';
```

**Same fix needed for:**
- `tags` table (if has deleted_at)
- `contents` table (if has deleted_at)

---

### 4. **playlist_assignments** - Missing created_by tracking
```sql
-- Add user tracking for accountability
ALTER TABLE playlist_assignments
    ADD COLUMN assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX idx_playlist_assignments_assigned_by ON playlist_assignments(assigned_by);

COMMENT ON COLUMN playlist_assignments.assigned_by IS 'User who created this assignment';
```

---

### 5. **device_speed_tests** - Add trigger for auto quality calculation
```sql
-- Function to auto-calculate quality
CREATE OR REPLACE FUNCTION calculate_speed_test_quality()
RETURNS TRIGGER AS $$
BEGIN
    -- Determine quality based on download speed
    NEW.quality := CASE
        WHEN NEW.download_speed >= 25 THEN 'good'
        WHEN NEW.download_speed >= 10 THEN 'fair'
        ELSE 'poor'
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger before insert/update
CREATE TRIGGER set_speed_test_quality
    BEFORE INSERT OR UPDATE ON device_speed_tests
    FOR EACH ROW
    EXECUTE FUNCTION calculate_speed_test_quality();

COMMENT ON FUNCTION calculate_speed_test_quality() IS
    'Auto-calculate speed test quality: good (>=25Mbps), fair (>=10Mbps), poor (<10Mbps)';
```

---

## ➕ NEW TABLES TO ADD (Priority Order)

### Phase 5 (Immediate - Security & Compliance)
1. **roles** - RBAC system (CRITICAL)
2. **user_sessions** - Session management (CRITICAL)
3. **audit_logs** - Already exists ✅

### Phase 6 (Short-term - Analytics)
4. **content_playback_logs** - Analytics & compliance
5. **device_groups** - Hierarchical organization

### Phase 7 (Mid-term - Advanced Features)
6. **content_versions** - Version control
7. **playlist_schedules** - Structured scheduling (alternative)
8. **notifications** - Alert system

### Phase 8 (Long-term - Performance)
9. **upload_sessions** - Resumable uploads
10. **cache_invalidation_logs** - CDN management

---

## 📐 RECOMMENDED ERD (Entity Relationship Diagram)

```
┌─────────────────┐
│  organizations  │◄──────────┬─────────────────────────┐
└────────┬────────┘           │                         │
         │                    │                         │
         │ 1:N                │ 1:N                     │ 1:N
         ▼                    ▼                         ▼
    ┌────────┐          ┌──────────┐            ┌──────────┐
    │ users  │          │ devices  │            │ contents │
    └───┬────┘          └────┬─────┘            └────┬─────┘
        │                    │                       │
        │ 1:N                │ M:N (device_tags)     │ M:N (content_tags)
        ▼                    ▼                       ▼
   ┌──────────┐         ┌──────┐              ┌──────┐
   │audit_logs│         │ tags │◄─────────────┤ tags │
   └──────────┘         └──────┘              └──────┘
                             │                      │
                             │                      │
                             ▼                      ▼
                     ┌───────────────┐      ┌────────────────┐
                     │playlist_assign│      │playlist_contents│
                     └───────┬───────┘      └────────┬───────┘
                             │                       │
                             │ N:1                   │ N:1
                             ▼                       ▼
                        ┌──────────┐           ┌──────────┐
                        │playlists │◄──────────┤playlists │
                        └──────────┘           └──────────┘
```

**Legend:**
- `1:N` = One-to-Many
- `M:N` = Many-to-Many (junction table)
- `◄──` = Foreign Key relationship
- `┌───┐` = Table

---

## 🚀 MIGRATION STRATEGY

### Step 1: Run Pending Migrations (IMMEDIATE)
```bash
# On production server
cd /home/gzjbbk/prototipe2/backend-python/migrations

# Run migration 009 (PIN 6 digits) - CRITICAL
docker exec -i signage-postgres psql -U signage_user -d signage_db < 009_change_organization_pin_to_6_digits.sql

# Verify
docker exec signage-postgres psql -U signage_user -d signage_db -c "
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'organizations' AND column_name = 'organization_pin';
"
```

### Step 2: Add RBAC System (Phase 5A - Week 1)
```bash
# Create roles table
docker exec -i signage-postgres psql -U signage_user -d signage_db < 010_create_roles_table.sql

# Migrate existing users
docker exec -i signage-postgres psql -U signage_user -d signage_db < 011_migrate_users_to_rbac.sql
```

### Step 3: Add Session Management (Phase 5B - Week 1)
```bash
docker exec -i signage-postgres psql -U signage_user -d signage_db < 012_create_user_sessions_table.sql
```

### Step 4: Fix Consistency Issues (Phase 5C - Week 2)
```bash
# Fix device defaults
docker exec -i signage-postgres psql -U signage_user -d signage_db < 013_fix_device_defaults.sql

# Fix soft delete constraints
docker exec -i signage-postgres psql -U signage_user -d signage_db < 014_fix_soft_delete_constraints.sql

# Add missing user tracking
docker exec -i signage-postgres psql -U signage_user -d signage_db < 015_add_assignment_tracking.sql
```

### Step 5: Add Analytics (Phase 6 - Week 3-4)
```bash
docker exec -i signage-postgres psql -U signage_user -d signage_db < 016_create_playback_logs.sql
docker exec -i signage-postgres psql -U signage_user -d signage_db < 017_create_device_groups.sql
```

---

## 📊 INDEXING OPTIMIZATION

### Query Performance Improvements

#### 1. Add Missing Composite Indexes
```sql
-- Fast lookup: "Get all active content for organization by type"
CREATE INDEX idx_contents_org_active_type
    ON contents(organization_id, is_active, content_type)
    WHERE deleted_at IS NULL;

-- Fast lookup: "Get pending commands for device"
CREATE INDEX idx_commands_device_pending
    ON device_commands(device_id, status, created_at DESC)
    WHERE status IN ('pending', 'sent');

-- Fast lookup: "Get recent device logs by level"
CREATE INDEX idx_logs_device_level_recent
    ON device_logs(device_id, log_level, timestamp DESC)
    WHERE timestamp > NOW() - INTERVAL '7 days';
```

#### 2. Add Partial Indexes (Query-Specific)
```sql
-- Only index active users (faster user lookups)
CREATE INDEX idx_users_active
    ON users(organization_id, username)
    WHERE is_active = TRUE;

-- Only index unexpired commands
CREATE INDEX idx_commands_unexpired
    ON device_commands(device_id, status)
    WHERE expires_at > NOW();

-- Only index online devices (last_seen < 5 minutes)
CREATE INDEX idx_devices_online
    ON devices(organization_id, status)
    WHERE last_seen > NOW() - INTERVAL '5 minutes';
```

#### 3. Add JSONB Indexes (for schedule queries)
```sql
-- Index on schedule JSONB column (if using structured queries)
CREATE INDEX idx_playlists_schedule_gin ON playlists USING GIN (schedule);

-- Index on HLS variants JSONB
CREATE INDEX idx_contents_hls_variants_gin ON contents USING GIN (hls_variants);
```

---

## 🔒 SECURITY RECOMMENDATIONS

### 1. Enable Row-Level Security (RLS)
```sql
-- Enable RLS on multi-tenant tables
ALTER TABLE contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE playlists ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (example for contents)
CREATE POLICY contents_isolation ON contents
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);

-- Application must set organization context per request
-- SET LOCAL app.current_organization_id = 123;
```

### 2. Add Database Constraints for Security
```sql
-- Prevent users from accessing other organizations
ALTER TABLE users
    ADD CONSTRAINT check_user_org_match
    CHECK (
        role = 'SUPER_ADMIN' OR
        organization_id IS NOT NULL
    );

-- Ensure devices cannot be assigned to wrong organization's content
ALTER TABLE content_assignments
    ADD CONSTRAINT check_device_content_org_match
    CHECK (
        (SELECT organization_id FROM devices WHERE id = device_id) =
        (SELECT organization_id FROM contents WHERE id = content_id)
    );
```

### 3. Add Audit Triggers
```sql
-- Auto-populate audit_logs on sensitive operations
CREATE OR REPLACE FUNCTION log_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id, organization_id, action, resource_type, resource_id, details
    ) VALUES (
        NEW.id, NEW.organization_id, TG_OP || '.user', 'user', NEW.id,
        jsonb_build_object('old', to_jsonb(OLD), 'new', to_jsonb(NEW))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_users_changes
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION log_user_changes();
```

---

## 📈 SCALABILITY CONSIDERATIONS

### 1. Table Partitioning (for large datasets)
```sql
-- Partition device_logs by month (for high-volume logging)
CREATE TABLE device_logs (
    -- ... existing columns
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE device_logs_2025_01 PARTITION OF device_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE device_logs_2025_02 PARTITION OF device_logs
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Auto-create partitions using extension
CREATE EXTENSION IF NOT EXISTS pg_partman;
```

### 2. Implement Table Archival Strategy
```sql
-- Move old logs to archive table after 90 days
CREATE TABLE device_logs_archive (LIKE device_logs INCLUDING ALL);

-- Scheduled job to archive old data
CREATE OR REPLACE FUNCTION archive_old_logs()
RETURNS void AS $$
BEGIN
    WITH deleted AS (
        DELETE FROM device_logs
        WHERE timestamp < NOW() - INTERVAL '90 days'
        RETURNING *
    )
    INSERT INTO device_logs_archive SELECT * FROM deleted;
END;
$$ LANGUAGE plpgsql;
```

### 3. Add Connection Pooling Configuration
```sql
-- Optimize connection settings in postgresql.conf
-- max_connections = 200
-- shared_buffers = 256MB
-- effective_cache_size = 1GB
-- work_mem = 16MB
-- maintenance_work_mem = 64MB
```

---

## ✅ SUMMARY & ACTION ITEMS

### CRITICAL (Do This Week)
- [x] ✅ **Migration 009** - Change PIN to 6 digits (ALREADY DONE!)
- [ ] 🔴 **Migration 010** - Create `roles` table (RBAC)
- [ ] 🔴 **Migration 011** - Create `user_sessions` table
- [ ] 🔴 **Migration 012** - Fix device defaults consistency
- [ ] 🔴 **Migration 013** - Fix soft delete unique constraints

### HIGH PRIORITY (Next 2 Weeks)
- [ ] 🟡 **Migration 014** - Add `content_playback_logs` table
- [ ] 🟡 **Migration 015** - Add missing `assigned_by` tracking
- [ ] 🟡 Add composite indexes for performance
- [ ] 🟡 Add partial indexes for common queries
- [ ] 🟡 Implement RLS policies

### MEDIUM PRIORITY (Month 1-2)
- [ ] 🟢 **Migration 016** - Add `device_groups` table
- [ ] 🟢 **Migration 017** - Add `content_versions` table
- [ ] 🟢 Add audit triggers for compliance
- [ ] 🟢 Implement table partitioning for logs

### LOW PRIORITY (Future Phases)
- [ ] ⚪ Add `notifications` table
- [ ] ⚪ Add `upload_sessions` table
- [ ] ⚪ Add `playlist_schedules` table (structured)
- [ ] ⚪ Implement connection pooling optimizations

---

## 📝 SCHEMA HEALTH SCORE

**Overall: 8.5/10** ⭐⭐⭐⭐ (Excellent MVP, needs RBAC & sessions)

**Breakdown:**
- ✅ Multi-Tenancy: **10/10** (Perfect isolation)
- ✅ Normalization: **9/10** (Proper 3NF)
- ✅ Indexing: **8/10** (Good, can optimize further)
- ⚠️ Security: **7/10** (Missing RLS, session management)
- ⚠️ RBAC: **5/10** (Basic role field, needs proper RBAC)
- ✅ Audit Trail: **9/10** (Excellent tracking)
- ✅ Scalability: **8/10** (Well-designed, needs partitioning later)
- ⚠️ Analytics: **6/10** (No playback tracking yet)

---

## 🎯 CONCLUSION

Your database schema is **well-designed for a multi-tenant digital signage MVP**. The architecture follows best practices:
- ✅ Clean multi-tenancy with organization_id everywhere
- ✅ Proper normalization (3NF)
- ✅ Good use of foreign keys and constraints
- ✅ Soft deletes and audit tracking
- ✅ Flexible JSONB for complex data (schedules, HLS variants)

**Key Missing Pieces:**
1. **RBAC system** (roles table) - CRITICAL for production
2. **Session management** (user_sessions table) - CRITICAL for security
3. **Playback analytics** (content_playback_logs) - Important for compliance
4. **Device grouping** (device_groups) - Nice-to-have for enterprise

**Next Steps:**
Run the critical migrations (010-013) ASAP, then proceed with Phase 6 enhancements.

---

**Generated:** 2025-01-09
**Reviewed By:** Database Architect AI
**Status:** ✅ Ready for Implementation
