# Module Documentation Standard

> Standar dokumentasi per module untuk developer. Dokumen ini mendefinisikan struktur, format, dan konten yang wajib ada untuk setiap module dalam platform.

---

## 1. Overview

### 1.1 Tujuan

Dokumentasi module bertujuan untuk:
- Memberikan pemahaman komprehensif tentang setiap module
- Menjadi single source of truth untuk developer
- Mempercepat onboarding developer baru
- Memudahkan maintenance dan debugging
- Mendukung kolaborasi antar tim

### 1.2 Pendekatan Hybrid

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID DOCUMENTATION APPROACH                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    MARKDOWN FILES (Git Versioned)                    │   │
│   │   ─────────────────────────────────────────────────────────────────  │   │
│   │   • Module specifications                                            │   │
│   │   • ERD & table definitions                                          │   │
│   │   • API contracts                                                    │   │
│   │   • Business rules                                                   │   │
│   │   • Workflow descriptions                                            │   │
│   │                                                                      │   │
│   │   Keuntungan: Version controlled, reviewable via PR, offline access │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                     │                                        │
│                                     ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      DVL TOOL (Web Application)                      │   │
│   │   ─────────────────────────────────────────────────────────────────  │   │
│   │   • Interactive ERD viewer                                           │   │
│   │   • API explorer with try-it                                         │   │
│   │   • Development progress tracking                                    │   │
│   │   • Task/bug tracking                                                │   │
│   │   • Search across all modules                                        │   │
│   │   • Comments & discussions                                           │   │
│   │                                                                      │   │
│   │   Keuntungan: Interactive, searchable, real-time updates            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Sync: DVL tool reads markdown files + stores dynamic data in database    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Folder Structure

### 2.1 Documentation Directory

```
docs/
├── modules/                           # Per-module documentation
│   ├── _template/                     # Template for new modules
│   │   ├── README.md
│   │   ├── DATABASE.md
│   │   ├── API.md
│   │   ├── FEATURES.md
│   │   ├── WORKFLOWS.md
│   │   ├── BUSINESS_RULES.md
│   │   └── CHANGELOG.md
│   │
│   ├── pms/                           # PMS Module
│   │   ├── README.md                  # Module overview
│   │   ├── DATABASE.md                # ERD & tables
│   │   ├── API.md                     # API endpoints
│   │   ├── FEATURES.md                # Feature list
│   │   ├── WORKFLOWS.md               # Process flows
│   │   ├── BUSINESS_RULES.md          # Business logic
│   │   └── CHANGELOG.md               # Development log
│   │
│   ├── pos/                           # POS Module
│   │   └── ... (same structure)
│   │
│   ├── acc/                           # Accounting Module
│   │   └── ... (same structure)
│   │
│   └── ... (other modules)
│
├── shared/                            # Shared/Building Block docs
│   ├── auth/
│   ├── notification/
│   ├── file-service/
│   └── ...
│
└── (existing docs...)                 # Existing documentation
    ├── DEVELOPMENT_STANDARDS.md
    ├── DATABASE_SCHEMA_PLATFORM.md
    └── ...
```

### 2.2 Module Code Reference

Dokumentasi juga dapat mereferensikan lokasi code:

```
backend/
├── modules/
│   ├── pms/
│   │   ├── api/              # API routes
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── tests/            # Unit tests
│   └── ...
│
frontend/
├── modules/
│   ├── pms/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── stores/           # State management
│   │   └── types/            # TypeScript types
│   └── ...
```

---

## 3. Required Documents per Module

### 3.1 Document Checklist

| Document | Required | Description |
|----------|----------|-------------|
| README.md | ✅ Yes | Module overview, quick start |
| DATABASE.md | ✅ Yes | ERD, tables, relationships |
| API.md | ✅ Yes | All API endpoints |
| FEATURES.md | ✅ Yes | Feature list with status |
| WORKFLOWS.md | ✅ Yes | Process flows & diagrams |
| BUSINESS_RULES.md | ✅ Yes | Business logic rules |
| CHANGELOG.md | ✅ Yes | Development history |

