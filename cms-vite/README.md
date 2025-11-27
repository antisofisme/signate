# CMS Vite - Digital Signage Admin Dashboard

Admin dashboard untuk mengelola content, devices, playlists, users dan organizations.

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 18.3.1 |
| Build Tool | Vite | 5.3.3 |
| Language | TypeScript | 5.5.3 |
| Routing | React Router | 6.x |
| Server State | TanStack Query | 5.51.1 |
| Client State | Zustand | 4.5.4 |
| Forms | React Hook Form + Zod | 7.x + 3.x |
| UI Components | Shadcn UI | Latest |
| Styling | Tailwind CSS | 3.4.1 |
| Icons | Lucide React | 0.408.0 |
| HTTP Client | Axios | 1.7.2 |
| i18n | i18next | 23.x |
| Notifications | Sonner | Latest |

## Architecture

```
cms-vite/
├── src/
│   ├── main.tsx                  # React entry point
│   ├── routes/                   # React Router configuration
│   │   ├── index.tsx             # Route definitions
│   │   └── ProtectedRoute.tsx    # Auth guard
│   ├── pages/                    # Page components
│   ├── features/                 # Feature modules
│   │   ├── auth/                 # Authentication
│   │   ├── dashboard/            # Dashboard & stats
│   │   ├── devices/              # Device management
│   │   ├── content/              # Content management
│   │   ├── playlists/            # Playlist management
│   │   ├── schedules/            # Schedule management
│   │   ├── users/                # User management
│   │   ├── organizations/        # Organization management
│   │   ├── roles/                # Role & permission management
│   │   ├── device-groups/        # Device grouping
│   │   ├── display-zones/        # Display zone management
│   │   ├── tags/                 # Content tagging
│   │   ├── emergency/            # Emergency alerts
│   │   ├── notifications/        # Notification system
│   │   ├── analytics/            # Analytics & reports
│   │   ├── audit/                # Audit logs
│   │   ├── system/               # System settings
│   │   ├── profile/              # User profile
│   │   └── help/                 # Help & documentation
│   ├── shared/                   # Shared components
│   │   ├── components/
│   │   │   ├── ui/               # Shadcn UI primitives
│   │   │   ├── layout/           # Layout components
│   │   │   └── common/           # Reusable components
│   │   └── hooks/                # Shared hooks
│   ├── lib/                      # Core utilities
│   │   ├── api/                  # Axios client & endpoints
│   │   ├── stores/               # Zustand stores
│   │   ├── websocket/            # WebSocket client
│   │   └── utils/                # Helper functions
│   ├── i18n/                     # Internationalization
│   │   └── locales/              # EN & ID translations
│   └── styles/                   # Global styles
├── public/                       # Static assets
└── dist/                         # Build output
```

## Feature Modules

### 1. Authentication (`/features/auth`)
- Login dengan JWT
- Multi-organization support
- Organization selector
- Session management
- Token refresh

### 2. Dashboard (`/features/dashboard`)
- Device statistics (online/offline/total)
- Content statistics
- Playlist statistics
- Recent activities
- Quick actions

### 3. Devices (`/features/devices`)
- Device list dengan pagination
- 6-digit activation code
- Online/offline status
- Device commands (restart, refresh, clear cache)
- Device detail & edit
- Assign playlist to device

### 4. Content (`/features/content`)
- Content list dengan filter & search
- Upload image/video
- Content preview
- Thumbnail generation
- HLS video support
- Content metadata edit
- Tag assignment

### 5. Playlists (`/features/playlists`)
- Playlist list
- Playlist builder (drag & drop)
- Content item management
- Item duration & ordering
- Playlist assignment to devices

### 6. Schedules (`/features/schedules`)
- Schedule list
- Create/edit schedule
- Time-based playback rules
- Weekly recurring schedules
- Assign to devices

### 7. Users (`/features/users`)
- User list
- Create/edit user
- Role assignment
- Password management
- User activation/deactivation

### 8. Organizations (`/features/organizations`)
- Organization list
- Create/edit organization
- Organization PIN
- Multi-tenant data isolation

### 9. Roles & Permissions (`/features/roles`)
- Role list
- Create/edit role
- Permission assignment
- RBAC management

### 10. Device Groups (`/features/device-groups`)
- Group devices
- Bulk actions
- Group-level scheduling

### 11. Display Zones (`/features/display-zones`)
- Multi-zone layouts
- Zone configuration
- Zone-specific content

### 12. Tags (`/features/tags`)
- Content tagging
- Tag management
- Tag-based filtering

### 13. Emergency (`/features/emergency`)
- Emergency alert broadcast
- Priority messaging
- Alert management

