---
name: smart-tv-signage-implementation
description: Guides step-by-step implementation of Smart TV Digital Signage system with correct order, validation, and best practices. Ensures proper foundation before advancing to next phase. Prevents common mistakes and validates each step before proceeding.
---

# Smart TV Digital Signage - Implementation Guide

This skill provides structured, phase-by-phase guidance for implementing the Smart TV Digital Signage system. It ensures correct implementation order, validates each step, and prevents moving forward until prerequisites are complete.

## Project Overview

**Components:**
- Backend API (FastAPI + Python)
- Web Admin (React/Vue)
- WebOS TV App
- Monitor Browser Viewer
- PostgreSQL Database
- Anthias (Digital Signage - already running on server)

**Server Status:**
- Anthias running at: 192.168.5.12:8000
- Server user: gzjbbk
- Server location: /home/gzjbbk/Anthias/

---

## Current Progress Status

✅ **PHASE 1: Foundation - COMPLETED**
✅ **PHASE 2: Backend API Core Features - COMPLETED**
✅ **PHASE 3: Docker Compose Setup - COMPLETED**
✅ **PHASE 4: Web Admin Frontend - COMPLETED**
🔴 **PHASE 5: Monitor Viewer - CURRENT (NEXT TO BUILD)**
⏳ **PHASE 6: WebOS TV App - PENDING**

**What We Have Now:**
- Backend API fully functional (devices, content, tags, assignments, playlist)
- Web Admin can upload/manage content, assign to devices/tags
- Docker services running (PostgreSQL, Redis, Backend, Anthias)
- Content stored in Anthias with proxy endpoint for proper serving
- Database with all tables and relationships

**What We Need Next:**
- Monitor Browser Viewer (`/viewer` URL)
- Activation code system
- Fullscreen content display with smooth transitions
- After this: WebOS TV App

---

## Implementation Phases

### PHASE 1: Foundation (Weeks 1-2) - ✅ COMPLETED

**Must complete in order:**

#### Step 1.1: Database Schema
**Location:** `database/init.sql`

**Tasks:**
1. Create all tables:
   - `devices` (TV & Monitor registry)
   - `content` (Content metadata, NOT files)
   - `tags` (Device grouping)
   - `device_tags` (Many-to-many)
   - `content_assignments` (Content → Device/Tag)
   - `schedules` (Time-based scheduling)
   - `users` (Admin accounts)
   - `firebird_config` (External API config)

2. Add indexes for performance
3. Add seed data (initial admin user)

**Validation Checklist:**
- [ ] All tables created with correct columns
- [ ] Foreign keys properly defined
- [ ] Indexes on frequently queried columns
- [ ] Seed data for admin user exists
- [ ] Can connect to PostgreSQL
- [ ] Schema matches documentation

**Test Command:**
```sql
-- Test all tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- Test admin user seeded
SELECT * FROM users WHERE role = 'admin';
```

**DO NOT PROCEED** until database schema is complete and validated.

---

#### Step 1.2: Backend API - Project Setup
**Location:** `backend/`

**Tasks:**
1. Create `requirements.txt` with dependencies:
   - fastapi
   - uvicorn
   - sqlalchemy
   - psycopg2-binary
   - python-jose (JWT)
   - passlib (password hashing)
   - python-multipart (file upload)
   - httpx (HTTP client for Anthias)
   - redis
   - python-dotenv

2. Create `backend/app/main.py` (entry point)
3. Create `backend/app/core/config.py` (settings from .env)
4. Create `backend/app/core/database.py` (SQLAlchemy connection)
5. Create `backend/Dockerfile`

**Validation Checklist:**
- [ ] All dependencies listed
- [ ] FastAPI app initializes
- [ ] Database connection works
- [ ] Environment variables loaded from .env
- [ ] Can run: `uvicorn app.main:app --reload`
- [ ] Swagger docs accessible at /docs

**Test Command:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
```

**DO NOT PROCEED** until backend starts without errors.

---

#### Step 1.3: Backend API - Database Models
**Location:** `backend/app/models/`

**Tasks:**
1. Create SQLAlchemy models matching database schema:
   - `device.py` (Device model)
   - `content.py` (Content model)
   - `tag.py` (Tag model)
   - `user.py` (User model)
   - `schedule.py` (Schedule model)
   - `firebird_config.py` (FirebirdConfig model)

2. Add relationships (ForeignKey, backref)
3. Add validation (constraints, enums)

**Validation Checklist:**
- [ ] Models match database schema
- [ ] Relationships defined correctly
- [ ] Enums for status fields (pending/active/inactive)
- [ ] Can create test records
- [ ] Can query records

**Test Command:**
```python
# Test in Python shell
from app.models.device import Device
from app.core.database import SessionLocal

