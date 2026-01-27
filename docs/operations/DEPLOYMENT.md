# Deployment Guide

## Code Synchronization Protocol

**SETIAP perubahan code WAJIB update di KEDUA lokasi:**
1. Local development
2. Server (VPS atau Local Network)

### Files yang WAJIB Sinkron

**Configuration:**
- `.env` (local & server)
- `.env.example`
- `backend/app/core/config.py`

**Source Code:**
- CMS Admin: `cms-vite/src/**/*`
- Backend: `backend-python/app/**/*`
- Player: `player-vite/**/*`
- WebOS App: `webos-app/**/*`

---

## Deployment Workflow

### Local → VPS Production

```bash
# 1. Test di local
npm run dev          # frontend
uvicorn app.main:app --reload  # backend

# 2. Sync ke VPS
sshpass -p 'Bait174663@vps' rsync -avz \
  --exclude '__pycache__' \
  --exclude 'node_modules' \
  --exclude '.git' \
  /mnt/g/khoirul/signate/ root@31.97.111.175:/root/signage/

# 3. Rebuild container
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "cd /root/signage && docker-compose -f docker/docker-compose.yml up -d --build backend-api"
```

### Local → Local Network Server

```bash
# 1. Sync files
sshpass -p 'Password@2021' scp -r \
  file_yang_diubah gzjbbk@192.168.5.12:/home/gzjbbk/signate/

# 2. Rebuild container
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml up -d --build backend-api"
```

---

## Migration Deployment

### Pre-Migration

```bash
# 1. Backup database (VPS)
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/vps_pre_migration_XXX_$(date +%Y%m%d_%H%M%S).sql

# 2. Stop backend
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "cd /root/signage && docker-compose -f docker/docker-compose.yml stop backend-api"
```

### Run Migration

```bash
# 3. Upload migration file
sshpass -p 'Bait174663@vps' scp \
  backend-python/migrations/XXX_*.sql \
  root@31.97.111.175:/root/signage/backend-python/migrations/

# 4. Execute migration
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db \
   < /root/signage/backend-python/migrations/XXX_*.sql"
```

### Post-Migration

```bash
# 5. Sync code if needed
sshpass -p 'Bait174663@vps' rsync -avz --exclude '__pycache__' \
  backend-python/ root@31.97.111.175:/root/signage/backend-python/

# 6. Restart backend
sshpass -p 'Bait174663@vps' ssh root@31.97.111.175 \
  "cd /root/signage && docker-compose -f docker/docker-compose.yml start backend-api"

# 7. Verify
curl http://31.97.111.175:25536/health
```

---

## Best Practices

1. **SELALU update LOCAL dulu, baru SERVER**
2. **COMMIT ke Git setelah update sukses**
3. **Test di local sebelum deploy**
4. **Dokumentasikan perubahan di commit message**
5. **Backup database sebelum migration**

### Konsekuensi Jika TIDAK Sinkron

- Reinstall dari local kehilangan perubahan server
- Konfigurasi tidak konsisten
- Bug yang sudah fixed muncul lagi
- Dev environment berbeda dengan production
