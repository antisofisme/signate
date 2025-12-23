# SPEC-05: Internal Development Management System

> Sistem internal untuk manajemen development, module registry, feature tracking, dan project monitoring

**Related Documents:**
- [SPEC-06: Public Website Integration](./SPEC-06-public-website-integration.md) - Integrasi dengan website company profile
- [ARCH-02: Module Architecture](./ARCH-02-module-architecture.md) - Arsitektur module aplikasi
- [GUIDE-01: Development Flow](./GUIDE-01-development-flow.md) - Flow development

---

## 1. Overview

### 1.1 Tujuan

Internal Development Management System adalah **single source of truth** untuk:
- **Module Registry** - Daftar semua module & status development
- **Feature Tracking** - Track fitur per module, versi, status
- **Release Management** - Changelog, versioning, deployment history
- **Client Management** - CRM internal untuk client/customer
- **Development Dashboard** - Monitoring progress & health

### 1.2 Prinsip Inti

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PRINSIP INTERNAL DEV MANAGEMENT                                          ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  1. SINGLE SOURCE OF TRUTH                                                ║
║     • Semua data teknis disimpan di satu sistem                          ║
║     • Tidak ada duplikasi manual di berbagai tempat                      ║
║     • Otomatis sync ke sistem lain (website, docs, dashboard)            ║
║                                                                           ║
║  2. AUTOMATION FIRST                                                      ║
║     • CI/CD auto-update registry saat deploy                             ║
║     • Changelog auto-generated dari commits                              ║
║     • Status auto-update berdasarkan deployment                          ║
║                                                                           ║
║  3. VERSION-AWARE                                                         ║
║     • Semua data punya version tracking                                  ║
║     • History lengkap tersimpan                                          ║
║     • Rollback capability untuk metadata                                 ║
║                                                                           ║
║  4. PUBLIC/PRIVATE BOUNDARY                                               ║
║     • Jelas mana data internal vs public                                 ║
║     • Feature flags untuk visibility control                             ║
║     • API berbeda untuk internal vs public access                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### 1.3 Use Cases

**Internal (Development Team):**
- Track progress development per module
- Manage feature roadmap
- Monitor deployment & releases
- Debug production issues dengan version history
- Coordinate antar developer

**External (via Public API):**
- Company website consume module list & features
- Public documentation auto-generate dari registry
- Customer portal lihat module yang mereka subscribe
- Partner API access untuk integration

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTERNAL DEV MANAGEMENT SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                        CORE COMPONENTS                          │   │
│  │                                                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │   │
│  │  │   Module     │  │   Feature    │  │   Release    │         │   │
│  │  │   Registry   │  │   Tracking   │  │  Management  │         │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │   │
│  │         │                  │                  │                 │   │
│  │         └──────────────────┴──────────────────┘                 │   │
│  │                            │                                    │   │
│  │                    ┌───────▼────────┐                          │   │
│  │                    │   PostgreSQL   │                          │   │
│  │                    │   Database     │                          │   │
│  │                    └───────┬────────┘                          │   │
│  │                            │                                    │   │
│  └────────────────────────────┼────────────────────────────────────┘   │
│                               │                                        │
│  ┌────────────────────────────┼────────────────────────────────────┐   │
│  │                     API LAYER                                   │   │
│  │                            │                                    │   │
│  │         ┌──────────────────┴──────────────────┐                │   │
│  │         │                                      │                │   │
│  │    ┌────▼──────┐                      ┌───────▼──────┐         │   │
│  │    │ Internal  │                      │   Public     │         │   │
│  │    │    API    │                      │    API       │         │   │
│  │    │ (Admin)   │                      │ (Read-only)  │         │   │
│  │    └────┬──────┘                      └───────┬──────┘         │   │
│  └─────────┼─────────────────────────────────────┼────────────────┘   │
│            │                                      │                    │
└────────────┼──────────────────────────────────────┼────────────────────┘
             │                                      │
    ┌────────▼────────┐                   ┌────────▼────────┐
    │   Internal      │                   │   Company       │
    │   Dashboard     │                   │   Website       │
    │                 │                   │   (Public)      │
    └─────────────────┘                   └─────────────────┘
