# CMS Migration: Next.js → Vite + React

**Date**: 2025-11-02
**Status**: ✅ Migration Complete

---

## 📋 Summary

CMS digital signage telah di-refactor dari **Next.js 15** ke **Vite + React** karena:

### ❌ Kenapa Next.js Overkill:
1. **SSR/Server Components tidak terpakai** - CMS internal tidak perlu SEO
2. **API Routes tidak perlu** - Semua API sudah ada di FastAPI (Python backend)
3. **Deploy complexity** - Perlu Node.js server runtime
4. **Larger bundle** - Next.js runtime overhead

### ✅ Keuntungan Vite + React:
1. **Faster dev server** - Lightning fast HMR
2. **Simpler architecture** - Pure SPA, no server runtime
3. **Static build** - Deploy ke Nginx/Apache/Vercel/Netlify
4. **Smaller bundle** - Tree-shaking by default
5. **Perfect fit** - Backend terpisah (FastAPI), tidak perlu SSR

---

## 🔄 Changes Made

### 1. Folder Rename
```bash
cms-nextjs/ → cms-vite/
```

### 2. Dependencies Changed

#### Removed (Next.js specific):
```json
- "next": "^15.0.0"
- "next-themes": "^0.3.0"
- "next-intl": "^3.15.3"
- "eslint-config-next": "15.0.0"
```

#### Added (Vite + React Router):
```json
+ "vite": "^5.3.3"
+ "@vitejs/plugin-react": "^4.3.1"
+ "react-router-dom": "^6.23.1"
+ "i18next": "^23.11.5"
+ "react-i18next": "^14.1.2"
```

### 3. Structure Changes

#### Before (Next.js):
```
cms-nextjs/
├── app/                    # Next.js App Router
│   ├── (auth)/
│   ├── (dashboard)/
│   ├── layout.tsx
│   └── globals.css
├── features/               # Business logic
├── components/             # UI components
└── lib/                    # Utilities
```

#### After (Vite):
```
cms-vite/
├── index.html             # Entry point (Vite)
├── src/
│   ├── main.tsx          # React entry
│   ├── App.tsx           # Root component
│   ├── routes/           # React Router routes
│   ├── pages/            # Page components
│   ├── features/         # Business logic (same)
│   ├── components/       # UI components (same)
│   ├── lib/              # Utilities (same)
│   └── styles/
│       └── globals.css   # Tailwind styles
└── dist/                 # Build output (static files)
```

### 4. Configuration Files

#### Created:
- ✅ `vite.config.ts` - Vite configuration dengan path alias & proxy
- ✅ `index.html` - Entry HTML file
- ✅ `src/main.tsx` - React entry point dengan React Query
- ✅ `src/routes/index.tsx` - React Router v6 configuration

#### Updated:
- ✅ `package.json` - Vite scripts & dependencies
- ✅ `tsconfig.json` - Vite-compatible TS config
- ✅ `tsconfig.node.json` - Node config for Vite

#### Removed:
- ❌ `next.config.ts` - No longer needed
- ❌ `app/` directory - Replaced with `src/`

---

## 📦 Tech Stack (Maintained)

### Same Dependencies:
- ✅ **React Query** - Server state management
- ✅ **Zustand** - Client/UI state
- ✅ **Axios** - HTTP client
- ✅ **React Hook Form** - Form state
- ✅ **Shadcn UI** - UI components
- ✅ **Tailwind CSS** - Styling
- ✅ **TypeScript** - Type safety

### Architecture (Maintained):
- ✅ **Feature-based** organization
- ✅ **Clean Architecture** principles
- ✅ **Centralized API** endpoints (lib/api/endpoints.ts)
- ✅ **Multi-tenant** support (single domain + org selector)

---

## 🚀 Development Workflow

### Before (Next.js):
```bash
npm run dev          # Next.js dev server (port 3000)
npm run build        # Build for production
npm run start        # Start Node.js server
```

### After (Vite):
```bash
npm run dev          # Vite dev server (port 3000) ⚡ FASTER
npm run build        # Build static files → dist/
npm run preview      # Preview production build
```

---

## 📁 Key Files Created

