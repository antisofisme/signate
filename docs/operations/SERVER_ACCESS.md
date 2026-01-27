# Server Access & Credentials

> **SECURITY WARNING**: File ini berisi credentials sensitif. Jangan commit ke public repo.

## VPS Production Server (Primary)

| Field | Value |
|-------|-------|
| IP Address | 31.97.111.175 |
| SSH User | root |
| SSH Password | `Bait174663@vps` |
| Project Directory | `/root/atlas-puguh/` (ATLAS_PUGUH) |
| Legacy Directory | `/root/signage/` (old signage) |
| OS | Ubuntu/Debian |
| Orchestration | Nomad (namespace: puguh) |

### Services Running on VPS

| Service | Status | Port | Notes |
|---------|--------|------|-------|
| Nomad | ✅ | - | Container orchestration |
| Consul | ✅ | - | Service discovery |
| Docker | ✅ | - | Container runtime |
| PostgreSQL | ✅ | 5433 | job: puguh-postgres |
| Backend API | ✅ | Dynamic (25536) | job: puguh-backend |
| Frontend | ✅ | 3000 | job: puguh-frontend |

### VPS URLs

**Direct IP Access:**
- Frontend UI: http://31.97.111.175:3000/
- Backend API: http://31.97.111.175:25536/api/
- API Docs: http://31.97.111.175:25536/docs
- Health Check: http://31.97.111.175:25536/health

**Legacy URLs (may not work):**
- Player: http://31.97.111.175:8080/
- CMS Admin: http://31.97.111.175:3000/
- Backend: http://31.97.111.175:8001/
- Portainer: http://31.97.111.175:9000/

---

## Local Network Server (Development)

| Field | Value |
|-------|-------|
| IP Address | 192.168.5.12 |
| SSH User | gzjbbk |
| SSH Password | Password@2021 |
| Project Directory | `/home/gzjbbk/signate/` |
| Purpose | Development & testing |

### Local URLs

- Player: http://192.168.5.12:8080/
- CMS Admin: http://192.168.5.12:3000/
- Backend API: http://192.168.5.12:8001/
- API Docs: http://192.168.5.12:8001/docs

---

## Service Ports

| Port | Service | Description |
|------|---------|-------------|
| 8001 | Backend API | FastAPI |
| 3000 | CMS Admin | React + Vite |
| 5433 | PostgreSQL | Database |
| 8080 | Player/Viewer | Vite player |
| 80/443 | Nginx | Reverse proxy (VPS) |
| 9000 | Portainer | Docker management |

---

## Default Test Credentials

### Users (Clean Database - 2025-11-27)

| Username | Password | Role | Organization |
|----------|----------|------|--------------|
| superadmin | admin123 | SUPER_ADMIN | All (system-wide) |
| tenantadmin | admin123 | ADMIN | Hotel Signage Demo |

### Organizations

| ID | Name |
|----|------|
| 21 | System |
| 22 | Hotel Signage Demo |

### Roles

| ID | Role | Description |
|----|------|-------------|
| 5 | SUPER_ADMIN | System-wide access |
| 6 | ADMIN | Organization admin |
| 7 | CONTENT_MANAGER | Manage content & playlists |
| 8 | VIEWER | View only access |

### Password Hash (bcrypt)
```
$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2
```

---

## Quick SSH Commands

### VPS
```bash
# SSH ke VPS
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175

# Check Nomad jobs
ssh root@31.97.111.175 "nomad job status -namespace=puguh"

# View backend logs
ssh root@31.97.111.175 "docker logs signage-backend --tail 50"

# Access database
ssh root@31.97.111.175 "docker exec -it signage-postgres psql -U signage_user -d signage_db"
```

### Local Server
```bash
# SSH ke local server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Check services
docker-compose -f docker/docker-compose.yml ps

# View logs
docker logs signage-backend --tail 50
```

---

## SSL Certificate (VPS Only)

| Field | Value |
|-------|-------|
| Provider | Let's Encrypt |
| Expires | 2026-02-24 |
| Auto-renewal | Enabled |
| Location | `/etc/letsencrypt/live/admin.zhmhotels.online/` |

### Subdomains with SSL
- admin.zhmhotels.online
- player.zhmhotels.online
- api.zhmhotels.online
- portainer.zhmhotels.online

### SSL Commands
```bash
# Check expiration
ssh root@31.97.111.175 "certbot certificates"

# Renew manually
ssh root@31.97.111.175 "certbot renew"

# Test renewal
ssh root@31.97.111.175 "certbot renew --dry-run"
```

---

## Nginx Configuration (VPS)

| Subdomain | Port | Service |
|-----------|------|---------|
| admin.zhmhotels.online | 3000 | CMS Admin |
| player.zhmhotels.online | 8080 | Player |
| api.zhmhotels.online | 8001 | Backend API |
| portainer.zhmhotels.online | 9000 | Portainer |

### Nginx Commands
```bash
# Test config
ssh root@31.97.111.175 "nginx -t"

# Reload
ssh root@31.97.111.175 "systemctl reload nginx"

# View error logs
ssh root@31.97.111.175 "tail -f /var/log/nginx/error.log"
```
