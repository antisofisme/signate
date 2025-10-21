# STEP 1: Setup Environment & Prerequisites

## 🎯 Apa yang akan kita lakukan?

Di step ini kita akan setup Ubuntu server dari awal (jika fresh) atau memastikan semua prerequisites sudah ready untuk instalasi Anthias. Tutorial ini cover:

**Untuk Fresh Ubuntu**:
- System update & essential tools
- Docker & Docker Compose installation
- User permissions & security setup
- Portainer installation untuk Docker management

**Untuk Existing Ubuntu**:
- Verification semua tools sudah ready
- Update jika ada yang missing

## 📋 Environment Setup & Verification

### 1. Koneksi ke Server

**Apa itu**: Kita akan connect ke server via SSH untuk bisa jalankan command dari jarak jauh.

**Command yang dijalankan**:
```bash
ssh gzjbbk@192.168.5.12
```

**Penjelasan**: 
- `ssh` = program untuk remote access ke server Linux
- `gzjbbk` = username di server
- `192.168.5.12` = IP address server target

### 2. Cek Status Current System

Mari kita lihat kondisi server saat ini:

**Command**:
```bash
whoami && pwd && date
```

**Hasil**:
```
gzjbbk
/home/gzjbbk
Fri Aug 15 04:07:46 UTC 2025
```

✅ **Status**: Koneksi berhasil! Kita sekarang berada di server sebagai user `gzjbbk`.

### 3. Cek Versi OS dan System Info

**Command**:
```bash
cat /etc/os-release
```

**Hasil**:
```
PRETTY_NAME="Ubuntu 22.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.4 LTS (Jammy Jellyfish)"
```

✅ **Status**: Bagus! Server menggunakan Ubuntu 22.04 LTS yang compatible dengan Anthias.

## 🔧 Fresh Installation (Skip jika sudah ada)

### A. System Update & Essential Tools

**Jika fresh Ubuntu, jalankan commands ini**:

**Command update system**:
```bash
sudo apt update && sudo apt upgrade -y
```

**Command install essential tools**:
```bash
sudo apt install -y curl wget vim htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

**Expected Output**:
```
Reading package lists... Done
Building dependency tree... Done
[... installing packages ...]
Setting up essential tools...
```

### B. Docker Installation (jika belum ada)

**Command remove old Docker versions**:
```bash
sudo apt remove -y docker docker-engine docker.io containerd runc
```

**Command add Docker GPG key**:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
```

**Command add Docker repository**:
```bash
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

**Command install Docker**:
```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-compose
```

**Command enable Docker service**:
```bash
sudo systemctl enable docker
sudo systemctl start docker
```

**Command configure Docker restart policies**:
```bash
# Restart Docker service automatically on system reboot
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

**Command add user to docker group**:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

⚠️ **Important**: Jika fresh install, logout dan login kembali setelah docker group assignment.

## 📋 Verification & Prerequisites Check

### 4. Cek Docker Installation

**Apa itu Docker**: Software untuk menjalankan aplikasi dalam container (seperti virtual machine ringan). Anthias memerlukan Docker untuk berjalan.

**Command untuk cek Docker**:
```bash
docker --version
docker-compose --version
```

**Hasil**:
```
Docker version 27.5.1, build 27.5.1-0ubuntu3~22.04.2
docker-compose version 1.29.2, build unknown
```

✅ **Status**: Docker sudah terinstall dengan baik!

### 5. Test Docker Permissions

Sekarang kita perlu memastikan user `gzjbbk` bisa menjalankan Docker tanpa sudo.

**Command**:
```bash
docker ps
```

**Hasil**:
```
CONTAINER ID   IMAGE                     PORTS                          NAMES
[... existing containers may be running ...]
```

✅ **Status**: Docker permissions sudah OK! User bisa jalankan Docker tanpa sudo.

### 6. Check Available Resources

**Command check disk space**:
```bash
df -h
```

**Command check memory**:
```bash
free -h
```

**Expected Output**:
```
              total        used        free      shared  buff/cache   available
Mem:            16Gi       2.1Gi        12Gi       1.0Mi       1.8Gi        13Gi
Swap:           2.0Gi          0B       2.0Gi
```

✅ **Status**: Sufficient resources available untuk Anthias deployment.

### 7. Portainer untuk Container Management

**Apa itu Portainer**: Web interface untuk manage Docker containers dengan tampilan GUI yang mudah dipahami.

**Jika Portainer belum ada, install sekarang**:

**Command create Portainer volume**:
```bash
docker volume create portainer_data
```

