# Backend-Frontend Service Mapping

## Overview
This document maps all 17 backend services to their corresponding frontend features, pages, and implementation status.

---

## Comprehensive Mapping Table

| # | Backend Service | Frontend Feature | Feature Path | Pages | Frontend Status | Notes |
|---|---|---|---|---|---|---|
| 1 | **auth** | auth | `/features/auth/` | LoginPage, RegisterPage, ForgotPasswordPage, ResetPasswordPage, SelectOrganizationPage | ✅ IMPLEMENTED | Core auth system with JWT, login/register/password reset |
| 2 | **content** | contents | `/features/contents/` | ContentPage | ✅ IMPLEMENTED | Content upload, management, storage integration |
| 3 | **device** | devices | `/features/devices/` | DevicesPage, DeviceGroupsPage, DevicePreviewPage | ✅ IMPLEMENTED | Device registration, heartbeat, groups, commands, extended info |
| 4 | **playlist** | playlists | `/features/playlists/` | PlaylistsPage | ✅ IMPLEMENTED | Playlist CRUD, content assignment, device/tag assignment |
| 5 | **user** | users | `/features/users/` | UsersPage (in SettingsPage tab) | ✅ IMPLEMENTED | User CRUD, password management, role assignment |
| 6 | **organization** | organizations | `/features/organizations/` | OrganizationsPage (in SettingsPage tab) | ✅ IMPLEMENTED | Organization CRUD, quota management |
| 7 | **rbac** | rbac | `/features/rbac/` | RolesPage | ✅ IMPLEMENTED | Role CRUD, permission management, system roles |
| 8 | **schedule** | schedules | `/features/schedules/` | No standalone page | ⚠️ PARTIAL | API/hooks implemented but no dedicated UI page |
| 9 | **tag** | tags | `/features/tags/` | TagsPage | ✅ IMPLEMENTED | Tag CRUD, bulk operations |
| 10 | **template** | templates | `/features/templates/` | No standalone page | ⚠️ PARTIAL | API/hooks implemented but no dedicated UI page |
| 11 | **session** | sessions | `/features/sessions/` | SessionsPage | ✅ IMPLEMENTED | Session management, revocation, statistics |
| 12 | **translation** | translations | `/features/translations/` | No standalone page | ⚠️ PARTIAL | API implemented with pages folder, but may not be fully integrated |
| 13 | **analytics** | analytics | `/features/analytics/` | AnalyticsPage | ✅ IMPLEMENTED | Dashboard, content performance, device engagement, playback logs |
| 14 | **audit** | audit | `/features/audit/` | AuditLogsPage | ✅ IMPLEMENTED | Audit log listing and viewing |
| 15 | **widget** | widgets | `/features/widgets/` | No standalone page | ⚠️ PARTIAL | API implemented but no dedicated UI page |
| 16 | **weather** | weather | `/features/weather/` | No standalone page | ⚠️ PARTIAL | API implemented (GET current, forecast) but no UI |
| 17 | **pms** | pms | `/features/pms/` | No standalone page | ⚠️ PARTIAL | WebSocket endpoints for sync, minimal REST (trigger sync only) |

---

## Implementation Status Summary

### ✅ FULLY IMPLEMENTED (12 services)
1. **auth** - Complete authentication system with all flows
2. **content** - Content management with upload/download
3. **device** - Device management with multiple sub-features (groups, commands, health, logs, assignments)
4. **playlist** - Playlist management with content and device/tag assignments
5. **user** - User management with CRUD and password changes
6. **organization** - Organization management with quota system
7. **rbac** - Role-based access control with permission management
8. **tag** - Tag management with bulk operations
9. **session** - Session management with statistics
10. **analytics** - Analytics dashboard with multiple views
11. **audit** - Audit log viewing
12. **rbac** - Role and permission management

### ⚠️ PARTIALLY IMPLEMENTED (5 services)
1. **schedule** - API fully built (CRUD, scheduling logic) but no dedicated UI page
   - Has hooks and services but missing visual UI
   
2. **template** - API fully built (CRUD, rendering, validation) but no dedicated UI page
   - Has routes and services but no UI components or pages
   
3. **translation** - API fully built (multi-language support) but UI integration unclear
   - Has `/pages/` folder but appears to be minimal implementation
   - May need full integration with content/playlist UI
   
4. **widget** - API fully built (CRUD, playlist widgets) but no dedicated UI page
   - Has routes and services but no UI components
   
5. **weather** - API minimal (only GET endpoints) and no UI
   - Only supports fetching current/forecast data
   - No management interface

6. **pms** - WebSocket-based with minimal REST API
   - Only has `POST /pms/trigger-sync/{organization_id}`
   - Complex WebSocket syncing logic but no UI

---

## Page Location Analysis

### Pages in `/src/pages/` (19 files)
- **Authentication Pages**: LoginPage, RegisterPage, ForgotPasswordPage, ResetPasswordPage
- **Dashboard & Core**: DashboardPage, SelectOrganizationPage, SettingsPage
- **Feature Pages**: 
  - Device Management: DevicesPage, DeviceGroupsPage, DevicePreviewPage
  - Content: ContentPage
  - Playlists: PlaylistsPage
  - RBAC: RolesPage
  - Tags: TagsPage
  - Sessions: SessionsPage
  - Analytics: AnalyticsPage
  - Audit: AuditLogsPage
  - Organizations/Users: OrganizationsPage, UsersPage (shown as tabs in SettingsPage)

