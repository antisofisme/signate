#!/bin/bash

# =============================================================================
# RESET DATABASE - Development Only
# =============================================================================
# Script untuk recreate database dari scratch
# WARNING: Menghapus semua data di database!
# =============================================================================

set -e

echo "==========================================="
echo "  DATABASE RESET (Development)"
echo "==========================================="
echo ""
echo "⚠️  WARNING: Ini akan MENGHAPUS semua data!"
echo ""

read -p "Lanjutkan? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Dibatalkan."
    exit 1
fi

echo ""
echo "🛑 Stopping postgres container..."
docker-compose stop postgres

echo "🗑️  Removing postgres container..."
docker rm signage-postgres 2>/dev/null || true

echo "💾 Removing postgres volume (this deletes all data)..."
docker volume rm signage_postgres-data 2>/dev/null || true

echo "🚀 Starting fresh postgres with init.sql..."
docker-compose up -d postgres

echo "⏳ Waiting for postgres to initialize..."
sleep 8

echo ""
echo "✅ Database reset complete!"
echo ""
echo "Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
