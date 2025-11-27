# 🌐 Panduan Akses Digital Signage

## ✨ Smart Auto-Detection (RECOMMENDED)

**Sistem sekarang sudah menggunakan auto-detect pintar!**

Anda tidak perlu lagi memilih URL manual. Sistem akan otomatis mendeteksi:
- Jika akses dari **LAN** (192.168.x.x) → gunakan HTTP lokal
- Jika akses dari **Internet** (domain) → gunakan HTTPS domain

**Cara menggunakan:**
- CMS: Buka http://192.168.5.12:3000 (dari LAN) ATAU https://admin.zhmhotels.online (dari Internet)
- Player: Buka http://192.168.5.12:8080 (dari LAN) ATAU https://player.zhmhotels.online (dari Internet)

Sistem akan otomatis memilih API URL yang tepat berdasarkan lokasi Anda!

---

## Untuk Staff/Tim di Kantor (Jaringan Lokal)

Gunakan **IP Lokal** untuk performa terbaik:

### CMS Admin
```
URL: http://192.168.5.12:3000
Login: admin / admin123
```

### Player (Display)
```
URL: http://192.168.5.12:8080
```

**Keuntungan:**
- ⚡ Lebih cepat (akses langsung)
- 🔒 Lebih stabil (tidak bergantung internet)
- ✅ Tidak ada masalah NAT/routing

---

## Untuk Client/Remote (Akses dari Luar)

Gunakan **Domain HTTPS** untuk keamanan:

### CMS Admin
```
URL: https://admin.zhmhotels.online
Login: admin / admin123
```

### Player (Display)
```
URL: https://player.zhmhotels.online
```

**Keuntungan:**
- 🔐 Terenkripsi & aman
- 🌍 Bisa diakses dari mana saja
- ✨ URL profesional

---

## Troubleshooting

### Jika HTTPS dari kantor kadang timeout:
1. **Gunakan IP lokal HTTP** (recommended)
2. Atau setup DNS override di router:
   - Login router → DNS Settings
   - Tambah: `admin.zhmhotels.online → 192.168.5.12`
   - Tambah: `player.zhmhotels.online → 192.168.5.12`

### Jika tidak bisa akses dari luar:
1. Pastikan internet stabil
2. Check Cloudflare tunnel status
3. Hubungi IT support

### Penjelasan Teknis

**Kenapa HTTPS dari LAN kadang gagal?**

Masalah: **NAT Hairpinning**
```
Device di LAN → Domain HTTPS → Keluar router → Internet
            → Cloudflare → Harus balik lagi ke router
            → Router mungkin tidak support "hairpin" routing
            → Kadang timeout/gagal
```

**Solusi:**
```
Device di LAN → IP Lokal HTTP → Langsung ke server
            → Lebih cepat, lebih reliable
```

---

## Best Practice

| Lokasi | URL yang Digunakan | Alasan |
|--------|-------------------|--------|
| 🏢 Kantor | `http://192.168.5.12:3000` | Cepat & stabil |
| 🌐 Remote | `https://admin.zhmhotels.online` | Aman & accessible |
| 📱 Mobile/Demo | `https://admin.zhmhotels.online` | Professional |
| 🖥️ Display/TV | `http://192.168.5.12:8080` | Cepat (jika di kantor) |
| 🖥️ Display/TV Remote | `https://player.zhmhotels.online` | Jika di lokasi lain |

---

## Technical Details

### Current Setup
- **Backend API**: Port 8001 (HTTP lokal) / HTTPS domain
- **CMS Admin**: Port 3000 (HTTP lokal) / HTTPS domain
- **Player**: Port 8080 (HTTP lokal) / HTTPS domain
- **SSL**: Cloudflare managed certificates
- **Reverse Proxy**: Nginx

### Network Diagram
```
┌─────────────────────────────────────────┐
│         INTERNAL ACCESS (LAN)           │
├─────────────────────────────────────────┤
│ Browser → http://192.168.5.12:3000     │
│         → Direct to server ✅           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│        EXTERNAL ACCESS (Internet)       │
├─────────────────────────────────────────┤
│ Browser → https://admin.zhmhotels.online│
│         → Cloudflare → Router → Server  │
│         → Encrypted & secure ✅         │
└─────────────────────────────────────────┘
```

---

**Dibuat**: 2025-11-25
**Update terakhir**: 2025-11-25
