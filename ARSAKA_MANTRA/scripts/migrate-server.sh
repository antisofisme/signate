#!/bin/bash
# =============================================================================
# ATLAS Server Migration Script
# One-command migration between VPS instances
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[MIGRATE]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =============================================================================
# CONFIGURATION
# =============================================================================

OLD_SERVER="${OLD_SERVER:-31.97.111.175}"
NEW_SERVER="${NEW_SERVER:-72.61.209.224}"
SSH_USER="${SSH_USER:-root}"
BACKUP_DIR="/tmp/atlas-migration-$(date +%Y%m%d-%H%M%S)"

# Services to migrate
POSTGRES_CONTAINER="postgresql"  # Pattern match
BACKUP_FILE="atlas-backup.tar.gz"

# =============================================================================
# USAGE
# =============================================================================

usage() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
  backup      Backup data from old server
  setup       Setup new server (install Nomad, Docker)
  transfer    Transfer backup to new server
  restore     Restore data on new server
  deploy      Deploy all Nomad jobs
  full        Run complete migration (all steps)

Options:
  --old-server IP    Source server (default: $OLD_SERVER)
  --new-server IP    Target server (default: $NEW_SERVER)
  --skip-setup       Skip new server setup (if already done)

Examples:
  $0 full --old-server 31.97.111.175 --new-server 72.61.209.224
  $0 backup && $0 transfer && $0 restore
  NEW_SERVER=1.2.3.4 $0 deploy
EOF
}

# =============================================================================
# STEP 1: BACKUP FROM OLD SERVER
# =============================================================================

