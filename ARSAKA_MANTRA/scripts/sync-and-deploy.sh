#!/bin/bash
# =============================================================================
# Sync & Deploy - Update existing deployment with latest code
# For quick iterations without full migration
# =============================================================================

set -e

SERVER="${1:-72.61.209.224}"
SSH_USER="${SSH_USER:-root}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."

echo "=== Sync & Deploy to $SERVER ==="

# Build images locally or on server?
BUILD_LOCAL="${BUILD_LOCAL:-0}"

if [ "$BUILD_LOCAL" = "1" ]; then
    echo ">>> Building images locally..."
    cd "$PROJECT_ROOT"

    # Build backend
    docker build -t arsaka-mantra-api:latest -f backend/Dockerfile backend/

    # Build frontend
    docker build -t arsaka-mantra-web:latest -f frontend/Dockerfile frontend/

    # Build MCP server
    docker build -t mantra-mcp-server:latest -f mcp-server/Dockerfile mcp-server/

    echo ">>> Saving images..."
    docker save arsaka-mantra-api:latest arsaka-mantra-web:latest mantra-mcp-server:latest | gzip > /tmp/atlas-images.tar.gz

    echo ">>> Transferring images..."
    scp /tmp/atlas-images.tar.gz ${SSH_USER}@${SERVER}:/tmp/

    ssh ${SSH_USER}@${SERVER} "docker load < /tmp/atlas-images.tar.gz && rm /tmp/atlas-images.tar.gz"
else
    echo ">>> Building on server..."

    # Sync source code
    rsync -avz --exclude '.venv' --exclude 'node_modules' --exclude '__pycache__' \
        "$PROJECT_ROOT/backend/" ${SSH_USER}@${SERVER}:/opt/atlas/backend/

    rsync -avz --exclude 'node_modules' --exclude 'dist' \
        "$PROJECT_ROOT/frontend/" ${SSH_USER}@${SERVER}:/opt/atlas/frontend/

    rsync -avz --exclude 'node_modules' --exclude 'dist' \
        "$PROJECT_ROOT/mcp-server/" ${SSH_USER}@${SERVER}:/opt/atlas/mcp-server/

    # Build on server
    ssh ${SSH_USER}@${SERVER} << 'BUILD'
cd /opt/atlas
docker build -t arsaka-mantra-api:latest -f backend/Dockerfile backend/
docker build -t arsaka-mantra-web:latest -f frontend/Dockerfile frontend/
docker build -t mantra-mcp-server:latest -f mcp-server/Dockerfile mcp-server/
BUILD
fi

# Sync and run Nomad jobs
echo ">>> Syncing Nomad jobs..."
scp "$PROJECT_ROOT/nomad/"*.nomad ${SSH_USER}@${SERVER}:/opt/nomad/jobs/

echo ">>> Redeploying..."
ssh ${SSH_USER}@${SERVER} << 'DEPLOY'
cd /opt/nomad/jobs
for job in mantra-backend mantra-frontend mantra-mcp; do
    if [ -f "${job}.nomad" ]; then
        echo "Restarting $job..."
        nomad job run "${job}.nomad"
    fi
done
DEPLOY

echo ""
echo "=== Sync Complete ==="
echo "Check status: ssh $SERVER 'nomad job status'"