---

## 4. Document Templates

### 4.1 README.md (Module Overview)

```markdown
# {Module Name} Module

> {One-line description of the module}

---

## Overview

### Purpose
{Describe what this module does and why it exists}

### Scope
{Define what is in scope and out of scope for this module}

---

## Quick Facts

| Attribute | Value |
|-----------|-------|
| **Module Code** | {e.g., PMS, POS, ACC} |
| **Status** | {Planning / Development / Testing / Production} |
| **Completion** | {0-100}% |
| **Owner** | {Team or person responsible} |
| **Backend Port** | {e.g., 8001} |
| **API Prefix** | {e.g., /api/v1/pms} |

---

## Dependencies

### Requires (This module depends on)

| Module/Service | Type | Purpose |
|----------------|------|---------|
| Auth Service | Required | Authentication & authorization |
| {Other} | {Required/Optional} | {Purpose} |

### Required By (Other modules depend on this)

| Module | Purpose |
|--------|---------|
| {Module} | {How they use this module} |

---

## Key Concepts

### {Concept 1}
{Explanation}

### {Concept 2}
{Explanation}

---

## Quick Links

- [Database Schema](./DATABASE.md)
- [API Reference](./API.md)
- [Features](./FEATURES.md)
- [Workflows](./WORKFLOWS.md)
- [Business Rules](./BUSINESS_RULES.md)
- [Changelog](./CHANGELOG.md)

---

## Getting Started

### For Backend Developers
{Quick steps to start working on backend}

### For Frontend Developers
{Quick steps to start working on frontend}

---

## Related Documentation

- [Development Standards](../../DEVELOPMENT_STANDARDS.md)
- [API Contracts](../../API_CONTRACTS_PLATFORM.md)
- {Other relevant docs}
```

---

### 4.2 DATABASE.md (ERD & Tables)

```markdown
# {Module Name} - Database Schema

> Database tables, relationships, dan ERD untuk {Module Name} module.

---

## Entity Relationship Diagram

### Main ERD

{ASCII diagram atau link ke image}

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   {table_1}      │       │   {table_2}      │       │   {table_3}      │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │───┐   │ id (PK)          │───┐   │ id (PK)          │
│ name             │   │   │ table1_id (FK)   │◀──┘   │ table2_id (FK)   │◀──┘
│ status           │   │   │ field_a          │       │ field_x          │
│ created_at       │   └──▶│ field_b          │       │ field_y          │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

### Relationship Summary

| From | To | Type | Description |
|------|----|------|-------------|
| {table_1} | {table_2} | 1:N | {description} |
| {table_2} | {table_3} | 1:N | {description} |

---

## Tables

### {table_name}

**Description**: {What this table stores}

**Schema**: `{schema_name}` (e.g., `pms`, `pos`, `public`)

#### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | `gen_random_uuid()` | Primary key |
| `tenant_id` | UUID | NO | - | FK to tenants |
| `{column}` | {type} | {YES/NO} | {default} | {description} |
| `created_at` | TIMESTAMPTZ | NO | `now()` | Record creation time |
| `updated_at` | TIMESTAMPTZ | NO | `now()` | Last update time |
| `deleted_at` | TIMESTAMPTZ | YES | NULL | Soft delete timestamp |

#### Indexes

| Name | Columns | Type | Purpose |
|------|---------|------|---------|
| `{table}_pkey` | `id` | PRIMARY | Primary key |
| `idx_{table}_tenant` | `tenant_id` | BTREE | Tenant filtering |
| `{index_name}` | `{columns}` | {type} | {purpose} |

#### Foreign Keys

| Column | References | On Delete | On Update |
|--------|------------|-----------|-----------|
| `tenant_id` | `platform.tenants(id)` | RESTRICT | CASCADE |
| `{column}` | `{table}({column})` | {action} | {action} |

#### Constraints

| Name | Type | Definition |
|------|------|------------|
| `{constraint_name}` | CHECK | `{expression}` |
| `{constraint_name}` | UNIQUE | `({columns})` |

#### Triggers

| Name | Event | Description |
|------|-------|-------------|
| `{trigger_name}` | {BEFORE/AFTER} {INSERT/UPDATE/DELETE} | {what it does} |

---

### {next_table}

{Repeat structure above for each table}

---

## Enums / Types

### {enum_name}

| Value | Description |
|-------|-------------|
| `{value_1}` | {description} |
| `{value_2}` | {description} |

---

## Views

### {view_name}

**Purpose**: {What this view provides}

```sql
-- View definition
CREATE VIEW {view_name} AS
SELECT ...
```

---

## Functions / Stored Procedures

### {function_name}

**Purpose**: {What this function does}

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `{param}` | {type} | {description} |

**Returns**: {return type and description}

```sql
-- Function signature
CREATE FUNCTION {function_name}({params}) RETURNS {type}
```

---

## Migration Notes

### Initial Migration
- Migration file: `{migration_filename}`
- Created: {date}

### Schema Changes
| Version | Date | Change | Migration File |
|---------|------|--------|----------------|
| 1.0 | {date} | Initial schema | `001_initial.py` |
| 1.1 | {date} | {change description} | `002_{name}.py` |
```

