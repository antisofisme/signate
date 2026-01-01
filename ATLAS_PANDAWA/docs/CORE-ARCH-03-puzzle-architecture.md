# Puzzle Architecture - Modular Enterprise Platform

> Arsitektur modular "puzzle-like" untuk membangun aplikasi enterprise yang fleksibel dan mudah dikembangkan.

---

## Daftar Isi

1. [Konsep Dasar](#1-konsep-dasar)
   - 1.1 Apa itu Puzzle Architecture?
   - 1.2 Prinsip Utama
   - 1.3 Kenapa Modular Monolith?
   - 1.4 **Arsitektur 4-Layer** ← NEW
2. [Komponen Core](#2-komponen-core)
   - 2.1 **Core Services** (Auth, RBAC, Notification, Audit, etc.) ← NEW
   - 2.2 **Core Infrastructure** (Events, Registry, Slots, Router) ← NEW
   - 2.3 Event Bus
   - 2.4 Module Registry
   - 2.5 Slot Registry
   - 2.6 Slot Component
3. [Module Structure](#3-module-structure)
4. [Hooks System](#4-hooks-system)
5. [Slots System](#5-slots-system)
6. [Runtime Management](#6-runtime-management)
7. [Database Schema](#7-database-schema)
8. [API Contracts](#8-api-contracts)
9. [Best Practices](#9-best-practices)
10. [Examples](#10-examples)

---

## 1. Konsep Dasar

### 1.1 Apa itu Puzzle Architecture?

**Puzzle Architecture** adalah pendekatan arsitektur dimana aplikasi dibangun dari modul-modul independen (puzzle pieces) yang dapat:
- **Ditambahkan** tanpa mengubah core system
- **Dihapus** tanpa merusak fitur lain
- **Diperbaiki** secara terisolasi
- **Dikombinasikan** sesuai kebutuhan tenant

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        PUZZLE-LIKE ARCHITECTURE                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │                         CORE SYSTEM (Minimal)                        │  ║
║  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐   │  ║
║  │  │  Auth   │ │ Routing │ │ Events  │ │Registry │ │  UI Slots   │   │  ║
║  │  │ Service │ │  Engine │ │   Bus   │ │ Manager │ │   System    │   │  ║
║  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘   │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                    │                                       ║
║                    ┌───────────────┼───────────────┐                      ║
║                    │               │               │                      ║
║                    ▼               ▼               ▼                      ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       ║
║  │  MODULE  │ │  MODULE  │ │  MODULE  │ │  MODULE  │ │  MODULE  │       ║
║  │   PMS    │ │   POS    │ │   HRM    │ │Membership│ │Analytics │       ║
║  │          │ │          │ │          │ │          │ │          │       ║
║  │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │       ║
║  │ │Routes│ │ │ │Routes│ │ │ │Routes│ │ │ │Routes│ │ │ │Routes│ │       ║
║  │ │Hooks │ │ │ │Hooks │ │ │ │Hooks │ │ │ │Hooks │ │ │ │Hooks │ │       ║
║  │ │Slots │ │ │ │Slots │ │ │ │Slots │ │ │ │Slots │ │ │ │Slots │ │       ║
║  │ │  UI  │ │ │ │  UI  │ │ │ │  UI  │ │ │  UI  │ │ │ │  UI  │ │       ║
║  │ │ API  │ │ │ │ API  │ │ │ │ API  │ │ │ │ API  │ │ │ │ API  │ │       ║
║  │ └──────┘ │ │ └──────┘ │ │ └──────┘ │ │ └──────┘ │ │ └──────┘ │       ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       ║
║       🧩           🧩           🧩           🧩           🧩             ║
║   (Puzzle Piece)                                                          ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### 1.2 Prinsip Utama

| Prinsip | Deskripsi |
|---------|-----------|
| **Minimal Core** | Core hanya berisi orchestration, bukan business logic |
| **Coarse-Grained Modules** | Satu aplikasi = satu module (PMS, POS, HRM) |
| **Runtime Toggle** | Tenant bisa enable/disable module dari UI |
| **Extension Points** | Predefined hooks dan slots untuk module attach |
| **Bounded Context** | Setiap module = 1 domain, komunikasi via events |

### 1.3 Kenapa Modular Monolith (Bukan Microservices)?

| Aspect | Microservices | Modular Monolith |
|--------|---------------|------------------|
| Complexity | Tinggi (distributed) | Medium |
| Communication | Network (latency) | In-process (cepat) |
| Data Consistency | Eventual | ACID |
| Deployment | Per-service | Single unit |
| Team Size Needed | Besar | Kecil-Medium |
| Migration Path | - | Easy → Microservices later |

> **Best Practice**: Start with a well-designed modular monolith. This enables teams to develop a thorough understanding of the domain, define precise boundaries, and delay expensive distributed system costs until necessary.

### 1.4 Arsitektur 4-Layer

Platform ini menggunakan arsitektur 4-layer yang jelas:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         ARSITEKTUR 4-LAYER                                 ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 1: CORE SERVICES (Centralized Business Services)             │  ║
║  │  ──────────────────────────────────────────────────────────────     │  ║
║  │  Services dengan DATABASE dan API yang SEMUA module butuhkan        │  ║
║  │                                                                      │  ║
║  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │  ║
║  │  │  Auth  │ │  RBAC  │ │ Notif  │ │ Audit  │ │ Search │            │  ║
║  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │  ║
║  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │  ║
║  │  │ Files  │ │  User  │ │  Org   │ │ Config │ │ i18n   │            │  ║
║  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                    │                                       ║
║                        Provides APIs & Events                             ║
║                                    │                                       ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 2: CORE INFRASTRUCTURE (Orchestration)                       │  ║
║  │  ──────────────────────────────────────────────────────────────     │  ║
║  │  Infrastructure TANPA database, hanya orchestrate system            │  ║
║  │                                                                      │  ║
║  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │  ║
║  │  │ Events │ │Registry│ │ Slots  │ │ Router │ │Middlewr│            │  ║
║  │  │  Bus   │ │        │ │        │ │        │ │        │            │  ║
║  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                    │                                       ║
║                          Import & Use                                      ║
║                                    │                                       ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 3: SHARED UTILITIES (Pure Functions, No State)               │  ║
║  │  ──────────────────────────────────────────────────────────────     │  ║
║  │  Code yang BISA di-copy paste tanpa side effects                    │  ║
║  │                                                                      │  ║
║  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │  ║
║  │  │  UI    │ │ Format │ │Validate│ │ Types  │ │Constant│            │  ║
║  │  │Compnts │ │  Utils │ │  Utils │ │        │ │        │            │  ║
║  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                    │                                       ║
║                          Business Logic                                    ║
║                                    │                                       ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 4: MODULES (Business Domains - Puzzle Pieces)                │  ║
║  │  ──────────────────────────────────────────────────────────────     │  ║
║  │  Domain-specific business logic, dapat di-enable/disable            │  ║
║  │                                                                      │  ║
║  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │  ║
║  │  │  PMS   │ │  POS   │ │  HRM   │ │Account │ │Inventory            │  ║
║  │  │   🧩   │ │   🧩   │ │   🧩   │ │   🧩   │ │   🧩   │            │  ║
║  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

#### Perbedaan Antar Layer

| Layer | Punya Database? | Punya API? | Punya State? | Contoh |
|-------|-----------------|------------|--------------|--------|
| **Core Services** | ✅ Ya | ✅ Ya | ✅ Ya | Auth, Notification, Audit, Search, Files |
| **Core Infrastructure** | ❌ Tidak | ❌ Tidak | ✅ Ya (in-memory) | Event Bus, Module Registry, Slots |
| **Shared Utilities** | ❌ Tidak | ❌ Tidak | ❌ Tidak | formatDate(), Button component |
| **Modules** | ✅ Ya | ✅ Ya | ✅ Ya | PMS, POS, HRM, Accounting |

#### Aturan Dependency

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DEPENDENCY RULES                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Module → dapat menggunakan → Core Services ✅                           │
│  Module → dapat menggunakan → Core Infrastructure ✅                     │
│  Module → dapat menggunakan → Shared Utilities ✅                        │
│  Module → TIDAK BOLEH langsung → Module lain ❌                          │
│                                                                          │
│  Core Services → dapat menggunakan → Core Infrastructure ✅              │
│  Core Services → dapat menggunakan → Shared Utilities ✅                 │
│  Core Services → TIDAK BOLEH → Modules ❌                                │
│                                                                          │
│  Shared Utilities → HANYA pure functions, tidak import apapun ✅         │
│                                                                          │
│  Cross-Module Communication → via Events/Hooks SAJA ✅                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Komponen Core

Core terdiri dari 2 bagian: **Core Services** dan **Core Infrastructure**.

### 2.1 Core Services (Centralized Business Services)

Core Services adalah business services dengan database dan API yang **SEMUA module butuhkan**:

```
core/
├── services/                       # Centralized Business Services
│   │
│   ├── auth/                       # Authentication Service
│   │   ├── models.py               # users, sessions, tokens tables
│   │   ├── routes.py               # /auth/login, /auth/logout, /auth/refresh
│   │   ├── repositories/
│   │   ├── use_cases/
│   │   └── events.py               # auth.login, auth.logout, auth.token_refresh
│   │
│   ├── rbac/                       # Authorization Service
│   │   ├── models.py               # roles, permissions, user_roles tables
│   │   ├── routes.py               # /roles, /permissions
│   │   ├── decorators.py           # @require_permission()
│   │   └── events.py               # rbac.role_assigned, rbac.permission_granted
│   │
│   ├── organization/               # Organization/Tenant Service
│   │   ├── models.py               # organizations, memberships tables
│   │   ├── routes.py               # /organizations, /memberships
│   │   └── events.py               # org.created, org.member_added
│   │
│   ├── user/                       # User Management Service
│   │   ├── models.py               # user profiles, preferences
│   │   ├── routes.py               # /users, /profile
│   │   └── events.py               # user.created, user.updated, user.deleted
│   │
│   ├── notification/               # Notification Service
│   │   ├── models.py               # notifications, templates, preferences tables
│   │   ├── routes.py               # /notifications
│   │   ├── channels/               # in_app, push, email handlers
│   │   └── events.py               # notification.sent, notification.read
│   │
│   ├── audit/                      # Audit Logging Service
│   │   ├── models.py               # audit_logs table
│   │   ├── routes.py               # /audit-logs (read only)
│   │   ├── middleware.py           # Auto-capture all actions
│   │   └── handlers.py             # Listens to ALL events
│   │
│   ├── files/                      # File Management Service
│   │   ├── models.py               # files, file_references tables
│   │   ├── routes.py               # /files/upload, /files/download
│   │   ├── storage/                # R2, S3 adapters
│   │   └── events.py               # file.uploaded, file.deleted
│   │
│   ├── search/                     # Search Service
│   │   ├── routes.py               # /search
│   │   ├── indexer.py              # Meilisearch integration
│   │   └── handlers.py             # Listens to entity changes for indexing
│   │
│   └── config/                     # Configuration Service
│       ├── models.py               # system_settings, org_settings tables
│       ├── routes.py               # /settings
│       └── feature_flags.py        # Feature flag management
│
└── ...
```

**Karakteristik Core Services:**
- ✅ Punya database tables sendiri
- ✅ Punya API endpoints sendiri
- ✅ Publish dan subscribe events
- ✅ Digunakan oleh SEMUA modules
- ❌ TIDAK boleh import dari modules

### 2.2 Core Infrastructure (Orchestration)

Core Infrastructure adalah komponen orchestration **TANPA database**:

```
core/
├── events/                     # Event Bus
│   ├── EventBus.ts
│   ├── types.ts
│   └── hooks.ts
├── registry/                   # Module Registry
│   ├── ModuleRegistry.ts
│   ├── types.ts
│   └── loader.ts
├── slots/                      # UI Slot System
│   ├── SlotRegistry.ts
│   ├── Slot.tsx
│   └── types.ts
├── router/                     # Dynamic Route Registry
│   ├── DynamicRouter.ts
│   └── ModuleRoutes.tsx
├── middleware/                 # Core Middleware
│   ├── auth.py                 # JWT validation
│   ├── tenant.py               # Multi-tenant context
│   ├── rate_limit.py           # Rate limiting
│   └── security_headers.py     # Security headers
└── config/
    └── modules.config.ts
```

**Karakteristik Core Infrastructure:**
- ❌ TIDAK punya database tables
- ❌ TIDAK punya API endpoints
- ✅ In-memory state (registries, caches)
- ✅ Orchestrate modules dan services
- ✅ Provide extension points (hooks, slots)

### 2.3 Event Bus

Central event system untuk komunikasi antar module:

```typescript
// core/events/EventBus.ts
type HookHandler = {
  callback: (...args: any[]) => any;
  priority: number;
};

class EventBus {
  private hooks: Map<string, HookHandler[]> = new Map();

  /**
   * Action: Fire and forget
   * Semua handler dipanggil, tidak ada return value
   */
  async doAction(hookName: string, ...args: any[]): Promise<void> {
    const handlers = this.hooks.get(hookName) || [];
    const sorted = handlers.sort((a, b) => a.priority - b.priority);

    for (const handler of sorted) {
      await handler.callback(...args);
    }
  }

  /**
   * Filter: Transform data through chain
   * Data melewati semua handler dan ditransformasi
   */
  async applyFilters<T>(hookName: string, value: T, ...args: any[]): Promise<T> {
    const handlers = this.hooks.get(hookName) || [];
    const sorted = handlers.sort((a, b) => a.priority - b.priority);

    let result = value;
    for (const handler of sorted) {
      result = await handler.callback(result, ...args);
    }
    return result;
  }

  /**
   * Register hook handler
   */
  addHook(hookName: string, callback: Function, priority = 10): void {
    if (!this.hooks.has(hookName)) {
      this.hooks.set(hookName, []);
    }
    this.hooks.get(hookName)!.push({ callback, priority });
  }

  /**
   * Remove hook handler
   */
  removeHook(hookName: string, callback: Function): void {
    const handlers = this.hooks.get(hookName);
    if (handlers) {
      const index = handlers.findIndex(h => h.callback === callback);
      if (index > -1) handlers.splice(index, 1);
    }
  }
}

export const eventBus = new EventBus();
```

### 2.4 Module Registry

Central registry untuk manage modules:

```typescript
// core/registry/ModuleRegistry.ts
import { eventBus } from '../events/EventBus';
import { slotRegistry } from '../slots/SlotRegistry';
import { router } from '../router/DynamicRouter';

export interface ModuleManifest {
  id: string;
  name: string;
  version: string;

  // Core version compatibility
  coreVersion: string;

  // Dependencies
  dependencies: string[];

  // Routes
  routes: RouteConfig[];

  // Hook subscriptions
  hooks: Record<string, Function>;

  // UI slot contributions
  slots: Record<string, React.ComponentType>;

  // Permissions required
  permissions: string[];

  // Lifecycle hooks
  onEnable?: () => Promise<void>;
  onDisable?: () => Promise<void>;
}

class ModuleRegistry {
  private modules: Map<string, ModuleManifest> = new Map();
  private enabledModules: Set<string> = new Set();

  /**
   * Register module (saat app boot)
   */
  register(module: ModuleManifest): void {
    // Validate dependencies
    for (const dep of module.dependencies) {
      if (!this.modules.has(dep)) {
        console.warn(`Module ${module.id} requires ${dep} which is not registered`);
      }
    }

    this.modules.set(module.id, module);
    console.log(`[ModuleRegistry] Registered: ${module.id} v${module.version}`);
  }

  /**
   * Enable module untuk tenant
   */
  async enable(moduleId: string): Promise<void> {
    const module = this.modules.get(moduleId);
    if (!module) {
      throw new Error(`Module ${moduleId} not found`);
    }

    // Check dependencies enabled
    for (const dep of module.dependencies) {
      if (!this.enabledModules.has(dep)) {
        throw new Error(`Cannot enable ${moduleId}: dependency ${dep} is not enabled`);
      }
    }

    // Register routes
    module.routes.forEach(route => router.addRoute(route));

    // Subscribe to hooks
    Object.entries(module.hooks).forEach(([hookName, handler]) => {
      eventBus.addHook(hookName, handler);
    });

    // Register slot content
    Object.entries(module.slots).forEach(([slotName, component]) => {
      slotRegistry.addContent(slotName, component, module.id);
    });

    // Run lifecycle hook
    if (module.onEnable) {
      await module.onEnable();
    }

    this.enabledModules.add(moduleId);
    console.log(`[ModuleRegistry] Enabled: ${moduleId}`);
  }

  /**
   * Disable module untuk tenant
   */
  async disable(moduleId: string): Promise<void> {
    const module = this.modules.get(moduleId);
    if (!module) return;

    // Check if other modules depend on this
    for (const [id, mod] of this.modules) {
      if (this.enabledModules.has(id) && mod.dependencies.includes(moduleId)) {
        throw new Error(`Cannot disable ${moduleId}: ${id} depends on it`);
      }
    }

    // Remove routes
    module.routes.forEach(route => router.removeRoute(route.path));

    // Unsubscribe from hooks
    Object.entries(module.hooks).forEach(([hookName, handler]) => {
      eventBus.removeHook(hookName, handler);
    });

    // Remove slot content
    slotRegistry.removeByModule(moduleId);

    // Run lifecycle hook
    if (module.onDisable) {
      await module.onDisable();
    }

    this.enabledModules.delete(moduleId);
    console.log(`[ModuleRegistry] Disabled: ${moduleId}`);
  }

  /**
   * Check if module is enabled
   */
  isEnabled(moduleId: string): boolean {
    return this.enabledModules.has(moduleId);
  }

  /**
   * Get all registered modules
   */
  getAll(): ModuleManifest[] {
    return Array.from(this.modules.values());
  }

  /**
   * Get enabled modules
   */
  getEnabled(): ModuleManifest[] {
    return Array.from(this.modules.values())
      .filter(m => this.enabledModules.has(m.id));
  }
}

export const moduleRegistry = new ModuleRegistry();
```

### 2.5 Slot Registry

UI injection point system:

```typescript
// core/slots/SlotRegistry.ts
import React from 'react';

interface SlotContent {
  component: React.ComponentType<any>;
  moduleId: string;
  priority: number;
}

class SlotRegistry {
  private slots: Map<string, SlotContent[]> = new Map();

  /**
   * Add content to slot
   */
  addContent(
    slotName: string,
    component: React.ComponentType<any>,
    moduleId: string,
    priority = 10
  ): void {
    if (!this.slots.has(slotName)) {
      this.slots.set(slotName, []);
    }
    this.slots.get(slotName)!.push({ component, moduleId, priority });
  }

  /**
   * Get slot content (sorted by priority)
   */
  getContent(slotName: string): React.ComponentType<any>[] {
    const contents = this.slots.get(slotName) || [];
    return contents
      .sort((a, b) => a.priority - b.priority)
      .map(c => c.component);
  }

  /**
   * Remove all content from specific module
   */
  removeByModule(moduleId: string): void {
    for (const [slotName, contents] of this.slots) {
      this.slots.set(
        slotName,
        contents.filter(c => c.moduleId !== moduleId)
      );
    }
  }
}

export const slotRegistry = new SlotRegistry();
```

### 2.6 Slot Component

React component untuk render slot content:

```tsx
// core/slots/Slot.tsx
import React from 'react';
import { slotRegistry } from './SlotRegistry';

interface SlotProps {
  name: string;
  children?: React.ReactNode;
  [key: string]: any;
}

export function Slot({ name, children, ...props }: SlotProps) {
  const slotContent = slotRegistry.getContent(name);

  return (
    <>
      {/* Default content */}
      {children}

      {/* Injected content from modules */}
      {slotContent.map((Component, index) => (
        <Component key={`${name}-${index}`} {...props} />
      ))}
    </>
  );
}

// Usage in layout
function Sidebar() {
  return (
    <nav>
      <Slot name="sidebar.menu.top" />
      <DefaultMenuItems />
      <Slot name="sidebar.menu.bottom" />
    </nav>
  );
}
```

---

## 3. Module Structure

### 3.1 Directory Structure

Setiap module mengikuti struktur standar:

```
modules/
├── pms/                            # Hotel Operations Module
│   ├── manifest.ts                 # Module declaration
│   ├── index.ts                    # Entry point & exports
│   │
│   ├── backend/                    # Python backend
│   │   ├── __init__.py
│   │   ├── manifest.py             # Backend manifest
│   │   ├── router.py               # FastAPI routes
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── reservation.py
│   │   │   └── room.py
│   │   ├── repositories/           # Data access
│   │   │   ├── __init__.py
│   │   │   └── reservation_repo.py
│   │   ├── use_cases/              # Business logic
│   │   │   ├── __init__.py
│   │   │   └── create_reservation.py
│   │   ├── events/                 # Event handlers
│   │   │   ├── __init__.py
│   │   │   └── handlers.py
│   │   └── migrations/             # Module-specific migrations
│   │       └── 001_pms_tables.sql
│   │
│   └── frontend/                   # React frontend
│       ├── routes.tsx              # Module routes
│       ├── hooks/                  # Hook subscriptions
│       │   ├── index.ts
│       │   └── useReservation.ts
│       ├── slots/                  # UI slot contributions
│       │   ├── index.ts
│       │   ├── SidebarMenu.tsx
│       │   └── DashboardWidget.tsx
│       ├── components/             # Module components
│       │   ├── ReservationList.tsx
│       │   └── RoomCalendar.tsx
│       ├── api/                    # API client
│       │   └── pmsApi.ts
│       └── stores/                 # Module state
│           └── reservationStore.ts
│
├── pos/                            # Point of Sale Module
│   └── ... (same structure)
│
├── hrm/                            # HR Management Module
│   └── ... (same structure)
│
├── membership/                     # Membership/Loyalty Module
│   └── ... (same structure)
│
└── analytics/                      # Analytics Module
    └── ... (same structure)
```

### 3.2 Module Manifest (Frontend)

```typescript
// modules/pms/manifest.ts
import { ModuleManifest } from '@/core/registry/types';
import { pmsRoutes } from './frontend/routes';
import * as hooks from './frontend/hooks';
import * as slots from './frontend/slots';

export const PMSModule: ModuleManifest = {
  id: 'pms',
  name: 'Hotel Operations (PMS)',
  version: '1.0.0',
  coreVersion: '^1.0.0',

  // Module dependencies
  dependencies: ['auth', 'users'],

  // Routes contributed by this module
  routes: pmsRoutes,

  // Hook subscriptions
  hooks: {
    // Actions (fire events)
    'user.login': hooks.onUserLogin,
    'dashboard.render': hooks.onDashboardRender,

    // Filters (transform data)
    'user.profile.data': hooks.addRoomAssignment,
    'report.generate': hooks.addPMSMetrics,
  },

  // UI slots filled by this module
  slots: {
    'sidebar.menu': slots.PMSSidebarMenu,
    'dashboard.widgets': slots.PMSDashboardWidget,
    'user.profile.tabs': slots.GuestHistoryTab,
  },

  // Permissions required
  permissions: [
    'pms.view',
    'pms.reservations.create',
    'pms.reservations.manage',
    'pms.rooms.manage',
    'pms.reports.view',
  ],

  // Lifecycle hooks
  async onEnable() {
    console.log('[PMS] Module enabled, initializing...');
    // Initialize module-specific resources
  },

  async onDisable() {
    console.log('[PMS] Module disabled, cleaning up...');
    // Cleanup module resources
  },
};
```

### 3.3 Module Manifest (Backend)

```python
# modules/pms/backend/manifest.py
from dataclasses import dataclass, field
from typing import Dict, Callable, List
from fastapi import APIRouter

@dataclass
class BackendModuleManifest:
    id: str
    name: str
    version: str
    router: APIRouter
    event_handlers: Dict[str, Callable] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

# modules/pms/backend/__init__.py
from .manifest import BackendModuleManifest
from .router import pms_router
from .events.handlers import on_user_created, on_checkout_calculate

pms_module = BackendModuleManifest(
    id="pms",
    name="Hotel Operations (PMS)",
    version="1.0.0",
    router=pms_router,
    event_handlers={
        "user.created": on_user_created,
        "checkout.calculate": on_checkout_calculate,
    },
    dependencies=["auth", "users"],
    permissions=[
        "pms.view",
        "pms.reservations.create",
        "pms.reservations.manage",
        "pms.rooms.manage",
        "pms.reports.view",
    ],
)
```

### 3.4 Module Registration

```typescript
// App.tsx atau main entry point
import { moduleRegistry } from '@/core/registry/ModuleRegistry';

// Import all available modules
import { PMSModule } from '@/modules/pms/manifest';
import { POSModule } from '@/modules/pos/manifest';
import { HRMModule } from '@/modules/hrm/manifest';
import { MembershipModule } from '@/modules/membership/manifest';

// Register all modules (saat app boot)
moduleRegistry.register(PMSModule);
moduleRegistry.register(POSModule);
moduleRegistry.register(HRMModule);
moduleRegistry.register(MembershipModule);

// Enable modules based on tenant config
async function initializeTenantModules(tenantId: string) {
  const enabledModules = await fetchTenantModules(tenantId);

  for (const moduleId of enabledModules) {
    await moduleRegistry.enable(moduleId);
  }
}
```

---

## 4. Hooks System

### 4.1 Dua Jenis Hook

#### Actions (Do Something)

Actions adalah hook yang **melakukan sesuatu** tanpa mengembalikan nilai. Cocok untuk side effects seperti logging, notifications, atau analytics.

```
┌──────────────────────────────────────────────────────────────┐
│  Core: eventBus.doAction('user.created', user)               │
│                                                              │
│  Plugins listening:                                          │
│  ├── Email Module    → Send welcome email                    │
│  ├── Analytics       → Track signup event                    │
│  ├── Notification    → Notify admin                          │
│  └── Membership      → Create initial membership             │
└──────────────────────────────────────────────────────────────┘
```

**Usage:**

```typescript
// Firing action
await eventBus.doAction('user.created', { id: 1, name: 'John' });

// Subscribing to action
eventBus.addHook('user.created', async (user) => {
  await sendWelcomeEmail(user.email);
});
```

#### Filters (Transform Data)

Filters adalah hook yang **mentransformasi data**. Data melewati chain handler dan masing-masing bisa memodifikasi.

```
┌──────────────────────────────────────────────────────────────┐
│  Core: eventBus.applyFilters('user.profile.data', userData)  │
│         Input: { name: "John", role: "user" }                │
│                                                              │
│  Plugins processing (by priority):                           │
│  ├── RBAC Module     → Add permissions array                 │
│  ├── Profile Module  → Add avatar URL                        │
│  └── Membership      → Add tier info                         │
│                                                              │
│  Final Output:                                               │
│  { name: "John", role: "user", permissions: [...],           │
│    avatar: "...", tier: "gold" }                             │
└──────────────────────────────────────────────────────────────┘
```

**Usage:**

```typescript
// Applying filter
const enrichedUser = await eventBus.applyFilters('user.profile.data', user);

// Subscribing to filter (MUST return modified data)
eventBus.addHook('user.profile.data', async (user) => {
  return {
    ...user,
    membershipTier: await getMembershipTier(user.id),
  };
});
```

### 4.2 Hook Naming Conventions

| Pattern | Description | Examples |
|---------|-------------|----------|
| `entity.action` | Entity lifecycle events | `user.created`, `order.placed` |
| `entity.action.data` | Data transformation | `user.profile.data`, `invoice.total.data` |
| `context.render` | UI rendering hooks | `dashboard.render`, `sidebar.render` |
| `context.action.before` | Before action | `checkout.submit.before` |
| `context.action.after` | After action | `checkout.submit.after` |

### 4.3 Predefined Core Hooks

```typescript
// core/events/coreHooks.ts
export const CORE_HOOKS = {
  // === User Lifecycle ===
  'user.created': 'Fired when user is created',
  'user.updated': 'Fired when user is updated',
  'user.deleted': 'Fired when user is deleted',

  // === Auth Lifecycle ===
  'auth.login': 'Fired on successful login',
  'auth.logout': 'Fired on logout',
  'auth.token.refresh': 'Fired when token is refreshed',

  // === Data Transformation ===
  'user.profile.data': 'Filter user profile data',
  'dashboard.widgets.data': 'Filter dashboard widgets list',
  'sidebar.menu.data': 'Filter sidebar menu items',
  'report.data': 'Filter report data before render',

  // === UI Rendering ===
  'dashboard.render': 'Called when dashboard renders',
  'settings.render': 'Called when settings page renders',

  // === Business Events ===
  'checkout.total.calculate': 'Filter checkout total calculation',
  'invoice.generate.before': 'Called before invoice generation',
  'invoice.generate.after': 'Called after invoice generation',
} as const;
```

### 4.4 Hook Priority

Priority menentukan urutan eksekusi (lower = earlier):

```typescript
// Default priority = 10

eventBus.addHook('user.profile.data', addBasicInfo, 5);    // Runs first
eventBus.addHook('user.profile.data', addPermissions, 10); // Runs second
eventBus.addHook('user.profile.data', addAnalytics, 20);   // Runs last
```

---

## 5. Slots System

### 5.1 Konsep UI Slots

UI Slots adalah titik-titik injeksi yang sudah didefinisikan di layout, dimana module bisa menyisipkan komponen mereka.

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER                                                      │
│  ┌─────────────────┐                    ┌─────────────────┐ │
│  │ Slot: header.   │                    │ Slot: header.   │ │
│  │ left            │                    │ right           │ │
│  └─────────────────┘                    └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ SIDEBAR    │  MAIN CONTENT                                  │
│            │                                                 │
│ ┌────────┐ │  ┌─────────────────────────────────────────┐  │
│ │ Slot:  │ │  │ Slot: content.header                    │  │
│ │sidebar.│ │  └─────────────────────────────────────────┘  │
│ │menu.top│ │                                                │
│ └────────┘ │  ┌─────────────────────────────────────────┐  │
│            │  │                                          │  │
│ [Default   │  │  Page Content                            │  │
│  Menu      │  │                                          │  │
│  Items]    │  └─────────────────────────────────────────┘  │
│            │                                                │
│ ┌────────┐ │  ┌─────────────────────────────────────────┐  │
│ │ Slot:  │ │  │ Slot: content.footer                    │  │
│ │sidebar.│ │  └─────────────────────────────────────────┘  │
│ │menu.   │ │                                                │
│ │bottom  │ │                                                │
│ └────────┘ │                                                │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Predefined Core Slots

```typescript
// core/slots/coreSlots.ts
export const CORE_SLOTS = {
  // === Layout Slots ===
  'layout.header.left': 'Left side of header',
  'layout.header.right': 'Right side of header',
  'layout.sidebar.top': 'Top of sidebar',
  'layout.sidebar.bottom': 'Bottom of sidebar',
  'layout.footer.left': 'Left side of footer',
  'layout.footer.right': 'Right side of footer',

  // === Dashboard Slots ===
  'dashboard.widgets': 'Dashboard widget area',
  'dashboard.quick-actions': 'Quick action buttons',
  'dashboard.stats': 'Statistics cards area',

  // === User Profile Slots ===
  'user.profile.header': 'User profile header area',
  'user.profile.tabs': 'User profile tab area',
  'user.profile.badges': 'User badges area',
  'user.profile.actions': 'User action buttons',

  // === Settings Slots ===
  'settings.tabs': 'Settings tab area',
  'settings.sections': 'Settings section area',

  // === Navigation Slots ===
  'sidebar.menu': 'Sidebar menu items',
  'topnav.actions': 'Top navigation action buttons',
} as const;
```

### 5.3 Using Slots in Layout

```tsx
// layouts/MainLayout.tsx
import { Slot } from '@/core/slots/Slot';

export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="layout">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <Logo />
          <Slot name="layout.header.left" />
        </div>
        <div className="header-right">
          <Slot name="layout.header.right" />
          <UserMenu />
        </div>
      </header>

      <div className="layout-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <Slot name="layout.sidebar.top" />
          <nav className="sidebar-menu">
            <Slot name="sidebar.menu" />
          </nav>
          <Slot name="layout.sidebar.bottom" />
        </aside>

        {/* Main Content */}
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}
```

### 5.4 Module Contributing to Slots

```tsx
// modules/pms/frontend/slots/SidebarMenu.tsx
import { NavLink } from 'react-router-dom';

export function PMSSidebarMenu() {
  return (
    <>
      <NavLink to="/pms/reservations" className="menu-item">
        <CalendarIcon />
        <span>Reservations</span>
      </NavLink>
      <NavLink to="/pms/rooms" className="menu-item">
        <BedIcon />
        <span>Rooms</span>
      </NavLink>
      <NavLink to="/pms/guests" className="menu-item">
        <UsersIcon />
        <span>Guests</span>
      </NavLink>
    </>
  );
}

// modules/pms/frontend/slots/DashboardWidget.tsx
export function PMSDashboardWidget() {
  const { data: stats } = usePMSStats();

  return (
    <div className="dashboard-widget">
      <h3>PMS Overview</h3>
      <div className="stats-grid">
        <StatCard label="Check-ins Today" value={stats?.checkIns} />
        <StatCard label="Check-outs Today" value={stats?.checkOuts} />
        <StatCard label="Occupancy Rate" value={`${stats?.occupancy}%`} />
      </div>
    </div>
  );
}

// modules/pms/frontend/slots/index.ts
export { PMSSidebarMenu } from './SidebarMenu';
export { PMSDashboardWidget } from './DashboardWidget';
```

---

## 6. Runtime Management

### 6.1 Tenant Module Configuration

Tenant bisa enable/disable module dari admin panel:

```
┌─────────────────────────────────────────────────────────────┐
│                      TENANT DASHBOARD                        │
│  "Enable/Disable modules dari sini"                         │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Available Modules                                        ││
│  │                                                          ││
│  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐       ││
│  │ │ PMS │ │ POS │ │ HRM │ │Memb.│ │Acct.│ │Analy│       ││
│  │ │ ✅  │ │ ✅  │ │ ❌  │ │ ✅  │ │ ❌  │ │ ✅  │       ││
│  │ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘       ││
│  │                                                          ││
│  │ [Enabled: 4]  [Disabled: 2]  [Total: 6]                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Frontend Dynamic Loading

```typescript
// hooks/useModuleLoader.ts
import { useEffect, useState } from 'react';
import { moduleRegistry } from '@/core/registry/ModuleRegistry';
import { useAuth } from '@/features/auth/hooks/useAuth';

export function useModuleLoader() {
  const { tenant } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function loadModules() {
      if (!tenant?.id) return;

      try {
        setLoading(true);

        // Fetch tenant's enabled modules from API
        const response = await fetch(`/api/v1/tenant/modules`);
        const { enabled } = await response.json();

        // Enable each module
        for (const moduleId of enabled) {
          if (!moduleRegistry.isEnabled(moduleId)) {
            await moduleRegistry.enable(moduleId);
          }
        }

        setLoading(false);
      } catch (err) {
        setError(err as Error);
        setLoading(false);
      }
    }

    loadModules();
  }, [tenant?.id]);

  return { loading, error };
}
```

### 6.3 Module Toggle Component

```tsx
// components/ModuleToggle.tsx
import { Switch } from '@/components/ui/switch';
import { moduleRegistry } from '@/core/registry/ModuleRegistry';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface ModuleToggleProps {
  moduleId: string;
  moduleName: string;
  isEnabled: boolean;
}

export function ModuleToggle({ moduleId, moduleName, isEnabled }: ModuleToggleProps) {
  const queryClient = useQueryClient();

  const toggleMutation = useMutation({
    mutationFn: async (enable: boolean) => {
      const endpoint = enable
        ? `/api/v1/tenant/modules/${moduleId}/enable`
        : `/api/v1/tenant/modules/${moduleId}/disable`;

      const response = await fetch(endpoint, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to toggle module');

      // Update local registry
      if (enable) {
        await moduleRegistry.enable(moduleId);
      } else {
        await moduleRegistry.disable(moduleId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant', 'modules'] });
    },
  });

  return (
    <div className="module-toggle">
      <span>{moduleName}</span>
      <Switch
        checked={isEnabled}
        onCheckedChange={(checked) => toggleMutation.mutate(checked)}
        disabled={toggleMutation.isPending}
      />
    </div>
  );
}
```

---

## 7. Database Schema

### 7.1 Tenant Modules Table

```sql
-- Migration: XXX_create_tenant_modules.sql
-- Description: Track which modules are enabled for each tenant

BEGIN;

CREATE TABLE tenant_modules (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Foreign keys
    tenant_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Module info
    module_id VARCHAR(50) NOT NULL,

    -- Status
    is_enabled BOOLEAN DEFAULT FALSE NOT NULL,

    -- Configuration (module-specific settings)
    config JSONB DEFAULT '{}' NOT NULL,

    -- Timestamps
    enabled_at TIMESTAMP WITH TIME ZONE,
    disabled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    -- Audit trail
    enabled_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    disabled_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    UNIQUE(tenant_id, module_id)
);

-- Indexes
CREATE INDEX idx_tenant_modules_tenant ON tenant_modules(tenant_id);
CREATE INDEX idx_tenant_modules_enabled ON tenant_modules(is_enabled) WHERE is_enabled = TRUE;

-- Comments
COMMENT ON TABLE tenant_modules IS 'Track enabled modules per tenant';
COMMENT ON COLUMN tenant_modules.config IS 'Module-specific configuration as JSON';

COMMIT;
```

### 7.2 Available Modules Table

```sql
-- Migration: XXX_create_available_modules.sql
-- Description: Registry of available modules in the system

BEGIN;

CREATE TABLE available_modules (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Module identity
    module_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,

    -- Module metadata
    icon VARCHAR(50),
    category VARCHAR(50),

    -- Dependencies (array of module_ids)
    dependencies TEXT[] DEFAULT '{}',

    -- Permissions required
    permissions TEXT[] DEFAULT '{}',

    -- Pricing (for future marketplace)
    is_free BOOLEAN DEFAULT TRUE NOT NULL,
    price_monthly DECIMAL(10, 2),
    price_yearly DECIMAL(10, 2),

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_beta BOOLEAN DEFAULT FALSE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Seed default modules
INSERT INTO available_modules (module_id, name, description, version, category, dependencies, is_free) VALUES
('pms', 'Hotel Operations (PMS)', 'Front desk, reservations, room management', '1.0.0', 'hospitality', '{}', TRUE),
('pos', 'Point of Sale', 'F&B operations, billing, inventory', '1.0.0', 'sales', '{}', TRUE),
('hrm', 'Human Resources', 'Employee management, attendance, payroll', '1.0.0', 'hr', '{}', TRUE),
('membership', 'Membership & Loyalty', 'Guest loyalty program, tiers, points', '1.0.0', 'crm', '{}', TRUE),
('accounting', 'Accounting', 'General ledger, financial reporting', '1.0.0', 'finance', '{}', TRUE),
('analytics', 'Analytics & Reports', 'Business intelligence, dashboards', '1.0.0', 'reporting', '{}', TRUE);

COMMIT;
```

### 7.3 Module Database Tables Pattern

Setiap module memiliki tabel dengan prefix module:

```sql
-- modules/pms/backend/migrations/001_pms_tables.sql

BEGIN;

-- PMS: Rooms
CREATE TABLE pms_rooms (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    room_type_id INTEGER NOT NULL,
    floor INTEGER,
    status VARCHAR(20) DEFAULT 'available' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, room_number)
);

-- PMS: Reservations
CREATE TABLE pms_reservations (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    room_id INTEGER NOT NULL REFERENCES pms_rooms(id),
    guest_id INTEGER NOT NULL REFERENCES users(id),
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed' NOT NULL,
    total_amount DECIMAL(12, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_pms_rooms_org ON pms_rooms(organization_id);
CREATE INDEX idx_pms_reservations_dates ON pms_reservations(check_in_date, check_out_date);

COMMIT;
```

---

## 8. API Contracts

### 8.1 Module Management Endpoints

```yaml
# Platform Admin APIs (untuk manage available modules)
GET    /api/v1/platform/modules              # List all available modules
POST   /api/v1/platform/modules              # Add new module
PATCH  /api/v1/platform/modules/{id}         # Update module info
DELETE /api/v1/platform/modules/{id}         # Remove module

# Tenant APIs (untuk manage enabled modules per tenant)
GET    /api/v1/tenant/modules                # List tenant's modules with status
POST   /api/v1/tenant/modules/{id}/enable    # Enable module for tenant
POST   /api/v1/tenant/modules/{id}/disable   # Disable module for tenant
PATCH  /api/v1/tenant/modules/{id}/config    # Update module config
```

### 8.2 API Responses

```typescript
// GET /api/v1/tenant/modules
interface TenantModulesResponse {
  data: {
    enabled: ModuleInfo[];
    disabled: ModuleInfo[];
  };
}

interface ModuleInfo {
  id: string;
  name: string;
  description: string;
  version: string;
  icon: string;
  category: string;
  isEnabled: boolean;
  enabledAt?: string;
  config?: Record<string, any>;
  dependencies: string[];
}

// POST /api/v1/tenant/modules/{id}/enable
interface EnableModuleResponse {
  success: boolean;
  message: string;
  data: {
    moduleId: string;
    enabledAt: string;
  };
}
```

### 8.3 Backend Implementation

```python
# backend-python/services/modules/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user
from .repositories import ModuleRepository
from .use_cases import EnableModuleUseCase, DisableModuleUseCase

router = APIRouter(prefix="/tenant/modules", tags=["Modules"])

@router.get("")
async def list_tenant_modules(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all modules with their enabled status for current tenant"""
    repo = ModuleRepository(db)
    modules = repo.get_tenant_modules(current_user.organization_id)

    enabled = [m for m in modules if m.is_enabled]
    disabled = [m for m in modules if not m.is_enabled]

    return {
        "data": {
            "enabled": [m.to_dict() for m in enabled],
            "disabled": [m.to_dict() for m in disabled]
        }
    }

@router.post("/{module_id}/enable")
async def enable_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Enable a module for current tenant"""
    use_case = EnableModuleUseCase(db)
    result = use_case.execute(
        module_id=module_id,
        tenant_id=current_user.organization_id,
        enabled_by_id=current_user.id
    )

    return {
        "success": True,
        "message": f"Module {module_id} enabled successfully",
        "data": result
    }

@router.post("/{module_id}/disable")
async def disable_module(
    module_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Disable a module for current tenant"""
    use_case = DisableModuleUseCase(db)
    result = use_case.execute(
        module_id=module_id,
        tenant_id=current_user.organization_id,
        disabled_by_id=current_user.id
    )

    return {
        "success": True,
        "message": f"Module {module_id} disabled successfully",
        "data": result
    }
```

---

## 9. Best Practices

### 9.1 Do's

| # | Practice | Description |
|---|----------|-------------|
| 1 | **Keep Core Minimal** | Core hanya orchestration, BUKAN business logic |
| 2 | **Isolate Module State** | Setiap module punya store sendiri |
| 3 | **Use Events for Cross-Module** | Komunikasi via events, bukan direct import |
| 4 | **Version Your Modules** | Semver untuk compatibility tracking |
| 5 | **Document Extension Points** | Hooks dan slots harus terdokumentasi |
| 6 | **Test in Isolation** | Module bisa di-test tanpa module lain |
| 7 | **Handle Missing Dependencies** | Graceful degradation jika dependency disabled |

### 9.2 Don'ts

| # | Anti-Pattern | Why |
|---|--------------|-----|
| 1 | **Direct Module Import** | Breaks isolation, tight coupling |
| 2 | **Shared Mutable State** | Race conditions, unpredictable behavior |
| 3 | **Core Business Logic** | Core harus tetap generic |
| 4 | **Circular Dependencies** | A depends on B depends on A |
| 5 | **Skip Manifest Declaration** | Routes/hooks tidak terdaftar dengan benar |
| 6 | **Ignore Priority** | Hook order matters untuk filters |

### 9.3 Module Checklist

Sebelum module dianggap production-ready:

```
□ Manifest lengkap (id, name, version, dependencies)
□ Routes terdaftar
□ Hooks terdokumentasi
□ Slots terdokumentasi
□ Permissions defined
□ Lifecycle hooks (onEnable, onDisable)
□ Unit tests untuk business logic
□ Integration tests untuk hooks
□ Migration files untuk database
□ API documentation
□ README.md untuk module
```

### 9.4 Sebelum Buat Fitur Baru

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  ⚠️  SEBELUM BUAT FITUR BARU, TANYA:                                      ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  □ Apakah ini bisa jadi module terpisah?                                  ║
║  □ Apa extension points yang dibutuhkan?                                  ║
║  □ Module mana yang perlu subscribe ke event ini?                         ║
║  □ UI slot mana yang perlu di-fill?                                       ║
║  □ Apakah ada dependency ke module lain?                                  ║
║  □ Apakah ini fitur core atau module-specific?                            ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## 10. Examples

### 10.1 Complete Module Example: Membership

```typescript
// modules/membership/manifest.ts
import { ModuleManifest } from '@/core/registry/types';

export const MembershipModule: ModuleManifest = {
  id: 'membership',
  name: 'Membership & Loyalty',
  version: '1.0.0',
  coreVersion: '^1.0.0',

  dependencies: ['auth', 'users'],

  routes: [
    { path: '/membership', component: () => import('./pages/MembershipDashboard') },
    { path: '/membership/tiers', component: () => import('./pages/TierManagement') },
    { path: '/membership/members', component: () => import('./pages/MemberList') },
  ],

  hooks: {
    // Add membership badge to user profile
    'user.profile.data': async (user) => ({
      ...user,
      membershipTier: await getMembershipTier(user.id),
      loyaltyPoints: await getLoyaltyPoints(user.id),
    }),

    // Apply member discount to checkout
    'checkout.total.calculate': async (total, { userId }) => {
      const discount = await getMemberDiscount(userId);
      return total * (1 - discount);
    },

    // Grant points on purchase
    'order.completed': async (order) => {
      await grantLoyaltyPoints(order.userId, order.total);
    },
  },

  slots: {
    'sidebar.menu': () => import('./slots/SidebarMenu'),
    'dashboard.widgets': () => import('./slots/LoyaltyWidget'),
    'user.profile.badges': () => import('./slots/MembershipBadge'),
    'checkout.summary': () => import('./slots/DiscountDisplay'),
  },

  permissions: [
    'membership.view',
    'membership.manage',
    'membership.tiers.manage',
    'membership.points.grant',
  ],
};
```

### 10.2 Hook Implementation Example

```typescript
// modules/membership/hooks/useCheckoutDiscount.ts
import { eventBus } from '@/core/events/EventBus';
import { getMemberDiscount } from '../api/membershipApi';

// Register the hook
eventBus.addHook(
  'checkout.total.calculate',
  async (total: number, context: { userId: number }) => {
    try {
      const discount = await getMemberDiscount(context.userId);
      const discountedTotal = total * (1 - discount);

      console.log(`[Membership] Applied ${discount * 100}% discount`);
      return discountedTotal;
    } catch (error) {
      // Graceful degradation - return original total if discount fails
      console.error('[Membership] Failed to apply discount:', error);
      return total;
    }
  },
  15 // Priority: after base calculation (10), before tax (20)
);
```

### 10.3 Slot Implementation Example

```tsx
// modules/membership/slots/MembershipBadge.tsx
import { useMembershipTier } from '../hooks/useMembershipTier';
import { Badge } from '@/components/ui/badge';

interface MembershipBadgeProps {
  userId: number;
}

export function MembershipBadge({ userId }: MembershipBadgeProps) {
  const { data: tier, isLoading } = useMembershipTier(userId);

  if (isLoading || !tier) return null;

  const tierColors = {
    bronze: 'bg-amber-600',
    silver: 'bg-gray-400',
    gold: 'bg-yellow-500',
    platinum: 'bg-purple-600',
  };

  return (
    <Badge className={tierColors[tier.level]}>
      {tier.name}
    </Badge>
  );
}

export default MembershipBadge;
```

### 10.4 Cross-Module Communication Example

```typescript
// modules/pos/hooks/orderCompleteHandler.ts
import { eventBus } from '@/core/events/EventBus';

// POS fires event when order is completed
async function completeOrder(order: Order) {
  // ... process order ...

  // Fire event for other modules to react
  await eventBus.doAction('order.completed', {
    orderId: order.id,
    userId: order.userId,
    total: order.total,
    items: order.items,
  });
}

// modules/membership/hooks/orderHandler.ts
// Membership listens and grants points
eventBus.addHook('order.completed', async (order) => {
  const pointsEarned = calculatePoints(order.total);
  await grantPoints(order.userId, pointsEarned);

  // Notify user
  await eventBus.doAction('notification.send', {
    userId: order.userId,
    type: 'points_earned',
    message: `You earned ${pointsEarned} loyalty points!`,
  });
});

// modules/analytics/hooks/orderHandler.ts
// Analytics listens and tracks
eventBus.addHook('order.completed', async (order) => {
  await trackEvent('order_completed', {
    value: order.total,
    items_count: order.items.length,
  });
});
```

---

## Summary

### Key Benefits

| Benefit | Description |
|---------|-------------|
| ✅ **Tenant Flexibility** | Enable/disable modules dari UI tanpa redeploy |
| ✅ **Developer Isolation** | Develop module independently, bug terisolasi |
| ✅ **Easy Testing** | Test module in isolation |
| ✅ **Future Marketplace** | Ready untuk third-party plugins |
| ✅ **Coarse-Grained** | Simpler mental model (1 app = 1 module) |
| ✅ **Gradual Migration** | Bisa migrate ke microservices later |

### Implementation Checklist

| Phase | Tasks |
|-------|-------|
| **Phase 1** | Implement core system (EventBus, Registry, Slots) |
| **Phase 2** | Create module template structure |
| **Phase 3** | Migrate existing features to modules |
| **Phase 4** | Implement runtime toggle UI |
| **Phase 5** | Document all extension points |

### Architecture Decision Records

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Modular Monolith over Microservices | Simpler ops, ACID transactions, faster iteration |
| ADR-002 | Coarse-grained modules | 1 app = 1 module for simpler mental model |
| ADR-003 | Runtime enable/disable | Tenant flexibility tanpa redeploy |
| ADR-004 | WordPress-style hooks | Proven pattern, familiar to developers |
| ADR-005 | React slots for UI injection | Clean separation, no component prop drilling |

---

## References

- [Plugin Architecture Best Practices (ArjanCodes)](https://arjancodes.com/blog/best-practices-for-decoupling-software-using-plugins/)
- [Modular Monolith + DDD (The Reformed Programmer)](https://www.thereformedprogrammer.net/my-experience-of-using-modular-monolith-and-ddd-architectures/)
- [WordPress Hooks Handbook](https://developer.wordpress.org/plugins/hooks/)
- [Facebook iOS Plugin Architecture](https://engineering.fb.com/2023/02/06/ios/facebook-ios-app-architecture/)
- [Composable Architecture (MACH)](https://www.contentstack.com/cms-guides/what-is-composable-architecture)
- [Feature-Based Architecture in React](https://dev.to/naserrasouli/scalable-react-projects-with-feature-based-architecture-117c)

---

*Last Updated: 2025-12-09*
