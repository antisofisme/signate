#!/bin/bash
# =============================================================================
# ATLAS_CHAT_AI Deployment Script
# =============================================================================
# Usage:
#   ./scripts/deploy.sh [staging|production]
#
# Prerequisites:
#   - SSH access to VPS configured
#   - Docker and Docker Compose installed on VPS
#   - .env file configured with production values
# =============================================================================

set -e

# Configuration
VPS_HOST="${VPS_HOST:-31.97.111.175}"
VPS_USER="${VPS_USER:-root}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/atlas-chat}"
PROJECT_NAME="atlas-chat"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
ENVIRONMENT="${1:-production}"
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    echo "Usage: $0 [staging|production]"
    exit 1
fi

log_info "Deploying ATLAS_CHAT_AI to ${ENVIRONMENT}..."
log_info "Target: ${VPS_USER}@${VPS_HOST}:${DEPLOY_DIR}"

# =============================================================================
# Step 1: Pre-deployment checks
# =============================================================================
log_info "Step 1: Pre-deployment checks..."

# Check SSH connectivity
if ! ssh -o ConnectTimeout=5 "${VPS_USER}@${VPS_HOST}" "echo 'SSH OK'" > /dev/null 2>&1; then
    log_error "Cannot connect to VPS. Check SSH configuration."
    exit 1
fi
log_success "SSH connection OK"

# Check if .env exists
if [[ ! -f "docker/.env" ]]; then
    log_warn ".env file not found. Creating from template..."
    if [[ -f "docker/.env.example" ]]; then
        cp docker/.env.example docker/.env
        log_warn "Please edit docker/.env with production values before continuing"
        exit 1
    else
        log_error ".env.example not found"
        exit 1
    fi
fi
log_success ".env file exists"

# =============================================================================
# Step 2: Build Docker images locally
# =============================================================================
log_info "Step 2: Building Docker images..."

cd "$(dirname "$0")/.."

# Get version from .env or use latest
VERSION=$(grep "^VERSION=" docker/.env | cut -d'=' -f2 || echo "latest")
API_IMAGE="atlas-chat-api:${VERSION}"
ADMIN_IMAGE="atlas-chat-admin:${VERSION}"

# Build API image
log_info "Building API image..."
docker build -t "${API_IMAGE}" -f docker/Dockerfile .
log_success "Built ${API_IMAGE}"

# Build Admin frontend image
log_info "Building Admin frontend image..."
docker build -t "${ADMIN_IMAGE}" -f frontend/Dockerfile ./frontend
log_success "Built ${ADMIN_IMAGE}"

# =============================================================================
# Step 3: Save and transfer images
# =============================================================================
log_info "Step 3: Transferring images to VPS..."

# Create deploy directory on VPS
ssh "${VPS_USER}@${VPS_HOST}" "mkdir -p ${DEPLOY_DIR}"

# Save and transfer API image
TEMP_API="/tmp/atlas-chat-api.tar"
docker save "${API_IMAGE}" > "${TEMP_API}"
scp "${TEMP_API}" "${VPS_USER}@${VPS_HOST}:${DEPLOY_DIR}/atlas-chat-api.tar"
rm -f "${TEMP_API}"
log_success "API image transferred"

# Save and transfer Admin image
TEMP_ADMIN="/tmp/atlas-chat-admin.tar"
docker save "${ADMIN_IMAGE}" > "${TEMP_ADMIN}"
scp "${TEMP_ADMIN}" "${VPS_USER}@${VPS_HOST}:${DEPLOY_DIR}/atlas-chat-admin.tar"
rm -f "${TEMP_ADMIN}"
log_success "Admin frontend image transferred"

# =============================================================================
# Step 4: Transfer configuration files
# =============================================================================
log_info "Step 4: Transferring configuration files..."

# Transfer docker-compose and .env
scp docker/docker-compose.prod.yml "${VPS_USER}@${VPS_HOST}:${DEPLOY_DIR}/docker-compose.yml"
scp docker/.env "${VPS_USER}@${VPS_HOST}:${DEPLOY_DIR}/.env"

# Transfer migrations
ssh "${VPS_USER}@${VPS_HOST}" "mkdir -p ${DEPLOY_DIR}/migrations"
scp backend/infrastructure/database/migrations/*.sql "${VPS_USER}@${VPS_HOST}:${DEPLOY_DIR}/migrations/"

log_success "Configuration files transferred"

# =============================================================================
# Step 5: Deploy on VPS
# =============================================================================
log_info "Step 5: Deploying on VPS..."

ssh "${VPS_USER}@${VPS_HOST}" << ENDSSH
set -e
cd ${DEPLOY_DIR}

# Load images
echo "Loading Docker images..."
docker load < atlas-chat-api.tar
rm -f atlas-chat-api.tar
docker load < atlas-chat-admin.tar
rm -f atlas-chat-admin.tar

# Stop existing containers (if any)
echo "Stopping existing containers..."
docker compose down --remove-orphans 2>/dev/null || true

# Start services
echo "Starting services..."
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 15

# Check health
echo "Checking service health..."
docker compose ps

# Show logs
echo "Recent logs:"
docker compose logs --tail=20 chat-api chat-admin

echo "Deployment complete!"
ENDSSH

log_success "Deployment complete!"

# =============================================================================
# Step 6: Post-deployment verification
# =============================================================================
log_info "Step 6: Post-deployment verification..."

# Get API port from .env
API_PORT=$(grep "^API_PORT=" docker/.env | cut -d'=' -f2 || echo "8003")

# Wait a bit more for full startup
sleep 5

# Check health endpoint
HEALTH_URL="http://${VPS_HOST}:${API_PORT}/api/v1/health"
log_info "Checking health endpoint: ${HEALTH_URL}"

if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
    log_success "Health check passed!"
    curl -s "${HEALTH_URL}" | python3 -m json.tool 2>/dev/null || curl -s "${HEALTH_URL}"
else
    log_warn "Health check failed. Service might still be starting..."
    log_info "Check logs with: ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose logs -f chat-api'"
fi

# =============================================================================
# Summary
# =============================================================================
ADMIN_PORT=$(grep "^ADMIN_PORT=" docker/.env | cut -d'=' -f2 || echo "3003")

echo ""
echo "=============================================="
echo "ATLAS_CHAT_AI Deployment Summary"
echo "=============================================="
echo "Environment: ${ENVIRONMENT}"
echo "VPS: ${VPS_USER}@${VPS_HOST}"
echo "Deploy Dir: ${DEPLOY_DIR}"
echo "Images: ${API_IMAGE}, ${ADMIN_IMAGE}"
echo ""
echo "Useful commands:"
echo "  View logs:    ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose logs -f'"
echo "  Restart:      ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose restart'"
echo "  Stop:         ssh ${VPS_USER}@${VPS_HOST} 'cd ${DEPLOY_DIR} && docker compose down'"
echo ""
echo "Endpoints:"
echo "  API Health: http://${VPS_HOST}:${API_PORT}/api/v1/health"
echo "  API Docs:   http://${VPS_HOST}:${API_PORT}/docs"
echo "  Admin UI:   http://${VPS_HOST}:${ADMIN_PORT}"
echo "=============================================="
