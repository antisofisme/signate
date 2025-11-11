#!/bin/bash
# Digital Signage Backup Script - Phase 6 Simple Version
# Performs automated backup of database, media files, and configurations

set -e

# Configuration
BACKUP_DIR="/backup/signage"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="signage_backup_${TIMESTAMP}"
RETENTION_DAYS=7

# Database credentials
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="signage_db"
DB_USER="signage_user"
DB_PASS="${POSTGRES_PASSWORD:-signage_password}"

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
cd "${BACKUP_DIR}/${BACKUP_NAME}"

echo "[$(date)] Starting backup process..."

# 1. Backup PostgreSQL Database
echo "[$(date)] Backing up PostgreSQL database..."
PGPASSWORD="${DB_PASS}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    -f "database.sql" \
    --verbose \
    --no-owner \
    --no-privileges

# Compress database backup
gzip -9 database.sql

# 2. Backup media files
echo "[$(date)] Backing up media files..."
if [ -d "/home/gzjbbk/signage/media" ]; then
    tar -czf media.tar.gz -C /home/gzjbbk/signage media/
fi

# 3. Backup configuration files
echo "[$(date)] Backing up configuration files..."
tar -czf configs.tar.gz \
    -C /home/gzjbbk/signage \
    .env \
    docker/docker-compose.yml \
    backend-python/requirements.txt \
    cms-vite/package.json \
    player-vite/package.json \
    2>/dev/null || true

# 4. Backup Docker volumes (optional)
echo "[$(date)] Backing up Docker volumes..."
docker run --rm \
    -v signage_postgres-data:/source:ro \
    -v "${BACKUP_DIR}/${BACKUP_NAME}":/backup \
    alpine tar -czf /backup/postgres-volume.tar.gz -C /source .

# 5. Create backup manifest
echo "[$(date)] Creating backup manifest..."
cat > manifest.json << EOF
{
  "timestamp": "${TIMESTAMP}",
  "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "1.0.0",
  "components": {
    "database": "database.sql.gz",
    "media": "media.tar.gz",
    "configs": "configs.tar.gz",
    "volumes": "postgres-volume.tar.gz"
  },
  "size": "$(du -sh . | cut -f1)",
  "retention_days": ${RETENTION_DAYS}
}
EOF

# 6. Create final archive
echo "[$(date)] Creating final backup archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
rm -rf "${BACKUP_NAME}/"

# 7. Upload to remote storage (optional)
# Uncomment and configure for S3, FTP, etc.
# aws s3 cp "${BACKUP_NAME}.tar.gz" s3://your-bucket/backups/

# 8. Clean old backups
echo "[$(date)] Cleaning old backups..."
find "${BACKUP_DIR}" -name "signage_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

echo "[$(date)] Backup completed successfully!"
echo "Backup saved to: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# 9. Send notification (optional)
# curl -X POST "http://localhost:8001/api/v1/notifications/backup" \
#   -H "Content-Type: application/json" \
#   -d "{\"status\":\"success\",\"file\":\"${BACKUP_NAME}.tar.gz\"}"