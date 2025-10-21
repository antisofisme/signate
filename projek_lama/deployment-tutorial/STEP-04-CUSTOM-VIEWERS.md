# STEP 4: Deploy Custom Viewers

> **💡 Quick Start**: Untuk deployment yang lebih mudah, gunakan file yang sudah ready di direktori `anthias-ready-files/`. Files tersebut sudah dikonfigurasi dan tested untuk single viewer endpoint `/viewer`.

## 🎯 Apa yang akan kita lakukan?

Di step ini kita akan:
1. Deploy single enhanced viewer dengan horizontal layout
2. Configure nginx routing untuk endpoint `/viewer`
3. Test horizontal slide layout dan fullscreen functionality
4. Configure viewer settings

⚠️ **Update**: Tutorial ini sudah disederhanakan ke single viewer endpoint `/viewer` untuk kemudahan deployment.

## 🚨 **Critical Integration Points**

### A. Nginx Configuration di Container vs Host
- **Host File**: `/home/gzjbbk/Anthias/docker/nginx/nginx.development.conf`
- **Container File**: `/etc/nginx/sites-enabled/nginx.development.conf` 
- **⚠️ Penting**: Nginx config harus update di KEDUA tempat dan restart container

### B. File Path Resolution
- **Host Path**: `/home/gzjbbk/Anthias/static/custom-viewers/viewer.html`
- **Container Path**: `/srv/anthias/static/custom-viewers/viewer.html`
- **⚠️ Penting**: Volume mount atau manual copy harus sync kedua lokasi

### C. Cache Busting
- **Problem**: Nginx ETag caching serve file lama meski sudah update
- **Solution**: Restart nginx container atau force cache clear

## 📋 Custom Viewers Deployment

### 1. Persiapan Custom Viewer Files

**Apa itu**: Kita sudah develop custom viewers dengan horizontal layout dan fullscreen features. Sekarang kita copy ke server Anthias.

**Command cek custom viewer files di local**:
```bash
ls -la /home/gzjbbk/signate/viewers/
```

**Actual Output**:
```
anthias-viewer-standalone.html  # Standalone viewer dengan semua fitur
basic-viewer.html              # Basic viewer untuk testing
enhanced-viewer.html           # Enhanced viewer dengan advanced features
simple-viewer.html             # Simple viewer minimalis
README.md                      # Documentation
```

### 2. Copy Viewers ke Server Anthias

**Command copy files ke server**:
```bash
# Create custom directory di Anthias
mkdir -p /home/gzjbbk/Anthias/static/custom-viewers

# Copy all viewer files
scp /home/gzjbbk/signate/viewers/* gzjbbk@192.168.5.12:/home/gzjbbk/Anthias/static/custom-viewers/
```

**Command verify files copied**:
```bash
ls -la /home/gzjbbk/Anthias/static/custom-viewers/
```

**Actual Output**:
```
-rw-rw-r-- 1 gzjbbk gzjbbk  2305 Aug 15 05:08 README.md
-rw-rw-r-- 1 gzjbbk gzjbbk 19976 Aug 15 05:08 anthias-viewer-standalone.html
-rw-rw-r-- 1 gzjbbk gzjbbk  4837 Aug 15 05:08 basic-viewer.html
-rw-rw-r-- 1 gzjbbk gzjbbk 25821 Aug 15 05:08 enhanced-viewer.html
-rw-rw-r-- 1 gzjbbk gzjbbk 12743 Aug 15 05:08 simple-viewer.html
```

✅ **Status**: Custom viewer files berhasil di-copy ke server!

### 3. Update Anthias nginx Configuration

**Apa itu**: Tambahkan routing di nginx config agar custom viewers bisa diakses via URL.

**Command backup nginx config**:
```bash
cd /home/gzjbbk/Anthias && cp docker/nginx/nginx.development.conf docker/nginx/nginx.development.conf.backup
```

**Command edit nginx config**:
```bash
cd /home/gzjbbk/Anthias && cat >> docker/nginx/nginx.development.conf << 'EOF'

    # Custom viewers routing
    location /viewer-enhanced {
        alias /srv/anthias/static/custom-viewers/enhanced-viewer.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location /viewer-basic {
        alias /srv/anthias/static/custom-viewers/basic-viewer.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location /viewer-simple {
        alias /srv/anthias/static/custom-viewers/simple-viewer.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location /viewer-standalone {
        alias /srv/anthias/static/custom-viewers/anthias-viewer-standalone.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location /custom-viewers/ {
        alias /srv/anthias/static/custom-viewers/;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
EOF
```

### 4. Update Docker Volume Mounting

**Apa itu**: Tambahkan volume mount di docker-compose agar custom viewers accessible dari nginx container.

**Command backup docker-compose**:
```bash
cd /home/gzjbbk/Anthias && cp docker-compose.dev.yml docker-compose.dev.yml.backup3
```

**Command add volume mount ke nginx service**:
```bash
# Add volume mount untuk custom viewers di nginx service
cd /home/gzjbbk/Anthias && sed -i '/anthias-nginx:/,/restart: always/s/restart: always/volumes:\n      - .\/static\/custom-viewers:\/srv\/anthias\/static\/custom-viewers:ro\n      - anthias-data:\/data:ro\n    restart: always/' docker-compose.dev.yml
```

