# Signate Development Guide

## Project Structure

```
signate/
├── docs/                    # Documentation
│   ├── DEVELOPMENT.md      # This file
│   ├── API.md             # API documentation
│   └── DEPLOYMENT.md      # Deployment guide
├── viewers/                # Viewer implementations
│   ├── enhanced-viewer.html        # Enhanced Anthias viewer
│   ├── anthias-viewer-standalone.html # Standalone viewer
│   ├── simple-viewer.html          # Basic viewer
│   ├── basic-viewer.html           # Original viewer
│   └── README.md                   # Viewer documentation
├── core/                   # Core platform (planned)
├── cloud/                  # Cloud management (planned)
├── mobile/                 # Mobile app (planned)
├── analytics/              # Analytics module (planned)
├── .gitignore
└── README.md
```

## Development Phases

### Phase 1: Viewer Enhancement ✅
- [x] Multiple viewer implementations
- [x] Configuration management
- [x] True fullscreen support
- [x] Cross-device compatibility
- [x] Horizontal layout design

### Phase 2: Core Platform (Next)
- [ ] Fork and customize Anthias
- [ ] Enhanced API endpoints
- [ ] Multi-tenant support
- [ ] Advanced scheduling
- [ ] User management

### Phase 3: Cloud Management
- [ ] Multi-device dashboard
- [ ] Remote monitoring
- [ ] Analytics collection
- [ ] Content distribution

### Phase 4: Enterprise Features
- [ ] SSO/LDAP integration
- [ ] Advanced analytics
- [ ] Custom branding
- [ ] Mobile app

## Technology Stack

For detailed technology stack information, see [TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md).

**Summary:**
- **Frontend**: React 19 + TypeScript + Redux Toolkit + Bootstrap
- **Backend**: Django 4.2 + Django REST Framework + Celery
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache/Queue**: Redis + ZeroMQ
- **Infrastructure**: Docker + nginx + WebSocket
- **Build Tools**: Webpack 5 + Babel + Jest

## Getting Started

1. **Development Environment**
   ```bash
   cd /home/gzjbbk/signate
   python3 -m http.server 8080
   ```

2. **Testing Viewers**
   ```bash
   # Access viewers at:
   http://localhost:8080/viewers/enhanced-viewer.html
   http://localhost:8080/viewers/anthias-viewer-standalone.html
   ```

3. **With Anthias Backend**
   ```bash
   # Start Anthias development server
   cd /home/gzjbbk/Anthias
   docker compose -f docker-compose.dev.yml up -d
   
   # Access via Anthias
   http://screenly.local:8000/viewer
   ```

## Contribution Guidelines

- Follow existing code patterns
- Document all new features
- Test across multiple browsers
- Maintain backward compatibility
- Use semantic commit messages

## Future Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mobile App    │    │  Web Dashboard  │    │   Display       │
│                 │    │                 │    │   Devices       │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │   Signate Cloud API     │
                    │                         │
                    │  - Device Management    │
                    │  - Content Distribution │
                    │  - Analytics Collection │
                    │  - User Management      │
                    └─────────────────────────┘
```