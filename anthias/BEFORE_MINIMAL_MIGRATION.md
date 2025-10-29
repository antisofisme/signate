# Anthias Structure Before Minimal Migration

## Summary Statistics
- **Total Size**: 3.8M
- **Total Files**: 172 files
- **Python Files**: 83 files
- **Total Python LOC**: 7,697 lines

## Directory Structure
```
.
├── ansible/                    # Platform deployment configs - TO REMOVE
│   └── roles/
├── anthias_app/                # Django app - KEEP (minimal)
│   ├── management/
│   └── migrations/
├── anthias_django/             # Django config - KEEP (minimal)
├── api/                        # REST API - SIMPLIFY to storage only
│   ├── migrations/
│   ├── serializers/
│   ├── tests/
│   ├── urls/
│   └── views/
├── bin/                        # Scripts - TO REMOVE
├── docker/                     # Docker configs - SIMPLIFY
│   └── nginx/
├── docs/                       # Documentation - TO REMOVE
│   ├── d2/
│   └── images/
├── lib/                        # Libraries - REVIEW & SIMPLIFY
├── requirements/               # Python deps - SIMPLIFY
├── tests/                      # Test suite - TO REMOVE
│   ├── assets/
│   └── config/
├── tools/                      # Build tools - TO REMOVE
│   └── image_builder/
└── viewer/                     # Frontend player - TO REMOVE (we have separate viewer)
```

## Key Files to KEEP (with modifications)
- `anthias_app/models.py` - Simplify Asset model
- `manage.py` - Django management
- `anthias_django/settings.py` - Simplify Django settings
- `api/` - Replace with minimal storage API
- `docker/Dockerfile` - Simplify
- `requirements/` - Simplify to minimal deps

## Files/Dirs to REMOVE (95% reduction target)
1. **Viewer** (we have separate viewer at /viewer)
   - `viewer/` directory

2. **Platform-specific deployment**
   - `ansible/`
   - `tools/image_builder/`
   - `bin/` (startup scripts)

3. **Documentation**
   - `docs/`

4. **Testing infrastructure**
   - `tests/`
   - `api/tests/`

5. **Complex features** (moved to Backend)
   - `celery_tasks.py` (background jobs)
   - Scheduler logic (in API views)
   - Web UI templates/static

6. **Build artifacts**
   - Package configs for frontend
   - Balena configs

## Current Asset Model Fields (to simplify)
Current fields:
- asset_id (primary key) - KEEP
- name - KEEP
- uri (file path) - KEEP
- md5 (checksum) - KEEP
- mimetype - KEEP
- start_date - REMOVE (Backend handles scheduling)
- end_date - REMOVE (Backend handles scheduling)
- duration - REMOVE (Backend handles this)
- is_enabled - REMOVE (Backend handles this)
- is_processing - REMOVE (Backend handles this)
- nocache - REMOVE (Backend handles this)
- play_order - REMOVE (Backend handles this)
- skip_asset_check - REMOVE (Backend handles this)

## Migration Goal
Reduce from 7,697 LOC to ~500 LOC (93% reduction)
Keep only: File upload, serve, delete, MD5 calculation

## Target Architecture
```
Backend (FastAPI) → Anthias Storage Service → File System
     ↓
  PostgreSQL (metadata, scheduling, playlists)
```

Anthias becomes a simple file storage service with no business logic.
