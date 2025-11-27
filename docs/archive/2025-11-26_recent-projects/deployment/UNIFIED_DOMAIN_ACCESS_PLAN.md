# 🌐 Unified Domain Access Plan
**Digital Signage - CMS & Player**

**Tujuan**: Akses seragam menggunakan domain dari dalam dan luar jaringan
**Target**: `https://admin.zhmhotels.online` dan `https://player.zhmhotels.online`
**Status**: Analysis Complete - Implementation Needed

---

## 📊 Executive Summary

### Current State (🔴 CRITICAL ISSUES FOUND)
- ❌ **Multiple hardcoded URLs** across backend, CMS, dan player
- ❌ **Inconsistent configuration** antara .env files
- ❌ **Mixed HTTP/HTTPS** access patterns
- ❌ **No centralized configuration** management
- ⚠️ **Gap in deployment** - local .env berbeda dengan server .env

### Target State (✅ DESIRED)
- ✅ **Unified domain access** dari LAN dan Internet
- ✅ **No hardcoded URLs** - semua dari environment variables
- ✅ **Consistent HTTPS** untuk production
- ✅ **Centralized configuration** dengan validation
- ✅ **Automated deployment** dengan configuration sync

---

## 🔍 Detailed Analysis

### 1. Backend (FastAPI) - Grade: C+ (60/100)

#### ✅ **GOOD** - What Works:
```python
# backend-python/.env (on server)
PUBLIC_BASE_URL=https://api.zhmhotels.online  ✅ Correct domain
CORS_ORIGINS=http://localhost:3000,...        ✅ Includes necessary origins
```

```python
# backend-python/shared/config.py
class Settings(BaseSettings):
    PUBLIC_BASE_URL: str = "http://localhost:8001"  # Read from .env
    CORS_ORIGINS: str = ""  # Parsed to list
```

#### ❌ **BAD** - What's Broken:
```python
# backend-python/main.py - Line 35-36 - HARDCODED!
"http://192.168.5.12:8080",  # Player URL
"http://192.168.5.12:3000"   # CMS URL
```

```python
# backend-python/shared/config.py - Line 53 - DEFAULT FALLBACK WRONG!
PUBLIC_BASE_URL: str = "http://localhost:8001"  # Should be from env only
```

```python
# backend-python/services/device/log_routes.py - Line 85
"url": "http://192.168.5.12:8080/"  # Hardcoded player URL
```

#### 🔧 **Required Fixes**:
1. Add `CMS_URL` and `PLAYER_URL` to Settings class
2. Remove hardcoded URLs from main.py CORS
3. Update log_routes.py to use settings.PLAYER_URL
4. Add validation for required env vars
5. Update .env.example with all required variables

---

### 2. CMS Admin (React + Vite) - Grade: D+ (40/100)

#### ✅ **GOOD** - What Works:
```typescript
// cms-vite/src/lib/api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'fallback';
```

#### ❌ **BAD** - What's Broken:

**1. Hardcoded WebSocket URL** - `cms-vite/src/lib/websocket/WebSocketProvider.tsx:172`
```typescript
// Line 172 - CRITICAL HARDCODE!
if (import.meta.env.DEV) {
    return `ws://192.168.5.12:8001/api/ws/admin`  // ❌ HARDCODED!
}
```

**2. Wrong Fallback** - `cms-vite/src/lib/api/client.ts:14`
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.5.12:8001';
// Should be: || 'https://api.zhmhotels.online'
```

**3. Inconsistent .env files**:
```env
# cms-vite/.env (local - for development)
VITE_API_URL=http://192.168.5.12:8001  ✅ OK for dev

# cms-vite/.env.production (local - WRONG!)
VITE_API_URL=http://192.168.5.12:8001  ❌ Should be HTTPS domain!
VITE_WS_URL=ws://192.168.5.12:8001     ❌ Should be WSS domain!
```

**4. Missing WS URL usage**:
```typescript
// WebSocketProvider.tsx doesn't use VITE_WS_URL env var
// It constructs URL manually with hardcoded logic
```

