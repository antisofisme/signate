# Quick Start Guide - Nomad Stack

> **Setup Nomad + Docker + Consul dalam 5 menit**

---

## 🚀 Option 1: Automatic Installation (Recommended)

### Single Command Installation:

```bash
# 1. Download tutorial folder
cd ~
git clone <your-repo> tutorial-nomad-stack
# Atau copy folder tutorial-nomad-stack ke server

# 2. Go to tutorial directory
cd tutorial-nomad-stack

# 3. Run installation script
sudo ./scripts/install-all.sh
```

### Verification:

```bash
# Run health check
./scripts/health-check.sh
```

---

## 📚 Option 2: Manual Step-by-Step

Ikuti tutorial lengkap:

1. [00-prerequisites.md](00-prerequisites.md) - System preparation
2. [01-install-docker.md](01-install-docker.md) - Install Docker
3. [02-install-nomad.md](02-install-nomad.md) - Install Nomad
4. [03-install-consul.md](03-install-consul.md) - Install Consul

---

## 🎯 Deploy First Application

### Example: Deploy Backend API

```bash
# Navigate to jobs folder
cd tutorial-nomad-stack/jobs

# Deploy backend API
nomad job run example-backend.nomad

# Check job status
nomad job status backend-api

# View logs
nomad alloc logs -f $(nomad job allocs backend-api | grep running | awk 'NR==1{print $1}')
```

### Example: Deploy Full Stack

```bash
# Deploy database
nomad job run postgres.nomad

# Deploy cache
nomad job run redis.nomad

# Deploy backend
nomad job run example-backend.nomad

# Deploy frontend
nomad job run example-frontend.nomad

# Check all jobs
nomad job status
```

---

## 🌐 Access Web UIs

After installation, access these UIs:

- **Nomad UI**: `http://YOUR_SERVER_IP:4646`
  - View jobs, allocations, nodes
  - Monitor cluster status
  
- **Consul UI**: `http://YOUR_SERVER_IP:8500`
  - View registered services
  - Check health status

---

## 📊 Common Commands

### Nomad Commands:

```bash
# List jobs
nomad job status

# Deploy job
nomad job run <file.nomad>

# Stop job
nomad job stop <job-name>

# View logs
nomad alloc logs <alloc-id>

# List nodes
nomad node status
```

### Docker Commands:

```bash
# List containers
docker ps

# View logs
docker logs <container-name>

# Container stats
docker stats
```

### Consul Commands:

```bash
# List services
consul catalog services

# Check members
consul members
```

---

## 🆘 Troubleshooting

### Services won't start:

```bash
# Check Docker
sudo systemctl status docker
sudo journalctl -u docker -n 50

# Check Nomad
sudo systemctl status nomad
sudo journalctl -u nomad -n 50

# Check Consul
sudo systemctl status consul
sudo journalctl -u consul -n 50
```

### Reset everything:

```bash
# Stop all services
sudo systemctl stop nomad consul docker

# Remove data (CAUTION: This deletes all data!)
sudo rm -rf /opt/nomad/data/*
sudo rm -rf /opt/consul/data/*

# Restart services
sudo systemctl start docker consul nomad
```

---

## 📖 Next Steps

1. ✅ Customize job files untuk aplikasi Anda
2. ✅ Setup Traefik untuk load balancing
3. ✅ Configure monitoring (Prometheus + Grafana)
4. ✅ Setup SSL/TLS certificates
5. ✅ Implement secrets management (Vault)

---

## 📞 Resources

- [Nomad Documentation](https://developer.hashicorp.com/nomad/docs)
- [Consul Documentation](https://developer.hashicorp.com/consul/docs)
- [Docker Documentation](https://docs.docker.com/)

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-01
