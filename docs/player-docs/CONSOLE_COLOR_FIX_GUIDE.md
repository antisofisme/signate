# Console Color Fix Guide

## Overview
Dokumentasi lengkap untuk troubleshooting dan deployment perubahan warna console log di player-vite.

**Tanggal**: 2025-11-20
**Versi**: 1.0
**Hash Build**: `index-DEQyn_SS.js`

---

## Masalah yang Diperbaiki

### 1. Console %c Formatting Tidak Bekerja
**Gejala**: Literal text `%c` dan CSS styles muncul sebagai text, bukan applied sebagai warna.

**Root Cause**: Emoji dipisah sebagai argument pertama, sehingga Chrome mengabaikan `%c` directives di argument kedua.

**Solusi**: Gabungkan emoji ke dalam template literal yang sama dengan `%c`:
```typescript
// BEFORE (BUG)
this.originalConsole.log(emoji, '%c' + namespace + '%c', color, '', ...args);

// AFTER (FIX)
this.originalConsole.log(`${emoji} %c${namespace}%c`, color, 'color: inherit;', ...args);
```

### 2. Namespace CamelCase Tidak Match dengan Color Keys
**Gejala**: Namespace seperti `[PlayerVideoJS]`, `[DeviceInfo]` tidak mendapat warna yang sesuai.

**Root Cause**: Color keys hanya `Player`, `Device`, tidak ada `PlayerVideoJS` atau `DeviceInfo`.

**Solusi**: Tambahkan prefix detection logic:
```typescript
if (!NAMESPACE_COLORS[category] && !NAMESPACE_COLORS[namespace]) {
  const prefixes = ['Shell', 'Player', 'Network', 'Device', 'Toast', 'Modal', 'Popup', 'Storage'];
  for (const prefix of prefixes) {
    if (category.startsWith(prefix)) {
      category = prefix;
      break;
    }
  }
}
```

### 3. Warna Kurang Kontras pada Dark Console
**Gejala**: Warna terlalu gelap, sulit dibaca di DevTools F12 (dark theme).

**Solusi**: Update ke warna lebih cerah dengan kontras tinggi.

---

## Skema Warna Final

### Kategori dan Warna

| Kategori | Warna | Hex Code | Namespace Contoh |
|----------|-------|----------|------------------|
| **Shell** | Kuning | `#fbbf24` | [Shell:Bootstrap], [Shell:Activation] |
| **Player** | Hijau | `#4ade80` | [PlayerVideoJS], [Player:VideoJS] |
| **Network** | Biru | `#60a5fa` | [NetworkHeartbeat], [Network:API] |
| **Device** | Cyan | `#22d3ee` | [DeviceInfo], [DeviceFingerprint] |
| **UI/Toast** | Merah Cerah | `#f87171` | [Toast], [Modal], [Popup] |
| **Storage** | Orange | `#fb923c` | [Storage:Cache], [Storage:Local] |
| **Default** | Gray | `#94a3b8` | [Models/Content], lainnya |

### Alasan Pemilihan Warna

- **Shell (Kuning)**: Infrastructure/system - mudah dikenali
- **Player (Hijau)**: Media/content player - hijau = "play"
- **Network (Biru)**: Network/communication - biru = "data flow"
- **Device (Cyan)**: Device/hardware - cyan = "device info"
- **Toast (Merah)**: User notifications - merah cerah untuk visibility
- **Storage (Orange)**: Data persistence - orange = "storage"
- **Default (Gray)**: Uncategorized - neutral

---

## File yang Diubah

### `/mnt/g/khoirul/signate/player-vite/src/shared/logger/shared-logger.ts`

**Line 88-113**: Update NAMESPACE_COLORS
```typescript
const NAMESPACE_COLORS: Record<string, string> = {
  // Shell (yellow - infrastructure/system)
  Shell: 'color: #fbbf24; font-weight: bold',

  // Player (green - media/content player)
  Player: 'color: #4ade80; font-weight: bold',

  // Network (blue - network/communication)
  Network: 'color: #60a5fa; font-weight: bold',

  // Device (cyan - device/hardware info)
  Device: 'color: #22d3ee; font-weight: bold',
  DeviceInfo: 'color: #22d3ee; font-weight: bold',
  DeviceFingerprint: 'color: #22d3ee; font-weight: bold',

  // UI (bright red - user notifications)
  Toast: 'color: #f87171; font-weight: bold',
  Modal: 'color: #f87171; font-weight: bold',
  Popup: 'color: #f87171; font-weight: bold',

  // Storage (orange - data persistence)
  Storage: 'color: #fb923c; font-weight: bold',

  // Default (gray - others/uncategorized)
  default: 'color: #94a3b8; font-weight: bold',
};
```

