# DOKUMEN PEMAHAMAN SISTEM LAUNCHER SMART TV + DIGITAL SIGNAGE

## OVERVIEW PROYEK

Membangun sistem digital signage terintegrasi yang terdiri dari:
- **Smart TV WebOS** (aplikasi launcher custom)
- **Monitor Browser** (web-based viewer)  
- **Backend API Server** (orchestrator)
- **Anthias** (digital signage untuk serve konten)
- **Web Admin Panel** (manajemen terpusat)
- **Firebird API** (external, sudah ada - untuk data tamu)

---

## ARSITEKTUR SISTEM

### **DEPLOYMENT ARCHITECTURE**

```
┌─────────────────── SERVER (DOCKER) ────────────────────┐
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Service 1: ANTHIAS                              │  │
│  │  - Digital signage platform                      │  │
│  │  - Serve images/videos via HTTP                  │  │
│  │  - URL: http://server:port/image/xxx.jpg         │  │
│  │  - Admin UI untuk upload konten                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Service 2: BACKEND API (Python FastAPI)         │  │
│  │  - REST API orchestrator                         │  │
│  │  - Connect ke Anthias API                        │  │
│  │  - Fetch dari Firebird API (external)            │  │
│  │  - Device management                             │  │
│  │  - Content scheduling & tagging                  │  │
│  │  - WebSocket untuk real-time updates             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Service 3: WEB ADMIN FRONTEND (React/Vue)       │  │
│  │  - UI untuk admin                                │  │
│  │  - Upload konten ke Anthias                      │  │
│  │  - Device management (TV + Monitor)              │  │
│  │  - Content tagging & scheduling                  │  │
│  │  - Preview konten                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Service 4: DATABASE (PostgreSQL/MySQL)          │  │
│  │  - Metadata konten                               │  │
│  │  - Device registry                               │  │
│  │  - Schedules                                     │  │
│  │  - Tags/Groups                                   │  │
│  │  - User accounts                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
└────────────────────────────────────────────────────────┘

           ▲                              ▲
           │ REST API                     │ REST API
           │                              │
┌──────────┴──────────┐        ┌─────────┴──────────┐
│   SMART TV WebOS    │        │  MONITOR BROWSER   │
│   (IPK Application) │        │  (Web Viewer)      │
│                     │        │                    │
│ - Fetch dari API    │        │ - Buka URL viewer  │
│ - Display banner    │        │ - Generate code    │
│ - Display info tamu │        │ - Full screen mode │
│ - IP + Passphrase   │        │ - Unique code ID   │
└─────────────────────┘        └────────────────────┘

           ▲
           │ HTTPS Request
           │
┌──────────┴──────────┐
│   FIREBIRD API      │
│   (EXTERNAL)        │
│ - Data tamu hotel   │
│ - Already exists    │
└─────────────────────┘
```

---

## TECH STACK

### **Server Side (Docker Services)**

**Service 1: Anthias**
- Platform: Raspberry Pi OS / Linux Docker image
- Fungsi: Digital signage, serve konten via HTTP URL
- API: Built-in Anthias REST API

**Service 2: Backend API**
- Language: Python 3.11+
- Framework: FastAPI
- Database ORM: SQLAlchemy
- WebSocket: FastAPI native
- HTTP Client: httpx (untuk call Anthias API + Firebird API)
- Authentication: JWT tokens
- CORS: Enabled untuk Web Admin + TV/Monitor

**Service 3: Web Admin Frontend**
- Framework: React + Vite atau Vue 3
- UI Library: Ant Design / Material-UI / Shadcn
- HTTP Client: Axios
- State Management: Redux Toolkit / Pinia
- File Upload: React Dropzone
- Styling: Tailwind CSS

**Service 4: Database**
- PostgreSQL atau MySQL
- Digunakan untuk:
  - Device registry (TV & Monitor)
  - Content metadata
  - Schedules
  - Tags/Groups
  - User accounts

### **Client Side**

**WebOS TV Application**
- Development Tool: Ares CLI
- Framework: React (recommended)
- Package Format: IPK
- HTTP Client: Axios / Fetch API
- WebSocket Client: Native WebSocket API
- Smooth Transitions: CSS3 + GPU acceleration

**Monitor Browser Viewer**
- Pure Web App (HTML/CSS/JS)
- Framework: React / Vue (lightweight)
- Full screen: JavaScript Fullscreen API
- Auto-refresh: WebSocket / Polling

