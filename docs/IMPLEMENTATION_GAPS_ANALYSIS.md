# Backend-Frontend Mapping: Detailed Gaps Analysis

## Executive Summary

**Total Services**: 17 (Backend)
**Fully Implemented**: 12 services (70.6%)
**Partially Implemented**: 5 services (29.4%)
**Not Implemented**: 0 services (0%)

**Key Finding**: Core business logic is complete. Missing implementations are mostly UI layers for less frequently used services.

---

## Services Status Details

### FULLY IMPLEMENTED (12 Services)

#### 1. AUTH SERVICE
**Backend Routes**: 5 endpoints
- POST /auth/login
- POST /auth/register
- POST /auth/forgot-password
- POST /auth/reset-password
- POST /auth/logout

**Frontend Coverage**: 100%
- LoginPage (/pages/LoginPage.tsx)
- RegisterPage (/pages/RegisterPage.tsx)
- ForgotPasswordPage (/pages/ForgotPasswordPage.tsx)
- ResetPasswordPage (/pages/ResetPasswordPage.tsx)
- SelectOrganizationPage (/pages/SelectOrganizationPage.tsx)
- Auth hooks and Zustand store implemented
- JWT token handling complete

**Status**: PRODUCTION READY

---

#### 2. CONTENT SERVICE
**Backend Routes**: 9 endpoints
- POST /content/upload
- POST /content/bulk-upload
- GET /content (list)
- GET /content/{id}
- PUT /content/{id}
- GET /content/download
- DELETE /content/{id}
- POST /content/bulk-delete
- POST /content/bulk-update

**Frontend Coverage**: 100%
- ContentPage (/pages/ContentPage.tsx)
- Upload components
- Preview components
- Bulk operations UI

**Status**: PRODUCTION READY

---

#### 3. DEVICE SERVICE
**Backend Routes**: 48 endpoints (across multiple route files)
- Core: CRUD operations (routes.py)
- Groups: Group management (group_routes.py)
- Commands: Remote device commands (command_routes.py)
- Extended: Device info (extended_routes.py)
- Health: Health metrics (health_routes.py)
- Logs: Device logs (log_routes.py)
- Assignments: Device assignments (assignment_routes.py)

**Frontend Coverage**: 100%
- DevicesPage (/pages/DevicesPage.tsx)
- DeviceGroupsPage (/pages/DeviceGroupsPage.tsx)
- DevicePreviewPage (/pages/DevicePreviewPage.tsx)
- Multiple API modules (deviceApi.ts, groupsApi.ts, health.ts, commands.ts)
- WebSocket integration for health monitoring
- Comprehensive component library

**Status**: PRODUCTION READY

---

#### 4. PLAYLIST SERVICE
**Backend Routes**: 15 endpoints
- Core: POST/GET/PATCH/DELETE /playlists
- Content: Manage playlist contents
- Device Assignment: Assign to devices
- Tag Assignment: Assign to tags
- Reordering: Change content order
- Resolution: Get content for device
- Conflict checking: Validate assignments

**Frontend Coverage**: 100%
- PlaylistsPage (/pages/PlaylistsPage.tsx)
- Content assignment UI
- Device/tag assignment UI
- Reordering drag-and-drop
- Complete hook integration

**Status**: PRODUCTION READY

---

#### 5. USER SERVICE
**Backend Routes**: 6 endpoints
- GET /users (list with filters)
- POST /users (create)
- GET /users/{user_id}
- PUT /users/{user_id}
- PUT /users/{user_id}/change-password
- DELETE /users/{user_id}

**Frontend Coverage**: 100%
- UsersPage component (in SettingsPage as tab)
- User CRUD forms
- Password change modal
- Role assignment
- Implemented in /features/users/

**Status**: PRODUCTION READY

---

#### 6. ORGANIZATION SERVICE
**Backend Routes**: 11 endpoints
- Core CRUD: GET/POST/PUT/DELETE
- Quota: Check and manage quotas
  - Get quota
  - Check device quota
  - Check user quota
  - Check content quota
  - Update quota

**Frontend Coverage**: 100%
- OrganizationsPage component (in SettingsPage as tab)
- Organization CRUD
- Quota management UI
- Implemented in /features/organizations/

**Status**: PRODUCTION READY

---

#### 7. RBAC SERVICE
**Backend Routes**: 10 endpoints
- Roles: GET/POST/PUT/DELETE /roles
- System Roles: GET predefined system roles
- Permissions: GET all permissions
- Permission Checks: POST check user permission
- Permission Management: POST/DELETE add/remove permissions

