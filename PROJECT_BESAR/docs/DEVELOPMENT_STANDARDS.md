# Development Standards

> Standar fundamental yang berlaku untuk SEMUA code di platform.
>
> **Last Updated**: 2025-12-06
> **Status**: Draft - Sedang dirumuskan

---

## Quick Reference

| # | Category | Status |
|---|----------|--------|
| 1 | Naming Conventions | ✅ Approved |
| 2 | Database Patterns | ✅ Approved |
| 3 | RBAC / Permission | ✅ Approved |
| 4 | Audit Log | ✅ Approved |
| 5 | Caching | ✅ Approved |
| 6 | API Patterns | ✅ Approved |
| 7 | Error Handling | ✅ Approved |
| 8 | Validation | ⏳ Pending |
| 9 | Testing | ⏳ Pending |
| 10 | Code Structure | ⏳ Pending |
| 11 | Frontend Patterns | ⏳ Pending |
| 12 | Cleanup / Maintenance | ⏳ Pending |

---

## 1. Naming Conventions ✅

### 1.1 Database

| Element | Convention | Example |
|---------|------------|---------|
| **Tables** | plural, snake_case | `users`, `room_types`, `folio_transactions` |
| **Columns** | snake_case | `first_name`, `check_in_date`, `total_amount` |
| **Primary Key** | `id` (integer, auto-increment) | `id` |
| **Foreign Key** | `{referenced_table_singular}_id` | `user_id`, `organization_id`, `room_type_id` |
| **Boolean** | `is_`, `has_`, `can_` prefix | `is_active`, `has_breakfast`, `can_cancel` |
| **Timestamp** | `_at` suffix | `created_at`, `updated_at`, `deleted_at`, `checked_in_at` |
| **Date only** | `_date` suffix | `arrival_date`, `departure_date`, `birth_date` |
| **Count/Amount** | descriptive | `total_nights`, `room_count`, `total_amount` |
| **Index** | `idx_{table}_{columns}` | `idx_users_email`, `idx_reservations_org_date` |
| **Foreign Key Constraint** | `fk_{table}_{ref_table}` | `fk_users_organizations`, `fk_folios_guests` |
| **Check Constraint** | `chk_{table}_{rule}` | `chk_users_email_format`, `chk_rates_positive` |
| **Unique Constraint** | `uq_{table}_{columns}` | `uq_users_email`, `uq_rooms_org_number` |

**Examples:**
```sql
-- Good
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    guest_id INTEGER NOT NULL REFERENCES guests(id),
    room_type_id INTEGER NOT NULL REFERENCES room_types(id),
    arrival_date DATE NOT NULL,
    departure_date DATE NOT NULL,
    total_nights INTEGER NOT NULL,
    total_amount NUMERIC(15,4) NOT NULL,
    is_guaranteed BOOLEAN DEFAULT FALSE NOT NULL,
    is_cancelled BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_reservations_org_arrival ON reservations(organization_id, arrival_date);
ALTER TABLE reservations ADD CONSTRAINT chk_reservations_dates
    CHECK (departure_date > arrival_date);

-- Bad
CREATE TABLE Reservation (                    -- singular, PascalCase
    reservation_id INTEGER PRIMARY KEY,       -- should be just 'id'
    org INTEGER,                              -- not descriptive, no _id suffix
    guestId INTEGER,                          -- camelCase
    active BOOLEAN,                           -- missing is_ prefix
    created TIMESTAMP                         -- missing _at suffix
);
```

---

### 1.2 Python Backend

| Element | Convention | Example |
|---------|------------|---------|
| **Class** | PascalCase | `UserModel`, `ReservationDTO`, `CreateBookingUseCase` |
| **Function** | snake_case | `get_user_by_id`, `create_reservation`, `validate_dates` |
| **Method** | snake_case | `def calculate_total(self):` |
| **Variable** | snake_case | `user_count`, `is_valid`, `total_amount` |
| **Constant** | UPPER_SNAKE_CASE | `MAX_RETRY`, `DEFAULT_PAGE_SIZE`, `JWT_EXPIRY` |
| **Private** | `_` prefix | `_internal_method`, `_cached_value` |
| **File** | snake_case.py | `user_model.py`, `auth_routes.py`, `create_booking.py` |
| **Module/Folder** | snake_case | `services/`, `use_cases/`, `repositories/` |

**Class Naming by Type:**
| Type | Pattern | Example |
|------|---------|---------|
| SQLAlchemy Model | `{Entity}Model` | `UserModel`, `ReservationModel` |
| Pydantic DTO | `{Entity}{Action}DTO` | `UserCreateDTO`, `UserResponseDTO` |
| Repository | `{Entity}Repository` | `UserRepository`, `ReservationRepository` |
| Use Case | `{Action}{Entity}UseCase` | `CreateReservationUseCase`, `GetUserUseCase` |
| Service | `{Entity}Service` | `AuthService`, `PaymentService` |
| Exception | `{Description}Error` | `ValidationError`, `NotFoundError` |

**Examples:**
```python
# Good
class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    is_cancelled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CreateReservationDTO(BaseModel):
    guest_id: int
    room_type_id: int
    arrival_date: date
    departure_date: date


class CreateReservationUseCase:
    def __init__(self, reservation_repo: ReservationRepository):
        self._reservation_repo = reservation_repo

    def execute(self, dto: CreateReservationDTO) -> ReservationModel:
        total_nights = self._calculate_nights(dto.arrival_date, dto.departure_date)
        # ...


# Bad
class reservation:                    # lowercase, should be PascalCase
    pass

class ReservationDto:                 # inconsistent, should be DTO uppercase
    pass

def GetUserById():                    # PascalCase, should be snake_case
    pass

def createReservation():              # camelCase, should be snake_case
    pass
```

---

### 1.3 React Frontend

| Element | Convention | Example |
|---------|------------|---------|
| **Component** | PascalCase | `UserList`, `LoginForm`, `ReservationCard` |
| **Component File** | PascalCase.tsx | `UserList.tsx`, `LoginForm.tsx` |
| **Hook** | camelCase, `use` prefix | `useUsers`, `useAuth`, `useReservations` |
| **Hook File** | camelCase.ts | `useUsers.ts`, `useAuth.ts` |
| **Type/Interface** | PascalCase | `User`, `Reservation`, `ApiResponse` |
| **Type File** | camelCase.ts atau index.ts | `types.ts`, `user.types.ts` |
| **Constant** | UPPER_SNAKE_CASE | `API_BASE_URL`, `MAX_FILE_SIZE` |
| **Variable** | camelCase | `userName`, `isLoading`, `totalCount` |
| **Function** | camelCase | `handleSubmit`, `formatDate`, `calculateTotal` |
| **Folder (feature)** | camelCase atau kebab-case | `users/`, `room-types/` |
| **API file** | camelCase + Api suffix | `userApi.ts`, `reservationApi.ts` |

**File Structure Pattern:**
```
features/
└── reservations/
    ├── api/
    │   └── reservationApi.ts
    ├── components/
    │   ├── ReservationList.tsx
    │   ├── ReservationCard.tsx
    │   └── ReservationForm.tsx
    ├── hooks/
    │   ├── useReservations.ts
    │   └── useReservationForm.ts
    └── types/
        └── index.ts
```

**Examples:**
```tsx
// Good - UserList.tsx
interface User {
  id: number;
  firstName: string;
  lastName: string;
  isActive: boolean;
  createdAt: string;
}

interface UserListProps {
  organizationId: number;
  onUserSelect: (user: User) => void;
}

export function UserList({ organizationId, onUserSelect }: UserListProps) {
  const { data: users, isLoading } = useUsers(organizationId);

  const handleUserClick = (user: User) => {
    onUserSelect(user);
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="user-list">
      {users.map(user => (
        <UserCard key={user.id} user={user} onClick={handleUserClick} />
      ))}
    </div>
  );
}

// Bad
interface user {                      // lowercase, should be PascalCase
  ID: number;                         // uppercase, should be camelCase
  first_name: string;                 // snake_case, should be camelCase
}

function userList() {                 // lowercase, should be PascalCase
  const Users = useUsers();           // PascalCase variable, should be camelCase
  const handle_click = () => {};      // snake_case, should be camelCase
}
```

---

### 1.4 API Endpoints

| Element | Convention | Example |
|---------|------------|---------|
| **Base Path** | `/api/v{version}` | `/api/v1` |
| **Resource** | plural, kebab-case | `/users`, `/room-types`, `/folio-transactions` |
| **Single Resource** | `/{resource}/{id}` | `/users/1`, `/reservations/123` |
| **Nested Resource** | `/{parent}/{id}/{child}` | `/users/1/roles`, `/hotels/5/rooms` |
| **Action** | verb at end (only if needed) | `/auth/login`, `/auth/logout`, `/reports/generate` |
| **Query Params** | snake_case | `?page=1&page_size=20&sort_by=created_at` |
| **Filter Params** | snake_case | `?is_active=true&organization_id=5` |

**HTTP Methods:**
| Action | Method | URL Pattern | Example |
|--------|--------|-------------|---------|
| List | GET | `/{resource}` | `GET /api/v1/users` |
| Get One | GET | `/{resource}/{id}` | `GET /api/v1/users/1` |
| Create | POST | `/{resource}` | `POST /api/v1/users` |
| Full Update | PUT | `/{resource}/{id}` | `PUT /api/v1/users/1` |
| Partial Update | PATCH | `/{resource}/{id}` | `PATCH /api/v1/users/1` |
| Delete | DELETE | `/{resource}/{id}` | `DELETE /api/v1/users/1` |
| Custom Action | POST | `/{resource}/{id}/{action}` | `POST /api/v1/reservations/1/cancel` |

**Examples:**
```
# Good
GET    /api/v1/reservations
GET    /api/v1/reservations/123
POST   /api/v1/reservations
PATCH  /api/v1/reservations/123
DELETE /api/v1/reservations/123
POST   /api/v1/reservations/123/cancel
POST   /api/v1/reservations/123/check-in
GET    /api/v1/hotels/5/rooms
GET    /api/v1/reservations?status=confirmed&arrival_date=2025-01-15

# Bad
GET    /api/v1/getReservations           # verb in URL
GET    /api/v1/reservation/123           # singular
POST   /api/v1/reservations/create       # redundant 'create'
GET    /api/v1/Reservations              # PascalCase
GET    /api/v1/reservations?arrivalDate  # camelCase query param
```

---

### 1.5 Environment Variables

