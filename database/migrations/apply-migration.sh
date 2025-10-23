#!/bin/bash
# =============================================================================
# Migration Script - Apply database migrations
# =============================================================================

set -e  # Exit on error

echo "========================================="
echo "Database Migration Script"
echo "========================================="
echo ""

# Configuration
CONTAINER_NAME="signate-postgres"
DB_NAME="signage_db"
DB_USER="postgres"
MIGRATION_FILE="001_add_uuid_support.sql"

# Check if container is running
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ Error: Container $CONTAINER_NAME is not running"
    echo ""
    echo "Start the container first:"
    echo "  cd /home/gzjbbk/signage"
    echo "  docker-compose up -d"
    exit 1
fi

echo "✅ Container $CONTAINER_NAME is running"
echo ""

# Backup database first
echo "📦 Creating backup..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE

if [ -f "$BACKUP_FILE" ]; then
    echo "✅ Backup created: $BACKUP_FILE"
else
    echo "❌ Error: Backup failed"
    exit 1
fi
echo ""

# Apply migration
echo "🔄 Applying migration: $MIGRATION_FILE"
echo ""

docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < $MIGRATION_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Migration applied successfully!"
    echo "========================================="
    echo ""
    echo "Backup file: $BACKUP_FILE"
    echo ""

    # Show verification
    echo "📊 Database Status:"
    docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
    SELECT
        COUNT(*) as total_devices,
        COUNT(device_uuid) as devices_with_uuid,
        COUNT(unique_code) as devices_with_code,
        COUNT(CASE WHEN platform = 'browser' THEN 1 END) as browser_devices,
        COUNT(CASE WHEN platform = 'webOS' THEN 1 END) as webos_devices
    FROM devices;
    "
else
    echo ""
    echo "========================================="
    echo "❌ Migration failed!"
    echo "========================================="
    echo ""
    echo "To restore backup:"
    echo "  docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < $BACKUP_FILE"
    exit 1
fi
