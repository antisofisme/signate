# 🚀 Deployment Guide - Digital Signage

Panduan lengkap deployment sistem Digital Signage ke server production.

---

## 📋 Prerequisites

Server requirements:
- Ubuntu 20.04+ atau Debian 11+
- Docker dan Docker Compose installed
- SSH access ke server
- Minimum 2GB RAM, 10GB disk space

---

## 🎯 Quick Deployment

### 1. Transfer Files ke Server

Dari komputer local (WSL):

```bash
# Pastikan di direktori project
cd /mnt/g/khoirul/signate

# Transfer ke server menggunakan rsync
sshpass -p 'Password@2021' rsync -avz --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' \
  -e ssh . gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/
```

### 2. SSH ke Server

```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12
```

### 3. Deploy Semua Services

```bash
cd /home/gzjbbk/prototipe2

# Buat .env jika belum ada
cp .env.example .env

# Edit .env (opsional, untuk production ganti secret keys)
nano .env

# Deploy menggunakan script
./docker/deploy.sh
```

Tunggu beberapa saat, semua services akan berjalan!

---

## ✅ Verifikasi Deployment

### Check Services Status

```bash
cd /home/gzjbbk/prototipe2
docker-compose -f docker/docker-compose.yml ps
```

Output yang benar:
```
NAME                      STATUS        PORTS
signage-backend-python    Up (healthy)  0.0.0.0:8001->8000/tcp
signage-celery-worker     Up
signage-player            Up (healthy)  0.0.0.0:8080->80/tcp
signage-postgres          Up (healthy)  0.0.0.0:5433->5432/tcp
signage-redis             Up (healthy)  0.0.0.0:6379->6379/tcp
```

### Test Endpoints

```bash
# Test Backend API
curl http://192.168.5.12:8001/health

# Test Player
curl http://192.168.5.12:8080/

# Test Database
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT 1;"
```

### Access dari Browser

Dari komputer manapun di jaringan yang sama:

- **Backend API:** http://192.168.5.12:8001/docs
- **Player:** http://192.168.5.12:8080/

---

## 🔧 Management Commands

### Deploy / Redeploy

```bash
cd /home/gzjbbk/prototipe2

# Deploy semua services
./docker/deploy.sh

# Rebuild semua services
./docker/deploy.sh --rebuild

# Deploy service tertentu
./docker/deploy.sh player --rebuild
./docker/deploy.sh backend-api --rebuild

# Deploy dengan melihat logs
./docker/deploy.sh --logs
```

### View Logs

```bash
# Logs semua services
docker-compose -f docker/docker-compose.yml logs -f

# Logs service tertentu
docker logs -f signage-backend-python
docker logs -f signage-player
docker logs -f signage-postgres

# Last 50 lines
docker logs --tail 50 signage-backend-python
```

### Restart Services

```bash
# Restart semua
docker-compose -f docker/docker-compose.yml restart

# Restart service tertentu
docker-compose -f docker/docker-compose.yml restart backend-api
docker-compose -f docker/docker-compose.yml restart player
```

### Stop Services

```bash
# Stop semua
docker-compose -f docker/docker-compose.yml down

# Stop tanpa menghapus volumes (data tetap ada)
docker-compose -f docker/docker-compose.yml stop
```

---

## 🔄 Update Deployment

Setelah ada perubahan code di local:

### Method 1: Rsync + Rebuild (Recommended)

```bash
# 1. Di WSL - Transfer perubahan ke server
cd /mnt/g/khoirul/signate
sshpass -p 'Password@2021' rsync -avz --exclude 'node_modules' --exclude '.git' \
  -e ssh . gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/

# 2. SSH ke server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# 3. Rebuild service yang berubah
cd /home/gzjbbk/prototipe2

# Jika backend berubah
./docker/deploy.sh backend-api --rebuild

# Jika player berubah
./docker/deploy.sh player --rebuild

# Jika semua berubah
./docker/deploy.sh --rebuild
```

### Method 2: Direct Git Pull (Jika menggunakan Git di server)

```bash
# SSH ke server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Pull latest changes
cd /home/gzjbbk/prototipe2
git pull origin feature/api-integration

# Rebuild
./docker/deploy.sh --rebuild
```

---

## 🗄️ Database Management

### Access Database

```bash
# Interactive psql
docker exec -it signage-postgres psql -U signage_user -d signage_db

# Run SQL query
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT * FROM users;"

# Run SQL file
docker exec -i signage-postgres psql -U signage_user -d signage_db < migration.sql
```

### Backup Database

```bash
# Manual backup
docker exec signage-postgres pg_dump -U signage_user signage_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i signage-postgres psql -U signage_user -d signage_db < backup_20250107.sql
```

### Run Migrations

```bash
# Dari WSL - Upload migration file
sshpass -p 'Password@2021' scp backend-python/migrations/009_new_migration.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/

# SSH ke server dan jalankan
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12
cd /home/gzjbbk/prototipe2
docker exec -i signage-postgres psql -U signage_user -d signage_db < 009_new_migration.sql
```

---

## 🐛 Troubleshooting

### 1. CORS Error di Frontend

**Symptom:** Login gagal dengan error CORS

