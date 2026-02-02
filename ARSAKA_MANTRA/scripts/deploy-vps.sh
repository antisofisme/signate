#!/bin/bash
# ARSAKA_MANTRA VPS Deployment Script
# This script ensures all prerequisites are met before deploying
#
# Usage: ./deploy-vps.sh [--skip-build] [--skip-migrations]

set -e

# Configuration
VPS_HOST="31.97.111.175"
VPS_USER="root"
VPS_PASS="Bait174663@vps"
REMOTE_DIR="/root/arsaka-mantra"
NAMESPACE="mantra"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
SKIP_BUILD=false
SKIP_MIGRATIONS=false
for arg in "$@"; do
    case $arg in
        --skip-build) SKIP_BUILD=true ;;
        --skip-migrations) SKIP_MIGRATIONS=true ;;
    esac
done

ssh_cmd() {
    sshpass -p "$VPS_PASS" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_HOST" "$1"
}

scp_cmd() {
    sshpass -p "$VPS_PASS" scp -o StrictHostKeyChecking=no -r "$1" "$VPS_USER@$VPS_HOST:$2"
}

echo "================================================"
echo "  ARSAKA_MANTRA VPS Deployment"
echo "================================================"
echo ""

# Step 1: Sync code to VPS
log_info "Step 1: Syncing code to VPS..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

sshpass -p "$VPS_PASS" rsync -avz --exclude '__pycache__' --exclude '.git' --exclude 'node_modules' \
    "$PROJECT_DIR/" "$VPS_USER@$VPS_HOST:$REMOTE_DIR/" 2>/dev/null
log_info "Code synced successfully"

# Step 2: Build Docker image
if [ "$SKIP_BUILD" = false ]; then
    log_info "Step 2: Building Docker image..."
    ssh_cmd "cd $REMOTE_DIR/backend && docker build -t arsaka-mantra-api:v2.0.0 ."
    log_info "Docker image built: arsaka-mantra-api:v2.0.0"
else
    log_warn "Step 2: Skipping Docker build (--skip-build)"
fi

# Step 3: Verify/Set Consul KV
log_info "Step 3: Checking Consul KV..."
DB_PASS=$(ssh_cmd "consul kv get mantra/db_password 2>/dev/null" || echo "")
if [ -z "$DB_PASS" ]; then
    log_warn "Consul KV 'mantra/db_password' not set. Setting now..."
    ssh_cmd "consul kv put mantra/db_password 'mantra_password'"
    log_info "Consul KV set successfully"
else
    log_info "Consul KV already set"
fi

# Step 4: Check if Postgres is running
log_info "Step 4: Checking PostgreSQL status..."
PG_STATUS=$(ssh_cmd "nomad job status -namespace=$NAMESPACE mantra-postgres 2>/dev/null | grep 'Status' | head -1" || echo "")
if [[ "$PG_STATUS" != *"running"* ]]; then
    log_error "PostgreSQL is not running! Deploy postgres first:"
    echo "  nomad job run -namespace=$NAMESPACE $REMOTE_DIR/nomad/mantra-postgres.nomad"
    exit 1
fi
log_info "PostgreSQL is running"

# Step 5: Deploy/Update backend job
log_info "Step 5: Deploying backend Nomad job..."
ssh_cmd "cd $REMOTE_DIR/nomad && nomad job run -namespace=$NAMESPACE mantra-backend.nomad"

# Wait for deployment
log_info "Waiting for backend to be healthy..."
sleep 10

# Step 6: Run migrations if needed
if [ "$SKIP_MIGRATIONS" = false ]; then
    log_info "Step 6: Checking/Running migrations..."

    # Find postgres container
    PG_CONTAINER=$(ssh_cmd "docker ps --format '{{.Names}}' | grep postgres | grep mantra | head -1" || echo "")

    if [ -n "$PG_CONTAINER" ]; then
        # Check if tables exist
        TABLE_COUNT=$(ssh_cmd "docker exec $PG_CONTAINER psql -U mantra_owner -d arsaka_mantra -t -c \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'\"" 2>/dev/null | tr -d ' ' || echo "0")

        if [ "$TABLE_COUNT" -lt 3 ]; then
            log_warn "Database tables missing. Running migrations..."
            for migration in 001 002 003 004; do
                MIGRATION_FILE="$REMOTE_DIR/backend/migrations/${migration}_*.sql"
                ssh_cmd "docker exec -i $PG_CONTAINER psql -U mantra_owner -d arsaka_mantra < $MIGRATION_FILE" 2>/dev/null || true
            done
            log_info "Migrations completed"
        else
            log_info "Database already has $TABLE_COUNT tables"
        fi
    else
        log_warn "Could not find postgres container"
    fi
else
    log_warn "Step 6: Skipping migrations (--skip-migrations)"
fi

# Step 7: Verify deployment
log_info "Step 7: Verifying deployment..."
sleep 5
HEALTH=$(ssh_cmd "curl -s http://localhost:8002/health" 2>/dev/null || echo "{}")

if [[ "$HEALTH" == *"healthy"* ]]; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "  Backend API:  http://$VPS_HOST:8002/"
    echo "  API Docs:     http://$VPS_HOST:8002/docs"
    echo "  Health:       http://$VPS_HOST:8002/health"
    echo ""
else
    log_error "Health check failed!"
    echo "Check logs with: nomad alloc logs -namespace=$NAMESPACE <alloc-id>"
    exit 1
fi
