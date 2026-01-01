# Step 3: Install Consul

> **Install HashiCorp Consul - Service discovery & health checking**

---

## 🎯 Tujuan

Install Consul untuk service discovery, health checking, dan service mesh.

---

## 📋 Installation Steps

### Step 1: Install Consul

```bash
# Consul should be available from HashiCorp repo (added in Step 2)
sudo apt-get install -y consul

# Verify installation
consul version
```

**Expected Output:**
```
Consul v1.17.0
```

---

### Step 2: Configure Consul (Single Server Mode)

```bash
# Create Consul configuration
sudo tee /etc/consul.d/consul.hcl > /dev/null <<'CONSULEOF'
# Consul Configuration - Single Server Mode

datacenter = "dc1"
data_dir   = "/opt/consul/data"
log_level  = "INFO"

# Server configuration
server = true
bootstrap_expect = 1

# Bind addresses
bind_addr   = "0.0.0.0"
client_addr = "0.0.0.0"

# UI
ui_config {
  enabled = true
}

# Service registration
services {
  name = "consul"
  port = 8300
}

# Telemetry
telemetry {
  prometheus_retention_time = "60s"
  disable_hostname = false
}

# Performance tuning
performance {
  raft_multiplier = 1
}

# Autopilot
autopilot {
  cleanup_dead_servers = true
  last_contact_threshold = "200ms"
  max_trailing_logs = 250
  server_stabilization_time = "10s"
}
CONSULEOF
```

---

### Step 3: Start Consul Service

```bash
# Start Consul
sudo systemctl start consul

# Enable on boot
sudo systemctl enable consul

# Check status
sudo systemctl status consul
```

---

### Step 4: Verify Consul

```bash
# Check members
consul members

# Check catalog
consul catalog services

# Access Consul UI
# http://YOUR_SERVER_IP:8500
```

**Expected Output:**
```
Node          Address         Status  Type    Build   Protocol  DC   Partition  Segment
nomad-server  127.0.0.1:8301  alive   server  1.17.0  2         dc1  default    <all>
```

---

## ✅ Consul Installation Complete!

**Next Step**: [04-configure-nomad.md](04-configure-nomad.md)

---

**Last Updated**: 2026-01-01
