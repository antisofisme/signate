#!/bin/bash

################################################################################
# Nomad + Docker + Consul Stack - Automatic Installation Script
# Version: 1.0.0
# Date: 2026-01-01
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

check_root() {
    if [[ $EUID -ne 0 ]]; then
       log_error "This script must be run as root (use sudo)"
       exit 1
    fi
}

################################################################################
# Main Installation
################################################################################

log_info "Starting Nomad Stack Installation..."
echo ""

# Check root
check_root

# Step 0: Prerequisites
log_info "Step 0: Checking prerequisites..."
apt-get update -qq
apt-get install -y curl wget git vim htop net-tools ca-certificates gnupg lsb-release > /dev/null 2>&1
log_info "✓ Prerequisites installed"
echo ""

# Step 1: Install Docker
log_info "Step 1: Installing Docker..."
if command -v docker &> /dev/null; then
    log_warn "Docker already installed ($(docker --version))"
else
    # Add Docker repository
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt-get update -qq
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1

    # Configure Docker daemon
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json <<'DOCKEREOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true
}
DOCKEREOF

    # Start Docker
    systemctl daemon-reload
    systemctl start docker
    systemctl enable docker > /dev/null 2>&1

    log_info "✓ Docker installed: $(docker --version)"
fi
echo ""

# Step 2: Install HashiCorp Repository
log_info "Step 2: Adding HashiCorp repository..."
if [ ! -f /usr/share/keyrings/hashicorp-archive-keyring.gpg ]; then
    wget -O- https://apt.releases.hashicorp.com/gpg | \
        gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
        https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
        tee /etc/apt/sources.list.d/hashicorp.list

    apt-get update -qq
    log_info "✓ HashiCorp repository added"
else
    log_warn "HashiCorp repository already exists"
fi
echo ""

# Step 3: Install Nomad
log_info "Step 3: Installing Nomad..."
if command -v nomad &> /dev/null; then
    log_warn "Nomad already installed ($(nomad version | head -1))"
else
    apt-get install -y nomad > /dev/null 2>&1

    # Create directories
    mkdir -p /opt/nomad/{data,config}
    mkdir -p /opt/nomad/volumes/{postgres,redis,uploads,logs}

    # Create Nomad configuration
    cat > /etc/nomad.d/nomad.hcl <<'NOMADEOF'
datacenter = "dc1"
data_dir   = "/opt/nomad/data"
bind_addr  = "0.0.0.0"

server {
  enabled          = true
  bootstrap_expect = 1
}

client {
  enabled = true

  host_volume "postgres_data" {
    path      = "/opt/nomad/volumes/postgres"
    read_only = false
  }

  host_volume "redis_data" {
    path      = "/opt/nomad/volumes/redis"
    read_only = false
  }
}

consul {
  address             = "127.0.0.1:8500"
  server_service_name = "nomad-server"
  client_service_name = "nomad-client"
  auto_advertise      = true
  server_auto_join    = true
  client_auto_join    = true
}

plugin "docker" {
  config {
    allow_privileged = false
    volumes {
      enabled = true
    }
  }
}

ui {
  enabled = true
}
NOMADEOF

    # Start Nomad
    systemctl daemon-reload
    systemctl start nomad
    systemctl enable nomad > /dev/null 2>&1

    log_info "✓ Nomad installed: $(nomad version | head -1)"
fi
echo ""

# Step 4: Install Consul
log_info "Step 4: Installing Consul..."
if command -v consul &> /dev/null; then
    log_warn "Consul already installed ($(consul version | head -1))"
else
    apt-get install -y consul > /dev/null 2>&1

    # Create directories
    mkdir -p /opt/consul/{data,config}

    # Create Consul configuration
    cat > /etc/consul.d/consul.hcl <<'CONSULEOF'
datacenter       = "dc1"
data_dir         = "/opt/consul/data"
log_level        = "INFO"
server           = true
bootstrap_expect = 1
bind_addr        = "0.0.0.0"
client_addr      = "0.0.0.0"

ui_config {
  enabled = true
}
CONSULEOF

    # Start Consul
    systemctl daemon-reload
    systemctl start consul
    systemctl enable consul > /dev/null 2>&1

    log_info "✓ Consul installed: $(consul version | head -1)"
fi
echo ""

# Step 5: Verify Installation
log_info "Step 5: Verifying installation..."
sleep 5  # Wait for services to start

# Check Docker
if systemctl is-active --quiet docker; then
    log_info "✓ Docker service: RUNNING"
else
    log_error "✗ Docker service: FAILED"
fi

# Check Nomad
if systemctl is-active --quiet nomad; then
    log_info "✓ Nomad service: RUNNING"
else
    log_error "✗ Nomad service: FAILED"
fi

# Check Consul
if systemctl is-active --quiet consul; then
    log_info "✓ Consul service: RUNNING"
else
    log_error "✗ Consul service: FAILED"
fi

echo ""
log_info "═══════════════════════════════════════════════════"
log_info "Installation Complete!"
log_info "═══════════════════════════════════════════════════"
echo ""
echo "Access the web UIs:"
echo "  - Nomad UI:  http://$(hostname -I | awk '{print $1}'):4646"
echo "  - Consul UI: http://$(hostname -I | awk '{print $1}'):8500"
echo ""
echo "Verify installation:"
echo "  docker --version"
echo "  nomad version"
echo "  consul version"
echo ""
echo "Check service status:"
echo "  systemctl status docker"
echo "  systemctl status nomad"
echo "  systemctl status consul"
echo ""
log_info "Next: Deploy your first job with 'nomad job run <job-file>'"
echo ""
