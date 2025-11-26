# Production Deployment Checklist

Complete step-by-step checklist for deploying Signage System to production with domain.

## ✅ Pre-Deployment

### 1. Domain & DNS

- [ ] Domain purchased and registered (e.g., zhmhotels.online)
- [ ] DNS control panel accessible
- [ ] Email address for SSL certificates ready
- [ ] Public IP address confirmed (43.247.36.250)

### 2. Server Requirements

- [ ] Server accessible via SSH
- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Minimum 2GB RAM available
- [ ] Minimum 10GB disk space available
- [ ] Server IP configured (192.168.5.12)

### 3. Network Requirements

- [ ] MikroTik router access available
- [ ] Port 80 can be forwarded
- [ ] Port 443 can be forwarded
- [ ] Server can access internet
- [ ] No firewall blocking ports 80, 443

## 📝 Step 1: Environment Setup

### Copy and Edit Environment File

```bash
cd /home/gzjbbk/signate
cp docker/.env.production .env
nano .env
```

### Update These Values

- [ ] `DOMAIN=zhmhotels.online` (your actual domain)
- [ ] `SSL_EMAIL=your-email@example.com` (your real email)
- [ ] `JWT_SECRET_KEY=` (generate strong random key)
- [ ] `DATABASE_PASSWORD=` (strong password)
- [ ] `SERVER_IP=192.168.5.12` (verify this is correct)
- [ ] `SERVER_PUBLIC_IP=43.247.36.250` (verify this is correct)

### Generate Strong Secrets

```bash
# Generate JWT secret (use this value for JWT_SECRET_KEY)
openssl rand -base64 32

# Generate database password (use this value for DATABASE_PASSWORD)
openssl rand -base64 24
```

### Verify Environment File

```bash
# Check required variables are set
grep -E "^(DOMAIN|SSL_EMAIL|JWT_SECRET_KEY|DATABASE_PASSWORD)=" .env

# Should show all 4 variables with non-default values
```

**Status**: [ ] Environment configured ✅

---

## 🌐 Step 2: DNS Configuration

### Add DNS A Records

Login to your DNS provider (Hostinger, Cloudflare, etc.) and add:

| Type | Name   | Value         | TTL  |
|------|--------|---------------|------|
| A    | admin  | 43.247.36.250 | 3600 |
| A    | api    | 43.247.36.250 | 3600 |
| A    | player | 43.247.36.250 | 3600 |

**Important**: Use `admin`, `api`, `player` as the name, NOT the full domain!

### Verify DNS Records Added

- [ ] admin.zhmhotels.online → 43.247.36.250
- [ ] api.zhmhotels.online → 43.247.36.250
- [ ] player.zhmhotels.online → 43.247.36.250

### Wait for DNS Propagation

- [ ] Waited 5-10 minutes minimum
- [ ] Tested DNS from server: `host admin.zhmhotels.online`
- [ ] Tested DNS from internet: https://dnschecker.org

**Status**: [ ] DNS propagated ✅

---

## 🔀 Step 3: MikroTik Port Forwarding

### Login to MikroTik

- [ ] Accessed via Winbox or WebFig
- [ ] Identified WAN interface (interface with public IP)

### Add Port Forwarding Rules

**Port 80 (HTTP):**
- [ ] Chain: `dstnat`
- [ ] Protocol: `tcp (6)`
- [ ] Dst. Port: `80`
- [ ] In. Interface: `[your-WAN-interface]`
- [ ] Action: `dst-nat`
- [ ] To Addresses: `192.168.5.12`
- [ ] To Ports: `80`
- [ ] Comment: `Signage HTTP`

**Port 443 (HTTPS):**
- [ ] Chain: `dstnat`
- [ ] Protocol: `tcp (6)`
- [ ] Dst. Port: `443`
- [ ] In. Interface: `[your-WAN-interface]`
- [ ] Action: `dst-nat`
- [ ] To Addresses: `192.168.5.12`
- [ ] To Ports: `443`
- [ ] Comment: `Signage HTTPS`

### Test Port Forwarding

From outside network (mobile data):

```bash
curl -I http://43.247.36.250
```

- [ ] Port 80 accessible from internet
- [ ] Connection reaches server (should see Nginx or backend response)

**Status**: [ ] Port forwarding working ✅

---

## 🚀 Step 4: Deploy Docker Services

### Run Deployment Script

```bash
cd /home/gzjbbk/signate
bash docker/deploy-production.sh
```

### Verify Deployment Steps

The script will:

- [ ] Load environment variables from .env
- [ ] Validate all required variables
- [ ] Generate Nginx configuration from template
- [ ] Stop existing containers
- [ ] Build new Docker images
- [ ] Start all services
- [ ] Wait for services to be healthy
- [ ] Display access URLs

### Check Service Status

```bash
docker-compose -f docker/docker-compose.yml ps
```

