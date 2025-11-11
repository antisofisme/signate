#!/bin/bash
# Digital Signage Restore Script
# Restores system from backup

set -e

# Check arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /backup/signage/signage_backup_20241111_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"

# Database credentials
DB_HOST="localhost"
DB_PORT="5433"
DB_NAME="signage_db"
DB_USER="signage_user"
DB_PASS="${POSTGRES_PASSWORD:-signage_password}"

echo "[$(date)] Starting restore process..."

# Verify backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Create restore directory
mkdir -p "${RESTORE_DIR}"
cd "${RESTORE_DIR}"

# Extract backup
echo "[$(date)] Extracting backup..."
tar -xzf "${BACKUP_FILE}"
BACKUP_DIR=$(find . -maxdepth 1 -type d -name "signage_backup_*" | head -1)

if [ -z "${BACKUP_DIR}" ]; then
    echo "Error: Invalid backup archive structure"
    exit 1
fi

cd "${BACKUP_DIR}"

# Read manifest
if [ ! -f "manifest.json" ]; then
    echo "Error: Backup manifest not found"
    exit 1
fi

echo "[$(date)] Backup info:"
cat manifest.json

# Confirm restore
read -p "Continue with restore? This will overwrite existing data! (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 1
fi

# Stop services
echo "[$(date)] Stopping services..."
cd /home/gzjbbk/signage
docker-compose -f docker/docker-compose.yml stop

# 1. Restore database
echo "[$(date)] Restoring database..."
if [ -f "database.sql.gz" ]; then
    gunzip -c database.sql.gz > database.sql
    
    # Drop and recreate database
    PGPASSWORD="${DB_PASS}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};"
    
    PGPASSWORD="${DB_PASS}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d postgres \
        -c "CREATE DATABASE ${DB_NAME};"
    
    # Restore data
    PGPASSWORD="${DB_PASS}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -f database.sql
fi

# 2. Restore media files
echo "[$(date)] Restoring media files..."
if [ -f "media.tar.gz" ]; then
    # Backup current media
    if [ -d "/home/gzjbbk/signage/media" ]; then
        mv /home/gzjbbk/signage/media "/home/gzjbbk/signage/media.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Extract media
    tar -xzf media.tar.gz -C /home/gzjbbk/signage/
fi

# 3. Restore configurations
echo "[$(date)] Restoring configurations..."
if [ -f "configs.tar.gz" ]; then
    # Backup current configs
    cp /home/gzjbbk/signage/.env "/home/gzjbbk/signage/.env.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    
    # Extract configs to temp
    mkdir -p configs_temp
    tar -xzf configs.tar.gz -C configs_temp/
    
    # Selective restore (preserve current .env if needed)
    read -p "Restore .env file? Current settings will be overwritten (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp configs_temp/.env /home/gzjbbk/signage/.env
    fi
fi

# 4. Restore Docker volumes (optional)
echo "[$(date)] Restoring Docker volumes..."
if [ -f "postgres-volume.tar.gz" ]; then
    read -p "Restore PostgreSQL Docker volume? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker run --rm \
            -v signage_postgres-data:/target \
            -v "${PWD}":/backup:ro \
            alpine sh -c "rm -rf /target/* && tar -xzf /backup/postgres-volume.tar.gz -C /target"
    fi
fi

# 5. Start services
echo "[$(date)] Starting services..."
cd /home/gzjbbk/signage
docker-compose -f docker/docker-compose.yml up -d

# 6. Wait for services
echo "[$(date)] Waiting for services to start..."
sleep 10

# 7. Verify services
echo "[$(date)] Verifying services..."
docker-compose -f docker/docker-compose.yml ps

# Clean up
cd /
rm -rf "${RESTORE_DIR}"

echo "[$(date)] Restore completed successfully!"
echo "Please verify all services are running correctly."

# Send notification (optional)
# curl -X POST "http://localhost:8001/api/v1/notifications/restore" \
#   -H "Content-Type: application/json" \
#   -d "{\"status\":\"success\",\"backup\":\"${BACKUP_FILE}\"}"