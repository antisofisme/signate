# Cara Connect Frontend ke Backend VPS

**Masalah**: Frontend tidak bisa connect ke backend karena port salah.

**Penyebab**: Nomad pakai dynamic port allocation - port 30934 sudah tidak valid.

**Solusi**: Cari port yang benar, lalu update `.env`

---

## 📋 Step-by-Step (5 Menit)

### 1. SSH ke VPS

```bash
ssh root@31.97.111.175
# Password: <password VPS kamu>
```

### 2. Cari Port Backend

Jalankan command ini di VPS:

```bash
nomad job status -namespace=puguh puguh-backend
```

**Cari bagian "Allocations"**, scroll ke kanan untuk lihat kolom **"Ports"**.

Contoh output:
```
Allocations
ID        Node     Version  Desired  Status   ... Ports
abc123    node1    0        run      running  ... http=32768:8001
                                                   ^^^^^^^^
                                         INI PORT VPS YANG BENAR!
```

**Format**: `http=HOST_PORT:CONTAINER_PORT`
- `32768` = Port di VPS (yang kita butuhkan)
- `8001` = Port di container

**Catat port HOST_PORT nya!** (contoh: 32768)

### 3. Test Port dari Local

Keluar dari SSH (ketik `exit`), lalu test dari local:

```bash
# Ganti 32768 dengan port yang kamu dapat
curl http://31.97.111.175:32768/health
```

**Expected response**:
```json
{"status":"healthy","service":"puguh-backend","phase":"a"}
```

Kalau dapat response ini → **PORT BENAR!** ✅

Kalau timeout → coba port lain atau check firewall VPS.

### 4. Update Frontend .env

Edit file `frontend/.env`:

```bash
# Ganti PORT dengan port yang kamu dapat
VITE_API_BASE_URL=http://31.97.111.175:PORT

# Contoh (kalau port adalah 32768):
VITE_API_BASE_URL=http://31.97.111.175:32768
```

### 5. Restart Dev Server

```bash
# Stop dev server (Ctrl+C di terminal yang jalankan npm run dev)
# Atau kill process:
pkill -f "vite"

# Start ulang
cd frontend
npm run dev
```

### 6. Test di Browser

Buka: http://localhost:5173/

**Seharusnya sekarang**:
- ✅ Decision List load dengan data dari database
- ✅ Create form bisa submit
- ✅ Semua screen functional

---

## 🔧 Troubleshooting

### Port Tidak Ketemu di Output Nomad

**Coba command ini**:
```bash
nomad alloc status -namespace=puguh <ALLOC_ID>

# ALLOC_ID ada di kolom pertama output `nomad job status`
```

Cari bagian **"Allocated Resources"** → **"Ports"**

### Port Ketemu Tapi Curl Timeout

**Kemungkinan**: Firewall VPS block port

**Fix**: Buka port di firewall
```bash
# Di VPS (kalau pakai ufw)
sudo ufw allow 32768/tcp

# Atau kalau pakai iptables
sudo iptables -A INPUT -p tcp --dport 32768 -j ACCEPT
```

### Multiple Allocations

Kalau ada lebih dari 1 allocation, pilih yang **Status = running** dan **Desired = run**

### Backend Tidak Healthy

Check logs:
```bash
nomad logs -namespace=puguh -job puguh-backend
```

Look for errors.

---

## 🎯 Alternatif: Pakai Static Port

**Kalau tidak mau cari-cari port setiap redeploy**, set static port:

### Edit Nomad Job

Edit file `nomad/backend-api.nomad`, line 26-29:

```hcl
network {
  mode = "bridge"
  port "http" {
    to = 8001
    static = 30934  # Tambah line ini
  }
}
```

### Redeploy

```bash
nomad job run -namespace=puguh nomad/backend-api.nomad
```

**Sekarang port SELALU 30934!** Tidak berubah-ubah lagi.

Update `.env`:
```env
VITE_API_BASE_URL=http://31.97.111.175:30934
```

---

## 📝 Quick Reference

**VPS IP**: `31.97.111.175`

**Command untuk cek port**:
```bash
ssh root@31.97.111.175 "nomad job status -namespace=puguh puguh-backend" | grep -A 20 Allocations
```

**Test backend**:
```bash
curl http://31.97.111.175:PORT/health
curl http://31.97.111.175:PORT/api/decisions?limit=2
```

**Frontend .env**:
```env
VITE_API_BASE_URL=http://31.97.111.175:PORT
```

**Restart frontend**:
```bash
pkill -f vite
cd frontend && npm run dev
```

---

**Setelah port benar** → Everything will just work! ✅

Mau saya buatkan script otomatis untuk cari port dan update .env?
