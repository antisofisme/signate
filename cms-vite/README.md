# CMS Vite - Digital Signage Admin Dashboard

## Architecture

Admin dashboard untuk mengelola content, devices, dan organizations menggunakan **Vite + React** dengan **Clean Architecture**.

**Platform:**
- Web (Browser - Modern Chrome, Firefox, Safari, Edge)

## Tech Stack Decisions

### ✅ Framework & Build Tool
- **Vite** 5+ (bukan Next.js/CRA)
- **React** 18+
- **TypeScript** untuk type safety

**Kenapa Vite?**
- ✅ **Faster dev server** - Lightning fast HMR
- ✅ **Simpler architecture** - No Node.js server runtime
- ✅ **Static build** - Deploy anywhere (Nginx, Apache, S3, Vercel)
- ✅ **Smaller bundle** - Tree-shaking by default
- ✅ **Perfect fit** - CMS tidak perlu SSR/SEO
- ✅ **Backend terpisah** - FastAPI sudah handle semua API

**Kenapa BUKAN Next.js?**
- ❌ **Overkill** - SSR/Server Components tidak terpakai
- ❌ **API Routes tidak perlu** - Semua API di FastAPI
- ❌ **Deploy complexity** - Perlu Node.js server
- ❌ **Larger bundle** - Next.js runtime overhead

### ✅ Routing
- **React Router v6** (bukan App Router)

**Kenapa React Router?**
- ✅ Client-side routing (cukup untuk SPA)
- ✅ Mature & stable
- ✅ Nested routes & layouts
- ✅ Protected routes (auth guards)

### ✅ State Management
- **React Query** (@tanstack/react-query) - Server state & API data
- **Zustand** - Client/UI state & auth
- **React Hook Form** - Form state

**Pembagian State:**
| State Type | Tool | Example |
|------------|------|---------|
| Server data (API) | React Query | Devices, content, playlists |
| UI state | Zustand | Sidebar open/close, theme, modals |
| Auth | Zustand (persisted) | User, token, organizations |
| Forms | React Hook Form | Add device, upload content |

**Kenapa React Query?**
- ✅ Auto caching & background refetch
- ✅ Loading/error states built-in
- ✅ Optimistic updates
- ✅ DevTools untuk debugging

**Kenapa Zustand?**
- ✅ Simple API (no boilerplate)
- ✅ Small bundle size
- ✅ Persistence built-in
- ✅ No Context hell

### ✅ UI & Theming
- **Shadcn UI** - Component library (headless, customizable)
- **Tailwind CSS** - Utility-first CSS
- **Lucide React** - Icons (from Shadcn UI)
- **Dark Mode** - Light/Dark theme switching
- **i18n** - Multi-language (i18next)
  - Bahasa Indonesia (default)
  - English

**Kenapa Shadcn UI?**
- ✅ Copy-paste components (no node_modules bloat)
- ✅ Fully customizable
- ✅ Accessible by default (Radix UI)
- ✅ Tailwind-based (consistent styling)

### ✅ API Integration
- **Axios** - HTTP client (dengan interceptors)

**Kenapa Axios?**
- ✅ Interceptors untuk auth token
- ✅ Request/response transformation
- ✅ Better error handling
- ✅ Progress tracking (upload files)

### ✅ Environment Config
- **Vite env variables** (.env files)

**Format:**
```env
VITE_API_URL=http://192.168.5.12:8001
VITE_API_VERSION=v1
VITE_APP_NAME="Digital Signage CMS"
```

---

## Structure (Modular + Clean + Centralized Architecture)

**Architecture:** Modular (feature-based) + Clean Architecture (layered) + Centralized (shared code)

See `README_STRUCTURE.md` for detailed architecture explanation.