**Solution:**
```bash
# Check CORS configuration
docker logs signage-backend-python 2>&1 | grep "CORS enabled"

# Jika tidak ada, pastikan .env memiliki CORS_ORIGINS
echo "CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://192.168.5.12:8080" >> .env

# Restart backend
docker-compose -f docker/docker-compose.yml restart backend-api
```

### 2. Player Tidak Load

**Symptom:** Player menampilkan 404 atau blank

**Solution:**
```bash
# Check logs
docker logs signage-player

# Rebuild player
docker-compose -f docker/docker-compose.yml up -d --build player
```

### 3. Database Connection Failed

**Symptom:** Backend tidak bisa connect ke database

**Solution:**
```bash
# Check postgres health
docker inspect signage-postgres | grep Health

# Restart postgres
docker-compose -f docker/docker-compose.yml restart postgres

# Wait for healthy status
sleep 10
docker-compose -f docker/docker-compose.yml ps
```

### 4. Port Already in Use

**Symptom:** "bind: address already in use"

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8080

# Kill the process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
nano docker/docker-compose.yml
# Change "8080:80" to "8090:80"
```

### 5. Container Keeps Restarting

**Symptom:** Container status shows "Restarting"

**Solution:**
```bash
# Check logs for error
docker logs signage-backend-python

# Common issues:
# - Database not ready → wait longer
# - Missing environment variables → check .env
# - Python import errors → rebuild container
```

---

## 🔒 Production Security

### Change Default Secrets

```bash
# Generate new secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 16)

# Update .env
nano .env

# Add these values:
# SECRET_KEY=<generated-secret-key>
# JWT_SECRET=<generated-jwt-secret>
# ENCRYPTION_KEY=<generated-encryption-key>

# Restart backend
docker-compose -f docker/docker-compose.yml restart backend-api
```

### Setup Automated Backups

```bash
# Create backup script
cat > /home/gzjbbk/backup.sh << 'EOFBACKUP'
#!/bin/bash
BACKUP_DIR=/home/gzjbbk/backups
mkdir -p $BACKUP_DIR
docker exec signage-postgres pg_dump -U signage_user signage_db > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
EOFBACKUP

# Make executable
chmod +x /home/gzjbbk/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/gzjbbk/backup.sh") | crontab -
```

---

## 📊 Monitoring

### Resource Usage

```bash
# Real-time resource usage
docker stats

# Disk usage
docker system df

# Clean unused resources
docker system prune -a
```

### Service Health

```bash
# Check all services
docker-compose -f docker/docker-compose.yml ps

# Detailed inspect
docker inspect signage-backend-python | grep -A 10 Health
```

---

## 🎯 Common Workflows

### Workflow 1: Deploy Perubahan Backend

```bash
# 1. Di WSL - Transfer backend
cd /mnt/g/khoirul/signate
sshpass -p 'Password@2021' rsync -avz backend-python/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/backend-python/

# 2. SSH dan rebuild
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/prototipe2 && ./docker/deploy.sh backend-api --rebuild"
```

### Workflow 2: Deploy Perubahan Player

```bash
# 1. Di WSL - Transfer player
cd /mnt/g/khoirul/signate
sshpass -p 'Password@2021' rsync -avz player-vanillajs/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/player-vanillajs/

# 2. SSH dan rebuild
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/prototipe2 && ./docker/deploy.sh player --rebuild"
```

### Workflow 3: Fresh Install (Clean Slate)

```bash
# SSH ke server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Stop semua dan hapus volumes
cd /home/gzjbbk/prototipe2
docker-compose -f docker/docker-compose.yml down --volumes

# Deploy ulang
./docker/deploy.sh

# Database akan di-initialize otomatis dengan init.sql
```

---

## 📝 Quick Reference

```bash
# Deploy all
./docker/deploy.sh

# Deploy with rebuild
./docker/deploy.sh --rebuild

# Deploy specific service
./docker/deploy.sh backend-api --rebuild

# View all logs
docker-compose -f docker/docker-compose.yml logs -f

# Check status
docker-compose -f docker/docker-compose.yml ps

# Stop all
docker-compose -f docker/docker-compose.yml down

# Backup database
docker exec signage-postgres pg_dump -U signage_user signage_db > backup.sql

# Access database
docker exec -it signage-postgres psql -U signage_user -d signage_db
```

---

## ✨ Next Steps

1. **Setup SSL/HTTPS** (optional untuk production)
   - Install Nginx sebagai reverse proxy
   - Setup SSL certificates dengan Let's Encrypt
   - Configure domain name

2. **Setup Monitoring** (optional)
   - Prometheus + Grafana untuk monitoring
   - AlertManager untuk notifications
   - Log aggregation dengan ELK stack

3. **Setup CI/CD** (optional)
   - GitHub Actions untuk auto-deploy
   - Automated testing
   - Staging environment

---

## 📞 Support

Jika ada masalah:
1. Check logs: `docker logs <container-name>`
2. Check docker/README.md untuk troubleshooting lengkap
3. Check CLAUDE.md untuk arsitektur details
4. Review deployment guide ini

**Selamat! Sistem Digital Signage sudah berjalan! 🎉**