---

### 4.3 API.md (API Endpoints)

```markdown
# {Module Name} - API Reference

> API endpoints untuk {Module Name} module.

---

## Base URL

```
Production: https://api.example.com/api/v1/{module_code}
Staging:    https://staging-api.example.com/api/v1/{module_code}
Local:      http://localhost:8001/api/v1/{module_code}
```

---

## Authentication

All endpoints require authentication unless marked as `[Public]`.

```
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_uuid}
```

---

## Endpoints Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/{resources}` | List all {resources} | Required |
| POST | `/{resources}` | Create new {resource} | Required |
| GET | `/{resources}/{id}` | Get {resource} by ID | Required |
| PUT | `/{resources}/{id}` | Update {resource} | Required |
| DELETE | `/{resources}/{id}` | Delete {resource} | Required |

---

## Endpoints Detail

### List {Resources}

```
GET /{resources}
```

**Description**: Retrieve a paginated list of {resources}.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number |
| `limit` | integer | No | 20 | Items per page (max: 100) |
| `sort` | string | No | `-created_at` | Sort field (prefix `-` for desc) |
| `search` | string | No | - | Search term |
| `status` | string | No | - | Filter by status |
| `{filter}` | {type} | No | - | {description} |

**Response** `200 OK`:

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "field_1": "value",
      "field_2": "value",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**Errors**:

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |

---

### Get {Resource}

```
GET /{resources}/{id}
```

**Description**: Retrieve a single {resource} by ID.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | {Resource} ID |

**Response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field_1": "value",
    "field_2": "value",
    "related_items": [],
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

**Errors**:

| Code | Description |
|------|-------------|
| 404 | Not Found - {Resource} does not exist |

---

### Create {Resource}

```
POST /{resources}
```

**Description**: Create a new {resource}.

**Request Body**:

```json
{
  "field_1": "value",        // Required - {description}
  "field_2": "value",        // Required - {description}
  "field_3": "value"         // Optional - {description}
}
```

**Validation Rules**:

| Field | Rules |
|-------|-------|
| `field_1` | Required, string, max 100 chars |
| `field_2` | Required, valid enum value |
| `field_3` | Optional, integer, min 0 |

