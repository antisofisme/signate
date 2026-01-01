# DEVELOPMENT STANDARDS V14

> Standards #45: Internal Collaboration Hub (ICH)

---

## Standard #45: Internal Collaboration Hub (ICH)

### 45.1 Overview

**ICH (Internal Collaboration Hub)** adalah Cross-Module Add-on yang menyediakan platform komunikasi dan kolaborasi internal untuk seluruh organisasi.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ICH - Internal Collaboration Hub             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    CHAT     │  │    NOTES    │  │  FLAG &     │             │
│  │   ENGINE    │  │   ENGINE    │  │  THREAD     │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                         │
│              │   TASK BOARD ENGINE   │                         │
│              └───────────────────────┘                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Works across: PMS, POS, ACC, INV, HRM, PROC, AST, SPA, GYM,   │
│                LDR, CRS, S&C, FDA                               │
└─────────────────────────────────────────────────────────────────┘
```

#### Core Features

| Feature | Description |
|---------|-------------|
| **Messaging** | Real-time chat (DM, group, department channels) |
| **Notes** | Personal, department, and organization notes |
| **Flags & Threads** | Flag any entity, create discussion threads |
| **Task Board** | Track and manage follow-up tasks |
| **Entity Sharing** | Share system entities in chat with permission check |

---

### 45.2 Module Classification

```yaml
Module Code: ich
Module Name: Internal Collaboration Hub
Type: Cross-Module Add-on
Standalone: No (requires at least 1 other module)
Parent Module: None (works across all modules)

Dependencies:
  Required: At least 1 subscribable module
  Optional: FDA (for alert integration)

Subscription Tiers:
  - ICH Basic: Chat + Notes only
  - ICH Pro: Chat + Notes + Flags + Threads
  - ICH Enterprise: Full features + Advanced analytics
```

---

### 45.3 Feature 1: Messaging (Chat)

#### 45.3.1 Chat Types

```
┌─────────────────────────────────────────────────────────────────┐
│                       CHAT TYPES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DIRECT MESSAGE (DM)                                        │
│     • 1-on-1 private conversation                              │
│     • End-to-end encrypted                                      │
│     • Cannot be monitored by admin                              │
│                                                                 │
│  2. GROUP CHAT                                                  │
│     • Custom members (cross-department allowed)                 │
│     • Created by any user                                       │
│     • Admin can add/remove members                              │
│     • Persists until deleted                                    │
│                                                                 │
│  3. DEPARTMENT CHANNEL                                          │
│     • Auto-created per department                               │
│     • All department members auto-joined                        │
│     • Cannot leave (membership follows HR)                      │
│     • Department head = channel admin                           │
│                                                                 │
│  4. ORGANIZATION CHANNEL                                        │
│     • Company-wide announcements                                │
│     • Only designated users can post                            │
│     • All employees are members                                 │
│     • Read receipts available                                   │
│                                                                 │
│  5. CROSS-DEPARTMENT CHANNEL                                    │
│     • Created by managers                                       │
│     • For projects/initiatives spanning departments             │
│     • Example: "Night Audit Team", "VIP Handling"               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.3.2 Chat Features

```python
class ChatFeature(str, Enum):
    """Available chat features"""
    TEXT_MESSAGE = "text"           # Plain text
    RICH_TEXT = "rich_text"         # Formatted text (bold, italic, etc.)
    FILE_ATTACHMENT = "file"        # Upload files
    IMAGE = "image"                 # Image with preview
    VOICE_NOTE = "voice"            # Voice message (optional)
    ENTITY_SHARE = "entity"         # Share system entity
    MENTION_USER = "mention_user"   # @username
    MENTION_DEPT = "mention_dept"   # @department
    MENTION_ALL = "mention_all"     # @all (channel only)
    REACTION = "reaction"           # Emoji reactions
    REPLY = "reply"                 # Reply to specific message
    FORWARD = "forward"             # Forward message
    PIN_MESSAGE = "pin"             # Pin important message
    SEARCH = "search"               # Search message history
```

#### 45.3.3 Entity Sharing in Chat

