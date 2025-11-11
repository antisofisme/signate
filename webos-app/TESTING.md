# WebOS App Testing Guide

Panduan lengkap untuk testing WebOS app tanpa TV fisik.

## 🎯 Testing Options

Ada 4 cara testing WebOS app (dari tercepat ke paling lengkap):

1. **Browser Testing** ⚡ Tercepat, untuk hosted app
2. **WebOS Simulator** 🚀 Modern (webOS TV 22+), tanpa IPK
3. **ares-server** 📡 Local WebOS environment
4. **WebOS Emulator** 📺 Full TV simulation (deprecated untuk webOS TV 22+)

## 1️⃣ Browser Testing (Recommended untuk Hosted App)

Karena app kita adalah **hosted app** (load dari web server), kita bisa test langsung di browser!

### Quick Test

```bash
# Pastikan viewer server running
cd ../viewer
python3 -m http.server 8080

# Buka di browser
# Chrome: http://localhost:8080
# Firefox: http://localhost:8080
```

### Simulate TV Resolution

Di Chrome DevTools:
1. **Press F12** → Open DevTools
2. **Click** device toolbar icon (Ctrl+Shift+M)
3. **Select** "Responsive"
4. **Set dimensions**: 1920 x 1080
5. **Reload** page

### Test Features

✅ Activation code muncul
✅ Registration ke backend
✅ Playlist loading
✅ Content playback
✅ Offline caching (DevTools → Application → IndexedDB)
✅ Auto-refresh (console logs)

## 2️⃣ WebOS Simulator (Recommended untuk webOS TV 22+)

**MODERN** approach - tidak perlu build IPK, langsung run dari source folder!

### Prerequisites

1. **WebOS Studio** atau **WebOS CLI** terinstall
2. **Download Simulator** untuk OS kamu:
   - https://webostv.developer.lge.com/develop/tools/simulator-installation

### Quick Start

```bash
# Run app di Simulator (TANPA build IPK!)
ares-launch --simulator /mnt/g/khoirul/signate/webos-app

# Pastikan viewer server running:
cd ../viewer && python3 -m http.server 8080
```

### Advanced Usage

```bash
# Specify Simulator version
ares-launch -s 23 -sp /path/to/webOS_TV_23_Simulator webos-app

# With auto-reload on code changes
ares-launch --simulator --inspect webos-app
```

### Features

- ✅ **Instant reload** saat code berubah
- ✅ **Built-in inspector** (auto-open Chrome DevTools)
- ✅ **No IPK needed** - langsung run dari source
- ✅ **Faster iteration** - save → reload otomatis
- ⚠️ Simulator hanya untuk webOS TV 22+ (versi baru)

### Expected Behavior

