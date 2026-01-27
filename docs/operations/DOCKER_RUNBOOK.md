# Docker Runbook

## Critical: Run from Parent Directory

**SELALU jalankan docker-compose dari parent directory:**

```bash
# CORRECT
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml up -d

# WRONG - env vars tidak terload!
cd /home/gzjbbk/signate/docker
docker-compose up -d
```

**Kenapa?** docker-compose mencari `.env` di current directory.

---

## Common Commands

### Check Status
```bash
# All services
docker-compose -f docker/docker-compose.yml ps

# Specific service logs
docker logs signage-backend --tail 50
docker logs signage-postgres --tail 50
```

### Start/Stop/Restart
```bash
# Start all
docker-compose -f docker/docker-compose.yml up -d

# Stop all
docker-compose -f docker/docker-compose.yml down

# Restart specific service
docker-compose -f docker/docker-compose.yml restart backend-api

# Rebuild and restart
docker-compose -f docker/docker-compose.yml up -d --build backend-api
```

### Environment Variables
```bash
# Check env in container
docker exec signage-backend env | grep CORS_ORIGINS
```

---

## Common Issues & Solutions

### 1. CORS Error

**Symptom:** Login gagal dengan "No Access-Control-Allow-Origin header"

**Root Cause:** docker-compose dijalankan dari subdirectory

**Solution:**
```bash
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d

# Verify
docker logs signage-backend 2>&1 | grep "CORS enabled"
```

### 2. Invalid Salt Error

**Symptom:** Login returns 500, logs show "ValueError: Invalid salt"

**Root Cause:** Password hash korup (bash interpret dollar signs)

**Solution:**
```bash
echo "UPDATE users SET password_hash = '\$2b\$12\$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2' WHERE username='admin';" > /tmp/reset_pass.sql

docker exec -i signage-postgres psql -U signage_user -d signage_db < /tmp/reset_pass.sql
```

### 3. Fresh Database Install

```bash
# Stop all
cd /home/gzjbbk/signate
docker-compose -f docker/docker-compose.yml down --volumes

# Remove volumes (DATA AKAN HILANG!)
docker volume rm signate_postgres-data signate_redis-data

# Start fresh
docker-compose -f docker/docker-compose.yml up -d

# Wait & verify
sleep 10
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT username FROM users;"
```

---

## Database Commands

```bash
# Connect to database
docker exec -it signage-postgres psql -U signage_user -d signage_db

# Backup
docker exec signage-postgres pg_dump -U signage_user -d signage_db > backup.sql

# Restore
docker exec -i signage-postgres psql -U signage_user -d signage_db < backup.sql
```

---

## Portainer Management

**Access:** https://portainer.zhmhotels.online/

```bash
# View logs
docker logs portainer --tail 50

# Restart
docker restart portainer

# Update
docker stop portainer && docker rm portainer
docker pull portainer/portainer-ce:latest
docker run -d -p 9000:9000 -p 9443:9443 \
  --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

---

## VPS Remote Commands

```bash
# Check services
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "cd /root/signage && docker-compose -f docker/docker-compose.yml ps"

# View logs
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "docker logs signage-backend --tail 50"

# Restart service
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "cd /root/signage && docker-compose -f docker/docker-compose.yml restart backend-api"

# Backup database
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/vps_backup_$(date +%Y%m%d_%H%M%S).sql
```