Users dapat share entity dari module lain ke dalam chat dengan permission check:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTITY SHARING FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User clicks "Share" on any entity                          │
│                     │                                           │
│                     ▼                                           │
│  2. System checks: Can recipient view this entity?             │
│     ┌─────────────────────────────────────────┐                │
│     │ Permission Matrix:                       │                │
│     │ • Same department? → Full details        │                │
│     │ • Cross-dept with permission? → Limited  │                │
│     │ • No permission? → Summary only          │                │
│     │ • Confidential? → Block share            │                │
│     └─────────────────────────────────────────┘                │
│                     │                                           │
│                     ▼                                           │
│  3. Entity Card rendered based on permission                   │
│     ┌─────────────────────────────────────────┐                │
│     │ [Invoice #INV-2024-001]                  │                │
│     │ Guest: John Doe                          │                │
│     │ Amount: Rp 5,000,000                     │                │
│     │ Status: Pending                          │                │
│     │ [View Details] [Create Flag]             │                │
│     └─────────────────────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.3.4 Shareable Entities

```yaml
Shareable Entities:
  PMS:
    - Reservations (booking details)
    - Guest profiles (limited info)
    - Room status
    - Housekeeping tasks

  POS:
    - Transactions (receipts)
    - Orders (for kitchen/service)
    - Table status

  ACC:
    - Invoices
    - Payment receipts
    - Account statements (limited)

  INV:
    - Stock items
    - Purchase requests
    - Receiving documents

  HRM:
    - Employee profiles (limited)
    - Schedules
    - Leave requests

  PROC:
    - Purchase orders
    - Supplier info (limited)
    - Quotations

  AST:
    - Asset info
    - Maintenance requests
    - Work orders

Permission Levels:
  full: All details visible
  limited: Basic info only (no amounts, no sensitive data)
  summary: Just entity type and ID
  blocked: Cannot share (confidential data)
```

#### 45.3.5 Chat Database Schema

```sql
-- Schema: ich (Internal Collaboration Hub)
CREATE SCHEMA IF NOT EXISTS ich;

-- ============================================
-- CHAT TABLES
-- ============================================

-- Chat conversations (channels, groups, DMs)
CREATE TABLE ich.conversations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    conversation_type VARCHAR(20) NOT NULL,  -- dm, group, department, organization, cross_department
    name VARCHAR(200),                        -- NULL for DM
    description TEXT,
    department_id INTEGER,                    -- For department channels
    created_by INTEGER NOT NULL,
    is_archived BOOLEAN NOT NULL DEFAULT false,
    settings JSONB NOT NULL DEFAULT '{}',     -- pinned_messages, mute_settings, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_conversation_type CHECK (
        conversation_type IN ('dm', 'group', 'department', 'organization', 'cross_department')
    )
);

-- Conversation members
CREATE TABLE ich.conversation_members (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES ich.conversations(id),
    user_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'member',  -- admin, moderator, member
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_read_at TIMESTAMPTZ,
    is_muted BOOLEAN NOT NULL DEFAULT false,
    notification_setting VARCHAR(20) NOT NULL DEFAULT 'all',  -- all, mentions, none

    CONSTRAINT uq_conversation_member UNIQUE (conversation_id, user_id),
    CONSTRAINT chk_member_role CHECK (role IN ('admin', 'moderator', 'member'))
);

-- Chat messages
CREATE TABLE ich.messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES ich.conversations(id),
    sender_id INTEGER NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    content TEXT,                             -- Encrypted for DM
    content_encrypted BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB NOT NULL DEFAULT '{}',     -- file_info, entity_info, etc.
    reply_to_id BIGINT REFERENCES ich.messages(id),
    is_edited BOOLEAN NOT NULL DEFAULT false,
    edited_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_message_type CHECK (
        message_type IN ('text', 'rich_text', 'file', 'image', 'voice', 'entity', 'system')
    )
);

-- Create hypertable for messages (TimescaleDB)
SELECT create_hypertable('ich.messages', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Message mentions
CREATE TABLE ich.message_mentions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES ich.messages(id),
    mention_type VARCHAR(20) NOT NULL,        -- user, department, all
    target_id INTEGER,                        -- user_id or department_id
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_mention_type CHECK (mention_type IN ('user', 'department', 'all'))
);

-- Message reactions
CREATE TABLE ich.message_reactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES ich.messages(id),
    user_id INTEGER NOT NULL,
    reaction VARCHAR(50) NOT NULL,            -- emoji code
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_message_reaction UNIQUE (message_id, user_id, reaction)
);

-- Message read receipts (for important channels)
CREATE TABLE ich.message_read_receipts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES ich.messages(id),
    user_id INTEGER NOT NULL,
    read_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_message_read UNIQUE (message_id, user_id)
);

-- Shared entities in chat
CREATE TABLE ich.shared_entities (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id BIGINT NOT NULL REFERENCES ich.messages(id),
    module_code VARCHAR(20) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    permission_level VARCHAR(20) NOT NULL,    -- full, limited, summary
    snapshot JSONB NOT NULL,                  -- Entity data at share time
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_conversations_org ON ich.conversations(organization_id);
CREATE INDEX idx_conversations_dept ON ich.conversations(department_id) WHERE department_id IS NOT NULL;
CREATE INDEX idx_conv_members_user ON ich.conversation_members(user_id);
CREATE INDEX idx_conv_members_conv ON ich.conversation_members(conversation_id);
CREATE INDEX idx_messages_conv ON ich.messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_sender ON ich.messages(sender_id);
CREATE INDEX idx_mentions_target ON ich.message_mentions(mention_type, target_id);
CREATE INDEX idx_shared_entities ON ich.shared_entities(module_code, entity_type, entity_id);
```

---

### 45.4 Feature 2: Notes & Knowledge Base

#### 45.4.1 Note Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                       NOTE LEVELS                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 1: PERSONAL NOTES (Private)                             │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Only creator can see                   │                   │
│  │ • Personal reminders, to-do lists        │                   │
│  │ • Guest preferences notes                │                   │
│  │ • Work notes                             │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Level 2: DEPARTMENT NOTES (Shared in Department)              │
│  ┌─────────────────────────────────────────┐                   │
│  │ • All department members can view        │                   │
│  │ • Edit permission configurable           │                   │
│  │ • SOPs, procedures                       │                   │
│  │ • Department announcements               │                   │
│  │ • Shift handover notes                   │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Level 3: ORGANIZATION NOTES (Company-wide)                    │
│  ┌─────────────────────────────────────────┐                   │
│  │ • All employees can view                 │                   │
│  │ • Edit by designated users only          │                   │
│  │ • Company policies                       │                   │
│  │ • General SOPs                           │                   │
│  │ • Knowledge base articles                │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.4.2 Note Features

```yaml
Note Features:
  Content:
    - Rich text editor (WYSIWYG)
    - Markdown support
    - Code blocks (for technical notes)
    - Tables
    - Checklists
    - File attachments
    - Image embedding

  Organization:
    - Folders / Categories
    - Tags
    - Pin important notes
    - Favorites
    - Search (full-text)

  Collaboration:
    - Comments on notes
    - Version history
    - Restore previous versions
    - Share link (internal only)

  Templates:
    - SOP template
    - Checklist template
    - Meeting notes template
    - Handover notes template
    - Custom templates
```

#### 45.4.3 Notes Database Schema

```sql
-- ============================================
-- NOTES TABLES
-- ============================================

-- Note categories/folders
CREATE TABLE ich.note_categories (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    parent_id INTEGER REFERENCES ich.note_categories(id),
    level VARCHAR(20) NOT NULL,               -- personal, department, organization
    department_id INTEGER,                    -- For department level
    owner_id INTEGER,                         -- For personal level
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_note_level CHECK (level IN ('personal', 'department', 'organization'))
);

-- Notes
CREATE TABLE ich.notes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    category_id INTEGER REFERENCES ich.note_categories(id),
    level VARCHAR(20) NOT NULL,               -- personal, department, organization
    department_id INTEGER,
    owner_id INTEGER NOT NULL,                -- Creator
    title VARCHAR(500) NOT NULL,
    content TEXT,                             -- Rich text / Markdown
    content_format VARCHAR(20) NOT NULL DEFAULT 'markdown',
    tags TEXT[] DEFAULT '{}',
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    is_template BOOLEAN NOT NULL DEFAULT false,
    template_type VARCHAR(50),
    view_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_note_level CHECK (level IN ('personal', 'department', 'organization'))
);

-- Note versions (for history)
CREATE TABLE ich.note_versions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_id BIGINT NOT NULL REFERENCES ich.notes(id),
    version_number INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    changed_by INTEGER NOT NULL,
    change_summary VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_note_version UNIQUE (note_id, version_number)
);

-- Note comments
CREATE TABLE ich.note_comments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_id BIGINT NOT NULL REFERENCES ich.notes(id),
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    parent_id BIGINT REFERENCES ich.note_comments(id),
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Note permissions (for shared notes)
CREATE TABLE ich.note_permissions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    note_id BIGINT NOT NULL REFERENCES ich.notes(id),
    permission_type VARCHAR(20) NOT NULL,     -- user, department, role
    target_id INTEGER NOT NULL,
    can_view BOOLEAN NOT NULL DEFAULT true,
    can_edit BOOLEAN NOT NULL DEFAULT false,
    can_delete BOOLEAN NOT NULL DEFAULT false,
    granted_by INTEGER NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_permission_type CHECK (permission_type IN ('user', 'department', 'role'))
);

-- User favorites
CREATE TABLE ich.note_favorites (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    note_id BIGINT NOT NULL REFERENCES ich.notes(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_note_favorite UNIQUE (user_id, note_id)
);

-- Indexes
CREATE INDEX idx_notes_org_level ON ich.notes(organization_id, level);
CREATE INDEX idx_notes_dept ON ich.notes(department_id) WHERE department_id IS NOT NULL;
CREATE INDEX idx_notes_owner ON ich.notes(owner_id);
CREATE INDEX idx_notes_tags ON ich.notes USING gin(tags);
CREATE INDEX idx_notes_search ON ich.notes USING gin(to_tsvector('indonesian', title || ' ' || COALESCE(content, '')));
CREATE INDEX idx_note_versions ON ich.note_versions(note_id, version_number DESC);
```

---

### 45.5 Feature 3: Flag & Thread System

#### 45.5.1 Flag Types

```
┌─────────────────────────────────────────────────────────────────┐
│                       FLAG TYPES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🚩 ISSUE                                                       │
│     "Ada masalah yang perlu diselesaikan"                      │
│     Example: Discrepancy in stock count                         │
│                                                                 │
│  ❓ QUESTION                                                    │
│     "Perlu klarifikasi atau penjelasan"                        │
│     Example: Why was this discount applied?                     │
│                                                                 │
│  📌 FOLLOW_UP                                                   │
│     "Perlu ditindaklanjuti"                                    │
│     Example: Guest request needs handling                       │
│                                                                 │
│  ℹ️  INFO                                                        │
│     "FYI, untuk diketahui saja"                                │
│     Example: VIP guest arriving tomorrow                        │
│                                                                 │
│  ⚠️  ALERT                                                       │
│     "Perhatian khusus diperlukan"                              │
│     Example: Payment overdue                                    │
│                                                                 │
│  ⭐ IMPORTANT                                                   │
│     "Hal penting untuk diingat"                                │
│     Example: Special rate agreement                             │
│                                                                 │
│  🔍 REVIEW                                                      │
│     "Perlu direview/dicek"                                     │
│     Example: Large transaction needs approval                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.5.2 Flag Visibility (Private by Default)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLAG VISIBILITY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PRIVATE (Default)                                             │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Only creator can see                   │                   │
│  │ • Personal reminder/tracking             │                   │
│  │ • Can upgrade to Department/Org later    │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  DEPARTMENT                                                     │
│  ┌─────────────────────────────────────────┐                   │
│  │ • All department members can see         │                   │
│  │ • Collaborative investigation            │                   │
│  │ • Department head notified               │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  ORGANIZATION                                                   │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Relevant stakeholders can see          │                   │
│  │ • Based on entity type & permissions     │                   │
│  │ • Cross-department collaboration         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  SPECIFIC USERS                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Share with specific users              │                   │
│  │ • Invite to thread                       │                   │
│  │ • Assign responsibility                  │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.5.3 Flag → Thread Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLAG → THREAD FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: CREATE FLAG                                           │
│  ┌─────────────────────────────────────────┐                   │
│  │ User sees suspicious void transaction    │                   │
│  │ Clicks FLAG button                       │                   │
│  │                                          │                   │
│  │ Flag Type: [🚩 Issue        ▼]          │                   │
│  │ Visibility: [🔒 Private     ▼]          │                   │
│  │ Note: [Void 5x dalam 1 jam_______]      │                   │
│  │ Priority: [⚡ High          ▼]          │                   │
│  │ Assign to: [@manager_fnb    ▼]          │                   │
│  │                                          │                   │
│  │ [Cancel]              [Create Flag]      │                   │
│  └─────────────────────────────────────────┘                   │
│                     │                                           │
│                     ▼                                           │
│  Step 2: THREAD AUTO-CREATED                                   │
│  ┌─────────────────────────────────────────┐                   │
│  │ Thread #TH-2024-00123                    │                   │
│  │ Entity: Void Transaction #VD-12345       │                   │
│  │ Status: 🟡 Open                          │                   │
│  │ Priority: ⚡ High                        │                   │
│  │ Assigned: @manager_fnb                   │                   │
│  │ Due: -                                   │                   │
│  │ Watchers: @creator                       │                   │
│  │                                          │                   │
│  │ ─────────────────────────────────────── │                   │
│  │ @creator (just now)                      │                   │
│  │ Created flag: Void 5x dalam 1 jam        │                   │
│  │                                          │                   │
│  │ [View Entity] [Add Comment] [Resolve]    │                   │
│  └─────────────────────────────────────────┘                   │
│                     │                                           │
│                     ▼                                           │
│  Step 3: DISCUSSION & RESOLUTION                               │
│  ┌─────────────────────────────────────────┐                   │
│  │ @manager_fnb (2 hours ago)               │                   │
│  │ Sudah saya cek, ini karena customer      │                   │
│  │ ganti order berkali-kali.                │                   │
│  │                                          │                   │
│  │ @creator (1 hour ago)                    │                   │
│  │ Ok, berarti valid ya. Terima kasih.      │                   │
│  │                                          │                   │
│  │ ─────────────────────────────────────── │                   │
│  │ Resolution: [Valid - Bukan fraud___]     │                   │
│  │                                          │                   │
│  │ [Mark as Resolved]                       │                   │
│  └─────────────────────────────────────────┘                   │
│                     │                                           │
│                     ▼                                           │
│  Step 4: CLOSED                                                │
│  ┌─────────────────────────────────────────┐                   │
│  │ Thread #TH-2024-00123                    │                   │
│  │ Status: ✅ Resolved                      │                   │
│  │ Resolution: Valid - Bukan fraud          │                   │
│  │ Resolved by: @creator                    │                   │
│  │ Resolved at: 2024-01-15 14:30            │                   │
│  │                                          │                   │
│  │ [Reopen] [Archive]                       │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.5.4 Auto-Merge Same Entity Flags

```
┌─────────────────────────────────────────────────────────────────┐
│               AUTO-MERGE SAME ENTITY FLAGS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Scenario: Multiple users flag the same entity                 │
│                                                                 │
│  ┌──────────────┐        ┌──────────────┐                      │
│  │ User A       │        │ User B       │                      │
│  │ flags        │        │ flags        │                      │
│  │ Invoice #123 │        │ Invoice #123 │                      │
│  └──────┬───────┘        └──────┬───────┘                      │
│         │                       │                               │
│         └───────────┬───────────┘                               │
│                     │                                           │
│                     ▼                                           │
│  ┌─────────────────────────────────────────┐                   │
│  │ System detects: Same entity flagged      │                   │
│  │                                          │                   │
│  │ If Thread exists:                        │                   │
│  │ → Add User B as watcher                  │                   │
│  │ → Add User B's note as comment           │                   │
│  │ → Notify User B: "Thread already exists" │                   │
│  │                                          │                   │
│  │ If No Thread (both private):             │                   │
│  │ → Keep separate (private flags)          │                   │
│  │ → Suggest: "Others flagged this too"     │                   │
│  │   (if user upgrades to dept/org)         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Result: Consolidated Thread                                    │
│  ┌─────────────────────────────────────────┐                   │
│  │ Thread #TH-2024-00123                    │                   │
│  │ Entity: Invoice #123                     │                   │
│  │ Flagged by: User A, User B               │                   │
│  │ Watchers: User A, User B, Manager        │                   │
│  │                                          │                   │
│  │ [Discussion continues collaboratively]   │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.5.5 Thread Status Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREAD STATUS FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     ┌────────┐                                                 │
│     │  NEW   │ ←── Flag created, no response yet               │
│     └───┬────┘                                                 │
│         │                                                       │
│         │ Assignee views / comments                             │
│         ▼                                                       │
│     ┌────────────┐                                             │
│     │ IN_PROGRESS│ ←── Being worked on                         │
│     └───┬────────┘                                             │
│         │                                                       │
│         ├─── Needs more info ───► ┌──────────┐                 │
│         │                          │ PENDING  │                 │
│         │                          └────┬─────┘                 │
│         │                               │                       │
│         │ ◄────── Info provided ────────┘                       │
│         │                                                       │
│         │ Resolution found                                      │
│         ▼                                                       │
│     ┌──────────┐                                               │
│     │ RESOLVED │ ←── Issue addressed                           │
│     └───┬──────┘                                               │
│         │                                                       │
│         │ After review period (7 days)                         │
│         ▼                                                       │
│     ┌──────────┐                                               │
│     │ CLOSED   │ ←── Archived, read-only                       │
│     └──────────┘                                               │
│                                                                 │
│     Special: REOPENED                                          │
│     (From RESOLVED back to IN_PROGRESS if issue recurs)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.5.6 Flag & Thread Database Schema

```sql
-- ============================================
-- FLAG & THREAD TABLES
-- ============================================

-- Entity flags
CREATE TABLE ich.flags (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    thread_id BIGINT,                         -- NULL if private, linked when shared

    -- Flag details
    flag_type VARCHAR(20) NOT NULL,
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    note TEXT,

    -- Flagged entity
    module_code VARCHAR(20) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    entity_snapshot JSONB,                    -- Entity data at flag time

    -- Creator & assignment
    created_by INTEGER NOT NULL,
    department_id INTEGER,                    -- Creator's department

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_flag_type CHECK (
        flag_type IN ('issue', 'question', 'follow_up', 'info', 'alert', 'important', 'review')
    ),
    CONSTRAINT chk_flag_visibility CHECK (
        visibility IN ('private', 'department', 'organization', 'specific')
    ),
    CONSTRAINT chk_flag_priority CHECK (
        priority IN ('low', 'medium', 'high', 'urgent')
    )
);

-- Flag specific sharing (for visibility = 'specific')
CREATE TABLE ich.flag_shares (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flag_id BIGINT NOT NULL REFERENCES ich.flags(id),
    share_type VARCHAR(20) NOT NULL,          -- user, department
    target_id INTEGER NOT NULL,
    shared_by INTEGER NOT NULL,
    shared_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_share_type CHECK (share_type IN ('user', 'department'))
);

-- Threads (created when flag is shared or assigned)
CREATE TABLE ich.threads (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    thread_code VARCHAR(50) NOT NULL,         -- TH-2024-00001

    -- Thread details
    title VARCHAR(500),                       -- Auto-generated or custom
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',

    -- Linked entity
    module_code VARCHAR(20) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,

    -- Assignment
    assigned_to INTEGER,
    assigned_department_id INTEGER,
    due_date TIMESTAMPTZ,

    -- Resolution
    resolution_type VARCHAR(50),              -- valid, invalid, fixed, wontfix, duplicate
    resolution_notes TEXT,
    resolved_by INTEGER,
    resolved_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,

    CONSTRAINT uq_thread_code UNIQUE (organization_id, thread_code),
    CONSTRAINT chk_thread_status CHECK (
        status IN ('new', 'in_progress', 'pending', 'resolved', 'closed', 'reopened')
    )
);

-- Thread watchers
CREATE TABLE ich.thread_watchers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id BIGINT NOT NULL REFERENCES ich.threads(id),
    user_id INTEGER NOT NULL,
    watch_type VARCHAR(20) NOT NULL,          -- creator, assignee, mentioned, subscribed
    is_muted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_thread_watcher UNIQUE (thread_id, user_id)
);

-- Thread comments
CREATE TABLE ich.thread_comments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id BIGINT NOT NULL REFERENCES ich.threads(id),
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT false,  -- Internal note (hidden from some watchers)
    is_edited BOOLEAN NOT NULL DEFAULT false,
    edited_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- For reply threading
    parent_id BIGINT REFERENCES ich.thread_comments(id)
);

-- Thread activity log
CREATE TABLE ich.thread_activities (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id BIGINT NOT NULL REFERENCES ich.threads(id),
    user_id INTEGER NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create hypertable for activities
SELECT create_hypertable('ich.thread_activities', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_flags_org ON ich.flags(organization_id);
CREATE INDEX idx_flags_entity ON ich.flags(module_code, entity_type, entity_id);
CREATE INDEX idx_flags_creator ON ich.flags(created_by);
CREATE INDEX idx_flags_visibility ON ich.flags(visibility);
CREATE INDEX idx_threads_org ON ich.threads(organization_id);
CREATE INDEX idx_threads_entity ON ich.threads(module_code, entity_type, entity_id);
CREATE INDEX idx_threads_status ON ich.threads(status);
CREATE INDEX idx_threads_assigned ON ich.threads(assigned_to);
CREATE INDEX idx_thread_watchers ON ich.thread_watchers(user_id);
CREATE INDEX idx_thread_comments ON ich.thread_comments(thread_id, created_at);
```

---

### 45.6 Feature 4: Task Board

#### 45.6.1 Task Sources

```
┌─────────────────────────────────────────────────────────────────┐
│                      TASK SOURCES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. FROM FLAGS (Converted)                                     │
│     ┌───────────────────────────────────────┐                  │
│     │ Flag upgraded to task                  │                  │
│     │ Linked to original entity              │                  │
│     │ Thread history preserved               │                  │
│     └───────────────────────────────────────┘                  │
│                                                                 │
│  2. MANUAL CREATION                                            │
│     ┌───────────────────────────────────────┐                  │
│     │ User creates standalone task           │                  │
│     │ May or may not link to entity          │                  │
│     │ Personal or team task                  │                  │
│     └───────────────────────────────────────┘                  │
│                                                                 │
│  3. FROM FDA ALERTS (Auto - if integrated)                     │
│     ┌───────────────────────────────────────┐                  │
│     │ FDA detects anomaly                    │                  │
│     │ Auto-creates thread + task             │                  │
│     │ Assigned to relevant auditor           │                  │
│     └───────────────────────────────────────┘                  │
│                                                                 │
│  4. FROM SYSTEM EVENTS                                         │
│     ┌───────────────────────────────────────┐                  │
│     │ Scheduled tasks (reminders)            │                  │
│     │ Approval workflows                     │                  │
│     │ Escalation from other modules          │                  │
│     └───────────────────────────────────────┘                  │
│                                                                 │
│  5. FROM CHAT (Quick task)                                     │
│     ┌───────────────────────────────────────┐                  │
│     │ Convert chat message to task           │                  │
│     │ "/task @user Do something by Friday"   │                  │
│     │ Quick task creation from conversation  │                  │
│     └───────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.6.2 Task Board Views

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK BOARD VIEWS                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. MY TASKS                                                   │
│     Tasks assigned to current user                              │
│     ┌─────────────────────────────────────────────────────┐    │
│     │ 📋 My Tasks (12)                    [+ New Task]    │    │
│     │                                                      │    │
│     │ 🔴 Overdue (2)                                      │    │
│     │ • Check void discrepancy - Due: Yesterday           │    │
│     │ • Review supplier invoice - Due: 2 days ago         │    │
│     │                                                      │    │
│     │ 🟡 Due Today (3)                                    │    │
│     │ • Prepare night audit report                        │    │
│     │ • Follow up VIP request                             │    │
│     │ • Verify stock count                                │    │
│     │                                                      │    │
│     │ 🟢 Upcoming (7)                                     │    │
│     │ • ...                                               │    │
│     └─────────────────────────────────────────────────────┘    │
│                                                                 │
│  2. DEPARTMENT TASKS                                           │
│     All tasks in user's department                              │
│                                                                 │
│  3. KANBAN BOARD                                               │
│     ┌───────────┬───────────┬───────────┬───────────┐         │
│     │   TO DO   │ IN PROGRESS│  REVIEW   │   DONE    │         │
│     ├───────────┼───────────┼───────────┼───────────┤         │
│     │ ┌───────┐ │ ┌───────┐ │ ┌───────┐ │ ┌───────┐ │         │
│     │ │Task 1 │ │ │Task 3 │ │ │Task 5 │ │ │Task 7 │ │         │
│     │ └───────┘ │ └───────┘ │ └───────┘ │ └───────┘ │         │
│     │ ┌───────┐ │ ┌───────┐ │           │ ┌───────┐ │         │
│     │ │Task 2 │ │ │Task 4 │ │           │ │Task 8 │ │         │
│     │ └───────┘ │ └───────┘ │           │ └───────┘ │         │
│     └───────────┴───────────┴───────────┴───────────┘         │
│                                                                 │
│  4. LIST VIEW                                                  │
│     Sortable table with filters                                 │
│                                                                 │
│  5. CALENDAR VIEW                                              │
│     Tasks by due date on calendar                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 45.6.3 Task Database Schema

```sql
-- ============================================
-- TASK TABLES
-- ============================================

-- Tasks
CREATE TABLE ich.tasks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    task_code VARCHAR(50) NOT NULL,           -- TSK-2024-00001

    -- Task details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'todo',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',

    -- Source
    source_type VARCHAR(20) NOT NULL,         -- flag, manual, fda, system, chat
    source_id BIGINT,                         -- flag_id, fda_alert_id, etc.
    thread_id BIGINT REFERENCES ich.threads(id),

    -- Linked entity (optional)
    module_code VARCHAR(20),
    entity_type VARCHAR(50),
    entity_id BIGINT,

    -- Assignment
    created_by INTEGER NOT NULL,
    assigned_to INTEGER,
    assigned_department_id INTEGER,

    -- Dates
    due_date TIMESTAMPTZ,
    start_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_task_code UNIQUE (organization_id, task_code),
    CONSTRAINT chk_task_status CHECK (
        status IN ('todo', 'in_progress', 'review', 'done', 'cancelled')
    ),
    CONSTRAINT chk_task_source CHECK (
        source_type IN ('flag', 'manual', 'fda', 'system', 'chat')
    )
);

