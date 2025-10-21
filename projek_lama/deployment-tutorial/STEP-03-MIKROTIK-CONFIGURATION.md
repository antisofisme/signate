# STEP 3: Konfigurasi MikroTik untuk Anthias

## 🎯 Apa yang akan kita lakukan?

Di step ini kita akan:
1. Setup DNS record di MikroTik untuk `anthias.local`
2. Configure port forwarding jika diperlukan
3. Setup firewall rules untuk akses Anthias
4. Test konektivitas dari berbagai devices

## 📋 MikroTik Configuration

### 1. Akses MikroTik WebFig/WinBox

**Option 1: Via WebFig (Browser)**
```
http://192.168.x.1 (atau IP gateway MikroTik)
Username: admin
Password: [sesuai konfigurasi]
```

**Option 2: Via WinBox**
- Download WinBox dari mikrotik.com
- Connect ke IP MikroTik
- Login dengan credentials

### 2. Setup DNS Record untuk anthias.local

**Via WebFig**:
1. Go to **IP → DNS**
2. Click **Static** tab
3. Add new static DNS entry:
   - **Name**: `anthias.local`
   - **Address**: `192.168.5.12`
   - **TTL**: `1d` (1 day)

**Via Terminal/SSH**:
```bash
/ip dns static
add name=anthias.local address=192.168.5.12 ttl=1d
```

**Verification**:
```bash
/ip dns static print
```

Expected output:
```
0  anthias.local  192.168.5.12  1d
```

### 3. Enable DNS Service (jika belum aktif)

**Check current DNS settings**:
```bash
/ip dns print
```

**Enable DNS service jika disabled**:
```bash
/ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1
```

**Verification**:
```bash
/ip dns cache print where name~"anthias"
```

### 4. Configure Firewall Rules

**Allow HTTP traffic to Anthias server**:
```bash
/ip firewall filter
add chain=forward dst-address=192.168.5.12 dst-port=8000 protocol=tcp action=accept comment="Allow HTTP to Anthias"
```

**Allow SSH to Anthias server (untuk maintenance)**:
```bash
/ip firewall filter
add chain=forward dst-address=192.168.5.12 dst-port=22 protocol=tcp action=accept comment="Allow SSH to Anthias"
```

**Check firewall rules**:
```bash
/ip firewall filter print where comment~"Anthias"
```

### 5. Port Forwarding (Jika Akses dari Internet)

**Jika ingin akses dari internet ke Anthias**:
```bash
/ip firewall nat
add chain=dstnat dst-port=8000 protocol=tcp action=dst-nat to-addresses=192.168.5.12 to-ports=8000 comment="Port forward to Anthias"
```

⚠️ **Security Warning**: Expose ke internet hanya jika diperlukan dan dengan proper security!

### 6. DHCP Client Options (Optional)

**Untuk auto-distribute anthias.local ke DHCP clients**:
```bash
/ip dhcp-server option
add name=anthias-dns code=6 value="'192.168.5.12'"

/ip dhcp-server network
set [find] dns-server=192.168.5.12,8.8.8.8
```

## 🧪 Testing Konfigurasi

### 1. Test DNS Resolution dari MikroTik

**Via MikroTik terminal**:
```bash
/tool nslookup anthias.local
```

**Expected output**:
```
Server: 8.8.8.8
Address: 192.168.5.12
```

### 2. Test dari Komputer Client

**Windows (Command Prompt)**:
```cmd
nslookup anthias.local
ping anthias.local
```

**Linux/Mac**:
```bash
dig anthias.local
ping -c 3 anthias.local
```

**Expected result**: `anthias.local` resolve ke `192.168.5.12`

### 3. Test Web Access

**From browser on any device di network**:
```
http://anthias.local:8000
```

**Expected**: Anthias dashboard terbuka tanpa issues

### 4. Test dari Mobile Devices

**Connect smartphone/tablet ke WiFi yang sama**:
1. Open browser
2. Navigate to `http://anthias.local:8000`
3. Verify dashboard loads properly
4. Test viewer interfaces

