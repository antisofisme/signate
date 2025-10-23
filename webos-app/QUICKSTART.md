# WebOS App Quick Start Guide

Panduan cepat untuk deploy Digital Signage app ke LG Smart TV.

## 🚀 Quick Setup (15 menit)

### 1. Install WebOS CLI Tools (5 menit)

```bash
# Install globally
npm install -g @webos-tools/cli

# Verify
ares --version
```

### 2. Enable Developer Mode di TV (5 menit)

1. Buka **LG Content Store** di TV
2. Search dan install: **"Developer Mode"**
3. Buka **Developer Mode** app
4. Turn ON: **Developer Mode**
5. Turn ON: **Key Server**
6. Catat **IP Address** TV (misal: 192.168.5.100)

### 3. Setup TV Connection (2 menit)

```bash
ares-setup-device

# Masukkan info:
# name: mytv
# host: 192.168.5.100  ← IP TV Anda
# port: 9922           ← default
# user: prisoner       ← default
# (enter untuk sisanya)
```

### 4. Package & Deploy (3 menit)

```bash
cd webos-app

# Package app
./package.sh

# Deploy ke TV
./deploy.sh

# Jawab 'y' untuk launch app
```

## 🎯 Activation (2 menit)

1. **TV** akan tampilkan **6-digit code**
2. Buka **Web Admin**: http://localhost:3000/devices
3. Klik device yang baru muncul
4. Klik **Activate**
5. **Done!** TV siap dipakai

## 📱 Add Content (1 menit)

1. Go to **Content** page
2. Click **Upload** button
3. Select images/videos
4. Click device name
5. **Assign content**
6. TV auto-update dalam **10 detik**!

## 🔧 Useful Commands

```bash
# List installed apps
ares-install --device mytv --list

# Launch app
ares-launch --device mytv com.signage.viewer

# Close app
ares-launch --device mytv --close com.signage.viewer

# Uninstall app
ares-install --device mytv --remove com.signage.viewer

# View logs
ares-log --device mytv --follow

# Debug app
ares-inspect --device mytv --app com.signage.viewer --open
```

## ❓ Troubleshooting

### App tidak bisa di-install

```bash
# Check connection
ares-device-info -d mytv

# Re-setup device
ares-setup-device
```

### Activation code tidak muncul

1. Check server running: http://192.168.5.12:8080
2. Check backend API: http://192.168.5.12:8001/health
3. Reload app:
   ```bash
   ares-launch --device mytv --close com.signage.viewer
   ares-launch --device mytv com.signage.viewer
   ```

### Content tidak update

1. Check device status "active" di Web Admin
2. Wait 10 seconds (auto-refresh interval)
3. Manual refresh: Restart app

## 📞 Need Help?

Check full README.md untuk detailed guide.

---

**Total Setup Time**: ~15 menit
**Difficulty**: Easy ✅