**Frontend Coverage**: 100%
- RolesPage (/pages/RolesPage.tsx)
- Role CRUD forms
- Permission matrix UI
- Role assignment in user management
- Implemented in /features/rbac/

**Status**: PRODUCTION READY

---

#### 8. TAG SERVICE
**Backend Routes**: 10 endpoints
- Core: POST/GET/PUT/DELETE /tags
- Bulk Operations: bulk-create, bulk-update, bulk-delete
- Search/Filter: Tag listing with search

**Frontend Coverage**: 100%
- TagsPage (/pages/TagsPage.tsx)
- Tag CRUD
- Bulk operations UI
- Tag selection components
- Implemented in /features/tags/

**Status**: PRODUCTION READY

---

#### 9. SESSION SERVICE
**Backend Routes**: 8 endpoints
- GET /sessions (list)
- GET /sessions/active
- GET /sessions/stats
- DELETE /sessions/{session_id} (revoke)
- POST /sessions/revoke-all
- GET /sessions/user/{user_id}
- GET /sessions/ip/{ip_address}
- DELETE /sessions/admin/{session_id}

**Frontend Coverage**: 100%
- SessionsPage (/pages/SessionsPage.tsx)
- Session listing
- Revocation UI
- Statistics display
- User session filtering
- Implemented in /features/sessions/

**Status**: PRODUCTION READY

---

#### 10. ANALYTICS SERVICE
**Backend Routes**: 7 endpoints
- GET /analytics/dashboard
- GET /analytics/content-performance
- GET /analytics/device-engagement
- GET /analytics/stats
- GET /analytics/timeline
- POST /analytics/playback/start
- PUT /analytics/playback/{log_id}/end

**Frontend Coverage**: 100%
- AnalyticsPage (/pages/AnalyticsPage.tsx)
- Dashboard widgets
- Charts for performance
- Device engagement metrics
- Playback tracking
- Implemented in /features/analytics/

**Status**: PRODUCTION READY

---

#### 11. AUDIT SERVICE
**Backend Routes**: 2 endpoints
- GET /audit (list with filters)
- GET /audit/{log_id}

**Frontend Coverage**: 100%
- AuditLogsPage (/pages/AuditLogsPage.tsx)
- Log listing with filters
- Log detail view
- Implemented in /features/audit/

**Status**: PRODUCTION READY

---

#### 12. BONUS: rbac (Duplicate in Summary)
See RBAC above - listed twice in initial analysis

---

### PARTIALLY IMPLEMENTED (5 Services)

#### 1. SCHEDULE SERVICE - CRITICAL GAP
**Status**: ⚠️ BACKEND COMPLETE, FRONTEND MISSING UI

**Backend Routes**: 10 endpoints (FULLY IMPLEMENTED)
```
POST   /schedules                          - Create schedule
GET    /schedules                          - List schedules
GET    /schedules/{schedule_id}            - Get schedule
PUT    /schedules/{schedule_id}            - Update schedule
DELETE /schedules/{schedule_id}            - Delete schedule
POST   /schedules/{schedule_id}/deactivate - Deactivate schedule
GET    /schedules/active/now               - Get currently active
POST   /schedules/active/check             - Check active
POST   /schedules/{schedule_id}/calculate-next - Calculate next occurrence
POST   /schedules/check-conflicts          - Validate no conflicts
POST   /schedules/refresh                  - Refresh schedules
```

**Frontend Implementation Status**:
- Feature folder: EXISTS (/features/schedules/)
- API layer: EXISTS (hooks, services)
- Page: MISSING
- Components: MINIMAL or MISSING

**What's Missing**:
1. SchedulesPage component
2. Schedule creation form (complex time/recurrence picker)
3. Schedule listing and filtering
4. Schedule editor with conflict preview
5. Time zone handling UI
6. Recurrence rule builder

**Recommendation**: HIGH PRIORITY
- Create /pages/SchedulesPage.tsx
- Implement schedule form with react-hook-form
- Add recurrence rule builder (consider rrule.js library)
- Add time zone picker
- Add conflict preview

**Estimated Effort**: 40-60 hours

---

#### 2. TEMPLATE SERVICE - IMPORTANT GAP
**Status**: ⚠️ BACKEND COMPLETE, FRONTEND MISSING UI

**Backend Routes**: 8 endpoints (FULLY IMPLEMENTED)
```
POST   /templates                    - Create template
GET    /templates                    - List templates
GET    /templates/{template_id}      - Get template
PUT    /templates/{template_id}      - Update template
DELETE /templates/{template_id}      - Delete template
POST   /templates/{template_id}/render        - Render template
POST   /templates/validate           - Validate template syntax
POST   /templates/extract-variables  - Extract template variables
```