### 5. Restart nginx Container

**Command restart nginx untuk apply changes**:
```bash
cd /home/gzjbbk/Anthias && docker-compose -f docker-compose.dev.yml restart anthias-nginx
```

**Actual Output**:
```
Restarting anthias_anthias-nginx_1 ... done
```

**Command verify nginx running**:
```bash
cd /home/gzjbbk/Anthias && docker-compose -f docker-compose.dev.yml ps anthias-nginx
```

**Actual Output**:
```
NAME                     STATE      PORTS
anthias_anthias-nginx_1  Up         0.0.0.0:8000->80/tcp
```

✅ **Status**: nginx configuration updated dan restart berhasil!

### 6. Test Custom Viewers

**Test 1: Enhanced Viewer**
```bash
curl -I http://192.168.5.12:8000/viewer-enhanced
```

**Actual Output**:
```
HTTP/1.1 200 OK
Server: nginx
Content-Type: text/html; charset=utf-8
Cache-Control: no-cache, no-store, must-revalidate
```

**Test 2: All Viewers**
```bash
curl -I http://192.168.5.12:8000/viewer-basic
curl -I http://192.168.5.12:8000/viewer-simple  
curl -I http://192.168.5.12:8000/viewer-standalone
```

**Actual Output**: All return HTTP 200 OK ✅

**Test 3: Browser Test**
1. Buka browser: `http://192.168.5.12:8000/viewer-enhanced`
2. Anda harus lihat enhanced viewer dengan advanced features
3. Test dengan beberapa sample images/videos

### 7. Integration dengan Anthias Assets

**Apa itu**: Modifikasi custom viewer untuk menggunakan asset dari Anthias database.

**Command check Anthias API endpoint**:
```bash
curl http://anthias.local:8000/api/v1/assets
```

**Expected Output**:
```json
{
  "results": [],
  "count": 0
}
```

**Update viewer-horizontal.html untuk API integration**:
```bash
# Edit viewer untuk fetch dari Anthias API
ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/Anthias/static/custom-viewers && cp viewer-horizontal.html viewer-horizontal.html.backup"
```

**Add API integration code**:
```javascript
// Fetch assets from Anthias API
fetch('/api/v1/assets')
  .then(response => response.json())
  .then(data => {
    displayAssetsHorizontally(data.results);
  });
```

### 8. Test Fullscreen Functionality

**Command test fullscreen API**:
```bash
# Test dari browser:
# 1. Akses http://anthias.local:8000/viewer-fullscreen
# 2. Click "Start Fullscreen Slideshow"
# 3. Verify browser enters true fullscreen mode
# 4. Test navigation dengan arrow keys
# 5. Test exit fullscreen dengan ESC key
```

**Expected Behavior**:
- Browser masuk true fullscreen (tanpa address bar/toolbar)
- Slide navigation dengan keyboard arrows
- Auto-advance slides setiap 5 detik
- Smooth transitions antar slide

### 9. Configuration Management

**Test viewer-config.html**:
```bash
# Browser test:
# 1. Akses http://anthias.local:8000/viewer-config
# 2. Set slide duration, transition effects, autoplay
# 3. Save settings ke localStorage
# 4. Test settings applied di viewer lain
```

**Expected Features**:
- Slide duration slider (1-30 seconds)
- Transition effects dropdown
- Autoplay toggle
- Fullscreen mode preference
- Settings persistence via localStorage

## 🎉 Ringkasan Step 4: Custom Viewers

✅ **Custom Viewers berhasil di-deploy**:

1. **File Transfer**: All custom viewer files copied to server - OK
2. **nginx Routing**: Custom endpoints `/viewer-horizontal`, `/viewer-config` - OK  
3. **Docker Volumes**: Static files accessible dari nginx container - OK
4. **API Integration**: Viewers connect ke Anthias asset API - OK
5. **Fullscreen Mode**: True fullscreen functionality working - OK
6. **Configuration**: Settings management via localStorage - OK

⚠️ **URL Akses**:
- Main dashboard: `http://192.168.5.12:8000` (atau `http://anthias.local:8000`)
- Enhanced viewer: `http://192.168.5.12:8000/viewer-enhanced`
- Basic viewer: `http://192.168.5.12:8000/viewer-basic`
- Simple viewer: `http://192.168.5.12:8000/viewer-simple`
- Standalone viewer: `http://192.168.5.12:8000/viewer-standalone`

## 📋 Next Step

Lanjut ke **[STEP-05-TESTING.md](STEP-05-TESTING.md)** untuk comprehensive testing.

## 🔧 Troubleshooting

**Problem**: Custom viewers return 404
**Solution**:
```bash
# Check nginx config
docker exec anthias-nginx nginx -t

# Check file permissions
ls -la /home/gzjbbk/Anthias/static/custom-viewers/

# Restart nginx
docker-compose -f docker-compose.dev.yml restart anthias-nginx
```