**Response** `201 Created`:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field_1": "value",
    "field_2": "value",
    "created_at": "2025-01-01T00:00:00Z"
  },
  "message": "{Resource} created successfully"
}
```

**Errors**:

| Code | Description |
|------|-------------|
| 400 | Bad Request - Validation failed |
| 409 | Conflict - {Resource} already exists |

---

### Update {Resource}

```
PUT /{resources}/{id}
```

**Description**: Update an existing {resource}.

**Request Body**:

```json
{
  "field_1": "new_value",    // Optional
  "field_2": "new_value"     // Optional
}
```

**Response** `200 OK`:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field_1": "new_value",
    "updated_at": "2025-01-01T00:00:00Z"
  },
  "message": "{Resource} updated successfully"
}
```

---

### Delete {Resource}

```
DELETE /{resources}/{id}
```

**Description**: Soft delete a {resource}.

**Response** `200 OK`:

```json
{
  "success": true,
  "message": "{Resource} deleted successfully"
}
```

**Errors**:

| Code | Description |
|------|-------------|
| 400 | Bad Request - Cannot delete (has dependencies) |

---

## Webhooks / Events

This module emits the following events:

| Event | Trigger | Payload |
|-------|---------|---------|
| `{module}.{resource}.created` | New {resource} created | `{ id, ... }` |
| `{module}.{resource}.updated` | {Resource} updated | `{ id, changes, ... }` |
| `{module}.{resource}.deleted` | {Resource} deleted | `{ id }` |

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| List/Read | 100 req/min |
| Create/Update | 30 req/min |
| Delete | 10 req/min |
| Bulk operations | 5 req/min |
```

---

### 4.4 FEATURES.md (Feature List)

```markdown
# {Module Name} - Features

> Daftar fitur dan status development untuk {Module Name} module.

---

## Feature Summary

| Total Features | Completed | In Progress | Planned |
|----------------|-----------|-------------|---------|
| {N} | {N} | {N} | {N} |

**Overall Progress**: {X}%

---

## Feature Categories

### 1. {Category Name}

| # | Feature | Description | Priority | Status | API | UI |
|---|---------|-------------|----------|--------|-----|-------|
| 1.1 | {Feature name} | {Brief description} | ⭐⭐⭐ | ✅ Done | ✅ | ✅ |
| 1.2 | {Feature name} | {Brief description} | ⭐⭐⭐ | 🔄 In Progress | ✅ | 🔄 |
| 1.3 | {Feature name} | {Brief description} | ⭐⭐ | 📋 Planned | ❌ | ❌ |
| 1.4 | {Feature name} | {Brief description} | ⭐ | 📋 Planned | ❌ | ❌ |

### 2. {Category Name}

| # | Feature | Description | Priority | Status | API | UI |
|---|---------|-------------|----------|--------|-----|-------|
| 2.1 | {Feature name} | {Brief description} | ⭐⭐⭐ | ✅ Done | ✅ | ✅ |

---

## Feature Details

### 1.1 {Feature Name}

**Status**: ✅ Done / 🔄 In Progress / 📋 Planned

**Description**:
{Detailed description of what this feature does}

**User Stories**:
- As a {role}, I want to {action} so that {benefit}
- As a {role}, I want to {action} so that {benefit}

**Acceptance Criteria**:
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

**Technical Notes**:
- {Implementation detail}
- {Dependency information}

**Related**:
- API: `GET /api/v1/{module}/{endpoint}`
- UI: `/{module}/{page}`
- Tables: `{table_name}`

---

### 1.2 {Feature Name}

{Repeat structure}

---

## Roadmap

### Phase 1: MVP
- [x] Feature 1.1
- [x] Feature 1.2
- [ ] Feature 1.3

### Phase 2: Enhancement
- [ ] Feature 2.1
- [ ] Feature 2.2

### Phase 3: Advanced
- [ ] Feature 3.1

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Done - Completed and tested |
| 🔄 | In Progress - Currently being developed |
| 📋 | Planned - Scheduled for development |
| ⏸️ | On Hold - Paused |
| ❌ | Cancelled - Will not be implemented |

