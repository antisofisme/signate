# Portainer Setup Guide - VPS Production Server

**Date**: 2025-11-26
**Target Server**: VPS Production (72.61.209.158)
**Domain**: portainer.zhmhotels.online
**Version**: Portainer CE 2.33.4 + Docker 28.5.2

---

## 🎯 Overview

Tutorial lengkap instalasi Portainer CE di VPS production server dengan Docker-optimized OS. Guide ini mencakup problem yang pernah terjadi, root cause analysis, dan step-by-step instalasi yang **BENAR dan VALIDATED**.

---

## ⚠️ CRITICAL: Docker Version Compatibility

### Problem yang Pernah Terjadi

**Error**: "Failed loading environment - The environment named local/primary is unreachable"

### Root Cause

**Docker 29.0.x INCOMPATIBLE dengan Portainer 2.33.4 (dan bahkan 2.35 STS)**

**Technical Details**:
- Docker 29.0.0+ mengubah **minimum API version ke 1.44**
- Portainer 2.33.4 hanya support **API version sampai 1.43**
- Docker socket communication failed karena API version mismatch
- Environment status stuck di Status: 2 (DOWN/UNREACHABLE)

**Research Sources**:
- [Portainer Discussion #12926](https://github.com/orgs/portainer/discussions/12926)
- [Portainer Issue #12939](https://github.com/portainer/portainer/issues/12939)
- [Official Portainer Docs](https://docs.portainer.io/faqs/known-issues/known-compatibility-issues-with-docker-engine-29.0.0)

### Solution

**WAJIB menggunakan Docker 28.x (bukan 29.x)**

Compatible versions:
- ✅ Docker 28.5.2 (API 1.51) - **RECOMMENDED**
- ✅ Docker 28.4.x (API 1.51)
- ✅ Docker 28.3.x (API 1.51)
- ❌ Docker 29.0.x (API 1.52+) - **NOT COMPATIBLE**

---

## 📋 Prerequisites

### Server Requirements

1. **VPS dengan Docker pre-installed** atau fresh Docker installation
2. **SSH access** dengan root privileges
3. **Nginx installed** untuk reverse proxy
4. **Domain/subdomain** dengan DNS configured (optional, bisa pakai IP direct)

### Server Info (Example - VPS Production)

```bash
IP: 72.61.209.158
SSH User: root
Domain: zhmhotels.online
Subdomain: portainer.zhmhotels.online
OS: Ubuntu 24.04 LTS (Docker-optimized)
```

---

## 🔧 Step-by-Step Installation

### Step 1: Check Docker Version (CRITICAL!)

```bash
# SSH ke server
ssh root@72.61.209.158

# Check Docker version
docker version

# Output harus menunjukkan:
# Client: Version 28.x.x, API version: 1.51
# Server: Version 28.x.x, API version: 1.51 (minimum version 1.24)
```

**⚠️ Jika Docker version 29.x.x**: **WAJIB DOWNGRADE!** (lihat Step 1A)

**✅ Jika Docker version 28.x.x**: Lanjut ke Step 2

### Step 1A: Downgrade Docker (Jika Versi 29.x)

```bash
# 1. Check available Docker 28 versions
apt-cache madison docker-ce | grep '28\.'

# Output example:
# docker-ce | 5:28.5.2-1~ubuntu.24.04~noble | https://download.docker.com/linux/ubuntu noble/stable amd64 Packages
# docker-ce | 5:28.4.5-1~ubuntu.24.04~noble | https://download.docker.com/linux/ubuntu noble/stable amd64 Packages

# 2. Stop all running containers (OPTIONAL - jika ada)
docker stop $(docker ps -q)

# 3. Downgrade ke Docker 28.5.2 (RECOMMENDED)
apt-get install --allow-downgrades -y \
  docker-ce=5:28.5.2-1~ubuntu.24.04~noble \
  docker-ce-cli=5:28.5.2-1~ubuntu.24.04~noble \
  containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Verify downgrade successful
docker version

# Expected output:
# Client:
#  Version:           28.5.2
#  API version:       1.51
# Server:
#  Version:           28.5.2
#  API version:       1.51 (minimum version 1.24)

# 5. Restart Docker service
systemctl restart docker

# 6. Check Docker is running
systemctl is-active docker
# Output: active
```

**🔒 Lock Docker Version (Prevent Auto-Upgrade)**:

```bash
# Hold Docker packages to prevent accidental upgrade
apt-mark hold docker-ce docker-ce-cli containerd.io

# Verify hold status
apt-mark showhold
# Output should show:
# docker-ce
# docker-ce-cli
# containerd.io
```

### Step 2: Remove Old Portainer Data (Fresh Start)

```bash
# 1. Stop and remove old Portainer container (jika ada)
docker stop portainer 2>/dev/null || true
docker rm portainer 2>/dev/null || true

# 2. Remove old Portainer volume (HATI-HATI! Data akan hilang)
docker volume rm portainer_data 2>/dev/null || true

# 3. Verify cleanup
docker ps -a --filter name=portainer
# Output: (empty)

docker volume ls --filter name=portainer
# Output: (empty)
```

### Step 3: Install Portainer CE (Fresh)

```bash
# 1. Create fresh volume
docker volume create portainer_data

# 2. Install Portainer CE latest
docker run -d \
  -p 9000:9000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

# 3. Wait for container to start (5-10 seconds)
sleep 10

# 4. Check container status
docker ps --filter name=portainer

# Expected output:
# CONTAINER ID   IMAGE                          STATUS        PORTS
# xxxxxxxxxxxx   portainer/portainer-ce:latest  Up X seconds  0.0.0.0:9000->9000/tcp, 0.0.0.0:9443->9443/tcp
```

### Step 4: Validate Installation

```bash
# 1. Check Portainer API responding
curl -s http://localhost:9000/api/system/status

# Expected output:
# {"Version":"2.33.4","InstanceID":"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}

# 2. Check logs - should have NO errors
docker logs portainer --tail 50

# Expected: No "Podman" errors, no "unreachable" errors, no API version errors

# 3. Check Docker socket accessible
docker exec portainer ls -l /var/run/docker.sock

# Expected: socket file exists with proper permissions
```

**✅ Installation Complete!** Portainer backend sekarang running.

---

## 🌐 Step 5: Setup Nginx Reverse Proxy (HTTPS Access)

### Create Nginx Config for Portainer

```bash
# 1. Create nginx config file
cat > /etc/nginx/sites-available/portainer.zhmhotels.online << 'EOF'
server {
    listen 80;
    server_name portainer.zhmhotels.online;

    # Allow large file uploads
    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 2. Enable the site
ln -sf /etc/nginx/sites-available/portainer.zhmhotels.online /etc/nginx/sites-enabled/

# 3. Test nginx config
nginx -t

# Expected: syntax is ok, test is successful

# 4. Reload nginx
systemctl reload nginx

# 5. Test HTTP access
curl -I http://portainer.zhmhotels.online/

# Expected: HTTP/1.1 200 OK
```

### Install SSL Certificate (Let's Encrypt)

```bash
# 1. Install certbot (if not installed)
apt-get update
apt-get install -y certbot python3-certbot-nginx

# 2. Obtain SSL certificate for portainer subdomain
certbot --nginx -d portainer.zhmhotels.online \
  --non-interactive \
  --agree-tos \
  --email admin@zhmhotels.online \
  --redirect

# 3. Verify SSL certificate
certbot certificates

# Expected:
# Certificate Name: portainer.zhmhotels.online
#   Domains: portainer.zhmhotels.online
#   Expiry Date: 2026-XX-XX (auto-renews)

# 4. Test HTTPS access
curl -I https://portainer.zhmhotels.online/

# Expected: HTTP/1.1 200 OK with SSL headers

# 5. Enable auto-renewal
systemctl enable --now certbot.timer
systemctl is-active certbot.timer
# Output: active
```

**✅ HTTPS Access Ready!** Portainer sekarang accessible via https://portainer.zhmhotels.online/

---

## 🎨 Step 6: First-Time Setup (Browser UI)

### Access Portainer Web UI

1. **Open browser in Incognito/Private mode**
   - Reason: Avoid cached old Portainer state
   - URL: https://portainer.zhmhotels.online/

2. **Create Admin User** (First-time setup wizard)
   ```
   Username: admin (or your choice)
   Password: [secure password - min 12 characters]
   Confirm password: [same password]

   Click: "Create user"
   ```

3. **Select Environment Type**
   ```
   Click: "Get Started" button

   This will auto-create Docker environment with correct settings:
   - Environment Name: "local" (auto-generated)
   - Type: Docker Standalone
   - URL: /var/run/docker.sock
   ```

4. **Verify Environment Connected**
   ```
   Environment should show:
   - Status: CONNECTED (green icon)
   - Name: "local" or "primary"
   - Type: Docker Standalone
   - URL: unix:///var/run/docker.sock
   ```

5. **View Containers**
   ```
   Click into environment
   Navigate to: Containers

   Should see:
   - portainer (running)
   - Other containers if any
   ```

**✅ Portainer Fully Operational!** Environment connected, UI accessible, ready to manage Docker.

---

## ✅ Validation Checklist

### Backend Validation

```bash
# 1. Docker version
docker version --format '{{.Server.Version}} (API: {{.Server.APIVersion}})'
# Expected: 28.5.2 (API: 1.51)

# 2. Container running
docker ps --filter name=portainer --format 'Status: {{.Status}}'
# Expected: Status: Up X minutes

# 3. API responding
curl -s http://localhost:9000/api/system/status | grep Version
# Expected: "Version":"2.33.4"

# 4. No errors in logs
docker logs portainer --tail 30 2>&1 | grep -i error || echo "No errors"
# Expected: No errors

# 5. Nginx config valid
nginx -t
# Expected: syntax is ok, test is successful

# 6. HTTPS accessible
curl -sI https://portainer.zhmhotels.online/ | head -1
# Expected: HTTP/1.1 200 OK

# 7. SSL certificate valid
curl -sI https://portainer.zhmhotels.online/ | grep -i "strict-transport"
# Expected: Strict-Transport-Security header present
```

### Frontend Validation (Browser)

- [ ] Can access https://portainer.zhmhotels.online/ without SSL warnings
- [ ] First-time setup wizard appears (or login page if already setup)
- [ ] Can create admin user successfully
- [ ] "Get Started" button creates environment automatically
- [ ] Environment shows as **CONNECTED** (green status)
- [ ] Can view container list (including portainer container itself)
- [ ] No "environment unreachable" errors
- [ ] No "Podman" errors in console logs (F12)

**✅ All checks passed** = Portainer installation successful!

---

## 🔍 Troubleshooting Guide

### Issue 1: "Environment unreachable" setelah fresh install

**Symptoms**: Environment status shows as DOWN/UNREACHABLE

**Possible Causes**:
1. Docker version 29.x (incompatible)
2. Browser cache dari old Portainer state
3. Wrong environment type selected (Podman instead of Docker)

**Solutions**:

```bash
# A. Verify Docker version
docker version --format '{{.Server.APIVersion}}'
# Must be: 1.51 (Docker 28.x)
# If 1.52+: DOWNGRADE to Docker 28.x (see Step 1A)

# B. Check Portainer logs
docker logs portainer --tail 50 | grep -i error

# If "Podman" errors:
# - Delete environment in UI
# - Use "Get Started" button instead (auto-creates correct type)

# C. Clear browser cache
# - Use Incognito/Private window
# - Or clear all browser data (Ctrl+Shift+Delete)

# D. Restart Portainer
docker restart portainer
sleep 5
# Access UI again, use "Get Started" button
```

### Issue 2: SSL Certificate Error / "Not Secure"

**Symptoms**: Browser shows "Not Secure" warning

**Solutions**:

```bash
# 1. Check certificate exists
certbot certificates | grep portainer.zhmhotels.online

# 2. If not found, obtain certificate
certbot --nginx -d portainer.zhmhotels.online \
  --non-interactive --agree-tos \
  --email admin@zhmhotels.online --redirect

# 3. Verify nginx SSL config
cat /etc/nginx/sites-available/portainer.zhmhotels.online | grep ssl

# Should contain:
# listen 443 ssl;
# ssl_certificate /etc/letsencrypt/live/portainer.zhmhotels.online/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/portainer.zhmhotels.online/privkey.pem;

# 4. Reload nginx
nginx -t && systemctl reload nginx
```

### Issue 3: Cannot Access Portainer (Connection Refused)

**Symptoms**: Cannot connect to https://portainer.zhmhotels.online/

**Solutions**:

```bash
# 1. Check container running
docker ps --filter name=portainer
# If not running: docker start portainer

# 2. Check port bindings
docker port portainer
# Expected:
# 9000/tcp -> 0.0.0.0:9000
# 9443/tcp -> 0.0.0.0:9443

# 3. Check nginx running
systemctl is-active nginx
# If not active: systemctl start nginx

# 4. Check nginx listening on port 80/443
ss -tulpn | grep nginx
# Expected: nginx listening on :80 and :443

# 5. Check DNS resolution
nslookup portainer.zhmhotels.online
# Should resolve to: 72.61.209.158

# 6. Test direct IP access
curl -I http://72.61.209.158:9000/
# If works: DNS or nginx config issue
# If fails: Portainer container issue
```

### Issue 4: Docker Auto-Upgraded to 29.x

**Symptoms**: Portainer stopped working after system update

**Solutions**:

```bash
# 1. Check current Docker version
docker version --format '{{.Server.Version}}'

# If 29.x.x:
# 2. Downgrade to 28.5.2 (see Step 1A)
apt-get install --allow-downgrades -y \
  docker-ce=5:28.5.2-1~ubuntu.24.04~noble \
  docker-ce-cli=5:28.5.2-1~ubuntu.24.04~noble

# 3. Hold package to prevent future upgrades
apt-mark hold docker-ce docker-ce-cli containerd.io

# 4. Restart Portainer
docker restart portainer
```

### Issue 5: "Invalid Password" during login

**Symptoms**: Cannot login with created admin password

**Solutions**:

```bash
# 1. Reset Portainer admin password
docker stop portainer
docker run --rm \
  -v portainer_data:/data \
  portainer/portainer-ce:latest \
  --admin-password='$2y$05$YourBcryptHashHere'
docker start portainer

# OR reset completely (LOSES ALL DATA):
docker stop portainer
docker rm portainer
docker volume rm portainer_data

# Then reinstall from Step 2
```

---

## 📊 Performance & Monitoring

### Container Resource Usage

```bash
# Check Portainer resource usage
docker stats portainer --no-stream

# Expected (typical):
# CPU: 0.1-1%
# Memory: 20-50 MB
# Network: minimal
```

### Logs Monitoring

```bash
# Real-time logs
docker logs portainer --follow

# Last 100 lines
docker logs portainer --tail 100

# Filter errors only
docker logs portainer 2>&1 | grep -i error

# Filter by timestamp
docker logs portainer --since 10m
```

---

## 🔐 Security Best Practices

### 1. Change Default Admin Password

- Use strong password (min 16 characters, mixed case, numbers, symbols)
- Enable 2FA if available in Portainer settings
- Rotate passwords regularly

### 2. Restrict Network Access

```bash
# Option A: Firewall rules (allow only specific IPs)
ufw allow from YOUR_IP to any port 9000 proto tcp
ufw deny 9000/tcp

# Option B: Nginx IP whitelist
# Edit /etc/nginx/sites-available/portainer.zhmhotels.online
location / {
    allow YOUR_IP;
    deny all;

    proxy_pass http://localhost:9000;
    # ... rest of config
}
```

### 3. Enable HTTPS Only

```bash
# Ensure nginx redirects HTTP to HTTPS
# Check config contains:
server {
    listen 80;
    server_name portainer.zhmhotels.online;
    return 301 https://$server_name$request_uri;
}
```

### 4. Regular Updates

```bash
# Check for Portainer updates (when Docker 29 support added)
docker pull portainer/portainer-ce:latest

# Update Portainer (backup first!)
docker stop portainer
docker rm portainer
docker run -d -p 9000:9000 -p 9443:9443 \
  --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

---

## 📝 Maintenance Tasks

### Daily Checks

```bash
# Container health
docker ps --filter name=portainer

# Resource usage
docker stats portainer --no-stream
```

### Weekly Checks

```bash
# Check logs for errors
docker logs portainer --since 7d 2>&1 | grep -i error

# Verify SSL certificate expiry
certbot certificates | grep -A2 portainer.zhmhotels.online

# Check disk usage
docker system df
```

### Monthly Tasks

```bash
# Backup Portainer data
docker exec portainer tar czf - /data | cat > portainer_backup_$(date +%Y%m%d).tar.gz

# Clean unused Docker resources
docker system prune -a --volumes -f

# Review access logs (if enabled)
tail -100 /var/log/nginx/access.log | grep portainer
```

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Start Portainer
docker start portainer

# Stop Portainer
docker stop portainer

# Restart Portainer
docker restart portainer

# View logs
docker logs portainer --tail 50

# Check status
docker ps --filter name=portainer

# Access shell (troubleshooting)
docker exec -it portainer /bin/sh

# Backup data volume
docker run --rm -v portainer_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/portainer_backup.tar.gz /data

# Restore data volume
docker run --rm -v portainer_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/portainer_backup.tar.gz -C /
```

### URLs

- **HTTPS**: https://portainer.zhmhotels.online/
- **HTTP**: http://72.61.209.158:9000/ (direct access, testing only)
- **API Docs**: https://docs.portainer.io/api/

---

## 📚 Additional Resources

### Official Documentation

- [Portainer Docs](https://docs.portainer.io/)
- [Portainer CE Installation](https://docs.portainer.io/start/install-ce)
- [Docker Engine API](https://docs.docker.com/engine/api/)
- [Known Issues - Docker 29](https://docs.portainer.io/faqs/known-issues/known-compatibility-issues-with-docker-engine-29.0.0)

### Community Resources

- [Portainer GitHub](https://github.com/portainer/portainer)
- [Portainer Community Forums](https://community.portainer.io/)
- [Docker 29 Compatibility Discussion](https://github.com/orgs/portainer/discussions/12926)

### Related Files

- `CLAUDE.md` - Server credentials and architecture documentation
- `PORTAINER_FIX_SUMMARY.md` - Detailed problem analysis and fix report
- `docker-compose.yml` - Docker Compose configuration (if using)
- `DEPLOYMENT_CHECKLIST.md` - General deployment procedures

---

## ✅ Success Criteria

Installation considered successful when ALL of the following are true:

- [ ] Docker version 28.x.x (NOT 29.x)
- [ ] Portainer container running (status: Up)
- [ ] Portainer API responding (version 2.33.4)
- [ ] HTTPS access working (no SSL warnings)
- [ ] Environment status: CONNECTED (green)
- [ ] Can view container list in UI
- [ ] No errors in container logs
- [ ] SSL certificate valid and auto-renewing
- [ ] No "environment unreachable" errors
- [ ] No "Podman" errors in logs
- [ ] Nginx reverse proxy working correctly

**Current Status**: ✅ ALL CRITERIA MET (as of 2025-11-26)

---

**Last Updated**: 2025-11-26
**Validated On**: VPS Production (72.61.209.158)
**Maintained By**: Development Team