| Element | Convention | Example |
|---------|------------|---------|
| **Format** | UPPER_SNAKE_CASE | `DATABASE_URL`, `REDIS_HOST` |
| **Prefix by Service** | `{SERVICE}_` | `DB_`, `REDIS_`, `JWT_`, `S3_` |
| **Boolean** | `true`/`false` string | `DEBUG=true`, `ENABLE_CACHE=false` |
| **List** | comma-separated | `CORS_ORIGINS=http://a.com,http://b.com` |

**Standard Variables:**
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=signage_db
DB_USER=signage_user
DB_PASSWORD=secret
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
JWT_REFRESH_EXPIRY_DAYS=7

# Application
APP_ENV=development
APP_DEBUG=true
APP_PORT=8001
APP_HOST=0.0.0.0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Storage
S3_BUCKET=signage-content
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# External Services
RABBITMQ_URL=amqp://guest:guest@localhost:5672
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## 2. Database Patterns ✅

### 2.0 Arsitektur Database (2-Layer + Schema per App)

Platform ini menggunakan arsitektur **2-layer database** dengan **schema per app**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATABASE PLATFORM                                │
│                           (1 - Shared)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  • users              → Semua orang yang daftar                         │
│  • organizations      → Semua bisnis (hotel, supplier, resto, dll)      │
│  • user_organizations → Siapa kerja/akses dimana                        │
│  • apps               → Katalog aplikasi yang tersedia                  │
│  • app_permissions    → Permission yang tersedia per app                │
│  • subscriptions      → Org subscribe app apa                           │
│  • billing            → Pembayaran subscription                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Setiap org dapat database sendiri
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATABASE ORGANIZATION (per org)                       │
│                      Contoh: db_hotel_grandjaya                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SCHEMA: shared (data bersama)                                          │
│  ├── roles                    → Role custom org                         │
│  ├── role_permissions         → Permission per role                     │
│  ├── user_roles               → User assignment ke role                 │
│  └── settings                 → Pengaturan org                          │
│                                                                          │
│  SCHEMA: pms (kalau subscribe PMS)                                      │
│  ├── reservations                                                        │
│  ├── rooms                                                               │
│  ├── guests                                                              │
│  ├── folios                                                              │
│  └── audit_logs               → Log khusus PMS                          │
│                                                                          │
│  SCHEMA: accounting (kalau subscribe Accounting)                        │
│  ├── accounts                                                            │
│  ├── journals                                                            │
│  ├── invoices                                                            │
│  └── audit_logs               → Log khusus Accounting                   │
│                                                                          │
│  SCHEMA: hrm (kalau subscribe HRM)                                      │
│  ├── employees                                                           │
│  ├── attendance                                                          │
│  ├── payroll                                                             │
│  └── audit_logs               → Log khusus HRM                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Ringkasan Arsitektur:**

```
JUMLAH DATABASE:
├── Platform DB    : 1 (untuk semua)
└── Organization DB: 1 per organisasi (BUKAN per app!)

JUMLAH SCHEMA (di dalam Org DB):
├── shared    : 1 (selalu ada)
└── {app}     : 1 per app yang di-subscribe (pms, accounting, hrm, dll)
```

**Prinsip:**

| Aspek | Platform DB | Organization DB |
|-------|-------------|-----------------|
| Jumlah | 1 (shared) | 1 per organization |
| Isi | Users, orgs, apps, billing | Data transaksi per app |
| Schema | 1 (public) | 1 per app + shared |
| `organization_id` | Ya (untuk relasi) | **TIDAK PERLU** |
| Backup | Backup 1x | Backup per org atau per schema/app |
| Isolation | Shared | 100% terpisah |

**Keuntungan Schema per App:**
- ✅ Backup per app: `pg_dump -n pms db_hotel_a > pms_backup.sql`
- ✅ Unsubscribe = archive schema, data aman
- ✅ Subscribe lagi = restore schema
- ✅ Audit log terpisah per app
- ✅ Isolasi antar app dalam 1 database

**Connection Pattern:**
```python
# Platform DB - untuk auth, user management
platform_db = get_platform_database()

# Organization DB - dipilih berdasarkan user login
org_db = get_organization_database(organization_id=current_user.organization_id)

# Set schema untuk app tertentu
org_db.execute("SET search_path TO pms, shared")

# Atau pakai schema prefix
org_db.execute("SELECT * FROM pms.reservations")
```

**Backup & Restore per App:**
```bash
# Backup schema PMS saja
pg_dump -n pms db_hotel_a > hotel_a_pms_backup.sql

# Backup schema Accounting saja
pg_dump -n accounting db_hotel_a > hotel_a_accounting_backup.sql

# Restore schema
psql db_hotel_a < hotel_a_pms_backup.sql

# Archive schema (unsubscribe tapi keep data)
ALTER SCHEMA pms RENAME TO pms_archived_20250101;

# Drop schema (hapus permanen)
DROP SCHEMA pms CASCADE;
```

---

### 2.1 Audit Columns (WAJIB Semua Table)

Setiap table WAJIB memiliki audit columns berikut:

```sql
-- Minimal Audit Columns
created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
created_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
updated_at      TIMESTAMP WITH TIME ZONE,
updated_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,

-- Untuk table yang support soft delete (hampir semua)
deleted_at      TIMESTAMP WITH TIME ZONE,
deleted_by_id   INTEGER REFERENCES users(id) ON DELETE SET NULL
```

**Variasi untuk context tertentu:**
| Context | Column Name | Example |
|---------|-------------|---------|
| Upload | `uploaded_by_id` | contents, documents |
| Assignment | `assigned_by_id` | room_assignments, tasks |
| Approval | `approved_by_id` | purchase_orders, leave_requests |
| Cancellation | `cancelled_by_id` | reservations, orders |

**Template Table Lengkap:**
```sql
CREATE TABLE example_table (
    -- Primary Key
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- External UUID (untuk API exposure)
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- Multi-tenancy (jika applicable)
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Business columns
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active' NOT NULL,

    -- Booleans
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT chk_example_status CHECK (status IN ('active', 'inactive', 'pending'))
);

-- Indexes
CREATE INDEX idx_example_table_org ON example_table(organization_id);
CREATE INDEX idx_example_table_status ON example_table(status) WHERE deleted_at IS NULL;
```

---

### 2.2 Soft Delete

**Rule:** Semua table menggunakan soft delete, KECUALI:
- Log tables (audit_logs, activity_logs) → tidak perlu delete
- Temporary/session tables → bisa hard delete
- Junction tables tanpa data penting → bisa hard delete

**Pattern:**
```sql
-- Soft delete: set deleted_at
UPDATE users SET
    deleted_at = NOW(),
    deleted_by_id = :current_user_id
WHERE id = :user_id;

-- Query active records (SELALU filter deleted_at)
SELECT * FROM users WHERE deleted_at IS NULL;

-- Query including deleted (untuk admin/audit)
SELECT * FROM users; -- tanpa filter

-- Restore soft deleted
UPDATE users SET
    deleted_at = NULL,
    deleted_by_id = NULL
WHERE id = :user_id;
```

**Repository Pattern:**
```python
class BaseRepository:
    def get_all(self, include_deleted: bool = False):
        query = select(self.model)
        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        return query

    def soft_delete(self, id: int, deleted_by_id: int):
        entity = self.get_by_id(id)
        entity.deleted_at = datetime.now(timezone.utc)
        entity.deleted_by_id = deleted_by_id
        return entity
```

---

### 2.3 Multi-Tenancy (Database per Org + Schema per App)

**Rule:**
- Setiap organization punya **database sendiri**
- Setiap app yang di-subscribe punya **schema sendiri**
- `organization_id` **TIDAK PERLU** di organization database

**PLATFORM DATABASE (shared):**
```sql
-- Table yang PERLU organization_id (untuk relasi)
CREATE TABLE user_organizations (
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    is_owner BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, organization_id)
);

CREATE TABLE org_subscriptions (
    organization_id INTEGER REFERENCES organizations(id),
    app_id INTEGER REFERENCES apps(id),
    plan VARCHAR(50),
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (organization_id, app_id)
);
```

**ORGANIZATION DATABASE - Schema Structure:**
```sql
-- Schema shared (selalu ada)
CREATE SCHEMA shared;

-- Schema per app (dibuat saat subscribe)
CREATE SCHEMA pms;         -- kalau subscribe PMS
CREATE SCHEMA accounting;  -- kalau subscribe Accounting
CREATE SCHEMA hrm;         -- kalau subscribe HRM
```

**ORGANIZATION DATABASE - Table Examples:**
```sql
-- Schema shared: data bersama semua app
CREATE TABLE shared.roles (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    ...
);

-- Schema pms: tabel khusus PMS
CREATE TABLE pms.reservations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    -- organization_id TIDAK PERLU
    guest_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    arrival_date DATE NOT NULL,
    ...
);

CREATE TABLE pms.rooms (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    room_number VARCHAR(20) NOT NULL,
    ...
);

-- Schema accounting: tabel khusus Accounting
CREATE TABLE accounting.journals (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    journal_date DATE NOT NULL,
    ...
);
```

**Link ke Platform User:**
```sql
-- user_id adalah ID dari platform.users (cross-database reference)
CREATE TABLE hrm.employees (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INTEGER NOT NULL,  -- FK ke platform.users
    employee_code VARCHAR(20),
    ...
);

-- Audit columns pakai user_id dari platform
created_by_id INTEGER,  -- user_id dari platform
updated_by_id INTEGER,  -- user_id dari platform
```

**Query dengan Schema:**
```sql
-- Set search path untuk app tertentu
SET search_path TO pms, shared;
SELECT * FROM reservations;  -- pms.reservations
SELECT * FROM roles;         -- shared.roles

-- Atau pakai schema prefix eksplisit
SELECT * FROM pms.reservations;
SELECT * FROM shared.roles;
SELECT * FROM accounting.journals;
```

---

### 2.4 Primary Key Strategy

**Rule:** Integer untuk internal, UUID untuk external API.

```sql
CREATE TABLE users (
    -- Internal PK (untuk joins, FK references)
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- External ID (untuk API exposure, tidak predictable)
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- ... other columns
);

-- Internal use: pakai id
SELECT * FROM users WHERE id = 123;
SELECT * FROM reservations WHERE user_id = 123;

-- API exposure: pakai uuid
GET /api/v1/users/550e8400-e29b-41d4-a716-446655440000
```

**Kenapa?**
- Integer: Faster joins, smaller indexes, auto-increment
- UUID: Not predictable (security), globally unique, safe for API

---

### 2.5 Timestamps

**Rule:** Semua timestamp WITH TIME ZONE, store in UTC.