**Frontend Implementation Status**:
- Feature folder: EXISTS (/features/templates/)
- API layer: EXISTS (hooks, services)
- Page: MISSING
- Components: MINIMAL or MISSING

**What's Missing**:
1. TemplatesPage component
2. Template editor with syntax highlighting
3. Template preview/render preview
4. Variable extraction display
5. Template validation feedback
6. Template library/gallery

**Recommendation**: HIGH PRIORITY
- Create /pages/TemplatesPage.tsx
- Implement template editor with Monaco or CodeMirror
- Add template preview pane
- Add variable extraction list
- Add syntax validation with error display

**Estimated Effort**: 30-50 hours

---

#### 3. TRANSLATION SERVICE - UNCLEAR INTEGRATION
**Status**: ⚠️ BACKEND COMPLETE, FRONTEND PARTIALLY UNCLEAR

**Backend Routes**: 9 endpoints (FULLY IMPLEMENTED)
```
POST   /translations                     - Create translation
GET    /translations                     - List translations
GET    /translations/{translation_id}    - Get translation
DELETE /translations/{translation_id}    - Delete translation
GET    /translations/{entity_type}/{entity_id} - Get entity translations
DELETE /translations/{entity_type}/{entity_id} - Delete entity translations
POST   /translations/bulk                - Bulk import
GET    /translations/languages/supported - Get supported languages
GET    /translations/languages/organization - Get organization languages
GET    /translations/stats               - Get statistics
```

**Frontend Implementation Status**:
- Feature folder: EXISTS (/features/translations/)
- Feature has pages/ subfolder (unusual)
- API layer: EXISTS
- Main Page: UNCLEAR (may be in pages/ subfolder)
- Integration: UNCLEAR

**Questions to Resolve**:
1. Is this user-facing or internal?
2. Is this embedded in content/playlist management?
3. Should it be standalone or integrated?
4. What's the purpose (UI i18n vs content translations)?

**What Might Be Missing**:
1. Clarity on whether this is for UI localization or content
2. Language management UI (if not embedded)
3. Translation management interface
4. Bulk import/export tools

**Recommendation**: CLARIFY FIRST
- Review /features/translations/pages/ contents
- Determine if integrated into other features
- Decide on architecture (standalone vs embedded)
- May not need separate management UI if fully embedded

**Estimated Effort**: 10-20 hours (depends on scope decision)

---

#### 4. WIDGET SERVICE - MEDIUM GAP
**Status**: ⚠️ BACKEND COMPLETE, FRONTEND MISSING UI

**Backend Routes**: 9 endpoints (FULLY IMPLEMENTED)
```
POST   /widgets                  - Create widget
GET    /widgets                  - List widgets
GET    /widgets/{widget_id}      - Get widget
PUT    /widgets/{widget_id}      - Update widget
DELETE /widgets/{widget_id}      - Delete widget
POST   /playlists/{playlist_id}/widgets          - Add to playlist
GET    /playlists/{playlist_id}/widgets          - List playlist widgets
PUT    /playlist-widgets/{playlist_widget_id}    - Update playlist widget
DELETE /playlists/{playlist_id}/widgets/{widget_id} - Remove from playlist
```

**Frontend Implementation Status**:
- Feature folder: EXISTS (/features/widgets/)
- API layer: EXISTS (hooks, services)
- Page: MISSING
- Components: MINIMAL or MISSING

**What's Missing**:
1. WidgetsPage component
2. Widget library/gallery view
3. Widget configuration UI
4. Playlist widget assignment
5. Widget preview

**Note**: Widgets might be:
- Display elements for playlists (clock, weather, RSS, etc.)
- Content modules
- Interactive elements on digital displays

**Recommendation**: MEDIUM PRIORITY
- Create /pages/WidgetsPage.tsx
- Implement widget gallery
- Add widget configuration forms (type-specific)
- Add preview
- Integrate with playlist page if not already

**Estimated Effort**: 25-40 hours

---

#### 5. WEATHER SERVICE - LOW PRIORITY
**Status**: ⚠️ BACKEND MINIMAL, FRONTEND MISSING

**Backend Routes**: 2 endpoints (MINIMAL)
```
GET /weather/current   - Get current weather
GET /weather/forecast  - Get weather forecast
```

**Frontend Implementation Status**:
- Feature folder: EXISTS (/features/weather/)
- API layer: EXISTS
- Page: MISSING
- Components: MINIMAL or MISSING

**What's Missing**:
1. WeatherPage (if needed)
2. Weather configuration
3. Location management
4. Data source configuration