### 14. Notifications (`/features/notifications`)
- User notifications
- Mark as read
- Notification preferences

### 15. Analytics (`/features/analytics`)
- Device uptime reports
- Content play statistics
- User activity reports
- Export to CSV/Excel

### 16. Audit Logs (`/features/audit`)
- System audit trail
- Filter by user/action/date
- Activity history

### 17. System Settings (`/features/system`)
- Global settings
- System configuration
- Maintenance mode

### 18. Profile (`/features/profile`)
- User profile edit
- Change password
- Preferences

## State Management

### Server State (TanStack Query)
```typescript
// Automatic caching, background refetch
const { data, isLoading, error } = useQuery({
  queryKey: ['devices'],
  queryFn: deviceApi.getAll,
  staleTime: 30000,
});
```

### Client State (Zustand)
```typescript
// Auth store (persisted)
const { user, token, logout } = useAuthStore();

// UI store (persisted)
const { theme, language, sidebarOpen } = useUIStore();
```

### Form State (React Hook Form + Zod)
```typescript
const form = useForm<DeviceFormData>({
  resolver: zodResolver(deviceSchema),
});
```

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/login` | LoginPage | User login |
| `/dashboard` | DashboardPage | Main dashboard |
| `/devices` | DevicesPage | Device management |
| `/devices/:id` | DeviceDetailPage | Device detail |
| `/content` | ContentPage | Content management |
| `/content/upload` | UploadPage | Content upload |
| `/playlists` | PlaylistsPage | Playlist management |
| `/playlists/:id` | PlaylistDetailPage | Playlist builder |
| `/schedules` | SchedulesPage | Schedule management |
| `/users` | UsersPage | User management |
| `/organizations` | OrganizationsPage | Organization management |
| `/roles` | RolesPage | Role management |
| `/device-groups` | DeviceGroupsPage | Device groups |
| `/analytics` | AnalyticsPage | Reports & analytics |
| `/audit-logs` | AuditLogsPage | Audit trail |
| `/settings` | SettingsPage | System settings |
| `/profile` | ProfilePage | User profile |

## Components

### Layout Components
- `DashboardLayout` - Main app layout with sidebar
- `Sidebar` - Navigation sidebar
- `Topbar` - Top navigation bar
- `PageHeader` - Page title & breadcrumb

### Shared Components
- `Button` - Button variants
- `Modal` - Dialog modal
- `DeleteConfirmModal` - Delete confirmation
- `Pagination` - Table pagination
- `StatsCard` - Statistics card
- `Tabs` - Tab navigation
- `ThemeSwitcher` - Dark/light mode toggle
- `LanguageSwitcher` - EN/ID language toggle
- `ErrorBoundary` - Error catching
- `OptimizedImage` - Lazy loading images

### Shadcn UI Components
- Button, Card, Input, Table
- Dialog, Select, Checkbox
- Dropdown Menu, Tooltip
- Form components
- Toast notifications

## Internationalization

### Supported Languages
- **English (en)** - Full translation
- **Bahasa Indonesia (id)** - Full translation

### Usage
```typescript
const { t } = useTranslation();
<h1>{t('dashboard.title')}</h1>
```

## WebSocket

Real-time updates via WebSocket:
- Device status changes
- New notifications
- Emergency alerts
- Content sync events

## Environment Variables

```env
# Backend API
VITE_API_URL=https://api.zhmhotels.online
VITE_API_VERSION=v1

# WebSocket
VITE_WS_URL=wss://api.zhmhotels.online

# Application
VITE_APP_NAME="Digital Signage CMS"
VITE_DEFAULT_LANGUAGE=id

# Features
VITE_ENABLE_DARK_MODE=true
```

## Docker Deployment

```yaml
cms-frontend:
  container_name: signage-cms
  image: nginx:alpine
  ports:
    - 3000:80
  volumes:
    - ./cms-vite/dist:/usr/share/nginx/html:ro
    - ./cms-vite/nginx.conf:/etc/nginx/nginx.conf:ro
```

## Nginx Configuration

```nginx
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  # SPA fallback
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Static asset caching
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # API proxy
  location /api {
    proxy_pass http://signage-backend-python:8000;
  }
}
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

## Build Output

```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js      # Main bundle
│   ├── index-[hash].css     # Styles
│   └── vendor-[hash].js     # Vendor chunks
└── ...
```

## URLs

| Environment | URL |
|-------------|-----|
| Production | https://admin.zhmhotels.online |
| Local | http://localhost:3000 |

## Security Features

- JWT token authentication
- Token refresh mechanism
- Protected routes
- Role-based access control (RBAC)
- Multi-tenant data isolation
- CORS protection
- XSS prevention (React auto-escaping)
