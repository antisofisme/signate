# WebOS Smart TV Digital Signage App

WebOS hosted application untuk LG Smart TV yang mengambil konten dari server dan bisa di-update secara remote.

## 📋 Fitur

- ✅ **Hosted App** - Load dari web server, tidak perlu re-install untuk update
- ✅ **Remote Content** - Konten di-manage dari Web Admin
- ✅ **Auto Update** - TV otomatis ambil konten baru setiap 10 detik
- ✅ **Offline Cache** - Konten di-cache di TV, hemat bandwidth
- ✅ **Full HD** - Support 1920x1080 resolution
- ✅ **Multi Format** - Images (PNG, JPEG, WebP) & Videos (MP4)

## 🏗️ Arsitektur

```
LG Smart TV (WebOS App)
        ↓
    Load App dari Server
  (http://192.168.5.12:8080)
        ↓
   Fetch Playlist dari API
  (http://192.168.5.12:8001)
        ↓
    Cache Konten ke TV
        ↓
  Play Content Offline
```

## 📁 Structure

```
webos-app/
├── appinfo.json          # WebOS app configuration
├── index.html            # Loader that redirects to server (hosted app)
├── icon.png              # App icon 80x80
├── largeIcon.png         # Large icon 130x130
├── bg.png                # Background image 1920x1080
└── README.md             # This file
```

## 🔧 Prerequisites

### 1. Install WebOS CLI Tools

```bash
# Install ares-cli globally
npm install -g @webos-tools/cli

# Verify installation
ares --version
ares-package --version
ares-install --version
ares-launch --version
```

### 2. Enable Developer Mode pada LG TV

1. **Buka LG Content Store** di TV
2. **Search dan install**: "Developer Mode"
3. **Buka Developer Mode app**
4. **Enable**: Developer Mode → ON
5. **Enable**: Key Server → ON
6. **Catat**: IP Address TV (misal: 192.168.5.100)

### 3. Setup TV Connection

```bash
# Add TV sebagai device
ares-setup-device

# Ikuti prompt:
# name: mytv
# host: 192.168.5.100 (IP TV Anda)
# port: 9922 (default)
# user: prisoner (default)
# description: My LG TV
# password: (kosongkan)
# privatekey: (kosongkan untuk default)
# passphrase: (kosongkan)
# default: y

# Verify connection
ares-device-info -d mytv
```

## 🚀 Build & Deploy

### 1. Package App

```bash
# Dari root directory signate
cd webos-app

# Package app menjadi .ipk file
ares-package . --outdir ../build

# Output: ../build/com.signage.viewer_1.0.0_all.ipk
```

### 2. Install ke TV

```bash
# Install app ke TV
ares-install --device mytv ../build/com.signage.viewer_1.0.0_all.ipk

# Verify installation
ares-install --device mytv --list
```

### 3. Launch App

```bash
# Launch app di TV
ares-launch --device mytv com.signage.viewer

# Close app
ares-launch --device mytv --close com.signage.viewer
```

### 4. Debug App (Optional)

```bash
# Enable inspector untuk debugging
ares-inspect --device mytv --app com.signage.viewer --open

# Buka di Chrome: chrome://inspect
```

## 📱 Usage

### First Time Setup