```sql
-- Column definition
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL

-- Storing (always UTC)
INSERT INTO events (name, event_time)
VALUES ('Meeting', '2025-01-15 14:00:00+07:00');
-- Stored as: 2025-01-15 07:00:00+00:00 (UTC)

-- Querying with timezone conversion
SELECT
    name,
    event_time AT TIME ZONE 'Asia/Jakarta' as local_time
FROM events;
```

**Application Layer:**
```python
from datetime import datetime, timezone

# Always use UTC in backend
now_utc = datetime.now(timezone.utc)

# Convert for display
from zoneinfo import ZoneInfo
local_tz = ZoneInfo("Asia/Jakarta")
local_time = now_utc.astimezone(local_tz)
```

---

### 2.6 Money / Currency

**Rule:** NUMERIC(15,4) untuk semua monetary amounts.

```sql
-- Column definition
total_amount NUMERIC(15,4) NOT NULL,
tax_amount NUMERIC(15,4) NOT NULL DEFAULT 0,
discount_amount NUMERIC(15,4) NOT NULL DEFAULT 0,
exchange_rate NUMERIC(15,6) NOT NULL DEFAULT 1,  -- 6 decimals untuk rate

-- Constraints
CONSTRAINT chk_positive_amount CHECK (total_amount >= 0)
```

**Kenapa NUMERIC(15,4)?**
- 15 digits total: supports up to 99,999,999,999.9999 (cukup untuk IDR billions)
- 4 decimal places: precision untuk tax calculations
- NUMERIC not FLOAT: exact precision, no floating-point errors

**Python:**
```python
from decimal import Decimal, ROUND_HALF_UP

# Use Decimal, not float
amount = Decimal("1000.50")
tax_rate = Decimal("0.11")
tax = (amount * tax_rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
```

---

### 2.7 Status / Enum Handling

**Rule:** VARCHAR + CHECK constraint (bukan PostgreSQL ENUM).

```sql
-- Recommended: VARCHAR + CHECK
status VARCHAR(50) NOT NULL DEFAULT 'pending',
CONSTRAINT chk_reservation_status CHECK (
    status IN ('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show')
)

-- NOT recommended: PostgreSQL ENUM
-- CREATE TYPE reservation_status AS ENUM ('pending', 'confirmed', ...);
-- Alasan: Sulit modify (add/remove values), migration kompleks
```

**Alternative: Lookup Table (untuk status yang kompleks)**
```sql
-- Lookup table
CREATE TABLE reservation_statuses (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- Main table
status_code VARCHAR(50) NOT NULL REFERENCES reservation_statuses(code)
```

**Kapan pakai apa:**
| Approach | Kapan Dipakai |
|----------|---------------|
| VARCHAR + CHECK | Status simple, jarang berubah (3-10 values) |
| Lookup Table | Status kompleks, perlu metadata, user-configurable |

---

### 2.8 JSON Columns

**Rule:** Gunakan JSONB untuk flexible/dynamic data.

**Kapan pakai JSONB:**
- User preferences (language, theme, notifications)
- Metadata (custom fields, external data)
- Settings/config per entity
- Denormalized data untuk performance

**Kapan TIDAK pakai JSONB:**
- Data yang sering di-query/filter → normalize ke columns
- Relationships → use proper FK
- Critical business data → normalize

**Pattern:**
```sql
-- Column definition
preferences JSONB DEFAULT '{}' NOT NULL,
metadata JSONB DEFAULT '{}' NOT NULL,
settings JSONB DEFAULT '{}' NOT NULL,

-- Example data
preferences = {
    "language": "id",
    "theme": "dark",
    "notifications": {
        "email": true,
        "push": false
    }
}

-- Querying JSONB
SELECT * FROM users
WHERE preferences->>'language' = 'id';

SELECT * FROM users
WHERE preferences->'notifications'->>'email' = 'true';

-- Index untuk JSONB (jika sering di-query)
CREATE INDEX idx_users_preferences ON users USING GIN (preferences);
```

**Naming Convention untuk JSONB columns:**
| Name | Purpose | Example Content |
|------|---------|-----------------|
| `preferences` | User/entity preferences | `{"language": "id", "theme": "dark"}` |
| `metadata` | External/system metadata | `{"source": "api", "imported_at": "..."}` |
| `settings` | Configuration settings | `{"max_attempts": 3, "timeout": 30}` |
| `extra_data` | Additional flexible data | `{"custom_field_1": "value"}` |
| `config` | Technical configuration | `{"retry": true, "batch_size": 100}` |

---

### 2.9 Standard Table Templates

#### Template A: Platform Database Table

```sql
-- ============================================================
-- TEMPLATE: Platform Database Table (Shared)
-- ============================================================
CREATE TABLE {table_name} (
    -- PRIMARY KEY
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- RELASI KE ORGANIZATION (jika perlu)
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,

    -- BUSINESS COLUMNS
    -- ... your columns here ...

    -- STATUS & FLAGS
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- AUDIT TRAIL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- CONSTRAINTS
    CONSTRAINT chk_{table_name}_status CHECK (status IN ('active', 'inactive'))
);

-- INDEXES
CREATE INDEX idx_{table_name}_org ON {table_name}(organization_id);
CREATE INDEX idx_{table_name}_status ON {table_name}(status) WHERE deleted_at IS NULL;
```

#### Template B: Organization Shared Schema Table

```sql
-- ============================================================
-- TEMPLATE: Organization Shared Schema (data bersama antar app)
-- ============================================================
CREATE TABLE shared.{table_name} (
    -- PRIMARY KEY
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- BUSINESS COLUMNS
    -- ... your columns here ...

    -- STATUS & FLAGS
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- AUDIT TRAIL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER,  -- user_id dari platform
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by_id INTEGER,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_id INTEGER
);

-- INDEXES
CREATE INDEX idx_shared_{table_name}_active ON shared.{table_name}(is_active)
    WHERE deleted_at IS NULL;
```

#### Template C: Organization App Schema Table

```sql
-- ============================================================
-- TEMPLATE: Organization App Schema (per app, misal: pms, accounting)
-- ============================================================
CREATE TABLE {app_schema}.{table_name} (
    -- PRIMARY KEY
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    uuid UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,

    -- ⚠️ TIDAK PERLU organization_id (database sudah terpisah)

    -- BUSINESS COLUMNS
    -- ... your columns here ...

    -- STATUS & FLAGS
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- AUDIT TRAIL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER,  -- user_id dari platform (cross-db reference)
    updated_at TIMESTAMP WITH TIME ZONE,
    updated_by_id INTEGER,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_id INTEGER,

    -- CONSTRAINTS
    CONSTRAINT chk_{table_name}_status CHECK (status IN ('active', 'inactive'))
);

-- INDEXES
CREATE INDEX idx_{app}_{table_name}_status ON {app_schema}.{table_name}(status)
    WHERE deleted_at IS NULL;

-- COMMENTS
COMMENT ON TABLE {app_schema}.{table_name} IS 'Description of table purpose';
```

#### Kapan Pakai Template Mana?

| Template | Database | Schema | Contoh Table |
|----------|----------|--------|--------------|
| **A (Platform)** | Platform DB | public | users, organizations, apps, subscriptions |
| **B (Shared)** | Org DB | shared | roles, role_permissions, user_roles, settings |
| **C (App)** | Org DB | {app} | pms.reservations, accounting.journals, hrm.employees |

---

## 3. RBAC / Permission ✅

### 3.0 Konsep 2-Level RBAC

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LEVEL 1: APP PERMISSIONS (Fixed - dari developer)                      │
│  ─────────────────────────────────────────────────                      │
│  Setiap APP define permission yang tersedia                             │
│                                                                          │
│  APP: PMS              APP: Accounting         APP: HRM                 │
│  ├── reservation:*     ├── journal:*           ├── employee:*           │
│  ├── room:*            ├── invoice:*           ├── payroll:*            │
│  ├── guest:*           ├── payment:*           ├── attendance:*         │
│  └── rate:*            └── report:*            └── leave:*              │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  LEVEL 2: ORG ROLES (Custom - org buat sendiri)                         │
│  ─────────────────────────────────────────────                          │
│  Setiap ORG buat ROLES dan assign permissions                           │
│                                                                          │
│  ORG: Hotel A                      ORG: Hotel B                         │
│  ├── "Front Desk"                  ├── "Receptionist" (nama beda)       │
│  │   └── [permissions...]          │   └── [permissions...]             │
│  ├── "HK Supervisor"               ├── "Housekeeping"                   │
│  │   └── [permissions...]          │   └── [permissions...]             │
│  └── "Accountant"                  └── "Finance Staff"                  │
│      └── [permissions...]              └── [permissions...]             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3.1 Database Structure

#### Platform DB (shared)

```sql
-- Apps yang tersedia
CREATE TABLE apps (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(50) NOT NULL UNIQUE,    -- 'pms', 'accounting', 'hrm'
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Permission yang tersedia PER APP (defined by developer)
CREATE TABLE app_permissions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    app_id INTEGER NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
    code VARCHAR(100) NOT NULL,          -- 'reservation:create'
    module VARCHAR(50) NOT NULL,         -- 'reservation'
    action VARCHAR(50) NOT NULL,         -- 'create'
    name VARCHAR(200) NOT NULL,          -- 'Create Reservation'
    description TEXT,
    UNIQUE(app_id, code)
);

-- Org subscribe app apa
CREATE TABLE org_subscriptions (
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    app_id INTEGER REFERENCES apps(id) ON DELETE CASCADE,
    plan VARCHAR(50),                    -- 'basic', 'pro', 'enterprise'
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (organization_id, app_id)
);

-- User access ke org (tanpa role - role di org db)
CREATE TABLE user_organizations (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    is_owner BOOLEAN DEFAULT FALSE,      -- pemilik org
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, organization_id)
);
```

#### Organization DB (per org)

```sql
-- Role yang dibuat oleh ORG (custom)
CREATE TABLE roles (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,     -- role bawaan tidak bisa dihapus
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_id INTEGER
);

-- Permission yang di-assign ke role
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_code VARCHAR(150) NOT NULL,  -- 'pms:reservation:create'
    PRIMARY KEY (role_id, permission_code)
);

-- User di-assign ke role
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,            -- dari platform.users
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by_id INTEGER,
    PRIMARY KEY (user_id, role_id)
);

-- Override permission per user (optional)
CREATE TABLE user_permissions (
    user_id INTEGER NOT NULL,
    permission_code VARCHAR(150) NOT NULL,
    is_granted BOOLEAN NOT NULL,         -- true=grant, false=revoke
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by_id INTEGER,
    PRIMARY KEY (user_id, permission_code)
);
```

