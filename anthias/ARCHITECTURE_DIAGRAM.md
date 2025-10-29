# Anthias Minimal Storage Service - Architecture

## Before & After Comparison

### Before Migration: Monolithic Anthias

```
┌─────────────────────────────────────────────────────────────────┐
│                     ANTHIAS (Monolith - 7,697 LOC)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Web Application                       │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐ │   │
│  │  │  Viewer  │ Web UI   │  REST    │   Admin Panel    │ │   │
│  │  │  Player  │ (Django) │  API     │   (Django)       │ │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Business Logic                         │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐ │   │
│  │  │Scheduler │ Playlist │  Device  │   Authentication │ │   │
│  │  │  Logic   │ Manager  │ Manager  │   & Auth        │ │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Background Jobs                        │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐ │   │
│  │  │  Celery  │  Redis   │ ZMQ      │   WebSocket      │ │   │
│  │  │  Tasks   │  Cache   │ Messages │   Server         │ │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Data Layer                            │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────────┐ │   │
│  │  │ SQLite   │  File    │ Platform │   Hardware       │ │   │
│  │  │ Database │ Storage  │ Control  │   Control        │ │   │
│  │  └──────────┴──────────┴──────────┴──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Dependencies: 38 packages                                      │
│  Size: 3.8 MB                                                   │
│  Startup: ~5 seconds                                            │
│  Memory: ~200 MB                                                │
└─────────────────────────────────────────────────────────────────┘
```

### After Migration: Microservices Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DIGITAL SIGNAGE SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐                                                    │
│  │   Web Admin     │   React + Vite (TypeScript)                       │
│  │   (Port 3000)   │   • Content Management                            │
│  │                 │   • Device Management                              │
│  │   500+ files    │   • Playlist Management                           │
│  │   TypeScript    │   • Analytics Dashboard                           │
│  └────────┬────────┘                                                    │
│           │ HTTP/REST                                                    │
│           ▼                                                              │
│  ┌─────────────────┐                                                    │
│  │    Backend      │   FastAPI (Python)                                │
│  │   (Port 8001)   │   • Business Logic                                │
│  │                 │   • Authentication                                 │
│  │   50+ files     │   • Scheduling System                             │
│  │   15,000+ LOC   │   • Playlist Engine         ┌──────────────────┐ │
│  │                 │   • Device Management       │   PostgreSQL     │ │
│  │                 │   • Content Metadata   ────▶│   (Port 5433)    │ │
│  │                 │   • Analytics & Reports     │                  │ │
│  │                 │   • Translation System      │  • Content       │ │
│  │                 │   • Template Engine         │  • Playlists     │ │
│  │                 │   • Command System          │  • Devices       │ │
│  │                 │   • Widget Management       │  • Users         │ │
│  └────────┬────────┘                             │  • Analytics     │ │
│           │ HTTP/REST                            └──────────────────┘ │
│           ▼                                                              │
│  ┌─────────────────┐                                                    │
│  │    Anthias      │   Django (Python) - MINIMAL                       │
│  │   Storage       │   • File Upload                                   │
│  │   (Port 8000)   │   • File Serving                                  │
│  │                 │   • File Deletion                                 │
│  │   15 files      │   • MD5 Calculation          ┌──────────────────┐ │
│  │   840 LOC       │                              │   SQLite         │ │
│  │                 │   Dependencies: 3       ────▶│   (Minimal)      │ │
│  │                 │   Size: 265 KB               │                  │ │
│  │                 │   Startup: ~1 second         │  • Asset refs    │ │
│  │                 │   Memory: ~50 MB             └──────────────────┘ │
│  └────────┬────────┘                                                    │
│           │ File I/O                                                    │
│           ▼                                                              │
│  ┌─────────────────┐                                                    │
│  │  File Storage   │   Local Filesystem                                │
│  │  /data/         │   • Videos                                        │
│  │                 │   • Images                                        │
│  │                 │   • Web content                                   │
│  └─────────────────┘                                                    │
│                                                                          │
│  ┌─────────────────┐                                                    │
│  │    Viewer       │   Static HTML/JavaScript                          │
│  │   (Port 8080)   │   • Content Playback                              │
│  │                 │   • Device Registration                           │
│  │   30+ files     │   • Heartbeat                                     │
│  │   JavaScript    │   • Command Execution                             │
│  └────────┬────────┘                                                    │
│           │ HTTP/REST                                                    │
│           └──────────────────────────▶ Backend                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. Web Admin (React + TypeScript)
```
┌────────────────────────────────────────┐
│         Web Admin Frontend             │
├────────────────────────────────────────┤
│ • User Interface                       │
│ • Content Upload Forms                 │
│ • Playlist Management UI               │
│ • Device Management UI                 │
│ • Analytics Dashboard                  │
│ • Template Management                  │
│ • Translation Management               │
│ • Real-time Updates (WebSocket)        │
│                                        │
│ Technology: React + Vite + TypeScript  │
│ Port: 3000 (dev), Static build (prod) │
│ API Calls: Backend (port 8001)        │
└────────────────────────────────────────┘
```