```

### 2.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW DIAGRAM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DEVELOPER                                                              │
│     │                                                                   │
│     │ 1. Push code & deploy                                            │
│     ▼                                                                   │
│  ┌─────────────┐                                                       │
│  │   CI/CD     │                                                       │
│  │  Pipeline   │                                                       │
│  └──────┬──────┘                                                       │
│         │                                                               │
│         │ 2. Auto-update metadata                                      │
│         ▼                                                               │
│  ┌─────────────────────────────────────────┐                          │
│  │  Internal Dev Management System         │                          │
│  │  • Module Registry                      │                          │
│  │  • Feature Tracking                     │                          │
│  │  • Release Management                   │                          │
│  └──────┬──────────────────────────────────┘                          │
│         │                                                               │
│         │ 3. Expose via API                                            │
│         ├─────────────────┬─────────────────┐                         │
│         │                 │                 │                         │
│         ▼                 ▼                 ▼                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │
│  │  Internal   │   │   Company   │   │  Customer   │                │
│  │  Dashboard  │   │   Website   │   │   Portal    │                │
│  └─────────────┘   └─────────────┘   └─────────────┘                │
│         │                 │                 │                         │
│         │                 │                 │                         │
│         ▼                 ▼                 ▼                         │
│     Dev Team          Public           Customers                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 Module Registry

**Tujuan:** Daftar semua module yang ada/dikembangkan dengan metadata lengkap.

**Data yang Disimpan:**
- Module code (pms, pos, acc, dll)
- Module name & description
- Category (core, platform, feature, addon)
- Parent module (untuk sub-module)
- Current version
- Development status (planned, in-progress, beta, stable, deprecated)
- Public visibility flag
- Icon/logo
- Documentation URL
- Repository URL
- Created & updated timestamps

**Contoh Data:**
```json
{
  "module_code": "pms",
  "module_name": "Property Management System",
  "description": "Core hotel operations management",
  "category": "core",
  "parent_module": null,
  "current_version": "2.5.3",
  "status": "stable",
  "public_visible": true,
  "icon_url": "/assets/icons/pms.svg",
  "docs_url": "https://docs.example.com/pms",
  "repo_url": "https://github.com/company/pms",
  "created_at": "2023-01-15T10:00:00Z",
  "updated_at": "2024-12-20T15:30:00Z"
}
```

---

### 3.2 Feature Tracking

**Tujuan:** Track fitur-fitur per module dengan detail versi & status.

**Data yang Disimpan:**
- Feature ID & name
- Module code (FK to module_registry)
- Description
- Feature type (core, premium, addon)
- Status (planned, in-development, beta, stable, deprecated)
- Version introduced
- Version deprecated (if applicable)
- Public visible
- Breaking change flag
- Dependencies (feature lain yang dibutuhkan)
- Created & updated timestamps

**Contoh Data:**
```json
{
  "feature_id": "pms_online_checkin",
  "feature_name": "Online Check-in",
  "module_code": "pms",
  "description": "Guest self-service check-in via mobile",
  "feature_type": "premium",
  "status": "stable",
  "version_introduced": "2.3.0",
  "version_deprecated": null,
  "public_visible": true,
  "breaking_change": false,
  "dependencies": ["pms_guest_app", "pms_digital_key"],
  "created_at": "2023-06-10T08:00:00Z",
  "updated_at": "2024-08-15T12:00:00Z"
}
```

---

### 3.3 Release Management

**Tujuan:** Track semua release dengan changelog, breaking changes, deployment info.

**Data yang Disimpan:**
- Release ID
- Module code
- Version number (semantic versioning)
- Release type (major, minor, patch)
- Release date
- Deployment environment (staging, production)
- Changelog (auto-generated + manual notes)
- Breaking changes list
- Migration notes
- Git commit hash
- Deployed by
- Status (scheduled, deployed, rolled-back)

**Contoh Data:**
```json
{
  "release_id": "rel_001",
  "module_code": "pms",
  "version": "2.5.0",
  "release_type": "minor",
  "release_date": "2024-12-15T10:00:00Z",
  "environment": "production",
  "changelog": [
    {
      "type": "feature",
      "description": "Add contactless check-in support"
    },
    {
      "type": "improvement",
      "description": "Optimize room assignment algorithm"
    },
    {
      "type": "fix",
      "description": "Fix rate calculation for extra guests"
    }
  ],
  "breaking_changes": [],
  "migration_notes": "Run migration 045_add_contactless_fields.sql",
  "git_commit": "a3f2c1b",
  "deployed_by": "deploy-bot",
  "status": "deployed"
}
```

---

### 3.4 Client Management (CRM)

**Tujuan:** Manage client/customer yang menggunakan aplikasi.

**Data yang Disimpan:**
- Client ID & name
- Business type (hotel, resort, chain, etc)
- Contact information
- Status (prospect, trial, active, churned)
- Subscription start/end date
- Modules subscribed (array of module codes)
- Custom features (client-specific customizations)
- Support tier
- Account manager
- Created & updated timestamps

**Contoh Data:**
```json
{
  "client_id": "client_001",
  "client_name": "Grand Hotel Bali",
  "business_type": "resort",
  "contact": {
    "email": "it@grandhotelbali.com",
    "phone": "+62-361-123456"
  },
  "status": "active",
  "subscription_start": "2023-01-01",
  "subscription_end": "2024-12-31",
  "modules_subscribed": ["pms", "pos", "acc", "spa"],
  "custom_features": ["custom_reporting", "ota_integration_special"],
  "support_tier": "premium",
  "account_manager": "John Doe",
  "created_at": "2022-11-15T09:00:00Z",
  "updated_at": "2024-12-01T14:00:00Z"
}
```

---

## 4. Database Schema

### 4.1 ERD

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATABASE SCHEMA (ERD)                            │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│  module_registry     │
├──────────────────────┤
│ id (PK)              │
│ module_code (UNIQUE) │◄─────────┐
│ module_name          │          │
│ description          │          │
│ category             │          │
│ parent_module_code   │──┐       │
│ current_version      │  │       │
│ status               │  │       │
│ public_visible       │  │       │
│ icon_url             │  │       │
│ docs_url             │  │       │
│ repo_url             │  │       │
│ created_at           │  │       │
│ updated_at           │  │       │
│ metadata (JSONB)     │  │       │
└──────────────────────┘  │       │
         ▲                │       │
         │                │       │
         └────────────────┘       │
                                  │
┌──────────────────────┐          │
│  features            │          │
├──────────────────────┤          │
│ id (PK)              │          │
│ feature_id (UNIQUE)  │          │
│ feature_name         │          │
│ module_code (FK)     │──────────┤
│ description          │          │
│ feature_type         │          │
│ status               │          │
│ version_introduced   │          │
│ version_deprecated   │          │
│ public_visible       │          │
│ breaking_change      │          │
│ dependencies (JSON)  │          │
│ created_at           │          │
│ updated_at           │          │
│ metadata (JSONB)     │          │
└──────────────────────┘          │
                                  │
┌──────────────────────┐          │
│  releases            │          │
├──────────────────────┤          │
│ id (PK)              │          │
│ release_id (UNIQUE)  │          │
│ module_code (FK)     │──────────┤
│ version              │          │
│ release_type         │          │
│ release_date         │          │
│ environment          │          │
│ changelog (JSONB)    │          │
│ breaking_changes     │          │
│ migration_notes      │          │
│ git_commit           │          │
│ deployed_by          │          │
│ status               │          │
│ created_at           │          │
│ metadata (JSONB)     │          │
└──────────────────────┘          │
                                  │
┌──────────────────────┐          │
│  clients             │          │
├──────────────────────┤          │
│ id (PK)              │          │
│ client_id (UNIQUE)   │          │
│ client_name          │          │
│ business_type        │          │
│ contact (JSONB)      │          │
│ status               │          │
│ subscription_start   │          │
│ subscription_end     │          │
│ modules_subscribed   │◄─────────┘
│   (ARRAY)            │
│ custom_features      │
│ support_tier         │
│ account_manager      │
│ created_at           │
│ updated_at           │
│ metadata (JSONB)     │
└──────────────────────┘

┌──────────────────────┐
│  deployment_history  │
├──────────────────────┤
│ id (PK)              │
│ release_id (FK)      │
│ module_code          │
│ version              │
│ environment          │
│ deployed_at          │
│ deployed_by          │
│ status               │
│ rollback_at          │
│ rollback_reason      │
│ metadata (JSONB)     │
└──────────────────────┘
```

