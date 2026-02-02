#!/bin/bash
# =============================================================================
# ATLAS Quick Deploy - For new VPS with no existing data
# Fastest possible deployment from scratch
# =============================================================================

set -e

SERVER="${1:-}"
SSH_USER="${SSH_USER:-root}"

if [ -z "$SERVER" ]; then
    echo "Usage: $0 <server-ip>"
    echo "Example: $0 72.61.209.224"
    exit 1
fi

echo "=== Quick Deploy to $SERVER ==="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOMAD_DIR="${SCRIPT_DIR}/../nomad"

# Step 1: Install everything on server
echo ">>> Installing Docker + Nomad..."
ssh ${SSH_USER}@${SERVER} << 'INSTALL'
set -e
apt-get update -qq

# Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
fi

# Nomad + Consul
if ! command -v nomad &> /dev/null; then
    wget -qO- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list
    apt-get update -qq && apt-get install -y nomad consul
fi

# Directories
mkdir -p /opt/nomad/jobs /opt/volumes/{postgres,mantra_postgres,qdrant,meilisearch,redis}
chmod 777 /opt/volumes/*

# Nomad config
cat > /etc/nomad.d/nomad.hcl << 'EOF'
data_dir = "/opt/nomad/data"
bind_addr = "0.0.0.0"

server {
  enabled = true
  bootstrap_expect = 1
}

client {
  enabled = true
  host_volume "postgres_data" { path = "/opt/volumes/postgres" read_only = false }
  host_volume "mantra_postgres_data" { path = "/opt/volumes/mantra_postgres" read_only = false }
  host_volume "qdrant_data" { path = "/opt/volumes/qdrant" read_only = false }
  host_volume "meilisearch_data" { path = "/opt/volumes/meilisearch" read_only = false }
  host_volume "redis_data" { path = "/opt/volumes/redis" read_only = false }
}

plugin "docker" {
  config {
    allow_privileged = true
    volumes { enabled = true }
  }
}
EOF

systemctl enable nomad consul docker
systemctl restart consul nomad

# Wait for Nomad
sleep 5
nomad status 2>/dev/null || echo "Nomad starting..."
INSTALL

# Step 2: Upload Nomad jobs
echo ">>> Uploading Nomad jobs..."
scp "$NOMAD_DIR"/*.nomad ${SSH_USER}@${SERVER}:/opt/nomad/jobs/

# Step 3: Set secrets
echo ">>> Setting secrets..."
ssh ${SSH_USER}@${SERVER} << 'SECRETS'
# Set default secrets in Consul KV
consul kv put mantra/db_password "$(openssl rand -base64 16)"
consul kv put puguh/db_password "$(openssl rand -base64 16)"
consul kv put meilisearch/master_key "$(openssl rand -base64 32)"
consul kv put rabbitmq/password "$(openssl rand -base64 16)"
SECRETS

# Step 4: Deploy all jobs
echo ">>> Deploying services..."
ssh ${SSH_USER}@${SERVER} << 'DEPLOY'
cd /opt/nomad/jobs
nomad namespace apply -description "MANTRA" mantra 2>/dev/null || true

# Infrastructure first
for job in mantra-postgres mantra-redis; do
    [ -f "${job}.nomad" ] && nomad job run "${job}.nomad"
done
sleep 10

# Optional services
for job in mantra-qdrant-meilisearch mantra-rabbitmq; do
    [ -f "${job}.nomad" ] && nomad job run "${job}.nomad" 2>/dev/null || true
done
sleep 5

# Applications
for job in mantra-backend mantra-frontend; do
    [ -f "${job}.nomad" ] && nomad job run "${job}.nomad"
done

echo ""
echo "=== Deployment Status ==="
nomad job status
DEPLOY

echo ""
echo "=== Quick Deploy Complete ==="
echo "Server: $SERVER"
echo ""
echo "Services:"
echo "  - Backend:  http://$SERVER:8001"
echo "  - Frontend: http://$SERVER:3001"
echo "  - Nomad UI: http://$SERVER:4646"
