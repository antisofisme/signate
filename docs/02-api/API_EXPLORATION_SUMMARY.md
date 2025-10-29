# Web-Admin Frontend - API Exploration Summary

## Exploration Completed: October 28, 2025

This document summarizes the comprehensive exploration of all API calls made by the web-admin React/Vite frontend application.

---

## Deliverables

### 1. WEB_ADMIN_API_DOCUMENTATION.md (19 KB)
Comprehensive reference with:
- Complete API module documentation (11 modules)
- Detailed endpoint tables with HTTP methods, parameters, and returns
- Page-by-page API usage breakdown
- Error handling patterns
- Request/response patterns
- React Query key patterns
- Development notes

### 2. API_CALLS_QUICK_REFERENCE.md (7.1 KB)
Quick reference guide with:
- Alphabetical endpoint listing (85+ total endpoints)
- Endpoint counts by module
- Most frequently used endpoints
- API client export reference
- Usage examples
- Environment configuration
- Important notes

---

## Key Findings

### API Modules Documented (11 Total)

| Module | Endpoints | Key Features |
|--------|-----------|--------------|
| Auth | 3 | Login, logout, user profile |
| Devices | 18 | Registration, management, content assignment, speed tests |
| Content | 8 | Upload, management, assignments |
| Tags | 11 | Device grouping, content assignment |
| Playlists | 14 | Content scheduling, device assignment |
| Widgets | 7 | Widget management for dashboard |
| Users | 6 | User management and roles |
| Settings | 3 | System info, backup, cache |
| Activities | 5 | Activity logging and statistics |
| Client | 2 | Device client integration |
| Firebird | 8 | SystemPMS integration |

**Total: 85 API Endpoints**

---

## Architecture Overview

### API Client Structure
```
src/services/api.js
├── axios instance configuration
├── Request interceptor (token injection)
├── Response interceptor (standardized unwrapping)
├── 11 API modules
└── Error handling
```

### Response Format
```javascript
// Backend response
{
  success: true,
  data: { /* actual payload */ },
  meta: { timestamp, request_id, version }
}

// Auto-unwrapped to
{ /* actual payload */ }
```

### Authentication Flow
1. User logs in: `POST /api/auth/login`
2. Token stored in `localStorage`
3. Automatically injected in all requests as Bearer token
4. 401 errors trigger logout and redirect to `/login`

---

## Component API Usage Analysis

### Pages Using Most API Calls
1. **Dashboard** - 7 different endpoints (devices, content, tags, playlists, activities)
2. **Devices** - 5 endpoints (list, register, update, delete operations)
3. **Contents** - 6 endpoints (list, upload, manage, assign)
4. **Playlists** - 6 endpoints (CRUD + assignment)
5. **Tags** - 5 endpoints (CRUD + device management)

### Modal Components with API Calls
- DeviceDetailModal - Device info, tags, playlists, content
- AssignContentModal - Content assignment with playlist sync
- DeviceLogsModal - Device logs viewing
- SpeedHistoryModal - Speed test history
- Various Form Modals - Create/update operations

---

## Data Flow Patterns

### Query Flow (Fetch)
1. Component uses `useQuery()` from React Query
2. `queryKey` identifies cached data
3. `queryFn` calls API module method
4. Response auto-unwrapped by interceptor
5. Data displayed in UI

### Mutation Flow (Create/Update/Delete)
1. Component uses `useMutation()` from React Query
2. User action triggers mutation
3. Optimistic or standard update
4. `queryClient.invalidateQueries()` called on success
5. Related queries refetch automatically
6. Toast notification shown to user

### Real-time Updates
- Dashboard uses WebSocket for live updates
- Fallback to polling with `refetchInterval`
- Activities refresh every 60 seconds
- Devices refresh every 10 seconds in dashboard
- System info refreshes every 30 seconds

---

## Most Frequently Used Endpoints

### By Request Count (Per Page Session)
1. `GET /api/devices` - Used on Dashboard (10s) and Devices page
2. `GET /api/content` - Dashboard and Contents page
3. `GET /api/content/{id}/assignments` - Multiple places for assignment display
4. `GET /api/tags` - Dashboard and Tags page
5. `GET /api/playlists` - Dashboard and Playlists page
6. `POST /api/content/upload` - Contents upload
7. `PUT /api/devices/{id}` - Device approvals and updates
8. `GET /api/activities` - Activities page (60s refresh)
9. `GET /api/settings/system/info` - System tab (30s refresh)
10. `GET /api/users` - Settings user management

---

## Technical Highlights

### Error Handling
- Consistent error format from backend
- Access via `error.response?.data?.detail`
- 401 auto-handling with logout
- Toast notifications for user feedback
- Validation error details for fields