All services should show "Up" status:
- [ ] signage-backend-python
- [ ] signage-cms
- [ ] signage-player
- [ ] signage-postgres
- [ ] signage-redis

### Test Local Access

```bash
# Backend API
curl -I http://localhost:8001/health
# Should return: 200 OK

# CMS Admin
curl -I http://localhost:3000
# Should return: 200 OK

# Player
curl -I http://localhost:8080
# Should return: 200 OK
```

- [ ] Backend API responding on port 8001
- [ ] CMS Admin responding on port 3000
- [ ] Player responding on port 8080

**Status**: [ ] Docker services running ✅

---

## 🌍 Step 5: Nginx Setup

### Run Nginx Setup Script

```bash
sudo bash docker/setup-nginx.sh
```

### Verify Nginx Installation

The script will:

- [ ] Install Nginx if not present
- [ ] Copy generated config to /etc/nginx/sites-available/
- [ ] Enable site with symlink
- [ ] Remove default site
- [ ] Test configuration
- [ ] Reload Nginx

### Check Nginx Status

```bash
sudo systemctl status nginx
# Should show: active (running)
```

- [ ] Nginx service active and running
- [ ] No configuration errors

### Test HTTP Access

From outside network (mobile data):

```bash
curl -I http://admin.zhmhotels.online
curl -I http://api.zhmhotels.online/health
curl -I http://player.zhmhotels.online
```

- [ ] admin.zhmhotels.online accessible (HTTP)
- [ ] api.zhmhotels.online accessible (HTTP)
- [ ] player.zhmhotels.online accessible (HTTP)

**Status**: [ ] Nginx configured ✅

---

## 🔐 Step 6: SSL Certificate Installation

### Prerequisites Check

**CRITICAL**: All must be true before proceeding!

- [ ] DNS fully propagated (test with `host admin.zhmhotels.online`)
- [ ] Port 80 accessible from internet (tested in Step 5)
- [ ] Port 443 forwarded in MikroTik (configured in Step 3)
- [ ] Nginx running (verified in Step 5)

### Run SSL Setup Script

```bash
sudo bash docker/setup-ssl.sh
```

### Verify SSL Installation

The script will:

- [ ] Install certbot if needed
- [ ] Stop Nginx temporarily
- [ ] Generate SSL certificates for all 3 domains
- [ ] Update Nginx config for HTTPS
- [ ] Start Nginx with SSL
- [ ] Setup auto-renewal (twice daily)

### Check SSL Certificates

```bash
sudo certbot certificates
```

Should show:
- [ ] Certificate for admin.zhmhotels.online (expires in ~90 days)
- [ ] Alternative names: api.zhmhotels.online, player.zhmhotels.online
- [ ] Certificate valid and not expired

### Test HTTPS Access

From outside network (mobile data):

```bash
curl -I https://admin.zhmhotels.online
curl -I https://api.zhmhotels.online/health
curl -I https://player.zhmhotels.online
```

- [ ] admin.zhmhotels.online accessible via HTTPS ✅
- [ ] api.zhmhotels.online accessible via HTTPS ✅
- [ ] player.zhmhotels.online accessible via HTTPS ✅
- [ ] HTTP redirects to HTTPS automatically ✅

**Status**: [ ] SSL certificates installed ✅

---

## 🧪 Step 7: Final Testing

### Test Admin Dashboard

Open in browser: https://admin.zhmhotels.online

- [ ] Login page loads
- [ ] No SSL certificate errors
- [ ] Can login with credentials (admin/admin123)
- [ ] Dashboard displays correctly
- [ ] Device list loads
- [ ] Content management works

### Test Backend API

Open in browser: https://api.zhmhotels.online/docs

- [ ] Swagger UI loads
- [ ] All endpoints visible
- [ ] Can test endpoints
- [ ] Authentication works
- [ ] Responses return correctly

### Test Player

Open in browser: https://player.zhmhotels.online

- [ ] Player loads
- [ ] Activation screen shows
- [ ] Can enter activation code
- [ ] WebSocket connects
- [ ] Content displays

### Test WebSocket

Check backend logs:

```bash
docker logs signage-backend-python --tail 50
```

- [ ] WebSocket connections successful
- [ ] No CORS errors
- [ ] Real-time updates working

### Test from Different Networks

- [ ] Tested from office WiFi
- [ ] Tested from mobile data
- [ ] Tested from different location
- [ ] All working consistently

**Status**: [ ] All tests passed ✅

---

## 📊 Step 8: Monitoring & Verification

### Setup Monitoring

```bash
# View all service logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Check Resource Usage

```bash
# Check disk space
df -h

# Check memory
free -h

# Check Docker stats
docker stats --no-stream
```

- [ ] Disk space sufficient (>5GB free)
- [ ] Memory usage normal (<80%)
- [ ] CPU usage normal (<50%)

### Verify Database

```bash
docker exec -it signage-postgres psql -U signage_user -d signage_db
```

```sql
-- Check user count
SELECT COUNT(*) FROM users;