```
cms-vite/
├── .env.example               # Environment template
├── package.json
├── tsconfig.json
├── vite.config.ts             # Vite configuration
├── tailwind.config.ts
├── index.html                 # Entry point (Vite)
├── README_STRUCTURE.md        # 📘 Architecture guide (Modular + Clean + Centralized)
├── src/
│   ├── main.tsx              # ⚡ React entry point
│   ├── App.tsx               # 🎯 Root component + Router
│   ├── routes/               # 🌐 ROUTING (React Router)
│   │   ├── index.tsx         # Route definitions
│   │   ├── ProtectedRoute.tsx
│   │   └── AuthLayout.tsx
│   ├── pages/                # 📄 PAGE COMPONENTS (thin, compose features)
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── dashboard/
│   │   │   └── DashboardPage.tsx
│   │   ├── devices/
│   │   │   ├── DevicesPage.tsx
│   │   │   └── DeviceDetailPage.tsx
│   │   ├── content/
│   │   │   ├── ContentPage.tsx
│   │   │   └── UploadPage.tsx
│   │   ├── playlists/
│   │   │   └── PlaylistsPage.tsx
│   │   ├── users/
│   │   │   └── UsersPage.tsx
│   │   ├── settings/
│   │   │   └── SettingsPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── features/             # 🎯 BUSINESS LOGIC (per feature/domain)
│   │   ├── auth/
│   │   │   ├── components/        # Feature-specific components
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   └── OrgSelector.tsx
│   │   │   ├── hooks/             # React Query + custom hooks
│   │   │   │   ├── useAuth.ts
│   │   │   │   └── useAuthStore.ts
│   │   │   ├── services/          # API calls (feature-specific)
│   │   │   │   └── authApi.ts
│   │   │   └── types/
│   │   │       └── auth.ts
│   │   ├── devices/
│   │   │   ├── components/
│   │   │   │   ├── DeviceTable.tsx
│   │   │   │   ├── DeviceModal.tsx
│   │   │   │   ├── DeviceActions.tsx
│   │   │   │   └── DeviceStatusBadge.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useDevices.ts
│   │   │   │   └── useDeviceActions.ts
│   │   │   ├── services/
│   │   │   │   └── deviceApi.ts
│   │   │   └── types/
│   │   │       └── device.ts
│   │   ├── content/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── playlists/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── users/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types/
│   │   └── dashboard/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── services/
│   ├── shared/               # 🧩 SHARED/GENERIC COMPONENTS (domain-agnostic)
│   │   └── components/
│   │       ├── ui/          # Shadcn UI primitives
│   │       │   ├── button.tsx
│   │       │   ├── card.tsx
│   │       │   ├── input.tsx
│   │       │   ├── table.tsx
│   │       │   ├── dialog.tsx
│   │       │   └── ...
│   │       ├── layout/      # App layout components
│   │       │   ├── Sidebar.tsx
│   │       │   ├── Topbar.tsx
│   │       │   ├── DashboardLayout.tsx
│   │       │   └── AuthLayout.tsx
│   │       └── common/      # Generic reusable components
│   │           ├── Button.tsx
│   │           ├── LoadingSpinner.tsx
│   │           ├── ErrorBoundary.tsx
│   │           ├── EmptyState.tsx
│   │           ├── ThemeSwitcher.tsx
│   │           └── LanguageSwitcher.tsx
│   ├── lib/                 # 📦 CENTRALIZED UTILITIES (stable patterns)
│   │   ├── errors/          # Error handling
│   │   │   ├── apiErrors.ts        # Error types & classes
│   │   │   ├── errorMessages.ts    # Error messages (Indonesian)
│   │   │   └── errorHandler.ts     # Error handling logic
│   │   ├── api/             # HTTP client & API
│   │   │   ├── client.ts           # Axios instance + interceptors
│   │   │   ├── endpoints.ts        # API route definitions
│   │   │   ├── responseTypes.ts    # Response type definitions
│   │   │   └── interceptors.ts     # Request/response interceptors
│   │   ├── validation/      # Validation utilities
│   │   │   └── schemas.ts          # Validation rules
│   │   ├── constants/       # App-wide constants
│   │   │   └── app.ts              # Constants (roles, limits, formats)
│   │   ├── notifications/   # Toast notifications
│   │   │   └── toast.ts            # Toast manager & useToast hook
│   │   ├── auth/            # Auth utilities
│   │   │   └── permissions.ts      # RBAC (role-based access control)
│   │   ├── stores/          # Zustand stores (global state)
│   │   │   ├── authStore.ts        # Auth state (user, token, org)
│   │   │   └── uiStore.ts          # UI state (sidebar, theme, modals)
│   │   ├── hooks/           # Shared hooks
│   │   │   ├── useDebounce.ts
│   │   │   └── useLocalStorage.ts
│   │   └── utils/           # General utilities
│   │       ├── cn.ts               # Tailwind class merger
│   │       └── dateTime.ts         # Date/time formatting
│   ├── styles/
│   │   └── globals.css            # Tailwind + theme variables
│   └── i18n/                # 🌐 TRANSLATIONS
│       ├── config.ts
│       ├── locales/
│       │   ├── id.json           # Bahasa Indonesia
│       │   └── en.json           # English
│       └── useTranslation.ts
├── public/                   # Static assets
│   ├── images/
│   └── fonts/
└── dist/                     # Build output (static files)
```

