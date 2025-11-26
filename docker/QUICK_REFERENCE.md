# Quick Reference Guide - Signage System Deployment

One-page quick reference for common deployment tasks and commands.

## 📂 File Locations

```
/home/gzjbbk/signage/          # Project root
├── .env                        # Active environment config (NEVER commit!)
├── docker/
│   ├── .env.production         # Production template
│   ├── .env.local              # Development template
│   ├── deploy-production.sh    # Main deployment
│   ├── setup-nginx.sh          # Nginx setup
│   ├── setup-ssl.sh            # SSL setup
│   ├── docker-compose.yml      # Services definition
│   └── nginx/
│       ├── signage.conf.template   # Config template
│       └── signage.conf            # Generated config
```

## 🚀 Deployment Commands

### First Time Setup

```bash
# 1. Copy environment template
cp docker/.env.production .env

# 2. Edit variables (CRITICAL: change JWT_SECRET_KEY, DATABASE_PASSWORD, SSL_EMAIL)
nano .env

# 3. Deploy Docker services
bash docker/deploy-production.sh

# 4. Setup Nginx (after DNS propagation)
sudo bash docker/setup-nginx.sh

# 5. Install SSL (after HTTP works)
sudo bash docker/setup-ssl.sh
```

### Regular Updates

```bash
# Pull latest code
git pull

# Rebuild and restart services
cd /home/gzjbbk/signage
docker-compose -f docker/docker-compose.yml up -d --build
```

## 🐳 Docker Commands

```bash
# View all services
docker-compose -f docker/docker-compose.yml ps

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Stop all services
docker-compose -f docker/docker-compose.yml down

# Restart specific service
docker-compose -f docker/docker-compose.yml restart backend-api

# View logs (all services)
docker-compose -f docker/docker-compose.yml logs -f

# View logs (specific service)
docker logs signage-backend-python -f

# Rebuild specific service
docker-compose -f docker/docker-compose.yml up -d --build backend-api
```

## 🌐 Service URLs

### Local Access (from server)
```
http://localhost:8001          # Backend API
http://localhost:8001/docs     # API Documentation
http://localhost:3000          # CMS Admin
http://localhost:8080          # Player
```

### Production Access (from internet)
```
https://admin.zhmhotels.online    # Admin Dashboard
https://api.zhmhotels.online      # Backend API
https://api.zhmhotels.online/docs # API Docs
https://player.zhmhotels.online   # Player/Display
```

## 🔍 Testing & Verification

### Test Local Services

```bash
# Backend health check
curl -I http://localhost:8001/health

# CMS Admin
curl -I http://localhost:3000

# Player
curl -I http://localhost:8080
```

### Test Domain Access (from mobile data)

```bash
# Before SSL
curl -I http://admin.zhmhotels.online

# After SSL
curl -I https://admin.zhmhotels.online
```

### Check DNS Propagation

```bash
host admin.zhmhotels.online
host api.zhmhotels.online
host player.zhmhotels.online
```

## 🔧 Nginx Commands

```bash
# Check status
sudo systemctl status nginx

# Start/Stop/Restart
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx

# Reload config (without downtime)
sudo systemctl reload nginx

# Test configuration
sudo nginx -t

# View access logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/api.zhmhotels.online.access.log

# View error logs
sudo tail -f /var/log/nginx/error.log
```

## 🔐 SSL Commands

```bash
# View certificates
sudo certbot certificates

# Manual renewal
sudo certbot renew --force-renewal

# Reload Nginx after renewal
sudo systemctl reload nginx

# Test auto-renewal
sudo certbot renew --dry-run
```

## 💾 Database Commands

```bash
# Connect to database
docker exec -it signage-postgres psql -U signage_user -d signage_db

# Quick queries
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT COUNT(*) FROM users;"
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT COUNT(*) FROM devices;"

# Backup database
docker exec signage-postgres pg_dump -U signage_user signage_db > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i signage-postgres psql -U signage_user -d signage_db < backup.sql
```

## 🐛 Quick Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs

# Check specific service
docker logs signage-backend-python

# Restart everything
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

### Domain Not Accessible

```bash
# 1. Check DNS
host admin.zhmhotels.online

# 2. Check Nginx
sudo systemctl status nginx
sudo nginx -t

# 3. Test from server
curl -I http://localhost:8001

# 4. Check MikroTik port forwarding
# From mobile data:
curl -I http://43.247.36.250
```

### SSL Certificate Issues

```bash
# Check certificates
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal
sudo systemctl reload nginx

# Regenerate from scratch
sudo certbot delete --cert-name admin.zhmhotels.online
sudo bash docker/setup-ssl.sh
```

### High Resource Usage

```bash
# Check Docker stats
docker stats --no-stream

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose -f docker/docker-compose.yml restart
```

## 🔑 Default Credentials

```
Username: admin
Password: admin123
```

**Change after first login!**

## 📊 Monitoring

```bash
# Real-time Docker stats
docker stats

# Service logs
docker-compose -f docker/docker-compose.yml logs -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# System resources
htop
```

## 🔄 Environment Variables

### Critical Variables to Update

```env
# In .env file:
DOMAIN=zhmhotels.online
SSL_EMAIL=your-email@example.com
JWT_SECRET_KEY=<generate-random-32-chars>
DATABASE_PASSWORD=<generate-random-password>
```

### Generate Secrets

```bash
# JWT Secret
openssl rand -base64 32

# Database Password
openssl rand -base64 24
```

## 🌐 DNS Setup (Hostinger)

```
Type: A
Name: admin
Points To: 43.247.36.250
TTL: 3600

Type: A
Name: api
Points To: 43.247.36.250
TTL: 3600

Type: A
Name: player
Points To: 43.247.36.250
TTL: 3600
```

## 🔀 MikroTik Port Forwarding

```mikrotik
# Forward Port 80
/ip firewall nat add chain=dstnat protocol=tcp dst-port=80 \
  in-interface=[WAN-interface] action=dst-nat \
  to-addresses=192.168.5.12 to-ports=80

# Forward Port 443
/ip firewall nat add chain=dstnat protocol=tcp dst-port=443 \
  in-interface=[WAN-interface] action=dst-nat \
  to-addresses=192.168.5.12 to-ports=443
```

## ⚠️ Important Notes

1. **Always run docker-compose from project root**:
   ```bash
   # ✅ Correct
   cd /home/gzjbbk/signage
   docker-compose -f docker/docker-compose.yml up -d

   # ❌ Wrong - environment variables won't load!
   cd /home/gzjbbk/signage/docker
   docker-compose up -d
   ```

2. **Never commit .env file to git!**

3. **DNS propagation takes 5-30 minutes** - be patient

4. **Port forwarding must be configured before SSL setup**

5. **HTTP must work before installing SSL**

## 📞 Emergency Contacts

- Domain: Hostinger support
- MikroTik: MikroTik documentation
- SSL: Let's Encrypt community
- Logs: `docker-compose -f docker/docker-compose.yml logs`

## 📚 Full Documentation

- Complete guide: `docker/README.md`
- Deployment checklist: `docker/DEPLOYMENT_CHECKLIST.md`
- MikroTik setup: `/tmp/MIKROTIK_SETUP.md`
- Domain setup: `/tmp/DOMAIN_SETUP_GUIDE.md`

---

**Last Updated**: 2025-01-13
