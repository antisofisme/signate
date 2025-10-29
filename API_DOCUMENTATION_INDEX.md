# Backend API Documentation - Complete Index

**Project:** Smart TV Digital Signage
**Framework:** FastAPI + SQLAlchemy
**Date Generated:** October 28, 2025
**Total Documentation:** 3,965 lines across 6 documents

---

## Documentation Files

### 1. **API_QUICK_REFERENCE.md** (7.2 KB, 342 lines)
**Best for:** Quick lookup, getting started, testing

**Contains:**
- Router file overview table
- Most important endpoints
- Device registration flow diagram
- Heartbeat and content delivery flow
- Authentication examples (curl commands)
- Common operations examples
- Response formats
- Status codes reference
- Device statuses
- Command types
- Device lifecycle diagram
- Testing endpoints

**Read this first:** Yes, if you need to understand the API quickly

**Location:** `/mnt/g/khoirul/signate/API_QUICK_REFERENCE.md`

---

### 2. **API_ENDPOINTS_DOCUMENTATION.md** (30 KB, 1,772 lines)
**Best for:** Complete reference, implementation details, testing

**Contains:**
- Comprehensive endpoint documentation
- Every endpoint with:
  - HTTP method and path
  - Full request schema
  - Complete response format
  - Query parameters
  - Path parameters
  - Error codes
  - Authentication requirements
- Organized by router:
  - Authentication (4 endpoints)
  - Devices (20+ endpoints)
  - Content (11 endpoints)
  - Tags (11 endpoints)
  - Playlists (8+ endpoints)
  - Activities (5 endpoints)
  - Settings (4 endpoints)
  - Device Logs (4 endpoints)
  - Speed Test (5 endpoints)
  - Firebird (6+ endpoints)
  - Client (2 endpoints)
  - Root/Health (3 endpoints)
- Standard response formats
- Authentication details
- Error codes table

**Read this for:** Implementation, testing specific endpoints, understanding all parameters

**Location:** `/mnt/g/khoirul/signate/API_ENDPOINTS_DOCUMENTATION.md`

---

### 3. **API_STRUCTURE_SUMMARY.md** (16 KB, 499 lines)
**Best for:** Architecture understanding, database relationships, design patterns

**Contains:**
- Overview of 15 API router modules
- Each router with:
  - File location
  - Prefix
  - Authentication requirements
  - All endpoints
  - Key features
- Endpoint statistics (90-100 total)
- Authentication & security details
- 15 database models
- Router priority by usage
- Key design patterns:
  - Content resolution hierarchy
  - Device lifecycle
  - Command queue system
  - Real-time monitoring
- Integration points (Anthias, PostgreSQL, Redis, Firebird)
- Standardization details
- Testing notes

**Read this for:** Understanding architecture, seeing the big picture, database modeling

**Location:** `/mnt/g/khoirul/signate/API_STRUCTURE_SUMMARY.md`

---

### 4. **API_ENDPOINT_ANALYSIS_REPORT.md** (20 KB, 542 lines)
**Best for:** Analysis, comparison, categorization

**Contains:**
- [Analysis of all endpoints](Analysis Report)
- (Previously generated, complementary to main documentation)

**Location:** `/mnt/g/khoirul/signate/API_ENDPOINT_ANALYSIS_REPORT.md`

---

### 5. **API_INTEGRATION_PLAN.md** (9.4 KB, 223 lines)
**Best for:** Integration planning, roadmap

**Contains:**
- Integration strategies
- (Previously generated, complementary to main documentation)

**Location:** `/mnt/g/khoirul/signate/API_INTEGRATION_PLAN.md`

---

### 6. **API_MIGRATION_100_PERCENT_COMPLETE.md** (19 KB, 587 lines)
**Best for:** Migration details, what was changed

**Contains:**
- Migration status
- (Previously generated, historical reference)

**Location:** `/mnt/g/khoirul/signate/API_MIGRATION_100_PERCENT_COMPLETE.md`

---

## How to Use These Documents

### For New Developers
1. Start with **API_QUICK_REFERENCE.md** for overview
2. Read **API_STRUCTURE_SUMMARY.md** for architecture
3. Reference **API_ENDPOINTS_DOCUMENTATION.md** for specific endpoints

### For Backend Development
- Use **API_ENDPOINTS_DOCUMENTATION.md** for implementation details
- Use **API_STRUCTURE_SUMMARY.md** for database schema understanding

### For Testing/QA
- Use **API_QUICK_REFERENCE.md** for common operations
- Use **API_ENDPOINTS_DOCUMENTATION.md** for complete endpoint testing
- Use curl examples in Quick Reference for quick testing

### For Integration
- Use **API_STRUCTURE_SUMMARY.md** to understand design patterns
- Use **API_ENDPOINTS_DOCUMENTATION.md** for exact request/response formats
- Reference authentication details for token handling

### For Deployment
- See **API_STRUCTURE_SUMMARY.md** for external service integration
- Check **API_QUICK_REFERENCE.md** for health check endpoints
- Use `/health` and `/docs` endpoints for monitoring

---

## Quick Access by Topic

### Device Management
- **Quick Start:** API_QUICK_REFERENCE.md - "Device Registration Flow"
- **Full Details:** API_ENDPOINTS_DOCUMENTATION.md - "Device Management Endpoints"
- **Architecture:** API_STRUCTURE_SUMMARY.md - "Device Lifecycle"

### Content Management
- **Quick Start:** API_QUICK_REFERENCE.md - "Content to Viewer"
- **Full Details:** API_ENDPOINTS_DOCUMENTATION.md - "Content Management Endpoints"
- **Architecture:** API_STRUCTURE_SUMMARY.md - "Content Resolution Hierarchy"