---

## Proses Deployment

### Step 1: Build Locally

```bash
cd /mnt/g/khoirul/signate/player-vite
npm run build
```

**Output**: File baru `dist/assets/index-DEQyn_SS.js` akan dibuat.

### Step 2: Sync Source Code ke Server

**PENTING**: Dockerfile melakukan `npm run build` di DALAM Docker, jadi **WAJIB sync source code**, bukan hanya dist/.

```bash
# Sync source code
sshpass -p 'Password@2021' rsync -avz \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '.git' \
  src/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/src/
```

### Step 3: Rebuild Docker Image (Tanpa Cache)

**CRITICAL**: Gunakan `--no-cache` untuk memastikan build ulang dari source baru.

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && \
   docker-compose -f docker/docker-compose.yml build --no-cache player"
```

**Why `--no-cache`?**
- Docker build menggunakan cache layer
- Tanpa `--no-cache`, Docker akan skip step `RUN npm run build` jika source code terlihat sama
- Dengan `--no-cache`, Docker akan rebuild semua layer dari awal

### Step 4: Recreate Container

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker rm -f signage-player && \
   cd /home/gzjbbk/signate && \
   docker-compose -f docker/docker-compose.yml up -d player"
```

### Step 5: Clear Nginx Cache

**CRITICAL**: Nginx cache JS files selama 1 tahun dengan flag `immutable`.

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-player sh -c 'rm -rf /var/cache/nginx/* && nginx -s reload'"
```

**Nginx Cache Configuration** (`/etc/nginx/conf.d/nginx.conf`):
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Why Clear Nginx Cache?**
- JS files di-cache 1 tahun dengan `immutable` flag
- Browser TIDAK akan revalidate file, bahkan dengan hard refresh
- WAJIB clear nginx cache agar file baru di-serve

### Step 6: Verify Deployment

```bash
# Check file hash in container
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-player ls -lh /usr/share/nginx/html/assets/ | grep index-"

# Expected output: index-DEQyn_SS.js

# Verify colors in JS file
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-player strings /usr/share/nginx/html/assets/index-DEQyn_SS.js | \
   grep -E '(#fbbf24|#4ade80|#f87171)' | head -3"

# Expected output: Warna baru (yellow, green, red)
```

---

## User Browser Cache

### Hard Refresh

Setelah deployment, user WAJIB melakukan **hard refresh**:

1. **Tutup semua tab** yang membuka http://192.168.5.12:8080/
2. **Hard Refresh**:
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`
3. Buka lagi: http://192.168.5.12:8080/
4. Buka DevTools (F12) → Console

### Complete Cache Clear (Jika Hard Refresh Tidak Cukup)

1. Buka: `chrome://settings/clearBrowserData`
2. Time range: **All time**
3. Centang: **Cached images and files**
4. Klik **Clear data**
5. Restart Chrome
6. Buka http://192.168.5.12:8080/

### Check Service Worker

```
chrome://serviceworker-internals/
```

Cari `192.168.5.12:8080`, jika ada klik **Unregister**.

### Verify File Loaded

Di DevTools:
1. Tab **Network**
2. Refresh halaman
3. Filter: `JS`
4. Cari file: Harus `index-DEQyn_SS.js`

---

## Troubleshooting

### Issue 1: Warna Tidak Berubah Setelah Deployment

**Symptoms**: Console log masih menampilkan warna lama.

**Checklist**:
1. ✅ Verify file hash di container: `docker exec signage-player ls /usr/share/nginx/html/assets/`
2. ✅ Verify warna di JS file: `docker exec signage-player strings /usr/share/nginx/html/assets/index-*.js | grep '#fbbf24'`
3. ✅ Clear nginx cache: `docker exec signage-player rm -rf /var/cache/nginx/* && nginx -s reload`
4. ✅ User hard refresh: Ctrl + Shift + R
5. ✅ Clear browser cache: chrome://settings/clearBrowserData

### Issue 2: Docker Build Menggunakan File Lama

**Symptoms**: Setelah rebuild, file di container masih hash lama.

**Root Cause**: Docker menggunakan cache layer.

**Solution**:
1. Hapus file lama di host:
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate/player-vite/dist/assets && \
   rm -f index-BTHA8azT.* index-BYKiNfKT.* index-DkwVLDmO.*"
```

2. Rebuild dengan `--no-cache`:
```bash
docker-compose -f docker/docker-compose.yml build --no-cache player
```

### Issue 3: Source Code Tidak Terupdate di Server

**Symptoms**: Rebuild Docker menghasilkan build lama.

**Root Cause**: Source code di server tidak di-sync.

**Solution**: Sync source code SEBELUM rebuild Docker:
```bash
sshpass -p 'Password@2021' rsync -avz \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '.git' \
  src/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/src/
