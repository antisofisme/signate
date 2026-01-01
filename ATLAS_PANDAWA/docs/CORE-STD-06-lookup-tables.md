# Development Standards V6

> Standards #27+ untuk ATLAS_PANDAWA - Enterprise Hospitality Platform

---

## Table of Contents

- [Standard #27: Lookup/Type Tables](#standard-27-lookuptype-tables)
  - [27.1 Konsep Dasar](#271-konsep-dasar)
  - [27.2 Klasifikasi Lookup Tables](#272-klasifikasi-lookup-tables)
  - [27.3 Standard Schema Pattern](#273-standard-schema-pattern)
  - [27.4 Multi-Level Lookup Strategy](#274-multi-level-lookup-strategy)
  - [27.5 Backend Implementation](#275-backend-implementation)
  - [27.6 API Pattern](#276-api-pattern)
  - [27.7 Frontend Implementation](#277-frontend-implementation)
  - [27.8 Caching Strategy](#278-caching-strategy)
  - [27.9 Performance Optimization](#279-performance-optimization)
  - [27.10 Performance SLA](#2710-performance-sla)
  - [27.11 Integration dengan Standards Lain](#2711-integration-dengan-standards-lain)
  - [27.12 Best Practices](#2712-best-practices)
  - [27.13 Anti-Patterns](#2713-anti-patterns)

---

## Standard #27: Lookup/Type Tables

### 27.1 Konsep Dasar

**Lookup Table** adalah tabel referensi yang menyimpan nilai-nilai yang digunakan sebagai Foreign Key di tabel lain. Contoh: `content_types`, `device_statuses`, `payment_methods`.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      LOOKUP TABLE CONCEPT                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐         ┌──────────────────────────────────┐     │
│  │  content_types   │         │          contents                 │     │
│  ├──────────────────┤         ├──────────────────────────────────┤     │
│  │ id: 1            │◄────────│ content_type_id: 1               │     │
│  │ code: "IMAGE"    │         │ name: "Banner Hotel"             │     │
│  │ name: "Image"    │         │ ...                              │     │
│  ├──────────────────┤         └──────────────────────────────────┘     │
│  │ id: 2            │                                                   │
│  │ code: "VIDEO"    │         ┌──────────────────────────────────┐     │
│  │ name: "Video"    │◄────────│          contents                 │     │
│  ├──────────────────┤         ├──────────────────────────────────┤     │
│  │ id: 3            │         │ content_type_id: 2               │     │
│  │ code: "WEBPAGE"  │         │ name: "Promo Video"              │     │
│  │ name: "Web Page" │         │ ...                              │     │
│  └──────────────────┘         └──────────────────────────────────┘     │
│                                                                          │
│  Benefit:                                                                │
│  ✅ Data integrity via FK constraint                                    │
│  ✅ Consistent values across system                                     │
│  ✅ Easy to add new types without code changes                          │
│  ✅ Human-readable names untuk UI                                       │
│  ✅ Audit trail siapa yang tambah/ubah                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Kapan Menggunakan Lookup Table vs Enum:**

| Kriteria | Lookup Table | Code Enum |
|----------|--------------|-----------|
| Values bisa bertambah? | ✅ Ya | ❌ Tidak |
| Perlu metadata (icon, color)? | ✅ Ya | ❌ Tidak |
| Per-tenant customization? | ✅ Ya | ❌ Tidak |
| Performance critical? | ⚠️ Perlu caching | ✅ Instant |
| Audit trail diperlukan? | ✅ Ya | ❌ Tidak |
| < 10 values & fixed? | ❌ Overkill | ✅ Cocok |

---

### 27.2 Klasifikasi Lookup Tables

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOOKUP TABLE CLASSIFICATION                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Level 1: SYSTEM TYPES (Static)                                         │
│  ────────────────────────────────                                        │
│  • organization_id = NULL (system-wide)                                  │
│  • is_system = TRUE                                                      │
│  • Hanya Super Admin yang bisa edit                                     │
│  • Contoh: content_types, device_statuses, roles                        │
│  • Caching: PERMANENT (sampai restart)                                   │
│                                                                          │
│  Level 2: TENANT TYPES (Semi-Static)                                    │
│  ────────────────────────────────────                                    │
│  • organization_id = tenant_id                                           │
│  • is_system = FALSE                                                     │
│  • Admin tenant yang bisa manage                                        │
│  • Contoh: room_categories, menu_categories, shift_types                │
│  • Caching: 1 hour TTL                                                   │
│                                                                          │
│  Level 3: USER TYPES (Dynamic)                                          │
│  ─────────────────────────────                                           │
│  • organization_id = tenant_id                                           │
│  • created_by_id = user_id                                               │
│  • User bisa create sendiri                                             │
│  • Contoh: tags, labels, custom_fields                                   │
│  • Caching: 5 minutes TTL atau no cache                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Classification Matrix:**

| Level | Scope | Managed By | Mutability | Cache TTL | Example Tables |
|-------|-------|------------|------------|-----------|----------------|
| **L1: System** | Global | Super Admin | Immutable | Permanent | content_types, roles, permissions |
| **L2: Tenant** | Organization | Tenant Admin | Semi-mutable | 1 hour | room_categories, menu_categories |
| **L3: User** | Organization | End User | Mutable | 5 min / None | tags, labels, custom_fields |

---

### 27.3 Standard Schema Pattern

#### Base Schema (WAJIB untuk semua lookup tables)

```sql
-- Template: {entity}_types atau {entity}_categories atau {entity}_statuses
CREATE TABLE {entity}_types (
    -- Primary Key
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Multi-tenancy (NULL = system-wide)
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,

    -- Core Fields
    code VARCHAR(50) NOT NULL,          -- Immutable identifier, UPPER_SNAKE_CASE
    name VARCHAR(100) NOT NULL,         -- Display name, localizable
    description TEXT,                   -- Optional description

    -- Ordering & Default
    display_order INTEGER DEFAULT 0,    -- For UI ordering
    is_default BOOLEAN DEFAULT FALSE,   -- Default selection

    -- Status Flags
    is_active BOOLEAN DEFAULT TRUE,     -- Soft delete
    is_system BOOLEAN DEFAULT FALSE,    -- System-managed vs user-managed

    -- Metadata (extensible)
    metadata JSONB DEFAULT '{}',        -- icon, color, config, etc.

    -- Hierarchy (optional)
    parent_id INTEGER REFERENCES {entity}_types(id) ON DELETE SET NULL,

    -- Audit Trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT uq_{entity}_types_org_code UNIQUE(organization_id, code),
    CONSTRAINT chk_{entity}_types_code_format CHECK (code ~ '^[A-Z][A-Z0-9_]*$')
);

-- Indexes
CREATE INDEX idx_{entity}_types_org ON {entity}_types(organization_id);
CREATE INDEX idx_{entity}_types_active ON {entity}_types(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_{entity}_types_parent ON {entity}_types(parent_id) WHERE parent_id IS NOT NULL;

-- Covering index untuk query umum
CREATE INDEX idx_{entity}_types_lookup ON {entity}_types(organization_id, is_active)
    INCLUDE (code, name, display_order);

-- Comment
COMMENT ON TABLE {entity}_types IS 'Lookup table untuk {entity} types';
COMMENT ON COLUMN {entity}_types.code IS 'Immutable identifier, format: UPPER_SNAKE_CASE';
COMMENT ON COLUMN {entity}_types.metadata IS 'Extensible: {icon?: string, color?: string, config?: object}';
```

#### Metadata Schema (Standardized)

```typescript
// Metadata structure untuk consistency
interface LookupMetadata {
    // Visual
    icon?: string;           // Icon name (lucide/heroicons)
    color?: string;          // Hex color atau Tailwind class
    badge_variant?: 'default' | 'success' | 'warning' | 'error' | 'info';

    // Behavior
    requires_approval?: boolean;
    max_per_entity?: number;
    allowed_transitions?: string[];  // Untuk status-type lookups

    // Validation
    validation_rules?: Record<string, any>;

    // Localization
    translations?: Record<string, { name: string; description?: string }>;

    // Custom
    [key: string]: any;
}
```

#### Example: Content Types Table

```sql
CREATE TABLE content_types (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    parent_id INTEGER REFERENCES content_types(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_content_types_org_code UNIQUE(organization_id, code),
    CONSTRAINT chk_content_types_code_format CHECK (code ~ '^[A-Z][A-Z0-9_]*$')
);

-- System types (organization_id = NULL)
INSERT INTO content_types (organization_id, code, name, display_order, is_system, metadata) VALUES
(NULL, 'IMAGE', 'Image', 1, TRUE, '{"icon": "image", "color": "#3B82F6", "allowed_extensions": ["jpg", "png", "gif", "webp"]}'),
(NULL, 'VIDEO', 'Video', 2, TRUE, '{"icon": "video", "color": "#EF4444", "allowed_extensions": ["mp4", "webm", "mov"]}'),
(NULL, 'WEBPAGE', 'Web Page', 3, TRUE, '{"icon": "globe", "color": "#10B981"}'),
(NULL, 'YOUTUBE', 'YouTube', 4, TRUE, '{"icon": "youtube", "color": "#FF0000"}'),
(NULL, 'STREAM', 'Live Stream', 5, TRUE, '{"icon": "radio", "color": "#8B5CF6"}');
```

---

### 27.4 Multi-Level Lookup Strategy

**Tenant Override System:** Tenant bisa override system types dengan custom values.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MULTI-LEVEL LOOKUP RESOLUTION                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Query: GET content_types for tenant_id = 5                             │
│                                                                          │
│  Step 1: Get System Types (organization_id IS NULL)                     │
│  ┌─────────────────────────────────────────┐                            │
│  │ IMAGE, VIDEO, WEBPAGE, YOUTUBE, STREAM  │  ← Base types             │
│  └─────────────────────────────────────────┘                            │
│                     │                                                    │
│                     ▼                                                    │
│  Step 2: Get Tenant Types (organization_id = 5)                         │
│  ┌─────────────────────────────────────────┐                            │
│  │ CUSTOM_PDF, CUSTOM_PPT                  │  ← Tenant additions        │
│  └─────────────────────────────────────────┘                            │
│                     │                                                    │
│                     ▼                                                    │
│  Step 3: Merge (tenant overrides system with same code)                 │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ IMAGE, VIDEO, WEBPAGE, YOUTUBE, STREAM, CUSTOM_PDF, CUSTOM_PPT │    │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                          │
│  Resolution Priority:                                                    │
│  1. Tenant-specific (organization_id = tenant_id) - HIGHEST            │
│  2. System-wide (organization_id IS NULL) - FALLBACK                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**SQL Query Pattern:**

```sql
-- Get merged lookup values for tenant with override support
WITH system_types AS (
    SELECT *, 'system' as source
    FROM content_types
    WHERE organization_id IS NULL
      AND is_active = TRUE
),
tenant_types AS (
    SELECT *, 'tenant' as source
    FROM content_types
    WHERE organization_id = :tenant_id
      AND is_active = TRUE
)
SELECT COALESCE(t.id, s.id) as id,
       COALESCE(t.code, s.code) as code,
       COALESCE(t.name, s.name) as name,
       COALESCE(t.description, s.description) as description,
       COALESCE(t.display_order, s.display_order) as display_order,
       COALESCE(t.is_default, s.is_default) as is_default,
       COALESCE(t.metadata, s.metadata) as metadata,
       COALESCE(t.source, s.source) as source
FROM system_types s
FULL OUTER JOIN tenant_types t ON s.code = t.code
WHERE COALESCE(t.is_active, s.is_active, TRUE)
ORDER BY COALESCE(t.display_order, s.display_order),
         COALESCE(t.name, s.name);
```

---

### 27.5 Backend Implementation

#### Base Repository Pattern

```python
# core/services/lookup/repositories/lookup_repo.py
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class LookupRepository(Generic[T]):
    """
    Generic repository untuk semua lookup tables.
    Implements multi-tenancy dan caching-aware queries.
    """

    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class

    async def get_for_tenant(
        self,
        organization_id: int,
        include_system: bool = True,
        include_inactive: bool = False
    ) -> List[T]:
        """
        Get lookup values for tenant with optional system fallback.

        Args:
            organization_id: Tenant ID
            include_system: Include system-wide values (org_id IS NULL)
            include_inactive: Include soft-deleted values

        Returns:
            List of lookup values, tenant-specific first
        """
        conditions = []

        if include_system:
            conditions.append(
                or_(
                    self.model_class.organization_id == organization_id,
                    self.model_class.organization_id.is_(None)
                )
            )
        else:
            conditions.append(
                self.model_class.organization_id == organization_id
            )

        if not include_inactive:
            conditions.append(self.model_class.is_active == True)

        query = (
            select(self.model_class)
            .where(and_(*conditions))
            .order_by(
                # Tenant-specific first
                self.model_class.organization_id.desc().nullslast(),
                self.model_class.display_order,
                self.model_class.name
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_code(
        self,
        organization_id: int,
        code: str
    ) -> Optional[T]:
        """
        Get single lookup by code with tenant override support.
        Tenant-specific takes precedence over system.
        """
        # Try tenant-specific first
        query = (
            select(self.model_class)
            .where(
                and_(
                    self.model_class.organization_id == organization_id,
                    self.model_class.code == code,
                    self.model_class.is_active == True
                )
            )
        )
        result = await self.session.execute(query)
        tenant_value = result.scalar_one_or_none()

        if tenant_value:
            return tenant_value

        # Fallback to system
        query = (
            select(self.model_class)
            .where(
                and_(
                    self.model_class.organization_id.is_(None),
                    self.model_class.code == code,
                    self.model_class.is_active == True
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, lookup_id: int) -> Optional[T]:
        """Get single lookup by ID."""
        query = select(self.model_class).where(self.model_class.id == lookup_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_default(self, organization_id: int) -> Optional[T]:
        """Get default value for tenant."""
        # Try tenant default first
        query = (
            select(self.model_class)
            .where(
                and_(
                    self.model_class.organization_id == organization_id,
                    self.model_class.is_default == True,
                    self.model_class.is_active == True
                )
            )
        )
        result = await self.session.execute(query)
        tenant_default = result.scalar_one_or_none()

        if tenant_default:
            return tenant_default

        # Fallback to system default
        query = (
            select(self.model_class)
            .where(
                and_(
                    self.model_class.organization_id.is_(None),
                    self.model_class.is_default == True,
                    self.model_class.is_active == True
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_merged_for_tenant(self, organization_id: int) -> List[dict]:
        """
        Get merged system + tenant values with override support.
        Uses raw SQL for optimal performance.
        """
        table_name = self.model_class.__tablename__

        query = f"""
        WITH system_types AS (
            SELECT *, 'system' as source
            FROM {table_name}
            WHERE organization_id IS NULL AND is_active = TRUE
        ),
        tenant_types AS (
            SELECT *, 'tenant' as source
            FROM {table_name}
            WHERE organization_id = :org_id AND is_active = TRUE
        )
        SELECT
            COALESCE(t.id, s.id) as id,
            COALESCE(t.code, s.code) as code,
            COALESCE(t.name, s.name) as name,
            COALESCE(t.description, s.description) as description,
            COALESCE(t.display_order, s.display_order) as display_order,
            COALESCE(t.is_default, s.is_default) as is_default,
            COALESCE(t.metadata, s.metadata)::text as metadata,
            COALESCE(t.source, s.source) as source,
            CASE WHEN t.id IS NOT NULL THEN TRUE ELSE FALSE END as is_overridden
        FROM system_types s
        FULL OUTER JOIN tenant_types t ON s.code = t.code
        ORDER BY COALESCE(t.display_order, s.display_order),
                 COALESCE(t.name, s.name)
        """

        result = await self.session.execute(
            text(query),
            {"org_id": organization_id}
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def set_default(
        self,
        organization_id: int,
        item_id: int
    ) -> Optional[T]:
        """Set item as default, clearing previous default."""
        # Clear existing defaults for this tenant
        await self.session.execute(
            update(self.model_class)
            .where(
                and_(
                    self.model_class.organization_id == organization_id,
                    self.model_class.is_default == True
                )
            )
            .values(is_default=False)
        )

        # Set new default
        await self.session.execute(
            update(self.model_class)
            .where(self.model_class.id == item_id)
            .values(is_default=True)
        )

        await self.session.commit()
        return await self.get_by_id(item_id)

    async def deactivate(self, item_id: int) -> bool:
        """Soft delete lookup item."""
        result = await self.session.execute(
            update(self.model_class)
            .where(
                and_(
                    self.model_class.id == item_id,
                    self.model_class.is_system == False  # Cannot deactivate system
                )
            )
            .values(is_active=False)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def reorder(
        self,
        organization_id: int,
        ordered_ids: List[int]
    ) -> bool:
        """Reorder lookup items by ID list."""
        for order, item_id in enumerate(ordered_ids):
            await self.session.execute(
                update(self.model_class)
                .where(
                    and_(
                        self.model_class.id == item_id,
                        self.model_class.organization_id == organization_id
                    )
                )
                .values(display_order=order)
            )
        await self.session.commit()
        return True
```

#### Lookup Service with Caching

```python
# core/services/lookup/services/lookup_service.py
from typing import TypeVar, Generic, List, Optional, Type, Dict, Any
from datetime import timedelta
import json

from shared.cache import redis_client
from .repositories.lookup_repo import LookupRepository

T = TypeVar('T')

class LookupService(Generic[T]):
    """
    Service layer untuk lookup tables dengan multi-level caching.

    Caching Strategy:
    - L1: In-memory (system types) - permanent
    - L2: Redis (tenant types) - 1 hour TTL
    - L3: Database - source of truth
    """

    # L1: In-memory cache untuk system types
    _system_cache: Dict[str, List[dict]] = {}

    # Cache TTL
    SYSTEM_TTL = None  # Permanent (until restart)
    TENANT_TTL = 3600  # 1 hour
    USER_TTL = 300     # 5 minutes

    def __init__(
        self,
        repository: LookupRepository[T],
        cache_prefix: str
    ):
        self.repository = repository
        self.cache_prefix = cache_prefix

    def _cache_key(self, organization_id: Optional[int]) -> str:
        """Generate cache key."""
        if organization_id is None:
            return f"lookup:{self.cache_prefix}:system"
        return f"lookup:{self.cache_prefix}:org:{organization_id}"

    async def get_all(
        self,
        organization_id: int,
        force_refresh: bool = False
    ) -> List[dict]:
        """
        Get all lookup values with caching.

        Resolution order:
        1. L1 (in-memory) for system types
        2. L2 (Redis) for tenant types
        3. L3 (Database) as fallback
        """
        cache_key = self._cache_key(organization_id)

        # Skip cache if force refresh
        if not force_refresh:
            # L1: Check in-memory (system types only)
            if organization_id is None and self.cache_prefix in self._system_cache:
                return self._system_cache[self.cache_prefix]

            # L2: Check Redis
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

        # L3: Database query
        items = await self.repository.get_merged_for_tenant(organization_id)

        # Update caches
        if organization_id is None:
            # System types: L1 cache
            self._system_cache[self.cache_prefix] = items

        # L2 cache (Redis) for all
        await redis_client.setex(
            cache_key,
            self.TENANT_TTL if organization_id else 86400,  # 1 day for system
            json.dumps(items)
        )

        return items

    async def get_by_code(
        self,
        organization_id: int,
        code: str
    ) -> Optional[dict]:
        """Get single item by code with caching."""
        items = await self.get_all(organization_id)
        return next((i for i in items if i['code'] == code), None)

    async def get_by_id(self, lookup_id: int) -> Optional[T]:
        """Get single item by ID (no cache, direct DB)."""
        return await self.repository.get_by_id(lookup_id)

    async def get_default(self, organization_id: int) -> Optional[dict]:
        """Get default item with caching."""
        items = await self.get_all(organization_id)
        return next((i for i in items if i.get('is_default')), None)

    async def invalidate_cache(self, organization_id: Optional[int] = None):
        """
        Invalidate cache after mutation.

        Args:
            organization_id: Specific tenant to invalidate, or None for system
        """
        if organization_id is None:
            # Clear system cache (in-memory + Redis)
            self._system_cache.pop(self.cache_prefix, None)
            await redis_client.delete(self._cache_key(None))
        else:
            # Clear tenant cache (Redis only)
            await redis_client.delete(self._cache_key(organization_id))

    async def create(
        self,
        organization_id: int,
        data: dict,
        created_by_id: int
    ) -> T:
        """Create new lookup item and invalidate cache."""
        item = await self.repository.create(
            organization_id=organization_id,
            created_by_id=created_by_id,
            **data
        )
        await self.invalidate_cache(organization_id)
        return item

    async def update(
        self,
        item_id: int,
        data: dict,
        updated_by_id: int
    ) -> Optional[T]:
        """Update lookup item and invalidate cache."""
        item = await self.repository.update(
            item_id=item_id,
            updated_by_id=updated_by_id,
            **data
        )
        if item:
            await self.invalidate_cache(item.organization_id)
        return item

    async def deactivate(self, item_id: int) -> bool:
        """Deactivate (soft delete) and invalidate cache."""
        item = await self.repository.get_by_id(item_id)
        if item:
            result = await self.repository.deactivate(item_id)
            if result:
                await self.invalidate_cache(item.organization_id)
            return result
        return False
```

#### Batch Loading untuk N+1 Prevention

```python
# core/services/lookup/services/batch_loader.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class LookupBatchLoader:
    """
    Batch loader untuk menghindari N+1 query problem.
    Collect semua lookup IDs, query sekali, enrich data.
    """

    _pending_ids: Dict[str, set] = field(default_factory=dict)
    _loaded_data: Dict[str, Dict[int, dict]] = field(default_factory=dict)

    def collect(self, lookup_type: str, lookup_id: int):
        """Collect ID untuk batch loading."""
        if lookup_type not in self._pending_ids:
            self._pending_ids[lookup_type] = set()
        self._pending_ids[lookup_type].add(lookup_id)

    async def load_all(self, session):
        """Load semua collected IDs dalam satu query per type."""
        for lookup_type, ids in self._pending_ids.items():
            if not ids:
                continue

            # Get model class dari registry
            model_class = LOOKUP_REGISTRY.get(lookup_type)
            if not model_class:
                continue

            # Single query untuk semua IDs
            query = select(model_class).where(model_class.id.in_(list(ids)))
            result = await session.execute(query)
            items = result.scalars().all()

            # Index by ID
            self._loaded_data[lookup_type] = {
                item.id: self._to_dict(item) for item in items
            }

        # Clear pending
        self._pending_ids.clear()

    def get(self, lookup_type: str, lookup_id: int) -> Optional[dict]:
        """Get loaded data by type and ID."""
        return self._loaded_data.get(lookup_type, {}).get(lookup_id)

    def enrich(self, data: dict, mappings: Dict[str, str]) -> dict:
        """
        Enrich data dengan lookup values.

        Args:
            data: Original data dict
            mappings: {field_name: lookup_type} mapping
                      e.g., {'content_type_id': 'content_types'}

        Returns:
            Enriched data with lookup objects
        """
        enriched = data.copy()

        for field_name, lookup_type in mappings.items():
            lookup_id = data.get(field_name)
            if lookup_id:
                lookup_data = self.get(lookup_type, lookup_id)
                if lookup_data:
                    # Add as nested object
                    base_name = field_name.replace('_id', '')
                    enriched[base_name] = lookup_data

        return enriched

    @staticmethod
    def _to_dict(item) -> dict:
        """Convert model to dict."""
        return {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'metadata': item.metadata
        }


# Usage example
async def get_contents_with_types(session, organization_id: int):
    """Example: Get contents dengan content_type enrichment."""

    # Step 1: Get contents
    contents = await content_repo.get_all(organization_id)

    # Step 2: Collect all content_type_ids
    loader = LookupBatchLoader()
    for content in contents:
        loader.collect('content_types', content.content_type_id)

    # Step 3: Batch load (single query)
    await loader.load_all(session)

    # Step 4: Enrich data
    enriched_contents = [
        loader.enrich(
            content.to_dict(),
            {'content_type_id': 'content_types'}
        )
        for content in contents
    ]

    return enriched_contents
```

---

### 27.6 API Pattern

#### RESTful Endpoints

```python
# core/services/lookup/routes.py
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/api/v1/lookups", tags=["Lookups"])

# ============================================
# Generic Lookup Endpoints
# ============================================

@router.get("/{lookup_type}")
async def get_lookup_values(
    lookup_type: str = Path(..., description="Lookup type: content_types, device_statuses, etc."),
    organization_id: int = Depends(get_current_org_id),
    include_inactive: bool = Query(False, description="Include inactive items"),
    include_system: bool = Query(True, description="Include system-wide items"),
    session: AsyncSession = Depends(get_session)
) -> List[LookupResponse]:
    """
    Get lookup values untuk tenant dengan optional system fallback.

    Response includes:
    - id, code, name, description
    - display_order, is_default
    - metadata (icon, color, etc.)
    - source ('system' atau 'tenant')
    - is_overridden (true jika tenant override system)
    """
    service = get_lookup_service(lookup_type, session)
    if not service:
        raise HTTPException(404, f"Unknown lookup type: {lookup_type}")

    return await service.get_all(organization_id)


@router.get("/{lookup_type}/{code}")
async def get_lookup_by_code(
    lookup_type: str,
    code: str = Path(..., description="Lookup code, e.g., 'IMAGE'"),
    organization_id: int = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session)
) -> LookupResponse:
    """Get single lookup by code."""
    service = get_lookup_service(lookup_type, session)
    item = await service.get_by_code(organization_id, code)
    if not item:
        raise HTTPException(404, f"{lookup_type} with code '{code}' not found")
    return item


@router.get("/{lookup_type}/default")
async def get_default_lookup(
    lookup_type: str,
    organization_id: int = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session)
) -> Optional[LookupResponse]:
    """Get default lookup value for tenant."""
    service = get_lookup_service(lookup_type, session)
    return await service.get_default(organization_id)


# ============================================
# Admin Endpoints (Tenant Admin+)
# ============================================

@router.post("/{lookup_type}")
async def create_lookup(
    lookup_type: str,
    data: LookupCreateRequest,
    organization_id: int = Depends(get_current_org_id),
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
) -> LookupResponse:
    """Create new lookup value untuk tenant."""
    service = get_lookup_service(lookup_type, session)
    return await service.create(
        organization_id=organization_id,
        data=data.dict(),
        created_by_id=current_user.id
    )


@router.patch("/{lookup_type}/{item_id}")
async def update_lookup(
    lookup_type: str,
    item_id: int,
    data: LookupUpdateRequest,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
) -> LookupResponse:
    """Update lookup value (tenant items only, not system)."""
    service = get_lookup_service(lookup_type, session)
    item = await service.get_by_id(item_id)

    if not item:
        raise HTTPException(404, "Lookup item not found")

    if item.is_system:
        raise HTTPException(403, "Cannot modify system lookup items")

    return await service.update(
        item_id=item_id,
        data=data.dict(exclude_unset=True),
        updated_by_id=current_user.id
    )


@router.delete("/{lookup_type}/{item_id}")
async def deactivate_lookup(
    lookup_type: str,
    item_id: int,
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Soft delete lookup value (tenant items only)."""
    service = get_lookup_service(lookup_type, session)
    item = await service.get_by_id(item_id)

    if not item:
        raise HTTPException(404, "Lookup item not found")

    if item.is_system:
        raise HTTPException(403, "Cannot delete system lookup items")

    success = await service.deactivate(item_id)
    return {"success": success}


@router.post("/{lookup_type}/{item_id}/set-default")
async def set_default_lookup(
    lookup_type: str,
    item_id: int,
    organization_id: int = Depends(get_current_org_id),
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
) -> LookupResponse:
    """Set lookup as default untuk tenant."""
    service = get_lookup_service(lookup_type, session)
    return await service.set_default(organization_id, item_id)


@router.post("/{lookup_type}/reorder")
async def reorder_lookups(
    lookup_type: str,
    data: ReorderRequest,
    organization_id: int = Depends(get_current_org_id),
    current_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Reorder lookup items untuk tenant."""
    service = get_lookup_service(lookup_type, session)
    success = await service.reorder(organization_id, data.ordered_ids)
    return {"success": success}


# ============================================
# Bulk Endpoints
# ============================================

@router.post("/bulk")
async def get_multiple_lookups(
    data: BulkLookupRequest,
    organization_id: int = Depends(get_current_org_id),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, List[LookupResponse]]:
    """
    Get multiple lookup types in single request.

    Request body:
    {
        "types": ["content_types", "device_statuses", "playlist_types"]
    }

    Response:
    {
        "content_types": [...],
        "device_statuses": [...],
        "playlist_types": [...]
    }
    """
    result = {}
    for lookup_type in data.types:
        service = get_lookup_service(lookup_type, session)
        if service:
            result[lookup_type] = await service.get_all(organization_id)
    return result


@router.post("/cache/invalidate")
async def invalidate_lookup_cache(
    lookup_type: Optional[str] = Query(None, description="Specific type, or all if not provided"),
    current_user: User = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Invalidate lookup cache (Super Admin only)."""
    if lookup_type:
        service = get_lookup_service(lookup_type, session)
        if service:
            await service.invalidate_cache()
    else:
        # Invalidate all
        for lt in LOOKUP_REGISTRY.keys():
            service = get_lookup_service(lt, session)
            await service.invalidate_cache()

    return {"success": True, "message": "Cache invalidated"}
```

#### DTOs (Pydantic Models)

```python
# core/services/lookup/dtos.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class LookupMetadata(BaseModel):
    """Standard metadata schema."""
    icon: Optional[str] = None
    color: Optional[str] = None
    badge_variant: Optional[str] = None
    translations: Optional[Dict[str, Dict[str, str]]] = None

    class Config:
        extra = "allow"  # Allow additional fields


class LookupResponse(BaseModel):
    """Response DTO untuk lookup items."""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    display_order: int = 0
    is_default: bool = False
    is_active: bool = True
    is_system: bool = False
    metadata: Optional[LookupMetadata] = None
    source: Optional[str] = None  # 'system' atau 'tenant'
    is_overridden: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LookupCreateRequest(BaseModel):
    """Request DTO untuk create lookup."""
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: int = 0
    is_default: bool = False
    metadata: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None

    @validator('code')
    def validate_code(cls, v):
        if not re.match(r'^[A-Z][A-Z0-9_]*$', v):
            raise ValueError('Code must be UPPER_SNAKE_CASE')
        return v


class LookupUpdateRequest(BaseModel):
    """Request DTO untuk update lookup."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None


class ReorderRequest(BaseModel):
    """Request DTO untuk reorder."""
    ordered_ids: List[int]


class BulkLookupRequest(BaseModel):
    """Request DTO untuk bulk lookup."""
    types: List[str] = Field(..., min_items=1, max_items=20)
```

---

### 27.7 Frontend Implementation

#### useLookup Hook

```typescript
// shared/hooks/useLookup.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface LookupItem {
    id: number;
    code: string;
    name: string;
    description?: string;
    displayOrder: number;
    isDefault: boolean;
    isActive: boolean;
    isSystem: boolean;
    metadata?: {
        icon?: string;
        color?: string;
        badgeVariant?: string;
        [key: string]: any;
    };
    source?: 'system' | 'tenant';
    isOverridden?: boolean;
}

interface UseLookupOptions {
    includeInactive?: boolean;
    includeSystem?: boolean;
    enabled?: boolean;
}

/**
 * Hook untuk fetch dan manage lookup values.
 *
 * @example
 * const { data: contentTypes, isLoading } = useLookup('content_types');
 *
 * @example
 * const { getByCode, getDefault } = useLookup('device_statuses');
 * const onlineStatus = getByCode('ONLINE');
 */
export function useLookup(
    lookupType: string,
    options: UseLookupOptions = {}
) {
    const queryClient = useQueryClient();
    const { includeInactive = false, includeSystem = true, enabled = true } = options;

    // Query key untuk caching
    const queryKey = ['lookups', lookupType, { includeInactive, includeSystem }];

    // Fetch lookup data
    const query = useQuery({
        queryKey,
        queryFn: async () => {
            const params = new URLSearchParams();
            if (includeInactive) params.set('include_inactive', 'true');
            if (!includeSystem) params.set('include_system', 'false');

            const response = await api.get<LookupItem[]>(
                `/lookups/${lookupType}?${params}`
            );
            return response.data;
        },
        enabled,
        staleTime: 5 * 60 * 1000,  // 5 minutes
        gcTime: 30 * 60 * 1000,    // 30 minutes (was cacheTime)
    });

    // Helper functions
    const getByCode = (code: string): LookupItem | undefined => {
        return query.data?.find(item => item.code === code);
    };

    const getById = (id: number): LookupItem | undefined => {
        return query.data?.find(item => item.id === id);
    };

    const getDefault = (): LookupItem | undefined => {
        return query.data?.find(item => item.isDefault);
    };

    const getActiveItems = (): LookupItem[] => {
        return query.data?.filter(item => item.isActive) ?? [];
    };

    const getForSelect = (): { value: number; label: string }[] => {
        return (query.data ?? [])
            .filter(item => item.isActive)
            .map(item => ({
                value: item.id,
                label: item.name,
            }));
    };

    // Mutations
    const createMutation = useMutation({
        mutationFn: async (data: Partial<LookupItem>) => {
            const response = await api.post<LookupItem>(`/lookups/${lookupType}`, data);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['lookups', lookupType] });
        },
    });

    const updateMutation = useMutation({
        mutationFn: async ({ id, data }: { id: number; data: Partial<LookupItem> }) => {
            const response = await api.patch<LookupItem>(`/lookups/${lookupType}/${id}`, data);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['lookups', lookupType] });
        },
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: number) => {
            await api.delete(`/lookups/${lookupType}/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['lookups', lookupType] });
        },
    });

    const setDefaultMutation = useMutation({
        mutationFn: async (id: number) => {
            const response = await api.post<LookupItem>(
                `/lookups/${lookupType}/${id}/set-default`
            );
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['lookups', lookupType] });
        },
    });

    const reorderMutation = useMutation({
        mutationFn: async (orderedIds: number[]) => {
            await api.post(`/lookups/${lookupType}/reorder`, { ordered_ids: orderedIds });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['lookups', lookupType] });
        },
    });

    return {
        // Query state
        data: query.data ?? [],
        isLoading: query.isLoading,
        isError: query.isError,
        error: query.error,
        refetch: query.refetch,

        // Helpers
        getByCode,
        getById,
        getDefault,
        getActiveItems,
        getForSelect,

        // Mutations
        create: createMutation.mutateAsync,
        update: updateMutation.mutateAsync,
        delete: deleteMutation.mutateAsync,
        setDefault: setDefaultMutation.mutateAsync,
        reorder: reorderMutation.mutateAsync,

        // Mutation states
        isCreating: createMutation.isPending,
        isUpdating: updateMutation.isPending,
        isDeleting: deleteMutation.isPending,
    };
}
```

#### useBulkLookups Hook

```typescript
// shared/hooks/useBulkLookups.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

type LookupMap = Record<string, LookupItem[]>;

/**
 * Hook untuk fetch multiple lookup types dalam satu request.
 * Optimal untuk pages yang butuh banyak lookups.
 *
 * @example
 * const { lookups, getLookup } = useBulkLookups([
 *     'content_types',
 *     'device_statuses',
 *     'playlist_types'
 * ]);
 *
 * const contentTypes = getLookup('content_types');
 */
export function useBulkLookups(types: string[]) {
    const query = useQuery({
        queryKey: ['lookups', 'bulk', types],
        queryFn: async () => {
            const response = await api.post<LookupMap>('/lookups/bulk', { types });
            return response.data;
        },
        enabled: types.length > 0,
        staleTime: 5 * 60 * 1000,
    });

    const getLookup = (type: string): LookupItem[] => {
        return query.data?.[type] ?? [];
    };

    const getByCode = (type: string, code: string): LookupItem | undefined => {
        return getLookup(type).find(item => item.code === code);
    };

    return {
        lookups: query.data ?? {},
        isLoading: query.isLoading,
        getLookup,
        getByCode,
    };
}
```

#### LookupSelect Component

```typescript
// shared/components/LookupSelect.tsx
import React from 'react';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { useLookup } from '@/shared/hooks/useLookup';
import { Skeleton } from '@/components/ui/skeleton';

interface LookupSelectProps {
    lookupType: string;
    value?: number;
    onChange: (value: number | undefined) => void;
    placeholder?: string;
    disabled?: boolean;
    includeInactive?: boolean;
    className?: string;
    showIcon?: boolean;
    showColor?: boolean;
}

export function LookupSelect({
    lookupType,
    value,
    onChange,
    placeholder = 'Select...',
    disabled = false,
    includeInactive = false,
    className,
    showIcon = true,
    showColor = true,
}: LookupSelectProps) {
    const { data, isLoading, getActiveItems } = useLookup(lookupType, {
        includeInactive,
    });

    const items = includeInactive ? data : getActiveItems();

    if (isLoading) {
        return <Skeleton className="h-10 w-full" />;
    }

    return (
        <Select
            value={value?.toString()}
            onValueChange={(val) => onChange(val ? parseInt(val) : undefined)}
            disabled={disabled}
        >
            <SelectTrigger className={className}>
                <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent>
                {items.map((item) => (
                    <SelectItem key={item.id} value={item.id.toString()}>
                        <div className="flex items-center gap-2">
                            {showColor && item.metadata?.color && (
                                <span
                                    className="w-3 h-3 rounded-full"
                                    style={{ backgroundColor: item.metadata.color }}
                                />
                            )}
                            {showIcon && item.metadata?.icon && (
                                <span className="text-muted-foreground">
                                    {/* Icon component based on icon name */}
                                </span>
                            )}
                            <span>{item.name}</span>
                            {item.isDefault && (
                                <span className="text-xs text-muted-foreground">(Default)</span>
                            )}
                        </div>
                    </SelectItem>
                ))}
            </SelectContent>
        </Select>
    );
}
```

#### Preloading Strategy

```typescript
// shared/providers/LookupProvider.tsx
import React, { createContext, useContext, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Lookup types yang sering digunakan - preload saat app start
const PRELOAD_LOOKUPS = [
    'content_types',
    'device_statuses',
    'playlist_types',
    'roles',
];

interface LookupContextValue {
    isPreloaded: boolean;
    preloadLookups: () => Promise<void>;
}

const LookupContext = createContext<LookupContextValue | null>(null);

export function LookupProvider({ children }: { children: React.ReactNode }) {
    const queryClient = useQueryClient();
    const [isPreloaded, setIsPreloaded] = React.useState(false);

    const preloadLookups = async () => {
        try {
            const response = await api.post<Record<string, any[]>>('/lookups/bulk', {
                types: PRELOAD_LOOKUPS,
            });

            // Populate query cache
            Object.entries(response.data).forEach(([type, data]) => {
                queryClient.setQueryData(
                    ['lookups', type, { includeInactive: false, includeSystem: true }],
                    data
                );
            });

            setIsPreloaded(true);
        } catch (error) {
            console.error('Failed to preload lookups:', error);
        }
    };

    useEffect(() => {
        preloadLookups();
    }, []);

    return (
        <LookupContext.Provider value={{ isPreloaded, preloadLookups }}>
            {children}
        </LookupContext.Provider>
    );
}

export function useLookupContext() {
    const context = useContext(LookupContext);
    if (!context) {
        throw new Error('useLookupContext must be used within LookupProvider');
    }
    return context;
}
```

---

### 27.8 Caching Strategy

#### 3-Level Caching Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    3-LEVEL CACHING ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Request: GET /lookups/content_types                                    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  L1: IN-MEMORY CACHE (Python dict)                               │   │
│  │  ─────────────────────────────────                               │   │
│  │  • TTL: Permanent (system) / None (tenant)                      │   │
│  │  • Access: < 0.1ms                                               │   │
│  │  • Scope: Per-process                                            │   │
│  │  • Use: System types only                                        │   │
│  │                                                                   │   │
│  │  _system_cache = {                                               │   │
│  │      'content_types': [...],                                     │   │
│  │      'device_statuses': [...],                                   │   │
│  │  }                                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          │ MISS                                         │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  L2: REDIS CACHE                                                 │   │
│  │  ───────────────                                                 │   │
│  │  • TTL: 1 hour (tenant) / 24 hours (system)                     │   │
│  │  • Access: < 5ms                                                 │   │
│  │  • Scope: Shared across processes                                │   │
│  │  • Use: All lookup types                                         │   │
│  │                                                                   │   │
│  │  Keys:                                                           │   │
│  │  • lookup:content_types:system                                   │   │
│  │  • lookup:content_types:org:123                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          │ MISS                                         │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  L3: DATABASE (PostgreSQL)                                       │   │
│  │  ─────────────────────────                                       │   │
│  │  • Access: < 20ms (with proper indexes)                          │   │
│  │  • Scope: Source of truth                                        │   │
│  │  • Query: Optimized with covering indexes                        │   │
│  │                                                                   │   │
│  │  SELECT * FROM content_types                                     │   │
│  │  WHERE organization_id = :org_id OR organization_id IS NULL      │   │
│  │  ORDER BY display_order, name                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Cache Invalidation Flow:                                               │
│  ──────────────────────────                                              │
│  On CREATE/UPDATE/DELETE:                                               │
│  1. Update database (L3)                                                │
│  2. Delete Redis key (L2)                                               │
│  3. Clear in-memory if system type (L1)                                │
│  4. Publish event for other processes (optional)                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Cache Configuration

```python
# core/services/lookup/config.py
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CacheLevel(Enum):
    NONE = "none"           # No caching
    REDIS_ONLY = "redis"    # L2 only
    FULL = "full"           # L1 + L2

@dataclass
class LookupCacheConfig:
    """Configuration untuk lookup caching per type."""

    lookup_type: str
    cache_level: CacheLevel
    redis_ttl: int              # seconds
    memory_ttl: Optional[int]   # seconds, None = permanent
    preload: bool               # Load on startup

    @classmethod
    def system_config(cls, lookup_type: str) -> 'LookupCacheConfig':
        """Config untuk system types (permanent cache)."""
        return cls(
            lookup_type=lookup_type,
            cache_level=CacheLevel.FULL,
            redis_ttl=86400,     # 24 hours
            memory_ttl=None,     # Permanent
            preload=True
        )

    @classmethod
    def tenant_config(cls, lookup_type: str) -> 'LookupCacheConfig':
        """Config untuk tenant types (1 hour TTL)."""
        return cls(
            lookup_type=lookup_type,
            cache_level=CacheLevel.REDIS_ONLY,
            redis_ttl=3600,      # 1 hour
            memory_ttl=None,     # No in-memory
            preload=False
        )

    @classmethod
    def user_config(cls, lookup_type: str) -> 'LookupCacheConfig':
        """Config untuk user types (5 min TTL)."""
        return cls(
            lookup_type=lookup_type,
            cache_level=CacheLevel.REDIS_ONLY,
            redis_ttl=300,       # 5 minutes
            memory_ttl=None,
            preload=False
        )

    @classmethod
    def no_cache_config(cls, lookup_type: str) -> 'LookupCacheConfig':
        """Config untuk dynamic types (no cache)."""
        return cls(
            lookup_type=lookup_type,
            cache_level=CacheLevel.NONE,
            redis_ttl=0,
            memory_ttl=None,
            preload=False
        )


# Registry of cache configs
LOOKUP_CACHE_CONFIGS = {
    # System types - permanent cache
    'content_types': LookupCacheConfig.system_config('content_types'),
    'device_statuses': LookupCacheConfig.system_config('device_statuses'),
    'roles': LookupCacheConfig.system_config('roles'),
    'permissions': LookupCacheConfig.system_config('permissions'),

    # Tenant types - 1 hour cache
    'room_categories': LookupCacheConfig.tenant_config('room_categories'),
    'menu_categories': LookupCacheConfig.tenant_config('menu_categories'),
    'shift_types': LookupCacheConfig.tenant_config('shift_types'),

    # User types - 5 min cache
    'tags': LookupCacheConfig.user_config('tags'),
    'labels': LookupCacheConfig.user_config('labels'),

    # Dynamic - no cache
    'custom_fields': LookupCacheConfig.no_cache_config('custom_fields'),
}
```

---

### 27.9 Performance Optimization

#### Database Indexes

```sql
-- ============================================
-- COVERING INDEXES untuk optimal read performance
-- ============================================

-- Index untuk query umum: get all active for tenant
CREATE INDEX idx_{entity}_types_lookup ON {entity}_types(
    organization_id,
    is_active
) INCLUDE (code, name, display_order, metadata);

-- Index untuk get by code dengan tenant resolution
CREATE INDEX idx_{entity}_types_code_lookup ON {entity}_types(
    code,
    organization_id
) WHERE is_active = TRUE;

-- Index untuk default value lookup
CREATE INDEX idx_{entity}_types_default ON {entity}_types(
    organization_id
) WHERE is_default = TRUE AND is_active = TRUE;

-- Partial index untuk system types only
CREATE INDEX idx_{entity}_types_system ON {entity}_types(
    code,
    display_order
) WHERE organization_id IS NULL AND is_active = TRUE;

-- ============================================
-- QUERY ANALYSIS
-- ============================================

-- Explain analyze untuk verify index usage
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM content_types
WHERE (organization_id = 123 OR organization_id IS NULL)
  AND is_active = TRUE
ORDER BY display_order, name;

-- Expected: Index Scan using idx_content_types_lookup
-- Rows: ~20 (typical lookup table size)
-- Time: < 1ms
```

#### N+1 Problem Solutions

```python
# ============================================
# ANTI-PATTERN: N+1 Queries
# ============================================

# BAD: N+1 queries
async def get_contents_bad(session, org_id):
    contents = await content_repo.get_all(org_id)

    for content in contents:
        # N queries untuk N contents!
        content_type = await lookup_repo.get_by_id(content.content_type_id)
        content.content_type = content_type

    return contents

# ============================================
# SOLUTION 1: JOIN (Single Query)
# ============================================

# GOOD: Single query dengan JOIN
async def get_contents_with_join(session, org_id):
    query = (
        select(ContentModel, ContentTypeModel)
        .join(ContentTypeModel, ContentModel.content_type_id == ContentTypeModel.id)
        .where(ContentModel.organization_id == org_id)
    )
    result = await session.execute(query)

    contents = []
    for content, content_type in result.all():
        content_dict = content.to_dict()
        content_dict['content_type'] = content_type.to_dict()
        contents.append(content_dict)

    return contents

# ============================================
# SOLUTION 2: Batch Loading
# ============================================

# GOOD: Batch load dengan 2 queries total
async def get_contents_with_batch(session, org_id):
    # Query 1: Get contents
    contents = await content_repo.get_all(org_id)

    # Collect unique type IDs
    type_ids = {c.content_type_id for c in contents}

    # Query 2: Batch load types
    types = await lookup_repo.get_by_ids(list(type_ids))
    types_map = {t.id: t for t in types}

    # Enrich
    for content in contents:
        content.content_type = types_map.get(content.content_type_id)

    return contents

# ============================================
# SOLUTION 3: Cache Enrichment (Best untuk lookups)
# ============================================

# BEST: Use cached lookups untuk enrichment
async def get_contents_with_cache(session, org_id):
    # Get cached lookups (no DB query if cached)
    content_types = await lookup_service.get_all(org_id)
    types_map = {t['id']: t for t in content_types}

    # Get contents
    contents = await content_repo.get_all(org_id)

    # Enrich dari cache
    for content in contents:
        content.content_type = types_map.get(content.content_type_id)

    return contents
```

#### Frontend Optimization

```typescript
// ============================================
// PRELOADING: Load lookups sebelum dibutuhkan
// ============================================

// Di App.tsx atau layout
function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <LookupProvider>  {/* Preload common lookups */}
                <Router />
            </LookupProvider>
        </QueryClientProvider>
    );
}

// ============================================
// BULK LOADING: Single request untuk multiple types
// ============================================

// BAD: Multiple requests
function ContentPage() {
    const { data: contentTypes } = useLookup('content_types');
    const { data: statuses } = useLookup('content_statuses');
    const { data: categories } = useLookup('content_categories');
    // = 3 HTTP requests
}

// GOOD: Single bulk request
function ContentPage() {
    const { lookups, getLookup } = useBulkLookups([
        'content_types',
        'content_statuses',
        'content_categories'
    ]);
    // = 1 HTTP request

    const contentTypes = getLookup('content_types');
}

// ============================================
// VIRTUALIZATION: For long lists
// ============================================

import { useVirtualizer } from '@tanstack/react-virtual';

function LookupManager({ lookupType }: { lookupType: string }) {
    const { data } = useLookup(lookupType, { includeInactive: true });
    const parentRef = React.useRef<HTMLDivElement>(null);

    const virtualizer = useVirtualizer({
        count: data.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 48,  // row height
        overscan: 5,
    });

    return (
        <div ref={parentRef} className="h-[400px] overflow-auto">
            <div style={{ height: virtualizer.getTotalSize() }}>
                {virtualizer.getVirtualItems().map((virtualRow) => {
                    const item = data[virtualRow.index];
                    return (
                        <div
                            key={item.id}
                            style={{
                                position: 'absolute',
                                top: virtualRow.start,
                                height: virtualRow.size,
                            }}
                        >
                            <LookupRow item={item} />
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
```

---

### 27.10 Performance SLA

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOOKUP PERFORMANCE SLA                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Target Response Times:                                                  │
│  ──────────────────────                                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Operation              │  Target  │  Max    │  Cache Level    │    │
│  ├────────────────────────────────────────────────────────────────┤    │
│  │  L1 Hit (In-memory)     │  < 0.1ms │  0.5ms  │  System types   │    │
│  │  L2 Hit (Redis)         │  < 2ms   │  5ms    │  All types      │    │
│  │  L3 Query (Database)    │  < 10ms  │  20ms   │  Cache miss     │    │
│  │  Bulk Request (5 types) │  < 20ms  │  50ms   │  Mixed          │    │
│  │  Full Page Load         │  < 100ms │  200ms  │  With preload   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  Cache Hit Rate Targets:                                                │
│  ────────────────────────                                                │
│                                                                          │
│  │  Lookup Classification  │  Target Hit Rate  │  TTL           │      │
│  ├─────────────────────────┼───────────────────┼────────────────┤      │
│  │  System Types           │  > 99%            │  Permanent     │      │
│  │  Tenant Types           │  > 95%            │  1 hour        │      │
│  │  User Types             │  > 80%            │  5 minutes     │      │
│                                                                          │
│  Monitoring Metrics:                                                     │
│  ──────────────────                                                      │
│                                                                          │
│  • lookup_request_duration_seconds (histogram)                          │
│  • lookup_cache_hits_total (counter)                                    │
│  • lookup_cache_misses_total (counter)                                  │
│  • lookup_db_queries_total (counter)                                    │
│                                                                          │
│  Alerting Thresholds:                                                    │
│  ────────────────────                                                    │
│                                                                          │
│  • P95 latency > 50ms → Warning                                         │
│  • P99 latency > 100ms → Critical                                       │
│  • Cache hit rate < 90% → Warning                                       │
│  • Cache hit rate < 80% → Critical                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Monitoring Implementation

```python
# core/services/lookup/monitoring.py
from prometheus_client import Histogram, Counter
import time
from functools import wraps

# Metrics
LOOKUP_DURATION = Histogram(
    'lookup_request_duration_seconds',
    'Lookup request duration',
    ['lookup_type', 'cache_level'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25]
)

LOOKUP_CACHE_HITS = Counter(
    'lookup_cache_hits_total',
    'Lookup cache hits',
    ['lookup_type', 'cache_level']
)

LOOKUP_CACHE_MISSES = Counter(
    'lookup_cache_misses_total',
    'Lookup cache misses',
    ['lookup_type']
)

def track_lookup_metrics(lookup_type: str):
    """Decorator untuk track lookup metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            cache_level = 'miss'

            try:
                result, cache_level = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                LOOKUP_DURATION.labels(
                    lookup_type=lookup_type,
                    cache_level=cache_level
                ).observe(duration)

                if cache_level != 'miss':
                    LOOKUP_CACHE_HITS.labels(
                        lookup_type=lookup_type,
                        cache_level=cache_level
                    ).inc()
                else:
                    LOOKUP_CACHE_MISSES.labels(
                        lookup_type=lookup_type
                    ).inc()

        return wrapper
    return decorator
```

---

### 27.11 Integration dengan Standards Lain

#### Integration dengan Standard #17 (Centralized Registries)

```python
# shared/constants/lookups.py
"""
Centralized lookup type registry.
Sesuai Standard #17: Centralized Registries.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Type

class LookupType(str, Enum):
    """Registry of all lookup types in the system."""

    # Content & Media
    CONTENT_TYPES = "content_types"
    CONTENT_STATUSES = "content_statuses"

    # Devices
    DEVICE_STATUSES = "device_statuses"
    DEVICE_TYPES = "device_types"

    # Playlists
    PLAYLIST_TYPES = "playlist_types"
    PLAYLIST_STATUSES = "playlist_statuses"

    # Organizations & Users
    ROLES = "roles"
    PERMISSIONS = "permissions"

    # PMS (Future)
    ROOM_CATEGORIES = "room_categories"
    ROOM_STATUSES = "room_statuses"
    BOOKING_STATUSES = "booking_statuses"

    # POS (Future)
    MENU_CATEGORIES = "menu_categories"
    PAYMENT_METHODS = "payment_methods"

# Model registry untuk setiap lookup type
LOOKUP_MODEL_REGISTRY: Dict[str, Type] = {
    LookupType.CONTENT_TYPES: ContentTypeModel,
    LookupType.DEVICE_STATUSES: DeviceStatusModel,
    # ...
}
```

#### Integration dengan Standard #18 (Event/Message Schema)

```python
# Lookup mutation events
LOOKUP_EVENTS = {
    'lookup.created': {
        'payload': {
            'lookup_type': str,
            'lookup_id': int,
            'organization_id': Optional[int],
            'code': str,
        }
    },
    'lookup.updated': {
        'payload': {
            'lookup_type': str,
            'lookup_id': int,
            'organization_id': Optional[int],
            'changes': dict,
        }
    },
    'lookup.deleted': {
        'payload': {
            'lookup_type': str,
            'lookup_id': int,
            'organization_id': Optional[int],
        }
    },
}

# Event handler untuk cache invalidation
@event_bus.subscribe('lookup.*')
async def handle_lookup_mutation(event):
    """Invalidate cache on any lookup mutation."""
    lookup_type = event.payload['lookup_type']
    organization_id = event.payload.get('organization_id')

    service = get_lookup_service(lookup_type)
    await service.invalidate_cache(organization_id)
```

#### Integration dengan Standard #5 (Caching)

```python
# Cache key patterns sesuai Standard #5
LOOKUP_CACHE_PATTERNS = {
    # Pattern: lookup:{type}:system
    # Example: lookup:content_types:system
    'system': 'lookup:{type}:system',

    # Pattern: lookup:{type}:org:{org_id}
    # Example: lookup:content_types:org:123
    'tenant': 'lookup:{type}:org:{org_id}',

    # Pattern: lookup:{type}:user:{user_id}
    # Example: lookup:tags:user:456
    'user': 'lookup:{type}:user:{user_id}',
}
```

---

### 27.12 Best Practices

#### DO's

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ✅ DO's - Best Practices untuk Lookup Tables                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. SCHEMA                                                              │
│     ✅ Gunakan code sebagai immutable identifier                        │
│     ✅ Format code: UPPER_SNAKE_CASE                                    │
│     ✅ Tambahkan CHECK constraint untuk code format                     │
│     ✅ Gunakan UNIQUE constraint pada (organization_id, code)           │
│     ✅ Tambahkan covering index untuk query patterns                    │
│                                                                          │
│  2. CACHING                                                             │
│     ✅ Cache system types secara permanent di memory                    │
│     ✅ Gunakan Redis untuk tenant-specific data                         │
│     ✅ Invalidate cache setelah setiap mutation                         │
│     ✅ Preload common lookups saat application start                    │
│                                                                          │
│  3. API                                                                 │
│     ✅ Sediakan bulk endpoint untuk multiple types                      │
│     ✅ Include metadata dalam response                                  │
│     ✅ Return 'source' field untuk transparency                         │
│     ✅ Support reordering via API                                       │
│                                                                          │
│  4. FRONTEND                                                            │
│     ✅ Gunakan generic hook (useLookup)                                 │
│     ✅ Implement preloading untuk common types                          │
│     ✅ Cache di TanStack Query dengan staleTime                         │
│     ✅ Provide helper functions (getByCode, getDefault)                 │
│                                                                          │
│  5. PERFORMANCE                                                         │
│     ✅ Batch load untuk menghindari N+1                                 │
│     ✅ Use covering indexes                                             │
│     ✅ Monitor cache hit rates                                          │
│     ✅ Set alerting untuk SLA violations                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### DON'Ts

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ❌ DON'Ts - Anti-Patterns untuk Lookup Tables                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. SCHEMA                                                              │
│     ❌ JANGAN gunakan ID sebagai identifier di code (gunakan code)      │
│     ❌ JANGAN allow NULL untuk code atau name                           │
│     ❌ JANGAN buat lookup table tanpa organization_id                   │
│     ❌ JANGAN skip is_system flag untuk system types                    │
│                                                                          │
│  2. CACHING                                                             │
│     ❌ JANGAN cache tanpa invalidation strategy                         │
│     ❌ JANGAN use same TTL untuk semua lookup types                     │
│     ❌ JANGAN skip caching untuk frequently accessed types              │
│     ❌ JANGAN cache user-specific data terlalu lama                     │
│                                                                          │
│  3. API                                                                 │
│     ❌ JANGAN allow delete system lookup items                          │
│     ❌ JANGAN allow modifying code setelah created                      │
│     ❌ JANGAN return inactive items by default                          │
│     ❌ JANGAN skip validation untuk code format                         │
│                                                                          │
│  4. FRONTEND                                                            │
│     ❌ JANGAN fetch lookups di setiap component mount                   │
│     ❌ JANGAN hardcode lookup values di frontend                        │
│     ❌ JANGAN skip loading states                                       │
│     ❌ JANGAN ignore error handling                                     │
│                                                                          │
│  5. PERFORMANCE                                                         │
│     ❌ JANGAN query lookup per item (N+1)                               │
│     ❌ JANGAN skip indexes untuk lookup tables                          │
│     ❌ JANGAN ignore cache hit rate monitoring                          │
│     ❌ JANGAN use LIKE queries untuk code matching                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 27.13 Anti-Patterns

#### Anti-Pattern 1: Hardcoded Values

```typescript
// ❌ BAD: Hardcoded lookup values
function ContentTypeSelect() {
    const options = [
        { value: 1, label: 'Image' },
        { value: 2, label: 'Video' },
        { value: 3, label: 'Webpage' },
    ];

    return <Select options={options} />;
}

// ✅ GOOD: Dynamic from API
function ContentTypeSelect() {
    const { getForSelect } = useLookup('content_types');
    return <Select options={getForSelect()} />;
}
```

#### Anti-Pattern 2: ID-based Comparisons

```typescript
// ❌ BAD: Comparing by ID (fragile)
if (content.content_type_id === 1) {
    // Handle image...
}

// ✅ GOOD: Comparing by code (stable)
const contentType = getByCode(content.content_type_id);
if (contentType?.code === 'IMAGE') {
    // Handle image...
}
```

#### Anti-Pattern 3: Missing Multi-Tenancy

```python
# ❌ BAD: Global lookup tanpa tenant filter
async def get_content_types():
    return await session.execute(
        select(ContentTypeModel)
    )

# ✅ GOOD: Tenant-aware dengan fallback
async def get_content_types(organization_id: int):
    return await session.execute(
        select(ContentTypeModel)
        .where(
            or_(
                ContentTypeModel.organization_id == organization_id,
                ContentTypeModel.organization_id.is_(None)
            )
        )
    )
```

#### Anti-Pattern 4: Cache Without Invalidation

```python
# ❌ BAD: Cache tanpa invalidation
async def get_content_types(org_id):
    cached = await redis.get(f"types:{org_id}")
    if cached:
        return cached

    data = await db_query()
    await redis.set(f"types:{org_id}", data)
    return data

async def update_content_type(id, data):
    await db_update(id, data)
    # Cache tidak di-invalidate!

# ✅ GOOD: Cache dengan proper invalidation
async def update_content_type(id, data):
    item = await db_update(id, data)
    await redis.delete(f"types:{item.organization_id}")
    return item
```

---

## Summary

Standard #27: Lookup/Type Tables menyediakan:

1. **Schema Pattern** - Standardized structure untuk semua lookup tables
2. **Classification** - System / Tenant / User types dengan different caching
3. **Multi-Level Lookup** - Tenant override system types
4. **Caching Strategy** - 3-level: Memory → Redis → Database
5. **Performance SLA** - Clear targets dan monitoring
6. **Integration** - Dengan existing standards (#5, #17, #18)

**Key Metrics:**
- L1 Cache Hit: < 0.5ms
- L2 Cache Hit: < 5ms
- L3 Database Query: < 20ms
- Cache Hit Rate Target: > 95%

---

*Last Updated: 2025-12-09*