-- Task checklists (subtasks)
CREATE TABLE ich.task_checklists (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES ich.tasks(id),
    title VARCHAR(500) NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT false,
    completed_by INTEGER,
    completed_at TIMESTAMPTZ,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Task comments
CREATE TABLE ich.task_comments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES ich.tasks(id),
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_edited BOOLEAN NOT NULL DEFAULT false,
    edited_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Task attachments
CREATE TABLE ich.task_attachments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES ich.tasks(id),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100),
    uploaded_by INTEGER NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_tasks_org ON ich.tasks(organization_id);
CREATE INDEX idx_tasks_assigned ON ich.tasks(assigned_to);
CREATE INDEX idx_tasks_status ON ich.tasks(status);
CREATE INDEX idx_tasks_due ON ich.tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_tasks_thread ON ich.tasks(thread_id) WHERE thread_id IS NOT NULL;
CREATE INDEX idx_tasks_entity ON ich.tasks(module_code, entity_type, entity_id)
    WHERE module_code IS NOT NULL;
```

---

### 45.7 API Endpoints

```yaml
# ============================================
# ICH API ENDPOINTS
# ============================================

# Base path: /api/v1/ich

# --------------------------------------------
# CHAT ENDPOINTS
# --------------------------------------------
Chat:
  Conversations:
    GET    /conversations                    # List user's conversations
    POST   /conversations                    # Create conversation (group/dm)
    GET    /conversations/{id}               # Get conversation details
    PUT    /conversations/{id}               # Update conversation
    DELETE /conversations/{id}               # Archive conversation

  Members:
    GET    /conversations/{id}/members       # List members
    POST   /conversations/{id}/members       # Add members
    DELETE /conversations/{id}/members/{uid} # Remove member
    PUT    /conversations/{id}/members/{uid} # Update member role

  Messages:
    GET    /conversations/{id}/messages      # Get messages (paginated)
    POST   /conversations/{id}/messages      # Send message
    PUT    /messages/{id}                    # Edit message
    DELETE /messages/{id}                    # Delete message
    POST   /messages/{id}/reactions          # Add reaction
    DELETE /messages/{id}/reactions/{emoji}  # Remove reaction

  Entity Sharing:
    POST   /conversations/{id}/share-entity  # Share entity in chat
    GET    /share-entity/preview             # Preview entity card