backup_old_server() {
    log "Creating backup from $OLD_SERVER..."

    ssh ${SSH_USER}@${OLD_SERVER} << 'REMOTE_BACKUP'
set -e
BACKUP_DIR="/tmp/atlas-backup"
rm -rf $BACKUP_DIR && mkdir -p $BACKUP_DIR

echo ">>> Dumping PostgreSQL databases..."
# Find postgres containers and dump
for container in $(docker ps --format '{{.Names}}' | grep -i postgres); do
    DB_NAME=$(docker exec $container psql -U postgres -t -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname != 'postgres';" 2>/dev/null | tr -d ' ' | head -1)
    if [ -n "$DB_NAME" ]; then
        echo "Dumping $container -> $DB_NAME"
        docker exec $container pg_dump -U postgres $DB_NAME > $BACKUP_DIR/${container}_${DB_NAME}.sql 2>/dev/null || \
        docker exec $container pg_dump -U mantra_owner -d arsaka_mantra > $BACKUP_DIR/${container}.sql 2>/dev/null || true
    fi
done

echo ">>> Exporting Docker volumes..."
for vol in $(docker volume ls -q | grep -v "^[0-9a-f]\{64\}$"); do
    echo "Exporting volume: $vol"
    docker run --rm -v $vol:/data -v $BACKUP_DIR:/backup alpine \
        tar czf /backup/vol_${vol}.tar.gz -C /data . 2>/dev/null || true
done

echo ">>> Saving Consul KV (secrets)..."
consul kv export > $BACKUP_DIR/consul-kv.json 2>/dev/null || echo "{}" > $BACKUP_DIR/consul-kv.json

echo ">>> Copying Nomad jobs..."
cp -r /opt/nomad/jobs $BACKUP_DIR/nomad-jobs 2>/dev/null || mkdir -p $BACKUP_DIR/nomad-jobs

echo ">>> Creating archive..."
cd /tmp && tar czf atlas-backup.tar.gz atlas-backup/
ls -lh /tmp/atlas-backup.tar.gz
REMOTE_BACKUP

    log "Downloading backup..."
    mkdir -p "$BACKUP_DIR"
    scp ${SSH_USER}@${OLD_SERVER}:/tmp/atlas-backup.tar.gz "$BACKUP_DIR/"

    log "Backup saved to: $BACKUP_DIR/atlas-backup.tar.gz"
}

# =============================================================================
# STEP 2: SETUP NEW SERVER
# =============================================================================

setup_new_server() {
    log "Setting up new server $NEW_SERVER..."

    ssh ${SSH_USER}@${NEW_SERVER} << 'REMOTE_SETUP'
set -e

echo ">>> Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

echo ">>> Installing Nomad..."
if ! command -v nomad &> /dev/null; then
    curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
    apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    apt-get update && apt-get install -y nomad consul
fi

echo ">>> Creating directories..."
mkdir -p /opt/nomad/jobs /opt/volumes /opt/atlas

echo ">>> Configuring Nomad..."
cat > /etc/nomad.d/nomad.hcl << 'NOMAD_CONFIG'
data_dir = "/opt/nomad/data"
bind_addr = "0.0.0.0"

server {
  enabled = true
  bootstrap_expect = 1
}

client {
  enabled = true

  host_volume "postgres_data" {
    path = "/opt/volumes/postgres"
    read_only = false
  }

  host_volume "mantra_postgres_data" {
    path = "/opt/volumes/mantra_postgres"
    read_only = false
  }

  host_volume "qdrant_data" {
    path = "/opt/volumes/qdrant"
    read_only = false
  }

  host_volume "meilisearch_data" {
    path = "/opt/volumes/meilisearch"
    read_only = false
  }

  host_volume "redis_data" {
    path = "/opt/volumes/redis"
    read_only = false
  }
}

plugin "docker" {
  config {
    allow_privileged = true
    volumes {
      enabled = true
    }
  }
}
NOMAD_CONFIG

echo ">>> Creating volume directories..."
mkdir -p /opt/volumes/{postgres,mantra_postgres,qdrant,meilisearch,redis}
chmod 777 /opt/volumes/*

echo ">>> Starting services..."
systemctl enable nomad consul
systemctl restart consul nomad

sleep 5
nomad status || echo "Nomad starting..."
REMOTE_SETUP

    log "New server setup complete"
}

# =============================================================================
# STEP 3: TRANSFER BACKUP
# =============================================================================

transfer_backup() {
    log "Transferring backup to $NEW_SERVER..."

    if [ ! -f "$BACKUP_DIR/atlas-backup.tar.gz" ]; then
        error "Backup file not found. Run 'backup' first."
    fi

    scp "$BACKUP_DIR/atlas-backup.tar.gz" ${SSH_USER}@${NEW_SERVER}:/tmp/

    log "Transfer complete"
}

# =============================================================================
# STEP 4: RESTORE ON NEW SERVER
# =============================================================================

restore_new_server() {
    log "Restoring data on $NEW_SERVER..."

    ssh ${SSH_USER}@${NEW_SERVER} << 'REMOTE_RESTORE'
set -e
cd /tmp
tar xzf atlas-backup.tar.gz

echo ">>> Restoring volumes..."
for vol_archive in atlas-backup/vol_*.tar.gz; do
    vol_name=$(basename $vol_archive | sed 's/vol_\(.*\)\.tar\.gz/\1/')
    echo "Restoring volume: $vol_name"

    # Create Docker volume if not exists
    docker volume create $vol_name 2>/dev/null || true

    # Extract to volume
    docker run --rm -v $vol_name:/data -v /tmp/atlas-backup:/backup alpine \
        tar xzf /backup/vol_${vol_name}.tar.gz -C /data 2>/dev/null || true
done

echo ">>> Restoring Consul KV..."
if [ -f atlas-backup/consul-kv.json ] && [ -s atlas-backup/consul-kv.json ]; then
    consul kv import @atlas-backup/consul-kv.json 2>/dev/null || echo "KV import skipped"
fi

echo ">>> Copying Nomad jobs..."
cp -r atlas-backup/nomad-jobs/* /opt/nomad/jobs/ 2>/dev/null || true

echo ">>> Cleanup..."
rm -rf /tmp/atlas-backup /tmp/atlas-backup.tar.gz

echo ">>> Restore complete!"
REMOTE_RESTORE

    log "Restore complete"
}

# =============================================================================
# STEP 5: DEPLOY NOMAD JOBS
# =============================================================================

deploy_jobs() {
    log "Deploying Nomad jobs on $NEW_SERVER..."

    # First, copy latest job files from local
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    NOMAD_DIR="${SCRIPT_DIR}/../nomad"

    if [ -d "$NOMAD_DIR" ]; then
        log "Uploading latest Nomad job files..."
        scp "$NOMAD_DIR"/*.nomad ${SSH_USER}@${NEW_SERVER}:/opt/nomad/jobs/
    fi

    ssh ${SSH_USER}@${NEW_SERVER} << 'REMOTE_DEPLOY'
set -e
cd /opt/nomad/jobs

# Create namespace
nomad namespace apply -description "MANTRA namespace" mantra 2>/dev/null || true

echo ">>> Deploying infrastructure..."
for job in mantra-postgres mantra-redis mantra-qdrant mantra-meilisearch; do
    if [ -f "${job}.nomad" ]; then
        echo "Deploying $job..."
        nomad job run "${job}.nomad" || true
    fi
done

sleep 10  # Wait for infra

echo ">>> Deploying applications..."
for job in mantra-backend mantra-frontend mantra-mcp; do
    if [ -f "${job}.nomad" ]; then
        echo "Deploying $job..."
        nomad job run "${job}.nomad" || true
    fi
done

echo ">>> Deployment status:"
nomad job status
REMOTE_DEPLOY

    log "Deployment complete"
}

# =============================================================================
# STEP 6: RESTORE POSTGRESQL DATA
# =============================================================================

restore_postgres() {
    log "Restoring PostgreSQL data..."

    ssh ${SSH_USER}@${NEW_SERVER} << 'REMOTE_PG'
set -e

# Wait for postgres to be ready
echo "Waiting for PostgreSQL..."
sleep 10

# Find postgres container
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i postgres | head -1)

if [ -n "$PG_CONTAINER" ]; then
    for sql_file in /tmp/atlas-backup/*.sql; do
        if [ -f "$sql_file" ]; then
            echo "Restoring: $sql_file"
            docker cp "$sql_file" $PG_CONTAINER:/tmp/
            docker exec $PG_CONTAINER psql -U mantra_owner -d arsaka_mantra -f "/tmp/$(basename $sql_file)" 2>/dev/null || \
            docker exec $PG_CONTAINER psql -U postgres -f "/tmp/$(basename $sql_file)" 2>/dev/null || true
        fi
    done
fi

echo "PostgreSQL restore complete"
REMOTE_PG
}

# =============================================================================
# FULL MIGRATION
# =============================================================================

full_migration() {
    log "Starting full migration: $OLD_SERVER -> $NEW_SERVER"
    echo ""

    backup_old_server
    setup_new_server
    transfer_backup
    restore_new_server
    deploy_jobs
    restore_postgres

    echo ""
    log "=========================================="
    log "Migration complete!"
    log "New server: $NEW_SERVER"
    log "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Update DNS to point to $NEW_SERVER"
    echo "2. Test all services"
    echo "3. (Optional) Stop old server"
}

# =============================================================================
# MAIN
# =============================================================================

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --old-server) OLD_SERVER="$2"; shift 2;;
        --new-server) NEW_SERVER="$2"; shift 2;;
        --skip-setup) SKIP_SETUP=1; shift;;
        backup|setup|transfer|restore|deploy|full|restore-pg)
            COMMAND="$1"; shift;;
        -h|--help) usage; exit 0;;
        *) error "Unknown option: $1";;
    esac
done

case "${COMMAND:-}" in
    backup)     backup_old_server;;
    setup)      setup_new_server;;
    transfer)   transfer_backup;;
    restore)    restore_new_server;;
    deploy)     deploy_jobs;;
    restore-pg) restore_postgres;;
    full)       full_migration;;
    *)          usage; exit 1;;
esac
