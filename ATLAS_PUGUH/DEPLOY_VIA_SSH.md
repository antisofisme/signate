# Deploy Frontend ke VPS - Via SSH Langsung

**Problem**: WSL environment tidak bisa connect ke VPS.
**Solution**: SSH langsung ke VPS, build & deploy di sana.

---

## 🚀 Cara Tercepat (5 Menit)

### Step 1: Upload Files ke VPS

Jalankan dari **Windows PowerShell** atau **Git Bash** (BUKAN WSL):

```bash
cd F:\WINDSURF\neliti_code\signate\ATLAS_PUGUH

# Create tarball
cd frontend
tar czf ../frontend-source.tar.gz src public index.html package.json package-lock.json vite.config.ts tsconfig.json tsconfig.node.json tailwind.config.js postcss.config.js Dockerfile nginx.conf .env.production
cd ..

# Upload to VPS
scp frontend-source.tar.gz root@72.61.209.158:/root/signage/
scp nomad/frontend.nomad root@72.61.209.158:/root/signage/nomad/

# Password: 1(;2-Ur?F)PP73J#G-wW
```

### Step 2: SSH ke VPS

```bash
ssh root@72.61.209.158
# Password: 1(;2-Ur?F)PP73J#G-wW
```

### Step 3: Build & Deploy di VPS

```bash
cd /root/signage

# Extract files
rm -rf frontend-build
mkdir frontend-build
cd frontend-build
tar xzf ../frontend-source.tar.gz

# Build with Docker
echo "Installing dependencies & building..."
docker run --rm -v $(pwd):/app -w /app node:18-alpine sh -c "npm ci && npm run build"

echo "Building Docker image..."
docker build -t atlas-puguh-frontend:phase-a .

# Verify image
docker images | grep atlas-puguh-frontend

# Deploy to Nomad
cd /root/signage
nomad job run nomad/frontend.nomad

# Check status
sleep 5
nomad job status puguh-frontend
```

### Step 4: Verify

```bash
# Check if running
nomad job status puguh-frontend

# Should show:
# Status = running
# Healthy = 1

# Test endpoint
curl http://localhost:3000/health
# Should return: healthy

# Exit VPS
exit
```

### Step 5: Open Browser

```
http://72.61.209.158:3000/
```

**Expected**:
- ✅ Frontend UI muncul
- ✅ Decision List loads dengan data
- ✅ Navigation works
- ✅ No errors!

---

## 🎯 Alternatif: Build Lokal (Tanpa Docker)

Kalau Docker di VPS bermasalah, build manual:

```bash
# Di VPS
cd /root/signage/frontend-build

# Install Node.js (jika belum ada)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Build
npm ci
npm run build

# Serve dengan Nginx manual
apt-get install -y nginx
cp dist/* /var/www/html/
systemctl restart nginx

# Access at port 80
```

---

## 📋 Troubleshooting

### Cannot connect to VPS from Windows

**Check**:
- Firewall Windows allow SSH client
- VPS port 22 open
- Internet connection stable

**Try**:
```bash
ping 72.61.209.158
telnet 72.61.209.158 22
```

### Docker not found on VPS

**Install Docker**:
```bash
# Di VPS
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker
```

### Nomad job failed

**Check logs**:
```bash
nomad job status puguh-frontend
nomad logs -job puguh-frontend
```

**Common issues**:
- Image not found → Build lagi
- Port conflict → Check port 3000 not used
- Health check fail → Check nginx config

### Port 3000 not accessible

**Open firewall**:
```bash
ufw allow 3000/tcp
# Or
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
```

---

## ✅ Quick Reference

**VPS Credentials**:
```
IP: 72.61.209.158
User: root
Password: 1(;2-Ur?F)PP73J#G-wW
```

**Frontend URL**:
```
http://72.61.209.158:3000/
```

**Commands**:
```bash
# Check status
ssh root@72.61.209.158 "nomad job status puguh-frontend"

# View logs
ssh root@72.61.209.158 "nomad logs -job puguh-frontend"

# Restart
ssh root@72.61.209.158 "nomad job restart puguh-frontend"
```

---

## 🎉 Success!

Setelah deploy berhasil:
1. ✅ Buka http://72.61.209.158:3000/
2. ✅ Test semua screen (Decisions, Approvals, Audit)
3. ✅ Verify API calls work
4. ✅ No console errors

**Frontend + Backend sekarang sama-sama di VPS** → Network connectivity issues SOLVED! 🚀
