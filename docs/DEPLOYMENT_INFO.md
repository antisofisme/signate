# Deployment Information

## Production Server

**Server Details:**
- IP Address: `192.168.5.12`
- Username: `gzjbbk`
- Password: `Password@2021`
- OS: Linux (Ubuntu/Debian)
- Location: `/home/gzjbbk/`

---

## Services Already Running on Server

### 1. Anthias (Digital Signage)
- Status: ✓ Running
- Location: `/home/gzjbbk/Anthias/`
- Port: 8000
- Access: http://192.168.5.12:8000
- Docker Compose: `docker-compose.dev.yml`

**Containers:**
- anthias_anthias-nginx_1
- anthias_anthias-celery_1
- anthias_anthias-websocket_1
- anthias_anthias-server_1
- anthias_redis_1

### 2. Redis (from Anthias)
- Status: ✓ Running (part of Anthias)
- Port: 6379
- Connection: `redis://192.168.5.12:6379`
- **REUSE THIS** - No need to deploy new Redis!

### 3. Other Services
- Portainer: Port 9443, 9090
- pgAdmin: Port 5050

---

## Deployment Plan

### Backend API (FastAPI) - DEPLOY TO SERVER

**Location:** `/home/gzjbbk/signage-backend/`

**Services to Deploy:**
- ✓ PostgreSQL (Docker container)
- ✓ Backend API (FastAPI)
- ✓ Web Admin (React/Vue)
- ✓ Nginx (Reverse proxy)

**Reuse from Server:**
- ✗ Redis - Use existing: `redis://192.168.5.12:6379`
- ✗ Anthias - Already running: `http://192.168.5.12:8000`

---

## SSH Access

```bash
# SSH to server
ssh gzjbbk@192.168.5.12
# Password: Password@2021

# Or with sshpass
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12
```

---

## File Transfer (SCP)

```bash
# Upload file to server
sshpass -p 'Password@2021' scp file.txt gzjbbk@192.168.5.12:/home/gzjbbk/

# Upload folder to server
sshpass -p 'Password@2021' scp -r folder/ gzjbbk@192.168.5.12:/home/gzjbbk/

# Download from server
sshpass -p 'Password@2021' scp gzjbbk@192.168.5.12:/home/gzjbbk/file.txt ./
```

---

## Deployment Steps (When Ready)

### Step 1: Prepare Files
```bash
# Build backend locally
cd backend
docker build -t signage-backend .

# Build web-admin locally
cd web-admin
npm run build
```

### Step 2: Transfer to Server
```bash
# Copy project to server
sshpass -p 'Password@2021' scp -r . gzjbbk@192.168.5.12:/home/gzjbbk/signage/
```

### Step 3: Deploy on Server
```bash
# SSH to server
ssh gzjbbk@192.168.5.12

# Navigate to project
cd /home/gzjbbk/signage/

# Copy .env.example to .env
cp .env.example .env

# Edit .env with production values
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Verify
```bash
# Test PostgreSQL
docker exec -it signage-postgres psql -U signage_user -d signage_db

# Test Backend API
curl http://192.168.5.12:8000/docs

# Test Redis connection (existing)
redis-cli -h 192.168.5.12 -p 6379 ping
```

---

## Environment Variables (Production)

**Update `.env` on server:**

```env
# Database
DATABASE_URL=postgresql://signage_user:signage_password@postgres:5432/signage_db
POSTGRES_USER=signage_user
POSTGRES_PASSWORD=signage_password_CHANGE_THIS
POSTGRES_DB=signage_db

# Redis (EXISTING on server)
REDIS_URL=redis://192.168.5.12:6379

# Anthias (EXISTING on server)
ANTHIAS_API_URL=http://192.168.5.12:8000
ANTHIAS_API_KEY=

# Backend API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
ENVIRONMENT=production

# Security
JWT_SECRET=GENERATE_NEW_SECRET_HERE
ENCRYPTION_KEY=GENERATE_NEW_KEY_HERE

# CORS
CORS_ORIGINS=http://192.168.5.12:3000,http://192.168.5.12:8000
```

---

## Port Mapping on Server

| Service | Port | Status | URL |
|---------|------|--------|-----|
| Anthias | 8000 | Running ✓ | http://192.168.5.12:8000 |
| Backend API | 8001 | To Deploy | http://192.168.5.12:8001 |
| Web Admin | 3000 | To Deploy | http://192.168.5.12:3000 |
| PostgreSQL | 5432 | To Deploy | Internal |
| Redis | 6379 | Running ✓ | Internal (reuse) |
| Portainer | 9443 | Running ✓ | https://192.168.5.12:9443 |
| pgAdmin | 5050 | Running ✓ | http://192.168.5.12:5050 |

**Note:** Backend API will use port **8001** (not 8000) because Anthias already uses 8000.

---

## Security Notes

⚠️ **IMPORTANT:**
- Change default passwords in production!
- Generate new JWT_SECRET
- Generate new ENCRYPTION_KEY
- Use strong PostgreSQL password
- Enable firewall (ufw)
- Use HTTPS/SSL in production

---

## Backup Strategy

**Database Backup:**
```bash
# Backup PostgreSQL
docker exec signage-postgres pg_dump -U signage_user signage_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i signage-postgres psql -U signage_user -d signage_db < backup_20251021.sql
```

**Files Backup:**
```bash
# Backup entire project
tar -czf signage_backup_$(date +%Y%m%d).tar.gz /home/gzjbbk/signage/

# Download to local
sshpass -p 'Password@2021' scp gzjbbk@192.168.5.12:/home/gzjbbk/signage_backup_*.tar.gz ./
```

---

## Monitoring

**Check Services:**
```bash
# All containers
docker ps

# Signage services only
docker ps | grep signage

# Resource usage
docker stats

# Logs
docker-compose logs -f backend-api
docker-compose logs -f postgres
```

---

**Last Updated:** October 21, 2025
