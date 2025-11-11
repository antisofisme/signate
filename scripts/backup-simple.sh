#!/bin/bash
# Phase 6 Simple Backup Script

BACKUP_DIR="/home/gzjbbk/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/signage_db_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec signage-postgres pg_dump -U signage_user signage_db > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"

# Upload to S3 (optional)
# aws s3 cp $BACKUP_FILE.gz s3://my-backups/signage/