**Key Principles:**
- **Modular**: Code organized by feature/domain (not by type)
- **Clean Architecture**: Clear separation of concerns (UI → Business → Infrastructure)
- **Centralized**: Reusable code in `shared/` and `lib/` for consistency

**Path depth:** Max 5 levels (`src/features/devices/components/DeviceTable.tsx`)

---

## API Client (Centralized)

### File: `lib/api/client.ts`

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001';
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth-token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    const orgId = localStorage.getItem('selected-org-id');
    if (orgId) {
      config.headers['X-Organization-Id'] = orgId;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### File: `lib/api/endpoints.ts`

```typescript
/**
 * API Endpoints - Single Source of Truth
 * ⚠️ CENTRALIZED - semua endpoints di sini
 */

const API_V1 = '/api/v1';

export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    LOGIN: `${API_V1}/auth/login`,
    REGISTER: `${API_V1}/auth/register`,
    LOGOUT: `${API_V1}/auth/logout`,
    ME: `${API_V1}/auth/me`,
  },

  // Organizations
  ORGANIZATIONS: {
    LIST: `${API_V1}/organizations`,
    GET: (id: number) => `${API_V1}/organizations/${id}`,
    CREATE: `${API_V1}/organizations`,
    UPDATE: (id: number) => `${API_V1}/organizations/${id}`,
    DELETE: (id: number) => `${API_V1}/organizations/${id}`,
  },

  // Devices
  DEVICES: {
    LIST: `${API_V1}/devices`,
    GET: (id: number) => `${API_V1}/devices/${id}`,
    ACTIVATE: `${API_V1}/devices/activate`,
    UPDATE: (id: number) => `${API_V1}/devices/${id}`,
    DELETE: (id: number) => `${API_V1}/devices/${id}`,
    HEARTBEAT: (code: string) => `${API_V1}/devices/${code}/heartbeat`,
  },

  // Content
  CONTENT: {
    LIST: `${API_V1}/content`,
    GET: (id: number) => `${API_V1}/content/${id}`,
    UPLOAD: `${API_V1}/content/upload`,
    UPDATE: (id: number) => `${API_V1}/content/${id}`,
    DELETE: (id: number) => `${API_V1}/content/${id}`,
  },

  // Playlists
  PLAYLISTS: {
    LIST: `${API_V1}/playlists`,
    GET: (id: number) => `${API_V1}/playlists/${id}`,
    CREATE: `${API_V1}/playlists`,
    UPDATE: (id: number) => `${API_V1}/playlists/${id}`,
    DELETE: (id: number) => `${API_V1}/playlists/${id}`,
    ASSIGN_DEVICE: (id: number) => `${API_V1}/playlists/${id}/assign`,
  },

  // Users
  USERS: {
    LIST: `${API_V1}/users`,
    GET: (id: number) => `${API_V1}/users/${id}`,
    CREATE: `${API_V1}/users`,
    UPDATE: (id: number) => `${API_V1}/users/${id}`,
    DELETE: (id: number) => `${API_V1}/users/${id}`,
  },

  // Analytics
  ANALYTICS: {
    DASHBOARD: `${API_V1}/analytics/dashboard`,
    DEVICE_LOGS: (deviceId: number) => `${API_V1}/analytics/devices/${deviceId}/logs`,
    CONTENT_STATS: `${API_V1}/analytics/content/stats`,
  },
} as const;
```

---

## State Management Examples

### Auth Store (Zustand)

```typescript
// lib/stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
}

export interface Organization {
  id: number;
  name: string;
  pin: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  organizations: Organization[];
  selectedOrgId: number | null;

  setAuth: (user: User, token: string, organizations: Organization[]) => void;
  selectOrganization: (orgId: number) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      organizations: [],
      selectedOrgId: null,

      setAuth: (user, token, organizations) =>
        set({
          user,
          token,
          organizations,
          selectedOrgId: organizations.length === 1 ? organizations[0].id : null,
        }),

      selectOrganization: (orgId) => set({ selectedOrgId: orgId }),

      logout: () =>
        set({
          user: null,
          token: null,
          organizations: [],
          selectedOrgId: null,
        }),
    }),
    { name: 'auth-storage' }
  )
);
```

### UI Store (Zustand)

```typescript
// lib/stores/uiStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Language = 'id' | 'en';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: Language;
  currentModal: string | null;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setLanguage: (language: Language) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      language: 'id',
      currentModal: null,

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
      openModal: (modalId) => set({ currentModal: modalId }),
      closeModal: () => set({ currentModal: null }),
    }),
    { name: 'ui-preferences' }
  )
);
```

### React Query Hook Example

```typescript
// features/devices/hooks/useDevices.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deviceApi } from '../services/deviceApi';

export function useDevices() {
  return useQuery({
    queryKey: ['devices'],
    queryFn: deviceApi.getAll,
    staleTime: 30000, // 30 seconds
  });
}

export function useDeviceActions() {
  const queryClient = useQueryClient();

  const activateMutation = useMutation({
    mutationFn: deviceApi.activate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deviceApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  return {
    activate: activateMutation.mutate,
    delete: deleteMutation.mutate,
    isActivating: activateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
```

---

## Routing (React Router v6)

### File: `routes/index.tsx`

```typescript
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';

// Pages
import LoginPage from '@/pages/auth/LoginPage';
import DashboardPage from '@/pages/dashboard/DashboardPage';
import DevicesPage from '@/pages/devices/DevicesPage';
import ContentPage from '@/pages/content/ContentPage';
// ... other imports

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    element: (
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'devices', element: <DevicesPage /> },
      { path: 'content', element: <ContentPage /> },
      { path: 'playlists', element: <PlaylistsPage /> },
      { path: 'users', element: <UsersPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
]);
```

---

## Multi-Tenant Authentication Flow

**Strategy:** Single domain + Organization selector

### Flow:
1. User login → Backend returns `{ user, token, organizations[] }`
2. Frontend stores in `authStore` (Zustand)
3. **If 1 organization** → Auto-select, redirect to dashboard
4. **If >1 organizations** → Show organization selector
5. All API calls include `X-Organization-Id` header
6. Backend filters data by organization

### Implementation:
```typescript
// features/auth/hooks/useAuth.ts
const login = async (username: string, password: string) => {
  const response = await authApi.login(username, password);
  const { user, token, organizations } = response.data;

  // Save to Zustand store (persisted to localStorage)
  useAuthStore.getState().setAuth(user, token, organizations);

  // Auto-select if only 1 org
  if (organizations.length === 1) {
    useAuthStore.getState().selectOrganization(organizations[0].id);
    navigate('/dashboard');
  } else {
    navigate('/select-organization');
  }
};
```

---

## Development

```bash
# Install dependencies
npm install

# Run dev server (port 3000)
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Build & Deployment

### Build Output:
```bash
npm run build

# Output: dist/
# ├── index.html
# ├── assets/
# │   ├── index-[hash].js
# │   └── index-[hash].css
# └── ...
```

### Deployment Options:

#### 1. **Nginx (Production Server)**
```nginx
server {
  listen 3000;
  server_name 192.168.5.12;

  root /home/gzjbbk/prototipe2/cms-vite/dist;
  index index.html;

  # SPA fallback - all routes return index.html
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Cache static assets
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
```

#### 2. **Vercel / Netlify**
```bash
# Just connect Git repo, auto-deploy
# Build command: npm run build
# Output directory: dist
```

#### 3. **Docker**
```dockerfile
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## Environment Variables

### `.env.example`
```env
# Backend API Configuration
VITE_API_URL=http://192.168.5.12:8001
VITE_API_VERSION=v1

# Application Configuration
VITE_APP_NAME="Digital Signage CMS"
VITE_DEFAULT_LANGUAGE=id

# Feature Flags
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_ANALYTICS=false
```

### Usage in code:
```typescript
const apiUrl = import.meta.env.VITE_API_URL;
const appName = import.meta.env.VITE_APP_NAME;
```

---

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "@tanstack/react-query": "^5.51.1",
    "zustand": "^4.5.4",
    "axios": "^1.7.2",
    "react-hook-form": "^7.52.1",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.23.8",
    "lucide-react": "^0.408.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.4.0",
    "i18next": "^23.11.5",
    "react-i18next": "^14.1.2"
  },
  "devDependencies": {
    "vite": "^5.3.3",
    "typescript": "^5.5.3",
    "@vitejs/plugin-react": "^4.3.1",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.39",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0"
  }
}
```

---

## Key Decisions Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Build Tool | **Vite** (bukan Next.js) | Faster, simpler, no SSR overhead |
| Routing | **React Router v6** | Client-side routing cukup |
| State - Server | **React Query** | Caching, background refetch, optimistic updates |
| State - UI | **Zustand** | Simple, no boilerplate, persist-ready |
| State - Forms | **React Hook Form** | Performance, easy validation |
| UI Components | **Shadcn UI** | Customizable, accessible, Tailwind-based |
| Styling | **Tailwind CSS** | Utility-first, fast development |
| API Client | **Axios** | Interceptors, progress tracking |
| i18n | **i18next** | Mature, flexible |
| Multi-tenant | **Single domain + org selector** | Simpler than subdomain |
| Deployment | **Static files** | Nginx/Vercel/Netlify |

---

## Comparison: Vite vs Next.js

| Aspect | Vite + React | Next.js 15 |
|--------|--------------|------------|
| **Dev Server** | ⚡ Lightning fast | Fast |
| **Build Output** | Static files | Node.js server + static |
| **Bundle Size** | Smaller | Larger (Next runtime) |
| **SSR/SEO** | ❌ No (tidak perlu) | ✅ Yes (tidak terpakai) |
| **API Routes** | ❌ No (sudah ada FastAPI) | ✅ Yes (tidak terpakai) |
| **Server Components** | ❌ No (tidak perlu) | ✅ Yes (tidak terpakai) |
| **Deployment** | Any static host | Vercel/Node.js server |
| **Learning Curve** | Lower | Higher |
| **Use Case** | **Perfect for SPA CMS** | Better for marketing sites |

**Conclusion:** Vite + React adalah pilihan tepat untuk CMS digital signage karena tidak perlu SSR/SEO, backend sudah terpisah (FastAPI), dan lebih simple untuk deploy & maintain.

---

## Next Steps

1. ✅ Install dependencies: `npm install`
2. ✅ Setup Shadcn UI: `npx shadcn-ui@latest init`
3. ✅ Add components: `npx shadcn-ui@latest add button card input table dialog`
4. ✅ Implement auth feature (login, register, org selector)
5. ✅ Implement dashboard with device management
6. ✅ Implement content upload & playlist builder
7. ✅ Build & deploy to production

**Ready to start development!** 🚀
