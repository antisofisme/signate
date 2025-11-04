# CMS Vite - Clean Architecture (Max 3 Levels)

## Folder Structure

```
cms-vite/
├── src/
│   ├── components/           # 🎨 LAYER 1: UI Components (max 3 levels)
│   │   ├── ui/              # Shadcn UI
│   │   ├── layout/          # Sidebar, Topbar, DashboardLayout
│   │   ├── auth/            # LoginForm, RegisterForm, OrgSelector
│   │   ├── devices/         # DeviceTable, DeviceModal ← 3 levels ✅
│   │   ├── content/         # ContentGrid, UploadModal
│   │   ├── playlists/       # PlaylistBuilder, PlaylistItem
│   │   └── common/          # LoadingSpinner, ErrorBoundary
│   │
│   ├── pages/               # 📄 LAYER 1: Route Pages (max 2 levels)
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── DevicesPage.tsx
│   │   ├── ContentPage.tsx
│   │   ├── PlaylistsPage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── hooks/               # 🎯 LAYER 2: Business Logic (max 2 levels)
│   │   ├── useAuth.ts       # Auth hooks (React Query)
│   │   ├── useDevices.ts    # Device hooks
│   │   ├── useContent.ts    # Content hooks
│   │   └── usePlaylists.ts  # Playlist hooks
│   │
│   ├── stores/              # 🎯 LAYER 2: State Management (max 2 levels)
│   │   ├── authStore.ts     # Zustand - Auth (user, token, org)
│   │   └── uiStore.ts       # Zustand - UI (sidebar, theme, modals)
│   │
│   ├── services/            # 📡 LAYER 3: API Calls (max 2 levels)
│   │   ├── authApi.ts       # Auth API
│   │   ├── deviceApi.ts     # Device API
│   │   ├── contentApi.ts    # Content API
│   │   └── playlistApi.ts   # Playlist API
│   │
│   ├── types/               # 🏛️ LAYER 4: Domain Models (max 2 levels)
│   │   ├── auth.ts          # User, Organization
│   │   ├── device.ts        # Device
│   │   ├── content.ts       # Content
│   │   └── playlist.ts      # Playlist
│   │
│   ├── lib/                 # 🔧 LAYER 5: Infrastructure (max 2 levels)
│   │   ├── api.ts           # ⚡ Axios client
│   │   ├── endpoints.ts     # ⚡ API routes
│   │   ├── utils.ts         # Helpers
│   │   └── cn.ts            # Tailwind merger
│   │
│   ├── routes/              # 🌐 Routing (max 2 levels)
│   │   └── index.tsx        # React Router config
│   │
│   ├── i18n/                # 🌍 i18n (max 2 levels)
│   │   └── locales/         # id.json, en.json
│   │
│   ├── styles/              # 💅 Styles (max 2 levels)
│   │   └── globals.css
│   │
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
```

## Maximum Depth: 3 Levels

Examples:
- `src/components/devices/DeviceTable.tsx` ← 3 levels ✅
- `src/hooks/useDevices.ts` ← 2 levels ✅
- `src/services/deviceApi.ts` ← 2 levels ✅

## Clean Architecture Layers

```
Presentation (UI)  →  Business Logic  →  Data Access  →  Domain
    ↓                      ↓                  ↓            ↓
components/           hooks/           services/     types/
pages/                stores/
```