1. Simulator launch → Load `webos-app/index.html`
2. index.html check server (http://192.168.5.12:8080)
3. Jika server running → Redirect ke viewer full
4. Jika server offline → Show error + retry

## 3️⃣ ares-server (Local WebOS Environment)

WebOS CLI menyediakan local web server yang mensimulasikan WebOS environment.

### Setup

```bash
# Install WebOS CLI (if not yet)
npm install -g @webos-tools/cli

# Navigate to app directory
cd webos-app

# Run local server
ares-server

# Output:
# Serving the app at: http://localhost:1337/index.html
```

### Usage

```bash
# Start server (runs in background)
ares-server --open

# Server akan otomatis buka browser
# URL: http://localhost:1337
```

### Features

- ✅ Simulates WebOS environment
- ✅ Tests app loading
- ✅ Tests hosted app URL redirect
- ✅ Shows WebOS-specific logs
- ⚠️ Tidak bisa test TV-specific features

## 4️⃣ WebOS Emulator (Full TV Simulation - Deprecated)

**⚠️ WARNING:** Emulator deprecated untuk webOS TV 22+. Gunakan **Simulator** sebagai gantinya!

Emulator adalah virtual TV yang berjalan di VirtualBox.

### Prerequisites

1. **VirtualBox** - Download dari https://www.virtualbox.org/
2. **WebOS SDK** - Download dari LG Developer site
3. **Minimum RAM**: 4GB (8GB recommended)
4. **Disk Space**: 10GB free

### Download WebOS Emulator

1. **Register** di: https://webostv.developer.lge.com/
2. **Download SDK**: https://webostv.developer.lge.com/sdk/download/download-sdk/
3. **Download Emulator Image**: webOS TV Emulator
4. **File size**: ~3GB

### Installation

#### Windows

```bash
# Install SDK
webOS_TV_SDK_2.x.x_Windows.exe

# Launch SDK Manager
# Tools → Emulator Manager → Install
```

#### macOS

```bash
# Install SDK
sudo installer -pkg webOS_TV_SDK_2.x.x.pkg -target /

# Launch SDK Manager
/opt/webOS_TV_SDK/bin/webOS_TV_SDK_Manager
```

#### Linux

```bash
# Extract SDK
tar -xzf webOS_TV_SDK_2.x.x_Linux.tar.gz

# Run installer
cd webOS_TV_SDK_2.x.x
./install.sh

# Launch SDK Manager
./webOS_TV_SDK_Manager
```

### Setup Emulator

1. **Open SDK Manager**
2. **Go to**: Emulator Manager
3. **Click**: Add Emulator
4. **Select**: webOS TV version (recommended: latest)
5. **Configure**:
   - Name: webOS_TV_Emulator
   - RAM: 2048 MB
   - Screen: 1920x1080
6. **Click**: Create

### Launch Emulator

```bash
# Via CLI
ares-emulator --list
ares-emulator --launch webOS_TV_Emulator

# Via SDK Manager
# Emulator Manager → Select → Launch
```

### Connect to Emulator

```bash
# Add emulator as device
ares-setup-device

# Configuration:
# name: emulator
# host: 127.0.0.1
# port: 6622  ← Default emulator port
# user: prisoner
# (enter for rest)

# Verify connection
ares-device-info -d emulator
```

### Deploy to Emulator

```bash
# Package app
cd webos-app
./package.sh

# Install to emulator
ares-install --device emulator ../build/com.signage.viewer_1.0.0_all.ipk

# Launch app
ares-launch --device emulator com.signage.viewer
```

## 🧪 Testing Checklist

### Basic Functionality

- [ ] App launches successfully
- [ ] Activation code displays (6-digit)
- [ ] Registration API call works
- [ ] Backend connectivity (192.168.5.12:8001)

### Content Management

- [ ] Playlist loads from API
- [ ] Content downloads to cache
- [ ] Images display correctly
- [ ] Videos play with audio
- [ ] Content transitions smooth

### Caching System

- [ ] IndexedDB initialized
- [ ] Content cached on first load
- [ ] Subsequent plays use cache
- [ ] Cache syncs on playlist update
- [ ] Old content removed from cache

### Auto-Update

- [ ] Playlist refreshes every 10 seconds
- [ ] New content auto-downloads
- [ ] Removed content deleted from cache
- [ ] Playback updates without restart

### Performance

- [ ] App loads < 3 seconds
- [ ] Content switching < 500ms
- [ ] Memory usage stable
- [ ] No memory leaks (run 1 hour)
- [ ] CPU usage acceptable

## 🔍 Debugging

### Browser DevTools

```bash
# Chrome DevTools shortcuts
F12 - Toggle DevTools
Ctrl+Shift+I - Inspect element
Ctrl+Shift+C - Select element
Ctrl+Shift+J - Console

# Useful tabs:
# - Console: Logs and errors
# - Network: API calls
# - Application: IndexedDB cache
# - Performance: FPS and memory
```

### WebOS Inspector

```bash
# Launch inspector for emulator
ares-inspect --device emulator --app com.signage.viewer --open

# Opens Chrome DevTools connected to emulator
# URL: chrome://inspect
```

### Useful Console Commands

```javascript
// Check cache status
await getAllCachedContentIds()

// Get cached content
await getCachedContent(35)

// Check device info
getDeviceInfo()

// Force playlist refresh
refreshPlaylist()

// Clear cache (debugging)
indexedDB.deleteDatabase('SignageMediaCache')
```

## 📊 Performance Monitoring

### Check Memory Usage

```javascript
// In browser console
console.log(performance.memory)

// Monitor over time
setInterval(() => {
  console.log('Memory:', 
    (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB'
  )
}, 5000)
```

### Check Cache Size

```javascript
// In DevTools → Application → IndexedDB
// Right-click → Clear
// Or via code:
navigator.storage.estimate().then(estimate => {
  console.log('Cache size:', 
    (estimate.usage / 1048576).toFixed(2) + ' MB'
  )
  console.log('Available:', 
    (estimate.quota / 1048576).toFixed(2) + ' MB'
  )
})
```

## 🐛 Common Issues

### Emulator Won't Start

**Problem**: Emulator stuck on logo

**Solutions**:
1. Increase RAM allocation (4GB minimum)
2. Disable Hyper-V (Windows):
   ```bash
   bcdedit /set hypervisorlaunchtype off
   ```
3. Enable VT-x in BIOS
4. Restart VirtualBox service

### App Not Installing

**Problem**: `ares-install` fails on emulator

**Solutions**:
1. Check emulator is running
2. Verify connection: `ares-device-info -d emulator`
3. Re-setup device: `ares-setup-device`
4. Check port 6622 not blocked

### Network Not Reachable

**Problem**: App can't reach 192.168.5.12 from emulator

**Solutions**:
1. Change backend URL to localhost:
   - Update viewer to use `http://localhost:8001`
   - Port forward from host to emulator
2. Use host IP instead of localhost
3. Configure VirtualBox network to bridged mode

### Content Not Caching

**Problem**: Cache not working in emulator

**Solutions**:
1. Check IndexedDB support in emulator browser
2. Check disk space in emulator VM
3. Test in regular browser first
4. Check console for errors

## 💡 Best Testing Strategy (Updated 2025)

### Development Phase (Fast Iteration)

1. **Browser Testing** ⚡ (5 menit)
   - Test UI changes
   - Test API integration
   - Test caching logic
   - **Tercepat untuk debug!**

2. **WebOS Simulator** 🚀 (10 menit - webOS TV 22+)
   - Test hosted app loading & redirect
   - Verify WebOS compatibility
   - Test app lifecycle
   - Auto-reload on code changes
   - **RECOMMENDED untuk development!**

### Pre-Production

3. **ares-server** 📡 (15 menit)
   - Test WebOS environment
   - Verify app configuration
   - Test without Simulator/Emulator

4. **Emulator** 📺 (30 menit - ONLY for webOS TV 6.0 or older)
   - ⚠️ Deprecated untuk webOS TV 22+
   - Use Simulator instead jika memungkinkan

### Production

5. **Real TV** ✅ (5 menit - final validation)
   - Test on actual hardware
   - Verify resolution/quality
   - Long-term stability test (24+ hours)
   - Test remote control interaction

## 📚 Resources

- **WebOS CLI Docs**: https://webostv.developer.lge.com/develop/tools/cli-dev-guide
- **Emulator Guide**: https://webostv.developer.lge.com/develop/tools/emulator-introduction
- **WebOS Forum**: https://forum.webostv.developer.lge.com/

---

**Recommendation (2025)**:
1. **Development**: Start dengan **Browser Testing** (tercepat)
2. **Verification**: Test di **WebOS Simulator** (untuk webOS TV 22+)
3. **Production**: Final test di **Real TV** sebelum deploy

**⚠️ Skip Emulator** - deprecated untuk webOS TV 22+, gunakan Simulator!

**Estimated Testing Time**:
- Browser: 5 minutes ⚡
- WebOS Simulator: 10 minutes 🚀 (RECOMMENDED)
- ares-server: 15 minutes
- Emulator: 30 minutes (deprecated, skip jika bisa)
- Real TV: 5 minutes ✅ (final validation)
