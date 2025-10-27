# 🔄 Rebuild & Deployment Guide

## 📋 Overview

Dokumen ini menjelaskan cara rebuild semua Docker containers dari scratch untuk memastikan semua perubahan code dan konfigurasi ter-apply dengan benar.

## 🏗️ Struktur Docker Compose Baru

### Services yang Di-manage:

1. **PostgreSQL** (port 5433) - Database untuk Backend API
2. **Redis** (port 6379) - Cache & Queue untuk Backend dan Anthias
3. **Backend API** (port 8001) - FastAPI Backend
4. **Anthias Server** - Digital Signage CMS Core
5. **Anthias Celery** - Background task processor
6. **Anthias WebSocket** - Real-time communication
7. **Anthias Nginx** (port 8000) - Reverse proxy dengan CORS

### Network:
- **signate_signage-network** - Semua services terhubung dalam satu network

### Volumes (Persistent Data):
- **postgres-data** - Data PostgreSQL
- **redis-data** - Data Redis
- **anthias-data** - Data Anthias (configs, databases)
- **./anthias-assets** - Media files yang di-upload ke Anthias

## 🚀 Cara Rebuild (Step-by-Step)

### Option 1: Menggunakan Script Otomatis (Recommended)

```bash
# 1. Login ke server
ssh gzjbbk@192.168.5.12

# 2. Masuk ke direktori project
cd /home/gzjbbk/signage

# 3. Jalankan rebuild script
./rebuild.sh
```

### Option 2: Manual Step-by-Step

```bash
# 1. Stop semua containers
docker-compose down --remove-orphans

# 2. Stop containers lama dari Anthias (jika ada)
docker stop $(docker ps -aq --filter "name=anthias")
docker stop signage-backend 2>/dev/null || true

# 3. Remove containers lama
docker rm $(docker ps -aq --filter "name=anthias")
docker rm $(docker ps -aq --filter "name=signage")

# 4. (Optional) Hapus volumes jika ingin clean install
docker volume rm $(docker volume ls -q --filter "name=signate")

# 5. Build fresh images (NO CACHE untuk memastikan)
docker-compose build --no-cache --parallel

# 6. Start semua services
docker-compose up -d

# 7. Monitor logs
docker-compose logs -f
```

## 📦 Deploy dari Local ke Server

### Step 1: Sync Code ke Server

```bash
# Di local (WSL)
cd /mnt/g/khoirul/signate

# Sync dengan rsync (exclude node_modules, etc)
sshpass -p 'Password@2021' rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.git' \
  --exclude 'web-admin/node_modules' \
  --exclude 'web-admin/dist' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  ./ gzjbbk@192.168.5.12:/home/gzjbbk/signage/
```

### Step 2: SSH ke Server dan Rebuild

```bash
# SSH ke server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Masuk ke direktori
cd /home/gzjbbk/signage

# Rebuild
./rebuild.sh
```

## 🔍 Verifikasi Setelah Rebuild

### 1. Check Status Containers

```bash
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
signage-postgres        Up (healthy)        0.0.0.0:5433->5432/tcp
signage-redis           Up (healthy)        0.0.0.0:6379->6379/tcp
signage-backend         Up                  0.0.0.0:8001->8000/tcp
anthias-server          Up
anthias-celery          Up
anthias-websocket       Up
anthias-nginx           Up                  0.0.0.0:8000->80/tcp
```

### 2. Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend-api
docker-compose logs -f anthias-nginx
```

### 3. Test Endpoints

```bash
# Backend API health
curl http://192.168.5.12:8001/health

# Anthias (with CORS)
curl -I http://192.168.5.12:8000/api/v1/assets

# Backend docs
curl http://192.168.5.12:8001/docs
```

### 4. Test CORS

```bash
# Test CORS headers on Anthias
curl -I -X OPTIONS http://192.168.5.12:8000/api/v1/assets/test/content \
  -H "Origin: http://192.168.5.12:8080" \
  -H "Access-Control-Request-Method: GET"
```

Should see:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

## 🐛 Troubleshooting

### Problem: Container won't start

```bash
# Check logs
docker-compose logs [service-name]

# Example:
docker-compose logs backend-api
```

### Problem: Port already in use

```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :8001

# Kill process
sudo kill -9 [PID]
```

### Problem: Database connection failed

```bash
# Check postgres is healthy
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database (WARNING: Data loss!)
docker-compose down
docker volume rm signate_postgres-data
docker-compose up -d
```

### Problem: Anthias build fails

```bash
# Check if Anthias source code exists
ls -la ./anthias/

# Check Dockerfiles exist
ls -la ./anthias/docker/Dockerfile.*

# If missing, re-clone Anthias
git clone https://github.com/Screenly/Anthias anthias
```

## 📝 Important Files

### Di Local (/mnt/g/khoirul/signate):
- `docker-compose.yml` - Main orchestration file
- `rebuild.sh` - Automated rebuild script
- `.env` - Environment variables
- `backend/` - Backend API source code
- `anthias/` - Anthias CMS source code (submodule/clone)
- `anthias/docker/nginx/nginx.development.conf` - Nginx config dengan CORS

### Di Server (/home/gzjbbk/signage):
- Same structure as local
- `anthias-assets/` - Uploaded media files (persistent)

## ⚠️ Critical Notes

1. **CORS Config**: File `anthias/docker/nginx/nginx.development.conf` sudah dikonfigurasi dengan CORS headers. Jangan override!

2. **Data Persistence**:
   - PostgreSQL data: `postgres-data` volume
   - Redis data: `redis-data` volume
   - Anthias assets: `./anthias-assets` folder
   - Jangan hapus volumes kecuali ingin reset data!

3. **Network**:
   - Semua services dalam satu network: `signate_signage-network`
   - Backend bisa akses Anthias via hostname `anthias-nginx`

4. **Environment Variables**:
   - Default values di docker-compose.yml
   - Override via .env file
   - Password default: `your_password_here` (sudah sesuai dengan DB yang ada)

## 🎯 Next Steps After Rebuild

1. ✅ Verify all containers are running
2. ✅ Test Backend API: http://192.168.5.12:8001/docs
3. ✅ Test Anthias UI: http://192.168.5.12:8000
4. ✅ Test CORS: Check browser console untuk viewer
5. ✅ Upload test content ke Anthias
6. ✅ Assign content via Backend API
7. ✅ Test viewers (browser & WebOS)

## 📞 Support

Jika ada masalah:
1. Check logs: `docker-compose logs -f`
2. Check network: `docker network inspect signate_signage-network`
3. Check volumes: `docker volume ls | grep signate`
4. Restart specific service: `docker-compose restart [service-name]`
