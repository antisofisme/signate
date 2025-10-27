# Docker Deployment Files

This directory contains all Docker-related configuration and deployment scripts for the Smart TV Digital Signage system.

## 📁 Contents

- **docker-compose.yml** - Main Docker Compose configuration
- **rebuild.sh** - Complete system rebuild script
- **backup-database.sh** - Database backup script
- **reset-database.sh** - Database reset script (development only)

## 🚀 Quick Start

### Start All Services

```bash
# From project root
docker-compose -f docker/docker-compose.yml up -d
```

### Stop All Services

```bash
docker-compose -f docker/docker-compose.yml down
```

### View Logs

```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.yml logs -f backend-api
```

## 🔧 Management Scripts

### 1. Complete Rebuild (`rebuild.sh`)

Completely rebuilds all Docker containers from scratch. Use when you have major code changes or want a fresh start.

```bash
cd /home/gzjbbk/signate
./docker/rebuild.sh
```

**What it does:**
1. Stops all containers
2. Removes old containers
3. Optionally removes volumes (asks for confirmation)
4. Rebuilds images from scratch
5. Starts all services
6. Shows service status

**When to use:**
- After major code changes
- When switching branches
- When troubleshooting persistent issues
- After updating dependencies

### 2. Database Backup (`backup-database.sh`)

Creates a compressed backup of the PostgreSQL database.

```bash
cd /home/gzjbbk/signate
./docker/backup-database.sh
```

**Output:**
- Backup file: `database/backups/backup_YYYYMMDD_HHMMSS.sql.gz`

**To restore a backup:**
```bash
gunzip database/backups/backup_YYYYMMDD_HHMMSS.sql.gz
docker exec -i signage-postgres psql -U signage_user -d signage_db < database/backups/backup_YYYYMMDD_HHMMSS.sql
```

### 3. Database Reset (`reset-database.sh`)

⚠️ **DANGER**: Completely resets the database! Only use in development.

```bash
cd /home/gzjbbk/signate
./docker/reset-database.sh
```

**What it does:**
1. Confirms you really want to delete all data
2. Stops PostgreSQL container
3. Removes PostgreSQL container and volume
4. Creates fresh database with init.sql
5. Runs all migrations automatically

## 📦 Services

The docker-compose.yml defines these services:

### Backend API (`backend-api`)
- **Port**: 8001
- **Purpose**: FastAPI backend server
- **Health check**: http://localhost:8001/health
- **Auto-migrations**: Yes (runs on startup)
- **Dependencies**: postgres, redis

### PostgreSQL (`postgres`)
- **Port**: 5433 (host) → 5432 (container)
- **Database**: signage_db
- **User**: signage_user
- **Volume**: Persistent data in `postgres-data`
- **Connection**: `postgresql://signage_user:password@localhost:5433/signage_db`

### Redis (`redis`)
- **Port**: 6379
- **Purpose**: Caching and session storage
- **Volume**: Persistent data in `redis-data`

## 🔄 Auto-Migration System

The backend container automatically runs database migrations on startup:

1. **Waits** for PostgreSQL to be ready
2. **Checks** which migrations have been applied
3. **Runs** pending migrations in order
4. **Records** migration status
5. **Starts** FastAPI application

**Migration tracking table:**
```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version INTEGER UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE
);
```

**Check migration status:**
```bash
docker exec signage-postgres psql -U signage_user -d signage_db \
    -c "SELECT * FROM schema_migrations ORDER BY version;"
```

## 🔍 Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs backend-api

# Check container status
docker ps -a

# Restart specific service
docker-compose -f docker/docker-compose.yml restart backend-api
```

### Database connection failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs signage-postgres

# Test connection
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT 1;"
```

### Migration failed

```bash
# Check migration logs
docker logs signage-backend | grep migration

# Check failed migrations
docker exec signage-postgres psql -U signage_user -d signage_db \
    -c "SELECT * FROM schema_migrations WHERE success = FALSE;"

# Manually run migration
docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < backend/migrations/XXX_migration_name.sql
```

### Port already in use

```bash
# Find process using port 8001
sudo lsof -i :8001

# Kill process (use PID from above)
sudo kill -9 <PID>

# Or change port in docker-compose.yml
```

## 📊 Monitoring

### View service status

```bash
docker-compose -f docker/docker-compose.yml ps
```

### Check container health

```bash
docker inspect signage-backend --format='{{.State.Health.Status}}'
```

### Monitor logs in real-time

```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Backend only
docker-compose -f docker/docker-compose.yml logs -f backend-api

# Last 100 lines
docker-compose -f docker/docker-compose.yml logs --tail=100 backend-api
```

## 🔒 Security Notes

1. **Environment Variables**: Never commit `.env` file to Git
2. **Database Password**: Change default password in production
3. **Non-root User**: Backend runs as `appuser` (UID 1000)
4. **Network Isolation**: Services use private Docker network
5. **Volume Permissions**: Set correct permissions on mounted volumes

## 🌐 Network

All services run on a custom bridge network: `signage-network`

**DNS resolution:**
- `postgres` → PostgreSQL container
- `redis` → Redis container
- `backend-api` → Backend API container

## 💾 Volumes

Persistent data is stored in Docker volumes:

- **postgres-data**: Database files
- **redis-data**: Redis persistence
- **backend/migrations**: Migration SQL files (bind mount)
- **backend/app**: Application code (bind mount)

## 📝 Environment Variables

Required in `.env` file at project root:

```env
# Database
DATABASE_URL=postgresql://signage_user:password@postgres:5432/signage_db

# Redis
REDIS_URL=redis://redis:6379/0

# API
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development

# CORS
CORS_ORIGINS=http://localhost:3000,http://192.168.5.12:3000
```

## 🔄 Update Workflow

### For code changes only:

```bash
# Sync code to server
rsync -avz backend/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend/

# Restart backend (no rebuild needed)
docker-compose -f docker/docker-compose.yml restart backend-api
```

### For dependency changes:

```bash
# Rebuild backend image
docker-compose -f docker/docker-compose.yml build backend-api

# Restart with new image
docker-compose -f docker/docker-compose.yml up -d backend-api
```

### For everything:

```bash
./docker/rebuild.sh
```

## 📚 Documentation Links

- [Backend README](../backend/README.md)
- [Migrations README](../backend/migrations/README.md)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

## ⚡ Performance Tips

1. **Use BuildKit** for faster builds:
   ```bash
   export DOCKER_BUILDKIT=1
   ```

2. **Multi-stage builds** are already configured in Dockerfile

3. **Volume mounts** for development (hot reload)

4. **Health checks** ensure services are ready before dependent services start

5. **Resource limits** can be added in docker-compose.yml if needed

## 🆘 Getting Help

If you encounter issues:

1. Check this README first
2. Review logs: `docker-compose logs`
3. Check service status: `docker-compose ps`
4. Verify environment variables in `.env`
5. Try a complete rebuild: `./docker/rebuild.sh`
6. Check CLAUDE.md in project root for server-specific notes

## 📞 Contacts

- **Server**: 192.168.5.12
- **SSH User**: gzjbbk
- **Backend API**: http://192.168.5.12:8001
- **API Docs**: http://192.168.5.12:8001/docs