# --------------------------------------------
# NOTES ENDPOINTS
# --------------------------------------------
Notes:
  Categories:
    GET    /notes/categories                 # List categories
    POST   /notes/categories                 # Create category
    PUT    /notes/categories/{id}            # Update category
    DELETE /notes/categories/{id}            # Delete category

  Notes:
    GET    /notes                            # List notes (filtered)
    POST   /notes                            # Create note
    GET    /notes/{id}                       # Get note
    PUT    /notes/{id}                       # Update note
    DELETE /notes/{id}                       # Delete note
    GET    /notes/{id}/versions              # Get version history
    POST   /notes/{id}/restore/{version}     # Restore version

  Collaboration:
    POST   /notes/{id}/comments              # Add comment
    PUT    /notes/{id}/permissions           # Update permissions
    POST   /notes/{id}/favorite              # Add to favorites
    DELETE /notes/{id}/favorite              # Remove from favorites

# --------------------------------------------
# FLAGS & THREADS ENDPOINTS
# --------------------------------------------
Flags:
  GET    /flags                              # List user's flags
  POST   /flags                              # Create flag
  GET    /flags/{id}                         # Get flag details
  PUT    /flags/{id}                         # Update flag
  DELETE /flags/{id}                         # Delete flag (if private)
  POST   /flags/{id}/upgrade                 # Upgrade visibility
  POST   /flags/{id}/share                   # Share with specific users