---

## DATABASE SCHEMA

### **Tables**

**1. devices**
```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('tv', 'monitor')),
    device_name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45), -- nullable untuk monitor
    passphrase VARCHAR(50), -- nullable untuk monitor
    unique_code VARCHAR(20), -- nullable untuk TV
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'active', 'inactive')),
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. content**
```sql
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('image', 'video')),
    anthias_url VARCHAR(500) NOT NULL,
    duration INTEGER NOT NULL DEFAULT 10, -- durasi dalam detik
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**3. tags**
```sql
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**4. device_tags** (many-to-many)
```sql
CREATE TABLE device_tags (
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (device_id, tag_id)
);
```

**5. content_assignments**
```sql
CREATE TABLE content_assignments (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE, -- nullable
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE, -- nullable
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK ((device_id IS NOT NULL AND tag_id IS NULL) OR 
           (device_id IS NULL AND tag_id IS NOT NULL))
);
```

**6. schedules**
```sql
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE, -- nullable
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE, -- nullable
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week JSON NOT NULL, -- [1,2,3,4,5,6,7]
    start_date DATE NOT NULL,
    end_date DATE, -- nullable
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**7. users**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**8. firebird_config**
```sql
CREATE TABLE firebird_config (
    id SERIAL PRIMARY KEY,
    api_endpoint VARCHAR(500) NOT NULL,
    api_key TEXT NOT NULL, -- encrypted
    refresh_interval INTEGER DEFAULT 300, -- dalam detik
    query_params JSON,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API ENDPOINTS DESIGN

### **Backend API Endpoints**

**Authentication**
```
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
GET    /api/auth/me
```

**Devices Management**
```
GET    /api/devices              # List all devices
POST   /api/devices/tv           # Register TV (manual IP + passphrase)
POST   /api/devices/monitor      # Generate monitor code
PUT    /api/devices/:id          # Update device info
DELETE /api/devices/:id          # Remove device
GET    /api/devices/:id/status   # Get device status
POST   /api/devices/monitor/activate  # Activate monitor dengan code
```

**Content Management**
```
GET    /api/content              # List all content
POST   /api/content              # Create content (upload ke Anthias)
PUT    /api/content/:id          # Update content metadata
DELETE /api/content/:id          # Delete content
GET    /api/content/:id          # Get content detail
POST   /api/content/:id/assign   # Assign ke device/tag
```

**Tags Management**
```
GET    /api/tags                 # List all tags
POST   /api/tags                 # Create tag
PUT    /api/tags/:id             # Update tag
DELETE /api/tags/:id             # Delete tag
POST   /api/tags/:id/devices     # Assign devices ke tag
```

**Schedules**
```
GET    /api/schedules            # List all schedules
POST   /api/schedules            # Create schedule
PUT    /api/schedules/:id        # Update schedule
DELETE /api/schedules/:id        # Delete schedule
```

**Client Endpoints (untuk TV & Monitor)**
```
GET    /api/client/playlist      # Get content untuk device ini
       Query params: device_id, device_type
       Response: list content dengan URL, duration, order

GET    /api/client/guest-info    # Get data tamu dari Firebird
       Response: formatted guest data

POST   /api/client/heartbeat     # Device ping (update last_seen)
       Body: device_id, status, logs
```

**Firebird Integration**
```
GET    /api/firebird/test        # Test koneksi ke Firebird API
GET    /api/firebird/config      # Get config
PUT    /api/firebird/config      # Update config (endpoint, api_key, dll)
GET    /api/firebird/data        # Fetch data dari Firebird (manual trigger)
```

**WebSocket**
```
WS     /ws/device/:device_id     # Real-time updates untuk device
       Events: 
       - content_updated
       - schedule_changed
       - device_command (reboot, refresh, dll)
