# 🚀 Deploy Frontend ke VPS SEKARANG

**Script sudah SIAP!** Tinggal jalankan dengan password VPS Anda.

---

## ▶️ Cara Deploy (1 Command)

```bash
cd /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH

./deploy-frontend-direct.sh
```

**Password VPS akan diminta 3x**:
1. Saat upload files
2. Saat build Docker image
3. Saat deploy Nomad job

**Total waktu**: ~5-10 menit

---

## 📊 Yang Akan Terjadi:

### Step 1: Preparing Files (10 detik)
```
📦 Mengumpulkan semua file frontend
✅ Files prepared
```

### Step 2: Upload ke VPS (30 detik - 1 menit)
```
🚀 Upload source code ke VPS
Password: [ketik password VPS]
✅ Files uploaded
```

### Step 3: Build di VPS (3-5 menit)
```
🐳 Build Docker image di VPS
Password: [ketik password VPS]
- Installing dependencies...
- Building production bundle...
- Building Docker image...
✅ Docker image built
```

### Step 4: Upload Nomad Job (5 detik)
```
📋 Upload konfigurasi Nomad
✅ Nomad job uploaded
```

### Step 5: Deploy ke Nomad (30 detik)
```
🎯 Deploy frontend
Password: [ketik password VPS]
- Starting deployment...
- Allocating resources...
- Running health checks...
✅ DEPLOYMENT COMPLETE!
```

---

## ✅ Setelah Selesai

**Anda akan lihat output seperti ini**:

```
==========================================
✅ DEPLOYMENT COMPLETE!
==========================================

Frontend accessible at:
  http://31.97.111.175:3000/

To check status:
  ssh root@31.97.111.175 'nomad job status -namespace=puguh puguh-frontend'

To view logs:
  ssh root@31.97.111.175 'nomad logs -namespace=puguh -job puguh-frontend'
```

**Langsung buka browser**:
```
http://31.97.111.175:3000/
```

**Expected**:
- ✅ Decision List muncul dengan data
- ✅ Create form bisa submit
- ✅ Semua navigation work
- ✅ No CORS errors

---

## 🐛 Troubleshooting

### "Permission denied" saat SSH

**Pastikan password VPS benar**: Check di credentials Anda

### Build gagal - "Cannot find module"

**Jalankan ulang script** - kadang npm install perlu retry

### Nomad job failed

**Check logs**:
```bash
ssh root@31.97.111.175
nomad job status -namespace=puguh puguh-frontend
nomad logs -namespace=puguh -job puguh-frontend
```

### Port 3000 tidak accessible

**Buka firewall VPS**:
```bash
ssh root@31.97.111.175
ufw allow 3000/tcp
# Atau
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
```

---

## 🔄 Jika Perlu Redeploy

Update code → Jalankan script lagi:

```bash
./deploy-frontend-direct.sh
```

Script akan:
- Upload file terbaru
- Rebuild image
- Restart Nomad job

---

## 📝 Password VPS

**VPS IP**: 31.97.111.175
**User**: root
**Password**: [Lihat di credentials Anda]

---

## ⚡ Quick Start

**Copy-paste command ini**:

```bash
cd /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH && ./deploy-frontend-direct.sh
```

**Ketik password saat diminta** (3x total)

**Wait 5-10 minutes**

**Open browser**: http://31.97.111.175:3000/

**DONE!** ✅

---

Ready untuk deploy? Run command di atas sekarang! 🚀
