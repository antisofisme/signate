# Web-Admin Frontend API Documentation Index

## Overview

This directory contains complete documentation of all API calls made by the web-admin React/Vite frontend application. Three complementary documents provide different levels of detail for different use cases.

---

## Documentation Files

### 1. WEB_ADMIN_API_DOCUMENTATION.md (19 KB)
**Purpose**: Comprehensive technical reference for developers

**Contains**:
- Complete documentation of all 11 API modules
- Detailed endpoint tables with:
  - HTTP methods
  - URL paths with parameters
  - Request body structures
  - Response formats
  - Usage locations in components
- Page-by-page API breakdown
- Error handling patterns
- Request/response patterns
- React Query integration details
- Development notes and best practices

**Best For**:
- Backend developers implementing/verifying endpoints
- Frontend developers integrating new features
- API testing and QA teams
- Technical documentation reference

**Key Sections**:
1. Configuration (API Base URL, Authentication, Response Format)
2. Auth API (3 endpoints)
3. Devices API (18 endpoints)
4. Content API (8 endpoints)
5. Tags API (11 endpoints)
6. Playlists API (14 endpoints)
7. Widgets API (7 endpoints)
8. Users API (6 endpoints)
9. Settings API (3 endpoints)
10. Activities API (5 endpoints)
11. Client API (2 endpoints)
12. Firebird API (8 endpoints)
13. Page-by-Page Summary
14. Common Query Key Patterns
15. Error Handling Details
16. Request/Response Patterns
17. Development Notes

---

### 2. API_CALLS_QUICK_REFERENCE.md (7.1 KB)
**Purpose**: Quick lookup guide for API endpoints

**Contains**:
- Alphabetical listing of all 85+ endpoints
- Endpoints grouped by module
- Brief description of each endpoint
- Endpoint counts by module
- Most frequently used endpoints (top 10)
- API client class exports
- Usage examples
- Environment configuration
- Important notes for developers

**Best For**:
- Quick endpoint lookup during development
- Onboarding new team members
- Quick reference during code reviews
- API troubleshooting

**Quick Navigation**:
- Authentication (3 endpoints)
- Devices (18 endpoints)
- Content (8 endpoints)
- Tags (11 endpoints)
- Playlists (14 endpoints)
- Widgets (7 endpoints)
- Users (6 endpoints)
- Settings (3 endpoints)
- Activities (5 endpoints)
- Client (2 endpoints)
- Firebird (8 endpoints)

---

### 3. API_EXPLORATION_SUMMARY.md (9.1 KB)
**Purpose**: Executive summary and architectural overview

**Contains**:
- Key findings overview
- Architecture explanation:
  - API client structure
  - Response format
  - Authentication flow
- Component API usage analysis
- Data flow patterns (queries, mutations, real-time updates)
- Most frequently used endpoints
- Technical highlights:
  - Error handling
  - Performance optimizations
  - Security features
- Files analyzed list
- API patterns discovered
- Configuration requirements
- Backend recommendations
- Testing considerations
- Documentation maintenance guidelines

**Best For**:
- Project managers understanding scope
- Architects reviewing system design
- Team leads onboarding engineers
- Integration planning
- Testing strategy development

---

## API Statistics

| Metric | Value |
|--------|-------|
| Total API Modules | 11 |
| Total Endpoints | 85+ |
| Source Files Analyzed | 60+ |
| Pages Analyzed | 9 |
| Modal Components | 20+ |
| Authentication Type | Bearer Token |
| Response Format | Standardized JSON wrapper |
| Data Management | React Query + WebSocket |

---

## API Module Summary

| Module | Endpoints | Primary Functions |
|--------|-----------|-------------------|
| Auth | 3 | User login, logout, profile |
| Devices | 18 | Device management, speed tests, content assignment |
| Content | 8 | File upload, metadata, assignments |
| Tags | 11 | Device grouping, tagging, assignments |
| Playlists | 14 | Content scheduling, sequencing, assignments |
| Widgets | 7 | Dashboard widgets, configurations |
| Users | 6 | User CRUD, roles, password reset |
| Settings | 3 | System info, backup, cache |
| Activities | 5 | Activity logging, statistics, audit trails |
| Client | 2 | Device playlist, status queries |
| Firebird | 8 | SystemPMS integration, database queries |

---

## How to Use These Documents

