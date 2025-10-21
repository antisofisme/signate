# Tutorial Deployment Anthias untuk Pemula

Tutorial lengkap instalasi dan konfigurasi Anthias digital signage platform untuk pemula IT.

## 🎯 Apa yang akan kita capai?

Setelah mengikuti tutorial ini, Anda akan memiliki:
- ✅ Server Anthias yang berjalan sempurna
- ✅ Akses via DNS lokal (anthias.local:8000)
- ✅ Custom viewer dengan fitur advanced
- ✅ Dashboard untuk manage konten digital signage

## 📋 Yang perlu disiapkan

### Server Requirements
- **OS**: Ubuntu 22.04 LTS (atau yang lebih baru)
- **RAM**: Minimal 2GB (disarankan 4GB)
- **Storage**: Minimal 10GB free space
- **Network**: Koneksi internet dan akses LAN

### Target Server untuk Tutorial ini
- **IP Address**: 192.168.5.12
- **Username**: gzjbbk
- **OS**: Ubuntu 22.04.4 LTS
- **Docker**: Already installed

## 📚 Struktur Tutorial

1. **[STEP-01-PREREQUISITES.md](STEP-01-PREREQUISITES.md)** - Setup Environment & Prerequisites (Fresh Ubuntu + Verification) ✅
2. **[STEP-02-ANTHIAS-INSTALLATION.md](STEP-02-ANTHIAS-INSTALLATION.md)** - Instalasi Anthias ✅
3. **[STEP-03-MIKROTIK-CONFIGURATION.md](STEP-03-MIKROTIK-CONFIGURATION.md)** - Konfigurasi MikroTik ✅
4. **[STEP-04-CUSTOM-VIEWERS.md](STEP-04-CUSTOM-VIEWERS.md)** - Deploy Custom Viewers ✅
5. **[STEP-05-TESTING.md](STEP-05-TESTING.md)** - Testing dan Troubleshooting ✅

**Status Legend**:
- ✅ = Completed and Tested

**🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!**

**Final Status**: 
- ✅ **All containers running stable** (355MB RAM, <2% CPU)
- ✅ **Custom viewer deployed** (enhanced viewer with horizontal layout)
- ✅ **DNS resolution working** (`anthias.local` via MikroTik DNS)
- ✅ **API endpoints working** correctly
- ✅ **Web interface accessible** via `http://anthias.local:8000`
- ✅ **Custom viewer accessible** via `http://anthias.local:8000/viewer`

**Architecture**: 
- **Production Server**: 192.168.5.12 (Ubuntu 22.04 + Docker)
- **Network Access**: Via MikroTik DNS `anthias.local:8000`
- **Local Development**: Removed (menggunakan production server)

## ⚠️ Penting!

- Setiap command akan dijelaskan dengan detail
- Screenshot disertakan untuk setiap langkah penting
- Troubleshooting untuk masalah umum tersedia
- Tutorial ditulis sambil mengerjakan (real-time)

## 🚀 Mari Mulai!

**Option 1: Quick Deployment** (Recommended)
- Gunakan file yang sudah ready di direktori `anthias-ready-files/`
- Copy files tersebut dan jalankan sesuai instruksi di README

**Option 2: Step by Step Tutorial**
- Ikuti tutorial lengkap dari **STEP-01** hingga selesai
- Cocok untuk memahami detail deployment process

---

*Tutorial ini dibuat bersamaan dengan implementasi aktual untuk memastikan akurasi 100%*