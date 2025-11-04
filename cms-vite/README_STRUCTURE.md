# CMS Vite - Modular + Clean Architecture + Centralized (Shared)

## Architecture Principles

This project follows **3 core principles**:

1. **Modular**: Code organized by feature/domain (not by type)
2. **Clean Architecture**: Separation of concerns with clear dependencies
3. **Centralized (Shared)**: Reusable code centralized in `shared/` and `lib/`

## Folder Structure

```
cms-vite/
├── src/
│   ├── features/              # 🎯 MODULAR - Self-contained features
│   │   ├── auth/              # Authentication feature
│   │   │   ├── components/    # Auth-specific UI
│   │   │   ├── hooks/         # useAuth, useLogin
│   │   │   ├── services/      # authApi.ts
│   │   │   └── types/         # auth.ts
│   │   │
│   │   └── devices/           # Device management feature
│   │       ├── components/    # Device-specific UI
│   │       │   ├── DeviceTable.tsx
│   │       │   ├── ActivateDeviceModal.tsx
│   │       │   └── DeviceStatusBadge.tsx
│   │       ├── hooks/         # useDevices, useActivateDevice
│   │       ├── services/      # deviceApi.ts
│   │       └── types/         # device.ts
│   │
│   ├── shared/                # 🔄 CENTRALIZED - Reusable across features
│   │   └── components/        # Generic UI (no business logic)
│   │       ├── common/
│   │       │   ├── Button.tsx        # Generic button
│   │       │   ├── Modal.tsx
│   │       │   ├── Card.tsx
│   │       │   ├── ThemeSwitcher.tsx
│   │       │   └── LanguageSwitcher.tsx
│   │       └── layout/
│   │           ├── DashboardLayout.tsx
│   │           ├── Sidebar.tsx
│   │           └── Topbar.tsx
│   │
│   ├── lib/                   # 🔧 CENTRALIZED - Non-visual utilities
│   │   ├── api/
│   │   │   ├── client.ts      # Axios instance
│   │   │   └── endpoints.ts   # API routes
│   │   ├── stores/
│   │   │   ├── authStore.ts   # Zustand - Global auth state
│   │   │   └── uiStore.ts     # Zustand - UI preferences
│   │   └── utils/
│   │       ├── cn.ts          # Tailwind class merger
│   │       └── helpers.ts     # Helper functions
│   │
│   ├── pages/                 # 📄 Page compositions (thin layer)
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── DevicesPage.tsx
│   │   └── SelectOrganizationPage.tsx
│   │
│   ├── routes/                # 🌐 Routing configuration
│   │   ├── ProtectedRoute.tsx
│   │   └── index.tsx
│   │
│   ├── i18n/                  # 🌍 Internationalization
│   │   ├── index.ts
│   │   └── locales/
│   │       ├── id.json        # Indonesian
│   │       └── en.json        # English
│   │
│   ├── styles/                # 💅 Global styles
│   │   └── globals.css
│   │
│   ├── App.tsx                # Root component
│   └── main.tsx               # Entry point
```

## Decision Matrix: Where to Put Components?

| Component | Ask | Location |
|-----------|-----|----------|
| `Button` | Does it know about "device" or "auth" domain? | ❌ No → `shared/components/common/` |
| `ThemeSwitcher` | Does it know about business logic? | ❌ No → `shared/components/common/` |
| `DashboardLayout` | Is it specific to one feature? | ❌ No → `shared/components/layout/` |
| `DeviceTable` | Does it know about device domain? | ✅ Yes → `features/devices/components/` |
| `LoginForm` | Does it know about auth domain? | ✅ Yes → `features/auth/components/` |

## Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER (UI)                                    │
│  - pages/ (thin orchestration)                              │
│  - shared/components/ (generic UI)                          │
│  - features/*/components/ (domain-specific UI)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER (Business Logic)                         │
│  - features/*/hooks/ (React Query + business logic)         │
│  - lib/stores/ (Zustand - global state)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER (Data Access)                         │
│  - features/*/services/ (API calls)                         │
│  - lib/api/ (HTTP client, endpoints)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  DOMAIN LAYER (Business Entities)                           │
│  - features/*/types/ (TypeScript interfaces)                │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. Modular (Features)

