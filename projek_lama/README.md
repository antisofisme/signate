# Signate

Advanced Digital Signage Platform based on Anthias

## Project Overview

Signate is a comprehensive digital signage solution built on top of the open-source Anthias platform, designed to compete with commercial solutions like Screenly Pro.

## Vision

Create a feature-rich, scalable digital signage platform that offers:
- Cloud-based device management
- Advanced content scheduling
- Analytics and reporting
- Multi-user collaboration
- Enterprise-grade features

## Current Status

🚧 **In Development**

### Completed ✅
- [x] **Anthias Core Setup** - Base installation and configuration
- [x] **Custom Viewer** - Enhanced horizontal layout with fullscreen slideshow
- [x] **Tag-based Filtering** - Filter assets using filename tags (#hotel #kamar)
- [x] **Dual-box Filter UI** - Move tags between available/selected boxes
- [x] **Audio Controls** - Enable/disable audio for video assets
- [x] **Configuration Management** - Save/load settings to localStorage
- [x] **MikroTik DNS Integration** - Access via anthias.local
- [x] **Production Deployment** - Running stable on 192.168.5.12

### In Development 🚧
- [ ] **Enhanced UI/UX** - Zoom controls, grid/list views, responsive design
- [ ] **Content Management** - Favorites, search, sorting, playlists
- [ ] **Time-based Features** - Clock display, schedule, auto-brightness
- [ ] **Advanced Controls** - Keyboard shortcuts, touch gestures
- [ ] **Device Integration** - Kiosk mode, wake/sleep schedule

📋 *See [RENCANA-PENGEMBANGAN.md](RENCANA-PENGEMBANGAN.md) for complete feature roadmap*

## Technology Stack

**Base Platform:** Anthias (open-source digital signage)  
**Frontend:** React 19 + TypeScript + Redux Toolkit  
**Backend:** Django 4.2 + Django REST Framework + Celery  
**Database:** PostgreSQL / SQLite  
**Infrastructure:** Docker + nginx + Redis + WebSocket  

📋 *See [docs/TECHNOLOGY_STACK.md](docs/TECHNOLOGY_STACK.md) for complete technical details*

## 🚀 Upcoming Features

### Phase 1: Core UX Improvements
- 🔍 **Zoom/Pan Controls** - Zoom in/out untuk detail view images
- 📱 **Grid/List View Toggle** - Alternative layouts selain horizontal scroll
- ⌨️ **Keyboard Shortcuts** - Space=pause, arrows=navigate, shortcuts overlay
- 🌐 **Connection Status** - Online/offline indicator dengan auto-reconnect

### Phase 2: Content Management
- ⭐ **Favorites System** - Mark assets favorit untuk quick access
- 🔎 **Search/Filter Box** - Real-time search dengan autocomplete
- ⏰ **Time-based Filtering** - Show different assets per waktu (pagi/siang/malam)
- 👆 **Touch Gestures** - Swipe navigation, pinch zoom untuk mobile

### Phase 3: Advanced Features
- 📱 **Responsive Design** - Optimized experience untuk mobile/tablet
- 🖥️ **Fullscreen Kiosk Mode** - Hide browser UI completely
- 📜 **Recently Viewed** - History asset yang baru dilihat
- 🗂️ **Sort Options** - Sort by name, date, duration, type

### Phase 4: Polish & Enhancement
- 🕐 **Clock Display** - Digital clock di corner viewer
- 📅 **Schedule Display** - Jadwal/agenda hari ini
- ✨ **Transition Effects** - Fade, slide, zoom transitions antar asset
- 🎵 **Playlist Creator** - Custom playlists dari selected assets

*Complete roadmap: [RENCANA-PENGEMBANGAN.md](RENCANA-PENGEMBANGAN.md)*

## Getting Started

```bash
cd /home/gzjbbk/signate
# Development setup instructions to be added
```

## 🔧 Deployment & File Structure

### File Locations
```
Local Development:
  /home/gzjbbk/signate/anthias-ready-files/custom-viewers/viewer.html

❌ INCORRECT - URL /viewer is handled by React app, not static files:
  nginx container: /srv/anthias/static/custom-viewers/viewer.html  
  server container: /usr/src/app/static/viewer.html
```

### Deployment Issue
❌ **PROBLEM**: URL `/viewer` is routed to Django React app (`react.html` template), not static files.
🔍 **SOLUTION NEEDED**: Find correct way to serve custom viewer in Anthias architecture.

### 🎛️ Settings & Configuration

**Viewer Settings Location**:
- Browser localStorage: `anthias-viewer-config`
- URL parameters: `?server=http://anthias.local:8000&interval=60`

**Available Settings**:
- `serverUrl`: Anthias server endpoint
- `refreshInterval`: Auto-refresh interval (10-300s)
- `screenRotation`: 0°, 90°, 180°, 270°
- `objectFitMode`: contain, cover, fill
- `enableAudio`: true/false for video sound
- `videoVolume`: 0.0-1.0 volume level
- `selectedTags`: Array of asset filter tags

**Access Points**:
- **Main viewer**: `anthias.local:8000/viewer`
- **Admin panel**: `anthias.local:8000`
- **API**: `anthias.local:8000/api/v2/assets`

## License

To be determined based on commercial requirements and Anthias AGPL-3.0 compliance.

---

*Building the future of digital signage, one screen at a time.*