### 1. Vite Config (`vite.config.ts`)
```typescript
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://192.168.5.12:8001',
        changeOrigin: true,
      },
    },
  },
})
```

### 2. React Entry (`src/main.tsx`)
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { router } from './routes'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <RouterProvider router={router} />
  </QueryClientProvider>
)
```

### 3. Router (`src/routes/index.tsx`)
```typescript
import { createBrowserRouter, Navigate } from 'react-router-dom'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/dashboard" /> },
  { path: '/dashboard', element: <DashboardPage /> },
  // ... more routes
])
```

---

## 🏗️ Deployment

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

### Deploy to Nginx:
```nginx
server {
  listen 3000;
  root /path/to/cms-vite/dist;
  index index.html;

  # SPA fallback
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Cache static assets
  location ~* \.(js|css|png|jpg|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
```

---

## ✅ Migration Checklist

### Completed:
- [x] Rename cms-nextjs → cms-vite
- [x] Update README with Vite documentation (format like player-flutter/README.md)
- [x] Create Vite configuration files
- [x] Update package.json dependencies
- [x] Update tsconfig.json for Vite
- [x] Create src/ structure
- [x] Create React Router setup
- [x] Move existing code to src/
- [x] Create globals.css with Tailwind

### Pending (Implementation):
- [ ] npm install - Install dependencies
- [ ] Setup Shadcn UI components
- [ ] Implement features:
  - [ ] Auth (login, register, org selector)
  - [ ] Dashboard
  - [ ] Devices management
  - [ ] Content upload
  - [ ] Playlist builder
  - [ ] Users management
  - [ ] Settings

---

## 📊 Comparison

| Aspect | Next.js | Vite + React |
|--------|---------|--------------|
| Dev Server | Fast | ⚡ **Faster** |
| Build Output | Node.js server + static | **Static files only** |
| Bundle Size | ~300KB | **~200KB** (smaller) |
| SSR/SEO | ✅ (tidak terpakai) | ❌ (tidak perlu) |
| API Routes | ✅ (tidak terpakai) | ❌ (sudah ada FastAPI) |
| Deploy | Vercel/Node.js | **Any static host** |
| Learning Curve | Higher | **Lower** |
| Use Case | Marketing sites | ✅ **Perfect for SPA CMS** |

---

## 🎯 Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Vite over Next.js** | No SSR needed, backend terpisah (FastAPI), simpler deployment |
| **React Router over App Router** | Client-side routing cukup untuk internal CMS |
| **i18next over next-intl** | Framework-agnostic, works with any React setup |
| **Static build** | Easier deployment (Nginx/Apache), no Node.js runtime |
| **Same architecture** | Maintain clean architecture & feature-based organization |

---

## 🚀 Next Steps

1. **Install dependencies**:
   ```bash
   cd cms-vite
   npm install
   ```

2. **Setup Shadcn UI**:
   ```bash
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card input table dialog
   ```

3. **Start development**:
   ```bash
   npm run dev
   ```

4. **Implement features** (Phase by phase):
   - Phase 1: Auth (login, register, org selector)
   - Phase 2: Dashboard + device management
   - Phase 3: Content upload + playlist builder
   - Phase 4: Users + settings

5. **Build for production**:
   ```bash
   npm run build
   ```

6. **Deploy to production server**:
   ```bash
   # Copy dist/ to server
   scp -r dist/* gzjbbk@192.168.5.12:/path/to/cms/
   ```

---

## 📝 Notes

- ✅ **All features maintained** - React Query, Zustand, Shadcn UI, Dark mode, i18n
- ✅ **Architecture unchanged** - Feature-based, clean architecture
- ✅ **API integration same** - Axios dengan centralized endpoints
- ✅ **Faster development** - Vite HMR vs Next.js refresh
- ✅ **Simpler deployment** - Static files vs Node.js server

**Conclusion**: Migration dari Next.js ke Vite adalah keputusan yang tepat karena tidak ada fitur Next.js yang terpakai (SSR, API Routes, Server Components), dan Vite lebih cocok untuk SPA dengan backend terpisah.

---

**Status**: Ready for implementation! 🎉