**Self-contained feature modules:**
- Each feature owns its business logic, UI, API calls, and types
- Can be extracted into microservice/microfrontend
- Example: `features/devices/` knows everything about device management

### 2. Centralized (Shared)

**Generic reusable code:**
- `shared/components/` - UI components with NO business logic
- `lib/` - Infrastructure code (API client, state, utils)
- Can be used across ALL features

### 3. Clean Architecture

**Dependency Rule:**
```
Outer layers depend on inner layers (not vice versa)

UI → Business Logic → Data Access → Domain
```

## Import Patterns

```typescript
// ✅ CORRECT - Feature imports
import { DeviceTable } from '@/features/devices/components/DeviceTable'
import { useDevices } from '@/features/devices/hooks/useDevices'
import { deviceApi } from '@/features/devices/services/deviceApi'

// ✅ CORRECT - Shared imports
import { Button } from '@/shared/components/common/Button'
import { DashboardLayout } from '@/shared/components/layout/DashboardLayout'
import { ThemeSwitcher } from '@/shared/components/common/ThemeSwitcher'

// ✅ CORRECT - Lib imports
import { apiClient } from '@/lib/api/client'
import { useAuthStore } from '@/lib/stores/authStore'
import { cn } from '@/lib/utils/cn'

// ❌ WRONG - Don't import across features
// features/devices/ should NOT import from features/auth/
import { LoginForm } from '@/features/auth/components/LoginForm' // ❌
```

## Benefits

### Scalability
- Add new features without touching existing code
- Features can be split into separate repositories

### Maintainability
- Clear boundaries between features
- Easy to find code: "Where is device table?" → `features/devices/components/`

### Reusability
- Shared components used everywhere: `shared/components/`
- Infrastructure reused across features: `lib/`

### Testability
- Features isolated → easy to test independently
- Mock shared dependencies

## Example: Adding New Feature

To add "Content Management" feature:

```bash
# 1. Create feature structure
features/content/
├── components/       # ContentGrid, UploadModal
├── hooks/           # useContent, useUpload
├── services/        # contentApi.ts
└── types/           # content.ts

# 2. Create page
pages/ContentPage.tsx

# 3. Add route
routes/index.tsx

# 4. Reuse shared components
import { Button } from '@/shared/components/common/Button'
import { DashboardLayout } from '@/shared/components/layout/DashboardLayout'
```

## Comparison with Other Structures

| Structure | Features | Shared | Lib |
|-----------|----------|--------|-----|
| **Type-based** (OLD) | ❌ components/, hooks/, services/ mixed | N/A | N/A |
| **Our Structure** (NEW) | ✅ features/devices/, features/auth/ | ✅ shared/components/ | ✅ lib/ |

## Migration from Old Structure

If you have:
```
components/devices/  → Move to features/devices/components/
hooks/useDevices.ts  → Move to features/devices/hooks/
services/deviceApi   → Move to features/devices/services/
```

Generic components:
```
components/Button    → Move to shared/components/common/
components/Sidebar   → Move to shared/components/layout/
```

## Summary

**WHERE TO PUT CODE:**

| Code Type | Location | Reason |
|-----------|----------|--------|
| Device-specific UI | `features/devices/components/` | Domain-specific |
| Auth-specific hooks | `features/auth/hooks/` | Domain-specific |
| Generic Button | `shared/components/common/` | Reusable across features |
| API Client | `lib/api/client.ts` | Infrastructure |
| Auth Store | `lib/stores/authStore.ts` | Global state |
| Page | `pages/DevicesPage.tsx` | Thin orchestration |

**REMEMBER:**
- ✅ Feature-specific → `features/`
- ✅ Generic/Reusable → `shared/` or `lib/`
- ✅ Pages = thin orchestration
- ❌ Never mix feature business logic in `shared/`
