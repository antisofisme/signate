# Step 2: Install Nomad

> **Install HashiCorp Nomad - Orchestrator untuk manage workloads**

---

## 🎯 Tujuan

Install Nomad yang akan menjadi orchestrator utama untuk scheduling dan managing containers.

---

## 📋 Installation Steps

### Step 1: Add HashiCorp Repository

```bash
# Add HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add HashiCorp repository
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/hashicorp.list

# Update package list
sudo apt-get update
```

---

### Step 2: Install Nomad

```bash
# Install Nomad
sudo apt-get install -y nomad

# Verify installation
nomad version
```

**Expected Output:**
```
Nomad v1.7.3
```

---

### Step 3: Configure Nomad (Single Server Mode)

```bash
# Create Nomad configuration
sudo tee /etc/nomad.d/nomad.hcl > /dev/null <<'EOF'
# Nomad Configuration - Single Server Mode

datacenter = "dc1"
data_dir   = "/opt/nomad/data"
bind_addr  = "0.0.0.0"

# Server configuration
server {
  enabled          = true
  bootstrap_expect = 1
}

# Client configuration
client {
  enabled = true

  # Node metadata
  meta {
    "node_class" = "general"
    "rack"       = "rack1"
  }

  # Host volumes (for persistent data)
  host_volume "postgres_data" {
    path      = "/opt/nomad/volumes/postgres"
    read_only = false
  }

  host_volume "redis_data" {
    path      = "/opt/nomad/volumes/redis"
    read_only = false
  }
}

# Consul configuration (will be configured later)
consul {
  address = "127.0.0.1:8500"

  # Service registration
  server_service_name = "nomad-server"
  client_service_name = "nomad-client"
  auto_advertise      = true

  # Server auto-join
  server_auto_join = true
  client_auto_join = true
}

# Enable Docker driver
plugin "docker" {
  config {
    allow_privileged = false
    allow_caps       = ["CHOWN", "NET_RAW"]

    volumes {
      enabled = true
    }

    gc {
      image       = true
      image_delay = "3m"
      container   = true
    }
  }
}

# Telemetry (optional)
telemetry {
  collection_interval        = "1s"
  disable_hostname           = false
  prometheus_metrics         = true
  publish_allocation_metrics = true
  publish_node_metrics       = true
}

# ACL (Access Control - disable for now, enable in production)
acl {
  enabled = false
}

# UI Configuration
ui {
  enabled = true

  consul {
    ui_url = "http://localhost:8500/ui"
  }
}

EOF
```

---

### Step 4: Create Host Volumes

```bash
# Create volume directories
sudo mkdir -p /opt/nomad/volumes/{postgres,redis,uploads,logs}

# Set permissions
sudo chmod -R 755 /opt/nomad/volumes

# Verify
ls -la /opt/nomad/volumes/
```

---

### Step 5: Configure Nomad as Systemd Service

```bash
# Verify systemd service exists
sudo systemctl cat nomad.service

# If service file doesn't exist, create it:
sudo tee /etc/systemd/system/nomad.service > /dev/null <<'EOF'
[Unit]
Description=Nomad
Documentation=https://www.nomadproject.io/docs/
Wants=network-online.target
After=network-online.target

[Service]
Type=notify
ExecReload=/bin/kill -HUP $MAINPID
ExecStart=/usr/bin/nomad agent -config=/etc/nomad.d
KillMode=process
KillSignal=SIGINT
LimitNOFILE=infinity
LimitNPROC=infinity
Restart=on-failure
RestartSec=2
StartLimitBurst=3
TasksMax=infinity

[Install]
WantedBy=multi-user.target
EOF
```

---

### Step 6: Start Nomad Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start Nomad
sudo systemctl start nomad

# Enable on boot
sudo systemctl enable nomad

# Check status
sudo systemctl status nomad
```

**Expected Output:**
```
● nomad.service - Nomad
     Loaded: loaded (/etc/systemd/system/nomad.service; enabled)
     Active: active (running) since Thu 2026-01-01 06:00:00 UTC