#### 🔧 **Required Fixes**:
1. Remove hardcoded `ws://192.168.5.12:8001` from WebSocketProvider.tsx
2. Add `VITE_WS_URL` environment variable support
3. Update `.env.production` to use HTTPS domains
4. Update fallback URLs to use production domains
5. Sync `.env.production` between local and server

---

### 3. Player (React + Vite) - Grade: B- (70/100)

#### ✅ **GOOD** - What Works:
```typescript
// player-vite/src/shared/config/network-detector.ts
// Has proper auto-detection logic for LAN vs Internet
export function getApiBaseUrl(): string {
  if (isLocalNetwork()) {
    return 'http://192.168.5.12:8001';    // LAN
  } else {
    return 'https://api.zhmhotels.online'; // Internet
  }
}
```

#### ❌ **BAD** - What's Broken:

**1. Inconsistent .env.production** (on server):
```env
# player-vite/.env.production (on server - WRONG!)
VITE_API_BASE_URL=https://api.zhmhotels.online  ✅ Correct
VITE_WS_BASE_URL=wss://api.zhmhotels.online     ✅ Correct

# BUT: Player tetap pakai network-detector, bukan env vars!
# Gap: Env vars tidak dipakai karena network-detector di-hardcode
```

**2. Hardcoded URLs in network-detector**:
```typescript
// Should use env vars, not hardcoded values
return 'http://192.168.5.12:8001';          // ❌ Hardcoded
return 'https://api.zhmhotels.online';      // ❌ Hardcoded
return 'ws://192.168.5.12:8001';           // ❌ Hardcoded
return 'wss://api.zhmhotels.online';       // ❌ Hardcoded
```

#### 🔧 **Required Fixes**:
1. Update network-detector to use env vars instead of hardcoded values
2. Ensure .env.production is used during build
3. Remove auto-detection if using unified domain approach
4. Simplify configuration to always use domain (HTTPS)

---

## 🎯 Solution Strategy

### Option A: **Domain-Only Approach** (RECOMMENDED) ⭐
**Concept**: Semua akses (LAN & Internet) menggunakan domain HTTPS

**Pros**:
- ✅ Uniform access - tidak perlu mikir HTTP vs HTTPS
- ✅ Secure by default - always encrypted
- ✅ Simple configuration - one URL for all
- ✅ No NAT hairpinning issues jika DNS di-configure dengan benar
- ✅ Professional - production-ready

**Cons**:
- ⚠️ Sedikit lebih lambat di LAN (SSL overhead minimal ~10-20ms)
- ⚠️ Perlu DNS configuration di router untuk LAN split-brain DNS

**Architecture**:
```
┌─────────────────────────────────────────────────────────┐
│                   UNIFIED DOMAIN ACCESS                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐      ┌──────────────────────────┐     │
│  │  LAN User   │──────▶│  https://admin.zhmhotels  │     │
│  └─────────────┘      │        .online           │     │
│                       │                          │     │
│  ┌─────────────┐      │  (Split-brain DNS)       │     │
│  │ Internet    │──────▶│  → 192.168.5.12 (LAN)   │     │
│  │ User        │      │  → Public IP (Internet)  │     │
│  └─────────────┘      └──────────────────────────┘     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**Implementation**:
1. Configure router DNS untuk split-brain:
   ```
   admin.zhmhotels.online → 192.168.5.12 (LAN query)
   player.zhmhotels.online → 192.168.5.12 (LAN query)
   ```
2. Use HTTPS domains in all .env.production files
3. Remove all hardcoded HTTP/IP addresses
4. HTTPS traffic tetap through Cloudflare dari Internet

---

### Option B: **Auto-Detection Approach** (COMPLEX)
**Concept**: Deteksi LAN vs Internet, gunakan HTTP vs HTTPS accordingly

**Pros**:
- ✅ Fastest di LAN (no SSL overhead)
- ✅ No DNS configuration needed

**Cons**:
- ❌ Complex logic - prone to bugs
- ❌ Different URLs for different locations - confusing
- ❌ Mixed security (HTTP di LAN, HTTPS di Internet)
- ❌ Hard to maintain and debug
- ❌ Browser mixed content warnings

**Status**: ❌ NOT RECOMMENDED - too complex for minimal benefit

---

## 📋 Implementation Plan - Option A (Domain-Only)

### Phase 1: Backend Configuration (30 min)

**File**: `backend-python/.env` dan `backend-python/shared/config.py`

**Changes**:
```python
# 1.1 Update backend-python/.env (both local & server)
PUBLIC_BASE_URL=https://api.zhmhotels.online
CMS_URL=https://admin.zhmhotels.online
PLAYER_URL=https://player.zhmhotels.online
CORS_ORIGINS=https://admin.zhmhotels.online,https://player.zhmhotels.online,http://localhost:3000,http://localhost:8080

