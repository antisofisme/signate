#!/bin/bash

# =============================================================================
# SMART TV DIGITAL SIGNAGE - REBUILD SCRIPT
# =============================================================================
# Script untuk rebuild semua Docker containers dari scratch
# Memastikan semua perubahan code dan config di-apply dengan benar
# =============================================================================

set -e  # Exit on error

echo "=========================================="
echo "  SIGNAGE SYSTEM - COMPLETE REBUILD"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on server
if [ ! -d "/home/gzjbbk" ]; then
    print_error "Script harus dijalankan di server (192.168.5.12)"
    exit 1
fi

# Step 1: Stop dan hapus containers lama
print_step "1/5 - Stopping old containers..."
docker-compose down --remove-orphans || true

# Stop old anthias containers if exists
docker stop $(docker ps -aq --filter "name=anthias") 2>/dev/null || true
docker stop signage-backend 2>/dev/null || true

print_step "Removing old containers..."
docker rm $(docker ps -aq --filter "name=anthias") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=signage") 2>/dev/null || true

# Step 2: Cleanup (optional - comment out if you want to keep data)
read -p "Hapus volumes (data akan hilang)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Removing volumes..."
    docker volume rm $(docker volume ls -q --filter "name=signate") 2>/dev/null || true
else
    print_step "Keeping existing volumes (data preserved)"
fi

# Step 3: Cleanup networks
print_step "2/5 - Cleaning up networks..."
docker network rm signate_signage-network 2>/dev/null || true
docker network rm anthias_default 2>/dev/null || true

# Step 4: Build fresh images
print_step "3/5 - Building fresh Docker images (this may take a while)..."
docker-compose build --no-cache --parallel

# Step 5: Start services
print_step "4/5 - Starting all services..."
docker-compose up -d

# Step 6: Wait and check health
print_step "5/5 - Waiting for services to be healthy..."
sleep 10

# Show status
echo ""
print_step "Checking service status..."
docker-compose ps

echo ""
echo "=========================================="
echo "  REBUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - PostgreSQL:     localhost:5433"
echo "  - Redis:          localhost:6379"
echo "  - Backend API:    http://192.168.5.12:8001"
echo "  - Anthias:        http://192.168.5.12:8000"
echo ""
echo "Check logs:"
echo "  docker-compose logs -f"
echo ""
echo "Check specific service:"
echo "  docker-compose logs -f backend-api"
echo "  docker-compose logs -f anthias-server"
echo ""
