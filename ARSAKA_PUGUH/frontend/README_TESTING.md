# Phase A+ - Panduan Testing Frontend

**Status**: ✅ Frontend SIAP, ⚠️ Backend tidak accessible dari local

---

## ✅ Yang Sudah Berhasil

### Dev Server Berjalan
```
Frontend Dev Server: http://localhost:5173/
Status: ✅ RUNNING
```

### Semua Screen Sudah Dibuat
1. **Decision List** - `/decisions`
2. **Create Form** - `/decisions/new`
3. **Decision Detail** - `/decisions/:id`
4. **Approval Inbox** - `/approvals`
5. **Audit Trail** - `/audit`

---

## ⚠️ Masalah Saat Ini: Backend Tidak Accessible

### Gejala
Ketika buka http://localhost:5173/, frontend akan loading terus atau menampilkan error:
- "Error loading decisions"
- "Network Error"
- "Failed to fetch"

### Penyebab
Backend API di VPS (http://31.97.111.175:30934) **TIDAK BISA diakses** dari environment ini karena:
1. Nomad menggunakan **dynamic port allocation**
2. Port 30934 kemungkinan sudah berubah
3. Tidak ada tunnel/proxy ke VPS

---

## 🔧 Cara Memperbaiki (Pilih Salah Satu)

### ✅ Solusi 1: Deploy Backend di Local (RECOMMENDED)

Cara tercepat untuk testing adalah jalankan backend di local machine:

```bash
# 1. Navigate ke backend directory
cd /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH/backend

# 2. Install dependencies (jika belum)
pip install -r requirements.txt

# 3. Setup environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/arsaka_puguh"
export JWT_SECRET_KEY="test-secret-key-phase-a"
export ENVIRONMENT="local-dev"

# 4. Run backend
uvicorn core.app:app --host 0.0.0.0 --port 8001 --reload

# Backend akan jalan di: http://localhost:8001
```

**Kemudian restart frontend dev server** (sudah configure pakai localhost:8001)

---

### ✅ Solusi 2: Gunakan Mock Data (Testing UI Saja)

Jika hanya ingin test UI tanpa backend real, saya bisa tambahkan mock data:

```bash
# Saya bisa membuat mock API responses untuk testing
# Frontend akan pakai data dummy tapi UI tetap bisa dilihat
```

Mau saya buatkan mock data sekarang? (Y/n)

---

### ✅ Solusi 3: SSH Tunnel ke VPS

Jika backend HARUS dari VPS, buat SSH tunnel:

```bash
# 1. Find actual backend port di VPS
ssh user@31.97.111.175 "nomad job status -namespace=puguh puguh-backend"

# 2. Create SSH tunnel (contoh port 32768)
ssh -L 8001:localhost:32768 user@31.97.111.175

# 3. Backend akan accessible di http://localhost:8001
```

---

### ✅ Solusi 4: Deploy via Docker Compose (Paling Mudah)

Jika ada Docker Compose config:

```bash
cd /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH
docker-compose up -d

# Backend + Database akan jalan di local
# Update .env kalau perlu
```

---

## 🧪 Cara Testing Setelah Backend Jalan

### 1. Buka Browser
```
http://localhost:5173/
```

### 2. Test Decision List
- Klik "Decisions" di header
- Seharusnya muncul tabel (atau empty state jika DB kosong)
- Coba sort dengan click column headers

### 3. Test Create Form
- Klik "Create Decision" button
- Isi form:
  - Decision Type: purchase_request
  - Amount: 5000
  - Description: Test decision
- Klik Submit
- Harusnya muncul success message

### 4. Test Navigation
- Dari list, klik salah satu row → masuk ke detail
- Klik "Approvals" → lihat pending approvals
- Klik "Audit" → lihat audit trail

---

## 📊 Expected Behavior

### Jika Backend JALAN (✅):
- Decision List: Menampilkan data dari database
- Create Form: Bisa submit dan dapat response
- Decision Detail: Menampilkan full info decision
- Approval Inbox: Menampilkan pending workflows
- Audit Trail: Menampilkan events (atau empty state)

### Jika Backend TIDAK JALAN (⚠️):
- Decision List: Error message "Error loading decisions"
- Create Form: Submit button tidak berhasil, error network
- Decision Detail: Error loading
- Approval Inbox: Error loading
- Audit Trail: Error loading

**Frontend sudah handle error dengan baik** - akan muncul error message yang jelas.

---

## 🐛 Troubleshooting

### Frontend tidak muncul / blank screen
**Check browser console** (F12):
- Lihat error message
- Biasanya CORS atau network error

### API calls failed dengan CORS error
**Update backend CORS settings**:
```python
# Di backend, tambahkan localhost:5173 ke CORS_ORIGINS
CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
```

### Loading terus tanpa error
**Check Network tab** di browser DevTools:
- Klik Network tab
- Reload page
- Lihat request mana yang stuck
- Biasanya request ke `/api/decisions` timeout

---

## 🎯 Recommended Testing Flow

**Untuk Testing UI (Tanpa Backend)**:
1. Gunakan mock data (saya bisa buatkan)
2. Semua UI bisa dilihat dan di-interact
3. Tidak bisa submit data real

**Untuk Testing Full E2E**:
1. Deploy backend di local (paling simple)
2. Test complete decision lifecycle
3. Verify API integration

---

## 📝 Current Config

**Frontend `.env`**:
```env
VITE_API_BASE_URL=http://localhost:8001
```

**Vite Proxy**:
- Sudah configured untuk proxy `/api/*` ke backend
- Akan log error jika backend unreachable

**Port**:
- Frontend: 5173
- Backend (expected): 8001

---

## 💡 Next Steps

**Pilihan 1**: Saya buatkan mock data untuk testing UI

**Pilihan 2**: Anda deploy backend di local untuk testing full

**Pilihan 3**: Kita fix VPS backend connection dengan SSH tunnel

**Mana yang mau dicoba dulu?**

---

**Frontend Dev Server**: http://localhost:5173/ ✅ **RUNNING**
**Backend API**: ⚠️ **NEEDS CONFIGURATION**

Silakan pilih solusi mana yang paling cocok untuk environment Anda!
