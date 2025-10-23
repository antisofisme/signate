# WebOS Viewer (Production)

WebOS TV production viewer yang di-serve di **port 8081**.

## 🎯 Port Separation

Kita pisahkan environment untuk kemudahan development dan testing:

| Port | Environment | Purpose |
|------|-------------|---------|
| **8080** | Browser Testing | Testing di browser (development) |
| **8081** | WebOS Production | WebOS TV production app |

## 🚀 Running the Server

### On Server (Production)

```bash
# Navigate to webos-viewer directory
cd /home/gzjbbk/signage/webos-viewer

# Start server on port 8081
python3 -m http.server 8081

# Or run in background
nohup python3 -m http.server 8081 > viewer.log 2>&1 &
```

### On Local (Development)

```bash
cd /mnt/g/khoirul/signate/webos-viewer
python3 -m http.server 8081
```

## 📱 WebOS App Configuration

WebOS app (`webos-app/appinfo.json`) configured to load from:

```json
{
  "main": "http://192.168.5.12:8081/index.html"
}
```

## 🔄 Content Synchronization

File `index.html` di `webos-viewer/` adalah viewer untuk WebOS TV yang menggunakan UUID-based device identity.

**BERBEDA dengan `browser-viewer/`:**
- `browser-viewer/` → 6-digit activation code (untuk monitor browser)
- `webos-viewer/` → UUID persistent (untuk WebOS TV)

### Update WebOS Viewer

Jika ada perubahan pada `webos-viewer/index.html`:

```bash
# Deploy to server
scp /mnt/g/khoirul/signate/webos-viewer/index.html gzjbbk@192.168.5.12:/home/gzjbbk/signage/webos-viewer/
```

## 🧪 Testing

### Browser Testing (Port 8080)
```
http://192.168.5.12:8080/index.html
```

### WebOS Testing (Port 8081)
```
# Package and install WebOS app
cd webos-app
./package.sh
./deploy.sh mytv

# App will load from:
http://192.168.5.12:8081/index.html
```

## ✅ Benefits of Separation

1. **Independent Testing**: Test di browser tanpa mempengaruhi WebOS production
2. **Version Control**: Bisa roll back production tanpa affect testing
3. **Performance**: Pisahkan traffic browser testing dan TV production
4. **Easy Debugging**: Logs terpisah untuk setiap environment

## 🔧 Server Setup

### Check if Port 8081 is Available

```bash
# Check if port 8081 is in use
netstat -tulpn | grep :8081

# Or with lsof
lsof -i :8081
```

### Start Server on Boot (Optional)

Create systemd service:

```bash
# /etc/systemd/system/webos-viewer.service
[Unit]
Description=WebOS Viewer HTTP Server
After=network.target

[Service]
Type=simple
User=gzjbbk
WorkingDirectory=/home/gzjbbk/signage/webos-viewer
ExecStart=/usr/bin/python3 -m http.server 8081
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable webos-viewer
sudo systemctl start webos-viewer
sudo systemctl status webos-viewer
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    192.168.5.12 Server                       │
│                                                              │
│  ┌────────────────────────┐  ┌─────────────────────────┐  │
│  │  Port 8080             │  │  Port 8081              │  │
│  │  browser-viewer/       │  │  webos-viewer/          │  │
│  │  (Browser Testing)     │  │  (WebOS Production)     │  │
│  │                        │  │                         │  │
│  │  - Development         │  │  - Production           │  │
│  │  - Quick testing       │  │  - WebOS TV App         │  │
│  │  - DevTools available  │  │  - Stable version       │  │
│  └────────────────────────┘  └─────────────────────────┘  │
│            ↓                            ↓                    │
│    Browser (Chrome/Firefox)      LG WebOS TV                │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Use Cases

### Development Flow

1. Edit code in `webos-viewer/index.html`
2. Test di browser → `http://192.168.5.12:8081`
3. If stable, package WebOS app
4. Deploy IPK to WebOS TV

### Production Flow

1. WebOS TV runs app from Port 8081
2. Updates via `webos-viewer/index.html`
3. No need to reinstall IPK (hosted app!)
4. Just refresh content

## 🔐 Security

Both ports serve same content, but:
- Port 8080: Development/testing (can have bugs)
- Port 8081: Production (stable, tested version)

## 📝 Notes

- Kedua port serve file yang sama (`index.html`)
- Pisahkan port untuk isolasi environment
- WebOS app hanya load dari port 8081 (production)
- Browser testing bisa gunakan port 8080 atau 8081

---

**Current Status**:
- ✅ Port 8080 running (Browser Testing)
- ⏳ Port 8081 setup (WebOS Production)