# 1.2 Update backend-python/shared/config.py
class Settings(BaseSettings):
    PUBLIC_BASE_URL: str  # No default - must be in .env
    CMS_URL: str          # No default - must be in .env
    PLAYER_URL: str       # No default - must be in .env

    @validator('PUBLIC_BASE_URL', 'CMS_URL', 'PLAYER_URL')
    def validate_required_urls(cls, v):
        if not v:
            raise ValueError("URL must be set in environment")
        return v

# 1.3 Update backend-python/main.py - Remove hardcoded CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),  # From env
    ...
)

# 1.4 Update backend-python/services/device/log_routes.py
from shared.config import settings
...
"url": settings.PLAYER_URL  # Use from config
```

**Deployment**:
```bash
# Local
cat > backend-python/.env <<EOF
PUBLIC_BASE_URL=https://api.zhmhotels.online
CMS_URL=https://admin.zhmhotels.online
PLAYER_URL=https://player.zhmhotels.online
CORS_ORIGINS=https://admin.zhmhotels.online,https://player.zhmhotels.online
EOF

# Sync to server
sshpass -p 'Password@2021' scp backend-python/.env gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/
sshpass -p 'Password@2021' scp backend-python/shared/config.py gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/shared/

# Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"
```

---

### Phase 2: CMS Configuration (45 min)

**Files**: `.env.production`, `client.ts`, `WebSocketProvider.tsx`

**Changes**:
```env
# 2.1 Update cms-vite/.env.production (both local & server)
VITE_API_URL=https://api.zhmhotels.online
VITE_WS_URL=wss://api.zhmhotels.online/api/ws/admin
VITE_PLAYER_URL=https://player.zhmhotels.online
```

```typescript
// 2.2 Update cms-vite/src/lib/api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.zhmhotels.online';
// Changed fallback from HTTP to HTTPS domain

// 2.3 Update cms-vite/src/lib/websocket/WebSocketProvider.tsx
function getWebSocketUrl(): string {
  // Use env var directly - no hardcoded fallback
  const wsUrl = import.meta.env.VITE_WS_URL;

  if (!wsUrl) {
    throw new Error('VITE_WS_URL not configured');
  }

  return wsUrl;
}
```

**Deployment**:
```bash
# Local - Update .env.production
cat > cms-vite/.env.production <<EOF
VITE_API_URL=https://api.zhmhotels.online
VITE_WS_URL=wss://api.zhmhotels.online/api/ws/admin
VITE_PLAYER_URL=https://player.zhmhotels.online
EOF

# Update source files
# (Edit client.ts and WebSocketProvider.tsx as shown above)

# Build CMS
cd cms-vite
rm -rf dist/ node_modules/.vite
npm run build

# Verify no hardcoded URLs
grep -r "192\.168\.5\.12" dist/ && echo "❌ HARDCODED URLs FOUND!" || echo "✅ No hardcoded URLs"

# Sync to server
sshpass -p 'Password@2021' rsync -avz --delete \
  dist/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/cms-vite/dist/