---

### 3.2 Permission Format

**Format:** `{app}:{module}:{action}`

```
CONTOH:
├── pms:reservation:create
├── pms:reservation:read
├── pms:reservation:update
├── pms:reservation:cancel
├── pms:room:manage
├── accounting:journal:create
├── accounting:journal:approve
├── hrm:employee:read
├── hrm:payroll:process
```

**Standard Actions:**

| Action | Deskripsi |
|--------|-----------|
| `read` | View/list data |
| `create` | Buat data baru |
| `update` | Edit data |
| `delete` | Hapus data (soft delete) |
| `restore` | Restore deleted data |
| `manage` | Full CRUD (shortcut) |
| `export` | Export data |
| `import` | Import data |
| `approve` | Approve transaction |
| `reject` | Reject transaction |
| `cancel` | Cancel transaction |
| `void` | Void transaction |
| `process` | Process (payroll, etc) |

---

### 3.3 Permission Check Flow

```
USER request "pms:reservation:create"
         │
         ▼
┌─────────────────────────────────────┐
│ 1. User authenticated?              │  ◄── Platform DB
└─────────────────┬───────────────────┘
                  │ ✅
                  ▼
┌─────────────────────────────────────┐
│ 2. User punya akses ke org ini?     │  ◄── Platform DB (user_organizations)
└─────────────────┬───────────────────┘
                  │ ✅
                  ▼
┌─────────────────────────────────────┐
│ 3. Org subscribe app "pms"?         │  ◄── Platform DB (org_subscriptions)
└─────────────────┬───────────────────┘
                  │ ✅
                  ▼
┌─────────────────────────────────────┐
│ 4. User is owner?                   │  ◄── Platform DB → bypass permission
│    (owner punya full access)        │
└─────────────────┬───────────────────┘
                  │ ❌ (bukan owner)
                  ▼
┌─────────────────────────────────────┐
│ 5. User role punya permission?      │  ◄── Org DB (user_roles + role_permissions)
└─────────────────┬───────────────────┘
                  │ ✅ atau ❌
                  ▼
┌─────────────────────────────────────┐
│ 6. User punya override?             │  ◄── Org DB (user_permissions)
└─────────────────┬───────────────────┘
                  │
                  ▼
              RESULT
```

---

### 3.4 Implementation Pattern

```python
# permission_checker.py

async def check_permission(
    user_id: int,
    organization_id: int,
    permission: str  # e.g., "pms:reservation:create"
) -> bool:
    """Check if user has permission in organization."""

    # 1. Check user access to org
    user_org = await platform_db.get_user_organization(user_id, organization_id)
    if not user_org or not user_org.is_active:
        return False

    # 2. Check org subscribes the app
    app_code = permission.split(":")[0]  # "pms"
    if not await platform_db.org_has_app(organization_id, app_code):
        return False

    # 3. Owner bypass
    if user_org.is_owner:
        return True

    # 4. Check user roles have permission
    org_db = get_org_database(organization_id)
    has_role_permission = await org_db.user_has_role_permission(user_id, permission)

    # 5. Check user override
    override = await org_db.get_user_permission_override(user_id, permission)
    if override is not None:
        return override.is_granted

    return has_role_permission


# Dependency untuk FastAPI
async def require_permission(permission: str):
    async def checker(
        current_user: User = Depends(get_current_user),
        org_id: int = Depends(get_current_org)
    ):
        if not await check_permission(current_user.id, org_id, permission):
            raise HTTPException(403, "Permission denied")
        return True
    return Depends(checker)


# Penggunaan di route
@router.post("/reservations")
async def create_reservation(
    dto: CreateReservationDTO,
    _: bool = Depends(require_permission("pms:reservation:create"))
):
    # User sudah terverifikasi punya permission
    return await use_case.execute(dto)
```

---

### 3.5 Special Cases

**1. Super Admin (Platform Level):**
```python
# Di platform level, untuk maintenance/support
# Tidak masuk flow normal - akses via admin panel khusus
```

**2. Organization Owner:**
```python
# Owner punya full access ke semua fitur yang di-subscribe org-nya
if user_org.is_owner:
    return True  # Bypass permission check
```

**3. User dengan Multiple Roles:**
```python
# User bisa punya multiple roles
# Permission = gabungan semua role
user_roles = await get_user_roles(user_id)
for role in user_roles:
    if await role_has_permission(role.id, permission):
        return True
return False
```

---

### 3.6 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **App permissions** | Defined by developer, stored in Platform DB |
| **Org roles** | Created by org admin, stored in Org DB |
| **Permission format** | `{app}:{module}:{action}` |
| **Owner** | Full access ke semua fitur yang di-subscribe |
| **Role** | Custom per org, assign permissions sesuai kebutuhan |
| **Override** | User bisa dapat/dicabut permission individual |
| **Check location** | Route level (via Dependency) |

---

## 4. Audit Log ✅

### 4.0 Konsep Audit Log per App

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUDIT LOG STRUCTURE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PLATFORM DB                                                            │
│  └── auth_logs          → Login, logout, failed attempts                │
│                                                                          │
│  ORGANIZATION DB                                                        │
│  ├── pms.audit_logs     → Log khusus app PMS                           │
│  ├── accounting.audit_logs → Log khusus app Accounting                  │
│  ├── hrm.audit_logs     → Log khusus app HRM                           │
│  └── ... (per app)                                                      │
│                                                                          │
│  KEUNTUNGAN:                                                            │
│  ├── Backup per app = termasuk audit log-nya                           │
│  ├── Unsubscribe = archive log ikut                                    │
│  └── Query log per app lebih cepat                                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 4.1 Audit Log Types

| Type | Deskripsi | Contoh |
|------|-----------|--------|
| `AUTH` | Login, logout, password | User login success/failed |
| `CREATE` | Data baru dibuat | New reservation created |
| `UPDATE` | Data diubah | Reservation dates changed |
| `DELETE` | Data dihapus (soft) | Invoice deleted |
| `RESTORE` | Data di-restore | Invoice restored |
| `ACTION` | Business action | Reservation cancelled, Journal approved |
| `ACCESS` | View sensitive data | Viewed payroll report |
| `EXPORT` | Data di-export | Exported guest list |
| `DENIED` | Permission denied | Tried to approve without permission |

---

### 4.2 Database Structure

#### Platform DB (auth logs only)

```sql
CREATE TABLE auth_logs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Who
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),             -- copy untuk historical
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- What
    action VARCHAR(50) NOT NULL,         -- 'login', 'logout', 'failed_login'
    status VARCHAR(20) NOT NULL,         -- 'success', 'failed'
    failure_reason VARCHAR(200),

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_auth_logs_user ON auth_logs(user_id, created_at DESC);
CREATE INDEX idx_auth_logs_time ON auth_logs(created_at DESC);
```

#### Organization DB - Per App Schema

```sql
-- Setiap app punya audit_logs sendiri dalam schema-nya
-- Contoh: pms.audit_logs, accounting.audit_logs, hrm.audit_logs

CREATE TABLE {app_schema}.audit_logs (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Who
    user_id INTEGER NOT NULL,            -- dari platform.users
    user_name VARCHAR(200),              -- copy untuk historical

    -- What
    action VARCHAR(50) NOT NULL,         -- 'CREATE', 'UPDATE', 'DELETE', etc
    entity_type VARCHAR(100) NOT NULL,   -- 'reservation', 'journal'
    entity_id INTEGER,
    entity_uuid UUID,

    -- Details
    description TEXT,
    old_values JSONB,                    -- previous values
    new_values JSONB,                    -- new values
    changes JSONB,                       -- diff only
    metadata JSONB,

    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_id UUID,

    -- When
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX idx_{app}_audit_entity ON {app_schema}.audit_logs(entity_type, entity_id);
CREATE INDEX idx_{app}_audit_user ON {app_schema}.audit_logs(user_id, created_at DESC);
CREATE INDEX idx_{app}_audit_time ON {app_schema}.audit_logs(created_at DESC);
```

---

### 4.3 Log Format Example

```python
{
    "id": 12345,
    "user_id": 10,
    "user_name": "Andi Pratama",

    "action": "UPDATE",
    "entity_type": "reservation",
    "entity_id": 500,
    "entity_uuid": "550e8400-e29b-41d4-a716-446655440000",

    "description": "Changed reservation dates",

    "old_values": {
        "arrival_date": "2025-01-15",
        "departure_date": "2025-01-17"
    },

    "new_values": {
        "arrival_date": "2025-01-20",
        "departure_date": "2025-01-23"
    },

    "changes": {
        "arrival_date": {"from": "2025-01-15", "to": "2025-01-20"},
        "departure_date": {"from": "2025-01-17", "to": "2025-01-23"}
    },

    "metadata": {
        "reason": "Guest request"
    },

    "ip_address": "192.168.1.100",
    "request_id": "req-abc-123",
    "created_at": "2025-01-10T14:30:00+07:00"
}
```

---

### 4.4 Implementation Pattern

```python
class AuditService:
    def __init__(self, db, app_schema: str, current_user, request):
        self.db = db
        self.app_schema = app_schema  # 'pms', 'accounting', etc
        self.user_id = current_user.id
        self.user_name = current_user.name
        self.ip_address = request.client.host
        self.request_id = request.state.request_id

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: int = None,
        description: str = None,
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None
    ):
        changes = self._calculate_changes(old_values, new_values)

        # Insert ke schema yang sesuai
        await self.db.execute(f"""
            INSERT INTO {self.app_schema}.audit_logs
            (user_id, user_name, action, entity_type, entity_id,
             description, old_values, new_values, changes, metadata,
             ip_address, request_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """, self.user_id, self.user_name, action, entity_type, entity_id,
             description, old_values, new_values, changes, metadata,
             self.ip_address, self.request_id)
```

---

### 4.5 Sensitive Data Handling

```python
SENSITIVE_FIELDS = [
    'password', 'password_hash', 'token', 'secret',
    'credit_card', 'card_number', 'cvv', 'pin'
]

def sanitize_for_log(data: dict) -> dict:
    """Mask sensitive fields before logging."""
    sanitized = {}
    for key, value in data.items():
        if any(s in key.lower() for s in SENSITIVE_FIELDS):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    return sanitized
```

---

### 4.6 Retention Policy

