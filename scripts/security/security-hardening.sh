#!/bin/bash
# Security Hardening Script for Digital Signage System

set -e

echo "[$(date)] Starting security hardening..."

# ============================================
# 1. System Security
# ============================================
echo "[$(date)] Configuring system security..."

# Update system packages
apt-get update
apt-get upgrade -y

# Install security tools
apt-get install -y \
    fail2ban \
    ufw \
    unattended-upgrades \
    logwatch \
    rkhunter \
    chkrootkit

# ============================================
# 2. Firewall Configuration
# ============================================
echo "[$(date)] Configuring firewall..."

# Reset firewall
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (change port if needed)
ufw allow 22/tcp comment 'SSH'

# Allow application ports
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8001/tcp comment 'Backend API'
ufw allow 8080/tcp comment 'Player'
ufw allow 3000/tcp comment 'CMS Frontend'

# Allow monitoring ports (restrict source in production)
ufw allow from 192.168.5.0/24 to any port 9090 comment 'Prometheus'
ufw allow from 192.168.5.0/24 to any port 3001 comment 'Grafana'

# Enable firewall
ufw --force enable

# ============================================
# 3. Fail2Ban Configuration
# ============================================
echo "[$(date)] Configuring fail2ban..."

# Create jail.local
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = admin@example.com
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2

[nginx-noproxy]
enabled = true
port = http,https
filter = nginx-noproxy
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

# Restart fail2ban
systemctl restart fail2ban

# ============================================
# 4. Docker Security
# ============================================
echo "[$(date)] Securing Docker..."

# Create Docker daemon config
cat > /etc/docker/daemon.json << 'EOF'
{
  "icc": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "userland-proxy": false,
  "no-new-privileges": true,
  "live-restore": true,
  "userland-proxy-path": "/usr/bin/docker-proxy"
}
EOF

# Restart Docker
systemctl restart docker

# ============================================
# 5. Nginx Security Headers
# ============================================
echo "[$(date)] Adding security headers to Nginx..."

# Create security headers config
cat > /home/gzjbbk/signage/docker/nginx/security-headers.conf << 'EOF'
# Security Headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# Hide Nginx version
server_tokens off;

# Limit request methods
if ($request_method !~ ^(GET|POST|PUT|DELETE|HEAD|OPTIONS)$) {
    return 405;
}

# Block user agents
if ($http_user_agent ~* (wget|curl|python)) {
    return 403;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
EOF

# ============================================
# 6. Application Security
# ============================================
echo "[$(date)] Configuring application security..."

# Update .env with secure values
cat >> /home/gzjbbk/signage/.env << 'EOF'

# Security Settings
SECURE_COOKIES=true
SESSION_SECURE=true
CORS_ALLOW_CREDENTIALS=false
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900
PASSWORD_MIN_LENGTH=12
REQUIRE_PASSWORD_COMPLEXITY=true
SESSION_TIMEOUT=3600
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
EOF

# ============================================
# 7. Database Security
# ============================================
echo "[$(date)] Securing database..."

# Create database backup user with limited privileges
docker exec -i signage-postgres psql -U signage_user -d signage_db << 'EOF'
-- Create backup user
CREATE USER backup_user WITH PASSWORD 'secure_backup_password';
GRANT CONNECT ON DATABASE signage_db TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;

-- Revoke unnecessary privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
EOF

# ============================================
# 8. SSL/TLS Configuration
# ============================================
echo "[$(date)] Configuring SSL/TLS..."

# Install certbot
apt-get install -y certbot python3-certbot-nginx

# Generate strong DH parameters
openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

# ============================================
# 9. Monitoring & Alerts
# ============================================
echo "[$(date)] Setting up security monitoring..."

# Configure logwatch
cat > /etc/logwatch/conf/logwatch.conf << 'EOF'
Output = mail
Format = html
MailTo = admin@example.com
MailFrom = logwatch@signage.local
Range = yesterday
Detail = High
Service = All
EOF

# Configure rkhunter
rkhunter --update
rkhunter --propupd

# ============================================
# 10. Automated Security Updates
# ============================================
echo "[$(date)] Configuring automated updates..."

cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "admin@example.com";
EOF

# Enable automatic updates
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
EOF

# ============================================
# 11. Create Security Audit Script
# ============================================
cat > /home/gzjbbk/signage/scripts/security/security-audit.sh << 'EOF'
#!/bin/bash
# Security Audit Script

echo "=== Security Audit Report ==="
echo "Date: $(date)"
echo

echo "1. System Information"
uname -a
echo

echo "2. Open Ports"
ss -tuln
echo

echo "3. Failed Login Attempts"
grep "Failed password" /var/log/auth.log | tail -20
echo

echo "4. Docker Containers"
docker ps -a
echo

echo "5. Firewall Rules"
ufw status verbose
echo

echo "6. Fail2ban Status"
fail2ban-client status
echo

echo "7. Last System Updates"
grep " upgrade " /var/log/dpkg.log | tail -10
echo

echo "8. Disk Usage"
df -h
echo

echo "9. Memory Usage"
free -h
echo

echo "10. Running Processes"
ps aux --sort=-%cpu | head -20
EOF

chmod +x /home/gzjbbk/signage/scripts/security/security-audit.sh

# ============================================
# 12. Create Security Checklist
# ============================================
cat > /home/gzjbbk/signage/SECURITY_CHECKLIST.md << 'EOF'
# Security Checklist

## Regular Tasks (Daily)
- [ ] Check system logs for anomalies
- [ ] Review fail2ban logs
- [ ] Monitor disk usage
- [ ] Verify backup completion

## Weekly Tasks
- [ ] Run security audit script
- [ ] Review user access logs
- [ ] Check for system updates
- [ ] Verify SSL certificates

## Monthly Tasks
- [ ] Run rkhunter scan
- [ ] Review firewall rules
- [ ] Update security policies
- [ ] Test backup restoration

## Quarterly Tasks
- [ ] Penetration testing
- [ ] Security training
- [ ] Update incident response plan
- [ ] Review access controls

## Incident Response
1. Isolate affected systems
2. Preserve evidence
3. Analyze logs
4. Remove threat
5. Restore from backup
6. Document incident
7. Update security measures
EOF

echo "[$(date)] Security hardening completed!"
echo "Please review and customize security settings for your environment."
echo "Remember to:"
echo "1. Change default passwords"
echo "2. Configure SSL certificates"
echo "3. Update email addresses in configs"
echo "4. Test all security measures"