| Priority | Meaning |
|----------|---------|
| ⭐⭐⭐ | Critical - Must have for MVP |
| ⭐⭐ | Important - Should have |
| ⭐ | Nice to have - Can defer |
```

---

### 4.5 WORKFLOWS.md (Process Flows)

```markdown
# {Module Name} - Workflows

> Process flows dan user journeys untuk {Module Name} module.

---

## Workflow Index

| # | Workflow | Description | Complexity |
|---|----------|-------------|------------|
| 1 | {Workflow name} | {Brief description} | {Simple/Medium/Complex} |
| 2 | {Workflow name} | {Brief description} | {Simple/Medium/Complex} |

---

## 1. {Workflow Name}

### Overview

**Trigger**: {What initiates this workflow}
**Actor**: {Who performs this workflow}
**Outcome**: {What is the end result}

### Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Step 1    │────▶│   Step 2    │────▶│   Step 3    │────▶│   Step 4    │
│  {Action}   │     │  {Action}   │     │  {Action}   │     │  {Action}   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
 [{Service}]         [{Service}]         [{Service}]         [{Service}]
```

### Step-by-Step

#### Step 1: {Step Name}

**Actor**: {Who does this}
**Action**: {What they do}
**System**: {What the system does}

**Input**:
- {Input data}

**Output**:
- {Output data}

**Validations**:
- {Validation rule}

**Error Handling**:
| Error | Handling |
|-------|----------|
| {Error condition} | {How to handle} |

---

#### Step 2: {Step Name}

{Repeat structure}

---

### Decision Points

```
                    ┌─────────────────┐
                    │  {Condition?}   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         [Option A]    [Option B]    [Option C]
```

| Condition | Action |
|-----------|--------|
| {If condition A} | {Do this} |
| {If condition B} | {Do that} |
| {Default} | {Default action} |

---

### Integration Points

| Step | External Service | API Call | Purpose |
|------|------------------|----------|---------|
| {N} | {Service} | `{METHOD} {endpoint}` | {Why} |

---

### Events Emitted

| After Step | Event | Consumers |
|------------|-------|-----------|
| {N} | `{event.name}` | {Who listens} |

---

## 2. {Next Workflow}

{Repeat structure}

---

## State Transitions

### {Entity} States

```
┌─────────┐    create    ┌─────────┐    confirm    ┌─────────┐
│  DRAFT  │─────────────▶│ PENDING │──────────────▶│ ACTIVE  │
└─────────┘              └─────────┘               └────┬────┘
                              │                        │
                              │ cancel                 │ complete
                              ▼                        ▼
                         ┌─────────┐             ┌─────────┐
                         │CANCELLED│             │COMPLETED│
                         └─────────┘             └─────────┘
```

| From State | To State | Trigger | Conditions |
|------------|----------|---------|------------|
| DRAFT | PENDING | Submit | All required fields filled |
| PENDING | ACTIVE | Confirm | Payment received (if required) |
| PENDING | CANCELLED | Cancel | Within cancellation window |
| ACTIVE | COMPLETED | Complete | End date reached |
```

---

### 4.6 BUSINESS_RULES.md (Business Rules)

```markdown
# {Module Name} - Business Rules

> Aturan bisnis dan validasi logic untuk {Module Name} module.

---

## Rule Categories

| Category | Count |
|----------|-------|
| Validation Rules | {N} |
| Calculation Rules | {N} |
| Authorization Rules | {N} |
| Automation Rules | {N} |

---

## 1. Validation Rules

### VR-{XXX}-001: {Rule Name}

**Description**: {What this rule validates}

**Applies To**: {Entity/Action}

**Rule**:
```
IF {condition}
THEN {validation passes}
ELSE {error: "message"}
```

**Examples**:
| Input | Valid? | Reason |
|-------|--------|--------|
| {example 1} | ✅ Yes | {why} |
| {example 2} | ❌ No | {why} |

**Error Code**: `{MODULE}_{ENTITY}_INVALID_{REASON}`

**Error Message**: "{User-friendly message}"

---

### VR-{XXX}-002: {Rule Name}

{Repeat structure}

---

## 2. Calculation Rules

### CR-{XXX}-001: {Rule Name}

**Description**: {What this calculates}

**Formula**:
```
{result} = {formula}
```

**Variables**:
| Variable | Source | Type |
|----------|--------|------|
| `{var}` | {where it comes from} | {type} |

**Example**:
```
Input:
  - variable_1 = 100
  - variable_2 = 0.1

