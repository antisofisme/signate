# Docker - Archived Files

This folder contains old/unused Docker configuration files that have been archived for reference.

## Folder Structure

### `old-compose/` (2 files)
Old versions of docker-compose configuration files.

**Archived Files**:
- `docker-compose.old.yml` (Nov 6, 2024) - Very old version
- `docker-compose.old-dev.yml` (Nov 24, 2024) - Development version with old structure

**Why Archived**:
- Multiple docker-compose versions caused confusion
- Production version (docker-compose-production.yml) is now the single source of truth
- Renamed to `docker-compose.yml` to avoid version fragmentation

---

### `configs/` (4 files)
Old configuration files that are no longer used.

**Archived Files**:
- `pgbouncer-minimal.ini` - Minimal PgBouncer config (superseded by pgbouncer.ini)
- `prometheus.yml` - Prometheus monitoring config (not used)
- `userlist.txt` - Old PgBouncer userlist (superseded by environment variables)
- `nginx-proxy.conf` - Old nginx proxy config (superseded by nginx/ folder structure)

**Why Archived**:
- Replaced by better/complete configurations
- Not used in current production setup

---

### `scripts/` (5 files)
Old deployment and utility scripts.

**Archived Files**:
- `deploy.sh` (Nov 7, 2024) - Old deployment script
- `rebuild.sh` (Oct 29, 2024) - Old rebuild script
- `reset-database.sh` (Oct 29, 2024) - Old database reset script
- `validate-config.sh` (Oct 29, 2024) - Old config validation script
- `viewer-config-loader.js` (Oct 29, 2024) - Old viewer config (player-vite is now Vite-based)

**Why Archived**:
- Outdated (October versions)
- Replaced by deploy-production.sh
- viewer-config-loader.js not needed (player-vite uses Vite config)

---

## Active Files (Current docker/ folder)

**Docker Compose**:
- `docker-compose.yml` - Single source of truth (production config)

**Environment Files**:
- `.env.local` - Local development environment template
- `.env.production` - Production environment template

**Deployment Scripts**:
- `deploy-production.sh` - Production deployment script
- `backup-database.sh` - Database backup utility
- `setup-nginx.sh` - Nginx setup script
- `setup-ssl.sh` - SSL certificate setup script

**Configuration Files**:
- `pgbouncer.ini` - PgBouncer connection pooling config

**Documentation**:
- `README.md` - Docker setup documentation
- `DEPLOYMENT_CHECKLIST.md` - Deployment checklist
- `PORTAINER_SETUP_GUIDE.md` - Portainer setup guide
- `QUICK_REFERENCE.md` - Quick reference for common tasks

**Folders**:
- `envs/` - Environment variable templates
- `monitoring/` - Monitoring configs
- `nginx/` - Nginx configuration files
- `ssl/` - SSL certificates

---

## Changes Made (2025-11-26)

**Cleanup Actions**:
1. Merged docker-compose versions → Single `docker-compose.yml`
2. Archived old docker-compose variants (2 files)
3. Archived obsolete config files (4 files)
4. Archived outdated scripts (5 files)
5. Total archived: 11 files

**Benefits**:
- ✅ No version confusion (only one docker-compose.yml)
- ✅ Cleaner docker/ folder
- ✅ Easier maintenance
- ✅ Clear separation: active vs historical

---

**Last Updated**: 2025-11-26
**Archived By**: Claude Code
