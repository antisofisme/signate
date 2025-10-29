# Deployment & Infrastructure Documentation

Dokumentasi lengkap tentang deployment, Docker, Kubernetes, dan infrastructure management.

## 📚 Contents

### Docker & Containers
- **DEPLOYMENT_INFO.md** - Informasi deployment dasar
- **REBUILD-GUIDE.md** - Panduan rebuild services
- **DOCKER_COMPOSE_UPDATE_COMPLETE.md** - Update Docker Compose
- **DOCKER_HEALTH_CHECKS_SUMMARY.md** - Health checks configuration
- **DOCKER_SECURITY_FIXES_COMPLETE.md** - Security fixes untuk Docker

### Kubernetes & Orchestration
- **KUBERNETES_ORCHESTRATION_DESIGN.md** - Desain orchestration dengan Kubernetes

### Celery & Background Tasks
- **CELERY_INTEGRATION_ARCHITECTURE.md** - Arsitektur integrasi Celery
- **CELERY_VS_ASYNC_HONEST_ANALYSIS.md** - Analisis Celery vs Async

### Production Deployment
- **PRODUCTION_DEPLOYMENT_CHECKLIST.md** - Checklist deployment production

## 🎯 Quick Start

### For First Deployment
1. Read **DEPLOYMENT_INFO.md** for basic info
2. Follow **PRODUCTION_DEPLOYMENT_CHECKLIST.md**
3. Configure **Docker Compose** as per docs

### For Docker Management
1. **REBUILD-GUIDE.md** - How to rebuild services
2. **DOCKER_HEALTH_CHECKS_SUMMARY.md** - Configure health checks
3. **[CLAUDE.md](../../CLAUDE.md)** - Docker Compose best practices ⭐

### For Kubernetes
1. **KUBERNETES_ORCHESTRATION_DESIGN.md** - K8s architecture
2. Check production deployment checklist

## 📖 Key Documents

- **Deployment Info**: DEPLOYMENT_INFO.md
- **Rebuild Guide**: REBUILD-GUIDE.md
- **Production Checklist**: PRODUCTION_DEPLOYMENT_CHECKLIST.md
- **Docker Best Practices**: [CLAUDE.md](../../CLAUDE.md) ⭐

## ⚠️ Important

- **ALWAYS run docker-compose from parent directory!**
- See [CLAUDE.md Docker Best Practices](../../CLAUDE.md#-docker-compose-best-practices)
- Never hardcode environment variables
- Use `.env` file for configuration

## 🔙 Navigation

- [Back to Documentation Index](../README.md)
- [CLAUDE.md - Main Guide](../../CLAUDE.md)
- [Architecture Docs](../04-architecture/)