### Authentication
- **Quick Start:** API_QUICK_REFERENCE.md - "Authentication"
- **Full Details:** API_ENDPOINTS_DOCUMENTATION.md - "Authentication Endpoints"
- **Architecture:** API_STRUCTURE_SUMMARY.md - "Authentication & Security"

### Device Commands
- **Quick Start:** API_QUICK_REFERENCE.md - "Administrative Commands"
- **Full Details:** API_ENDPOINTS_DOCUMENTATION.md - "Device Command Endpoints"
- **Architecture:** API_STRUCTURE_SUMMARY.md - "Command Queue System"

### System Administration
- **Full Details:** API_ENDPOINTS_DOCUMENTATION.md - "Settings/System Endpoints"
- **Quick Reference:** API_QUICK_REFERENCE.md - "Testing"

### Activity/Audit Logs
- **Full Details:** API_ENDPOINTS_DOCUMENTATION.md - "Activities/Logs Endpoints"
- **Architecture:** API_STRUCTURE_SUMMARY.md - "Activities.py"

---

## Router Files Location

All router implementations are located at:
```
/mnt/g/khoirul/signate/backend/app/api/
```

| File | Size | Lines | Active |
|------|------|-------|--------|
| auth.py | 7KB | 217 | Yes |
| devices.py | 34KB | 1,734 | Yes |
| content.py | 25KB | 1,147 | Yes |
| tags.py | 18KB | 618 | Yes |
| playlists.py | 12KB | 400+ | Yes |
| activities.py | 18KB | 518 | Yes |
| settings.py | 17KB | 509 | Yes |
| logs.py | 14KB | 450 | Yes |
| speedtest.py | 13KB | 427 | Yes |
| firebird.py | 20KB | 400+ | Yes |
| client.py | 9KB | 303 | Yes |
| websocket.py | 2KB | ~50 | Yes |
| quickwins_demo.py | - | - | Development |
| v1/organizations.py | - | - | Legacy |

---

## Endpoint Statistics

```
Total API Endpoints:           ~90-100
Routers Active:                13
Routers Documented:            15

By Authentication:
- No Authentication Required:  ~35 endpoints (device clients)
- Authentication Required:     ~65 endpoints (admin/web)

By Function:
- Device Management:           20+ endpoints
- Content Management:          11 endpoints
- Tags:                        11 endpoints
- Playlists:                   8+ endpoints
- Activities:                  5 endpoints
- Speed Test:                  5 endpoints
- Device Logs:                 4 endpoints
- Settings/System:             4 endpoints
- Firebird Integration:        6+ endpoints
- Client/Device:               2 endpoints
- Authentication:              4 endpoints
- Root/Health:                 3 endpoints
```

---

## API Base URLs

**Production Server:**
```
API Base:     http://192.168.5.12:8001
Health:       http://192.168.5.12:8001/health
API Docs:     http://192.168.5.12:8001/docs
Ping:         http://192.168.5.12:8001/api/ping
```

**Authentication:**
```
Login:        POST http://192.168.5.12:8001/api/auth/login
Refresh:      POST http://192.168.5.12:8001/api/auth/refresh
Current User: GET  http://192.168.5.12:8001/api/auth/me
```

---

## Database & Storage

**Primary Database:** PostgreSQL (Port 5433)
**Content Storage:** Anthias (Port 8000)
**Cache:** Redis (optional)
**Legacy:** Firebird (optional)

---

## Key Features Documented

1. **Device Registration & Management**
   - TV device registration with IP/passphrase
   - Monitor self-registration with activation codes
   - Device activation workflow
   - Device heartbeat monitoring
   - Online/offline status (5-minute threshold)

2. **Content Management**
   - Upload to Anthias with metadata extraction
   - Support for images and videos
   - Metadata: resolution, bitrate, fps, codec, duration
   - Content assignment to devices/tags
   - Content serving with correct MIME types
   - Direct static file access via Anthias

3. **Device Grouping**
   - Create tags for device categorization
   - Assign multiple tags to devices
   - Content assignment to tags (applies to all tagged devices)
   - Tag-based content resolution

4. **Content Delivery**
   - Playlist generation for devices
   - Priority-based content ordering
   - Device-specific assignments
   - Tag-based assignments
   - Playlist-based assignments
   - Content deduplication

5. **Remote Management**
   - Command queue system (reset, reload, refresh)
   - Device polling for pending commands
   - Command execution reporting
   - Command expiration (7 days)

6. **Monitoring & Diagnostics**
   - Device console log submission
   - Batch log support
   - Device log filtering and search
   - Auto-cleanup (24-hour retention)
   - Network speed testing
   - Speed test trend analysis

7. **Audit & Security**
   - Activity logging for all actions
   - User/action/entity tracking
   - IP address and user-agent logging
   - Activity statistics and filtering
   - System backup functionality

---

## Support & References

**Related Documentation:**
- `/CLAUDE.md` - Server setup, deployment, environment
- `/CONTENT_TABLE_RENAME_PLAN.md` - Database migration plan
- Web Admin Source: `/web-admin/src/` - Frontend implementation
- Viewer Source: `/viewer/` - Device viewer application

---

## Document Maintenance

**Last Updated:** October 28, 2025
**Version:** 1.0 - Complete API Documentation
**Coverage:** 100% of active API endpoints

To update documentation:
1. Edit relevant router file in `/backend/app/api/`
2. Update API_ENDPOINTS_DOCUMENTATION.md with new endpoint details
3. Update API_STRUCTURE_SUMMARY.md if architecture changes
4. Update API_QUICK_REFERENCE.md with high-impact changes

---

**Start here:** [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)

