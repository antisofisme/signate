#!/bin/bash

# =============================================================================
# BACKUP DATABASE - Production Safe
# =============================================================================
# Script untuk backup database PostgreSQL
# Data tetap aman di volume, hanya membuat backup file
# =============================================================================

set -e

# Change to parent directory (project root)
cd "$(dirname "$0")/.."

BACKUP_DIR="./database/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

echo "==========================================="
echo "  DATABASE BACKUP"
echo "==========================================="
echo ""
echo "Working directory: $(pwd)"
echo ""

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

echo "📦 Creating backup..."
docker exec signage-postgres pg_dump -U signage_user signage_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo ""
echo "✅ Backup created: ${BACKUP_FILE}.gz"
echo ""
echo "To restore this backup:"
echo "  gunzip ${BACKUP_FILE}.gz"
echo "  docker exec -i signage-postgres psql -U signage_user -d signage_db < $BACKUP_FILE"
echo ""

# List recent backups
echo "Recent backups:"
ls -lh $BACKUP_DIR | tail -5
echo ""