### 2. Backend API (FastAPI)
```
┌────────────────────────────────────────┐
│         Backend API (FastAPI)          │
├────────────────────────────────────────┤
│ Business Logic:                        │
│ • Authentication & Authorization       │
│ • Content Metadata Management          │
│ • Playlist Management                  │
│ • Scheduling System                    │
│ • Device Management                    │
│ • Analytics & Reports                  │
│ • Translation System                   │
│ • Template Engine                      │
│ • Command System                       │
│ • Widget Management                    │
│                                        │
│ Data Storage:                          │
│ • PostgreSQL (metadata)                │
│ • Redis (cache, optional)              │
│                                        │
│ External Calls:                        │
│ • Anthias Storage (file operations)   │
│                                        │
│ Technology: FastAPI + PostgreSQL       │
│ Port: 8001                            │
└────────────────────────────────────────┘
```

### 3. Anthias Storage (Django Minimal)
```
┌────────────────────────────────────────┐
│      Anthias Storage Service           │
├────────────────────────────────────────┤
│ File Operations:                       │
│ • POST   /api/storage/upload           │
│ • GET    /api/storage/serve/{id}       │
│ • GET    /api/storage/{id}             │
│ • DELETE /api/storage/delete/{id}      │
│ • GET    /api/storage/health           │
│                                        │
│ Functions:                             │
│ • Upload file to /data/                │
│ • Calculate MD5 checksum               │
│ • Serve file content                   │
│ • Delete file from disk                │
│ • Store minimal metadata (SQLite)      │
│                                        │
│ NO Business Logic:                     │
│ ✗ No scheduling                        │
│ ✗ No playlists                         │
│ ✗ No authentication                    │
│ ✗ No device management                 │
│                                        │
│ Technology: Django (minimal)           │
│ Port: 8000                            │
│ Dependencies: 3 packages               │
│ Size: 265 KB                          │
└────────────────────────────────────────┘
```

### 4. Viewer (Static HTML/JS)
```
┌────────────────────────────────────────┐
│         Viewer (HTML/JavaScript)       │
├────────────────────────────────────────┤
│ Display Functions:                     │
│ • Content Playback (video, image, web) │
│ • HLS Streaming                        │
│ • Multi-language UI                    │
│ • Offline Mode                         │
│                                        │
│ Device Functions:                      │
│ • 6-digit Activation Code              │
│ • Device Registration                  │
│ • Heartbeat (every 30s)                │
│ • Command Execution                    │
│ • Analytics Tracking                   │
│                                        │
│ Technology: Vanilla JavaScript         │
│ Port: 8080                            │
│ API Calls: Backend (port 8001)        │
└────────────────────────────────────────┘
```

## Data Flow

### Content Upload Flow
```
1. Web Admin (Upload Form)
   │
   │ POST /api/content/upload
   ▼
2. Backend (FastAPI)
   │ • Validate user permissions
   │ • Validate file type/size
   │
   │ POST /api/storage/upload (multipart)
   ▼
3. Anthias Storage
   │ • Save file to /data/screenly_assets/
   │ • Calculate MD5
   │ • Store file reference in SQLite
   │
   │ Return: {asset_id, uri, md5, size, mimetype}
   ▼
4. Backend (FastAPI)
   │ • Store metadata in PostgreSQL
   │ • Link to playlists/schedules
   │
   │ Return: {content_id, status, url}
   ▼
5. Web Admin
   │ • Show success message
   │ • Update content list
```

