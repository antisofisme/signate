# Docker Deployment Guide

## Architecture

This Docker Compose setup deploys the complete Digital Signage system with:

### Services:

1. **postgres** (Port 5433) - PostgreSQL Database
2. **redis** (Port 6379) - Redis Cache
3. **backend-api** (Port 8001) - FastAPI Backend
4. **celery-worker** - Background Task Worker
5. **player** (Port 8080) - Player Static Site (Nginx)

### URLs:

- Backend API: http://192.168.5.12:8001
- API Docs: http://192.168.5.12:8001/docs
- Player: http://192.168.5.12:8080

---

## Quick Start

### Deploy All Services

**IMPORTANT:** Always run from project root!

```bash
cd /home/gzjbbk/prototipe2

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Or use deployment script
./docker/deploy.sh
```

### Verify Deployment

```bash
# Check status
docker-compose -f docker/docker-compose.yml ps

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8080/
```

---

## Management Commands

```bash
# Rebuild specific service
docker-compose -f docker/docker-compose.yml up -d --build player

# View logs
docker logs -f signage-player

# Restart service
docker-compose -f docker/docker-compose.yml restart player

# Stop all
docker-compose -f docker/docker-compose.yml down
```

See full documentation in this file for troubleshooting and advanced usage.