Calculation:
  result = 100 * 0.1 = 10

Output: 10
```

**Rounding**: {Rounding rules if applicable}

**Edge Cases**:
| Case | Handling |
|------|----------|
| {case} | {how to handle} |

---

## 3. Authorization Rules

### AR-{XXX}-001: {Rule Name}

**Description**: {Who can do what}

**Permission Required**: `{permission.code}`

**Conditions**:
- {Additional condition 1}
- {Additional condition 2}

**Matrix**:

| Role | Can View | Can Create | Can Edit | Can Delete |
|------|----------|------------|----------|------------|
| Admin | ✅ | ✅ | ✅ | ✅ |
| Manager | ✅ | ✅ | ✅ | ❌ |
| Staff | ✅ | ✅ | Own only | ❌ |
| Viewer | ✅ | ❌ | ❌ | ❌ |

---

## 4. Automation Rules

### AU-{XXX}-001: {Rule Name}

**Description**: {What happens automatically}

**Trigger**: {When this rule fires}

**Condition**:
```
IF {condition}
```

**Action**:
```
THEN {action}
```

**Example Scenario**:
1. {Step 1}
2. {Step 2}
3. {Step 3}

---

## 5. Default Values

| Entity | Field | Default Value | Condition |
|--------|-------|---------------|-----------|
| {Entity} | {field} | {value} | {when applied} |

---

## 6. Constraints Summary

| Constraint | Type | Value | Configurable? |
|------------|------|-------|---------------|
| {name} | {type} | {value} | {Yes/No} |

---

## Rule Change Log

| Date | Rule | Change | Reason |
|------|------|--------|--------|
| {date} | {rule_id} | {what changed} | {why} |
```

---

### 4.7 CHANGELOG.md (Development Log)

```markdown
# {Module Name} - Changelog

> Development history dan perubahan untuk {Module Name} module.

---

## Version History

| Version | Date | Type | Summary |
|---------|------|------|---------|
| 1.2.0 | 2025-02-01 | Feature | Added {feature} |
| 1.1.1 | 2025-01-28 | Bugfix | Fixed {bug} |
| 1.1.0 | 2025-01-20 | Feature | Added {feature} |
| 1.0.0 | 2025-01-15 | Release | Initial release |

---

## [Unreleased]

### Added
- {New feature being developed}

### Changed
- {Modification in progress}

### Fixed
- {Bug being fixed}

---

## [1.2.0] - 2025-02-01

### Added
- **{Feature Name}**: {Description of new feature}
  - {Detail 1}
  - {Detail 2}
  - Related: API `{endpoint}`, Table `{table}`

### Changed
- **{Change Name}**: {Description of change}
  - Before: {old behavior}
  - After: {new behavior}
  - Migration: {migration notes if any}

### Fixed
- **{Bug ID}**: {Bug description}
  - Cause: {root cause}
  - Fix: {how it was fixed}
  - Affected: {what was affected}

### Deprecated
- **{Feature}**: {Why deprecated, what to use instead}

### Removed
- **{Feature}**: {Why removed}

### Security
- **{Security fix}**: {Description}

---

## [1.1.1] - 2025-01-28

### Fixed
- **BUG-123**: {Bug title}
  - {Fix description}

---

## [1.1.0] - 2025-01-20

### Added
- {Feature description}

---

## [1.0.0] - 2025-01-15

### Added
- Initial release of {Module Name} module
- Features included:
  - {Feature 1}
  - {Feature 2}
  - {Feature 3}

---

## Development Notes

### Known Issues
| ID | Issue | Workaround | Target Fix |
|----|-------|------------|------------|
| {ID} | {Description} | {Workaround} | {Version} |

### Technical Debt
| Item | Description | Priority |
|------|-------------|----------|
| {Item} | {Description} | {High/Medium/Low} |

---

## Contributors

| Name | Contributions |
|------|---------------|
| {Name} | {What they worked on} |
```