### Performance Optimizations
- React Query caching
- Automatic query invalidation on mutations
- Polling intervals configured appropriately
- Lazy loading of modal data
- useMemo for filtered/computed data

### Security
- Bearer token authentication
- Token stored securely in localStorage
- Automatic token injection on all requests
- CORS properly configured
- Sensitive data not logged (debug mode available)

---

## Files Analyzed

### Source Files Reviewed
- `src/services/api.js` - Main API client (320 lines)
- `src/pages/Dashboard.tsx` - Dashboard page
- `src/pages/Devices.tsx` - Devices management
- `src/pages/Contents.tsx` - Content management
- `src/pages/Tags.tsx` - Tag management
- `src/pages/Playlists.tsx` - Playlist management
- `src/pages/Activities.tsx` - Activity logs
- `src/pages/Settings.tsx` - Settings container
- `src/pages/Login.tsx` - Login page
- `src/contexts/AuthContext.tsx` - Auth state management
- `src/components/settings/SystemTab.tsx` - System settings
- `src/components/settings/UsersTab.tsx` - User management
- `src/components/devices/modals/DeviceDetailModal.tsx` - Device details
- `src/components/devices/modals/AssignContentModal.tsx` - Content assignment
- Plus 20+ additional modal and component files

### Total Files Analyzed: 60+

---

## API Patterns Discovered

### Standard GET Lists
```javascript
GET /api/{resource}
Returns: { items: [...], total: number }
```

### Standard CRUD
```javascript
POST /api/{resource}        // Create
GET /api/{resource}/{id}    // Read
PATCH /api/{resource}/{id}  // Update
DELETE /api/{resource}/{id} // Delete
```

### Assignment Patterns
```javascript
POST /api/{resource}/{id}/assign        // Assign to devices/tags
DELETE /api/{resource}/{id}/assign      // Unassign (with body)
GET /api/{resource}/{id}/assignments    // View assignments
```

### Nested Resources
```javascript
GET /api/devices/{id}/content
POST /api/content/{id}/assign to { device_id, priority }
```

---

## Configuration Requirements

### Environment Variables
```bash
VITE_API_URL=http://192.168.5.12:8001      # Backend URL
VITE_DEBUG_API=false                        # Debug logging (optional)
```

### CORS Configuration (Backend)
Must include:
- Port 3000 (Web Admin development)
- Port 8080 (Viewer)

### Server Configuration
- Backend running on port 8001
- PostgreSQL running on port 5433
- API endpoints all under `/api/` namespace

---

## Recommendations for Backend Development

1. **Consistency**: All endpoints follow standardized response format
2. **Validation**: Include field information in validation errors
3. **Pagination**: Support `skip` and `limit` parameters for list endpoints
4. **Filtering**: Support dynamic filter parameters on list endpoints
5. **Sorting**: Support `sort_by` parameter with standard options
6. **Timestamps**: All timestamps in ISO 8601 format (UTC)
7. **Error Codes**: Use consistent error codes for error handling
8. **Documentation**: Maintain OpenAPI/Swagger spec in sync

---

## Testing Considerations

### API Testing Checklist
- [ ] All 85 endpoints respond with correct status codes
- [ ] Response format matches standardized wrapper
- [ ] Bearer token validation working
- [ ] 401 responses trigger logout correctly
- [ ] Validation errors include field information
- [ ] File uploads accept multipart/form-data
- [ ] Query parameters properly handled
- [ ] Pagination works correctly
- [ ] Sorting works as expected
- [ ] Filtering works as expected

### Frontend Testing
- [ ] All queries fetch and display data correctly
- [ ] All mutations succeed and invalidate queries
- [ ] Error messages display properly
- [ ] Toast notifications appear
- [ ] Loading states shown during requests
- [ ] Optimistic updates work correctly

---

## Documentation Maintenance

These documentation files should be updated when:
1. New API endpoints are added
2. Endpoint signatures change
3. Request/response formats change
4. New API modules are created
5. Authentication changes
6. Error handling changes
7. Query key patterns change

**Last Updated**: October 28, 2025
**Exploration Scope**: Complete web-admin frontend API coverage
**Status**: COMPLETE - 85 endpoints documented

---

## Quick Links

- **Main Documentation**: `WEB_ADMIN_API_DOCUMENTATION.md`
- **Quick Reference**: `API_CALLS_QUICK_REFERENCE.md`
- **API Source Code**: `src/services/api.js`
- **API Types**: `src/types/api.ts`

---

*This exploration was performed with thoroughness level: VERY THOROUGH*
*All .jsx, .tsx, .js, .ts files in src/ were scanned for API usage*
*Total analysis: 60+ source files, 85+ API endpoints documented*