sshpass -p 'Password@2021' scp .env.production \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/cms-vite/
```

---

### Phase 3: Player Configuration (45 min)

**Strategy**: Simplify - remove auto-detection, use domain only

**Files**: `.env.production`, `network-detector.ts`, config files

**Changes**:
```env
# 3.1 Update player-vite/.env.production (both local & server)
VITE_API_BASE_URL=https://api.zhmhotels.online
VITE_WS_BASE_URL=wss://api.zhmhotels.online
```

```typescript
// 3.2 Simplify player-vite/src/shared/config/network-detector.ts
export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || 'https://api.zhmhotels.online';
}

export function getWsBaseUrl(): string {
  return import.meta.env.VITE_WS_BASE_URL || 'wss://api.zhmhotels.online';
}

// Remove isLocalNetwork() and conditional logic
```

**Deployment**:
```bash
# Local - Update .env.production
cat > player-vite/.env.production <<EOF
VITE_API_BASE_URL=https://api.zhmhotels.online
VITE_WS_BASE_URL=wss://api.zhmhotels.online
VITE_HEARTBEAT_INTERVAL=30000
VITE_LOG_SEND_INTERVAL=30000
VITE_LOG_BUFFER_SIZE=50
EOF

# Update source files
# (Edit network-detector.ts as shown above)

# Build Player
cd player-vite
rm -rf dist/ node_modules/.vite
npm run build

# Verify no hardcoded IPs
grep -r "192\.168\.5\.12" dist/ && echo "❌ HARDCODED IPs FOUND!" || echo "✅ No hardcoded IPs"

# Sync to server
sshpass -p 'Password@2021' rsync -avz --delete \
  dist/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/dist/

sshpass -p 'Password@2021' scp .env.production \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/
```

---

### Phase 4: Router DNS Configuration (20 min)

**Purpose**: Split-brain DNS untuk LAN access ke domain

**Router Configuration** (access router admin panel):

1. **Login Router**: http://192.168.5.1 (adjust based on your router)

2. **Navigate to DNS Settings**:
   - Usually in: LAN Settings → DHCP/DNS Server
   - Or: Advanced → DNS → Static DNS Entries

3. **Add DNS Entries**:
   ```
   Host                          IP Address
   ────────────────────────────  ─────────────────
   admin.zhmhotels.online        192.168.5.12
   player.zhmhotels.online       192.168.5.12
   api.zhmhotels.online          192.168.5.12
   ```

4. **Save & Apply**

**Verification**:
```bash
# From LAN device
nslookup admin.zhmhotels.online
# Should return: 192.168.5.12

ping admin.zhmhotels.online
# Should respond from 192.168.5.12

# Test HTTPS access
curl -I https://admin.zhmhotels.online
# Should work if Cloudflare tunnel is active
```

**Alternative** (if router doesn't support custom DNS):
- Use hosts file on each device:
  ```
  # Windows: C:\Windows\System32\drivers\etc\hosts
  # Linux/Mac: /etc/hosts

  192.168.5.12 admin.zhmhotels.online
  192.168.5.12 player.zhmhotels.online
  192.168.5.12 api.zhmhotels.online
  ```

---

### Phase 5: Cloudflare Configuration (15 min)

**Verify Cloudflare Tunnel** is routing correctly:

1. **Login Cloudflare Dashboard**
2. **Navigate to**: Zero Trust → Access → Tunnels
3. **Verify Routes**:
   ```
   Domain                         Service
   ────────────────────────────── ──────────────────────
   admin.zhmhotels.online         http://192.168.5.12:3000
   player.zhmhotels.online        http://192.168.5.12:8080
   api.zhmhotels.online           http://192.168.5.12:8001
   ```

4. **Check Tunnel Status**: Should be "Healthy"

5. **Verify SSL/TLS**:
   - SSL/TLS → Overview → Encryption mode: "Full" or "Full (strict)"

**Test dari Internet**:
```bash
# From external device (not on LAN)
curl -I https://admin.zhmhotels.online
# Should return 200 OK

curl -I https://api.zhmhotels.online/health
# Should return healthy status
```

---

### Phase 6: Testing & Validation (30 min)

#### 6.1 Backend Tests
```bash
# Test health endpoint
curl https://api.zhmhotels.online/health