-- Check device count
SELECT COUNT(*) FROM devices;

-- Exit
\q
```

- [ ] Database accessible
- [ ] Tables exist
- [ ] Default admin user exists

### Check Auto-Renewal

```bash
# Check crontab
sudo grep certbot /etc/crontab
```

- [ ] Auto-renewal cron job configured
- [ ] Runs twice daily

**Status**: [ ] Monitoring configured ✅

---

## 📝 Step 9: Documentation

### Update Project Documentation

- [ ] Document production URLs in project README
- [ ] Save `.env` backup securely (NEVER commit to git!)
- [ ] Document any custom configurations
- [ ] Record deployment date and version

### Save Important Information

Create a secure note with:

- [ ] Domain name: zhmhotels.online
- [ ] Admin URL: https://admin.zhmhotels.online
- [ ] API URL: https://api.zhmhotels.online/docs
- [ ] Player URL: https://player.zhmhotels.online
- [ ] Default admin credentials
- [ ] Database password
- [ ] JWT secret key
- [ ] SSL renewal email

### Create Backup

```bash
# Backup database
docker exec signage-postgres pg_dump -U signage_user signage_db > backup_$(date +%Y%m%d).sql

# Backup .env
cp .env .env.backup_$(date +%Y%m%d)

# Backup uploaded files (if any)
# tar -czf uploads_backup_$(date +%Y%m%d).tar.gz /path/to/uploads
```

- [ ] Database backup created
- [ ] Environment file backed up
- [ ] Backup stored securely

**Status**: [ ] Documentation complete ✅

---

## 🎉 Step 10: Go Live

### Final Checklist

- [ ] All services running and healthy
- [ ] DNS fully propagated
- [ ] HTTPS working on all domains
- [ ] Admin dashboard accessible
- [ ] API endpoints responding
- [ ] Player loading correctly
- [ ] WebSocket connections working
- [ ] No errors in logs
- [ ] Backups created
- [ ] Documentation updated

### Announce Go-Live

- [ ] Inform team deployment is complete
- [ ] Share access URLs with stakeholders
- [ ] Provide login credentials to admins
- [ ] Schedule follow-up monitoring

### Post-Deployment Tasks

**Week 1:**
- [ ] Monitor logs daily
- [ ] Check SSL certificate status
- [ ] Verify auto-renewal works
- [ ] Monitor resource usage
- [ ] Test all features thoroughly

**Week 2:**
- [ ] Create additional admin users
- [ ] Setup content library
- [ ] Configure playlists
- [ ] Register devices
- [ ] Test full workflow

**Month 1:**
- [ ] Review performance metrics
- [ ] Optimize if needed
- [ ] Plan for scaling
- [ ] Document lessons learned

**Status**: [ ] System live and operational ✅

---

## 🚨 Emergency Rollback

If something goes wrong:

### Rollback Docker Services

```bash
cd /home/gzjbbk/signage
docker-compose -f docker/docker-compose.yml down
# Restore previous version
git checkout main
docker-compose -f docker/docker-compose.yml up -d
```

### Rollback Nginx Config

```bash
sudo cp /etc/nginx/sites-available/signage.backup.* /etc/nginx/sites-available/signage
sudo systemctl reload nginx
```

### Rollback Database

```bash
docker exec -i signage-postgres psql -U signage_user -d signage_db < backup_YYYYMMDD.sql
```

### Disable SSL (if needed)

```bash
# Restore HTTP-only config
sudo cp docker/nginx/signage.conf /etc/nginx/sites-available/signage
sudo systemctl reload nginx
```

---

## 📞 Support Contacts

**Technical Issues:**
- Check logs: `docker-compose -f docker/docker-compose.yml logs`
- Consult: `docker/README.md`
- Troubleshooting: `docker/README.md` → Troubleshooting section

**Infrastructure Issues:**
- DNS: Contact domain registrar support
- MikroTik: Consult MikroTik documentation
- SSL: Let's Encrypt community forums

**Application Issues:**
- Backend logs: `docker logs signage-backend-python`
- Frontend logs: Browser console
- Database: Check PostgreSQL logs

---

## ✅ Deployment Complete!

Congratulations! Your Signage System is now live at:

- 🎨 **Admin Dashboard**: https://admin.zhmhotels.online
- 🔌 **Backend API**: https://api.zhmhotels.online
- 📺 **Player/Display**: https://player.zhmhotels.online

**Next Steps:**
1. Start adding content
2. Register display devices
3. Create playlists
4. Monitor system health

**Maintenance:**
- SSL auto-renews every 90 days
- Check logs weekly
- Backup database weekly
- Update system monthly

---

**Deployment Date**: ________________
**Deployed By**: ________________
**Version**: 1.0.0
**Status**: ✅ Production
