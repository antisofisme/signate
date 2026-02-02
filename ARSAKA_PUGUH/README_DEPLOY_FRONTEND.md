# 🚀 Deploy Frontend ARSAKA_PUGUH ke VPS

**Status**: ✅ READY TO DEPLOY
**VPS**: 72.61.209.158
**Frontend Port**: 3000

---

## ⚡ Quick Deploy (1 Command)

### Dari Windows PowerShell atau Git Bash:

```bash
cd F:\WINDSURF\neliti_code\signage\ARSAKA_PUGUH

chmod +x DEPLOY_FRONTEND_FINAL.sh

./DEPLOY_FRONTEND_FINAL.sh
```

**Script akan otomatis**:
1. Create source package
2. Upload ke VPS
3. Build Docker image di VPS
4. Deploy via Nomad
5. Show deployment status

**Total waktu**: 5-10 menit

**Password sudah embedded** - tidak perlu input manual!

---

## 📋 Manual Deployment (Step-by-Step)

Jika script gagal atau ingin kontrol penuh:

### Step 1: Create Package

```bash
cd F:\WINDSURF\neliti_code\signage\ARSAKA_PUGUH\frontend

tar czf ../frontend-source.tar.gz \
    src public index.html \
    package.json package-lock.json \
    vite.config.ts tsconfig.json tsconfig.node.json \
    tailwind.config.js postcss.config.js \
    Dockerfile nginx.conf .env.production

cd ..
```

### Step 2: Upload to VPS

```bash
# Upload source
scp frontend-source.tar.gz root@72.61.209.158:/root/signage/

# Upload Nomad job
scp nomad/frontend.nomad root@72.61.209.158:/root/signage/nomad/

# Password: Bait174663@vps
```

### Step 3: SSH to VPS

```bash
ssh root@72.61.209.158
# Password: Bait174663@vps
```

### Step 4: Build on VPS

```bash
cd /root/signage

# Extract
rm -rf frontend-build
mkdir frontend-build
cd frontend-build
tar xzf ../frontend-source.tar.gz

# Install & build
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm ci
docker run --rm -v $(pwd):/app -w /app node:18-alpine npm run build

# Build image
docker build -t arsaka-puguh-frontend:phase-a .

# Verify
docker images | grep arsaka-puguh-frontend
```

### Step 5: Deploy to Nomad

```bash
cd /root/signage

# Run deployment
nomad job run nomad/frontend.nomad

# Check status
sleep 5
nomad job status puguh-frontend

# Should show: Status = running, Healthy = 1
```

### Step 6: Test

```bash
# Health check
curl http://localhost:3000/health
# Expected: healthy

# Exit VPS
exit
```

### Step 7: Open Browser

```
http://72.61.209.158:3000/
```

---

## ✅ Success Criteria

Deployment berhasil jika:

1. ✅ Nomad job status = `running`
2. ✅ Healthy count = `1`
3. ✅ Health check returns `healthy`
4. ✅ Browser shows frontend UI
5. ✅ Decision List loads with data
6. ✅ No CORS errors in console
7. ✅ All navigation works

---

## 🔧 Troubleshooting

### Cannot connect to VPS

**Check**:
```bash
ping 72.61.209.158
telnet 72.61.209.158 22
```

**If blocked**: Check firewall/network settings

### Docker not available on VPS

**Install Docker**:
```bash
ssh root@72.61.209.158
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker
```

### Build failed

**Check logs**:
```bash
ssh root@72.61.209.158
cd /root/signage/frontend-build
npm install
npm run build
```

**Common issues**:
- Node modules corrupted → Delete node_modules, run `npm ci`
- TypeScript errors → Check source files
- Out of memory → Increase VPS RAM

### Nomad deployment failed

**Check logs**:
```bash
ssh root@72.61.209.158
nomad job status puguh-frontend
nomad logs -job puguh-frontend
```

**Common issues**:
- Image not found → Rebuild image
- Port conflict → Kill process on port 3000
- Health check timeout → Check nginx config

### Port 3000 not accessible

**Open firewall**:
```bash
ssh root@72.61.209.158

# UFW
ufw allow 3000/tcp

# Or iptables
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
iptables-save > /etc/iptables/rules.v4
```

### Frontend loads but API fails

**Check backend CORS**:
```bash
ssh root@72.61.209.158
nomad job status puguh-backend

# Verify CORS includes frontend URL
nomad job inspect puguh-backend | grep CORS_ORIGINS
```

**Should include**: `http://72.61.209.158:3000`

If not, update backend:
```bash
# Edit backend Nomad job
nano /root/signage/nomad/backend-api.nomad

# Add to CORS_ORIGINS:
CORS_ORIGINS = "....,http://72.61.209.158:3000,..."

# Redeploy
nomad job run /root/signage/nomad/backend-api.nomad
```

---

## 📊 Post-Deployment Checks

### 1. Nomad Status

```bash
ssh root@72.61.209.158 'nomad job status puguh-frontend'
```

**Expected**:
```
Status        = running
Desired       = 1
Placed        = 1
Running       = 1
Healthy       = 1
```

### 2. Health Check

```bash
curl http://72.61.209.158:3000/health
```

**Expected**: `healthy`

### 3. Browser Test

Open: `http://72.61.209.158:3000/`

**Test checklist**:
- [ ] Frontend UI loads
- [ ] Decision List shows data
- [ ] Create decision form submits
- [ ] Approval inbox accessible
- [ ] Audit trail accessible
- [ ] No console errors
- [ ] Navigation works

---

## 🔑 VPS Credentials

```
IP:       72.61.209.158
User:     root
Password: Bait174663@vps
SSH:      ssh root@72.61.209.158
```

---

## 📁 Files Created

All files ready in: `F:\WINDSURF\neliti_code\signage\ARSAKA_PUGUH\`

| File | Purpose |
|------|---------|
| `DEPLOY_FRONTEND_FINAL.sh` | Automated deployment script |
| `README_DEPLOY_FRONTEND.md` | This file - deployment guide |
| `frontend/dist/` | Production build (430 KB) |
| `frontend/Dockerfile` | Docker image specification |
| `frontend/nginx.conf` | Nginx web server config |
| `nomad/frontend.nomad` | Nomad deployment job |

---

## 🎯 Next Steps

1. **Run deployment**:
   ```bash
   cd F:\WINDSURF\neliti_code\signage\ARSAKA_PUGUH
   ./DEPLOY_FRONTEND_FINAL.sh
   ```

2. **Verify deployment**:
   ```bash
   curl http://72.61.209.158:3000/health
   ```

3. **Test in browser**:
   ```
   http://72.61.209.158:3000/
   ```

4. **E2E testing**:
   - Create decision
   - Check approval inbox
   - View audit trail

---

## 🎉 Success!

After successful deployment:

✅ **Frontend**: http://72.61.209.158:3000/
✅ **Backend**: http://72.61.209.158:PORT/ (dynamic)
✅ **Both running on VPS** → No network issues!
✅ **Accessible from any browser** → Public deployment!

---

**Ready to deploy!** Run the script now! 🚀
