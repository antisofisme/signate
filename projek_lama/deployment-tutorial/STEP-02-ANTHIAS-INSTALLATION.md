# STEP 2: Instalasi Anthias

## 🎯 Apa yang akan kita lakukan?

Di step ini kita akan:
1. Download/clone Anthias dari GitHub
2. Setup development environment
3. Configure Docker containers dengan prefix `anthias-`
4. Start semua services dan test

## 📋 Instalasi Anthias

### 1. Download Anthias dari GitHub

**Apa itu**: Kita akan clone (download) source code Anthias terbaru dari repository official.

**Command pindah ke home directory dan clone**:
```bash
cd /home/gzjbbk
git clone https://github.com/Screenly/Anthias.git
```

**Hasil**:
```
Cloning into 'Anthias'...
```

✅ **Status**: Anthias berhasil di-download!

**Command cek isi directory**:
```bash
ls -la Anthias/
```

**Hasil**:
```
total 768
drwxrwxr-x 22 gzjbbk gzjbbk   4096 Aug 15 04:15 .
drwxrwxr-x 17 gzjbbk gzjbbk   4096 Aug 15 04:15 ..
-rw-rw-r--  1 gzjbbk gzjbbk    363 Aug 15 04:15 .dockerignore
drwxrwxr-x  8 gzjbbk gzjbbk   4096 Aug 15 04:15 .git
[... dan banyak file lainnya ...]
```

✅ **Status**: Directory Anthias terisi lengkap dengan semua source code!

### 2. Masuk ke Directory dan Cek Docker Configuration

**Command masuk ke directory Anthias**:
```bash
cd Anthias
ls -la docker-compose*.yml
```

**Hasil**:
```
-rw-rw-r-- 1 gzjbbk gzjbbk 1380 Aug 15 04:15 docker-compose.dev.yml
-rw-rw-r-- 1 gzjbbk gzjbbk  792 Aug 15 04:15 docker-compose.test.yml
```

**Penjelasan**:
- `docker-compose.dev.yml` = Configuration untuk development (yang akan kita pakai)
- `docker-compose.test.yml` = Configuration untuk testing

### 3. Edit Docker Compose untuk Container Prefix

**Apa itu**: Kita perlu edit file docker-compose agar semua container Anthias menggunakan prefix `anthias-` supaya tidak bingung dengan container lain.

**Command lihat isi file current**:
```bash
cat docker-compose.dev.yml
```

**Hasil**:
```yaml
services:
  anthias-server:
    build:
      context: .
      dockerfile: docker/Dockerfile.server
    ports:
      - 8000:80  # Port 8000 untuk akses web
    # ... configuration lainnya
  
  anthias-websocket:
    # ... WebSocket service
  
  anthias-celery:
    # ... Background task service
    
  redis:
    image: redis:alpine  # Database cache
    
  anthias-nginx:
    # ... Web server
```

**Analisis**: File sudah cukup baik, hampir semua service sudah ada prefix `anthias-`. Tapi kita perlu ubah `redis` jadi `anthias-redis` untuk konsistensi.

### 4. Edit Docker Compose untuk Konsistensi Naming

**Command backup file original dulu**:
```bash
cp docker-compose.dev.yml docker-compose.dev.yml.backup
```

**Command edit untuk konsistensi naming**:
```bash
# Rename service redis menjadi anthias-redis
sed 's/  redis:/  anthias-redis:/g' docker-compose.dev.yml.backup > docker-compose.dev.yml

# Update semua reference ke redis service
sed -i 's/redis:6379/anthias-redis:6379/g' docker-compose.dev.yml
sed -i 's/- redis/- anthias-redis/g' docker-compose.dev.yml
```

**Command cek hasil**:
```bash
grep anthias-redis docker-compose.dev.yml
```

**Hasil**:
```
      - CELERY_BROKER_URL=redis://anthias-redis:6379/0
      - CELERY_RESULT_BACKEND=redis://anthias-redis:6379/0
      - anthias-redis
      - CELERY_BROKER_URL=redis://anthias-redis:6379/0
      - CELERY_RESULT_BACKEND=redis://anthias-redis:6379/0
  anthias-redis:
```

✅ **Status**: Docker compose sudah di-edit! Semua service sekarang konsisten dengan prefix `anthias-`.

### 5. Start Anthias Services

**Apa yang akan terjadi**: Docker akan download/build semua image yang dibutuhkan, lalu start 5 containers:
- `anthias-server` (Django web app)
- `anthias-websocket` (Real-time communication)
- `anthias-celery` (Background tasks)
- `anthias-redis` (Cache database)
- `anthias-nginx` (Web server di port 8000)

⚠️ **Problem**: File Dockerfile tidak ada, hanya template `.j2`! Anthias menggunakan sistem build yang generate Dockerfile dari template.

**Command generate Dockerfile untuk development**:
```bash
./bin/generate_dev_mode_dockerfiles.sh
```

**Hasil** (proses akan download Python base image dan build tools):
```
Sending build context to Docker daemon  2.775MB
Step 1/6 : FROM python:3.11-bookworm
[... downloading Python base image ...]
Installing Poetry (2.1.4)
[... installing build tools ...]
Successfully built fed136a5f74c
Successfully tagged anthias-dockerfile-image-builder:latest
```

✅ **Status**: Dockerfile generation berhasil!

**Command cek apakah file sudah ada**:
```bash
ls -la docker/Dockerfile.*
```