```

---

## Complete Deployment Script

```bash
#!/bin/bash
# Deploy console color changes to production

set -e

echo "🔨 Step 1: Build locally..."
cd /mnt/g/khoirul/signate/player-vite
npm run build

echo "📤 Step 2: Sync source code to server..."
sshpass -p 'Password@2021' rsync -avz \
  --exclude 'node_modules' \
  --exclude 'dist' \
  --exclude '.git' \
  src/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/player-vite/src/

echo "🐳 Step 3: Rebuild Docker image (no cache)..."
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && \
   docker-compose -f docker/docker-compose.yml build --no-cache player"

echo "🔄 Step 4: Recreate container..."
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker rm -f signage-player && \
   cd /home/gzjbbk/signate && \
   docker-compose -f docker/docker-compose.yml up -d player"

echo "⏳ Waiting for container to start..."
sleep 8

echo "🧹 Step 5: Clear nginx cache..."
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-player sh -c 'rm -rf /var/cache/nginx/* && nginx -s reload'"

echo "✅ Step 6: Verify deployment..."
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-player ls -lh /usr/share/nginx/html/assets/ | grep index-"

echo "🔍 Verify colors in JS file..."
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-player strings /usr/share/nginx/html/assets/index-*.js | \
   grep -E '(#fbbf24|#4ade80|#f87171)' | head -3"

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📝 Next steps for users:"
echo "  1. Close all tabs with http://192.168.5.12:8080/"
echo "  2. Hard refresh: Ctrl + Shift + R"
echo "  3. Open http://192.168.5.12:8080/"
echo "  4. Open DevTools (F12) → Console"
echo ""
echo "Expected colors:"
echo "  - [Shell:xxx] → Yellow (#fbbf24)"
echo "  - [PlayerVideoJS] → Green (#4ade80)"
echo "  - [NetworkHeartbeat] → Blue (#60a5fa)"
echo "  - [DeviceInfo] → Cyan (#22d3ee)"
echo "  - [Toast] → Bright Red (#f87171)"
echo "  - [Storage:xxx] → Orange (#fb923c)"
```

---

## Technical Details

### Chrome %c Processing Rule

Chrome's console.log processes `%c` directives ONLY in the FIRST argument:

✅ **Correct**:
```typescript
console.log('%cNamespace%c Message', 'color: red', 'color: inherit');
console.log(`${emoji} %cNamespace%c Message`, 'color: red', 'color: inherit');
```

❌ **Wrong**:
```typescript
console.log(emoji, '%cNamespace%c Message', 'color: red', 'color: inherit');
// %c directives in second argument are IGNORED
```

### Docker Multi-stage Build

Dockerfile uses multi-stage build:
```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build  # Build happens HERE

# Stage 2: Production
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

**Key Point**: Build happens INSIDE Docker, NOT using local dist/.

### Nginx Cache Behavior

```nginx
location ~* \.(js|css)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

- `expires 1y`: Cache for 1 year
- `immutable`: Never revalidate, even on refresh
- Requires clearing nginx cache on every deployment

---

## Testing

### Manual Testing

1. Open http://192.168.5.12:8080/
2. Open DevTools (F12) → Console
3. Verify colors:
   - Shell logs should be **yellow**
   - Player logs should be **green**
   - Network logs should be **blue**
   - Device logs should be **cyan**
   - Toast logs should be **bright red**
   - Storage logs should be **orange**

### Test HTML Files

Test files created during development:
- `/tmp/test-bright-colors.html` - Preview bright colors on dark background
- `/tmp/test-split-namespace.html` - Test namespace-only coloring
- `/tmp/test-exact-syntax.html` - Test %c formatting syntax

---

## References

- **Build Hash**: `index-DEQyn_SS.js`
- **Deployment Date**: 2025-11-20
- **Docker Image**: `docker_player:latest` (hash: `20f93394685e`)
- **Nginx Version**: nginx:alpine
- **Node Version**: 18-alpine

---

## Future Improvements

1. **Dynamic Color Adjustment**: Allow users to customize colors via config
2. **Color Presets**: Light/dark theme presets
3. **Automated Deployment**: CI/CD pipeline for automatic deployment
4. **Cache Busting**: Implement better cache busting strategy
5. **Service Worker**: Remove aggressive caching from service worker

---

## Changelog

### v1.0 (2025-11-20)
- Initial documentation
- Documented console color fix
- Added nginx cache clearing steps
- Added complete deployment script
- Added troubleshooting guide

---

**Author**: Claude Code
**Last Updated**: 2025-11-20
**Status**: Production-ready ✅