```sql
-- Hapus log lama (scheduled job)

-- Auth logs: 1 tahun
DELETE FROM auth_logs WHERE created_at < NOW() - INTERVAL '1 year';

-- App logs: sesuai compliance
-- Financial (accounting): 7 tahun
DELETE FROM accounting.audit_logs WHERE created_at < NOW() - INTERVAL '7 years';

-- Operational (pms, hrm): 3 tahun
DELETE FROM pms.audit_logs WHERE created_at < NOW() - INTERVAL '3 years';
DELETE FROM hrm.audit_logs WHERE created_at < NOW() - INTERVAL '3 years';
```

---

### 4.7 Backup Audit Log per App

```bash
# Backup audit log ikut saat backup schema
pg_dump -n pms db_hotel_a > hotel_a_pms_backup.sql
# Includes: pms.reservations, pms.rooms, pms.audit_logs

# Backup audit log saja (kalau perlu)
pg_dump -n pms -t pms.audit_logs db_hotel_a > hotel_a_pms_auditlogs.sql
```

---

### 4.8 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Platform DB** | auth_logs (login/logout only) |
| **Org DB** | {app}.audit_logs per schema |
| **What to log** | All CRUD, business actions, sensitive access |
| **Format** | JSON with old/new values and diff |
| **Sensitive data** | Mask/redact before logging |
| **Retention** | Auth: 1yr, General: 3yr, Financial: 7yr |
| **Backup** | Ikut saat backup schema app |

---

## 5. Caching ✅

### 5.0 CHECKLIST WAJIB (Jangan Sampai Terlewat!)

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ⚠️  SETIAP BUAT/UPDATE FITUR CRUD, WAJIB CEK INI:                   ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  □ CREATE → Invalidate LIST cache                                     ║
║  □ UPDATE → Invalidate ENTITY + LIST cache                            ║
║  □ DELETE → Invalidate ENTITY + LIST cache                            ║
║  □ RESTORE → Invalidate ENTITY + LIST cache                           ║
║                                                                        ║
║  □ Role berubah → Invalidate PERMISSION cache semua user role tsb     ║
║  □ User role berubah → Invalidate PERMISSION cache user tsb           ║
║  □ Settings berubah → Invalidate SETTINGS cache                       ║
║                                                                        ║
║  □ Entity punya RELASI? → Invalidate cache entity terkait juga!       ║
║     Contoh: Room type dihapus → Invalidate rooms yang pakai type itu  ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 5.1 Invalidation Matrix (HARUS DIIKUTI)

| Action | Entity Cache | List Cache | Related Cache |
|--------|--------------|------------|---------------|
| **CREATE** | - | ✅ Invalidate | ✅ Jika ada relasi |
| **UPDATE** | ✅ Invalidate | ✅ Invalidate | ✅ Jika field relasi berubah |
| **DELETE** | ✅ Invalidate | ✅ Invalidate | ✅ Jika ada dependent |
| **RESTORE** | ✅ Invalidate | ✅ Invalidate | ✅ Jika ada relasi |

**Contoh Relasi yang Sering Terlewat:**

```python
# ❌ SALAH - Lupa invalidate relasi
async def update_room_type(self, id: int, dto):
    await self.repo.update(id, dto)
    await self.cache.delete(f"org:{org_id}:pms:room_type:{id}")  # ✅
    await self.cache.delete(f"org:{org_id}:pms:room_types:list") # ✅
    # TERLEWAT! Rooms yang pakai room_type ini juga perlu di-invalidate!

# ✅ BENAR - Invalidate entity + list + relasi
async def update_room_type(self, id: int, dto):
    await self.repo.update(id, dto)
    await self.cache.delete(f"org:{org_id}:pms:room_type:{id}")
    await self.cache.delete(f"org:{org_id}:pms:room_types:list")
    await self.cache.delete_pattern(f"org:{org_id}:pms:room:*")   # ✅ Rooms juga!
    await self.cache.delete(f"org:{org_id}:pms:rooms:list")       # ✅
```

---

### 5.2 Cache Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CACHING ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  CACHE STORAGE: Redis                                                   │
│                                                                          │
│  CACHE LEVELS:                                                          │
│  ├── Platform Cache    → Sessions, user info, app catalog              │
│  ├── Organization Cache → Settings, roles, permissions                  │
│  └── App Cache         → Business data per app                          │
│                                                                          │
│  KEY ISOLATION:                                                         │
│  ├── Platform  : platform:{type}:{id}                                  │
│  ├── Org       : org:{org_id}:{type}:{id}                              │
│  └── App       : org:{org_id}:{app}:{type}:{id}                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 5.3 Cache Key Naming Convention

**Format:** `{scope}:{org_id}:{app}:{type}:{id}`

```python
# Platform level (shared)
"platform:user:123"                      # User data
"platform:apps:list"                     # App catalog
"platform:session:abc123"                # Session token

# Organization level
"org:5:settings"                         # Org settings
"org:5:roles:list"                       # Roles list
"org:5:permissions:user:10"              # User permissions di org

# App level
"org:5:pms:room:101"                     # Room data
"org:5:pms:rooms:list"                   # Rooms list
"org:5:pms:room_type:5"                  # Room type
"org:5:pms:room_types:list"              # Room types list
"org:5:accounting:accounts:list"         # Chart of accounts
```

---

### 5.4 What to Cache

| Level | Data | TTL | Invalidation |
|-------|------|-----|--------------|
| **Platform** | User profile | 15 min | On update |
| **Platform** | Session | 24 hr | On logout |
| **Platform** | App catalog | 1 hr | On deploy |
| **Org** | Org settings | 30 min | On update |
| **Org** | Roles & permissions | 15 min | On role change |
| **App** | Lookup data (room types) | 30 min | On update |
| **App** | List queries | 5 min | On CRUD |
| **App** | Single entity | 15 min | On update/delete |

**JANGAN Cache:**
- Realtime data (availability, occupancy)
- Data sensitif (password, tokens)
- Data transaction (journals, folios aktif)

---

### 5.5 Implementation Pattern

```python
# cache_service.py

class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client

    # Key builders
    def _app_key(self, org_id: int, app: str, type: str, id: Any = None) -> str:
        if id:
            return f"org:{org_id}:{app}:{type}:{id}"
        return f"org:{org_id}:{app}:{type}"

    # Basic operations
    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl: timedelta):
        await self.redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern - untuk invalidate relasi."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

---

### 5.6 CRUD dengan Invalidation yang BENAR

```python
class RoomUseCase:
    """Contoh CRUD dengan invalidation yang lengkap."""

    async def create(self, org_id: int, dto: CreateRoomDTO):
        room = await self.repo.create(dto)

        # ✅ Invalidate list
        await self.cache.delete(f"org:{org_id}:pms:rooms:list")

        # ✅ Invalidate related (room type count mungkin berubah)
        await self.cache.delete(f"org:{org_id}:pms:room_type:{dto.room_type_id}")

        return room

    async def update(self, org_id: int, id: int, dto: UpdateRoomDTO):
        old_room = await self.repo.get_by_id(id)  # Get old data dulu
        room = await self.repo.update(id, dto)

        # ✅ Invalidate entity
        await self.cache.delete(f"org:{org_id}:pms:room:{id}")

        # ✅ Invalidate list
        await self.cache.delete(f"org:{org_id}:pms:rooms:list")

        # ✅ Invalidate related jika room_type berubah
        if old_room.room_type_id != dto.room_type_id:
            await self.cache.delete(f"org:{org_id}:pms:room_type:{old_room.room_type_id}")
            await self.cache.delete(f"org:{org_id}:pms:room_type:{dto.room_type_id}")

        return room

    async def delete(self, org_id: int, id: int):
        room = await self.repo.get_by_id(id)  # Get dulu sebelum delete
        await self.repo.soft_delete(id)

        # ✅ Invalidate entity
        await self.cache.delete(f"org:{org_id}:pms:room:{id}")

        # ✅ Invalidate list
        await self.cache.delete(f"org:{org_id}:pms:rooms:list")

        # ✅ Invalidate related
        await self.cache.delete(f"org:{org_id}:pms:room_type:{room.room_type_id}")

        return room
```

---

### 5.7 Permission Cache Invalidation

```python
class RoleUseCase:
    """Role berubah = invalidate semua user yang punya role ini."""

    async def update_role_permissions(self, org_id: int, role_id: int, permissions: list):
        await self.repo.update_permissions(role_id, permissions)

        # ✅ Invalidate role
        await self.cache.delete(f"org:{org_id}:role:{role_id}")
        await self.cache.delete(f"org:{org_id}:roles:list")

        # ✅ Invalidate SEMUA user yang punya role ini
        users = await self.repo.get_users_by_role(role_id)
        for user in users:
            await self.cache.delete(f"org:{org_id}:permissions:user:{user.id}")


class UserRoleUseCase:
    """User role berubah = invalidate permission user tsb."""

    async def assign_role(self, org_id: int, user_id: int, role_id: int):
        await self.repo.assign(user_id, role_id)

        # ✅ Invalidate user permission cache
        await self.cache.delete(f"org:{org_id}:permissions:user:{user_id}")

    async def remove_role(self, org_id: int, user_id: int, role_id: int):
        await self.repo.remove(user_id, role_id)

        # ✅ Invalidate user permission cache
        await self.cache.delete(f"org:{org_id}:permissions:user:{user_id}")
```

---

### 5.8 Invalidation Helper (Anti-Lupa)

```python
class CacheInvalidator:
    """Helper class untuk memastikan tidak ada yang terlewat."""

    def __init__(self, cache: CacheService, org_id: int, app: str):
        self.cache = cache
        self.org_id = org_id
        self.app = app

    async def on_create(self, entity_type: str, related_types: list[str] = None):
        """Call after CREATE."""
        # Invalidate list
        await self.cache.delete(f"org:{self.org_id}:{self.app}:{entity_type}s:list")

        # Invalidate related
        if related_types:
            for rel_type in related_types:
                await self.cache.delete_pattern(
                    f"org:{self.org_id}:{self.app}:{rel_type}:*"
                )

    async def on_update(self, entity_type: str, entity_id: int, related_types: list[str] = None):
        """Call after UPDATE."""
        # Invalidate entity
        await self.cache.delete(f"org:{self.org_id}:{self.app}:{entity_type}:{entity_id}")

        # Invalidate list
        await self.cache.delete(f"org:{self.org_id}:{self.app}:{entity_type}s:list")

        # Invalidate related
        if related_types:
            for rel_type in related_types:
                await self.cache.delete_pattern(
                    f"org:{self.org_id}:{self.app}:{rel_type}:*"
                )

    async def on_delete(self, entity_type: str, entity_id: int, related_types: list[str] = None):
        """Call after DELETE."""
        await self.on_update(entity_type, entity_id, related_types)


