# Server Information

## Production Server
- **IP Address**: 192.168.5.12
- **SSH User**: gzjbbk
- **SSH Password**: Password@2021

## Service Ports (ALL ON SERVER)
- **Port 8000**: Anthias (Digital Signage CMS)
- **Port 8001**: Backend API (FastAPI in Docker) ✅ RUNNING
- **Port 3000**: Web Admin (React/Vite Dev Mode) - Run locally, proxies API to server
- **Port 5433**: PostgreSQL Database ✅ RUNNING
- **Port 8080**: Viewer (Static HTML) ✅ RUNNING - For monitors, browsers, and WebOS TV

## URLs
- **Viewer**: http://192.168.5.12:8080/ (untuk monitor, browser, dan WebOS TV)
- **Web Admin**: http://localhost:3000/ (development - proxies to server)
- **Backend API**: http://192.168.5.12:8001/
- **API Docs**: http://192.168.5.12:8001/docs

## Current Status (ALL FIXED!)
✅ Backend API running in Docker on server (port 8001) - REBUILT with CORS fix!
✅ PostgreSQL database running in Docker on server (port 5433)
✅ Viewer running on server (port 8080) - Unified viewer for monitors, browsers, and WebOS TV
✅ Viewer configured to use correct backend (port 8001, NOT 8000!)
✅ CORS configuration includes port 8080 - Registration working!
✅ Web Admin can run locally and proxy API calls to server
✅ Dockerfile optimized with PYTHONDONTWRITEBYTECODE=1 to prevent build failures
✅ WebOS IPK packaging via webos-app folder (copies from viewer)

## Important Notes
- ⚠️ **ALL services MUST run on SERVER (192.168.5.12), NOT localhost**
- ✅ Backend API is running in Docker container (signage-backend)
- ✅ **Unified Viewer Architecture:**
  - **viewer/** (port 8080) → Single codebase for all platforms (monitors, browsers, WebOS TV)
  - **webos-app/** → Packaging folder for WebOS IPK (copies from viewer + adds appinfo.json)
  - Uses 6-digit activation code for device registration
- ✅ Viewer points to correct backend (8001) - device registration working!
- Viewer has heartbeat mechanism (sends every 30s after activation)
- Dashboard shows online/offline based on last_seen < 5 minutes
- Web Admin development server (localhost:3000) proxies /api requests to server backend

## 🔴 CRITICAL: Code & Config Synchronization Protocol
**SETIAP kali melakukan perubahan code atau konfigurasi, WAJIB update di KEDUA lokasi:**

### Files yang WAJIB Sinkron:
1. **Configuration Files:**
   - `.env` (local & server)
   - `.env.example` (local & server)
   - `backend/app/core/config.py` (local & server)

2. **Source Code:**
   - Semua file `.jsx`, `.js`, `.py` yang diubah
   - Frontend: `web-admin/src/**/*`
   - Backend: `backend/app/**/*`
   - Viewer: `viewer/**/*` (unified codebase for all platforms)
   - WebOS App: `webos-app/**/*` (IPK packaging - copies from viewer)

### Workflow Update:
```bash
# 1. Update di LOCAL terlebih dahulu
# Edit file yang diperlukan di /mnt/g/khoirul/signate

# 2. PASTIKAN testing lokal berhasil
npm run dev  # untuk frontend
uvicorn app.main:app --reload  # untuk backend

# 3. Sync ke SERVER menggunakan scp/rsync
sshpass -p 'Password@2021' scp -r file_yang_diubah gzjbbk@192.168.5.12:/home/gzjbbk/signate/

# 4. Rebuild container di server jika diperlukan
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/signate && docker-compose up -d --build backend-api"
```

### ⚠️ Konsekuensi Jika TIDAK Sinkron:
- ❌ Reinstall dari local akan kehilangan perubahan yang ada di server
- ❌ Perubahan konfigurasi tidak konsisten
- ❌ Bug yang sudah diperbaiki bisa muncul lagi
- ❌ Development environment berbeda dengan production

### ✅ Best Practice:
- **SELALU update LOCAL dulu, baru ke SERVER**
- **COMMIT ke Git setelah update sukses di kedua lokasi**
- **Test di local sebelum deploy ke server**
- **Dokumentasikan perubahan di changelog atau commit message**

## 📝 Documentation & Reporting Rules

### 🎯 Core Principles:
1. **TO THE POINT** - No verbose explanations, straight to the facts
2. **UPDATE existing analysis** - Don't create duplicate reports
3. **Reference code locations** - Use `file.py:123` format instead of long explanations
4. **Initial analysis can be detailed** - But only to avoid mistakes, still concise

### ✅ Allowed Documentation:
**Initial Analysis/Review (before work):**
- Detailed analysis to prevent mistakes
- Must still be concise and to the point
- No unnecessary explanations

**Work Reports (after completion):**
- Summary only: What was done
- Results: Key metrics, status
- Code references: `file.py:line` format
- Breaking changes: List only
- Next steps: Bullet points

### ❌ Prohibited Documentation:
- Verbose/detailed reports after work completion
- Duplicate documentation in multiple files
- Long explanations of code changes
- Unnecessary context or background
- Multiple report files for same work

### 📋 Report Format Template:

```markdown
## Work: [Task Name]

**Status:** ✅ Complete / ⚠️ Issues / 🔴 Blocked

**Changes:**
- Modified: file1.py:45, file2.ts:123
- Added: file3.py (200 lines)
- Deleted: old_file.js

**Results:**
- Metric 1: X → Y
- Tests: 45/45 passing
- Build: ✅ Success

**Breaking Changes:**
- API endpoint changed: /old → /new
- Response format: {old} → {new}

**Next:**
- [ ] Task 1
- [ ] Task 2
```

### 📍 Code Reference Examples:
```
✅ GOOD:
"Updated pagination in api/content.py:123-145"
"Fixed CORS in config.py:67"
"Added validation schema.py:89"

❌ BAD:
"I updated the pagination logic by changing the offset-based
approach to page-based approach in the content API file, which
involved modifying the query parameters and updating the response
structure to include page metadata..."
```

### 🔄 Update vs Create:
```
✅ UPDATE existing files:
- SPRINT1_COMPLETE.md (update metrics)
- API_STATUS.md (update progress)
- CHANGELOG.md (append entries)

❌ DON'T CREATE new files:
- SPRINT1_DETAILED_REPORT.md
- SPRINT1_ANALYSIS.md
- SPRINT1_SUMMARY.md
```