### 4.2 SQL Schema

```sql
-- Module Registry Table
CREATE TABLE module_registry (
    id SERIAL PRIMARY KEY,
    module_code VARCHAR(50) UNIQUE NOT NULL,
    module_name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- core, platform, feature, addon
    parent_module_code VARCHAR(50) REFERENCES module_registry(module_code),
    current_version VARCHAR(20),
    status VARCHAR(50) NOT NULL, -- planned, in-progress, beta, stable, deprecated
    public_visible BOOLEAN DEFAULT false,
    icon_url TEXT,
    docs_url TEXT,
    repo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,

    CONSTRAINT valid_status CHECK (status IN ('planned', 'in-progress', 'beta', 'stable', 'deprecated')),
    CONSTRAINT valid_category CHECK (category IN ('core', 'platform', 'feature', 'addon'))
);

CREATE INDEX idx_module_status ON module_registry(status);
CREATE INDEX idx_module_public ON module_registry(public_visible);
CREATE INDEX idx_module_category ON module_registry(category);

-- Features Table
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    feature_id VARCHAR(100) UNIQUE NOT NULL,
    feature_name VARCHAR(200) NOT NULL,
    module_code VARCHAR(50) NOT NULL REFERENCES module_registry(module_code) ON DELETE CASCADE,
    description TEXT,
    feature_type VARCHAR(50) NOT NULL, -- core, premium, addon
    status VARCHAR(50) NOT NULL,
    version_introduced VARCHAR(20),
    version_deprecated VARCHAR(20),
    public_visible BOOLEAN DEFAULT false,
    breaking_change BOOLEAN DEFAULT false,
    dependencies JSONB, -- Array of feature IDs
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,

    CONSTRAINT valid_feature_status CHECK (status IN ('planned', 'in-development', 'beta', 'stable', 'deprecated')),
    CONSTRAINT valid_feature_type CHECK (feature_type IN ('core', 'premium', 'addon'))
);

CREATE INDEX idx_feature_module ON features(module_code);
CREATE INDEX idx_feature_status ON features(status);
CREATE INDEX idx_feature_public ON features(public_visible);

-- Releases Table
CREATE TABLE releases (
    id SERIAL PRIMARY KEY,
    release_id VARCHAR(100) UNIQUE NOT NULL,
    module_code VARCHAR(50) NOT NULL REFERENCES module_registry(module_code) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    release_type VARCHAR(20) NOT NULL, -- major, minor, patch
    release_date TIMESTAMP NOT NULL,
    environment VARCHAR(50) NOT NULL, -- staging, production
    changelog JSONB, -- Array of change entries
    breaking_changes TEXT[],
    migration_notes TEXT,
    git_commit VARCHAR(40),
    deployed_by VARCHAR(100),
    status VARCHAR(50) NOT NULL, -- scheduled, deployed, rolled-back
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,

    CONSTRAINT valid_release_type CHECK (release_type IN ('major', 'minor', 'patch')),
    CONSTRAINT valid_release_status CHECK (status IN ('scheduled', 'deployed', 'rolled-back'))
);

CREATE INDEX idx_release_module ON releases(module_code);
CREATE INDEX idx_release_version ON releases(version);
CREATE INDEX idx_release_date ON releases(release_date DESC);

-- Clients Table
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    business_type VARCHAR(50),
    contact JSONB, -- {email, phone, address}
    status VARCHAR(50) NOT NULL, -- prospect, trial, active, churned
    subscription_start DATE,
    subscription_end DATE,
    modules_subscribed VARCHAR(50)[], -- Array of module codes
    custom_features TEXT[],
    support_tier VARCHAR(50), -- basic, premium, enterprise
    account_manager VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,

    CONSTRAINT valid_client_status CHECK (status IN ('prospect', 'trial', 'active', 'churned'))
);

CREATE INDEX idx_client_status ON clients(status);
CREATE INDEX idx_client_subscription ON clients(subscription_end);

-- Deployment History Table
CREATE TABLE deployment_history (
    id SERIAL PRIMARY KEY,
    release_id VARCHAR(100) REFERENCES releases(release_id),
    module_code VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    deployed_at TIMESTAMP NOT NULL,
    deployed_by VARCHAR(100),
    status VARCHAR(50) NOT NULL, -- success, failed, rolled-back
    rollback_at TIMESTAMP,
    rollback_reason TEXT,
    metadata JSONB
);

CREATE INDEX idx_deployment_module ON deployment_history(module_code);
CREATE INDEX idx_deployment_date ON deployment_history(deployed_at DESC);
```

