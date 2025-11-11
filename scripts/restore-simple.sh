#!/bin/bash
# Phase 6 Simple Restore Script

if [ -z "$1" ]; then
  echo "Usage: ./restore-simple.sh <backup_file.sql.gz>"
  exit 1
fi

BACKUP_FILE=$1

# Decompress
gunzip -c $BACKUP_FILE > /tmp/restore.sql

# Stop backend
docker-compose -f docker/docker-compose.yml stop backend-api

# Drop and recreate database
docker exec -it signage-postgres psql -U signage_user postgres -c "DROP DATABASE IF EXISTS signage_db;"
docker exec -it signage-postgres psql -U signage_user postgres -c "CREATE DATABASE signage_db;"

# Restore
docker exec -i signage-postgres psql -U signage_user signage_db < /tmp/restore.sql

# Restart backend
docker-compose -f docker/docker-compose.yml start backend-api

rm /tmp/restore.sql
echo "Restore completed!"