**Hasil**:
```
-rw-r--r-- 1 root   root   1521 docker/Dockerfile.celery
-rw-r--r-- 1 root   root    415 docker/Dockerfile.nginx
-rw-r--r-- 1 root   root   1428 docker/Dockerfile.server
-rw-r--r-- 1 root   root   1394 docker/Dockerfile.websocket
[... dan file template .j2 ...]
```

✅ **Status**: Semua Dockerfile sudah di-generate! Sekarang bisa start Anthias.

### 6. Start Anthias Services (Take 2)

**Command start services**:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

✅ **Status Update**: Build SELESAI!

**Progress yang telah selesai**:
1. ✅ Base images downloaded (Python 3.11, Debian bookworm)
2. ✅ System packages installed (733 packages, 294 MB)
3. ✅ Python dependencies installed
4. ✅ React frontend built
5. ✅ All 5 containers started successfully

### 6. Troubleshooting Redis Connection Error

⚠️ **Problem yang terjadi**: Build berhasil tapi web interface return HTTP 500 error.

**Error di logs**:
```bash
redis.exceptions.ConnectionError: Error -2 connecting to redis:6379. Name or service not known.
```

**Root Cause**: 
- Tutorial awal mengubah service `redis` → `anthias-redis` untuk konsistensi naming
- Tapi aplikasi Anthias hardcoded mencari `redis:6379` di kode Python
- Environment variables di docker-compose sudah diubah ke `anthias-redis:6379` 
- Tapi masih ada reference `redis:6379` di dalam aplikasi

**Dimana hardcode terjadi**:
- File `lib/github.py` line 109: `r.get('latest-remote-hash')` connect ke Redis
- Django settings mungkin ada Redis cache config yang hardcoded
- Celery configuration mungkin ada fallback ke `redis:6379`
- Ada beberapa file .py yang tidak menggunakan environment variables

**Yang dirubah saat edit docker-compose**:
1. **Service name**: `redis:` → `anthias-redis:`
2. **Environment variables**:
   - `CELERY_BROKER_URL=redis://redis:6379/0` → `redis://anthias-redis:6379/0`
   - `CELERY_RESULT_BACKEND=redis://redis:6379/0` → `redis://anthias-redis:6379/0`
3. **Dependencies**: `- redis` → `- anthias-redis`

**Solution**: Revert ke naming original
```bash
# Restore original docker-compose.dev.yml
cp docker-compose.dev.yml.backup docker-compose.dev.yml

# Restart with original configuration
docker-compose -f docker-compose.dev.yml down --remove-orphans
docker-compose -f docker-compose.dev.yml up -d
```

**Lesson Learned**:
- Service `redis` harus tetap nama `redis` (jangan dirubah ke `anthias-redis`)
- Container name otomatis jadi `anthias_redis_1` (Docker Compose auto-prefix)
- Environment variables tetap menggunakan `redis:6379`
- Anthias aplikasi expect service name `redis`, bukan `anthias-redis`

**Best Practice untuk Future**:
- Jangan ubah service names yang di-reference di application code
- Cek source code dulu sebelum rename services
- Use environment variables untuk configurable connections
- Test semua functionality setelah naming changes

**Command untuk cek hardcode references**:
```bash
# Cari semua hardcode redis references
grep -r "redis:6379" .
grep -r "localhost:6379" .
find . -name "*.py" -exec grep -l "redis" {} \;
```

### 7. Monitor Build Progress

**Command cek status containers**:
```bash
docker-compose -f docker-compose.dev.yml ps
```

**Command cek logs build real-time**:
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

**Actual Output build selesai**:
```
NAME                        STATE    PORTS
anthias_redis_1             Up       6379/tcp
anthias_anthias-server_1    Up       
anthias_anthias-websocket_1 Up       
anthias_anthias-celery_1    Up       
anthias_anthias-nginx_1     Up       0.0.0.0:8000->80/tcp
```

✅ **Status**: Semua 5 containers berhasil started!

💡 **Tip**: Buka Portainer di `http://192.168.5.12:9090` untuk visual monitoring.

### 8. Verifikasi Instalasi (Setelah Build Selesai)

**Command test web access**:
```bash
curl -I http://localhost:8000
```

**Actual Output**:
```
HTTP/1.1 200 OK
Server: nginx
Content-Type: text/html; charset=utf-8
Date: Fri, 15 Aug 2025 04:56:26 GMT
```

✅ **Status**: Anthias berhasil running! Dashboard bisa diakses di `http://192.168.5.12:8000`

**Command test dari komputer lain**:
```bash
curl -I http://192.168.5.12:8000
```

## 🎉 Ringkasan Step 2: Anthias Installation

✅ **Instalasi Anthias berhasil**:

1. **Repository Clone**: Anthias downloaded dari GitHub - OK
2. **Dockerfile Generation**: Template .j2 → Dockerfile - OK  
3. **Docker Build**: 5 containers built (20+ menit) - OK
4. **Container Start**: All services running - OK
5. **Web Interface**: HTTP 200 OK response - OK

⚠️ **Catatan Container Naming**:
- Anthias menggunakan mixed naming: `anthias_redis_1`, `anthias_anthias-server_1`
- Tidak perlu ubah naming karena sudah ada hardcode di aplikasi
- Semua berfungsi normal dengan naming default

### 9. Troubleshooting Build Issues

**Jika build gagal**:

**Problem**: "No space left on device"
**Solution**: 
```bash
docker system prune -f
df -h  # cek disk space
```

**Problem**: "Build failed"
**Solution**:
```bash
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --build
```

**Problem**: "Port 8000 already in use"
**Solution**:
```bash
sudo netstat -tulpn | grep 8000
# Kill process yang menggunakan port 8000
```