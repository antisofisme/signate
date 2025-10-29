# Docker Compose Quick Start Guide

## Services Overview

| Service | Port | Purpose | Access |
|---------|------|---------|--------|
| **backend-api** | 8001 | FastAPI Backend | http://192.168.5.12:8001 |
| **viewer** | 8080 | Static Viewer | http://192.168.5.12:8080 |
| **anthias-nginx** | 8000 | Anthias CMS | http://192.168.5.12:8000 |
| **flower** | 5555 | Celery Monitor | http://192.168.5.12:5555 |
| **postgres** | 5433 | Database | localhost:5433 |
| **redis** | 6379 | Cache/Broker | localhost:6379 |
| **celery-worker** | - | Background Tasks | - |
| **celery-beat** | - | Scheduled Tasks | - |

---

## Quick Commands

### Start All Services
```bash
cd /mnt/g/khoirul/signate/docker
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery-worker
docker-compose logs -f backend-api
docker-compose logs -f viewer
```

### Check Status
```bash
docker-compose ps
```

### Rebuild Services
```bash
# Full rebuild
docker-compose down --volumes --remove-orphans
docker-compose build --no-cache
docker-compose up -d

# Specific service
docker-compose up -d --build backend-api
```

### Restart Service
```bash
docker-compose restart celery-worker
docker-compose restart backend-api
```

---

## Access URLs

### Production (Server)
- **Backend API**: http://192.168.5.12:8001
- **API Docs**: http://192.168.5.12:8001/docs
- **Viewer**: http://192.168.5.12:8080
- **Anthias**: http://192.168.5.12:8000
- **Flower**: http://192.168.5.12:5555 (admin/admin123)

### Development (Local)
- **Web Admin**: http://localhost:3000
- **Backend API**: http://localhost:8001 (if running locally)

---

## Monitoring

### Flower (Celery Tasks)
```bash
# Access in browser
open http://192.168.5.12:5555

# Credentials
Username: admin
Password: admin123
```

### Check Worker Status
```bash
docker exec signage-celery-worker celery -A app.celery_app inspect active
docker exec signage-celery-worker celery -A app.celery_app inspect stats
```

### Check Redis
```bash
docker exec signage-redis redis-cli ping
docker exec signage-redis redis-cli INFO memory
```

### Check PostgreSQL
```bash
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT version();"
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs celery-worker

# Check container status
docker ps -a

# Remove and recreate
docker-compose rm -f celery-worker
docker-compose up -d celery-worker
```

### Redis Memory Full
```bash
# Check memory
docker exec signage-redis redis-cli INFO memory

# Flush if needed (CAUTION: deletes all data)
docker exec signage-redis redis-cli FLUSHALL
```

### Database Connection Issues
```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Test connection
docker exec signage-postgres pg_isready -U signage_user
```

### Celery Tasks Not Running
```bash
# Check worker is alive
docker exec signage-celery-worker celery -A app.celery_app inspect ping

# Check if tasks are registered
docker exec signage-celery-worker celery -A app.celery_app inspect registered

# Restart worker
docker-compose restart celery-worker
```

---

## Environment Setup

### First Time Setup
```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit configuration
nano .env

# 3. Update these values:
#    - POSTGRES_PASSWORD
#    - SECRET_KEY
#    - JWT_SECRET
#    - ENCRYPTION_KEY

# 4. Start services
docker-compose up -d

# 5. Check all services are running
docker-compose ps
```

### Update Configuration
```bash
# 1. Edit .env file
nano .env

# 2. Restart affected services
docker-compose restart backend-api celery-worker
```

---

## Backup & Restore

### Backup Database
```bash
# Run backup script
./backup-database.sh

# Manual backup
docker exec signage-postgres pg_dump -U signage_user signage_db > backup.sql
```

### Restore Database
```bash
# Stop services
docker-compose down

# Restore
docker-compose up -d postgres
docker exec -i signage-postgres psql -U signage_user signage_db < backup.sql

# Start all services
docker-compose up -d
```

---

## Health Checks

### Check All Services
```bash
# Backend API
curl http://192.168.5.12:8001/health

# Viewer
curl http://192.168.5.12:8080/health

# Anthias
curl http://192.168.5.12:8000/api/v1/health

# Redis
docker exec signage-redis redis-cli ping

# PostgreSQL
docker exec signage-postgres pg_isready -U signage_user
```

---

## Sync to Server

### From Local to Server
```bash
# Sync docker configs
sshpass -p 'Password@2021' scp -r docker/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/

# Rebuild on server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/signage/docker && docker-compose down && docker-compose up -d --build"
```

---

## Performance Tuning

### Adjust Celery Workers
Edit `docker-compose.yml`:
```yaml
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info --concurrency=8
```

### Adjust Redis Memory
Edit `docker-compose.yml`:
```yaml
redis:
  command: >
    redis-server
    --maxmemory 1gb
```

### Adjust PostgreSQL
Edit `.env`:
```bash
POSTGRES_POOL_MIN=5
POSTGRES_POOL_MAX=20
```

---

## Common Tasks

### View Celery Tasks in Flower
1. Open http://192.168.5.12:5555
2. Login with admin/admin123
3. Navigate to "Tasks" tab
4. See active, succeeded, failed tasks

### Manually Trigger Task
```bash
docker exec signage-celery-worker python -c "
from app.celery_app import celery_app
result = celery_app.send_task('app.tasks.cleanup_old_logs')
print(f'Task ID: {result.id}')
"
```

### Clear All Tasks
```bash
# Purge queue
docker exec signage-celery-worker celery -A app.celery_app purge

# Restart workers
docker-compose restart celery-worker celery-beat
```

---

## Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Update Flower credentials (`FLOWER_BASIC_AUTH`)
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET`
- [ ] Configure firewall to only allow necessary ports
- [ ] Use HTTPS in production (configure reverse proxy)
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity
- [ ] Keep Docker images updated

---

## Support

### View All Service Logs
```bash
docker-compose logs -f --tail=100
```

### Container Shell Access
```bash
# Backend
docker exec -it signage-backend bash

# Celery Worker
docker exec -it signage-celery-worker bash

# Viewer
docker exec -it signage-viewer sh

# PostgreSQL
docker exec -it signage-postgres psql -U signage_user -d signage_db
```

### Network Debugging
```bash
# Check network connectivity
docker network inspect signage-network

# Test connection between services
docker exec signage-backend ping redis
docker exec signage-celery-worker ping postgres
```

---

## Next Steps

1. **Create Celery Tasks**: Implement task modules in `backend/app/tasks/`
2. **Configure Beat Schedule**: Add periodic tasks in `celery_app.py`
3. **Test Background Processing**: Submit tasks and monitor in Flower
4. **Set Up Monitoring**: Configure alerts for failed tasks
5. **Production Deployment**: Add HTTPS, monitoring, and backups

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
