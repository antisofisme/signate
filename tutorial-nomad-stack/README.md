# Tutorial: Nomad + Docker Stack Setup

> **Dokumentasi lengkap untuk setup Nomad + Docker + Consul stack untuk production deployment**

## 📚 Daftar Isi

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Monitoring & Maintenance](#monitoring)

---

## 🎯 Overview

Stack ini menggunakan:
- **Nomad**: Orchestrator untuk manage workloads
- **Docker**: Container runtime untuk isolasi aplikasi
- **Consul**: Service discovery & health checking
- **Traefik**: Reverse proxy & load balancer

---

## 📋 Prerequisites

### Server Requirements
- **OS**: Ubuntu 24.04 LTS (atau 22.04 LTS)
- **RAM**: Minimum 2GB (Rekomendasi: 4GB+)
- **CPU**: Minimum 2 cores
- **Disk**: Minimum 20GB free space
- **Network**: Public IP address

### Access Requirements
- Root/sudo access
- SSH access
- Port 80, 443 terbuka (untuk web traffic)
- Port 4646 (Nomad UI - optional, bisa di-firewall)
- Port 8500 (Consul UI - optional, bisa di-firewall)

---

## 🚀 Quick Start

### Option 1: Automatic Installation (Recommended)

```bash
# 1. Download tutorial
git clone <repo-url> tutorial-nomad-stack
cd tutorial-nomad-stack

# 2. Run installation script
chmod +x scripts/install-all.sh
sudo ./scripts/install-all.sh

# 3. Verify installation
./scripts/health-check.sh
```

### Option 2: Manual Step-by-Step

Ikuti tutorial per-step di folder ini:

1. **[00-prerequisites.md](00-prerequisites.md)** - System preparation
2. **[01-install-docker.md](01-install-docker.md)** - Install Docker Engine
3. **[02-install-nomad.md](02-install-nomad.md)** - Install Nomad
4. **[03-install-consul.md](03-install-consul.md)** - Install Consul
5. **[04-configure-nomad.md](04-configure-nomad.md)** - Configure Nomad cluster
6. **[05-deploy-first-job.md](05-deploy-first-job.md)** - Deploy example application
7. **[06-setup-traefik.md](06-setup-traefik.md)** - Setup reverse proxy
8. **[07-monitoring.md](07-monitoring.md)** - Monitoring & logging

---

## 📁 Folder Structure

```
tutorial-nomad-stack/
├── README.md                    # This file
├── 00-prerequisites.md          # System preparation
├── 01-install-docker.md         # Docker installation
├── 02-install-nomad.md          # Nomad installation
├── 03-install-consul.md         # Consul installation
├── 04-configure-nomad.md        # Nomad configuration
├── 05-deploy-first-job.md       # Deploy example app
├── 06-setup-traefik.md          # Traefik setup
├── 07-monitoring.md             # Monitoring setup
│
├── configs/                     # Configuration files
│   ├── nomad.hcl               # Nomad config
│   ├── consul.hcl              # Consul config
│   └── traefik.yml             # Traefik config
│
├── jobs/                        # Nomad job files
│   ├── example-backend.nomad   # Backend example
│   ├── example-frontend.nomad  # Frontend example
│   ├── postgres.nomad          # PostgreSQL
│   ├── redis.nomad             # Redis
│   └── traefik.nomad           # Traefik load balancer
│
└── scripts/                     # Helper scripts
    ├── install-all.sh          # Auto-install everything
    ├── uninstall.sh            # Uninstall stack
    ├── health-check.sh         # Health check script
    └── backup.sh               # Backup script
```

---

## 🔧 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
└────────────────────┬────────────────────────────────────┘
                     │
              ┌──────▼──────┐
              │   Traefik   │  (Reverse Proxy)
              │  Port 80/443│
              └──────┬──────┘
                     │
        ┏━━━━━━━━━━━━┻━━━━━━━━━━━━┓
        ┃      Nomad Cluster       ┃
        ┃  (Orchestration Layer)   ┃
        ┗━━━━━━━━━━━━┯━━━━━━━━━━━━┛
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
   │Backend │  │Frontend│  │Database│
   │Service │  │Service │  │Service │
   │(Docker)│  │(Docker)│  │(Docker)│
   └────┬───┘  └────┬───┘  └────┬───┘
        │            │            │
        └────────────┼────────────┘
                     │
        ┏━━━━━━━━━━━━▼━━━━━━━━━━━━┓
        ┃         Consul           ┃
        ┃  (Service Discovery)     ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 🎯 Post-Installation

After installation, you'll have:

### Web UIs Available:
- **Nomad UI**: `http://YOUR_IP:4646` - Manage jobs & allocations
- **Consul UI**: `http://YOUR_IP:8500` - Service discovery & health
- **Traefik Dashboard**: `http://YOUR_IP:8080` - Routing & load balancing

### CLI Commands:
```bash
# Nomad
nomad status                    # List all jobs
nomad job run jobs/app.nomad    # Deploy a job
nomad job stop app              # Stop a job

# Consul
consul members                  # List cluster members
consul catalog services         # List registered services

# Docker
docker ps                       # List running containers
docker logs <container>         # View logs
```

---

## 📖 Learning Resources

### Official Documentation:
- [Nomad Documentation](https://developer.hashicorp.com/nomad/docs)
- [Consul Documentation](https://developer.hashicorp.com/consul/docs)
- [Docker Documentation](https://docs.docker.com/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

### Tutorials:
- [Nomad Getting Started](https://developer.hashicorp.com/nomad/tutorials/get-started)
- [Consul Service Mesh](https://developer.hashicorp.com/consul/tutorials/get-started-vms)

---

## ⚠️ Important Notes

1. **Single Server Setup**: Tutorial ini untuk single-server deployment
2. **Production Ready**: Bisa dipakai untuk production dengan resource yang cukup
3. **Scalability**: Bisa di-scale ke multi-server cluster nanti
4. **Security**: Jangan lupa setup firewall dan SSL/TLS untuk production

---

## 🆘 Troubleshooting

Jika ada masalah:
1. Check logs: `journalctl -u nomad -f`
2. Check Nomad status: `nomad agent-info`
3. Check Consul status: `consul members`
4. Run health check: `./scripts/health-check.sh`

---

## 📞 Support

Jika ada pertanyaan atau issue, bisa:
1. Check troubleshooting section di setiap tutorial
2. Review official documentation
3. Check Nomad/Consul community forums

---

## 📝 License

Tutorial ini bebas digunakan untuk keperluan apapun.

---

**Last Updated**: 2026-01-01
**Version**: 1.0.0