# Penggunaan
class RoomTypeUseCase:
    async def delete(self, org_id: int, id: int):
        await self.repo.soft_delete(id)

        # Pakai helper - tidak akan lupa!
        invalidator = CacheInvalidator(self.cache, org_id, "pms")
        await invalidator.on_delete(
            entity_type="room_type",
            entity_id=id,
            related_types=["room", "rate"]  # ✅ Otomatis invalidate rooms & rates
        )
```

---

### 5.9 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Storage** | Redis |
| **Key format** | `org:{org_id}:{app}:{type}:{id}` |
| **CREATE** | Invalidate LIST + RELATED |
| **UPDATE** | Invalidate ENTITY + LIST + RELATED |
| **DELETE** | Invalidate ENTITY + LIST + RELATED |
| **Role change** | Invalidate permission semua user role |
| **User role change** | Invalidate permission user |
| **Helper** | Gunakan `CacheInvalidator` agar tidak lupa |

---

## 6. API Patterns ✅

### 6.1 URL Structure

**Format:** `/api/v{version}/{app}/{resource}`

```python
# Platform endpoints (tanpa org context)
GET    /api/v1/platform/users/me              # Current user
GET    /api/v1/platform/organizations         # My organizations
POST   /api/v1/platform/auth/login            # Login
POST   /api/v1/platform/auth/logout           # Logout

# App endpoints (dengan org context via header)
GET    /api/v1/pms/reservations               # List
POST   /api/v1/pms/reservations               # Create
GET    /api/v1/pms/reservations/{id}          # Get
PATCH  /api/v1/pms/reservations/{id}          # Update
DELETE /api/v1/pms/reservations/{id}          # Delete
POST   /api/v1/pms/reservations/{id}/cancel   # Action
```

---

### 6.2 Request Headers

```python
# WAJIB untuk authenticated requests
Authorization: Bearer {token}

# WAJIB untuk app-level endpoints
X-Organization-ID: 5

# OPTIONAL
Content-Type: application/json
Accept-Language: id
X-Request-ID: uuid
```

---

### 6.3 Response Format

```python
# Success - Single entity
{
    "success": true,
    "data": { ... },
    "message": "Optional success message"
}

# Success - List with pagination
{
    "success": true,
    "data": [ ... ],
    "meta": {
        "page": 1,
        "page_size": 20,
        "total_items": 150,
        "total_pages": 8,
        "has_next": true,
        "has_prev": false
    }
}

# Error
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": [ ... ],
        "request_id": "req-abc-123"
    }
}
```

---

### 6.4 Pagination, Filtering, Sorting

```python
# Pagination
GET /api/v1/pms/reservations?page=1&page_size=20

# Filtering
GET /api/v1/pms/reservations?status=confirmed&arrival_date_gte=2025-01-01

# Filter suffixes: _gte, _lte, _gt, _lt, _like, _in, _is_null

# Sorting
GET /api/v1/pms/reservations?sort_by=arrival_date&sort_order=desc

# Search
GET /api/v1/pms/guests?search=john
```

---

### 6.5 Error Codes - Complete Reference

#### Authentication Errors (401)

| Code | Message |
|------|---------|
| `AUTH_TOKEN_MISSING` | Authentication token is required |
| `AUTH_TOKEN_INVALID` | Invalid authentication token |
| `AUTH_TOKEN_EXPIRED` | Authentication token has expired |
| `AUTH_TOKEN_REVOKED` | Authentication token has been revoked |
| `AUTH_SESSION_EXPIRED` | Session has expired, please login again |
| `AUTH_INVALID_CREDENTIALS` | Invalid email or password |
| `AUTH_ACCOUNT_LOCKED` | Account is locked due to too many failed attempts |
| `AUTH_ACCOUNT_DISABLED` | Account has been disabled |
| `AUTH_EMAIL_NOT_VERIFIED` | Please verify your email first |

#### Authorization Errors (403)

| Code | Message |
|------|---------|
| `AUTHZ_PERMISSION_DENIED` | You don't have permission to perform this action |
| `AUTHZ_ORG_ACCESS_DENIED` | You don't have access to this organization |
| `AUTHZ_APP_NOT_SUBSCRIBED` | Organization has not subscribed to this app |
| `AUTHZ_ROLE_INSUFFICIENT` | Your role is not sufficient for this action |
| `AUTHZ_OWNER_ONLY` | Only organization owner can perform this action |
| `AUTHZ_RESOURCE_FORBIDDEN` | You don't have access to this resource |

#### Validation Errors (400)

| Code | Message |
|------|---------|
| `VALIDATION_REQUIRED_FIELD` | {field} is required |
| `VALIDATION_INVALID_FORMAT` | {field} has invalid format |
| `VALIDATION_INVALID_TYPE` | {field} must be {type} |
| `VALIDATION_MIN_LENGTH` | {field} must be at least {min} characters |
| `VALIDATION_MAX_LENGTH` | {field} must be at most {max} characters |
| `VALIDATION_MIN_VALUE` | {field} must be at least {min} |
| `VALIDATION_MAX_VALUE` | {field} must be at most {max} |
| `VALIDATION_INVALID_EMAIL` | Invalid email address |
| `VALIDATION_INVALID_PHONE` | Invalid phone number |
| `VALIDATION_INVALID_DATE` | Invalid date format, use YYYY-MM-DD |
| `VALIDATION_DATE_PAST` | {field} cannot be in the past |
| `VALIDATION_DATE_FUTURE` | {field} cannot be in the future |
| `VALIDATION_DATE_RANGE` | {end_field} must be after {start_field} |
| `VALIDATION_INVALID_ENUM` | {field} must be one of: {values} |
| `VALIDATION_UNIQUE_VIOLATION` | {field} already exists |
| `VALIDATION_FOREIGN_KEY` | Referenced {entity} not found |

#### Resource Errors (404, 409, 410)

| Code | HTTP | Message |
|------|------|---------|
| `RESOURCE_NOT_FOUND` | 404 | {entity} not found |
| `RESOURCE_DELETED` | 410 | {entity} has been deleted |
| `RESOURCE_ALREADY_EXISTS` | 409 | {entity} already exists |
| `RESOURCE_CONFLICT` | 409 | Resource conflict: {reason} |
| `RESOURCE_LOCKED` | 423 | {entity} is locked for editing |
| `RESOURCE_ARCHIVED` | 410 | {entity} has been archived |

#### Business Logic Errors (422)

| Code | Message |
|------|---------|
| `BUSINESS_RULE_VIOLATION` | {rule description} |
| `BUSINESS_INSUFFICIENT_BALANCE` | Insufficient balance |
| `BUSINESS_LIMIT_EXCEEDED` | {limit_type} limit exceeded |
| `BUSINESS_INVALID_STATE` | Cannot {action} when status is {status} |
| `BUSINESS_DEPENDENCY_EXISTS` | Cannot delete: {entity} has dependent records |
| `BUSINESS_PERIOD_CLOSED` | Period {period} is closed |
| `BUSINESS_ALREADY_PROCESSED` | {entity} has already been processed |
| `BUSINESS_APPROVAL_REQUIRED` | Approval is required for this action |

#### App-Specific: PMS (422)

| Code | Message |
|------|---------|
| `PMS_ROOM_NOT_AVAILABLE` | Room is not available for selected dates |
| `PMS_RESERVATION_ALREADY_CANCELLED` | Reservation is already cancelled |
| `PMS_RESERVATION_ALREADY_CHECKED_IN` | Guest has already checked in |
| `PMS_RESERVATION_ALREADY_CHECKED_OUT` | Guest has already checked out |
| `PMS_CANNOT_CANCEL_CHECKED_IN` | Cannot cancel a checked-in reservation |
| `PMS_ROOM_OCCUPIED` | Room is currently occupied |
| `PMS_ROOM_NOT_CLEAN` | Room is not ready (not clean) |
| `PMS_FOLIO_HAS_BALANCE` | Folio has outstanding balance |
| `PMS_RATE_NOT_FOUND` | No rate available for selected dates |

#### App-Specific: Accounting (422)

| Code | Message |
|------|---------|
| `ACC_JOURNAL_UNBALANCED` | Journal entries are not balanced |
| `ACC_JOURNAL_ALREADY_POSTED` | Journal is already posted |
| `ACC_JOURNAL_ALREADY_VOIDED` | Journal is already voided |
| `ACC_PERIOD_CLOSED` | Accounting period is closed |
| `ACC_ACCOUNT_INACTIVE` | Account is inactive |
| `ACC_CANNOT_DELETE_POSTED` | Cannot delete posted journal |
| `ACC_INSUFFICIENT_BUDGET` | Insufficient budget |

#### App-Specific: HRM (422)

| Code | Message |
|------|---------|
| `HRM_EMPLOYEE_TERMINATED` | Employee has been terminated |
| `HRM_LEAVE_INSUFFICIENT` | Insufficient leave balance |
| `HRM_LEAVE_OVERLAP` | Leave request overlaps with existing leave |
| `HRM_ATTENDANCE_DUPLICATE` | Attendance already recorded for this date |
| `HRM_PAYROLL_ALREADY_PROCESSED` | Payroll already processed for this period |

#### App-Specific: Inventory (422)

| Code | Message |
|------|---------|
| `INV_INSUFFICIENT_STOCK` | Insufficient stock for {item} |
| `INV_ITEM_INACTIVE` | Item is inactive |
| `INV_NEGATIVE_STOCK` | Stock cannot be negative |
| `INV_BATCH_EXPIRED` | Batch has expired |

#### Rate Limiting Errors (429)

| Code | Message |
|------|---------|
| `RATE_LIMIT_EXCEEDED` | Too many requests, please try again later |
| `RATE_LIMIT_LOGIN` | Too many login attempts, try again in {minutes} minutes |
| `RATE_LIMIT_API` | API rate limit exceeded |

#### Server Errors (500, 502, 503)

| Code | HTTP | Message |
|------|------|---------|
| `SERVER_INTERNAL_ERROR` | 500 | An unexpected error occurred |
| `SERVER_DATABASE_ERROR` | 500 | Database error occurred |
| `SERVER_EXTERNAL_SERVICE` | 502 | External service is unavailable |
| `SERVER_MAINTENANCE` | 503 | System is under maintenance |
| `SERVER_OVERLOADED` | 503 | Server is overloaded, please try again |
| `SERVER_TIMEOUT` | 504 | Request timed out |

---

### 6.6 Error Response Examples

```python
# Validation Error (400)
{
    "success": false,
    "error": {
        "code": "VALIDATION_REQUIRED_FIELD",
        "message": "Invalid request data",
        "details": [
            {"field": "arrival_date", "code": "VALIDATION_REQUIRED_FIELD", "message": "arrival_date is required"},
            {"field": "guest_id", "code": "VALIDATION_FOREIGN_KEY", "message": "Referenced guest not found"}
        ]
    }
}

