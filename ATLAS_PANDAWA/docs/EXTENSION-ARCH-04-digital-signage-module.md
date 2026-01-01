# ARCH-04: Digital Signage Module Architecture

> Arsitektur multi-platform untuk digital signage player yang stabil 24/7, offline-capable, dan production-ready

**Related Documents:**
- [ARCH-02: Module Architecture](./ARCH-02-module-architecture.md) - General module architecture
- [ARCH-03: Puzzle Architecture](./ARCH-03-puzzle-architecture.md) - Module composition
- [STD-17: Logging & Observability](./STD-17-logging-observability.md) - Logging standards

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Principles](#2-architecture-principles)
3. [System Architecture](#3-system-architecture)
4. [Platform Implementations](#4-platform-implementations)
5. [Offline Strategy](#5-offline-strategy)
6. [Backend Integration](#6-backend-integration)
7. [Device Management](#7-device-management)
8. [Content Management](#8-content-management)
9. [Monitoring & Health](#9-monitoring--health)
10. [Deployment & Updates](#10-deployment--updates)
11. [Best Practices](#11-best-practices)

---

## 1. Overview

### 1.1 Purpose

Digital Signage Module menyediakan platform untuk menampilkan konten dinamis di berbagai display devices (lobby screens, room info displays, menu boards, advertising displays) di hotel.

**Target Use Cases:**
- **Lobby Displays** - Welcome messages, hotel information, weather, events
- **Room Information** - Room availability, check-in/out times, services
- **F&B Menu Boards** - Restaurant menus, daily specials, promotions
- **Advertising Displays** - Partner ads, hotel promotions, local attractions
- **Emergency Messaging** - Safety information, evacuation routes, alerts

### 1.2 Goals

Membangun **player signage** yang:
- ✅ **Stabil 24/7** - No crashes, auto-recovery
- ✅ **Offline Deterministik** - Tetap berjalan tanpa internet
- ✅ **High Quality Video** - 1080p–4K (tergantung device)
- ✅ **Single Codebase** - One web player untuk semua platform
- ✅ **Multi-Platform** - Android, Windows, Linux, Web
- ✅ **Scalable** - Manage ratusan devices dari satu dashboard
- ✅ **Low Maintenance** - Auto-update, self-healing

**Non-Goals:**
- ❌ Bukan interactive kiosk (touch screen apps)
- ❌ Bukan video conferencing platform
- ❌ Bukan general-purpose web browser

---

## 2. Architecture Principles

### 2.1 Core Principles (Locked)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  DIGITAL SIGNAGE ARCHITECTURE PRINCIPLES                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  1. WEB PLAYER = OTAK (Logic & Rendering)                                 ║
║     • HTML/CSS/JS untuk UI dan playback logic                            ║
║     • Scheduling & timeline management                                   ║
║     • Single codebase untuk semua platform                               ║
║                                                                           ║
║  2. NATIVE HELPER = SISTEM SARAF (OS-Level Control)                       ║
║     • File system management (offline storage)                           ║
║     • Network detection & content sync                                   ║
║     • Watchdog & auto-restart                                            ║
║     • Auto-start on boot                                                 ║
║     • Device identity & registration                                     ║
║                                                                           ║
║  3. OFFLINE HANDLED BY NATIVE                                             ║
║     • Native downloads & stores content                                  ║
║     • Deterministic file access                                          ║
║     • Web cache is best-effort only                                      ║
║                                                                           ║
║  4. WEB BROWSER = NON-TRUSTED RUNTIME                                     ║
║     • Cannot be relied upon for production offline                       ║
║     • Only for preview/testing/emergency fallback                        ║
║                                                                           ║
║  5. CONSISTENCY > FRAMEWORK                                               ║
║     • Architecture consistency across platforms                          ║
║     • No framework hopping                                               ║
║     • Boring is better than clever                                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### 2.2 Why NOT Full Native?

**Arguments Against:**
- ❌ **Expensive maintenance** - Need separate codebases for Android, Windows, Linux
- ❌ **No quality improvement** - Chromium/WebView already hardware-accelerated
- ❌ **Longer development** - 3x effort untuk multi-platform
- ❌ **Harder updates** - Update 3 apps vs update 1 web app

**Only Consider Full Native If:**
- ✅ Heavy DRM requirements (protected content)
- ✅ 100% offline extreme scenarios (military, remote areas)
- ✅ Aggressive hardware control needs

### 2.3 Why NOT Flutter?

**Arguments Against:**
- ❌ **Doesn't solve core problems** - Offline, watchdog, auto-start still need native
- ❌ **Adds complexity** - Another layer without solving signage-specific issues
- ❌ **Not designed for signage** - Flutter optimized for UI apps, not 24/7 displays

**Flutter Good For:**
- Mobile apps with rich UI
- Desktop productivity apps
- Cross-platform consumer apps

**Flutter NOT Good For:**
- Digital signage players
- Kiosk systems
- Always-on display systems

### 2.4 The "Half-Native" Concept

**Not a compromise, but separation of responsibilities.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SEPARATION OF RESPONSIBILITIES                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WEB PLAYER (One codebase)                                              │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ • HTML/CSS/JavaScript                                          │    │
│  │ • React/Vue/Svelte (UI framework)                              │    │
│  │ • Scheduling & timeline logic                                  │    │
│  │ • Playback orchestration                                       │    │
│  │ • Content rendering                                            │    │
│  │ • Transition effects                                           │    │
│  │ • Layout management                                            │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  NATIVE HELPER (OS-specific)                                            │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ • IP & network detection                                       │    │
│  │ • Content download & sync                                      │    │
│  │ • Offline file storage (deterministic)                         │    │
│  │ • Local HTTP server (serve to WebView)                         │    │
│  │ • Watchdog monitoring                                          │    │
│  │ • Auto-restart on crash                                        │    │
│  │ • Auto-start on boot                                           │    │
│  │ • Device registration                                          │    │
│  │ • System health reporting                                      │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIGITAL SIGNAGE SYSTEM ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         ┌─────────────────┐                            │
│                         │  BACKEND (SaaS) │                            │
│                         ├─────────────────┤                            │
│                         │ • CMS API       │                            │
│                         │ • Content CDN   │                            │
│                         │ • Device Mgmt   │                            │
│                         │ • Analytics     │                            │
│                         └────────┬────────┘                            │
│                                  │                                      │
│                                  │ HTTPS / WebSocket                   │
│                                  │                                      │
│                    ┌─────────────┼─────────────┐                       │
│                    │             │             │                       │
│         ┌──────────▼─────┐  ┌───▼──────┐  ┌──▼─────────┐             │
│         │   Android      │  │ Windows  │  │   Linux    │             │
│         │   Device       │  │  Device  │  │   Device   │             │
│         └────────────────┘  └──────────┘  └────────────┘             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              DEVICE LAYER (Per Platform)                         │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐    │  │
│  │  │  WEB PLAYER (Single Codebase)                          │    │  │
│  │  │  ┌──────────────────────────────────────────────────┐  │    │  │
│  │  │  │ • Playlist Engine                                 │  │    │  │
│  │  │  │ • Video/Image Player                              │  │    │  │
│  │  │  │ • Scheduling Logic                                │  │    │  │
│  │  │  │ • Transition Manager                              │  │    │  │
│  │  │  │ • Layout Renderer                                 │  │    │  │
│  │  │  └──────────────────────────────────────────────────┘  │    │  │
│  │  └────────────────────────────────────────────────────────┘    │  │
│  │                              ▲                                  │  │
│  │                              │ HTTP (localhost)                 │  │
│  │                              │                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐    │  │
│  │  │  WEBVIEW / CHROMIUM ENGINE                             │    │  │
│  │  │  • Android: WebView                                    │    │  │
│  │  │  • Windows: WebView2 (Edge Chromium)                   │    │  │
│  │  │  • Linux: Chromium Kiosk Mode                          │    │  │
│  │  └────────────────────────────────────────────────────────┘    │  │
│  │                              ▲                                  │  │
│  │                              │ Bridge API                       │  │
│  │                              │                                  │  │
│  │  ┌────────────────────────────────────────────────────────┐    │  │
│  │  │  NATIVE HELPER (OS-Specific)                           │    │  │
│  │  │  ┌──────────────────────────────────────────────────┐  │    │  │
│  │  │  │ • HTTP Server (localhost:8080)                   │  │    │  │
│  │  │  │ • Content Downloader & Sync                      │  │    │  │
│  │  │  │ • File Storage Manager                           │  │    │  │
│  │  │  │ • Network Monitor                                │  │    │  │
│  │  │  │ • Watchdog Service                               │  │    │  │
│  │  │  │ • Health Reporter                                │  │    │  │
│  │  │  │ • Auto-start Manager                             │  │    │  │
│  │  │  └──────────────────────────────────────────────────┘  │    │  │
│  │  └────────────────────────────────────────────────────────┘    │  │
│  │                              │                                  │  │
│  └──────────────────────────────┼──────────────────────────────────┘  │
│                                  │                                      │
│                                  ▼                                      │
│                         ┌─────────────────┐                            │
│                         │  OS / HARDWARE  │                            │
│                         │  • File System  │                            │
│                         │  • Network      │                            │
│                         │  • Display      │                            │
│                         └─────────────────┘                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONTENT DELIVERY FLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CONTENT CREATION (CMS)                                              │
│     Admin uploads video/image → Backend CMS                             │
│                                                                         │
│  2. CONTENT PUBLISHING                                                  │
│     Admin assigns content to playlist → Publish to devices              │
│                                                                         │
│  3. DEVICE POLLING (Native Helper)                                      │
│     Every 5 min: Check for new content                                  │
│     GET /api/devices/{device_id}/playlist                               │
│                                                                         │
│  4. DOWNLOAD & CACHE (Native Helper)                                    │
│     If new content → Download to local storage                          │
│     /data/signage/content/{content_id}.mp4                              │
│                                                                         │
│  5. SERVE LOCALLY (Native Helper)                                       │
│     Start HTTP server on localhost:8080                                 │
│     Serve: http://localhost:8080/content/{content_id}                   │
│                                                                         │
│  6. PLAYBACK (Web Player)                                               │
│     Load from: http://localhost:8080/player                             │
│     Fetch playlist: http://localhost:8080/api/playlist                  │
│     Play video: http://localhost:8080/content/{content_id}.mp4          │
│                                                                         │
│  7. HEALTH REPORTING (Native Helper)                                    │
│     Every 1 min: Send heartbeat to backend                              │
│     POST /api/devices/{device_id}/health                                │
│     { status, disk_space, uptime, current_content }                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Platform Implementations

### 4.1 Android Implementation

**Target Devices:**
- Android TV boxes
- Tablet displays
- Android-based signage hardware

**Architecture:**
```kotlin
// MainActivity.kt - Android App
class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var nativeHelper: SignageHelper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Start native helper (background service)
        nativeHelper = SignageHelper(this)
        nativeHelper.startService()

        // Setup WebView
        webView = WebView(this)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
        }

        // Add bridge for native <-> web communication
        webView.addJavascriptInterface(
            WebAppInterface(this, nativeHelper),
            "Android"
        )

        // Load player from localhost
        webView.loadUrl("http://127.0.0.1:8080/player")

        setContentView(webView)

        // Make fullscreen
        enableFullscreen()
    }
}

// SignageHelper.kt - Native Helper Service
class SignageHelper(private val context: Context) {
    private val httpServer = LocalHttpServer(8080)
    private val contentSyncer = ContentSyncer(context)
    private val watchdog = WatchdogService(context)

    fun startService() {
        // Start HTTP server
        httpServer.start()

        // Start content sync (background)
        contentSyncer.startPeriodicSync(intervalMinutes = 5)

        // Start watchdog
        watchdog.monitor()

        // Register device
        registerDevice()
    }

    fun registerDevice() {
        // Get device ID (MAC address or Android ID)
        val deviceId = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ANDROID_ID
        )

        // Register with backend
        api.registerDevice(deviceId, "android")
    }
}
```

**Auto-Start:**
```xml
<!-- AndroidManifest.xml -->
<receiver android:name=".BootReceiver">
    <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED"/>
    </intent-filter>
</receiver>
```

**Offline Storage:**
```kotlin
// Store in app-specific directory
val contentDir = File(context.filesDir, "signage/content")
contentDir.mkdirs()

// Download content
fun downloadContent(contentId: String, url: String) {
    val file = File(contentDir, "$contentId.mp4")
    HttpClient.download(url, file)
}
```

---

### 4.2 Windows Implementation

**Target Devices:**
- Windows 10/11 PCs
- Windows-based signage displays
- Intel NUC / mini PCs

**Architecture:**
```csharp
// Program.cs - Windows App (.NET)
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

public class SignageApp : Form
{
    private WebView2 webView;
    private SignageHelper helper;

    public SignageApp()
    {
        // Initialize WebView2 (Edge Chromium)
        webView = new WebView2();
        webView.Dock = DockStyle.Fill;
        this.Controls.Add(webView);

        // Initialize native helper
        helper = new SignageHelper();
        helper.Start();

        // Setup WebView2
        InitializeAsync();

        // Fullscreen
        this.FormBorderStyle = FormBorderStyle.None;
        this.WindowState = FormWindowState.Maximized;
    }

    async void InitializeAsync()
    {
        await webView.EnsureCoreWebView2Async(null);

        // Add message channel for native <-> web communication
        webView.CoreWebView2.AddHostObjectToScript("native", helper);

        // Navigate to player
        webView.CoreWebView2.Navigate("http://127.0.0.1:8080/player");
    }

    static void Main()
    {
        Application.Run(new SignageApp());
    }
}

// SignageHelper.cs - Native Helper
public class SignageHelper
{
    private HttpServer httpServer;
    private ContentSyncer syncer;
    private WatchdogService watchdog;

    public void Start()
    {
        // Start HTTP server
        httpServer = new HttpServer(8080);
        httpServer.Start();

        // Start content sync
        syncer = new ContentSyncer();
        syncer.StartPeriodicSync(TimeSpan.FromMinutes(5));

        // Start watchdog
        watchdog = new WatchdogService();
        watchdog.Monitor();

        // Register device
        RegisterDevice();
    }

    private void RegisterDevice()
    {
        string deviceId = GetMachineGuid();
        API.RegisterDevice(deviceId, "windows");
    }
}
```

**Auto-Start (Windows Service):**
```csharp
// Install as Windows Service
sc create SignagePlayer binPath= "C:\SignagePlayer\SignagePlayer.exe"
sc config SignagePlayer start= auto
sc start SignagePlayer
```

**Or Task Scheduler:**
```powershell
# Create scheduled task to run on startup
$action = New-ScheduledTaskAction -Execute "C:\SignagePlayer\SignagePlayer.exe"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "SignagePlayer" -Action $action -Trigger $trigger -RunLevel Highest
```

**Offline Storage:**
```csharp
// Store in ProgramData
string contentDir = Path.Combine(
    Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
    "SignagePlayer", "content"
);
Directory.CreateDirectory(contentDir);
```

---

### 4.3 Linux Implementation

**Target Devices:**
- Raspberry Pi
- Ubuntu/Debian PCs
- Linux-based digital signage appliances

**Architecture:**
```python
# main.py - Linux Daemon
import subprocess
from http.server import HTTPServer
from signage.helper import SignageHelper

class SignageApp:
    def __init__(self):
        self.helper = SignageHelper()

    def start(self):
        # Start HTTP server
        self.helper.start_http_server(port=8080)

        # Start content sync
        self.helper.start_content_sync(interval_minutes=5)

        # Start watchdog
        self.helper.start_watchdog()

        # Register device
        self.helper.register_device()

        # Launch Chromium in kiosk mode
        self.launch_chromium()

    def launch_chromium(self):
        """Launch Chromium in fullscreen kiosk mode"""
        subprocess.Popen([
            'chromium-browser',
            '--kiosk',
            '--no-first-run',
            '--disable-infobars',
            '--disable-session-crashed-bubble',
            '--disable-translate',
            '--autoplay-policy=no-user-gesture-required',
            'http://127.0.0.1:8080/player'
        ])

if __name__ == '__main__':
    app = SignageApp()
    app.start()
```

**Auto-Start (systemd):**
```ini
# /etc/systemd/system/signage-player.service
[Unit]
Description=Digital Signage Player
After=network.target

[Service]
Type=simple
User=signage
WorkingDirectory=/opt/signage-player
ExecStart=/usr/bin/python3 /opt/signage-player/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable signage-player
sudo systemctl start signage-player
```

**Offline Storage:**
```python
# Store in /var/lib/signage
import os

content_dir = '/var/lib/signage/content'
os.makedirs(content_dir, exist_ok=True)

def download_content(content_id, url):
    filepath = os.path.join(content_dir, f'{content_id}.mp4')
    # Download logic
```

---

### 4.4 Web Browser (Emergency/Preview Only)

**Purpose:**
- Preview content sebelum publish
- Testing playlist
- Emergency fallback
- Demo untuk client

**Limitations:**
- ❌ NO offline guarantee (service worker best-effort)
- ❌ NO auto-start
- ❌ NO watchdog
- ❌ NOT production-ready
- ❌ NOT in SLA

**Implementation:**
```javascript
// Use service worker for caching (best-effort)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

// Show warning banner
if (window.location.hostname !== 'localhost') {
  showBanner('⚠️ Web mode is for preview only. Use native player for production.');
}
```

---

## 5. Offline Strategy

### 5.1 The Problem with Web-Only Offline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  WEB CACHE vs NATIVE FILE STORAGE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WEB CACHE (Service Worker / IndexedDB)                                 │
│  ❌ Best-effort only                                                    │
│  ❌ Can be cleared by OS anytime                                        │
│  ❌ Storage quota limits                                                │
│  ❌ Not deterministic                                                   │
│  ❌ Browser security restrictions                                       │
│  ➡️ NOT suitable for production signage                                │
│                                                                         │
│  NATIVE FILE STORAGE                                                    │
│  ✅ Deterministic file access                                           │
│  ✅ OS cannot arbitrarily delete                                        │
│  ✅ Full disk space control                                             │
│  ✅ Persistent across reboots                                           │
│  ✅ Can survive browser crashes                                         │
│  ➡️ PRODUCTION-READY for signage                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Offline Implementation

**Content Sync Strategy:**
```
1. Native helper polls backend every 5 minutes
2. If new playlist/content detected:
   - Download content to local filesystem
   - Verify integrity (checksum)
   - Update local playlist manifest
3. If network lost:
   - Continue serving from local filesystem
   - Log sync failures
   - Retry when network returns
```

**Local File Structure:**
```
/var/lib/signage/
├── content/
│   ├── video_abc123.mp4
│   ├── image_def456.jpg
│   └── widget_ghi789.html
├── playlists/
│   └── playlist_current.json
├── cache/
│   └── thumbnails/
└── logs/
    └── player.log
```

**Playlist Manifest:**
```json
{
  "playlist_id": "pl_abc123",
  "version": 15,
  "updated_at": "2024-12-23T10:00:00Z",
  "items": [
    {
      "content_id": "video_abc123",
      "type": "video",
      "duration": 30,
      "local_path": "/content/video_abc123.mp4",
      "checksum": "sha256:abc..."
    },
    {
      "content_id": "image_def456",
      "type": "image",
      "duration": 10,
      "local_path": "/content/image_def456.jpg",
      "checksum": "sha256:def..."
    }
  ],
  "schedule": {
    "default": "loop",
    "overrides": []
  }
}
```

---

## 5.5 Data Model & Tenant Isolation (CRITICAL)

All signage entities must enforce strict multi-tenant isolation per CORE-REF-01:

### Device Entity

```typescript
interface Device {
  id: UUID;                          // PK
  tenant_id: UUID;                   // FK→Tenant (REQUIRED - multi-tenant isolation)
  device_id: string;                 // Unique device identifier (MAC, Android ID, etc.)
  name: string;                      // Display name ("Lobby Screen 1", "Room 101 TV")
  platform: ENUM;                    // 'android', 'windows', 'linux', 'web'
  location: string;                  // Physical location
  status: ENUM;                      // 'online', 'offline', 'error'
  last_seen_at: timestamp;
  created_at: timestamp;
  deleted_at: timestamp;             // Soft delete
}

// UNIQUE CONSTRAINT: (tenant_id, device_id)
// - One device_id per tenant
// - Different tenants can have device "device_abc" independently

// ALL QUERIES: WHERE tenant_id = $1
```

### Playlist Entity

```typescript
interface Playlist {
  id: UUID;                          // PK
  tenant_id: UUID;                   // FK→Tenant (REQUIRED - multi-tenant isolation)
  name: string;                      // "Lobby Rotation", "Emergency Messages"
  content_items: PlaylistItem[];
  schedule: PlaylistSchedule[];
  is_active: boolean;
  created_at: timestamp;
  updated_at: timestamp;
  deleted_at: timestamp;             // Soft delete
}

// UNIQUE CONSTRAINT: (tenant_id, name)
// - One playlist name per tenant

// ALL QUERIES: WHERE tenant_id = $1
```

### PlaylistItem Entity

```typescript
interface PlaylistItem {
  id: UUID;                          // PK
  playlist_id: UUID;                 // FK→Playlist
  tenant_id: UUID;                   // FK→Tenant (DENORMALIZED for query efficiency)
  content_id: UUID;                  // FK→Content
  sequence_number: int;              // Order in playlist
  duration_seconds: int;             // How long to show
  transition: string;                // Fade, slide, etc.
  created_at: timestamp;
}

// INDEX: (tenant_id, playlist_id, sequence_number)
// ALL QUERIES: WHERE tenant_id = $1
```

### Content Entity

```typescript
interface Content {
  id: UUID;                          // PK
  tenant_id: UUID;                   // FK→Tenant (REQUIRED - multi-tenant isolation)
  name: string;                      // "Hotel Logo", "Beach Video", "Weather Widget"
  type: ENUM;                        // 'video', 'image', 'html', 'livestream'
  file_path: string;                 // S3 path
  file_size_mb: decimal;
  duration_seconds: int;             // For videos
  is_active: boolean;
  created_by: UUID;                  // User ID
  created_at: timestamp;
  deleted_at: timestamp;             // Soft delete
}

// UNIQUE CONSTRAINT: (tenant_id, name)
// - One content name per tenant

// ALL QUERIES: WHERE tenant_id = $1
```

### DevicePlaylistAssignment Entity

```typescript
interface DevicePlaylistAssignment {
  id: UUID;                          // PK
  tenant_id: UUID;                   // FK→Tenant (REQUIRED - multi-tenant isolation)
  device_id: UUID;                   // FK→Device
  playlist_id: UUID;                 // FK→Playlist
  assigned_at: timestamp;
  updated_at: timestamp;
  deleted_at: timestamp;             // Soft delete (unassign)
}

// UNIQUE CONSTRAINT: (tenant_id, device_id)
// - One active playlist per device per tenant

// ALL QUERIES: WHERE tenant_id = $1
```

### Tenant Isolation Rules (LOCKED)

**Rule 1: ALL queries must include tenant_id**
```sql
-- ✅ CORRECT
SELECT * FROM devices WHERE tenant_id = $1 AND device_id = $2;

-- ❌ WRONG - missing tenant_id filter
SELECT * FROM devices WHERE device_id = $1;
```

**Rule 2: Denormalize tenant_id where needed for performance**
- Don't require JOINs to filter by tenant
- PlaylistItem has tenant_id (even though FK to Playlist which has it)
- Enables efficient filtering without table joins

**Rule 3: No Cross-Tenant Foreign Keys**
```
-- ❌ WRONG: Device from tenant A referencing Playlist from tenant B
device (tenant_id=hotel-123) → playlist (tenant_id=hotel-456)

-- ✅ CORRECT: All entities from same tenant
device (tenant_id=hotel-123) → playlist (tenant_id=hotel-123)
```

**Rule 4: Soft Delete for Audit Trail**
- Never physically delete devices, playlists, or content
- Always use soft delete (set deleted_at)
- Preserves history for compliance and auditing

### CRITICAL GUARDRAIL - Device Registration & Authentication

```
RULE: Device must authenticate as belonging to specific tenant
RULE: Device token scoped to single tenant (cannot access other tenants' content)
RULE: Device registration requires valid tenant context
```

**Implementation**:
- Device registration endpoint requires:
  - tenant_id from JWT claims (from authenticated user)
  - device_id (unique within tenant, not globally)
  - platform, os_version, app_version (for version management)
- Device is associated with registration tenant only
- All subsequent API calls must include device_id + jwt_token
- JWT token contains: { tenant_id, device_id, permissions: ['read-playlists'] }
- Token validation checks:
  1. JWT signature valid
  2. tenant_id matches device.tenant_id
  3. device_id matches device.id
  4. Token not expired
- **Prevents**: Device from one tenant accessing another tenant's content
- **Prevents**: Impersonation attacks (device claiming different tenant)

### CRITICAL GUARDRAIL - Playlist Version Management & Content Freshness

```
RULE: Devices must verify playlist version before displaying
RULE: Content delivery uses checksums for integrity verification
RULE: Failed downloads must retry or fallback to cached content
```

**Implementation**:
- Each playlist has immutable version number (monotonically increasing)
- Device maintains local playlist_version cached
- On sync interval:
  1. Device sends current playlist_version to backend
  2. Backend returns: { version: N, items: [...], checksum: "sha256:..." }
  3. If version unchanged: Device keeps displaying (no download needed)
  4. If version newer: Device downloads new playlist
  5. Device verifies checksum matches before displaying
- Content delivery includes checksum for integrity:
  - URL: "https://cdn.example.com/content/{content_id}"
  - Response header: "X-Content-Checksum: sha256:abc..."
  - Device verifies downloaded file matches checksum
- Failed downloads:
  - Retry up to 3 times with exponential backoff
  - If all retries fail: Continue displaying cached content
  - Log error to health endpoint for monitoring
- Prevents: Corrupted content display, man-in-the-middle attacks

### HIGH GUARDRAIL - Remote Command Authorization & Audit Trail

```
RULE: Remote commands (reboot, clear cache, etc.) require authorization
RULE: All remote commands logged for audit trail
RULE: Device must acknowledge command execution
```

**Implementation**:
- Remote commands require:
  - User must have 'manage-devices' permission in tenant
  - Command type specified (e.g., 'reboot', 'clear-cache', 'fetch-playlist')
  - Command signed with server private key (prevent tampering)
- Command flow:
  1. User initiates command via CMS dashboard
  2. Server generates command_id, signs with timestamp
  3. Device receives command, verifies signature
  4. Device executes command, sends acknowledgment with result
  5. Server logs: { command_id, device_id, executed_at, result }
- Prevent unauthorized commands:
  - Device checks command signature against known server public key
  - Only commands signed by server are executed
  - Unknown commands logged as security event
- Audit trail stored for compliance:
  - Command log includes who issued, when, result status
  - Failed commands logged with error details
  - Enables traceability for security investigations

### MEDIUM GUARDRAIL - Device Offline Handling & Graceful Degradation

```
RULE: Device must display cached content when offline (no blank screens)
RULE: Device must sync with server when connection restored
RULE: Health reporting continues during offline periods
```

**Implementation**:
- Device maintains local cache of:
  - Current playlist (includes all content metadata)
  - Last 3 playlist versions (for rollback if corrupt)
  - Content files downloaded (images, videos, html)
- Offline detection:
  - Device monitors network connectivity every 10 seconds
  - If connection lost: Switch to cached playlist immediately
  - Continue displaying cached content (prevents "no signal" screens)
- Offline sync queue:
  - Queue any changes (playlist updates) that occur while offline
  - When connection restored: Send sync request with queued items
  - Server responds with latest state, device reconciles
- Health reporting offline:
  - Device logs health metrics locally while offline
  - Uploads health log when connection restored
  - Server records: offline_duration, content_displayed_offline, cache_hit_rate
- Prevents: Blank screens during network outages, missed updates after reconnection

### MEDIUM GUARDRAIL - Content Cache Lifecycle & Storage Management

```
RULE: Device must manage storage to prevent "disk full" errors
RULE: Oldest content auto-deleted when storage threshold exceeded
RULE: Critical content (emergency messages) always kept
```

**Implementation**:
- Storage management:
  - Device monitors disk_used_percentage
  - If usage > 80%: Begin cleanup (remove oldest cached content)
  - If usage > 95%: Aggressive cleanup (remove all except current playlist)
  - If usage > 99%: Emergency mode (cannot download new content)
- Content prioritization:
  - Critical: Emergency messages, safety warnings (never delete)
  - Normal: Regular playlist content (delete oldest first)
  - Cached: Downloaded backup versions (delete oldest first)
- Cleanup timeline:
  - Content unused for > 30 days: Candidate for deletion
  - Content not in any playlist: Delete after 7 days
  - Health report tracks cleanup events
- Prevents: Disk full errors, lost emergency messages

### MEDIUM GUARDRAIL - Device Health Monitoring & Alerting

```
RULE: Critical health issues escalated to managers immediately
RULE: Device health trends tracked for predictive maintenance
RULE: Health data retained for historical analysis
```

**Implementation**:
- Health metrics reported every 60 seconds:
  - Memory usage, CPU usage, disk space, network latency
  - Uptime, last sync time, current playlist version, errors
- Alert thresholds:
  - CRITICAL: Memory > 95%, Disk > 95%, Offline > 30 min → Alert manager immediately
  - WARNING: Memory > 80%, Disk > 80%, Offline > 10 min → Log and monitor
  - INFO: All metrics logged for trend analysis
- Escalation:
  - CRITICAL alerts: SMS + Email to device manager
  - If unresolved after 1 hour: Escalate to ops director
- Trend analysis:
  - System detects patterns (e.g., device goes offline every evening at 6 PM)
  - Predictive: Alert if pattern suggests impending failure
  - Reports: Device health dashboard, maintenance schedule
- Prevents: Silent device failures, missed maintenance windows

---

## 6. Backend Integration

### 6.1 API Endpoints

**Device Registration:**
```http
POST /api/v1/signage/devices/register
Content-Type: application/json

{
  "device_id": "android_abc123",
  "platform": "android",
  "model": "Fire TV Stick 4K",
  "os_version": "Android 11",
  "app_version": "2.1.0",
  "screen_resolution": "3840x2160",
  "location": "Lobby Screen 1"
}

Response:
{
  "device_id": "device_abc123",
  "auth_token": "jwt_token_here",
  "config": {
    "sync_interval": 300,
    "health_interval": 60
  }
}
```

**Get Playlist:**
```http
GET /api/v1/signage/devices/{device_id}/playlist
Authorization: Bearer {token}

Response:
{
  "playlist_id": "pl_abc123",
  "version": 15,
  "items": [
    {
      "content_id": "video_abc123",
      "type": "video",
      "url": "https://cdn.example.com/content/video_abc123.mp4",
      "duration": 30,
      "checksum": "sha256:abc..."
    }
  ]
}
```

**Health Reporting:**
```http
POST /api/v1/signage/devices/{device_id}/health
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "online",
  "uptime": 86400,
  "disk_space_mb": 15360,
  "disk_used_mb": 2048,
  "current_content": "video_abc123",
  "playlist_version": 15,
  "errors": [],
  "network_status": "wifi",
  "cpu_usage": 45,
  "memory_usage": 62
}
```

### 6.2 WebSocket for Real-Time Updates

```javascript
// Native helper connects to WebSocket
const ws = new WebSocket('wss://api.example.com/signage/ws');

ws.on('message', (data) => {
  const message = JSON.parse(data);

  switch (message.type) {
    case 'playlist_updated':
      // Trigger immediate sync
      contentSyncer.sync();
      break;

    case 'emergency_message':
      // Show emergency content immediately
      player.playEmergency(message.content);
      break;

    case 'device_command':
      // Execute command (restart, update, etc.)
      handleCommand(message.command);
      break;
  }
});
```

---

## 7. Device Management

### 7.1 CMS Dashboard Features

**Device List:**
- View all registered devices
- Filter by status (online/offline), location, platform
- Bulk operations (assign playlist, send command)

**Device Detail:**
- Current playlist
- Health status & metrics
- Content sync status
- Logs & screenshots
- Remote commands (restart, update, screenshot)

**Device Provisioning:**
- QR code registration
- Auto-discovery on network
- Bulk import from CSV

### 7.2 Remote Commands

```python
# Send command from CMS
POST /api/v1/signage/devices/{device_id}/command

{
  "command": "restart",
  "params": {
    "delay_seconds": 60,
    "reason": "Scheduled maintenance"
  }
}

# Supported commands:
- restart: Restart player
- update: Update to new version
- screenshot: Take and upload screenshot
- reload_playlist: Force playlist refresh
- emergency_message: Show emergency content
- set_volume: Adjust audio volume
- diagnostic: Run diagnostic tests
```

---

## 8. Content Management

### 8.1 Content Types

**Supported Formats:**
- **Video:** MP4 (H.264/H.265), WebM
- **Image:** JPG, PNG, WebP, GIF
- **Web:** HTML widgets (weather, clock, RSS, custom)
- **Live Stream:** HLS, DASH (if network available)

### 8.2 Content Delivery

**CDN Strategy:**
```
1. Content uploaded to CMS → stored in S3/CloudFront
2. Device requests playlist → gets CDN URLs
3. Native helper downloads from CDN → local storage
4. Web player streams from localhost
```

**Optimization:**
- Video transcoding (1080p, 720p, 480p variants)
- Adaptive bitrate for network conditions
- Thumbnail generation
- Checksum verification

---

## 9. Monitoring & Health

### 9.1 Health Metrics

```python
{
  "device_id": "device_abc123",
  "status": "online",
  "last_seen": "2024-12-23T10:30:00Z",
  "uptime_seconds": 86400,
  "metrics": {
    "disk_space": {
      "total_mb": 15360,
      "used_mb": 2048,
      "available_mb": 13312
    },
    "performance": {
      "cpu_usage_percent": 45,
      "memory_usage_percent": 62,
      "temperature_celsius": 55
    },
    "playback": {
      "current_content": "video_abc123",
      "playlist_version": 15,
      "playback_errors_24h": 0,
      "frame_drops_1h": 3
    },
    "network": {
      "status": "wifi",
      "signal_strength": -45,
      "bandwidth_mbps": 50,
      "sync_errors_24h": 0
    }
  }
}
```

### 9.2 Alerting

**Alert Conditions:**
- Device offline > 5 minutes
- Disk space < 10%
- Playback errors > 5 per hour
- High CPU/memory (> 90% for 10 min)
- Content sync failures > 3 consecutive
- Temperature > 80°C

**Alert Channels:**
- Email
- SMS
- Webhook
- In-app notification

---

## 10. Deployment & Updates

### 10.1 Initial Deployment

**Step 1: Device Provisioning**
```
1. Install native app on device
2. Connect device to network
3. Scan QR code from CMS
4. Device registers with backend
5. Download initial content
6. Start playback
```

**Step 2: Configuration**
```
- Assign device to location
- Assign default playlist
- Configure schedule
- Set display settings (resolution, rotation)
```

### 10.2 Update Strategy

**App Updates:**
```
1. New version published to CMS
2. Devices check for updates (daily)
3. Download update in background
4. Install during off-hours (3 AM default)
5. Auto-restart with new version
6. Report success/failure
```

**Content Updates:**
```
1. Playlist modified in CMS
2. WebSocket notifies devices
3. Devices download new content
4. Transition to new playlist when ready
5. Delete old unused content
```

**Rollback:**
```
- Keep previous 2 versions
- Auto-rollback if crash loop detected
- Manual rollback from CMS
```

---

## 11. Best Practices

### 11.1 DO's ✅

**1. Use Native Helper for System Tasks**
```
✅ Download & store content in native
✅ Manage auto-start via native
✅ Implement watchdog in native
✅ Handle network detection in native
```

**2. Keep Web Player Simple**
```
✅ Focus on rendering & playback logic
✅ Fetch data from localhost
✅ Handle transitions & layouts
✅ Report playback events
```

**3. Design for Offline**
```
✅ Assume network can fail anytime
✅ Pre-download all content
✅ Graceful degradation
✅ Continue playing cached content
```

**4. Monitor Everything**
```
✅ Health reporting every minute
✅ Log all errors
✅ Track playback quality
✅ Alert on anomalies
```

### 11.2 DON'Ts ❌

**1. Don't Rely on Web-Only Offline**
```
❌ Service worker for production offline
❌ IndexedDB as primary storage
❌ Assuming cache won't be cleared
```

**2. Don't Use Public Browser for Production**
```
❌ Chrome/Firefox on desktop
❌ Mobile Safari
❌ Only for preview/testing
```

**3. Don't Over-Engineer**
```
❌ Full native just because "native is better"
❌ Flutter for signage
❌ Complex state management when simple works
```

**4. Don't Ignore Device Constraints**
```
❌ 4K on low-end devices
❌ Large playlists without pagination
❌ Unoptimized video files
```

---

## 12. Future Enhancements

### 12.1 Roadmap

**Phase 2 (Expanded Operations):**
- Multi-zone layouts (split screen)
- Interactive widgets (touch support)
- Advanced scheduling (date/time rules, triggers)
- **Integration with hotel PMS (room status, occupancy, events)** ← Moved from Phase 3 (operational value)
  - Real-time room status display (occupied, cleaning, maintenance, available)
  - Event notifications (breakfast service times, staff announcements)
  - Guest-facing information (check-in/check-out times, facility status)
- A/B testing for content
- Analytics dashboard

**Phase 3 (Intelligence & Analytics):**
- AI-powered content recommendations
- Face detection & audience analytics
- Dynamic content based on viewer demographics
- Advanced PMS integration (predictive analytics, dynamic pricing promotions)

**Phase 4:**
- AR overlays
- Voice interaction
- Mobile companion app
- Social media integration

---

## Reference

**Related Documents:**
- [ARCH-02: Module Architecture](./ARCH-02-module-architecture.md)
- [STD-17: Logging & Observability](./STD-17-logging-observability.md)
- [SPEC-05: Internal Dev Management](./SPEC-05-internal-dev-management.md)

**External Resources:**
- WebView2 Documentation: https://docs.microsoft.com/en-us/microsoft-edge/webview2/
- Android WebView Guide: https://developer.android.com/guide/webapps/webview
- Chromium Kiosk Mode: https://www.chromium.org/administrators/policy-list-3#KioskModeEnabled

---

**Last Updated:** 2024-12-23
**Status:** FINAL - Ready for Implementation
**Owner:** Engineering Team
**Module Code:** `signage` (per ARCH-02)