# Expected: {"status":"healthy","database":"connected"}

# Test CORS (from browser console on admin.zhmhotels.online)
fetch('https://api.zhmhotels.online/health')
  .then(r => r.json())
  .then(console.log)

# Should work without CORS errors
```

#### 6.2 CMS Tests
```
1. Open: https://admin.zhmhotels.online
2. Login: admin / admin123
3. Check:
   - ✅ Dashboard loads
   - ✅ Devices page loads
   - ✅ WebSocket connects (check browser console)
   - ✅ Real-time updates work
   - ✅ No console errors
4. Repeat from:
   - LAN device
   - Internet device (mobile hotspot)
```

#### 6.3 Player Tests
```
1. Open: https://player.zhmhotels.online
2. Enter activation code
3. Check:
   - ✅ Activation succeeds
   - ✅ Content loads
   - ✅ Heartbeat sends (check backend logs)
   - ✅ Console logs upload
   - ✅ Commands received via WebSocket
4. Repeat from:
   - LAN browser
   - Internet device
```

#### 6.4 Validation Checklist
```bash
# 1. No hardcoded URLs in code
cd /mnt/g/khoirul/signate
grep -r "192\.168\.5\.12" \
  cms-vite/src/ player-vite/src/ backend-python/ \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  | grep -v "# Comment\|// Comment"

# Expected: Only in comments or example files

# 2. Environment variables set correctly
echo "=== Backend ==="
cat backend-python/.env | grep URL

echo "=== CMS ==="
cat cms-vite/.env.production | grep VITE_

echo "=== Player ==="
cat player-vite/.env.production | grep VITE_

# 3. All services using HTTPS
# Expected: All URLs start with https:// or wss://
```

---

## 🔒 Security Considerations

### SSL/TLS
- ✅ All traffic encrypted via Cloudflare
- ✅ Valid SSL certificates
- ✅ TLS 1.2+ enforced

### CORS
- ✅ Restricted to known origins only
- ❌ No wildcard (*) origins in production

### Content Security Policy
```typescript
// Add to cms-vite/index.html and player-vite/index.html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self' https://api.zhmhotels.online wss://api.zhmhotels.online">
```

---

## 🚀 Deployment Automation

### Create Deployment Script
```bash
# scripts/deploy-unified-domain.sh

#!/bin/bash
set -e

SERVER="gzjbbk@192.168.5.12"
PASSWORD="Password@2021"

echo "🚀 Deploying Unified Domain Configuration"

# 1. Backend
echo "📦 Deploying backend..."
sshpass -p "$PASSWORD" scp backend-python/.env $SERVER:/home/gzjbbk/signate/backend-python/
sshpass -p "$PASSWORD" ssh $SERVER "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"

# 2. CMS
echo "📦 Building CMS..."
cd cms-vite
npm run build
echo "📦 Deploying CMS..."
sshpass -p "$PASSWORD" rsync -avz --delete dist/ $SERVER:/home/gzjbbk/signate/cms-vite/dist/

# 3. Player
echo "📦 Building Player..."
cd ../player-vite
npm run build
echo "📦 Deploying Player..."
sshpass -p "$PASSWORD" rsync -avz --delete dist/ $SERVER:/home/gzjbbk/signate/player-vite/dist/

echo "✅ Deployment complete!"
echo "🌐 Access URLs:"
echo "   CMS: https://admin.zhmhotels.online"
echo "   Player: https://player.zhmhotels.online"
echo "   API: https://api.zhmhotels.online"
```

### Usage
```bash
chmod +x scripts/deploy-unified-domain.sh
./scripts/deploy-unified-domain.sh
```

---

## 📝 Configuration Reference

### Environment Variables Matrix

| Variable | Backend | CMS | Player | Value |
|----------|---------|-----|--------|-------|
| API URL | `PUBLIC_BASE_URL` | `VITE_API_URL` | `VITE_API_BASE_URL` | `https://api.zhmhotels.online` |
| WS URL | - | `VITE_WS_URL` | `VITE_WS_BASE_URL` | `wss://api.zhmhotels.online` |
| CMS URL | `CMS_URL` | - | - | `https://admin.zhmhotels.online` |
| Player URL | `PLAYER_URL` | `VITE_PLAYER_URL` | - | `https://player.zhmhotels.online` |
| CORS Origins | `CORS_ORIGINS` | - | - | See backend .env |