### For Implementation
1. Start with **API_EXPLORATION_SUMMARY.md** for architecture overview
2. Use **WEB_ADMIN_API_DOCUMENTATION.md** for detailed endpoint specs
3. Reference **API_CALLS_QUICK_REFERENCE.md** during coding

### For Testing
1. Review **API_EXPLORATION_SUMMARY.md** testing section
2. Check **WEB_ADMIN_API_DOCUMENTATION.md** for request/response formats
3. Use **API_CALLS_QUICK_REFERENCE.md** for endpoint coverage

### For Integration
1. Read architecture section in **API_EXPLORATION_SUMMARY.md**
2. Study configuration requirements section
3. Review backend recommendations

### For Onboarding
1. Start with **API_CALLS_QUICK_REFERENCE.md** for overview
2. Dive into **WEB_ADMIN_API_DOCUMENTATION.md** for specifics
3. Reference **API_EXPLORATION_SUMMARY.md** for architectural context

---

## Key Findings

### Architecture Highlights
- **Axios-based client** with interceptors for authentication and response handling
- **Automatic token injection** from localStorage on all requests
- **Standardized response format** with automatic unwrapping
- **React Query integration** for caching and synchronization
- **WebSocket + polling** for real-time updates

### Authentication Flow
```
POST /api/auth/login 
  → Store token in localStorage
  → Inject in all requests as Bearer token
  → 401 errors trigger logout + redirect
```

### Most Used Endpoints
1. GET /api/devices (Dashboard: 10s refresh)
2. GET /api/content (Dashboard)
3. GET /api/tags (Dashboard)
4. GET /api/playlists (Dashboard)
5. GET /api/content/{id}/assignments (Multiple pages)

### API Patterns
- **Standard CRUD**: POST, GET, PATCH, DELETE
- **List with metadata**: GET returns `{ items, total }`
- **Assignment pattern**: POST/DELETE to `/assign` endpoints
- **Nested resources**: `/api/devices/{id}/content`

---

## Related Configuration Files

### Environment Variables
```bash
VITE_API_URL=http://192.168.5.12:8001
VITE_DEBUG_API=false
```

### Server Configuration
- Backend: Port 8001
- Database: Port 5433
- Web Admin (Dev): Port 3000
- Viewer: Port 8080

### CORS Requirements
- Allow port 3000 (web-admin development)
- Allow port 8080 (viewer client)

---

## Exploration Details

### Files Analyzed
- 60+ source files scanned
- 9 page components reviewed
- 20+ modal components examined
- All .jsx, .tsx, .js, .ts files in src/ directory

### Thoroughness
- **Level**: Very Thorough
- **Scope**: Complete web-admin API surface
- **Coverage**: All 85+ endpoints documented
- **Status**: Complete and verified

---

## Next Steps for Development

1. **Backend Team**:
   - Verify all endpoints match implementation
   - Update OpenAPI/Swagger spec
   - Ensure standardized response format
   - Implement missing endpoints if any

2. **Frontend Team**:
   - Review documentation during feature development
   - Use as reference for new API integrations
   - Maintain documentation as APIs evolve

3. **QA/Testing Team**:
   - Use endpoint documentation for test coverage
   - Verify error handling patterns
   - Test CORS configuration
   - Performance testing for frequently-used endpoints

4. **DevOps/Infrastructure**:
   - Configure CORS for web-admin and viewer ports
   - Monitor endpoints listed as most-used
   - Set up API performance monitoring
   - Configure backup strategy for database

---

## Maintenance

These documents should be updated whenever:
1. New API endpoints are added
2. Endpoint signatures change
3. Response format changes
4. Request parameters change
5. Authentication mechanism changes
6. Error handling changes
7. New API modules are created

---

## Document Metadata

| Property | Value |
|----------|-------|
| Created | October 28, 2025 |
| Last Updated | October 28, 2025 |
| Exploration Scope | Web-Admin Frontend |
| Total Endpoints | 85+ |
| API Modules | 11 |
| Documentation Size | 35.2 KB |
| Files | 3 documents |

---

## Quick Links

- **Comprehensive Reference**: WEB_ADMIN_API_DOCUMENTATION.md
- **Quick Lookup**: API_CALLS_QUICK_REFERENCE.md
- **Summary & Architecture**: API_EXPLORATION_SUMMARY.md
- **Source Code**: /web-admin/src/services/api.js
- **Types**: /web-admin/src/types/api.ts

---

*For questions or updates to this documentation, contact the development team.*