### Features WITHOUT Dedicated Pages (5)
1. **schedules** - No page (should add SchedulesPage)
2. **templates** - No page (should add TemplatesPage)
3. **translations** - Has pages folder but not integrated (unclear status)
4. **widgets** - No page (should add WidgetsPage)
5. **weather** - No page (should add WeatherPage)

---

## Feature Folder Structure

### Features WITH `/api/` folder (Advanced)
- **devices** - Has `deviceApi.ts`, `groupsApi.ts`, `health.ts`, `commands.ts`
- **playlists** - Structure similar
- **schedules** - Has `/api/` folder
- **templates** - Has `/api/` folder
- **translations** - Has `/api/` folder
- **widgets** - Has `/api/` folder

### Features WITHOUT `/api/` folder (Simpler)
- **auth** - Has `/services/` instead
- **contents** - Has `/services/`
- **users** - Has `/services/`
- **organizations** - Has `/services/`
- **rbac** - Has `/services/`
- **tags** - Has `/services/`
- **sessions** - Has `/api/` folder
- **analytics** - Has `/api/` folder
- **audit** - Has `/api/` folder
- **pms** - Has `/api/` folder
- **weather** - Has `/api/` folder

---

## Missing Frontend Features (Priority List)

### HIGH PRIORITY
1. **SchedulesPage** - Schedule management UI
   - Backend has full CRUD + scheduling logic
   - Frontend has API integration, just needs UI components and page
   
2. **TemplatesPage** - Template management UI
   - Backend has full CRUD + rendering/validation
   - Frontend has API integration, just needs UI

3. **WidgetsPage** - Widget management UI
   - Backend has CRUD for widgets and playlist widgets
   - Frontend has API integration, just needs UI

### MEDIUM PRIORITY
4. **WeatherPage** - Weather widget management (if needed)
   - Backend has basic GET endpoints
   - May be internal feature for displays, not user-facing

5. **Translation Management UI**
   - Backend has comprehensive multi-language API
   - Frontend has routes but integration status unclear
   - May be integrated into other content management pages

### LOW PRIORITY
6. **PMS UI** - Syncing interface
   - Complex backend WebSocket logic
   - May be internal/admin-only feature
   - Backend supports trigger-sync REST endpoint

---

## Backend Service Details

### Device Service (Most Complex)
- **File Structure**: 
  - `routes.py` - Main device CRUD
  - `assignment_routes.py` - Device group assignments
  - `command_routes.py` - Remote commands
  - `extended_routes.py` - Extended device info
  - `group_routes.py` - Group management
  - `health_routes.py` - Health metrics
  - `log_routes.py` - Device logs

- **Frontend Implementation**: Multi-component system
  - Device CRUD in DevicesPage
  - Device Groups in DeviceGroupsPage
  - Commands and health in respective components
  - Extended info in DevicePreviewPage

### Content Service (Upload-Heavy)
- **Endpoints**: Upload, bulk upload, download, CRUD, bulk operations
- **Frontend**: ContentPage with upload components

### Playlist Service (Assignment-Heavy)
- **Endpoints**: 
  - CRUD operations
  - Content item management
  - Device assignments
  - Tag assignments
  - Reordering
  - Content resolution for devices

- **Frontend**: PlaylistsPage with assignment UI

---

## API Routes Organization

### Centralized API Routes (backend-python)
All services reference `shared.api_routes.py` for:
- AuthRoutes
- DeviceRoutes
- ContentRoutes
- PlaylistRoutes
- UserRoutes
- OrganizationRoutes
- RBACRoutes
- etc.

This ensures consistent endpoint definitions across backend and frontend.

---

## Technology Stack Consistency

### Backend (Python - FastAPI)
- Clean Architecture pattern
- Repository pattern for data access
- Use cases for business logic
- DTOs for request/response validation
- Centralized error handling & logging

### Frontend (React - Vite)
- Feature-based architecture
- API layer (`/api/` or `/services/`)
- Custom hooks for data fetching
- TypeScript types
- TanStack Query for server state
- Zustand for global state

---

## Recommendations

1. **Complete Missing UI Pages** (High Priority)
   - Create SchedulesPage (scheduling builder)
   - Create TemplatesPage (template editor)
   - Create WidgetsPage (widget configuration)

2. **Clarify Translation Integration**
   - Determine if translations are integrated into content/playlist management
   - Consolidate translation UI if scattered

3. **Review PMS Service**
   - Determine if WebSocket PMS is user-facing or internal
   - May not need UI if it's automatic syncing

4. **Review Weather Service**
   - Determine if it's for weather widgets on displays
   - May not need management UI if only used internally

5. **Standardize Feature Folder Structure**
   - Decide on `/api/` vs `/services/` naming
   - Ensure all features follow same pattern

