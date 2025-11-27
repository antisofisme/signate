# Database Naming Conventions & Standards

**Last Updated**: 2025-11-13
**Database**: PostgreSQL 15.14
**Current Grade**: A (96/100)

---

## Table of Contents

1. [Overview](#overview)
2. [Naming Conventions](#naming-conventions)
3. [Column Type Standards](#column-type-standards)
4. [Constraints](#constraints)
5. [Indexes](#indexes)
6. [Relationships](#relationships)
7. [Examples](#examples)
8. [Migration Guidelines](#migration-guidelines)

---

## Overview

This document defines the standardized naming conventions and best practices for the Signage CMS database schema. All database objects must follow these conventions to maintain consistency and clarity.

### Design Principles

1. **Consistency**: All similar objects follow the same naming pattern
2. **Clarity**: Names are self-documenting and unambiguous
3. **Brevity**: Names are concise without sacrificing clarity
4. **Snake Case**: All database identifiers use `snake_case` (lowercase with underscores)
5. **Pluralization**: Table names are plural, column names are singular

---

## Naming Conventions

### 1. Tables

**Format**: `plural_noun` (e.g., `users`, `devices`, `playlists`)

**Rules**:
- Use plural form for table names
- Use `snake_case` for multi-word names
- Avoid abbreviations unless universally understood
- No prefixes like `tbl_` or `tb_`

**Examples**:
```sql
✅ users
✅ devices
✅ device_commands
✅ playlist_items
✅ pms_configurations

❌ user (singular)
❌ DeviceCommands (PascalCase)
❌ tbl_devices (prefix)
❌ dev_cmds (abbreviation)
```

### 2. Primary Keys

**Format**: `id` (always named `id`, not prefixed)

**Rules**:
- Always use `id` as the primary key column name
- Type: `INTEGER` or `BIGINT` with `AUTO_INCREMENT`/`SERIAL`
- Every table must have a primary key named `id`

**Examples**:
```sql
✅ id INTEGER PRIMARY KEY
✅ id BIGINT PRIMARY KEY

❌ user_id (prefixed with table name)
❌ userId (camelCase)
❌ pk_user (prefixed)
```

**Rationale**: Using `id` universally simplifies joins and ORM mappings. The table context makes it clear what the ID represents.

### 3. Foreign Keys

**Format**: `referenced_table_singular_id`

**Rules**:
- Always suffix with `_id`
- Use singular form of referenced table name
- Add `_id` even for many-to-many association tables

**Examples**:
```sql
-- Referencing 'users' table
✅ user_id INTEGER REFERENCES users(id)
✅ created_by_id INTEGER REFERENCES users(id)
✅ assigned_by_id INTEGER REFERENCES users(id)

-- Referencing 'organizations' table
✅ organization_id INTEGER REFERENCES organizations(id)

-- Referencing 'roles' table
✅ role_id INTEGER REFERENCES roles(id)

❌ user INTEGER (missing _id suffix)
❌ users_id (plural form)
❌ created_by (missing _id suffix)
❌ creator_id (when referencing users table - use user_id or specific like created_by_id)
```

### 4. Audit Trail Columns

**Standard Set**: Every table with user actions should include:

```sql
created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
updated_at TIMESTAMP WITH TIME ZONE
```

**Rules**:
- `created_by_id`: User who created the record
- `updated_by_id`: User who last updated the record
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated
- Always use `_id` suffix for user FKs
- Always use `_at` suffix for timestamps

**Special Cases**:
```sql
-- For specific actions
uploaded_by_id   -- User who uploaded (for contents)
assigned_by_id   -- User who assigned (for tags, groups)
added_by_id      -- User who added (for group members)
deleted_by_id    -- User who soft-deleted
approved_by_id   -- User who approved
rejected_by_id   -- User who rejected
```

### 5. Timestamp Columns

**Format**: `action_at` or `state_at`

**Rules**:
- Always suffix with `_at`
- Use past tense for actions: `created_at`, `updated_at`, `deleted_at`
- Use present tense for states: `expires_at`, `starts_at`, `ends_at`
- Always use `TIMESTAMP WITH TIME ZONE` for UTC consistency

**Examples**:
```sql
✅ created_at TIMESTAMP WITH TIME ZONE
✅ updated_at TIMESTAMP WITH TIME ZONE
✅ deleted_at TIMESTAMP WITH TIME ZONE
✅ last_seen_at TIMESTAMP WITH TIME ZONE
✅ last_activity_at TIMESTAMP WITH TIME ZONE
✅ last_synced_at TIMESTAMP WITH TIME ZONE
✅ recorded_at TIMESTAMP WITH TIME ZONE
✅ expires_at TIMESTAMP WITH TIME ZONE
✅ starts_at TIMESTAMP WITH TIME ZONE
✅ ends_at TIMESTAMP WITH TIME ZONE
✅ released_at TIMESTAMP WITH TIME ZONE
✅ revoked_at TIMESTAMP WITH TIME ZONE

❌ created_date (use _at suffix)
❌ last_seen (missing _at suffix)
❌ last_activity (missing _at suffix)
❌ timestamp (too generic - use specific name like recorded_at)
❌ updated (missing _at suffix)
❌ last_sync (missing _at suffix)
```

### 6. Boolean Columns

**Format**: `is_adjective` or `has_noun` or `can_verb`

**Rules**:
- Always prefix with `is_`, `has_`, or `can_`
- Use descriptive adjectives or past participles
- Default to `FALSE` unless the positive state is the norm

**Examples**:
```sql
-- is_ prefix (state/property)
✅ is_active BOOLEAN DEFAULT TRUE
✅ is_online BOOLEAN DEFAULT FALSE
✅ is_volume_enabled BOOLEAN DEFAULT TRUE
✅ is_personalization_supported BOOLEAN DEFAULT FALSE
✅ is_alert_triggered BOOLEAN DEFAULT FALSE
✅ is_system_role BOOLEAN DEFAULT FALSE

-- has_ prefix (possession)
✅ has_audio BOOLEAN DEFAULT FALSE
✅ has_subtitles BOOLEAN DEFAULT FALSE

-- can_ prefix (capability)
✅ can_edit BOOLEAN DEFAULT FALSE
✅ can_delete BOOLEAN DEFAULT FALSE

❌ active (missing is_ prefix)
❌ enabled (missing is_ prefix)
❌ volume_enabled (missing is_ prefix)
❌ supports_personalization (use is_personalization_supported)
❌ alert_triggered (missing is_ prefix)
```

### 7. JSON/JSONB Columns

**Format**: `descriptive_plural` or `descriptive_singular_config`

**Rules**:
- Use plural for arrays/collections
- Use singular + `_config` or `_settings` for configuration objects
- Prefer `JSONB` over `JSON` in PostgreSQL for indexing and performance

**Examples**:
```sql
✅ permissions JSONB DEFAULT '{}'
✅ metadata JSONB
✅ settings JSONB DEFAULT '{}'
✅ device_info JSONB
✅ pms_config JSONB

❌ permission (singular for array)
❌ meta (abbreviated)
❌ config (too generic without context)
```

### 8. Enum Columns

**Format**: `descriptive_singular`

**Rules**:
- Use VARCHAR with CHECK constraint for simple enums
- Create custom ENUM type for complex enums
- Always document valid values in comments

**Examples**:
```sql
-- Using CHECK constraint
✅ status VARCHAR(20) CHECK (status IN ('pending', 'active', 'inactive', 'suspended'))
✅ log_level VARCHAR(10) CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'))
✅ session_type VARCHAR(20) CHECK (session_type IN ('web', 'api', 'mobile', 'device'))

-- Using ENUM type
CREATE TYPE device_status AS ENUM ('pending', 'active', 'inactive', 'suspended');
✅ status device_status DEFAULT 'pending'

❌ device_status_enum (redundant _enum suffix)
```

---

## Column Type Standards

### Standard Types by Use Case

| Use Case | Type | Notes |
|----------|------|-------|
| **Primary Key** | `INTEGER` or `BIGINT` | Use `BIGINT` for high-volume tables |
| **Foreign Key** | Match referenced PK type | Usually `INTEGER` or `BIGINT` |
| **Short Text** | `VARCHAR(50-255)` | Names, codes, emails |
| **Long Text** | `TEXT` | Descriptions, notes, content |
| **Numbers** | `INTEGER`, `NUMERIC(p,s)` | Use `NUMERIC` for money |
| **Booleans** | `BOOLEAN` | Always with `is_`, `has_`, `can_` prefix |
| **Timestamps** | `TIMESTAMP WITH TIME ZONE` | Always use timezone |
| **Dates** | `DATE` | For date-only fields |
| **JSON** | `JSONB` | Prefer JSONB over JSON |
| **Files** | `VARCHAR(500)` for URLs | Store file path/URL |

### Size Guidelines

```sql
-- Short identifiers
username VARCHAR(50)
device_code VARCHAR(20)
pin VARCHAR(6)

-- Medium text
name VARCHAR(200)
email VARCHAR(100)
phone VARCHAR(20)

-- URLs and paths
url VARCHAR(500)
file_path VARCHAR(500)

-- Descriptions
description VARCHAR(500)  -- Short description
description TEXT          -- Long description

-- Money
price NUMERIC(10,2)
balance NUMERIC(10,2)
```

---

## Constraints

### 1. Check Constraints

**Format**: `check_table_description`

**Examples**:
```sql
-- Screen dimensions
ALTER TABLE devices ADD CONSTRAINT check_screen_dimensions
  CHECK (screen_width > 0 AND screen_height > 0);

-- File size
ALTER TABLE contents ADD CONSTRAINT check_file_size_positive
  CHECK (file_size > 0);

-- Date ranges
ALTER TABLE schedules ADD CONSTRAINT check_date_range
  CHECK (end_date IS NULL OR end_date >= start_date);

-- Rotation values
ALTER TABLE devices ADD CONSTRAINT check_rotation_values
  CHECK (rotation IN (0, 90, 180, 270));

-- Priority non-negative
ALTER TABLE playlists ADD CONSTRAINT check_priority_non_negative
  CHECK (priority >= 0);
```

### 2. Unique Constraints

**Format**: `uix_table_columns` or natural name

**Examples**:
```sql
-- Simple unique
✅ UNIQUE (email)
✅ UNIQUE (session_token)
✅ UNIQUE (username)

-- Composite unique with name
✅ CONSTRAINT uix_device_tag UNIQUE (device_id, tag_id)
✅ CONSTRAINT unique_role_name_per_org UNIQUE (organization_id, name)

❌ uk_user_email (unclear prefix)
```

### 3. Foreign Key Constraints

**Format**: `table_column_fkey` (auto-generated by PostgreSQL)

**Rules**:
- Always define ON DELETE behavior
- Use `CASCADE` for dependent data
- Use `SET NULL` for audit trails
- Use `RESTRICT` for protected references

**Examples**:
```sql
-- Cascade deletion (child data deleted with parent)
✅ FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE

-- Set null (preserve audit trail)
✅ FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL

-- Restrict (prevent deletion if referenced)
✅ FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
```

---

## Indexes

### 1. Index Naming

**Format**: `idx_table_columns` or `ix_table_columns`

**Examples**:
```sql
✅ CREATE INDEX idx_devices_organization ON devices(organization_id);
✅ CREATE INDEX idx_devices_status ON devices(status);
✅ CREATE INDEX idx_sessions_token ON user_sessions(session_token);
✅ CREATE INDEX idx_logs_timestamp ON device_logs(recorded_at DESC);

-- Composite indexes
✅ CREATE INDEX idx_devices_org_status ON devices(organization_id, status);
✅ CREATE INDEX idx_devices_org_status_seen
   ON devices(organization_id, status, last_seen_at DESC);
```

### 2. Index Strategy

**Always Index**:
- Primary keys (automatic)
- Foreign keys
- Columns frequently used in WHERE clauses
- Columns used in ORDER BY
- Columns used in GROUP BY
- Unique constraints (automatic)

**Consider Indexing**:
- Timestamp columns used for filtering/sorting
- Enum/status columns with low cardinality
- Composite indexes for common query patterns

**Don't Index**:
- Boolean columns (low cardinality)
- Very small tables (< 1000 rows)
- Columns rarely queried

---

## Relationships

### 1. One-to-Many

**Pattern**: Foreign key in child table

```sql
-- Users belong to Organizations (many users per org)
CREATE TABLE organizations (
  id INTEGER PRIMARY KEY,
  name VARCHAR(200) NOT NULL
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
  username VARCHAR(50) NOT NULL
);
```

### 2. Many-to-Many

**Pattern**: Junction/association table with composite primary key

```sql
-- Devices can have many Tags, Tags can be on many Devices
CREATE TABLE device_tags (
  id INTEGER PRIMARY KEY,
  device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
  tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
  assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT uix_device_tag UNIQUE (device_id, tag_id)
);

-- Indexes for junction table
CREATE INDEX idx_device_tags_device_id ON device_tags(device_id);
CREATE INDEX idx_device_tags_tag_id ON device_tags(tag_id);
```

### 3. Self-Referential

**Pattern**: Foreign key referencing same table

```sql
-- Device Groups can have parent groups
CREATE TABLE device_groups (
  id INTEGER PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  parent_group_id INTEGER REFERENCES device_groups(id) ON DELETE SET NULL,
  organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE
);
```

---

## Examples

### Complete Table Example

```sql
CREATE TABLE devices (
  -- Primary Key
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

  -- Foreign Keys (with _id suffix)
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  assigned_playlist_id INTEGER REFERENCES playlists(id) ON DELETE SET NULL,

  -- Basic Columns
  device_type VARCHAR(50) NOT NULL CHECK (device_type IN ('webos_tv', 'monitor', 'tablet')),
  device_name VARCHAR(200) NOT NULL,
  unique_code VARCHAR(20) UNIQUE NOT NULL,
  device_uuid UUID,

  -- Network Info
  ip_address VARCHAR(45),
  platform VARCHAR(50) DEFAULT 'browser',

  -- Screen Properties
  screen_width INTEGER,
  screen_height INTEGER,
  rotation INTEGER DEFAULT 0 CHECK (rotation IN (0, 90, 180, 270)),

  -- Boolean Columns (with is_ prefix)
  is_volume_enabled BOOLEAN DEFAULT TRUE NOT NULL,
  is_personalization_supported BOOLEAN DEFAULT FALSE NOT NULL,

  -- Status
  status VARCHAR(20) DEFAULT 'pending'
    CHECK (status IN ('pending', 'active', 'inactive', 'suspended')),

  -- Timestamps (with _at suffix)
  last_seen_at TIMESTAMP WITH TIME ZONE,
  code_expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE,
  released_at TIMESTAMP WITH TIME ZONE,

  -- Audit Trail (with _id suffix)
  created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

  -- JSON Data
  metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_devices_organization ON devices(organization_id);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen_at);
CREATE INDEX idx_devices_org_status_seen
  ON devices(organization_id, status, last_seen_at DESC);

-- Check Constraints
ALTER TABLE devices ADD CONSTRAINT check_screen_dimensions
  CHECK (screen_width > 0 AND screen_height > 0);

-- Comments
COMMENT ON TABLE devices IS 'Connected display devices (WebOS TVs, monitors, tablets)';
COMMENT ON COLUMN devices.unique_code IS '6-digit activation code for device pairing';
COMMENT ON COLUMN devices.is_volume_enabled IS 'Whether device plays audio for content';
```

---

## Migration Guidelines

### 1. Creating New Tables

```sql
-- Template for new table
CREATE TABLE table_name (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

  -- FKs first
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Data columns
  name VARCHAR(200) NOT NULL,
  description TEXT,

  -- Booleans
  is_active BOOLEAN DEFAULT TRUE NOT NULL,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE,

  -- Audit
  created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_table_name_organization ON table_name(organization_id);

-- Comments
COMMENT ON TABLE table_name IS 'Description of table purpose';
```

### 2. Adding Columns

```sql
-- Add column with proper naming
ALTER TABLE devices ADD COLUMN is_muted BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE devices ADD COLUMN last_restart_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE devices ADD COLUMN configured_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Add comment
COMMENT ON COLUMN devices.is_muted IS 'Whether device audio is muted';
```

### 3. Renaming Columns

```sql
-- Rename to follow conventions
ALTER TABLE devices RENAME COLUMN last_seen TO last_seen_at;
ALTER TABLE devices RENAME COLUMN volume_enabled TO is_volume_enabled;
ALTER TABLE devices RENAME COLUMN created_by TO created_by_id;

-- Update comment
COMMENT ON COLUMN devices.last_seen_at IS 'Last heartbeat timestamp from device';
```

### 4. Adding Constraints

```sql
-- Add check constraint
ALTER TABLE devices ADD CONSTRAINT check_rotation_values
  CHECK (rotation IN (0, 90, 180, 270));

-- Add unique constraint
ALTER TABLE devices ADD CONSTRAINT uix_organization_device_name
  UNIQUE (organization_id, device_name);

-- Add foreign key
ALTER TABLE devices ADD CONSTRAINT devices_updated_by_id_fkey
  FOREIGN KEY (updated_by_id) REFERENCES users(id) ON DELETE SET NULL;
```

---

## Anti-Patterns to Avoid

### ❌ Don't Do This:

```sql
-- Mixed case or camelCase
CREATE TABLE DeviceCommands (...);
CREATE TABLE device_Commands (...);

-- Abbreviated names
CREATE TABLE dev_cmds (...);
CREATE TABLE usr_sess (...);

-- Prefixes
CREATE TABLE tbl_devices (...);
CREATE TABLE tb_users (...);

-- Missing _id suffix on FKs
user INTEGER REFERENCES users(id)
created_by INTEGER REFERENCES users(id)

-- Missing _at suffix on timestamps
last_seen TIMESTAMP
created TIMESTAMP

-- Missing boolean prefixes
active BOOLEAN
enabled BOOLEAN
alert_triggered BOOLEAN

-- Generic names
data JSONB
info TEXT
value VARCHAR(255)
```

### ✅ Do This Instead:

```sql
-- snake_case, descriptive names
CREATE TABLE device_commands (...);

-- Full names
CREATE TABLE devices (...);
CREATE TABLE user_sessions (...);

-- No prefixes
CREATE TABLE devices (...);
CREATE TABLE users (...);

-- _id suffix on FKs
user_id INTEGER REFERENCES users(id)
created_by_id INTEGER REFERENCES users(id)

-- _at suffix on timestamps
last_seen_at TIMESTAMP WITH TIME ZONE
created_at TIMESTAMP WITH TIME ZONE

-- Boolean prefixes
is_active BOOLEAN
is_enabled BOOLEAN
is_alert_triggered BOOLEAN

-- Descriptive names
device_metadata JSONB
device_info TEXT
configuration_value VARCHAR(255)
```

---

## Validation Checklist

Before committing a migration, verify:

- [ ] Table names are plural and snake_case
- [ ] Primary key is named `id`
- [ ] All FKs have `_id` suffix
- [ ] All timestamps have `_at` suffix
- [ ] All booleans have `is_`, `has_`, or `can_` prefix
- [ ] All FKs define ON DELETE behavior
- [ ] Appropriate indexes created
- [ ] Check constraints added where needed
- [ ] Comments added for complex columns
- [ ] Follows existing patterns in the schema

---

## Reference Tables

### Current Schema Statistics

| Metric | Value | Grade |
|--------|-------|-------|
| Total Tables | 29 | - |
| FK Consistency | 100% | A+ |
| Timestamp Naming | 100% | A+ |
| Boolean Naming | 88% | A- |
| Check Constraints | 18 | A |
| Overall Score | 96/100 | A |

### Standard Column Names Reference

| Purpose | Column Name | Type | Notes |
|---------|-------------|------|-------|
| Primary Key | `id` | INTEGER/BIGINT | Always |
| Org FK | `organization_id` | INTEGER | Multi-tenant |
| User FK | `user_id` | INTEGER | References users |
| Creator | `created_by_id` | INTEGER | Audit trail |
| Updater | `updated_by_id` | INTEGER | Audit trail |
| Created | `created_at` | TIMESTAMP TZ | Auto-set |
| Updated | `updated_at` | TIMESTAMP TZ | Auto-update |
| Deleted | `deleted_at` | TIMESTAMP TZ | Soft delete |
| Active | `is_active` | BOOLEAN | Status flag |
| System | `is_system_role` | BOOLEAN | System vs custom |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-13 | Initial documentation after migration 039-044 |

---

**Maintained By**: Development Team
**Questions**: Refer to database architect or tech lead