db = SessionLocal()
device = Device(device_type="tv", device_name="Test TV", status="pending")
db.add(device)
db.commit()
print(device.id)  # Should print ID
```

**DO NOT PROCEED** until models are tested.

---

#### Step 1.4: Backend API - Authentication
**Location:** `backend/app/api/auth.py`, `backend/app/core/security.py`

**Tasks:**
1. Implement JWT token generation
2. Implement password hashing (bcrypt)
3. Create auth endpoints:
   - POST /api/auth/login
   - POST /api/auth/logout
   - POST /api/auth/refresh
   - GET /api/auth/me

4. Create authentication dependency for protected routes

**Validation Checklist:**
- [ ] Can login with seeded admin user
- [ ] JWT token generated
- [ ] Token validates correctly
- [ ] Protected endpoints require token
- [ ] Password hashing works

**Test Command:**
```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Should return: {"access_token": "...", "token_type": "bearer"}
```

**DO NOT PROCEED** until authentication works.

---

### PHASE 2: Backend API - Core Features (Week 2) - ✅ COMPLETED

#### Step 2.1: Device Management API
**Location:** `backend/app/api/devices.py`

**Tasks:**
1. Implement endpoints:
   - GET /api/devices (list all)
   - POST /api/devices/tv (register TV)
   - POST /api/devices/monitor (generate monitor code)
   - POST /api/devices/monitor/activate (activate monitor)
   - PUT /api/devices/:id (update device)
   - DELETE /api/devices/:id (delete device)
   - POST /api/client/heartbeat (device ping)

2. Implement pairing logic (IP + passphrase for TV)
3. Implement activation code generation (6-digit for Monitor)

**Validation Checklist:**
- [ ] Can register TV with IP + passphrase
- [ ] Can generate monitor activation code
- [ ] Can activate monitor with code
- [ ] Can list all devices
- [ ] Can update device status
- [ ] Heartbeat updates last_seen timestamp

**Test via Swagger:** http://localhost:8000/docs

**DO NOT PROCEED** until device management works.

---

#### Step 2.2: Anthias Integration Service
**Location:** `backend/app/services/anthias_service.py`

**Tasks:**
1. Create AnthiasService class with methods:
   - `upload_asset(file)` → upload to Anthias, return URL
   - `list_assets()` → get all assets from Anthias
   - `delete_asset(asset_id)` → delete from Anthias
   - `get_asset_info(asset_id)` → get asset details

2. Use httpx for async HTTP requests
3. Handle errors (Anthias down, upload failed, etc.)

**Validation Checklist:**
- [ ] Can connect to Anthias at 192.168.5.12:8000
- [ ] Can upload test image
- [ ] Can list assets
- [ ] Can delete asset
- [ ] Error handling works (graceful failures)

**Test Command:**
```python
# Test in Python
from app.services.anthias_service import AnthiasService

service = AnthiasService()
assets = await service.list_assets()
print(assets)  # Should print list from Anthias
```

**CRITICAL:** Anthias must be accessible before proceeding.

---

#### Step 2.3: Content Management API
**Location:** `backend/app/api/content.py`

**Tasks:**
1. Implement endpoints:
   - GET /api/content (list all)
   - POST /api/content (upload file → Anthias, save metadata)
   - PUT /api/content/:id (update metadata)
   - DELETE /api/content/:id (delete from Anthias + database)
   - POST /api/content/:id/assign (assign to device/tag)

2. Integrate with AnthiasService
3. Save Anthias URL to database (NOT file itself!)

**Validation Checklist:**
- [ ] Can upload image, saved to Anthias
- [ ] Metadata saved to PostgreSQL with Anthias URL
- [ ] Can list content with Anthias URLs
- [ ] Can assign content to device
- [ ] Can assign content to tag (all devices in tag)
- [ ] Can delete content (from both Anthias + database)

**Test Flow:**
```
1. Upload image via POST /api/content
2. Check database: content table has record with anthias_url
3. Check Anthias: asset exists at URL
4. Assign to device: POST /api/content/1/assign
5. Check database: content_assignments table has record
```

**DO NOT PROCEED** until content management works end-to-end.

---

#### Step 2.4: Playlist API (Client Endpoint)
**Location:** `backend/app/api/client.py`

**Tasks:**
1. Implement endpoint:
   - GET /api/client/playlist?device_id=xxx

2. Logic:
   - Get device info
   - Get device tags
   - Query content_assignments (match device_id OR tag_id)
   - Apply schedule filters (optional for MVP)
   - Sort by priority
   - Return list with Anthias URLs + duration

**Validation Checklist:**
- [ ] Device gets correct playlist
- [ ] Playlist includes content assigned to device
- [ ] Playlist includes content assigned to device's tags
- [ ] Returns Anthias URLs (not file data)
- [ ] Returns duration for each content

**Test Command:**
```bash
# Register device first, get device_id
# Then test playlist
curl http://localhost:8000/api/client/playlist?device_id=1