### File Locations

```
/mnt/g/khoirul/signate/
├── backend-python/
│   ├── .env                     # Backend config
│   ├── .env.example             # Template
│   ├── shared/config.py         # Settings class
│   └── main.py                  # CORS middleware
├── cms-vite/
│   ├── .env                     # Development config
│   ├── .env.production          # Production config
│   ├── src/lib/api/client.ts   # API client
│   └── src/lib/websocket/
│       └── WebSocketProvider.tsx
└── player-vite/
    ├── .env                     # Development config
    ├── .env.production          # Production config
    └── src/shared/config/
        └── network-detector.ts
```

---

## ⚠️ Common Pitfalls & Solutions

### Issue 1: "Failed to fetch" di LAN
**Cause**: DNS tidak resolve ke 192.168.5.12
**Solution**: Configure split-brain DNS di router atau gunakan hosts file

### Issue 2: CORS Error
**Cause**: Missing domain di CORS_ORIGINS
**Solution**: Add `https://admin.zhmhotels.online` dan `https://player.zhmhotels.online`

### Issue 3: WebSocket tidak connect
**Cause**: WS URL masih HTTP/WS instead of HTTPS/WSS
**Solution**: Update `VITE_WS_URL=wss://api.zhmhotels.online/api/ws/admin`

### Issue 4: Mixed Content Warning
**Cause**: HTTPS page loading HTTP resources
**Solution**: Ensure all URLs use https:// or wss://

### Issue 5: Cloudflare Tunnel tidak active
**Cause**: Tunnel service down atau misconfigured
**Solution**:
```bash
# Check tunnel status
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "systemctl status cloudflared"

# Restart if needed
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "sudo systemctl restart cloudflared"
```

---

## 📊 Success Metrics

### Before Implementation
- ❌ Multiple access URLs (HTTP/HTTPS/IP/Domain)
- ❌ 15+ hardcoded URLs in codebase
- ❌ Inconsistent configuration across services
- ❌ Configuration drift between local and server
- ⚠️ Login failures due to URL mismatches

### After Implementation
- ✅ Single unified domain access for all
- ✅ Zero hardcoded URLs
- ✅ Centralized configuration management
- ✅ Automated configuration sync
- ✅ 100% test pass rate

### Performance
- LAN Access: ~10-20ms SSL overhead (negligible)
- Internet Access: Same as before (already via Cloudflare)
- WebSocket Latency: <100ms (unchanged)

---

## 🎓 Next Steps

1. **Review this plan** dengan team
2. **Schedule implementation** - est. 2-3 hours total
3. **Backup current configuration** sebelum changes
4. **Execute Phase 1-6** secara berurutan
5. **Test thoroughly** setelah selesai
6. **Document any issues** encountered
7. **Update CLAUDE.md** dengan final configuration

---

## 📞 Support & Troubleshooting

Jika ada masalah during implementation:

1. **Check logs**:
   ```bash
   # Backend
   docker logs signage-backend-python --tail 100

   # Cloudflare Tunnel
   journalctl -u cloudflared -n 100
   ```

2. **Verify DNS**:
   ```bash
   nslookup admin.zhmhotels.online
   nslookup api.zhmhotels.online
   ```

3. **Test connectivity**:
   ```bash
   curl -I https://api.zhmhotels.online/health
   curl -I https://admin.zhmhotels.online
   ```

4. **Rollback if needed**:
   ```bash
   git checkout .  # Rollback code changes
   # Restore .env from backup
   # Restart services
   ```

---

**Document Version**: 1.0
**Date**: 2025-11-25
**Author**: Claude Code Analysis
**Status**: Ready for Implementation ✅