**Command install Portainer**:
```bash
docker run -d \
  --name portainer \
  --restart unless-stopped \
  -p 9090:9000 \
  -p 9443:9443 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

**⚠️ Important**: Flag `--restart unless-stopped` memastikan Portainer auto-start setelah system reboot.

**Expected Output**:
```
Unable to find image 'portainer/portainer-ce:latest' locally
latest: Pulling from portainer/portainer-ce
[... downloading image ...]
Status: Downloaded newer image for portainer/portainer-ce:latest
a1b2c3d4e5f6...
```

**Command verify Portainer running**:
```bash
docker ps | grep portainer
```

Dari output `docker ps` sebelumnya, kita lihat Portainer sudah running:
```
portainer/portainer-ce:latest   0.0.0.0:9443->9443/tcp   portainer
```

**Setup admin user** (first time access):
1. Buka browser ke `http://192.168.5.12:9090`
2. Create admin username/password
3. Choose "Docker" environment
4. Start using Portainer

✅ **Status**: Portainer sudah terinstall dan bisa diakses di `http://192.168.5.12:9090` atau `https://192.168.5.12:9443`

### 8. Check System Tools

**Command cek tools yang dibutuhkan**:
```bash
curl --version
```

**Hasil**:
```
curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0
```

✅ **Status**: Essential tools sudah terinstall dengan versi yang baik!

### 9. Configure Firewall (UFW)

**Apa itu**: Setup basic firewall untuk security.

**Jika fresh Ubuntu atau firewall belum configured**:

**Command enable UFW**:
```bash
sudo ufw enable
```

**Command allow essential ports**:
```bash
# SSH access
sudo ufw allow 22

# Portainer
sudo ufw allow 9090
sudo ufw allow 9443

# Anthias (will be used later)
sudo ufw allow 8000
```

**Command check UFW status**:
```bash
sudo ufw status
```

**Expected Output**:
```
Status: active

To                         Action      From
--                         ------      ----
22                         ALLOW       Anywhere
9090                       ALLOW       Anywhere
9443                       ALLOW       Anywhere
8000                       ALLOW       Anywhere
```

✅ **Status**: Firewall configured dengan ports yang diperlukan.

### 10. System Monitoring Tools

**Apa itu**: Tools untuk monitor system performance.

**Jika fresh Ubuntu, install monitoring tools**:
```bash
sudo apt install -y htop iotop nload ncdu tree
```

**Command test monitoring tools**:
```bash
# System processes
htop

# Disk I/O
sudo iotop

# Network usage
nload

# Disk usage
ncdu /

# Directory tree
tree /home
```

✅ **Status**: Monitoring tools available untuk troubleshooting.

## 🎉 Ringkasan Step 1: Setup Environment & Prerequisites

✅ **Semua prerequisites sudah siap**:

1. **Server Connection**: Ubuntu 22.04.4 LTS - OK
2. **Docker**: v27.5.1 dengan docker-compose v1.29.2 - OK  
3. **Docker Permissions**: User bisa jalankan Docker tanpa sudo - OK
4. **Portainer**: Sudah running di port 9090/9443 untuk Docker management - OK
5. **System Resources**: Sufficient disk space dan memory available - OK
6. **System Tools**: curl dan essential tools ready - OK
7. **Firewall**: UFW configured dengan essential ports - OK
8. **Monitoring Tools**: htop, iotop, nload available - OK

⚠️ **Catatan Penting**:
- Anthias akan menggunakan container names dengan prefix `anthias-` untuk avoid confusion
- Port 8000 akan digunakan untuk Anthias
- DNS `anthias.local` akan dikonfigurasi via MikroTik router (STEP-03)

## 📊 System Verification

**Command untuk verify semua ready**:
```bash
# System info
lsb_release -a
free -h
df -h

# Docker
docker --version
docker-compose --version
docker ps

# Services
sudo systemctl status docker

# Network
ip addr show
sudo ufw status

# Ports
ss -tulpn | grep -E "(22|8000|9090|9443)"
```

## 🔧 Troubleshooting

**Problem**: Docker permission denied
**Solution**:
```bash
sudo usermod -aG docker $USER
newgrp docker
# Atau logout/login kembali
```

**Problem**: Portainer tidak accessible
**Solution**:
```bash
docker logs portainer
sudo ufw allow 9090
# Check if port in use: sudo netstat -tulpn | grep 9090
```


**Problem**: UFW blocking connections
**Solution**:
```bash
sudo ufw status numbered
sudo ufw delete [number]  # Remove specific rule
sudo ufw allow [port]     # Add new rule
```

## 📋 Next Step

Lanjut ke **[STEP-02-ANTHIAS-INSTALLATION.md](STEP-02-ANTHIAS-INSTALLATION.md)** untuk install Anthias.

---

*Environment setup selesai! Server ready untuk Anthias deployment.*