# Frontend Siap Deploy ke VPS! 🚀

**Date**: 2026-01-11
**Status**: ✅ **READY TO DEPLOY**

---

## ✅ Yang Sudah Siap

### 1. Production Build
```
Build: ✅ SUCCESS
Output: frontend/dist/ (430 KB JS + 12 KB CSS)
TypeScript: ✅ No errors
Optimization: ✅ Gzip enabled
```

### 2. Docker Configuration
```
Dockerfile: ✅ Multi-stage build (Node + Nginx)
nginx.conf: ✅ SPA routing configured
Health check: ✅ /health endpoint
Image size: ~50-80 MB (estimated)
```

### 3. Nomad Job
```
File: nomad/frontend.nomad
Port: 3000 (static)
Service: puguh-frontend
Namespace: puguh
Health checks: ✅ HTTP + TCP
```

### 4. Backend CORS
```
Updated: ✅ nomad/backend-api.nomad
Added: http://31.97.111.175:3000
Added: http://puguh-frontend.service.consul
```

### 5. Deployment Scripts
```
Automated: deploy-frontend-vps.sh ✅
Manual guide: DEPLOY_FRONTEND_MANUAL.md ✅
```

---

## 🚀 Cara Deploy (2 Opsi)

### Opsi A: Automated Script (RECOMMENDED)

```bash
# Make executable
chmod +x deploy-frontend-vps.sh

# Run deployment
./deploy-frontend-vps.sh
```

**Script akan**:
1. Build production bundle
2. Build Docker image
3. Upload ke VPS
4. Deploy via Nomad
5. Show status

**Time**: 5-10 minutes
**Interaction**: Minimal (password SSH saja)

---

### Opsi B: Manual Step-by-Step

Ikuti panduan lengkap di: **`DEPLOY_FRONTEND_MANUAL.md`**

**Steps**:
1. Build bundle: `npm run build`
2. Build image: `docker build -t arsaka-puguh-frontend:phase-a frontend/`
3. Save: `docker save ... | gzip > frontend-image.tar.gz`
4. Upload: `scp frontend-image.tar.gz root@31.97.111.175:/tmp/`
5. SSH & load: `docker load < frontend-image.tar.gz`
6. Deploy: `nomad job run -namespace=puguh frontend.nomad`

**Time**: 10-15 minutes
**Control**: Full manual control setiap step

---

## 📊 Setelah Deploy Berhasil

### Accessible URLs

**Frontend**:
```
http://31.97.111.175:3000/
```

**Expected behavior**:
- ✅ Homepage redirect to `/decisions`
- ✅ Decision List load dengan data dari backend
- ✅ Create form bisa submit
- ✅ Navigation work (Approvals, Audit)
- ✅ No CORS errors
- ✅ No network errors

**Backend** (tetap accessible di port dynamic):
```
http://31.97.111.175:PORT/
```

---

## 🎯 Kenapa Deploy ke VPS?

### Problem Sebelumnya
❌ Frontend di local (WSL) tidak bisa akses backend di VPS
❌ Dynamic port allocation sulit di-track
❌ Network connectivity issues

### Solution: Deploy Kedua-duanya ke VPS
✅ Frontend dan backend di server yang sama
✅ Bisa pakai Consul DNS: `puguh-backend.service.consul`
✅ No network barriers
✅ Accessible dari browser manapun via IP publik

---

## 📁 File Structure Update

```
ARSAKA_PUGUH/
├── frontend/
│   ├── dist/                    ✅ Production build
│   ├── Dockerfile               ✅ NEW
│   ├── nginx.conf               ✅ NEW
│   ├── .env.production          ✅ NEW
│   └── ... (source files)
│
├── nomad/
│   ├── backend-api.nomad        ✅ UPDATED (CORS)
│   └── frontend.nomad           ✅ NEW
│
├── deploy-frontend-vps.sh       ✅ NEW
├── DEPLOY_FRONTEND_MANUAL.md    ✅ NEW
└── FRONTEND_DEPLOYMENT_READY.md ✅ NEW (file ini)
```

---

## ⚙️ Configuration Details

### Frontend Environment (.env.production)
```env
VITE_API_BASE_URL=http://puguh-backend.service.consul:8001
```

**Why Consul DNS?**
- ✅ Service discovery automatic
- ✅ No need to know dynamic port
- ✅ Load balancing ready (for Phase B)

**Alternative** (if Consul not working):
```env
VITE_API_BASE_URL=http://localhost:8001
```

### Backend CORS (nomad/backend-api.nomad)
```env
CORS_ORIGINS = "http://localhost:3000,...,http://31.97.111.175:3000,http://puguh-frontend.service.consul,..."
```

### Nginx Configuration
- **SPA routing**: All routes → `index.html`
- **Gzip**: ✅ Enabled for JS/CSS
- **Caching**: Static assets cached 1 year
- **Health check**: `/health` endpoint

---

## 🔧 Troubleshooting Checklist

### Pre-Deployment
- [ ] SSH access ke VPS works
- [ ] Docker installed di local
- [ ] Docker installed di VPS
- [ ] Nomad accessible di VPS

### During Deployment
- [ ] Build berhasil (no TypeScript errors)
- [ ] Docker image created
- [ ] Image uploaded successfully
- [ ] Image loaded di VPS
- [ ] Nomad job accepted

### Post-Deployment
- [ ] Nomad status = running
- [ ] Health check = healthy
- [ ] Frontend accessible: `http://31.97.111.175:3000/`
- [ ] Backend CORS allows frontend
- [ ] API calls berhasil (no CORS errors)

---

## 📝 Next Steps

### 1. Deploy Frontend
Run salah satu deployment method di atas.

### 2. Verify Deployment
```bash
# Check status
ssh root@31.97.111.175 "nomad job status -namespace=puguh puguh-frontend"

# Test health
curl http://31.97.111.175:3000/health
```

### 3. Update Backend CORS (if needed)
```bash
# Redeploy backend with updated CORS
ssh root@31.97.111.175 "nomad job run -namespace=puguh /path/to/backend-api.nomad"
```

### 4. Test di Browser
Buka: `http://31.97.111.175:3000/`

### 5. E2E Testing
- [ ] Decision List loads
- [ ] Create decision works
- [ ] Navigation works
- [ ] No console errors

---

## 🎉 Success Criteria

**Deployment berhasil jika**:

1. ✅ Frontend accessible via `http://31.97.111.175:3000/`
2. ✅ UI tampil dengan sempurna
3. ✅ Decision List menampilkan data dari backend
4. ✅ Create form bisa submit decision
5. ✅ No CORS errors di browser console
6. ✅ All 5 screens accessible (Decisions, Approvals, Audit)

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `deploy-frontend-vps.sh` | Automated deployment script |
| `DEPLOY_FRONTEND_MANUAL.md` | Manual step-by-step guide |
| `FRONTEND_DEPLOYMENT_READY.md` | This file - deployment summary |
| `frontend/Dockerfile` | Docker image definition |
| `frontend/nginx.conf` | Nginx web server config |
| `nomad/frontend.nomad` | Nomad job specification |

---

## 🚀 Ready to Go!

**Everything is prepared!** Tinggal run deployment script atau follow manual steps.

**Estimated Time**: 5-10 minutes untuk complete deployment.

**After deployment**: Frontend dan backend accessible dari browser manapun! 🎯

---

**Run deployment sekarang?**

```bash
chmod +x deploy-frontend-vps.sh
./deploy-frontend-vps.sh
```

Good luck! 🚀