---

## 5. API Contracts

### 5.1 Internal API (Admin Access)

**Authentication:** JWT token dengan role admin/developer

#### Module Registry Endpoints

```
POST   /api/internal/modules
GET    /api/internal/modules
GET    /api/internal/modules/:code
PUT    /api/internal/modules/:code
DELETE /api/internal/modules/:code
```

**Example: Create Module**
```http
POST /api/internal/modules
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "module_code": "gym",
  "module_name": "Fitness Center Management",
  "description": "Gym membership, class scheduling, and equipment tracking",
  "category": "core",
  "parent_module": null,
  "current_version": "1.0.0",
  "status": "beta",
  "public_visible": false,
  "docs_url": "https://docs.example.com/gym",
  "repo_url": "https://github.com/company/gym"
}
```

#### Feature Tracking Endpoints

```
POST   /api/internal/features
GET    /api/internal/features?module_code=pms
GET    /api/internal/features/:id
PUT    /api/internal/features/:id
DELETE /api/internal/features/:id
```

#### Release Management Endpoints

```
POST   /api/internal/releases
GET    /api/internal/releases?module_code=pms&environment=production
GET    /api/internal/releases/:id
PUT    /api/internal/releases/:id
POST   /api/internal/releases/:id/deploy
POST   /api/internal/releases/:id/rollback
```