```

---

### Step 7: Verify Nomad Installation

```bash
# Check Nomad server status
nomad server members

# Check Nomad node status
nomad node status

# Check agent info
nomad agent-info

# Access Nomad UI (from browser)
# http://YOUR_SERVER_IP:4646
```

**Expected Output:**
```
Name             Address    Port  Status  Leader  Protocol  Build  Datacenter  Region
nomad-server.dc1  127.0.0.1  4648  alive   true    2         1.7.3  dc1         global
```

---

### Step 8: Configure Nomad CLI Autocomplete

```bash
# Install autocomplete
nomad -autocomplete-install

# Reload shell
source ~/.bashrc

# Test autocomplete
nomad job <TAB><TAB>
```

---

### Step 9: Create Example Namespace (Optional)

```bash
# Create namespaces for different environments
nomad namespace apply -description "Production workloads" production
nomad namespace apply -description "Staging workloads" staging
nomad namespace apply -description "Development workloads" development

# List namespaces
nomad namespace list
```

---

## 🔧 Nomad Configuration Files

### Important Files & Directories:

| Path | Purpose |
|------|---------|
| /etc/nomad.d/nomad.hcl | Main configuration file |
| /opt/nomad/data/ | Nomad data directory |
| /opt/nomad/volumes/ | Host volumes for containers |
| /var/log/nomad.log | Nomad logs (if configured) |

---

## 📊 Nomad CLI Commands

### Basic Commands:

```bash
# Server commands
nomad server members          # List server members
nomad server force-leave <node>  # Remove dead server

# Node commands
nomad node status             # List all nodes
nomad node status <node-id>   # Detailed node info
nomad node drain <node-id>    # Drain node for maintenance

# Job commands
nomad job run <file.nomad>    # Submit a job
nomad job status              # List all jobs
nomad job status <job-id>     # Detailed job info
nomad job stop <job-id>       # Stop a job
nomad job logs <alloc-id>     # View job logs

# Allocation commands
nomad alloc status <alloc-id> # Allocation details
nomad alloc logs <alloc-id>   # Allocation logs
nomad alloc restart <alloc-id> # Restart allocation

# System commands
nomad system gc               # Garbage collect
nomad system reconcile summary # Reconcile state
```

---

## 🎯 Nomad UI Features

Access Nomad UI at: `http://YOUR_SERVER_IP:4646`

Features available:
- **Jobs**: View, stop, start jobs
- **Allocations**: Monitor running containers
- **Nodes**: View cluster nodes
- **Topology**: Visual cluster layout
- **Evaluations**: Job placement decisions
- **CSI Volumes**: Storage volumes

---

## ✅ Nomad Installation Complete!

Nomad sudah terinstall dan running dalam mode server + client.

**Next Step**: [03-install-consul.md](03-install-consul.md)

---

## 🆘 Troubleshooting

### Issue: Nomad won't start

```bash
# Check logs
sudo journalctl -u nomad -n 50 --no-pager

# Validate config
nomad config validate /etc/nomad.d/nomad.hcl

# Check if port 4646 is available
sudo netstat -tulpn | grep 4646
```

### Issue: Cannot connect to Nomad

```bash
# Check if service is running
sudo systemctl status nomad

# Check firewall
sudo ufw status | grep 4646

# Allow Nomad ports
sudo ufw allow 4646/tcp
sudo ufw allow 4647/tcp
sudo ufw allow 4648/tcp
```

### Issue: Docker driver not available

```bash
# Verify Docker is running
docker ps

# Check Nomad node status
nomad node status

# Restart Nomad
sudo systemctl restart nomad
```

### Issue: Node shows as "initializing"

```bash
# Wait a few seconds, then check again
nomad node status

# If still initializing, check logs
sudo journalctl -u nomad -f
```

---

**Last Updated**: 2026-01-01