Threads:
  GET    /threads                            # List threads (filtered)
  GET    /threads/{id}                       # Get thread details
  PUT    /threads/{id}                       # Update thread
  POST   /threads/{id}/comments              # Add comment
  PUT    /threads/{id}/assign                # Assign/reassign
  PUT    /threads/{id}/status                # Update status
  POST   /threads/{id}/resolve               # Resolve thread
  POST   /threads/{id}/reopen                # Reopen thread
  GET    /threads/{id}/activities            # Get activity log
  POST   /threads/{id}/watch                 # Subscribe to thread
  DELETE /threads/{id}/watch                 # Unsubscribe

# --------------------------------------------
# TASKS ENDPOINTS
# --------------------------------------------
Tasks:
  GET    /tasks                              # List tasks (filtered)
  POST   /tasks                              # Create task
  GET    /tasks/{id}                         # Get task details
  PUT    /tasks/{id}                         # Update task
  DELETE /tasks/{id}                         # Delete task
  PUT    /tasks/{id}/status                  # Update status
  POST   /tasks/{id}/comments                # Add comment

  Checklists:
    POST   /tasks/{id}/checklists            # Add checklist item
    PUT    /tasks/{id}/checklists/{cid}      # Update checklist item
    DELETE /tasks/{id}/checklists/{cid}      # Delete checklist item
    POST   /tasks/{id}/checklists/{cid}/toggle  # Toggle completion

  Board:
    GET    /tasks/board/my                   # My tasks board
    GET    /tasks/board/department           # Department board
    GET    /tasks/board/kanban               # Kanban view
    GET    /tasks/board/calendar             # Calendar view