```

---

## DEVICE MANAGEMENT FLOW

### **TV WebOS Registration & Pairing**

**Step 1: Admin Input di Web Admin**
```
Admin → Web Admin → "Add TV Device"
Input:
- Device Name: "TV Lobby"
- IP Address: "192.168.1.100"
- Passphrase: "ABC123" (dari Developer Mode App)
→ Backend API → Save ke database (status: pending)
```

**Step 2: TV Auto-Connect**
```
TV App Launch → 
Config hardcoded:
- Backend API URL
- Device IP (ambil dari network info)
- Passphrase (hardcoded atau input manual first time)
→ POST /api/client/heartbeat
→ Backend match IP + Passphrase
→ Update status: active
→ Response: device_id
→ TV save device_id to local storage
```

**Step 3: TV Operational**
```
TV App → Periodic fetch:
- GET /api/client/playlist?device_id=xxx
- GET /api/client/guest-info
- WebSocket connect untuk real-time updates
→ Display content
```

---

### **Monitor Browser Registration & Pairing**

**Step 1: Monitor Buka URL**
```
Browser → http://server/viewer
→ Backend generate unique_code: "XYZABC"
→ Display di screen: "Kode Aktivasi: XYZABC"
→ Save ke database (status: pending)
→ Poll every 5 sec untuk check activation
```

**Step 2: Admin Activate di Web Admin**
```
Admin → Web Admin → "Activate Monitor"
Input:
- Code: "XYZABC"
- Device Name: "Monitor Resto"
- Tag: "Resto"
→ POST /api/devices/monitor/activate
→ Update status: active
```

**Step 3: Monitor Operational**
```
Monitor detect activation →
Fetch playlist:
- GET /api/client/playlist?device_id=xxx
- GET /api/client/guest-info
- WebSocket connect
→ Full screen mode
→ Display content
```

---

## CONTENT DELIVERY FLOW

### **Upload & Assignment Flow**

**Step 1: Admin Upload Konten**
```
Admin → Web Admin → Upload image/video
→ POST /api/content
→ Backend:
  1. Upload file ke Anthias via Anthias API
  2. Get Anthias URL (http://anthias/asset/xxx.jpg)
  3. Save metadata ke database:
     - title
     - content_type
     - anthias_url
     - duration
→ Response: content_id
```

**Step 2: Admin Assign Konten**
```
Admin → Select content → "Assign to devices"
Options:
A. Individual devices:
   ☑ TV Lobby
   ☑ Monitor Resto
   
B. Tags/Groups:
   ☑ Tag: "Lobby Group"

→ POST /api/content/:id/assign
→ Backend save ke content_assignments table
→ Trigger WebSocket event ke affected devices
```

**Step 3: Device Fetch Playlist**
```
Device → GET /api/client/playlist?device_id=xxx
Backend logic:
1. Get device info (id, tags)
2. Query content_assignments:
   - WHERE device_id = xxx OR tag_id IN (device.tags)
3. Apply schedule filters (time, date, active)
4. Sort by priority
5. Return playlist:
   [
     {
       content_id: 1,
       title: "Banner Promo",
       url: "http://anthias/asset/banner1.jpg",
       duration: 10,
       type: "image"
     },
     ...
   ]
Device → Display content dengan smooth transitions
```

---

## FIREBIRD API INTEGRATION

### **Configuration**

Admin configure di Web Admin:
```
- API Endpoint: https://hotel-api.com/guests
- API Key: xxxxxx (encrypted)
- Refresh Interval: 300 seconds (5 menit)
- Query Params: { "status": "checked_in" }
```

### **Data Fetching Flow**

**Periodic Fetch (Backend)**
```
Backend Scheduler (Celery/APScheduler):
Every 5 minutes →
1. GET firebird_config
2. Request ke Firebird API:
   GET https://hotel-api.com/guests?status=checked_in
   Headers: { "Authorization": "Bearer xxx" }
3. Parse response
4. Cache data (Redis atau in-memory)
5. Format data untuk display
```

**Client Request**
```
TV/Monitor → GET /api/client/guest-info
Backend → Return cached data:
{
  "last_updated": "2025-10-21T10:30:00Z",
  "guests": [
    {
      "name": "John Doe",
      "room": "101",
      "check_in": "2025-10-20",
      "check_out": "2025-10-25"
    },
    ...
  ]
}
```

---

## SMOOTH TRANSITIONS (Inspired by Anthias)

### **Konsep di WebOS TV & Monitor Browser**

**Preloading Strategy**
```
Current content playing (duration: 10 sec)
  ↓
At 7 sec mark (3 sec before end):
  → Preload next content
  → Image: new Image().src = next_url
  → Video: <video preload="auto">
  ↓
At 9 sec mark:
  → Start fade-out current (1 sec transition)
  → Start fade-in next (1 sec transition)
  ↓
At 10 sec mark:
  → Switch to next content
  → Repeat cycle
```

**CSS Transitions**
```css
.content-container {
  will-change: opacity, transform;
  transition: opacity 1s ease-in-out;
}

.fade-out {
  opacity: 0;
}

.fade-in {
  opacity: 1;
}
```

**Hardware Acceleration**
```css
.content-image {
  transform: translate3d(0, 0, 0);
  backface-visibility: hidden;
  perspective: 1000px;
}
```

**JavaScript Implementation Concept**
```javascript
class ContentPlayer {
  constructor() {
    this.currentIndex = 0;
    this.playlist = [];
    this.preloadedContent = null;
  }

  async preloadNext() {
    const nextIndex = (this.currentIndex + 1) % this.playlist.length;
    const nextContent = this.playlist[nextIndex];
    
    if (nextContent.type === 'image') {
      const img = new Image();
      img.src = nextContent.url;
      this.preloadedContent = img;
    } else if (nextContent.type === 'video') {
      const video = document.createElement('video');
      video.preload = 'auto';
      video.src = nextContent.url;
      this.preloadedContent = video;
    }
  }

  async transition() {
    // Fade out current
    currentElement.classList.add('fade-out');
    
    // Wait for transition
    await sleep(1000);
    
    // Switch content
    currentElement.src = this.preloadedContent.src;
    currentElement.classList.remove('fade-out');
    currentElement.classList.add('fade-in');
    
    // Update index
    this.currentIndex = (this.currentIndex + 1) % this.playlist.length;
    
    // Preload next in background
    this.preloadNext();
  }
}
```

---

## DEVELOPMENT WORKFLOW

### **Development Tools**

**WebOS TV App Development**
```bash
# 1. Install Ares CLI
npm install -g @webos-tools/cli

# 2. Setup profile
ares-config --profile tv

# 3. Create project
ares-generate -t webapp -p "id=com.hotel.launcher" launcher-app

# 4. Develop with React + Vite
cd launcher-app
npm install
npm run dev

# 5. Build
npm run build

# 6. Package
ares-package dist/

# 7. Setup device (one time)
ares-setup-device
# Input TV IP, passphrase dari Developer Mode

# 8. Install to TV
ares-install --device tv com.hotel.launcher_1.0.0_all.ipk

# 9. Launch
ares-launch --device tv com.hotel.launcher

# 10. Debug/Inspect
ares-inspect --device tv com.hotel.launcher
```

**Server Development**
```bash
# 1. Clone project
git clone <repo-url>
cd project

# 2. Start all services
docker-compose up -d

# 3. Check services
docker-compose ps

# 4. Access services
# - Anthias: http://localhost:8080
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Web Admin: http://localhost:3000

# 5. View logs
docker-compose logs -f backend-api

# 6. Stop services
docker-compose down
```

---

## DOCKER COMPOSE STRUCTURE

```yaml
version: '3.8'

services:
  anthias:
    image: screenly/anthias:latest
    container_name: anthias
    ports:
      - "8080:80"
    volumes:
      - anthias-data:/data
    environment:
      - ANTHIAS_ENV=production
    restart: unless-stopped
    networks:
      - signage-network

  backend-api:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: backend-api
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - anthias
      - redis
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/signage_db
      - ANTHIAS_API_URL=http://anthias:80
      - FIREBIRD_API_URL=${FIREBIRD_API_URL}
      - FIREBIRD_API_KEY=${FIREBIRD_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - backend-uploads:/app/uploads
    restart: unless-stopped
    networks:
      - signage-network

  web-admin:
    build:
      context: ./web-admin
      dockerfile: Dockerfile
    container_name: web-admin
    ports:
      - "3000:80"
    depends_on:
      - backend-api
    environment:
      - VITE_API_URL=http://localhost:8000
    restart: unless-stopped
    networks:
      - signage-network

  postgres:
    image: postgres:15-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=signage_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - signage-network

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - signage-network

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend-api
      - web-admin
      - anthias
    restart: unless-stopped
    networks:
      - signage-network

volumes:
  anthias-data:
  postgres-data:
  redis-data:
  backend-uploads:

networks:
  signage-network:
    driver: bridge
```

---

## SECURITY CONSIDERATIONS

### **Backend API**
- JWT authentication untuk Web Admin
  - Access token (short-lived: 15 min)
  - Refresh token (long-lived: 7 days)
- API Key authentication untuk TV/Monitor clients
  - Device-specific keys
  - Rate limiting per device
- Password hashing: bcrypt
- CORS properly configured
  - Whitelist specific origins
- HTTPS in production (nginx reverse proxy)
- Input validation & sanitization
- SQL injection prevention (ORM parameterized queries)

### **TV/Monitor**
- Device-specific API keys (stored securely)
- Passphrase validation (TV)
- Unique code expiration (Monitor - expire after 10 min)
- HTTPS only communication
- No sensitive data stored on device

### **Firebird API**
- API key encrypted di database (Fernet encryption)
- Secure storage (environment variables)
- Rate limiting untuk prevent abuse
- Timeout untuk requests

### **Web Admin**
- Strong password policy
- Session management
- XSS prevention
- CSRF protection
- Role-based access control (RBAC)

### **File Upload**
- File type validation
- File size limits
- Virus scanning (optional: ClamAV)
- Unique filename generation
- Secure storage path

---

## NETWORK REQUIREMENTS

### **Server:**
- Static IP atau domain name
- Port 80/443 accessible dari TV/Monitor network
- Firewall rules: allow traffic from TV/Monitor IPs
- Minimum bandwidth: 10 Mbps upload
- Recommended: 100 Mbps untuk multiple devices

### **TV WebOS:**
- Connected to network (Ethernet recommended)
- Can access server IP/domain
- Developer Mode enabled (untuk install IPK)
- Minimum bandwidth: 5 Mbps download per TV
- Static IP recommended (atau DHCP reservation)

### **Monitor Browser:**
- Connected to network
- Modern browser (Chrome/Firefox/Edge latest version)
- Full screen support
- WebSocket support
- Minimum bandwidth: 5 Mbps download

---

## TESTING STRATEGY

### **Backend API:**
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/

# Coverage
pytest --cov=app tests/
```

**Test Coverage:**
- Unit tests: ≥80% code coverage
- API endpoint tests
- Database model tests
- Authentication tests
- Firebird API integration tests

### **WebOS TV:**
- Test on actual TV device (primary)
- Simulator testing (WebOS Emulator) - secondary
- Performance testing:
  - Memory usage monitoring
  - Smooth transitions validation
  - Network connectivity handling
- Edge cases:
  - No internet connection
  - Server unreachable
  - Corrupted content

### **Web Admin:**
```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e
```

**Test Coverage:**
- Component tests: Jest + React Testing Library
- E2E tests: Playwright atau Cypress
- Accessibility tests (a11y)

### **Monitor Browser:**
- Cross-browser testing (Chrome, Firefox, Edge)
- Full screen mode validation
- WebSocket reconnection testing
- Long-running stability tests

---

## DEPLOYMENT CHECKLIST

### **Initial Setup:**
- [ ] Setup server (VPS/Cloud/On-premise)
- [ ] Install Docker + Docker Compose
- [ ] Clone repository
- [ ] Configure environment variables (.env file)
- [ ] Generate SSL certificates (Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Run `docker-compose up -d`
- [ ] Verify all services running
- [ ] Create admin user account
- [ ] Test Firebird API connection
- [ ] Upload test content ke Anthias

### **TV Setup (per device):**
- [ ] Enable Developer Mode di TV
- [ ] Get passphrase dari Developer Mode App
- [ ] Note IP address TV (set static IP)
- [ ] Register TV di Web Admin
- [ ] Build & package IPK app
- [ ] Install IPK ke TV via Ares CLI
- [ ] Launch app & verify connection
- [ ] Test content display
- [ ] Test smooth transitions
- [ ] Monitor logs untuk errors

### **Monitor Setup (per device):**
- [ ] Buka browser ke viewer URL
- [ ] Note activation code
- [ ] Activate di Web Admin
- [ ] Assign tags/groups
- [ ] Set full screen mode
- [ ] Verify content display
- [ ] Test auto-refresh
- [ ] Configure browser auto-start (optional)

### **Production Deployment:**
- [ ] Setup HTTPS/SSL
- [ ] Configure reverse proxy (Nginx)
- [ ] Setup automatic backups
- [ ] Configure monitoring (uptime, logs)
- [ ] Setup alerting (email/SMS)
- [ ] Document admin procedures
- [ ] Train admin users
- [ ] Create disaster recovery plan

---

## MAINTENANCE & MONITORING

### **Logging:**
```
Backend API:
- Request/response logs
- Error logs (with stack traces)
- Authentication attempts
- Database queries (slow queries)
- External API calls (Firebird, Anthias)

TV/Monitor:
- Connection status
- Content playback logs
- Error logs
- Performance metrics

Centralized Logging (Optional):
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
```

### **Monitoring Metrics:**
```
System Health:
- CPU usage
- Memory usage
- Disk space
- Network bandwidth

Application Metrics:
- API response times
- Database query performance
- Cache hit rates
- WebSocket connections

Device Metrics:
- Online/offline status
- Last heartbeat timestamp
- Content delivery success rate
- Error frequency

Content Metrics:
- Total content count
- Storage usage
- Popular content (view counts)
```

### **Backup Strategy:**
```
Daily:
- Database backup (automated)
- Incremental backups

Weekly:
- Anthias content backup (full)
- Configuration backup

Monthly:
- Full system backup
- Off-site backup storage

Retention:
- Daily: 7 days
- Weekly: 4 weeks
- Monthly: 12 months
```

### **Update & Maintenance Schedule:**
```
Daily:
- Check monitoring dashboards
- Review error logs

Weekly:
- Security updates (OS, Docker images)
- Check disk space
- Review performance metrics

Monthly:
- Dependency updates
- Database optimization (VACUUM, ANALYZE)
- Content cleanup (unused/expired)
- Review user access

Quarterly:
- Security audit
- Performance review
- Backup restore testing
- Disaster recovery drill
```

---

## TROUBLESHOOTING GUIDE

### **TV Cannot Connect to Backend**
```
Symptoms:
- TV shows connection error
- Content not loading

Diagnosis:
1. Check TV internet connection
2. Ping server from TV network
3. Check firewall rules
4. Verify backend API is running
5. Check device registration status

Solutions:
- Reset network settings
- Re-register device
- Check API URL configuration
- Verify passphrase matches
```

### **Monitor Code Not Activating**
```
Symptoms:
- Code entered but not activating
- Code expired message

Diagnosis:
1. Check code in database (status, expiry)
2. Verify admin input code correctly
3. Check backend logs

Solutions:
- Generate new code
- Check system time sync
- Verify database connectivity
```

### **Content Not Displaying**
```
Symptoms:
- Black screen on TV/Monitor
- Old content still showing

Diagnosis:
1. Check playlist API response
2. Verify content URLs accessible
3. Check Anthias service status
4. Review content assignments

Solutions:
- Verify content is assigned to device
- Check schedule active
- Restart Anthias service
- Clear device cache
```

### **Smooth Transitions Not Working**
```
Symptoms:
- Content jumps/flickers
- Laggy transitions

Diagnosis:
1. Check TV/Monitor resources (CPU, memory)
2. Verify preloading working
3. Check network bandwidth
4. Review browser console errors

Solutions:
- Optimize content file sizes
- Reduce transition duration
- Enable hardware acceleration
- Update browser/TV firmware
```

---

## PERFORMANCE OPTIMIZATION

### **Backend API**
```
1. Database:
   - Index frequently queried columns
   - Use connection pooling
   - Query optimization (EXPLAIN ANALYZE)
   - Cache frequently accessed data (Redis)

2. API:
   - Response compression (gzip)
   - Rate limiting
   - Async processing (Celery)
   - CDN for static files

3. Caching Strategy:
   - Device playlist: 5 minutes
   - Guest info: 5 minutes
   - Content metadata: 15 minutes
   - Invalidate on update
```

### **WebOS TV App**
```
1. Memory Management:
   - Limit cached content (max 3 items)
   - Clean up old resources
   - Monitor memory usage

2. Network:
   - Minimize API calls
   - Use WebSocket for updates
   - Implement retry logic

3. Rendering:
   - Hardware acceleration
   - Optimize image sizes
   - Use video codecs supported by TV
```

### **Monitor Browser**
```
1. Browser Performance:
   - Service Worker for offline support
   - Lazy loading images
   - Debounce window resize

2. Memory:
   - Clear old content from DOM
   - Limit history/cache
```

### **Content Optimization**
```
Images:
- Format: JPEG (photos), PNG (graphics)
- Resolution: 1920x1080 (1080p), 3840x2160 (4K)
- Compression: 80-85% quality
- Max size: 2MB per image

Videos:
- Codec: H.264 (widely supported)
- Resolution: Match TV native
- Bitrate: 5-10 Mbps (1080p), 15-25 Mbps (4K)
- Max duration: 60 seconds per clip
- Max size: 100MB per video
```

---

## FUTURE ENHANCEMENTS (Optional)

### **Phase 2 Features:**
1. **Analytics Dashboard**
   - Content view counts
   - Device uptime statistics
   - Popular content reports
   - User activity logs
   - Export reports (PDF, CSV)

2. **Advanced Scheduling**
   - Conditional display (weather-based)
   - Date-based campaigns
   - Holiday schedules
   - A/B testing content
   - Priority-based scheduling

3. **Content Editor**
   - Built-in image editor
   - Text overlay tool
   - Template library
   - Drag-and-drop builder

### **Phase 3 Features:**
4. **Multi-zone Display**
   - Split screen support (2x2, 3x3 grid)
   - Picture-in-picture
   - Ticker/scrolling text
   - Video walls (multiple TVs)

5. **Mobile App**
   - iOS/Android untuk manage on-the-go
   - Push notifications
   - Quick content upload
   - Device status monitoring

6. **AI Integration**
   - Auto-generate content dari data
   - Smart scheduling based on patterns
   - Content recommendation
   - Anomaly detection

### **Phase 4 Features:**
7. **Interactive Features**
   - Touch screen support (for kiosks)
   - QR code display
   - Social media integration
   - Real-time polls/surveys

8. **Advanced Analytics**
   - Audience measurement (camera-based)
   - Heatmaps
   - Engagement metrics
   - ROI tracking

---

## COST ESTIMATION

### **Infrastructure (Monthly)**
```
Cloud Server (VPS):
- 4 vCPU, 8GB RAM, 100GB SSD
- Cost: $40-80/month

Or On-Premise:
- Server hardware: $1000-2000 (one-time)
- Electricity: ~$20/month

Domain & SSL:
- Domain: $10-15/year
- SSL (Let's Encrypt): Free

Total Monthly: $40-100 (cloud) or $20 (on-premise after initial)
```

### **Development (One-time)**
```
Estimated hours:
- Backend API: 120-160 hours
- WebOS TV App: 100-120 hours
- Web Admin: 80-100 hours
- Integration & Testing: 60-80 hours
- Documentation: 20-30 hours

Total: 380-490 hours

At $50/hour: $19,000-24,500
At $100/hour: $38,000-49,000

DIY (your time): 3-4 months full-time
```

### **Hardware (Per Location)**
```
Smart TV: Already owned
OR
Monitor + Media Player (Raspberry Pi): $150-300
```

---

## PROJECT TIMELINE

### **Phase 1: Foundation (Weeks 1-4)**
Week 1:
- Project setup
- Docker environment
- Database schema
- Basic backend API structure

Week 2:
- Authentication system
- Device management API
- Content management API

Week 3:
- Anthias integration
- Firebird API integration
- WebSocket implementation

Week 4:
- Testing & bug fixes
- API documentation

### **Phase 2: Frontend Development (Weeks 5-8)**
Week 5-6:
- Web Admin UI development
- Device management pages
- Content management pages

Week 7-8:
- Scheduling interface
- Tag management
- Settings & configuration

### **Phase 3: WebOS App Development (Weeks 9-12)**
Week 9-10:
- WebOS app structure
- Content player implementation
- Smooth transitions

Week 11-12:
- API integration
- Testing on actual TV
- Performance optimization

### **Phase 4: Monitor Viewer (Weeks 13-14)**
Week 13:
- Browser viewer development
- Full screen implementation
- Activation flow

Week 14:
- Testing across browsers
- Optimization

### **Phase 5: Integration & Testing (Weeks 15-16)**
Week 15:
- End-to-end testing
- Security audit
- Performance testing

Week 16:
- Bug fixes
- Documentation
- Deployment preparation

### **Total: 16 weeks (4 months)**

---

## GLOSSARY

- **Ares CLI**: WebOS command-line tool untuk develop/package/deploy aplikasi
- **IPK**: WebOS application package format (seperti APK di Android)
- **Anthias**: Open source digital signage platform (formerly Screenly OSE)
- **Passphrase**: 6-digit code dari WebOS Developer Mode App untuk pairing
- **Firebird**: SQL database server (bukan Firebase yang cloud-based!)
- **Signage/Signate**: Digital signage (papan informasi digital)
- **Smooth Transitions**: Perpindahan konten tanpa "flicker" atau lag
- **Device Tagging**: Grouping devices untuk content assignment
- **Playlist**: Urutan content yang akan ditampilkan di device
- **Heartbeat**: Periodic ping dari device ke server untuk monitoring
- **WebSocket**: Two-way communication protocol untuk real-time updates
- **JWT**: JSON Web Token untuk authentication
- **CORS**: Cross-Origin Resource Sharing untuk security
- **ORM**: Object-Relational Mapping (SQLAlchemy)
- **CDN**: Content Delivery Network untuk fast content delivery

---

## REFERENCES & DOCUMENTATION

### **Official Documentation:**
- WebOS TV Developer: https://webostv.developer.lge.com/
- Ares CLI User Guide: https://webostv.developer.lge.com/develop/tools/cli-dev-guide
- Anthias GitHub: https://github.com/Screenly/Anthias
- Anthias Documentation: https://anthias.screenly.io/
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- SQLAlchemy: https://www.sqlalchemy.org/

### **Useful Resources:**
- WebOS Developer Forum: https://forum.developer.lge.com/
- Anthias Community: https://forums.screenly.io/
- Docker Documentation: https://docs.docker.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

---

## SUPPORT & CONTACT

### **For Technical Issues:**
- Backend API: Check logs via `docker-compose logs backend-api`
- WebOS TV: Check TV logs via Ares CLI inspect
- Database: Check PostgreSQL logs
- Anthias: Check Anthias logs

### **Community Support:**
- WebOS Developer Community
- Anthias Forums
- Stack Overflow (tag: webos, anthias, fastapi)

---

**Document Version:** 1.0  
**Last Updated:** October 21, 2025  
**Author:** System Architecture Documentation  
**Status:** Final for Development

---

## APPENDIX A: Example Configuration Files

### **1. Backend .env File**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/signage_db

# Anthias
ANTHIAS_API_URL=http://localhost:8080
ANTHIAS_API_KEY=your-anthias-api-key

# Firebird
FIREBIRD_API_URL=https://external-firebird-api.com
FIREBIRD_API_KEY=your-firebird-api-key
FIREBIRD_REFRESH_INTERVAL=300

# Security
JWT_SECRET=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100

# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

### **2. WebOS TV App Config**
```javascript
// config.js
export const config = {
  apiBaseUrl: 'http://192.168.1.50:8000/api',
  wsUrl: 'ws://192.168.1.50:8000/ws',
  devicePassphrase: 'ABC123', // From Developer Mode
  refreshInterval: 60000, // 1 minute
  heartbeatInterval: 30000, // 30 seconds
  transitionDuration: 1000, // 1 second
  preloadOffset: 3000, // 3 seconds before end
};
```

### **3. Nginx Reverse Proxy Config**
```nginx
upstream backend {
    server backend-api:8000;
}

upstream anthias {
    server anthias:80;
}

upstream web-admin {
    server web-admin:80;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Backend API
    location /api/ {
        proxy_pass http://backend/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://backend/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # Anthias
    location /anthias/ {
        proxy_pass http://anthias/;
        proxy_set_header Host $host;
    }
    
    # Web Admin
    location / {
        proxy_pass http://web-admin/;
        proxy_set_header Host $host;
    }
}
```

---

## APPENDIX B: Example API Responses

### **Get Playlist Response**
```json
{
  "device_id": "123e4567-e89b-12d3-a456-426614174000",
  "device_name": "TV Lobby",
  "playlist": [
    {
      "content_id": 1,
      "title": "Promo Banner 1",
      "type": "image",
      "url": "http://192.168.1.50:8080/asset/banner1.jpg",
      "duration": 10,
      "order": 1
    },
    {
      "content_id": 2,
      "title": "Welcome Video",
      "type": "video",
      "url": "http://192.168.1.50:8080/asset/welcome.mp4",
      "duration": 30,
      "order": 2
    }
  ],
  "total_duration": 40,
  "last_updated": "2025-10-21T10:30:00Z"
}
```

### **Get Guest Info Response**
```json
{
  "last_updated": "2025-10-21T10:30:00Z",
  "total_guests": 15,
  "guests": [
    {
      "name": "John Doe",
      "room": "101",
      "check_in": "2025-10-20",
      "check_out": "2025-10-25",
      "status": "checked_in"
    },
    {
      "name": "Jane Smith",
      "room": "205",
      "check_in": "2025-10-21",
      "check_out": "2025-10-23",
      "status": "checked_in"
    }
  ]
}
```

---

**END OF DOCUMENTATION**