**Example: Create Release**
```http
POST /api/internal/releases
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "module_code": "pms",
  "version": "2.6.0",
  "release_type": "minor",
  "release_date": "2024-12-30T10:00:00Z",
  "environment": "staging",
  "changelog": [
    {
      "type": "feature",
      "description": "Add multi-language support for guest communications"
    },
    {
      "type": "improvement",
      "description": "Improve check-in performance by 40%"
    }
  ],
  "breaking_changes": [],
  "migration_notes": "Run migration 046_add_i18n_fields.sql"
}
```

### 5.2 Public API (Read-Only)

**Authentication:** API key atau public access (rate-limited)

#### Public Module List

```
GET /api/public/modules
GET /api/public/modules/:code
GET /api/public/modules/:code/features
GET /api/public/modules/:code/releases
```

**Example Response:**
```json
{
  "modules": [
    {
      "code": "pms",
      "name": "Property Management System",
      "description": "Core hotel operations management",
      "category": "core",
      "version": "2.5.3",
      "status": "stable",
      "features_count": 45,
      "icon_url": "/assets/icons/pms.svg"
    },
    {
      "code": "pos",
      "name": "Point of Sale",
      "description": "F&B and retail management",
      "category": "core",
      "version": "1.8.2",
      "status": "stable",
      "features_count": 28,
      "icon_url": "/assets/icons/pos.svg"
    }
  ],
  "total": 14,
  "public_only": true
}
```

#### Public Feature List

```
GET /api/public/features?module=pms&status=stable
```

**Example Response:**
```json
{
  "features": [
    {
      "id": "pms_online_checkin",
      "name": "Online Check-in",
      "description": "Guest self-service check-in",
      "type": "premium",
      "status": "stable",
      "since_version": "2.3.0"
    }
  ],
  "module": "pms",
  "total": 45
}
```

#### Public Changelog

```
GET /api/public/releases?module=pms&limit=10
```

---

## 6. CI/CD Integration

### 6.1 Auto-Update Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CI/CD AUTO-UPDATE FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Developer push code & tag version                                   │
│     git tag v2.6.0                                                      │
│     git push origin v2.6.0                                              │
│                                                                         │
│  2. CI/CD Pipeline triggers                                             │
│     • Run tests                                                         │
│     • Build application                                                 │
│     • Generate changelog from commits                                   │
│     • Extract version from tag                                          │
│                                                                         │
│  3. Update Internal Dev Management via API                              │
│     POST /api/internal/releases                                         │
│     {                                                                   │
│       "module_code": "pms",                                             │
│       "version": "2.6.0",                                               │
│       "changelog": [...auto-generated...],                              │
│       "git_commit": "a3f2c1b"                                           │
│     }                                                                   │
│                                                                         │
│  4. Deploy to environment                                               │
│     • Deploy to staging/production                                      │
│     • Update deployment_history table                                   │
│                                                                         │
│  5. Notify stakeholders                                                 │
│     • Send notification to team                                         │
│     • Trigger website rebuild (if public_visible)                       │
│     • Update documentation                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 GitHub Actions Example

```yaml
# .github/workflows/deploy-and-update-registry.yml
name: Deploy and Update Registry

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Extract version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Generate changelog
        id: changelog
        run: |
          # Extract commits since last tag
          CHANGELOG=$(git log $(git describe --tags --abbrev=0 HEAD^)..HEAD --pretty=format:'{"type":"commit","message":"%s"}' | jq -s '.')
          echo "CHANGELOG=$CHANGELOG" >> $GITHUB_OUTPUT

      - name: Run tests
        run: pytest

      - name: Build application
        run: docker build -t myapp:${{ steps.version.outputs.VERSION }} .

      - name: Update Internal Dev Management
        env:
          API_TOKEN: ${{ secrets.INTERNAL_API_TOKEN }}
          VERSION: ${{ steps.version.outputs.VERSION }}
        run: |
          curl -X POST https://internal.example.com/api/internal/releases \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
              "module_code": "pms",
              "version": "'$VERSION'",
              "release_type": "minor",
              "environment": "production",
              "changelog": ${{ steps.changelog.outputs.CHANGELOG }},
              "git_commit": "'$GITHUB_SHA'"
            }'

      - name: Deploy to production
        run: |
          # Deploy commands here
          kubectl apply -f k8s/production/
```