## 📱 Alternative Access Methods

### 1. QR Code untuk Easy Access

Generate QR code untuk `http://anthias.local:8000`:
```
[QR CODE PLACEHOLDER]
http://anthias.local:8000
```

### 2. Bookmark/Shortcut Setup

**Chrome/Edge**: Add to home screen
**Safari**: Add to home screen
**Firefox**: Create bookmark

### 3. Local hosts file (Fallback)

**Jika DNS tidak work di device tertentu**:

**Windows** (`C:\Windows\System32\drivers\etc\hosts`):
```
192.168.5.12    anthias.local
```

**Linux/Mac** (`/etc/hosts`):
```
192.168.5.12    anthias.local
```

## 🔧 Troubleshooting

### Problem: anthias.local tidak resolve

**Solution 1**: Check MikroTik DNS
```bash
/ip dns static print
/ip dns print
```

**Solution 2**: Check client DNS settings
```bash
ipconfig /all  # Windows
cat /etc/resolv.conf  # Linux
```

**Solution 3**: Clear DNS cache
```bash
ipconfig /flushdns  # Windows
sudo systemctl restart systemd-resolved  # Linux
```

### Problem: Connection timeout ke port 8000

**Check firewall rules**:
```bash
/ip firewall filter print where dst-port=8000
```

**Check Anthias service**:
```bash
# Via SSH ke server
docker-compose -f docker-compose.dev.yml ps
```

### Problem: Slow DNS resolution

**Optimize DNS cache**:
```bash
/ip dns set cache-max-ttl=1w
/ip dns cache flush
```

### Problem: Access dari internet tidak work

**Check NAT rules**:
```bash
/ip firewall nat print where comment~"Anthias"
```

**Check WAN interface**:
```bash
/interface print where running=yes
```

## 📊 Network Performance Optimization

### 1. QoS for Anthias Traffic

**Prioritize HTTP traffic to Anthias**:
```bash
/queue simple
add name=anthias-priority target=192.168.5.12/32 max-limit=100M/100M priority=1/1
```

### 2. Bandwidth Monitoring

**Monitor traffic to Anthias server**:
```bash
/tool traffic-monitor interface=bridge duration=60 count=1 target=192.168.5.12
```

### 3. Connection Tracking

**Monitor active connections**:
```bash
/ip firewall connection print where dst-address=192.168.5.12
```

## 🎉 Ringkasan Step 3: MikroTik Configuration

✅ **MikroTik berhasil dikonfigurasi**:

1. **DNS Static Record**: `anthias.local` → `192.168.5.12` - OK
2. **DNS Service**: Remote requests enabled - OK  
3. **Firewall Rules**: HTTP (8000) dan SSH (22) allowed - OK
4. **DHCP Integration**: DNS auto-distributed ke clients - OK
5. **Network Resolution**: `anthias.local` resolve dari semua devices - OK

⚠️ **URL Akses Final**:
- **Internal LAN**: `http://anthias.local:8000`
- **Fallback IP**: `http://192.168.5.12:8000`
- **Mobile/QR**: Generate QR code untuk easy access

## 📋 Next Step

Lanjut ke **[STEP-04-CUSTOM-VIEWERS.md](STEP-04-CUSTOM-VIEWERS.md)** untuk deploy custom viewers ke server.

## ✅ DNS Configuration Success!

**Status**: DNS `anthias.local` sudah working perfect!

**Verified Working**:
- ✅ **DNS Record**: `anthias.local → 192.168.5.12` di MikroTik
- ✅ **Ping**: `ping anthias.local` resolves correctly  
- ✅ **Web Access**: `http://anthias.local:8000` returns HTTP 200 OK
- ✅ **Custom Viewers**: All 4 viewers accessible via anthias.local
- ✅ **MikroTik DNS**: Working untuk semua devices di network

**Note**: `nslookup anthias.local` menggunakan MikroTik DNS server yang sudah dikonfigurasi.

---

*MikroTik configuration selesai! Anthias sekarang accessible via `anthias.local` dari seluruh network.*