# --------------------------------------------
# ENTITY FLAGGING (From other modules)
# --------------------------------------------
Entity:
  GET    /entity/{module}/{type}/{id}/flags  # Get flags for entity
  POST   /entity/{module}/{type}/{id}/flag   # Flag entity
  GET    /entity/{module}/{type}/{id}/thread # Get thread for entity
```

---

### 45.8 Real-time Integration (WebSocket)

```yaml
# WebSocket channels for ICH
WebSocket:
  Connection: wss://centrifugo.domain/connection/websocket

  Channels:
    # Chat channels
    chat:conversation:{conv_id}:
      Events:
        - message.new
        - message.edited
        - message.deleted
        - message.reaction
        - member.joined
        - member.left
        - typing.start
        - typing.stop

    # User's personal channel
    user:{user_id}:ich:
      Events:
        - conversation.new
        - conversation.updated
        - mention.received
        - flag.updated
        - thread.updated
        - task.assigned
        - task.updated

    # Department channel
    department:{dept_id}:ich:
      Events:
        - flag.new (department visibility)
        - thread.new
        - note.updated

  Message Format:
    {
      "event": "message.new",
      "data": {
        "conversation_id": 123,
        "message": {
          "id": 456,
          "sender_id": 789,
          "content": "Hello team!",
          "created_at": "2024-01-15T10:30:00Z"
        }
      }
    }
```

---

### 45.9 Integration with FDA

```
┌─────────────────────────────────────────────────────────────────┐
│                    FDA ↔ ICH INTEGRATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  When FDA detects anomaly:                                     │
│                                                                 │
│  ┌─────────────────────┐                                       │
│  │    FDA ENGINE       │                                       │
│  │                     │                                       │
│  │  Alert Generated:   │                                       │
│  │  • Cash skimming    │                                       │
│  │  • Risk: High       │                                       │
│  │  • Confidence: 85%  │                                       │
│  └──────────┬──────────┘                                       │
│             │                                                   │
│             │ (if ICH integration enabled)                      │
│             ▼                                                   │
│  ┌─────────────────────────────────────────┐                   │
│  │          ICH AUTO-CREATES               │                   │
│  │                                          │                   │
│  │  1. Flag (type: alert, visibility: org)  │                   │
│  │  2. Thread (linked to FDA alert)         │                   │
│  │  3. Task (assigned to auditor)           │                   │
│  │                                          │                   │
│  │  Watchers auto-added:                    │                   │
│  │  • Internal auditor                      │                   │
│  │  • Department head (of flagged entity)   │                   │
│  │  • CFO (for high-risk alerts)            │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Configuration (optional):                                     │
│  ┌─────────────────────────────────────────┐                   │
│  │ fda_integration:                         │                   │
│  │   enabled: true                          │                   │
│  │   auto_create_thread: true               │                   │
│  │   auto_create_task: true                 │                   │
│  │   auto_assign_to: "internal_auditor"     │                   │
│  │   notify_on_severity:                    │                   │
│  │     high: [cfo, gm, internal_auditor]    │                   │
│  │     medium: [internal_auditor]           │                   │
│  │     low: []  # no notification           │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 45.10 Python Implementation