1. **Install app** ke TV (lihat section Build & Deploy)
2. **Launch app** - akan muncul activation code
3. **Buka Web Admin** (http://localhost:3000)
4. **Go to Devices** page
5. **Activate** device dengan code yang muncul di TV
6. **Assign content** ke device
7. **TV otomatis** download dan play content!

### Update Content

1. **Buka Web Admin**
2. **Go to Content** page
3. **Upload** konten baru atau edit existing
4. **Go to Devices** page
5. **Klik device** yang ingin di-update
6. **Assign/Unassign** content
7. **TV auto-refresh** dalam 10 detik dan download konten baru!

### Update Viewer Code (TANPA Reinstall IPK!)

**Ini yang PALING PENTING** - Hosted app architecture memungkinkan update tanpa reinstall:

```bash
# 1. Fix bug di viewer/ (local)
vim ../viewer/js/player/playback.js

# 2. Test lokal
cd ../viewer
python3 -m http.server 8080

# 3. Sync ke server
sshpass -p 'Password@2021' scp -r ../viewer/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/

# 4. TV langsung dapat update - TIDAK PERLU REINSTALL IPK! ✅
# Restart app di TV (tutup → buka lagi) → Otomatis load versi baru
```

**Kenapa tidak perlu reinstall?**
- IPK hanya berisi `index.html` yang redirect ke server
- Semua viewer code (JS/HTML) ada di server (http://192.168.5.12:8080)
- Update di server = TV langsung dapat update!

### Update IPK (JARANG Diperlukan)

Rebuild IPK HANYA jika:
- ✅ Ubah icon/logo (icon.png, largeIcon.png, bg.png)
- ✅ Ubah appinfo.json (app ID, version, permissions)
- ✅ Ubah server URL di index.html

```bash
# 1. Update file yang perlu (icon, appinfo.json, dll)

# 2. Rebuild IPK
cd /mnt/g/khoirul/signate
ares-package webos-app -o webos-ipk/

# 3. Reinstall ke TV
ares-install --device mytv webos-ipk/com.signage.viewer_1.0.1_all.ipk

# 4. Launch
ares-launch --device mytv com.signage.viewer
```

## 🎨 Customization

### Icon Files

Buat icon untuk app:

1. **icon.png** - 80x80 pixels
2. **largeIcon.png** - 130x130 pixels
3. **bg.png** - 1920x1080 pixels (optional)

Simpan di folder `webos-app/icons/` lalu copy ke root `webos-app/`.

### App Configuration

Edit `appinfo.json` untuk customize:

```json
{
  "id": "com.signage.viewer",        // Unique app ID
  "version": "1.0.0",                 // App version
  "title": "Digital Signage Viewer",  // Nama app di TV
  "main": "index.html",               // Entry point (redirects to server)
  "resolution": "1920x1080"           // Target resolution
}
```

### Server URL

Jika server pindah IP, update di `webos-app/index.html`:

```javascript
// Line 12 in index.html
const SERVER_URL = 'http://NEW_IP:8080/index.html';
```

**Note:** Tidak perlu rebuild IPK! File `index.html` hanya perlu diupdate di TV saat reinstall pertama kali.

## 🧪 Testing

### Test with Simulator (Recommended - No IPK needed!)

**For webOS TV 22+ Simulator** - Test langsung tanpa build IPK:

```bash
# Run directly from source folder
ares-launch --simulator /mnt/g/khoirul/signate/webos-app

# Simulator will load index.html and redirect to server
```

**Pastikan viewer server running:**
```bash
cd ../viewer
python3 -m http.server 8080
```

### Test Local (Browser Testing)

```bash
# Run local web server
cd ../viewer
python3 -m http.server 8080

# Akses dari browser untuk test
# URL: http://192.168.5.12:8080
```

### Test Deployed App

1. **Launch app** di TV
2. **Check activation** code muncul
3. **Test activation** via Web Admin
4. **Test content** assignment
5. **Test playlist** refresh (assign content baru)
6. **Test offline** mode (disconnect WiFi)

## 🐛 Troubleshooting

### App Tidak Bisa Di-install

**Problem**: `ares-install` gagal

**Solutions**:
1. Check Developer Mode enabled di TV
2. Check Key Server enabled di TV
3. Check TV dan PC di network yang sama
4. Verify device setup: `ares-setup-device`
5. Test connection: `ares-device-info -d mytv`

### App Crash atau Tidak Load

**Problem**: App launch tapi blank/crash

**Solutions**:
1. Check server running: http://192.168.5.12:8080
2. Check backend API running: http://192.168.5.12:8001
3. Check appinfo.json "main" URL correct
4. Check TV browser console:
   ```bash
   ares-inspect --device mytv --app com.signage.viewer --open
   ```

### Content Tidak Update

**Problem**: Assign content baru tapi TV tidak refresh

**Solutions**:
1. Check playlist refresh timer (10 seconds)
2. Check device status "active" di Web Admin
3. Check heartbeat working (last_seen < 1 minute)
4. Manually reload app:
   ```bash
   ares-launch --device mytv --close com.signage.viewer
   ares-launch --device mytv com.signage.viewer
   ```

### Activation Code Tidak Muncul

**Problem**: App load tapi no activation code

**Solutions**:
1. Check backend API reachable from TV
2. Check CORS configured untuk TV IP
3. Check IndexedDB available di TV browser
4. Check console logs untuk errors

## 📊 Monitoring

### Check App Status

```bash
# List installed apps
ares-install --device mytv --list | grep signage

# Check running apps
ares-launch --device mytv --running

# Check device info
ares-device-info -d mytv
```

### Check Logs

```bash
# View app logs
ares-log --device mytv --follow
```

### Remote Debugging

```bash
# Enable inspector
ares-inspect --device mytv --app com.signage.viewer --open

# Buka Chrome DevTools:
# chrome://inspect
# Click "Open dedicated DevTools for Node"
```

## 🔐 Security Notes

1. **Developer Mode** hanya untuk development/testing
2. **Production**: Disable Developer Mode setelah deploy
3. **Network**: TV dan server harus di network yang sama
4. **Firewall**: Allow port 8080 (viewer) dan 8001 (API)

## 📚 Resources

- [WebOS CLI Documentation](https://webostv.developer.lge.com/develop/tools/cli-dev-guide)
- [WebOS App Development](https://webostv.developer.lge.com/develop/app-developer-guide)
- [Hosted App Guide](https://webostv.developer.lge.com/develop/app-developer-guide/web-app-types)

## 🎯 Next Steps

Setelah setup awal berhasil:

1. [ ] Deploy app ke semua TV di jaringan
2. [ ] Monitor device status via Web Admin
3. [ ] Setup auto-launch on boot (optional)
4. [ ] Create production icons
5. [ ] Document TV IP addresses
6. [ ] Setup monitoring/alerts

## 🚀 Production Checklist

Before deploying to production TVs:

- [ ] Test app dengan berbagai content types
- [ ] Test offline mode (disconnect WiFi)
- [ ] Test cache management (add/remove content)
- [ ] Test auto-refresh mechanism
- [ ] Verify icon files quality
- [ ] Document TV locations and IPs
- [ ] Train staff on Web Admin usage
- [ ] Setup backup server (optional)

---

**Status**: ✅ Ready for Deployment
**Version**: 1.0.0
**Last Updated**: 2025-10-23
