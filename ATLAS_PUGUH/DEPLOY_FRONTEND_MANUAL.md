# Deploy Frontend ke VPS - Manual Steps

**Target**: Deploy frontend ATLAS_PUGUH Phase A+ ke VPS untuk accessibility dari browser.

**Benefit**: Frontend dan backend sama-sama di VPS → No network connectivity issues!

---

## 🚀 Opsi 1: Automated Deployment (RECOMMENDED)

### Prerequisites
- SSH access ke VPS (root@31.97.111.175)
- Docker installed di local machine
- Script sudah ada: `deploy-frontend-vps.sh`

### Run Deployment

```bash
cd /mnt/f/WINDSURF/neliti_code/signate/ATLAS_PUGUH

# Make script executable
chmod +x deploy-frontend-vps.sh

# Run deployment
./deploy-frontend-vps.sh
```

**Script akan**:
1. Build production bundle (`npm run build`)
2. Build Docker image
3. Save image as tar.gz
4. Upload ke VPS
5. Load image di VPS
6. Deploy via Nomad
7. Show deployment status

**Total time**: ~5-10 minutes

---

## 📝 Opsi 2: Manual Deployment (Step-by-Step)

### Step 1: Build Production Bundle

```bash
cd frontend
npm run build

# Output: dist/ folder
```

### Step 2: Build Docker Image Locally

```bash
# Di root project
cd /mnt/f/WINDSURF/neliti_code/signate/ATLAS_PUGUH/frontend

docker build -t atlas-puguh-frontend:phase-a .

# Verify image built
docker images | grep atlas-puguh-frontend
```

### Step 3: Save Docker Image

```bash
cd ..
docker save atlas-puguh-frontend:phase-a | gzip > frontend-image.tar.gz

# Check file size
ls -lh frontend-image.tar.gz
```

### Step 4: Upload ke VPS

```bash
# Upload image
scp frontend-image.tar.gz root@31.97.111.175:/tmp/

# Upload Nomad job
scp nomad/frontend.nomad root@31.97.111.175:/tmp/
```

### Step 5: Load Image di VPS

```bash
# SSH ke VPS
ssh root@31.97.111.175

# Load Docker image
cd /tmp
docker load < frontend-image.tar.gz

# Verify
docker images | grep atlas-puguh-frontend

# Should show:
# REPOSITORY              TAG       IMAGE ID       CREATED         SIZE
# atlas-puguh-frontend    phase-a   xxxxx          x minutes ago   xx MB
```

### Step 6: Deploy ke Nomad

```bash
# Masih di VPS
nomad job run -namespace=puguh /tmp/frontend.nomad

# Monitor deployment
nomad job status -namespace=puguh puguh-frontend

# Wait sampai status = running, healthy = 1
```

### Step 7: Verify Deployment

```bash
# Check allocation
nomad job status -namespace=puguh puguh-frontend

# Output:
# Allocations
# ID        Node     ... Status   ...
# abc123    node1    ... running  ...

# Test endpoint
curl http://localhost:3000/health
# Should return: healthy

# Exit VPS
exit
```

### Step 8: Test dari Browser

Buka browser, akses:
```
http://31.97.111.175:3000/
```

**Expected**:
- ✅ Frontend load dengan UI lengkap
- ✅ Decision List page muncul
- ✅ Navigation work
- ✅ API calls ke backend berhasil (karena sama-sama di VPS)

---

## 🔧 Troubleshooting

### Docker build gagal - "Cannot find module"

**Fix**: Install dependencies dulu
```bash
cd frontend
npm install
npm run build
```

### Docker image terlalu besar

**Expected size**: ~50-80 MB (setelah gzip)

Kalau lebih besar, cek:
```bash
docker images atlas-puguh-frontend:phase-a
```

### Upload gagal - Connection timeout

**Fix**: Check SSH access
```bash
ssh root@31.97.111.175
```

Pastikan bisa login.

### Nomad job failed - "Image not found"

**Verify** image ada di VPS:
```bash
ssh root@31.97.111.175 "docker images | grep atlas-puguh-frontend"
```

Kalau tidak ada, repeat Step 5.

### Frontend load tapi API calls failed

**Check backend CORS**:
```bash
ssh root@31.97.111.175 "nomad job status -namespace=puguh puguh-backend"
```

Backend harus running dulu.

**Check CORS config** di `nomad/backend-api.nomad`:
```
CORS_ORIGINS = "...http://31.97.111.175:3000..."
```

Kalau CORS belum ada, update backend:
```bash
# Update backend Nomad job dengan CORS baru
nomad job run -namespace=puguh nomad/backend-api.nomad
```

### Port 3000 tidak accessible dari browser

**Check firewall VPS**:
```bash
ssh root@31.97.111.175

# Allow port 3000
ufw allow 3000/tcp

# Or iptables
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
```

**Check Nomad allocation**:
```bash
nomad job status -namespace=puguh puguh-frontend

# Pastikan Port = 3000 (static)
```

---

## 📊 Post-Deployment Checklist

### Backend Ready
- [ ] Backend running di VPS
- [ ] CORS updated untuk allow frontend IP
- [ ] Backend health check pass: `http://31.97.111.175:PORT/health`

### Frontend Deployed
- [ ] Docker image built & loaded
- [ ] Nomad job status = running
- [ ] Health check pass: `http://31.97.111.175:3000/health`
- [ ] Allocation healthy = 1

### Integration Test
- [ ] Browser access: `http://31.97.111.175:3000/`
- [ ] Decision List loads data from backend
- [ ] Create form can submit
- [ ] Navigation works
- [ ] No CORS errors in browser console

---

## 🎯 Expected URLs

Setelah deployment berhasil:

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | `http://31.97.111.175:3000/` | ✅ Public |
| **Backend API** | `http://31.97.111.175:PORT/` | ⚠️ Dynamic port |
| **Backend (Consul)** | `http://puguh-backend.service.consul:8001/` | ✅ Internal |

**Frontend ENV**:
```env
# Karena sama-sama di VPS, pakai Consul DNS
VITE_API_BASE_URL=http://puguh-backend.service.consul:8001
```

Atau alternatif jika Consul tidak work:
```env
# Pakai localhost (karena same server)
VITE_API_BASE_URL=http://localhost:8001
```

---

## 🔄 Update/Redeploy

Kalau ada perubahan code:

```bash
# 1. Rebuild
cd frontend
npm run build
cd ..
docker build -t atlas-puguh-frontend:phase-a frontend/

# 2. Save & upload
docker save atlas-puguh-frontend:phase-a | gzip > frontend-image.tar.gz
scp frontend-image.tar.gz root@31.97.111.175:/tmp/

# 3. Reload di VPS
ssh root@31.97.111.175 "docker load < /tmp/frontend-image.tar.gz"

# 4. Restart Nomad job
ssh root@31.97.111.175 "nomad job restart -namespace=puguh puguh-frontend"
```

---

## 📚 Useful Commands

```bash
# Check frontend logs
ssh root@31.97.111.175 "nomad logs -namespace=puguh -job puguh-frontend"

# Check allocation details
ssh root@31.97.111.175 "nomad alloc status -namespace=puguh <ALLOC_ID>"

# Restart frontend
ssh root@31.97.111.175 "nomad job restart -namespace=puguh puguh-frontend"

# Stop frontend
ssh root@31.97.111.175 "nomad job stop -namespace=puguh puguh-frontend"

# Remove old images (cleanup)
ssh root@31.97.111.175 "docker image prune -a"
```

---

**Ready to deploy!** 🚀

Choose automated script or follow manual steps above.