#### 45.10.1 Core Enums

```python
from enum import Enum

class ChatType(str, Enum):
    """Chat conversation types"""
    DM = "dm"
    GROUP = "group"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"
    CROSS_DEPARTMENT = "cross_department"

class MessageType(str, Enum):
    """Message types"""
    TEXT = "text"
    RICH_TEXT = "rich_text"
    FILE = "file"
    IMAGE = "image"
    VOICE = "voice"
    ENTITY = "entity"
    SYSTEM = "system"

class NoteLevel(str, Enum):
    """Note visibility levels"""
    PERSONAL = "personal"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"

class FlagType(str, Enum):
    """Flag types"""
    ISSUE = "issue"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    INFO = "info"
    ALERT = "alert"
    IMPORTANT = "important"
    REVIEW = "review"

class FlagVisibility(str, Enum):
    """Flag visibility levels"""
    PRIVATE = "private"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"
    SPECIFIC = "specific"

class ThreadStatus(str, Enum):
    """Thread status"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

class TaskStatus(str, Enum):
    """Task status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskSource(str, Enum):
    """Task source types"""
    FLAG = "flag"
    MANUAL = "manual"
    FDA = "fda"
    SYSTEM = "system"
    CHAT = "chat"

class Priority(str, Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
```

#### 45.10.2 Entity Sharing Service

```python
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class EntityPermission:
    """Permission level for entity sharing"""
    level: str  # full, limited, summary, blocked
    visible_fields: list[str]
    hidden_fields: list[str]

class EntitySharingService:
    """Service for sharing entities in chat with permission check"""

    # Define shareable fields per entity type
    ENTITY_PERMISSIONS = {
        "pms.reservation": {
            "full": ["*"],
            "limited": ["id", "guest_name", "check_in", "check_out", "room_type", "status"],
            "summary": ["id", "status"],
        },
        "pos.transaction": {
            "full": ["*"],
            "limited": ["id", "outlet", "total", "status", "created_at"],
            "summary": ["id", "outlet", "status"],
        },
        "acc.invoice": {
            "full": ["*"],
            "limited": ["id", "guest_name", "total", "status", "due_date"],
            "summary": ["id", "status"],
        },
        # ... more entity types
    }

    async def check_share_permission(
        self,
        sharer_id: int,
        recipient_id: int,
        module_code: str,
        entity_type: str,
        entity_id: int
    ) -> EntityPermission:
        """
        Check what level of entity data can be shared.

        Returns permission level based on:
        - Sharer's permission on entity
        - Recipient's permission on entity
        - Entity confidentiality settings
        - Cross-department sharing rules
        """
        # Get sharer's access level
        sharer_access = await self._get_user_entity_access(
            sharer_id, module_code, entity_type, entity_id
        )

        # Get recipient's access level
        recipient_access = await self._get_user_entity_access(
            recipient_id, module_code, entity_type, entity_id
        )

        # Check entity confidentiality
        entity_config = await self._get_entity_config(
            module_code, entity_type, entity_id
        )

        if entity_config.get("is_confidential"):
            return EntityPermission(
                level="blocked",
                visible_fields=[],
                hidden_fields=["*"]
            )

        # Determine permission level
        if recipient_access == "full":
            return EntityPermission(
                level="full",
                visible_fields=["*"],
                hidden_fields=[]
            )
        elif recipient_access == "partial":
            config = self.ENTITY_PERMISSIONS.get(f"{module_code}.{entity_type}", {})
            return EntityPermission(
                level="limited",
                visible_fields=config.get("limited", []),
                hidden_fields=[]
            )
        else:
            config = self.ENTITY_PERMISSIONS.get(f"{module_code}.{entity_type}", {})
            return EntityPermission(
                level="summary",
                visible_fields=config.get("summary", ["id"]),
                hidden_fields=[]
            )

    async def create_entity_card(
        self,
        module_code: str,
        entity_type: str,
        entity_id: int,
        permission: EntityPermission
    ) -> Dict[str, Any]:
        """
        Create entity card for display in chat.
        Only includes fields allowed by permission level.
        """
        # Fetch entity data
        entity_data = await self._fetch_entity(
            module_code, entity_type, entity_id
        )

        # Filter based on permission
        if permission.level == "full":
            card_data = entity_data
        elif permission.visible_fields:
            card_data = {
                k: v for k, v in entity_data.items()
                if k in permission.visible_fields
            }
        else:
            card_data = {"id": entity_id}

        return {
            "module_code": module_code,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "permission_level": permission.level,
            "data": card_data,
            "actions": self._get_available_actions(permission.level)
        }

    def _get_available_actions(self, permission_level: str) -> list[str]:
        """Get available actions based on permission level"""
        if permission_level == "full":
            return ["view_details", "create_flag", "open_in_module"]
        elif permission_level == "limited":
            return ["view_details", "create_flag"]
        else:
            return ["create_flag"]
```

#### 45.10.3 Flag & Thread Service