# Business Error (422)
{
    "success": false,
    "error": {
        "code": "PMS_ROOM_NOT_AVAILABLE",
        "message": "Room is not available for selected dates",
        "details": [
            {"field": "room_id", "message": "Room 101 is booked from 2025-01-15 to 2025-01-18"}
        ]
    }
}

# Permission Error (403)
{
    "success": false,
    "error": {
        "code": "AUTHZ_PERMISSION_DENIED",
        "message": "You don't have permission to perform this action",
        "details": [
            {"required_permission": "pms:reservation:cancel"}
        ]
    }
}
```

---

### 6.7 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Base URL** | `/api/v1/{app}/{resource}` |
| **Org context** | Header `X-Organization-ID` |
| **Auth** | Header `Authorization: Bearer {token}` |
| **Response** | `{success, data, error, meta}` |
| **Pagination** | `?page=1&page_size=20` |
| **Filtering** | `?field=value`, `?field_gte=value` |
| **Sorting** | `?sort_by=field&sort_order=asc` |
| **Error format** | `{code, message, details}` |
| **Error code format** | `{CATEGORY}_{SPECIFIC}` |

---

## 7. Error Handling ✅

### 7.0 Prinsip Error Handling

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ERROR HANDLING PRINCIPLES                                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  1. FAIL FAST       → Validasi di awal, jangan tunggu sampai dalam   ║
║  2. SPECIFIC ERRORS → Jangan generic Exception, pakai specific class  ║
║  3. CONTEXT RICH    → Sertakan context yang cukup untuk debugging    ║
║  4. USER FRIENDLY   → Message untuk user, detail untuk developer     ║
║  5. LOG EVERYTHING  → Semua error harus ter-log dengan context       ║
║  6. DON'T SWALLOW   → Jangan catch error tanpa handling/logging      ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 7.1 Exception Hierarchy (Backend)

```python
# shared/exceptions.py

class AppException(Exception):
    """Base exception untuk semua custom exceptions."""

    def __init__(
        self,
        code: str,
        message: str,
        details: list = None,
        http_status: int = 400
    ):
        self.code = code
        self.message = message
        self.details = details or []
        self.http_status = http_status
        super().__init__(message)


# === AUTHENTICATION ERRORS (401) ===

class AuthenticationError(AppException):
    """Base class untuk authentication errors."""
    def __init__(self, code: str, message: str, details: list = None):
        super().__init__(code, message, details, http_status=401)


class TokenMissingError(AuthenticationError):
    def __init__(self):
        super().__init__("AUTH_TOKEN_MISSING", "Authentication token is required")


class TokenInvalidError(AuthenticationError):
    def __init__(self):
        super().__init__("AUTH_TOKEN_INVALID", "Invalid authentication token")


class TokenExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__("AUTH_TOKEN_EXPIRED", "Authentication token has expired")


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("AUTH_INVALID_CREDENTIALS", "Invalid email or password")


# === AUTHORIZATION ERRORS (403) ===

class AuthorizationError(AppException):
    """Base class untuk authorization errors."""
    def __init__(self, code: str, message: str, details: list = None):
        super().__init__(code, message, details, http_status=403)


class PermissionDeniedError(AuthorizationError):
    def __init__(self, permission: str = None):
        details = [{"required_permission": permission}] if permission else []
        super().__init__(
            "AUTHZ_PERMISSION_DENIED",
            "You don't have permission to perform this action",
            details
        )


class OrgAccessDeniedError(AuthorizationError):
    def __init__(self, org_id: int = None):
        details = [{"organization_id": org_id}] if org_id else []
        super().__init__(
            "AUTHZ_ORG_ACCESS_DENIED",
            "You don't have access to this organization",
            details
        )


class AppNotSubscribedError(AuthorizationError):
    def __init__(self, app: str):
        super().__init__(
            "AUTHZ_APP_NOT_SUBSCRIBED",
            f"Organization has not subscribed to {app}",
            [{"app": app}]
        )


# === VALIDATION ERRORS (400) ===

class ValidationError(AppException):
    """Base class untuk validation errors."""
    def __init__(self, code: str, message: str, details: list = None):
        super().__init__(code, message, details, http_status=400)


class RequiredFieldError(ValidationError):
    def __init__(self, field: str):
        super().__init__(
            "VALIDATION_REQUIRED_FIELD",
            f"{field} is required",
            [{"field": field}]
        )


class InvalidFormatError(ValidationError):
    def __init__(self, field: str, expected_format: str):
        super().__init__(
            "VALIDATION_INVALID_FORMAT",
            f"{field} has invalid format",
            [{"field": field, "expected_format": expected_format}]
        )


class UniqueViolationError(ValidationError):
    def __init__(self, field: str, value: str = None):
        super().__init__(
            "VALIDATION_UNIQUE_VIOLATION",
            f"{field} already exists",
            [{"field": field, "value": value}]
        )


# === RESOURCE ERRORS (404, 409, 410) ===

class NotFoundError(AppException):
    def __init__(self, entity: str, id: any = None):
        details = [{"entity": entity, "id": id}] if id else [{"entity": entity}]
        super().__init__(
            "RESOURCE_NOT_FOUND",
            f"{entity} not found",
            details,
            http_status=404
        )


class AlreadyExistsError(AppException):
    def __init__(self, entity: str, identifier: str = None):
        details = [{"entity": entity, "identifier": identifier}] if identifier else []
        super().__init__(
            "RESOURCE_ALREADY_EXISTS",
            f"{entity} already exists",
            details,
            http_status=409
        )


class DeletedError(AppException):
    def __init__(self, entity: str, id: any = None):
        super().__init__(
            "RESOURCE_DELETED",
            f"{entity} has been deleted",
            [{"entity": entity, "id": id}],
            http_status=410
        )


class ConflictError(AppException):
    def __init__(self, reason: str, details: list = None):
        super().__init__(
            "RESOURCE_CONFLICT",
            f"Resource conflict: {reason}",
            details,
            http_status=409
        )


# === BUSINESS LOGIC ERRORS (422) ===

class BusinessError(AppException):
    """Base class untuk business logic errors."""
    def __init__(self, code: str, message: str, details: list = None):
        super().__init__(code, message, details, http_status=422)


class InvalidStateError(BusinessError):
    def __init__(self, action: str, current_status: str):
        super().__init__(
            "BUSINESS_INVALID_STATE",
            f"Cannot {action} when status is {current_status}",
            [{"action": action, "current_status": current_status}]
        )


class DependencyExistsError(BusinessError):
    def __init__(self, entity: str, dependent_entity: str, count: int = None):
        details = [{"entity": entity, "dependent": dependent_entity}]
        if count:
            details[0]["count"] = count
        super().__init__(
            "BUSINESS_DEPENDENCY_EXISTS",
            f"Cannot delete: {entity} has dependent {dependent_entity}",
            details
        )


# === APP-SPECIFIC ERRORS ===

# PMS Errors
class RoomNotAvailableError(BusinessError):
    def __init__(self, room_id: int, date_from: str, date_to: str):
        super().__init__(
            "PMS_ROOM_NOT_AVAILABLE",
            "Room is not available for selected dates",
            [{"room_id": room_id, "from": date_from, "to": date_to}]
        )


class ReservationAlreadyCancelledError(BusinessError):
    def __init__(self, reservation_id: int):
        super().__init__(
            "PMS_RESERVATION_ALREADY_CANCELLED",
            "Reservation is already cancelled",
            [{"reservation_id": reservation_id}]
        )


# Accounting Errors
class JournalUnbalancedError(BusinessError):
    def __init__(self, debit_total: float, credit_total: float):
        super().__init__(
            "ACC_JOURNAL_UNBALANCED",
            "Journal entries are not balanced",
            [{"debit": debit_total, "credit": credit_total}]
        )


class PeriodClosedError(BusinessError):
    def __init__(self, period: str):
        super().__init__(
            "ACC_PERIOD_CLOSED",
            f"Accounting period {period} is closed",
            [{"period": period}]
        )


# HRM Errors
class InsufficientLeaveBalanceError(BusinessError):
    def __init__(self, leave_type: str, requested: int, available: int):
        super().__init__(
            "HRM_LEAVE_INSUFFICIENT",
            "Insufficient leave balance",
            [{"leave_type": leave_type, "requested": requested, "available": available}]
        )


# Inventory Errors
class InsufficientStockError(BusinessError):
    def __init__(self, item_id: int, item_name: str, requested: float, available: float):
        super().__init__(
            "INV_INSUFFICIENT_STOCK",
            f"Insufficient stock for {item_name}",
            [{"item_id": item_id, "requested": requested, "available": available}]
        )
```

---

### 7.2 Throwing Errors (Use Cases)

```python
# PRINSIP: Throw early, be specific, provide context

class CreateReservationUseCase:
    async def execute(self, dto: CreateReservationDTO) -> Reservation:
        # 1. VALIDATE EARLY - jangan tunggu sampai save
        guest = await self.guest_repo.get_by_id(dto.guest_id)
        if not guest:
            raise NotFoundError("Guest", dto.guest_id)

        if guest.deleted_at:
            raise DeletedError("Guest", dto.guest_id)

        room = await self.room_repo.get_by_id(dto.room_id)
        if not room:
            raise NotFoundError("Room", dto.room_id)

        # 2. CHECK BUSINESS RULES
        if dto.departure_date <= dto.arrival_date:
            raise ValidationError(
                "VALIDATION_DATE_RANGE",
                "Departure date must be after arrival date",
                [{"field": "departure_date"}]
            )

        # 3. CHECK AVAILABILITY
        if not await self.availability_service.is_room_available(
            dto.room_id, dto.arrival_date, dto.departure_date
        ):
            raise RoomNotAvailableError(
                dto.room_id,
                dto.arrival_date.isoformat(),
                dto.departure_date.isoformat()
            )

        # 4. PROCEED WITH CREATION
        reservation = await self.repo.create(dto)
        return reservation


class CancelReservationUseCase:
    async def execute(self, reservation_id: int) -> Reservation:
        reservation = await self.repo.get_by_id(reservation_id)

        # Check exists
        if not reservation:
            raise NotFoundError("Reservation", reservation_id)

        # Check state
        if reservation.status == "cancelled":
            raise ReservationAlreadyCancelledError(reservation_id)

        if reservation.status == "checked_in":
            raise InvalidStateError("cancel", reservation.status)

        if reservation.status == "checked_out":
            raise InvalidStateError("cancel", reservation.status)

        # Proceed
        return await self.repo.update(reservation_id, {"status": "cancelled"})