---

## 5. DVL Tool Integration

### 5.1 Data Sources

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DVL TOOL DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SOURCE 1: Markdown Files (Read-only, synced from Git)                     │
│   ──────────────────────────────────────────────────────                    │
│   • README.md         → Module overview                                     │
│   • DATABASE.md       → ERD, tables                                         │
│   • API.md            → API endpoints                                       │
│   • FEATURES.md       → Feature list                                        │
│   • WORKFLOWS.md      → Process flows                                       │
│   • BUSINESS_RULES.md → Business rules                                      │
│   • CHANGELOG.md      → Version history                                     │
│                                                                              │
│   SOURCE 2: DVL Database (Read-write, dynamic data)                         │
│   ──────────────────────────────────────────────────                        │
│   • Development tasks & progress                                            │
│   • Bug/issue tracking                                                      │
│   • Comments & discussions                                                  │
│   • Team assignments                                                        │
│   • Real-time status updates                                                │
│   • Search indexes                                                          │
│                                                                              │
│   SOURCE 3: External (API integrations)                                     │
│   ──────────────────────────────────────                                    │
│   • Git commits (optional)                                                  │
│   • CI/CD status (optional)                                                 │
│   • Test coverage (optional)                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 DVL Tool Database Schema

```sql
-- DVL Tool internal tables (separate from main app)

-- Modules (synced from markdown, with additional fields)
CREATE TABLE dvl_modules (
    id UUID PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,    -- PMS, POS, ACC
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planning', -- planning, development, testing, production
    completion_percent INTEGER DEFAULT 0,
    owner_id UUID,
    backend_port INTEGER,
    api_prefix VARCHAR(50),
    markdown_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Features (can be synced or manually added)
CREATE TABLE dvl_features (
    id UUID PRIMARY KEY,
    module_id UUID REFERENCES dvl_modules(id),
    code VARCHAR(20),                     -- 1.1, 1.2, etc.
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    priority INTEGER DEFAULT 2,           -- 1=low, 2=medium, 3=high
    status VARCHAR(20) DEFAULT 'planned', -- planned, in_progress, done, cancelled
    api_done BOOLEAN DEFAULT FALSE,
    ui_done BOOLEAN DEFAULT FALSE,
    assigned_to UUID,
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks (development tasks)
CREATE TABLE dvl_tasks (
    id UUID PRIMARY KEY,
    module_id UUID REFERENCES dvl_modules(id),
    feature_id UUID REFERENCES dvl_features(id),
    title VARCHAR(300) NOT NULL,
    description TEXT,
    type VARCHAR(20),                     -- feature, bugfix, improvement, docs
    status VARCHAR(20) DEFAULT 'todo',    -- todo, in_progress, review, done
    priority INTEGER DEFAULT 2,
    assigned_to UUID,
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
CREATE TABLE dvl_comments (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50),              -- module, feature, task
    entity_id UUID,
    user_id UUID,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activity log
CREATE TABLE dvl_activity_log (
    id UUID PRIMARY KEY,
    module_id UUID,
    user_id UUID,
    action VARCHAR(50),
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.3 DVL Tool Features by Category

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DVL TOOL FEATURE MATRIX                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DOCUMENTATION (From Markdown)                                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  ✓ Module Explorer      - Browse all modules                        │    │
│  │  ✓ ERD Viewer           - Interactive diagram (from DATABASE.md)    │    │
│  │  ✓ Table Browser        - Column details, relationships             │    │
│  │  ✓ API Explorer         - Endpoints with try-it (from API.md)       │    │
│  │  ✓ Feature Catalog      - Feature list & status (from FEATURES.md)  │    │
│  │  ✓ Workflow Viewer      - Flow diagrams (from WORKFLOWS.md)         │    │
│  │  ✓ Rules Browser        - Business rules (from BUSINESS_RULES.md)   │    │
│  │  ✓ Changelog Viewer     - Version history (from CHANGELOG.md)       │    │
│  │  ✓ Full-text Search     - Search across all documentation           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DEVELOPMENT TRACKING (From Database)                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  ✓ Progress Dashboard   - Overall & per-module completion           │    │
│  │  ✓ Task Board           - Kanban view for tasks                     │    │
│  │  ✓ Bug Tracker          - Simple issue tracking                     │    │
│  │  ✓ Team View            - Who's working on what                     │    │
│  │  ✓ Timeline             - Development timeline                      │    │
│  │  ✓ Activity Feed        - Recent changes                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  COLLABORATION (From Database)                                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  ✓ Comments             - Discuss on any item                       │    │
│  │  ✓ @Mentions            - Notify team members                       │    │
│  │  ✓ Notifications        - Updates on watched items                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ADMIN (Database + Config)                                           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  ✓ Sync Markdown        - Pull latest docs from Git                 │    │
│  │  ✓ User Management      - Manage team access                        │    │
│  │  ✓ Settings             - Configure DVL tool                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Naming Conventions

### 6.1 File Naming

| File | Format |
|------|--------|
| Module folder | `lowercase` (e.g., `pms`, `pos`) |
| Document files | `UPPERCASE.md` (e.g., `README.md`, `API.md`) |

### 6.2 ID Conventions

| Type | Format | Example |
|------|--------|---------|
| Module Code | 2-4 uppercase letters | `PMS`, `POS`, `ACC` |
| Feature ID | `{category}.{number}` | `1.1`, `2.3` |
| Rule ID | `{TYPE}-{MODULE}-{NNN}` | `VR-PMS-001`, `CR-ACC-003` |
| Bug ID | `BUG-{NNN}` | `BUG-123` |

---

## 7. Maintenance Guidelines

### 7.1 When to Update Documentation

| Event | Action Required |
|-------|-----------------|
| New table added | Update DATABASE.md |
| New API endpoint | Update API.md |
| Feature completed | Update FEATURES.md status |
| Business rule changed | Update BUSINESS_RULES.md |
| Bug fixed | Add to CHANGELOG.md |
| New release | Create CHANGELOG entry |

### 7.2 Review Process

```
Developer writes/updates docs
           │
           ▼
    Create Pull Request
           │
           ▼
    Tech Lead reviews
           │
           ▼
    Merge to main branch
           │
           ▼
    DVL Tool syncs automatically
```

### 7.3 Documentation Quality Checklist

- [ ] All tables documented in DATABASE.md
- [ ] All endpoints documented in API.md
- [ ] All features listed in FEATURES.md
- [ ] Status is up-to-date
- [ ] Examples provided where helpful
- [ ] No broken internal links
- [ ] Consistent formatting

---

## 8. Quick Start for New Module

### Step 1: Create Folder Structure

```bash
# Copy template
cp -r docs/modules/_template docs/modules/{new_module}
```

### Step 2: Fill README.md

Start with the module overview - this is the entry point.

### Step 3: Document Database

List all tables, columns, relationships in DATABASE.md.

### Step 4: Document API

List all endpoints in API.md.

### Step 5: List Features

Create feature list in FEATURES.md with initial status.

### Step 6: Register in DVL Tool

The DVL tool will auto-detect new modules on sync.

---

*Last Updated: 2025-12-12*
*Category: Developer Standard*