```python
from datetime import datetime
from typing import Optional, List

class FlagService:
    """Service for managing flags and threads"""

    async def create_flag(
        self,
        organization_id: int,
        user_id: int,
        module_code: str,
        entity_type: str,
        entity_id: int,
        flag_type: FlagType,
        note: str,
        visibility: FlagVisibility = FlagVisibility.PRIVATE,
        priority: Priority = Priority.MEDIUM,
        assign_to: Optional[int] = None
    ) -> dict:
        """
        Create a new flag on an entity.

        If visibility is not PRIVATE, a thread is auto-created.
        If same entity already has a thread, user is added as watcher.
        """
        # Check for existing thread on same entity
        existing_thread = await self._find_existing_thread(
            organization_id, module_code, entity_type, entity_id
        )

        if existing_thread and visibility != FlagVisibility.PRIVATE:
            # Add user to existing thread instead of creating new
            await self._add_to_existing_thread(
                existing_thread["id"],
                user_id,
                flag_type,
                note,
                priority
            )
            return {
                "flag_id": None,
                "thread_id": existing_thread["id"],
                "merged": True,
                "message": "Added to existing thread"
            }

        # Get entity snapshot
        entity_snapshot = await self._get_entity_snapshot(
            module_code, entity_type, entity_id
        )

        # Create flag
        flag = await self.db.execute("""
            INSERT INTO ich.flags (
                organization_id, flag_type, visibility, priority, note,
                module_code, entity_type, entity_id, entity_snapshot,
                created_by, department_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """, organization_id, flag_type.value, visibility.value,
            priority.value, note, module_code, entity_type, entity_id,
            entity_snapshot, user_id, await self._get_user_department(user_id)
        )

        flag_id = flag["id"]
        thread_id = None

        # Create thread if not private
        if visibility != FlagVisibility.PRIVATE:
            thread_id = await self._create_thread(
                organization_id=organization_id,
                flag_id=flag_id,
                module_code=module_code,
                entity_type=entity_type,
                entity_id=entity_id,
                priority=priority,
                created_by=user_id,
                assign_to=assign_to
            )

            # Update flag with thread_id
            await self.db.execute(
                "UPDATE ich.flags SET thread_id = $1 WHERE id = $2",
                thread_id, flag_id
            )

        return {
            "flag_id": flag_id,
            "thread_id": thread_id,
            "merged": False
        }

    async def upgrade_flag_visibility(
        self,
        flag_id: int,
        user_id: int,
        new_visibility: FlagVisibility,
        share_with: Optional[List[int]] = None
    ) -> dict:
        """
        Upgrade flag visibility from private to department/organization.
        Creates a thread if not exists.
        """
        flag = await self._get_flag(flag_id)

        if flag["visibility"] != FlagVisibility.PRIVATE.value:
            raise ValueError("Flag is already shared")

        if flag["created_by"] != user_id:
            raise PermissionError("Only creator can upgrade flag visibility")

        # Check for existing thread
        existing_thread = await self._find_existing_thread(
            flag["organization_id"],
            flag["module_code"],
            flag["entity_type"],
            flag["entity_id"]
        )

        if existing_thread:
            # Merge into existing thread
            await self._merge_flag_to_thread(flag_id, existing_thread["id"])
            return {
                "thread_id": existing_thread["id"],
                "merged": True
            }

        # Create new thread
        thread_id = await self._create_thread(
            organization_id=flag["organization_id"],
            flag_id=flag_id,
            module_code=flag["module_code"],
            entity_type=flag["entity_type"],
            entity_id=flag["entity_id"],
            priority=Priority(flag["priority"]),
            created_by=user_id
        )

        # Update flag
        await self.db.execute("""
            UPDATE ich.flags
            SET visibility = $1, thread_id = $2, updated_at = now()
            WHERE id = $3
        """, new_visibility.value, thread_id, flag_id)

        # Add specific shares if provided
        if new_visibility == FlagVisibility.SPECIFIC and share_with:
            for target_id in share_with:
                await self._add_flag_share(flag_id, "user", target_id, user_id)

        return {
            "thread_id": thread_id,
            "merged": False
        }

    async def resolve_thread(
        self,
        thread_id: int,
        user_id: int,
        resolution_type: str,
        resolution_notes: str
    ) -> dict:
        """Resolve a thread"""
        thread = await self._get_thread(thread_id)

        # Check permission (creator, assignee, or department head)
        if not await self._can_resolve_thread(thread_id, user_id):
            raise PermissionError("Not authorized to resolve this thread")

        await self.db.execute("""
            UPDATE ich.threads
            SET status = 'resolved',
                resolution_type = $1,
                resolution_notes = $2,
                resolved_by = $3,
                resolved_at = now(),
                updated_at = now()
            WHERE id = $4
        """, resolution_type, resolution_notes, user_id, thread_id)

        # Log activity
        await self._log_thread_activity(
            thread_id, user_id, "resolved",
            {"resolution_type": resolution_type}
        )

        # Notify watchers
        await self._notify_watchers(
            thread_id,
            "thread.resolved",
            {
                "resolved_by": user_id,
                "resolution_type": resolution_type,
                "resolution_notes": resolution_notes
            }
        )

        return {"status": "resolved"}
```

---

### 45.11 Subscription Tiers

```yaml
ICH Subscription Tiers:

  ICH Basic:
    Price: Included with any module subscription
    Features:
      - Direct Messages (unlimited)
      - Department Channels
      - Personal Notes
      - Basic file sharing (images, documents)
    Limits:
      - Max 10 group chats
      - 1GB file storage per org
      - No flags/threads
      - No tasks

  ICH Pro:
    Price: Additional fee per organization
    Features:
      - All Basic features
      - Unlimited group chats
      - Cross-department channels
      - Department & Organization notes
      - Flags & Threads system
      - Basic task board
      - Entity sharing in chat
    Limits:
      - 10GB file storage per org
      - 1000 active threads

  ICH Enterprise:
    Price: Premium tier
    Features:
      - All Pro features
      - Advanced task board (Kanban, Calendar)
      - FDA integration (auto-threads from alerts)
      - Analytics & reporting
      - API access for integrations
      - Custom workflows
      - Audit log export
    Limits:
      - Unlimited storage
      - Unlimited threads
      - Priority support
```

---

### 45.12 Security Considerations

```yaml
Security:

  Chat:
    - DM messages encrypted at rest
    - No admin access to DM content
    - Message deletion is soft-delete (audit trail)
    - File uploads scanned for malware

  Entity Sharing:
    - Permission check on every share
    - Snapshot stored (point-in-time data)
    - Cannot share confidential entities
    - Audit log for all shares

  Flags & Threads:
    - Private flags only visible to creator
    - Thread access based on visibility rules
    - Resolution requires authorization
    - Full activity audit trail

  Notes:
    - Personal notes encrypted
    - Version history immutable
    - Deletion requires confirmation
    - Permission inheritance from folder

  General:
    - All actions logged
    - Rate limiting on API
    - Input sanitization (XSS prevention)
    - File type restrictions
```

---

### 45.13 Summary

| Feature | Description | Tier |
|---------|-------------|------|
| **Chat** | DM, Group, Department, Org channels | Basic+ |
| **Entity Sharing** | Share system entities with permission check | Pro+ |
| **Notes** | Personal, Department, Organization levels | Basic+/Pro+ |
| **Flags** | Flag any entity, private by default | Pro+ |
| **Threads** | Discussion threads from flags | Pro+ |
| **Tasks** | Task board from flags, manual, FDA | Pro+/Enterprise |
| **FDA Integration** | Auto-create threads from FDA alerts | Enterprise |

---

*Last Updated: 2025-12-10*