```

---

### 7.3 Catching Errors (Routes/Controllers)

```python
# shared/exception_handler.py

from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException):
    """Handler untuk semua AppException."""

    # Log error dengan context
    logger.warning(
        f"AppException: {exc.code}",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
        }
    )

    return JSONResponse(
        status_code=exc.http_status,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler untuk Pydantic validation errors."""

    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field,
            "code": f"VALIDATION_{error['type'].upper()}",
            "message": error["msg"]
        })

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": details,
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Handler untuk unexpected errors - JANGAN expose detail ke user."""

    # Log full error dengan traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )

    # Response generic ke user
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "SERVER_INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None)
            }
        }
    )


# Register handlers di FastAPI app
def setup_exception_handlers(app):
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

---

### 7.4 Route Implementation

```python
# routes.py

@router.post("/reservations", response_model=ReservationResponse)
async def create_reservation(
    dto: CreateReservationDTO,
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org),
    _: bool = Depends(require_permission("pms:reservation:create")),
    use_case: CreateReservationUseCase = Depends()
):
    # ⚠️ JANGAN try-catch di route - biarkan exception handler yang handle
    # Use case sudah throw specific errors dengan context

    reservation = await use_case.execute(dto)
    return {
        "success": True,
        "data": reservation
    }


# ❌ SALAH - jangan swallow errors
@router.post("/reservations")
async def create_reservation_wrong(dto: CreateReservationDTO):
    try:
        reservation = await use_case.execute(dto)
        return {"success": True, "data": reservation}
    except Exception as e:
        # JANGAN begini! Error detail hilang, tidak ter-log dengan benar
        return {"success": False, "error": str(e)}


# ❌ SALAH - jangan catch terlalu luas
@router.post("/reservations")
async def create_reservation_wrong2(dto: CreateReservationDTO):
    try:
        reservation = await use_case.execute(dto)
        return {"success": True, "data": reservation}
    except NotFoundError:
        # OK
        raise
    except Exception:
        # JANGAN catch Exception tanpa re-raise atau specific handling
        raise HTTPException(500, "Something went wrong")
```

---

### 7.5 Error Logging

```python
# shared/logging_config.py

import logging
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """JSON format untuk structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "traceback"):
            log_data["traceback"] = record.traceback
        if hasattr(record, "details"):
            log_data["details"] = record.details

        return json.dumps(log_data)


# Logging levels by error type
LOGGING_LEVELS = {
    # Validation, business rule - expected errors
    "VALIDATION_*": logging.WARNING,
    "BUSINESS_*": logging.WARNING,
    "PMS_*": logging.WARNING,
    "ACC_*": logging.WARNING,
    "HRM_*": logging.WARNING,
    "INV_*": logging.WARNING,

    # Auth - could be attack attempts
    "AUTH_*": logging.WARNING,
    "AUTHZ_*": logging.WARNING,

    # Resource not found - usually normal
    "RESOURCE_NOT_FOUND": logging.INFO,

    # Server errors - critical
    "SERVER_*": logging.ERROR,
}
```

---

### 7.6 Error Recovery Patterns

```python
class ReservationService:
    """Contoh error recovery dan retry patterns."""

    async def sync_to_channel_manager(self, reservation_id: int):
        """Sync reservation ke external system dengan retry."""

        MAX_RETRIES = 3
        RETRY_DELAY = 1  # seconds

        for attempt in range(MAX_RETRIES):
            try:
                await self.channel_manager.push(reservation_id)
                return True

            except ExternalServiceError as e:
                logger.warning(
                    f"Channel manager sync failed (attempt {attempt + 1}/{MAX_RETRIES})",
                    extra={
                        "reservation_id": reservation_id,
                        "error": str(e)
                    }
                )

                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                else:
                    # Final attempt failed - queue for retry later
                    await self.queue_for_retry(reservation_id)
                    raise  # Re-raise untuk caller awareness


    async def create_with_fallback(self, dto: CreateReservationDTO):
        """Create dengan fallback kalau external service down."""

        reservation = await self.repo.create(dto)

        try:
            await self.sync_to_channel_manager(reservation.id)
        except ExternalServiceError:
            # Log but don't fail - akan di-sync nanti via background job
            reservation.sync_status = "pending"
            await self.repo.update(reservation.id, {"sync_status": "pending"})

            logger.warning(
                "Channel manager sync queued for later",
                extra={"reservation_id": reservation.id}
            )

        return reservation
```

---

### 7.7 Frontend Error Handling

```typescript
// shared/api/errorHandler.ts

interface ApiError {
  code: string;
  message: string;
  details?: Array<{
    field?: string;
    code?: string;
    message?: string;
  }>;
  request_id?: string;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
}


// Global error handler
export function handleApiError(error: ApiError): void {
  // 1. Categorize error
  const category = error.code.split('_')[0];

  switch (category) {
    case 'AUTH':
      handleAuthError(error);
      break;
    case 'AUTHZ':
      handleAuthorizationError(error);
      break;
    case 'VALIDATION':
      // Biasanya di-handle di form level, tidak perlu toast
      break;
    case 'RESOURCE':
      handleResourceError(error);
      break;
    case 'BUSINESS':
    case 'PMS':
    case 'ACC':
    case 'HRM':
    case 'INV':
      handleBusinessError(error);
      break;
    case 'SERVER':
      handleServerError(error);
      break;
    default:
      handleUnknownError(error);
  }
}


function handleAuthError(error: ApiError) {
  if (error.code === 'AUTH_TOKEN_EXPIRED' || error.code === 'AUTH_TOKEN_INVALID') {
    // Redirect to login
    authStore.logout();
    router.push('/login');
    toast.error('Session expired. Please login again.');
  } else {
    toast.error(error.message);
  }
}


function handleAuthorizationError(error: ApiError) {
  toast.error(error.message);
  // Optionally redirect to dashboard
  if (error.code === 'AUTHZ_ORG_ACCESS_DENIED') {
    router.push('/select-organization');
  }
}


function handleResourceError(error: ApiError) {
  if (error.code === 'RESOURCE_NOT_FOUND') {
    router.push('/404');
  } else {
    toast.error(error.message);
  }
}


function handleBusinessError(error: ApiError) {
  // Business errors biasanya perlu ditampilkan ke user
  toast.error(error.message);
}


function handleServerError(error: ApiError) {
  // Server error - generic message, log request_id
  toast.error('Something went wrong. Please try again later.');
  console.error('Server error:', error.request_id);
}


// Form validation error mapping
export function mapValidationErrors(
  details: ApiError['details']
): Record<string, string> {
  const errors: Record<string, string> = {};

  for (const detail of details || []) {
    if (detail.field) {
      errors[detail.field] = detail.message || 'Invalid value';
    }
  }

  return errors;
}


// Usage in React component
function ReservationForm() {
  const { mutate, error } = useCreateReservation();
  const form = useForm<CreateReservationDTO>();

  useEffect(() => {
    if (error?.code?.startsWith('VALIDATION_')) {
      // Map API errors to form fields
      const fieldErrors = mapValidationErrors(error.details);
      Object.entries(fieldErrors).forEach(([field, message]) => {
        form.setError(field, { message });
      });
    } else if (error) {
      handleApiError(error);
    }
  }, [error]);

  return <form>...</form>;
}
```

---

### 7.8 Error Audit Integration

```python
class AuditableUseCase:
    """Base class untuk use cases yang perlu audit error."""

    async def execute_with_audit(self, dto, current_user, org_id, app):
        try:
            result = await self.execute(dto)
            return result

        except AppException as e:
            # Log ke audit log untuk errors yang significant
            if self._should_audit_error(e):
                await self.audit_service.log(
                    action="DENIED",
                    entity_type=self.entity_type,
                    description=f"Action failed: {e.message}",
                    metadata={
                        "error_code": e.code,
                        "details": e.details,
                        "input": dto.dict() if hasattr(dto, 'dict') else str(dto)
                    }
                )
            raise

    def _should_audit_error(self, error: AppException) -> bool:
        """Tentukan error mana yang perlu di-audit."""
        audit_codes = [
            "AUTHZ_PERMISSION_DENIED",
            "AUTHZ_ORG_ACCESS_DENIED",
            "BUSINESS_LIMIT_EXCEEDED",
        ]
        return error.code in audit_codes
```

---

### 7.9 Error Handling Checklist

```
╔═══════════════════════════════════════════════════════════════════════╗
║  ⚠️  CHECKLIST SEBELUM DEPLOY FITUR BARU:                            ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  BACKEND:                                                              ║
║  □ Semua error pakai specific exception class                         ║
║  □ Error message user-friendly (bukan technical jargon)               ║
║  □ Sensitive data tidak masuk error message/details                   ║
║  □ All expected errors punya error code yang sesuai                   ║
║  □ Exception handlers sudah di-register                               ║
║  □ Logging setup dengan structured format                             ║
║                                                                        ║
║  FRONTEND:                                                             ║
║  □ API errors di-handle dengan benar (toast/redirect/form)            ║
║  □ Auth errors redirect ke login                                      ║
║  □ Validation errors ditampilkan di form field                        ║
║  □ Loading states saat waiting response                               ║
║  □ Error boundaries untuk unexpected React errors                     ║
║                                                                        ║
║  TESTING:                                                              ║
║  □ Test case untuk setiap error scenario                              ║
║  □ Test exception handler returns correct format                      ║
║  □ Test error logging captures correct data                           ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### 7.10 Ringkasan

| Aspek | Aturan |
|-------|--------|
| **Exception classes** | Hierarchy dengan specific classes per error type |
| **Throwing** | Di use case, early & specific, dengan context |
| **Catching** | Di global handler, jangan swallow di route |
| **Logging** | Structured JSON, include request_id & context |
| **User message** | Friendly, tidak expose technical details |
| **Dev details** | Di details array atau log, tidak di message |
| **Auth errors** | Redirect ke login jika session invalid |
| **Validation** | Map ke form fields di frontend |
| **Business** | Show toast dengan message |
| **Server** | Generic message, log request_id |

---

## 8. Validation ⏳

> Pending

---

## 9. Testing ⏳

> Pending

---

## 10. Code Structure ⏳

> Pending

---

## 11. Frontend Patterns ⏳

> Pending

---

## 12. Cleanup / Maintenance ⏳

> Pending

---

*Document ini akan di-update seiring pembahasan setiap section.*
