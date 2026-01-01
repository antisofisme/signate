# Step 0: Prerequisites & System Preparation

> **Persiapan server sebelum instalasi Nomad stack**

---

## 🎯 Tujuan

Memastikan server memenuhi requirements dan siap untuk instalasi.

---

## ✅ Checklist Requirements

### Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 2 GB | 4 GB | 8+ GB |
| **Disk** | 20 GB | 50 GB | 100+ GB |
| **Network** | 100 Mbps | 1 Gbps | 1 Gbps+ |

### Software Requirements

- **OS**: Ubuntu 24.04 LTS atau 22.04 LTS
- **Kernel**: Linux 5.x atau lebih baru
- **Access**: Root atau sudo privileges

---

## 📋 Step-by-Step

### Step 1: Check System Information

```bash
# Check OS version
lsb_release -a

# Check kernel version
uname -r

# Check CPU
nproc
lscpu | grep "Model name"

# Check RAM
free -h

# Check disk space
df -h

# Check network
ip addr show
```

**Expected Output:**
```
Distributor ID: Ubuntu
Description:    Ubuntu 24.04 LTS
Release:        24.04
Codename:       noble
```

---

### Step 2: Update System Packages

```bash
# Update package list
sudo apt-get update

# Upgrade installed packages
sudo apt-get upgrade -y

# Install essential tools
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    ca-certificates \
    gnupg \
    lsb-release
```

---

### Step 3: Configure Firewall (UFW)

```bash
# Install UFW if not installed
sudo apt-get install -y ufw

# Allow SSH (IMPORTANT - jangan lupa!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow Nomad UI (optional - bisa dinonaktifkan untuk production)
sudo ufw allow 4646/tcp comment 'Nomad UI'

# Allow Consul UI (optional)
sudo ufw allow 8500/tcp comment 'Consul UI'

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status verbose
```

**Expected Output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere        # SSH
80/tcp                     ALLOW       Anywhere        # HTTP
443/tcp                    ALLOW       Anywhere        # HTTPS
4646/tcp                   ALLOW       Anywhere        # Nomad UI
8500/tcp                   ALLOW       Anywhere        # Consul UI
```

---

### Step 4: Configure System Limits

```bash
# Increase file descriptor limits
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF

# Apply limits for current session
ulimit -n 65536
ulimit -u 32768

# Verify
ulimit -n
ulimit -u
```

---

### Step 5: Disable Swap (Optional, tapi recommended)

```bash
# Check current swap
free -h

# Disable swap
sudo swapoff -a

# Remove swap from /etc/fstab
sudo sed -i '/swap/d' /etc/fstab

# Verify swap is off
free -h
```

**Why disable swap?**
- Nomad & Docker perform better without swap
- Prevents performance degradation
- More predictable resource management

---

### Step 6: Configure Hostname & Hosts

```bash
# Set hostname (ganti 'nomad-server' dengan nama yang Anda inginkan)
sudo hostnamectl set-hostname nomad-server

# Verify hostname
hostnamectl

# Update /etc/hosts
sudo tee -a /etc/hosts > /dev/null <<EOF
127.0.0.1 localhost
127.0.1.1 nomad-server

# Add your public IP if available
# YOUR_PUBLIC_IP nomad-server.example.com nomad-server
EOF

# Verify
cat /etc/hosts
```

---

### Step 7: Configure Time Synchronization

```bash
# Install chrony (time sync)
sudo apt-get install -y chrony

# Start and enable chrony
sudo systemctl start chrony
sudo systemctl enable chrony

# Check time sync status
timedatectl status

# Check chrony sources
chronyc sources
```

**Expected Output:**
```
               Local time: Thu 2026-01-01 05:30:00 UTC
           Universal time: Thu 2026-01-01 05:30:00 UTC
                 RTC time: Thu 2026-01-01 05:30:00
                Time zone: UTC (UTC, +0000)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

---

### Step 8: Create Directory Structure

```bash
# Create directories for Nomad
sudo mkdir -p /opt/nomad/{data,config}
sudo mkdir -p /opt/consul/{data,config}
sudo mkdir -p /opt/traefik/{config,logs}

# Set permissions
sudo chmod -R 755 /opt/nomad
sudo chmod -R 755 /opt/consul
sudo chmod -R 755 /opt/traefik

# Verify
ls -la /opt/
```

---

### Step 9: Verification Checklist

Run this verification script:

```bash
#!/bin/bash

echo "=== System Verification ==="
echo ""

# OS Check
echo "✓ OS: $(lsb_release -d | cut -f2)"
echo "✓ Kernel: $(uname -r)"
echo ""

# Resources
echo "✓ CPU Cores: $(nproc)"
echo "✓ RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "✓ Disk Free: $(df -h / | awk 'NR==2 {print $4}')"
echo ""

# Limits
echo "✓ File Descriptors: $(ulimit -n)"
echo "✓ Max Processes: $(ulimit -u)"
echo ""

# Network
echo "✓ Public IP: $(curl -s ifconfig.me)"
echo "✓ Hostname: $(hostname)"
echo ""

# Firewall
echo "✓ Firewall Status:"
sudo ufw status | grep -E "Status|22|80|443|4646|8500"
echo ""

# Time Sync
echo "✓ Time Sync: $(timedatectl | grep 'synchronized' | awk '{print $3}')"
echo ""

# Directories
echo "✓ Directories:"
ls -ld /opt/nomad /opt/consul /opt/traefik 2>/dev/null && echo "  All directories exist" || echo "  ERROR: Missing directories"
echo ""

echo "=== Verification Complete ==="
```

Save as `verify-prerequisites.sh` and run:
```bash
chmod +x verify-prerequisites.sh
./verify-prerequisites.sh
```

---

## ✅ Prerequisites Complete!

Jika semua step di atas berhasil, sistem Anda sudah siap untuk instalasi Nomad stack.

**Next Step**: [01-install-docker.md](01-install-docker.md)

---

## 🆘 Troubleshooting

### Issue: Cannot update packages
```bash
# Fix repository issues
sudo apt-get update --fix-missing
sudo dpkg --configure -a
```

### Issue: Firewall blocks SSH
```bash
# Disable firewall temporarily
sudo ufw disable

# Re-add SSH rule
sudo ufw allow 22/tcp

# Re-enable firewall
sudo ufw enable
```

### Issue: Time not synchronized
```bash
# Restart chrony
sudo systemctl restart chrony

# Force time sync
sudo chronyc makestep
```

---

**Last Updated**: 2026-01-01
