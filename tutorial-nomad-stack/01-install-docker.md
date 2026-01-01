# Step 1: Install Docker Engine

> **Install Docker sebagai container runtime untuk Nomad**

---

## 🎯 Tujuan

Install Docker Engine yang akan digunakan oleh Nomad untuk menjalankan containerized workloads.

---

## 📋 Installation Steps

### Step 1: Remove Old Docker Versions (if any)

```bash
# Remove old versions
sudo apt-get remove -y \
    docker \
    docker-engine \
    docker.io \
    containerd \
    runc

# Verify removal
docker --version 2>/dev/null && echo "Docker still installed" || echo "No old Docker found"
```

---

### Step 2: Install Docker Repository

```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list
sudo apt-get update
```

---

### Step 3: Install Docker Engine

```bash
# Install Docker packages
sudo apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**Expected Output:**
```
Docker version 27.4.1, build b9d17ea
Docker Compose version v2.32.3
```

---

### Step 4: Configure Docker Daemon

```bash
# Create Docker daemon configuration
sudo mkdir -p /etc/docker

sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false,
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ]
}
EOF

# Verify config
cat /etc/docker/daemon.json
```

**Configuration Explanation:**
- `log-driver`: Use JSON file logging
- `max-size`: Limit log file size to 10MB
- `max-file`: Keep max 3 log files
- `storage-driver`: Use overlay2 (recommended)
- `live-restore`: Keep containers running during Docker daemon restart
- `userland-proxy`: Disable for better performance

---

### Step 5: Start Docker Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start Docker
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

**Expected Output:**
```
● docker.service - Docker Application Container Engine
     Loaded: loaded (/lib/systemd/system/docker.service; enabled)
     Active: active (running) since Thu 2026-01-01 05:30:00 UTC
```

---

### Step 6: Configure User Permissions (Optional)

```bash
# Add current user to docker group (untuk run docker tanpa sudo)
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Test docker without sudo
docker ps
```

**Note**: Logout dan login lagi agar group membership effective.

---

### Step 7: Test Docker Installation

```bash
# Run hello-world container
docker run hello-world

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List images
docker images

# Check Docker system info
docker system info
```

**Expected Output from hello-world:**
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

---

### Step 8: Install Docker Utilities

```bash
# Install docker-clean (cleanup tool)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v /etc:/etc spotify/docker-gc

# Install ctop (container monitoring)
sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 \
    -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop

# Test ctop
ctop --help
```

---

### Step 9: Configure Docker Networking

```bash
# Create custom bridge network for Nomad services
docker network create \
    --driver bridge \
    --subnet 172.20.0.0/16 \
    --opt com.docker.network.bridge.name=nomad0 \
    nomad-net

# List networks
docker network ls

# Inspect nomad-net
docker network inspect nomad-net
```

---

### Step 10: Verification

Run this verification script:

```bash
#!/bin/bash

echo "=== Docker Verification ==="
echo ""

# Version check
echo "✓ Docker Version:"
docker --version
docker compose version
echo ""

# Service status
echo "✓ Docker Service:"
sudo systemctl is-active docker
echo ""

# Test container
echo "✓ Running test container..."
docker run --rm alpine echo "Docker is working!" 2>/dev/null && echo "  Container test: PASSED" || echo "  Container test: FAILED"
echo ""

# Network check
echo "✓ Networks:"
docker network ls
echo ""

# Storage info
echo "✓ Storage Driver:"
docker info | grep "Storage Driver"
echo ""

# Resource usage
echo "✓ Docker Disk Usage:"
docker system df
echo ""

echo "=== Verification Complete ==="
```

Save as `verify-docker.sh` and run:
```bash
chmod +x verify-docker.sh
./verify-docker.sh
```

---

## 🔧 Docker Configuration Files

### Location of Important Files:

| File | Purpose | Location |
|------|---------|----------|
| daemon.json | Docker daemon config | /etc/docker/daemon.json |
| docker.service | Systemd service file | /lib/systemd/system/docker.service |
| docker.socket | Docker socket | /var/run/docker.sock |
| containers | Container data | /var/lib/docker/containers/ |
| images | Image layers | /var/lib/docker/overlay2/ |

---

## 📊 Docker Monitoring Commands

```bash
# Real-time container stats
docker stats

# System-wide info
docker system info

# Disk usage
docker system df

# Container processes
ctop

# View logs
docker logs <container_name>

# Follow logs
docker logs -f <container_name>
```

---

## 🧹 Docker Maintenance

### Cleanup Commands:

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Clean everything (CAREFUL!)
docker system prune -a --volumes -f
```

---

## ✅ Docker Installation Complete!

Docker sudah terinstall dan siap digunakan oleh Nomad.

**Next Step**: [02-install-nomad.md](02-install-nomad.md)

---

## 🆘 Troubleshooting

### Issue: Docker service won't start

```bash
# Check logs
sudo journalctl -u docker -n 50 --no-pager

# Check daemon config syntax
sudo dockerd --validate

# Reset Docker
sudo systemctl reset-failed docker
sudo systemctl start docker
```

### Issue: Permission denied when running docker

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, or run:
newgrp docker
```

### Issue: Docker uses too much disk space

```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a -f

# Configure log rotation (already done in daemon.json)
sudo systemctl restart docker
```

### Issue: Containers cannot access internet

```bash
# Check Docker network
docker network ls

# Restart Docker
sudo systemctl restart docker

# Check iptables
sudo iptables -L -n

# Reset Docker network
sudo systemctl restart docker
```

---

**Last Updated**: 2026-01-01