# Should return:
{
  "playlist": [
    {
      "content_id": 1,
      "title": "Banner 1",
      "url": "http://192.168.5.12:8000/asset/xxx.jpg",
      "duration": 10,
      "type": "image"
    }
  ]
}
```

**DO NOT PROCEED** until playlist API works.

---

### PHASE 3: Docker Compose Setup (Week 2-3) - ✅ COMPLETED

#### Step 3.1: Docker Compose Configuration
**Location:** `docker-compose.yml`

**Tasks:**
1. Define services:
   - postgres (PostgreSQL 15)
   - redis (Redis 7)
   - backend-api (FastAPI)
   - web-admin (React/Vue - placeholder for now)
   - nginx (Reverse proxy - optional)

2. Configure networks
3. Configure volumes (postgres-data, redis-data)
4. Set environment variables from .env

**Validation Checklist:**
- [ ] All services start: `docker-compose up -d`
- [ ] PostgreSQL accessible
- [ ] Redis accessible
- [ ] Backend API accessible at http://localhost:8000
- [ ] Swagger docs at http://localhost:8000/docs
- [ ] All endpoints work via Docker

**Test Command:**
```bash
docker-compose up -d
docker-compose ps  # All services should be "Up"
curl http://localhost:8000/docs  # Should load
```

**DO NOT PROCEED** until Docker setup works.

---

### PHASE 4: Web Admin Frontend (Week 3-4) - ✅ COMPLETED

#### Step 4.1: Web Admin - Project Setup
**Location:** `web-admin/`

**Tasks:**
1. Choose framework (React + Vite recommended)
2. Initialize project:
   ```bash
   cd web-admin
   npm create vite@latest . -- --template react
   npm install
   ```
3. Install dependencies:
   - axios (HTTP client)
   - react-router-dom (routing)
   - @tanstack/react-query (API state)
   - tailwindcss (styling)
   - shadcn/ui or antd (UI components)

4. Create folder structure:
   - src/components/
   - src/pages/
   - src/services/ (API client)
   - src/hooks/
   - src/utils/

**Validation Checklist:**
- [ ] Vite dev server runs: `npm run dev`
- [ ] Can access http://localhost:3000
- [ ] TailwindCSS works
- [ ] Can make API call to backend

**DO NOT PROCEED** until frontend starts.

---

#### Step 4.2: Web Admin - Authentication UI
**Location:** `web-admin/src/pages/`

**Tasks:**
1. Create Login page
2. Implement login form
3. Call backend /api/auth/login
4. Store JWT token (localStorage or cookie)
5. Create protected routes
6. Create logout functionality

**Validation Checklist:**
- [ ] Can login with admin credentials
- [ ] Token stored correctly
- [ ] Protected routes redirect to login if not authenticated
- [ ] Can logout

---

#### Step 4.3: Web Admin - Device Management UI
**Location:** `web-admin/src/pages/Devices.jsx`

**Tasks:**
1. Create "Devices" page
2. List all devices (GET /api/devices)
3. Add "Register TV" form:
   - Device Name input
   - IP Address input
   - Passphrase input
   - Submit → POST /api/devices/tv

4. Add "Activate Monitor" form:
   - Activation Code input
   - Device Name input
   - Submit → POST /api/devices/monitor/activate

5. Display device status (pending/active/inactive)

**Validation Checklist:**
- [ ] Can see list of devices
- [ ] Can register TV via form
- [ ] Can activate monitor via form
- [ ] Device status updates in real-time

---

#### Step 4.4: Web Admin - Content Management UI
**Location:** `web-admin/src/pages/Content.jsx`

**Tasks:**
1. Create "Content" page
2. List all content (GET /api/content)
3. Add "Upload Content" form:
   - File input (drag & drop)
   - Title input
   - Duration input (seconds)
   - Submit → POST /api/content

4. Display content with:
   - Thumbnail (from Anthias URL)
   - Title, duration, type
   - Assign button
   - Delete button

5. Create "Assign Content" modal:
   - Select devices (checkboxes)
   - Select tags (checkboxes)
   - Submit → POST /api/content/:id/assign

**Validation Checklist:**
- [ ] Can upload image/video
- [ ] File saved to Anthias
- [ ] Content appears in list
- [ ] Can assign to device
- [ ] Can assign to tag
- [ ] Can delete content

**DO NOT PROCEED** until Web Admin can upload & assign content.

---

### PHASE 5: Monitor Viewer (Week 4-5) - 🔴 CURRENT PHASE

**THIS IS OUR NEXT PRIORITY!**

Monitor Viewer is a web-based viewer that displays content in fullscreen mode. It's the simplest client to build and test before tackling WebOS TV App.

**Why This First:**
- No special hardware needed (just browser)
- Easy to test and debug
- Validates backend playlist API
- Tests content display and transitions
- Validates assignment logic

#### Step 5.1: Monitor Viewer - Basic HTML
**Location:** `monitor-viewer/index.html`

**Tasks:**
1. Create single-page HTML viewer
2. On load:
   - Generate unique code (6-digit)
   - POST /api/devices/monitor → get device_id
   - Display activation code on screen
   - Poll every 5 seconds: GET /api/devices/:id/status

3. After activation:
   - Fetch playlist: GET /api/client/playlist?device_id=xxx
   - Enter fullscreen mode
   - Display content with smooth transitions

4. Implement content player:
   - Preload next content
   - Fade-out current, fade-in next
   - Loop playlist

**Validation Checklist:**
- [ ] Opens in browser
- [ ] Displays activation code
- [ ] Admin can activate via Web Admin
- [ ] After activation, goes fullscreen
- [ ] Displays content from playlist
- [ ] Smooth transitions work
- [ ] Loops playlist continuously

**Test Flow:**
```
1. Open monitor-viewer/index.html in browser
2. Note activation code (e.g., "XYZ123")
3. Go to Web Admin → Activate Monitor
4. Enter code + device name
5. Monitor should activate & display content
```

**DO NOT PROCEED** until monitor viewer works.

---

### PHASE 6: WebOS TV App (Week 5-8)

#### Step 6.1: Setup Development Environment

**Prerequisites:**
- Node.js installed
- Ares CLI installed: `npm install -g @webos-tools/cli`
- TV in Developer Mode (get passphrase)

**Tasks:**
1. Install Ares CLI
2. Setup TV device:
   ```bash
   ares-setup-device
   # Enter TV IP, passphrase
   ```
3. Test connection:
   ```bash
   ares-device-info -d tv
   ```

**Validation Checklist:**
- [ ] Ares CLI installed
- [ ] Can connect to TV
- [ ] TV in Developer Mode

---

#### Step 6.2: WebOS App - Project Setup
**Location:** `webos-app/`

**Tasks:**
1. Create project structure
2. Create `appinfo.json`:
   ```json
   {
     "id": "com.hotel.signage",
     "version": "1.0.0",
     "vendor": "Hotel",
     "type": "web",
     "main": "index.html",
     "title": "Hotel Signage",
     "icon": "icon.png"
   }
   ```

3. Create basic React app (or vanilla JS)
4. Build & test locally

**Validation Checklist:**
- [ ] Project structure created
- [ ] appinfo.json valid
- [ ] Can build app
- [ ] Can run locally in browser

---

#### Step 6.3: WebOS App - Core Functionality

**Tasks:**
1. Implement device registration:
   - Get TV IP from network
   - Hardcode passphrase (or config)
   - POST /api/client/heartbeat

2. Implement playlist fetcher:
   - GET /api/client/playlist?device_id=xxx
   - Store playlist in state

3. Implement content player:
   - Display image/video fullscreen
   - Preload next content
   - Smooth transitions (fade in/out)
   - Auto-advance based on duration

4. Implement heartbeat:
   - POST /api/client/heartbeat every 30 seconds

**Validation Checklist:**
- [ ] App connects to backend
- [ ] Gets device_id from heartbeat
- [ ] Fetches playlist
- [ ] Displays content fullscreen
- [ ] Transitions are smooth
- [ ] Loops playlist
- [ ] Heartbeat works

---

#### Step 6.4: WebOS App - Deploy to TV

**Tasks:**
1. Build app:
   ```bash
   npm run build
   ```

2. Package IPK:
   ```bash
   ares-package dist/
   ```

3. Install to TV:
   ```bash
   ares-install --device tv com.hotel.signage_1.0.0_all.ipk
   ```

4. Launch on TV:
   ```bash
   ares-launch --device tv com.hotel.signage
   ```

**Validation Checklist:**
- [ ] App builds successfully
- [ ] IPK created
- [ ] Installed on TV without errors
- [ ] App launches on TV
- [ ] Content displays correctly on TV
- [ ] Smooth transitions work on actual hardware

**DO NOT PROCEED** until TV app works on actual TV.

---

## Common Mistakes to Avoid

### Database
- ❌ Storing file binary data in PostgreSQL
- ✅ Store only metadata + Anthias URL

### Anthias Integration
- ❌ Implementing own file storage
- ✅ Use Anthias for file storage, get URL back

### Content Assignment
- ❌ Assigning content directly in content table
- ✅ Use content_assignments table (many-to-many)

### Device Registration
- ❌ Auto-registering devices without admin approval
- ✅ Admin registers device → device connects → status active

### WebOS Development
- ❌ Testing only in browser
- ✅ Always test on actual TV hardware

---

## Validation Gates

**Cannot start Phase 2** until:
- Database schema complete
- Backend API starts
- Models work
- Authentication works

**Cannot start Phase 3** until:
- Device API works
- Anthias integration works
- Content API works
- Playlist API works

**Cannot start Phase 4** until:
- Docker Compose runs all services
- Backend accessible via Docker

**Cannot start Phase 5** until:
- Web Admin can upload content
- Web Admin can assign content
- Web Admin can register/activate devices

**Cannot start Phase 6** until:
- Monitor viewer works
- Content displays correctly
- Backend API stable

---

## Testing Checklist Per Phase

### Phase 1 Complete When:
- [ ] PostgreSQL running
- [ ] All tables created
- [ ] Backend API starts
- [ ] Swagger docs accessible
- [ ] Can login via API
- [ ] Models CRUD works

### Phase 2 Complete When:
- [ ] Can register TV via API
- [ ] Can generate monitor code via API
- [ ] Can upload file to Anthias via API
- [ ] Metadata saved to PostgreSQL
- [ ] Can fetch playlist via API
- [ ] Playlist returns correct content with URLs

### Phase 3 Complete When:
- [ ] `docker-compose up` works
- [ ] All services healthy
- [ ] Backend accessible via Docker
- [ ] Database persistent (volumes work)

### Phase 4 Complete When:
- [ ] Web Admin login works
- [ ] Can register TV via UI
- [ ] Can activate monitor via UI
- [ ] Can upload content via UI
- [ ] Can assign content via UI
- [ ] Can see device list via UI

### Phase 5 Complete When:
- [ ] Monitor opens in browser
- [ ] Activation code generated
- [ ] Can activate from Web Admin
- [ ] Content displays after activation
- [ ] Smooth transitions work
- [ ] Loops playlist

### Phase 6 Complete When:
- [ ] WebOS app installs on TV
- [ ] App launches on TV
- [ ] Content displays on TV
- [ ] Transitions smooth on TV hardware
- [ ] Playlist updates work
- [ ] Heartbeat works

---

## Emergency Rollback

If stuck or broken:

1. **Database issues:** Drop & recreate tables from init.sql
2. **Backend issues:** Check logs, verify .env config
3. **Docker issues:** `docker-compose down -v && docker-compose up -d`
4. **Anthias issues:** Check Anthias server status at 192.168.5.12
5. **TV issues:** Uninstall app, rebuild, reinstall

---

## Success Criteria

**MVP Success (2-3 weeks):**
- Admin can upload content via Web Admin
- Content stored in Anthias
- Monitor viewer displays content
- Smooth transitions work
- Multiple monitors can be activated

**Full System Success (8-10 weeks):**
- All above +
- WebOS TV app works on actual TVs
- Scheduling system works
- Firebird integration works
- System stable for 24/7 operation

---

## Next Step Prompt

After completing each phase, ask:

**"Phase X completed. Validate checklist before proceeding to Phase Y?"**

Only proceed when user confirms all validation items checked.