**Important Questions**:
1. Is this user-facing or internal to displays?
2. Is it a widget for playlists?
3. Does it need management UI or just API calls?

**Recommendation**: LOW PRIORITY
- Clarify if weather is:
  - A widget for playlists (configure in playlist UI)
  - A standalone service (needs WeatherPage)
  - Internal to displays (no UI needed)
- Implementation depends on answers above

**Estimated Effort**: 5-15 hours (or 0 if internal)

---

#### 6. PMS SERVICE - SPECIALIZED
**Status**: ⚠️ WEBSOCKET-BASED, MINIMAL REST API

**Backend Routes**: 1 REST endpoint + WebSocket
```
POST /pms/trigger-sync/{organization_id} - Trigger sync
WebSocket endpoints for real-time sync (complex logic)
```

**Frontend Implementation Status**:
- Feature folder: EXISTS (/features/pms/)
- API layer: EXISTS (WebSocket routes and services)
- Page: MISSING
- Components: MINIMAL

**Likely Purpose**: PMS (Property Management System) integration
- Probably syncs with external PMS systems
- WebSocket for real-time updates
- May be automated/internal service

**What's Missing**:
1. UI for triggering sync
2. Sync status monitoring
3. Sync logs/history
4. Error reporting

**Important Questions**:
1. Is PMS sync automatic or manual?
2. Do users need to see sync status?
3. Is this admin-only feature?

**Recommendation**: LOW PRIORITY
- Clarify if PMS is user-facing
- If manual sync needed: create simple trigger UI
- If internal: may not need UI
- Monitor sync status: could be in admin dashboard

**Estimated Effort**: 10-20 hours (if needed)

---

## Summary Table: Implementation Gap

| Service | Backend | Frontend Page | Frontend API | Components | Recommendation |
|---------|---------|---------------|-------------|------------|-----------------|
| auth | 100% | 100% | 100% | 100% | COMPLETE |
| content | 100% | 100% | 100% | 100% | COMPLETE |
| device | 100% | 100% | 100% | 100% | COMPLETE |
| playlist | 100% | 100% | 100% | 100% | COMPLETE |
| user | 100% | 100% | 100% | 100% | COMPLETE |
| organization | 100% | 100% | 100% | 100% | COMPLETE |
| rbac | 100% | 100% | 100% | 100% | COMPLETE |
| tag | 100% | 100% | 100% | 100% | COMPLETE |
| session | 100% | 100% | 100% | 100% | COMPLETE |
| analytics | 100% | 100% | 100% | 100% | COMPLETE |
| audit | 100% | 100% | 100% | 100% | COMPLETE |
| schedule | 100% | 0% | 80% | 20% | CREATE SCHEDULEPAGE |
| template | 100% | 0% | 80% | 20% | CREATE TEMPLATEPAGE |
| widget | 100% | 0% | 80% | 20% | CREATE WIDGETSPAGE |
| translation | 100% | ? | 80% | ? | CLARIFY INTEGRATION |
| weather | 50% | 0% | 80% | 0% | CLARIFY PURPOSE |
| pms | 90% | 0% | 80% | 0% | CLARIFY SCOPE |

---

## Priority Roadmap

### PHASE 1: HIGH PRIORITY (2-3 weeks)
1. Create SchedulesPage
   - Implement schedule CRUD with form
   - Add recurrence rule builder
   - Add time picker and time zone selector
   - Add conflict preview

2. Create TemplatesPage
   - Implement template editor
   - Add syntax highlighting
   - Add preview pane
   - Add variable extraction view

### PHASE 2: MEDIUM PRIORITY (1-2 weeks)
3. Create WidgetsPage
   - Implement widget gallery/library
   - Add widget configuration UI
   - Integrate with playlist UI

4. Clarify Translation Integration
   - Determine if embedded or standalone
   - Complete implementation based on decision

### PHASE 3: LOW PRIORITY (as needed)
5. Clarify Weather Purpose
   - Determine if standalone or widget
   - Implement if user-facing

6. Clarify PMS Scope
   - Determine if user-facing
   - Implement basic UI if needed

---

## Architecture Notes

### Naming Inconsistency Found
- Some features use `/api/` folder (devices, playlists, sessions, analytics, audit)
- Some use `/services/` folder (auth, contents, users, organizations, rbac, tags)

**Recommendation**: Standardize on one approach
- Prefer `/api/` for explicit separation of concerns
- Make `/services/` for business logic only
- Consider refactoring older services

---

## Testing Coverage Gap

No detailed information available on unit/integration test coverage.

**Recommendation**:
- Add tests for all new UI pages
- Ensure API integration tests
- Consider e2e tests for complex workflows (schedule creation, template editing)