### Content Playback Flow
```
1. Viewer (Player)
   │
   │ GET /api/devices/{device_id}/playlist
   ▼
2. Backend (FastAPI)
   │ • Check current schedule
   │ • Get active playlist
   │ • Get content list with metadata
   │
   │ Return: [{content_id, asset_id, duration, ...}]
   ▼
3. Viewer (Player)
   │ • For each content item:
   │
   │ GET /api/storage/serve/{asset_id}
   ▼
4. Anthias Storage
   │ • Read file from /data/screenly_assets/
   │ • Stream file content
   │
   │ Return: File content (video/image/html)
   ▼
5. Viewer (Player)
   │ • Display content
   │ • Track playback analytics
```

## API Request Flow

```
┌─────────────┐
│  Web Admin  │
│  (Port 3000)│
└──────┬──────┘
       │
       │ All API requests
       ▼
┌─────────────────────────────────────────────┐
│           Backend API (Port 8001)           │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │     Business Logic Layer             │  │
│  │  • Authentication                    │  │
│  │  • Authorization                     │  │
│  │  • Validation                        │  │
│  │  • Scheduling                        │  │
│  │  • Playlist Management               │  │
│  └──────────────────────────────────────┘  │
│             │               │               │
│             │               │               │
│             ▼               ▼               │
│  ┌──────────────┐   ┌──────────────┐      │
│  │  PostgreSQL  │   │   Anthias    │      │
│  │  (Metadata)  │   │   Storage    │      │
│  │              │   │ (File Ops)   │      │
│  │  • Content   │   │              │      │
│  │  • Playlists │   │ POST /upload │      │
│  │  • Devices   │   │ GET  /serve  │      │
│  │  • Users     │   │ DELETE /del  │      │
│  │  • Analytics │   │              │      │
│  └──────────────┘   └──────────────┘      │
│                                             │
└─────────────────────────────────────────────┘
                    │
                    │ Only file URLs
                    ▼
              ┌─────────────┐
              │   Viewer    │
              │  (Port 8080)│
              └─────────────┘
```

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Server: 192.168.5.12                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Docker Network: signage-network               │    │
│  │                                                 │    │
│  │  ┌──────────────┐      ┌──────────────┐       │    │
│  │  │   Backend    │      │  PostgreSQL  │       │    │
│  │  │ Container    │─────▶│  Container   │       │    │
│  │  │ Port: 8001   │      │  Port: 5433  │       │    │
│  │  └──────┬───────┘      └──────────────┘       │    │
│  │         │                                       │    │
│  │         │ HTTP                                  │    │
│  │         ▼                                       │    │
│  │  ┌──────────────┐                              │    │
│  │  │   Anthias    │                              │    │
│  │  │   Storage    │                              │    │
│  │  │ Port: 8000   │                              │    │
│  │  └──────────────┘                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Static Web Servers (Nginx)                    │    │
│  │                                                 │    │
│  │  ┌──────────────┐                              │    │
│  │  │   Viewer     │   Static HTML/JS             │    │
│  │  │ Port: 8080   │   For TVs/Monitors          │    │
│  │  └──────────────┘                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Development Server                             │    │
│  │                                                 │    │
│  │  ┌──────────────┐                              │    │
│  │  │  Web Admin   │   Vite Dev Server            │    │
│  │  │ Port: 3000   │   (or static build)         │    │
│  │  └──────────────┘                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  File Storage                                   │    │
│  │  /data/screenly_assets/                        │    │
│  │  • Videos                                       │    │
│  │  • Images                                       │    │
│  │  • Web Content                                  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Summary

### Key Architectural Changes

1. **Separation of Concerns**
   - Web Admin → User Interface
   - Backend → Business Logic
   - Anthias → File Storage
   - Viewer → Content Display

2. **Single Responsibility**
   - Each component has ONE clear purpose
   - No code duplication
   - Clear API boundaries

3. **Scalability**
   - Components can scale independently
   - Backend can handle multiple Anthias instances
   - File storage can be moved to CDN/S3

4. **Maintainability**
   - Small, focused codebases
   - Clear dependencies
   - Easy to understand and modify

5. **Performance**
   - Fast startup times
   - Low memory usage
   - Efficient file serving
   - Minimal overhead