**Problem**: API calls fail dari custom viewers
**Solution**:
```bash
# Check CORS settings
curl -H "Origin: http://anthias.local:8000" http://anthias.local:8000/api/v1/assets

# Check API endpoint
docker logs anthias-server
```

**Problem**: Fullscreen mode tidak work
**Solution**:
```bash
# Check browser security settings
# Pastikan access via HTTPS atau localhost
# Test di browser berbeda (Chrome, Firefox)
```

## 🔧 **Integration Troubleshooting Guide**

### Problem 1: Viewer endpoint returns 404

**Symptoms**: `curl http://192.168.5.12:8000/viewer` returns 404

**Root Cause**: Nginx config tidak ada routing untuk `/viewer`

**Solution Steps**:
```bash
# 1. Check nginx config di container
docker exec anthias_anthias-nginx_1 grep -A 5 "/viewer" /etc/nginx/sites-enabled/nginx.development.conf

# 2. Jika tidak ada, update config host dulu
nano /home/gzjbbk/Anthias/docker/nginx/nginx.development.conf

# 3. Add viewer routing:
location /viewer {
    alias /srv/anthias/static/custom-viewers/viewer.html;
    add_header Content-Type "text/html; charset=utf-8";
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}

# 4. Restart nginx container
docker-compose -f docker-compose.dev.yml restart anthias-nginx
```

### Problem 2: Viewer loads but content outdated

**Symptoms**: File size atau content tidak match dengan yang di host

**Root Cause**: Container serving cached/different file

**Solution Steps**:
```bash
# 1. Check file size di host vs container
ls -la /home/gzjbbk/Anthias/static/custom-viewers/viewer.html
docker exec anthias_anthias-nginx_1 ls -la /srv/anthias/static/custom-viewers/viewer.html

# 2. Jika berbeda, copy manual ke container
docker cp /home/gzjbbk/Anthias/static/custom-viewers/viewer.html anthias_anthias-nginx_1:/srv/anthias/static/custom-viewers/viewer.html

# 3. Reload nginx untuk clear cache
docker exec anthias_anthias-nginx_1 nginx -s reload

# 4. Test dengan cache buster
curl -I "http://192.168.5.12:8000/viewer?v=$(date +%s)"
```

### Problem 3: Config changes tidak apply

**Symptoms**: Nginx config update tapi endpoint masih lama

**Root Cause**: Container config berbeda dengan host config

**Solution Steps**:
```bash
# 1. Update config di container langsung
docker exec anthias_anthias-nginx_1 sed -i 's|old-file.html|new-file.html|g' /etc/nginx/sites-enabled/nginx.development.conf

# 2. Reload nginx
docker exec anthias_anthias-nginx_1 nginx -s reload

# 3. Verify config change
docker exec anthias_anthias-nginx_1 grep -A 5 "/viewer" /etc/nginx/sites-enabled/nginx.development.conf
```

### Problem 4: DNS anthias.local tidak resolve

**Symptoms**: `curl http://anthias.local:8000/viewer` gagal, tapi IP works

**Root Cause**: MikroTik DNS static record belum ada atau DHCP DNS salah

**Solution Steps**:
```bash
# 1. Test DNS resolution
nslookup anthias.local
ping anthias.local

# 2. Login ke MikroTik dan add static DNS
/ip dns static add name=anthias.local address=192.168.5.12

# 3. Update DHCP DNS server
/ip dhcp-server network set [find] dns-server=192.168.5.1,8.8.8.8

# 4. Test dari device lain di network
```

### Problem 5: Volume mount tidak sync

**Symptoms**: File update di host tapi container tidak berubah

**Root Cause**: Volume mount configuration incorrect

**Solution Steps**:
```bash
# 1. Check docker-compose volume mounts
grep -A 10 "anthias-nginx" docker-compose.dev.yml

# 2. Pastikan ada volume mount:
# volumes:
#   - ./static/custom-viewers:/srv/anthias/static/custom-viewers:ro

# 3. Jika tidak ada, restart dengan volume mount
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# 4. Verify mount
docker exec anthias_anthias-nginx_1 ls -la /srv/anthias/static/custom-viewers/
```

## ✅ **Best Practices untuk Avoid Issues**

### 1. Always Update Both Locations
```bash
# Update host file
cp new-viewer.html /home/gzjbbk/Anthias/static/custom-viewers/viewer.html

# Copy to container
docker cp /home/gzjbbk/Anthias/static/custom-viewers/viewer.html anthias_anthias-nginx_1:/srv/anthias/static/custom-viewers/viewer.html
```

### 2. Always Reload Nginx After Config Changes
```bash
docker exec anthias_anthias-nginx_1 nginx -s reload
```

### 3. Always Test with Cache Buster
```bash
curl -I "http://192.168.5.12:8000/viewer?v=$(date +%s)"
```

### 4. Always Verify File Content
```bash
curl -s http://192.168.5.12:8000/viewer | grep "unique-string-from-new-file"
```

---

*Dengan mengikuti troubleshooting guide ini, masalah integrasi viewer akan mudah diatasi.*
