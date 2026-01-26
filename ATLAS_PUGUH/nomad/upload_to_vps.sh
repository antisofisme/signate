#!/bin/bash
# ============================================================================
# ATLAS_PUGUH Phase A - VPS Upload Script
# ============================================================================
# Purpose: Upload backend code and Nomad files to VPS
# Usage: ./upload_to_vps.sh [vps-ip] [vps-user]
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VPS_IP="${1:-31.97.111.175}"
VPS_USER="${2:-root}"
VPS_DEST="/root/atlas-puguh"

# Source directories (relative to script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
NOMAD_DIR="$PROJECT_ROOT/nomad"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."

    # Check if scp command exists
    if ! command -v scp &> /dev/null; then
        log_error "scp not found. Please install OpenSSH client."
        exit 1
    fi

    # Check if backend directory exists
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        exit 1
    fi

    # Check if nomad directory exists
    if [ ! -d "$NOMAD_DIR" ]; then
        log_error "Nomad directory not found: $NOMAD_DIR"
        exit 1
    fi

    log_info "Prerequisites OK"
}

# Test SSH connection
test_ssh_connection() {
    log_step "Testing SSH connection to VPS..."

    if ssh -o ConnectTimeout=5 -o BatchMode=yes "${VPS_USER}@${VPS_IP}" exit 2>/dev/null; then
        log_info "SSH connection successful"
    else
        log_warn "SSH connection failed (may need password)"
        log_warn "Please ensure you have SSH access to ${VPS_USER}@${VPS_IP}"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Create remote directories
create_remote_directories() {
    log_step "Creating remote directories..."

    ssh "${VPS_USER}@${VPS_IP}" << 'EOF'
mkdir -p /root/atlas-puguh/backend
mkdir -p /root/atlas-puguh/nomad
mkdir -p /opt/nomad/volumes/puguh/postgres
chown -R nomad:nomad /opt/nomad/volumes/puguh 2>/dev/null || true
EOF

    log_info "Remote directories created"
}

# Upload backend code
upload_backend() {
    log_step "Uploading backend code..."

    # Upload core application files
    scp -r "${BACKEND_DIR}/core" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"
    scp -r "${BACKEND_DIR}/shared" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"
    scp -r "${BACKEND_DIR}/migrations" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"

    # Upload configuration files
    scp "${BACKEND_DIR}/.env.example" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"
    scp "${BACKEND_DIR}/requirements-phase-a.txt" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"
    scp "${BACKEND_DIR}/Dockerfile" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"
    scp "${BACKEND_DIR}/README.md" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/backend/"

    log_info "Backend code uploaded"
}

# Upload Nomad files
upload_nomad_files() {
    log_step "Uploading Nomad job files..."

    scp "${NOMAD_DIR}/postgres.nomad" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/nomad/"
    scp "${NOMAD_DIR}/backend-api.nomad" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/nomad/"
    scp "${NOMAD_DIR}/deploy.sh" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/nomad/"
    scp "${NOMAD_DIR}/README.md" "${VPS_USER}@${VPS_IP}:${VPS_DEST}/nomad/"

    # Make deploy.sh executable
    ssh "${VPS_USER}@${VPS_IP}" "chmod +x ${VPS_DEST}/nomad/deploy.sh"

    log_info "Nomad files uploaded"
}

# Display next steps
display_next_steps() {
    echo ""
    echo -e "${GREEN}✅ Upload Complete!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo ""
    echo "1. SSH to VPS:"
    echo -e "   ${BLUE}ssh ${VPS_USER}@${VPS_IP}${NC}"
    echo ""
    echo "2. Configure environment:"
    echo -e "   ${BLUE}cd ${VPS_DEST}/backend${NC}"
    echo -e "   ${BLUE}cp .env.example .env${NC}"
    echo -e "   ${BLUE}nano .env${NC}  # Update passwords and secrets"
    echo ""
    echo "3. Update Nomad job files with passwords:"
    echo -e "   ${BLUE}cd ${VPS_DEST}/nomad${NC}"
    echo -e "   ${BLUE}nano postgres.nomad${NC}  # Update POSTGRES_PASSWORD"
    echo -e "   ${BLUE}nano backend-api.nomad${NC}  # Update DATABASE_URL and JWT_SECRET_KEY"
    echo ""
    echo "4. Deploy to Nomad:"
    echo -e "   ${BLUE}./deploy.sh all${NC}"
    echo ""
    echo "5. Run database migrations:"
    echo -e "   ${BLUE}docker ps | grep postgres${NC}  # Get container ID"
    echo -e "   ${BLUE}docker exec -i <container-id> psql -U atlas_user -d atlas_puguh < ${VPS_DEST}/backend/migrations/001_initial_schema.sql${NC}"
    echo -e "   ${BLUE}docker exec -i <container-id> psql -U atlas_user -d atlas_puguh < ${VPS_DEST}/backend/migrations/002_immutability_triggers.sql${NC}"
    echo -e "   ${BLUE}docker exec -i <container-id> psql -U atlas_user -d atlas_puguh < ${VPS_DEST}/backend/migrations/003_rls_policies.sql${NC}"
    echo -e "   ${BLUE}docker exec -i <container-id> psql -U atlas_user -d atlas_puguh < ${VPS_DEST}/backend/migrations/seed_phase_a.sql${NC}"
    echo ""
    echo "6. Verify deployment:"
    echo -e "   ${BLUE}./deploy.sh status${NC}"
    echo -e "   ${BLUE}curl http://127.0.0.1:8001/health${NC}"
    echo ""
    echo -e "${YELLOW}📖 Full Deployment Guide:${NC}"
    echo -e "   See ${PROJECT_ROOT}/NOMAD_QUICKSTART.md"
    echo ""
}

# Main script
main() {
    echo ""
    echo "============================================================================"
    echo "  ATLAS_PUGUH Phase A - VPS Upload"
    echo "============================================================================"
    echo ""
    echo "Target VPS: ${VPS_USER}@${VPS_IP}"
    echo "Destination: ${VPS_DEST}"
    echo ""

    # Confirm upload
    read -p "Continue with upload? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Upload cancelled"
        exit 0
    fi

    # Execute upload steps
    check_prerequisites
    test_ssh_connection
    create_remote_directories
    upload_backend
    upload_nomad_files
    display_next_steps
}

# Run main function
main

# ============================================================================
# USAGE EXAMPLES
# ============================================================================
#
# Default (31.97.111.175, root user):
#   ./upload_to_vps.sh
#
# Custom IP:
#   ./upload_to_vps.sh 192.168.1.100
#
# Custom IP and user:
#   ./upload_to_vps.sh 192.168.1.100 ubuntu
#
# ============================================================================