---

## 7. Governance & Security

### 7.1 Access Control

**Internal API:**
- Require authentication (JWT)
- Role-based access:
  - `admin` - Full access (CRUD all)
  - `developer` - Read all, write limited (features, releases)
  - `viewer` - Read only

**Public API:**
- API key untuk identification
- Rate limiting (100 req/min per IP)
- Only public_visible=true data exposed
- No write access

### 7.2 Audit Log

Semua perubahan data dicatat:
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- insert, update, delete
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT NOW(),
    old_value JSONB,
    new_value JSONB,
    metadata JSONB
);
```

### 7.3 Data Validation

**Before insert/update:**
- Validate semantic versioning format
- Check module_code exists in registry
- Validate status transitions (planned → in-progress → beta → stable)
- Ensure public_visible only for stable status

---

## 8. Dashboard & Monitoring

### 8.1 Internal Dashboard Features

**Module Overview:**
- Total modules by category
- Development status distribution
- Recently updated modules

**Release Timeline:**
- Upcoming releases (scheduled)
- Recent deployments
- Deployment success rate

**Client Management:**
- Active clients count
- Popular modules (most subscribed)
- Subscription expiry alerts

**Development Metrics:**
- Features added per month
- Bug fix rate
- Time to production (from commit to deploy)

### 8.2 Monitoring & Alerts

**Health Checks:**
- API endpoint availability
- Database connection
- External integrations (website, docs)

**Alerts:**
- Deployment failures
- Rollback executed
- API rate limit exceeded
- Subscription expiring soon

---

## 9. Migration & Rollback

### 9.1 Version Rollback

Jika deployment gagal, rollback metadata:
```sql
-- Rollback release status
UPDATE releases
SET status = 'rolled-back',
    metadata = jsonb_set(metadata, '{rollback_reason}', '"Deployment failed"')
WHERE release_id = 'rel_001';

-- Record rollback in history
INSERT INTO deployment_history (release_id, status, rollback_at, rollback_reason)
VALUES ('rel_001', 'rolled-back', NOW(), 'Deployment failed');
```

### 9.2 Data Migration

Saat struktur berubah, migrate data dengan care:
- Backup before migration
- Test migration di staging
- Rollback plan ready

---

## 10. Best Practices

### 10.1 DO's

✅ **Update registry via CI/CD**
- Jangan manual update, automate via pipeline

✅ **Use semantic versioning**
- major.minor.patch format consistently

✅ **Document breaking changes**
- Always note breaking changes in releases

✅ **Set public_visible carefully**
- Only stable features should be public

✅ **Keep changelog accurate**
- Auto-generate + manual review

### 10.2 DON'Ts

❌ **Jangan edit production data manual**
- Always via API dengan audit trail

❌ **Jangan skip version numbers**
- Follow semantic versioning strictly

❌ **Jangan expose internal features**
- Use public_visible flag correctly

❌ **Jangan deploy tanpa update registry**
- CI/CD must update registry first

---

## 11. Future Enhancements

### 11.1 Roadmap

**Phase 2:**
- AI-powered changelog generation
- Automated dependency conflict detection
- Performance metrics per module

**Phase 3:**
- A/B testing framework integration
- Multi-language support for descriptions
- Customer feedback integration

**Phase 4:**
- Predictive analytics for adoption
- Automated deprecation warnings
- Smart feature recommendations

---

## 12. Reference

**Related Documents:**
- [SPEC-06: Public Website Integration](./SPEC-06-public-website-integration.md)
- [ARCH-02: Module Architecture](./ARCH-02-module-architecture.md)
- [STD-05: Feature Flags](./STD-05-notification-versioning-flags-sla.md#25-feature-flags-standard)
- [GUIDE-01: Development Flow](./GUIDE-01-development-flow.md)

**External Resources:**
- Semantic Versioning: https://semver.org
- Conventional Commits: https://www.conventionalcommits.org
- API Versioning Best Practices

---

**Last Updated:** 2024-12-23
**Status:** DRAFT - Ready for Review
**Owner:** Engineering Team
