# Unified Environment Configuration Architecture
## Smart TV Digital Signage System

**Version:** 1.0.0
**Date:** October 27, 2025
**Status:** Architecture Design Document

---

## Executive Summary

This document outlines a comprehensive unified environment configuration architecture for the Smart TV Digital Signage system, addressing the current issues of hardcoded values, inconsistent configurations, and deployment complexity across all system components.

### Current Issues Identified

1. **Hardcoded IP addresses and ports** across multiple components
2. **Inconsistent configuration patterns** between services
3. **No environment-specific profiles** (dev/staging/production)
4. **Mixed configuration sources** (env files, hardcoded, docker-compose)
5. **Difficult deployment** to new environments
6. **Security concerns** with exposed credentials and secrets

### Solution Overview

- **Single source of truth**: One `.env` file controls the entire system
- **Environment profiles**: Separate configurations for dev/staging/production
- **Zero hardcoding**: All configurable values externalized
- **Docker-native**: Full docker-compose integration
- **Security-first**: Secrets management and secure defaults
- **Validation**: Startup checks and configuration validation

---

## 1. Unified Environment Structure

### 1.1 Master Configuration Hierarchy

```
signate/
├── .env                    # Active environment (git-ignored)
├── .env.example           # Template with all variables
├── envs/
│   ├── .env.development   # Development profile
│   ├── .env.staging       # Staging profile
│   └── .env.production    # Production profile
├── docker/
│   └── docker-compose.yml # Uses .env from parent
├── backend/
│   └── app/
│       └── core/
│           └── config.py  # Reads from environment
├── web-admin/
│   ├── .env              # Symlink to parent .env
│   └── vite.config.js    # Uses VITE_ prefixed vars
└── viewer/
    └── js/
        └── config/
            └── env.js    # Runtime config loader
```

### 1.2 Configuration Categories

#### Core Infrastructure
- Server addresses and ports
- Database connections
- Redis configuration
- Network settings

#### Service Discovery
- Inter-service communication
- API endpoints
- WebSocket connections
- Load balancer URLs

#### Security & Authentication
- JWT secrets and algorithms
- API keys
- Encryption keys
- CORS origins

#### Application Settings
- Feature flags
- Timeouts and intervals
- Cache TTLs
- Rate limits

#### Monitoring & Logging
- Log levels and formats
- Health check intervals
- Metrics endpoints
- Alert configurations

---

## 2. Complete .env.example Structure

```bash
# =============================================================================
# SMART TV DIGITAL SIGNAGE - UNIFIED ENVIRONMENT CONFIGURATION
# =============================================================================
# Version: 1.0.0
#
# Instructions:
# 1. Copy this file to .env: cp .env.example .env
# 2. Update values for your environment
# 3. Never commit .env to version control
# =============================================================================

# -----------------------------------------------------------------------------
# ENVIRONMENT PROFILE
# -----------------------------------------------------------------------------
# Options: development | staging | production
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# SERVER CONFIGURATION
# -----------------------------------------------------------------------------
# Primary server IP/hostname (used by all services)
SERVER_HOST=192.168.5.12
SERVER_DOMAIN=signage.local

# Service Ports (all services on same host)
PORT_BACKEND_API=8001
PORT_ANTHIAS=8000
PORT_WEB_ADMIN=3000
PORT_VIEWER=8080
PORT_POSTGRES=5433
PORT_REDIS=6379

# -----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=signage_user
POSTGRES_PASSWORD=changeme_in_production
POSTGRES_DB=signage_db

# Connection pool settings
POSTGRES_POOL_MIN=2
POSTGRES_POOL_MAX=10
POSTGRES_POOL_TIMEOUT=30

# Database URL (auto-constructed or override)
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# -----------------------------------------------------------------------------
# REDIS CONFIGURATION
# -----------------------------------------------------------------------------
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Redis URLs for different services
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
CELERY_BROKER_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0
CELERY_RESULT_BACKEND=redis://${REDIS_HOST}:${REDIS_PORT}/0

# -----------------------------------------------------------------------------
# API ENDPOINTS (Auto-constructed from SERVER_HOST and PORTS)
# -----------------------------------------------------------------------------
# Backend API
API_BASE_URL=http://${SERVER_HOST}:${PORT_BACKEND_API}
API_BASE_URL_INTERNAL=http://backend-api:8000

# Anthias CMS
ANTHIAS_API_URL=http://${SERVER_HOST}:${PORT_ANTHIAS}
ANTHIAS_API_URL_INTERNAL=http://anthias-nginx:80

# Web Admin
WEB_ADMIN_URL=http://${SERVER_HOST}:${PORT_WEB_ADMIN}

# Viewer
VIEWER_URL=http://${SERVER_HOST}:${PORT_VIEWER}

# -----------------------------------------------------------------------------
# SECURITY & AUTHENTICATION
# -----------------------------------------------------------------------------
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption key for sensitive data
ENCRYPTION_KEY=your-encryption-key-32-chars-long

# API Keys
ANTHIAS_API_KEY=
FIREBIRD_API_KEY=

# -----------------------------------------------------------------------------
# CORS CONFIGURATION
# -----------------------------------------------------------------------------
# Comma-separated list of allowed origins
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://${SERVER_HOST}:${PORT_WEB_ADMIN},http://${SERVER_HOST}:${PORT_VIEWER}
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# -----------------------------------------------------------------------------
# FRONTEND CONFIGURATION (Vite/React)
# -----------------------------------------------------------------------------
# All frontend env vars must be prefixed with VITE_
VITE_API_URL=http://${SERVER_HOST}:${PORT_BACKEND_API}
VITE_WS_URL=ws://${SERVER_HOST}:${PORT_BACKEND_API}
VITE_ENVIRONMENT=${ENVIRONMENT}
VITE_DEBUG=${DEBUG}

# -----------------------------------------------------------------------------
# VIEWER CONFIGURATION
# -----------------------------------------------------------------------------
VIEWER_API_URL=http://${SERVER_HOST}:${PORT_BACKEND_API}
VIEWER_HEARTBEAT_INTERVAL=30000
VIEWER_PLAYLIST_REFRESH_INTERVAL=60000
VIEWER_LOG_SEND_INTERVAL=5000
VIEWER_LOG_BUFFER_SIZE=20
VIEWER_CACHE_ENABLED=true
VIEWER_CACHE_MAX_SIZE=104857600

# -----------------------------------------------------------------------------
# DEVICE MANAGEMENT
# -----------------------------------------------------------------------------
DEVICE_HEARTBEAT_TIMEOUT=300
DEVICE_OFFLINE_THRESHOLD=600
DEVICE_CODE_LENGTH=6
DEVICE_CODE_EXPIRY_MINUTES=30

# -----------------------------------------------------------------------------
# CONTENT MANAGEMENT
# -----------------------------------------------------------------------------
MAX_UPLOAD_SIZE=104857600
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/gif,image/webp
ALLOWED_VIDEO_TYPES=video/mp4,video/mpeg,video/quicktime,video/webm
CONTENT_STORAGE_PATH=/data/content
THUMBNAIL_SIZE=320x240

# -----------------------------------------------------------------------------
# CACHE CONFIGURATION
# -----------------------------------------------------------------------------
CACHE_ENABLED=true
CACHE_TTL_PLAYLIST=300
CACHE_TTL_GUEST_INFO=300
CACHE_TTL_CONTENT_METADATA=900
CACHE_TTL_DEVICE_STATUS=60

# -----------------------------------------------------------------------------
# RATE LIMITING
# -----------------------------------------------------------------------------
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_DEVICE=60
RATE_LIMIT_PER_IP=100
RATE_LIMIT_WINDOW=60

# -----------------------------------------------------------------------------
# MONITORING & HEALTH
# -----------------------------------------------------------------------------
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=60
METRICS_ENABLED=true
METRICS_PORT=9090

# -----------------------------------------------------------------------------
# EXTERNAL INTEGRATIONS
# -----------------------------------------------------------------------------
# Firebird Database (Hotel System)
FIREBIRD_ENABLED=false
FIREBIRD_HOST=
FIREBIRD_PORT=3050
FIREBIRD_DATABASE=
FIREBIRD_USER=
FIREBIRD_PASSWORD=
FIREBIRD_REFRESH_INTERVAL=300

# -----------------------------------------------------------------------------
# DOCKER CONFIGURATION
# -----------------------------------------------------------------------------
COMPOSE_PROJECT_NAME=signage
DOCKER_NETWORK=signage-network
DOCKER_RESTART_POLICY=unless-stopped

# -----------------------------------------------------------------------------
# BACKUP CONFIGURATION
# -----------------------------------------------------------------------------
BACKUP_ENABLED=true
BACKUP_PATH=/backups
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"

# -----------------------------------------------------------------------------
# FEATURE FLAGS
# -----------------------------------------------------------------------------
FEATURE_MULTI_TENANCY=false
FEATURE_ANALYTICS=true
FEATURE_SPEED_TEST=true
FEATURE_REMOTE_CONTROL=false
FEATURE_CONTENT_SCHEDULING=true
FEATURE_DEVICE_GROUPS=true

# -----------------------------------------------------------------------------
# DEVELOPMENT TOOLS
# -----------------------------------------------------------------------------
ENABLE_API_DOCS=true
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=false
ENABLE_QUERY_LOGGING=false
```

---

## 3. Environment Profiles

### 3.1 Development Profile (.env.development)

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Use localhost for development
SERVER_HOST=localhost
SERVER_DOMAIN=localhost

# Development database
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=signage_dev

# Relaxed security for development
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=*

# Enable all dev tools
ENABLE_API_DOCS=true
ENABLE_HOT_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true
ENABLE_QUERY_LOGGING=true

# Disable production features
RATE_LIMIT_ENABLED=false
BACKUP_ENABLED=false
```

### 3.2 Staging Profile (.env.staging)

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Staging server
SERVER_HOST=staging.signage.local
SERVER_DOMAIN=staging.signage.local

# Staging database
POSTGRES_PASSWORD=${STAGING_DB_PASSWORD}
POSTGRES_DB=signage_staging

# Moderate security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=https://staging.signage.local

# Limited dev tools
ENABLE_API_DOCS=true
ENABLE_HOT_RELOAD=false
ENABLE_DEBUG_TOOLBAR=false

# Enable production-like features
RATE_LIMIT_ENABLED=true
BACKUP_ENABLED=true
```

### 3.3 Production Profile (.env.production)

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Production server
SERVER_HOST=signage.company.com
SERVER_DOMAIN=signage.company.com

# Production database (use secrets manager)
POSTGRES_PASSWORD=${PROD_DB_PASSWORD}
POSTGRES_DB=signage_prod

# Maximum security
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
CORS_ORIGINS=https://signage.company.com

# Disable all dev tools
ENABLE_API_DOCS=false
ENABLE_HOT_RELOAD=false
ENABLE_DEBUG_TOOLBAR=false
ENABLE_QUERY_LOGGING=false

# Enable all production features
RATE_LIMIT_ENABLED=true
BACKUP_ENABLED=true
METRICS_ENABLED=true
```

---

## 4. Configuration Loading Strategy

### 4.1 Backend (Python/FastAPI)

```python
# backend/app/core/config.py
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator, computed_field

class Settings(BaseSettings):
    """Unified configuration settings"""

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Server
    server_host: str = Field(default="localhost")
    port_backend_api: int = Field(default=8001)

    # Database
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="signage_user")
    postgres_password: str = Field(default="password")
    postgres_db: str = Field(default="signage_db")

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field
    @property
    def api_base_url(self) -> str:
        """Construct API base URL"""
        return f"http://{self.server_host}:{self.port_backend_api}"

    # CORS
    cors_origins: List[str] = Field(default_factory=list)

    @validator('cors_origins', pre=True)
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='allow'
    )

# Singleton instance
settings = Settings()
```

### 4.2 Web Admin (React/Vite)

```javascript
// web-admin/src/config/env.js
const getEnvVar = (key, defaultValue = '') => {
  // Vite environment variables
  if (import.meta.env?.[key]) {
    return import.meta.env[key];
  }

  // Fallback to process.env for SSR
  if (typeof process !== 'undefined' && process.env?.[key]) {
    return process.env[key];
  }

  return defaultValue;
};

export const config = {
  environment: getEnvVar('VITE_ENVIRONMENT', 'development'),
  debug: getEnvVar('VITE_DEBUG', 'false') === 'true',

  api: {
    baseUrl: getEnvVar('VITE_API_URL', 'http://localhost:8001'),
    wsUrl: getEnvVar('VITE_WS_URL', 'ws://localhost:8001'),
    timeout: parseInt(getEnvVar('VITE_API_TIMEOUT', '30000')),
  },

  features: {
    multiTenancy: getEnvVar('VITE_FEATURE_MULTI_TENANCY', 'false') === 'true',
    analytics: getEnvVar('VITE_FEATURE_ANALYTICS', 'true') === 'true',
    speedTest: getEnvVar('VITE_FEATURE_SPEED_TEST', 'true') === 'true',
  }
};

// Validate required configuration
const validateConfig = () => {
  const required = ['VITE_API_URL'];
  const missing = required.filter(key => !getEnvVar(key));

  if (missing.length > 0) {
    console.error(`Missing required environment variables: ${missing.join(', ')}`);
  }
};

validateConfig();
export default config;
```

### 4.3 Viewer (Vanilla JS)

```javascript
// viewer/js/config/env.js
(function() {
  'use strict';

  // Configuration loader for viewer
  window.ViewerConfig = {
    // Load from meta tags (injected by server)
    loadFromMeta: function() {
      const config = {};
      const metas = document.querySelectorAll('meta[name^="config-"]');

      metas.forEach(meta => {
        const key = meta.name.replace('config-', '');
        config[key] = meta.content;
      });

      return config;
    },

    // Load from config endpoint
    loadFromServer: async function() {
      try {
        const response = await fetch('/config.json');
        if (response.ok) {
          return await response.json();
        }
      } catch (e) {
        console.error('Failed to load config from server:', e);
      }
      return {};
    },

    // Default configuration
    defaults: {
      apiUrl: 'http://192.168.5.12:8001',
      heartbeatInterval: 30000,
      playlistRefreshInterval: 60000,
      logSendInterval: 5000,
      logBufferSize: 20,
      cacheEnabled: true,
    },

    // Initialize configuration
    init: async function() {
      // Try loading from meta tags first
      let config = this.loadFromMeta();

      // If no meta config, try server endpoint
      if (Object.keys(config).length === 0) {
        config = await this.loadFromServer();
      }

      // Merge with defaults
      this.config = { ...this.defaults, ...config };

      // Update global state
      if (window.ShellState) {
        window.ShellState.API_BASE_URL = this.config.apiUrl;
        window.ShellState.HEARTBEAT_INTERVAL = parseInt(this.config.heartbeatInterval);
      }

      if (window.PlayerState) {
        window.PlayerState.API_BASE_URL = this.config.apiUrl;
        window.PlayerState.REFRESH_INTERVAL = parseInt(this.config.playlistRefreshInterval);
      }

      return this.config;
    }
  };

  // Auto-initialize on load
  document.addEventListener('DOMContentLoaded', function() {
    window.ViewerConfig.init();
  });
})();
```

### 4.4 Docker Compose Integration

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  backend-api:
    env_file:
      - ../.env  # Load from parent directory
    environment:
      # Override with Docker-specific values
      POSTGRES_HOST: postgres
      REDIS_HOST: redis
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    networks:
      - ${DOCKER_NETWORK:-signage-network}
    restart: ${DOCKER_RESTART_POLICY:-unless-stopped}

  viewer:
    image: nginx:alpine
    volumes:
      - ../viewer:/usr/share/nginx/html:ro
      - ./viewer-config.js:/usr/share/nginx/html/config.js:ro
    environment:
      - API_URL=${API_BASE_URL}
      - HEARTBEAT_INTERVAL=${VIEWER_HEARTBEAT_INTERVAL}
    command: /bin/sh -c "envsubst < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js && nginx -g 'daemon off;'"
```

---

## 5. Migration Plan

### Phase 1: Preparation (Week 1)
1. **Audit all hardcoded values** across all components
2. **Create comprehensive .env.example** with all variables
3. **Set up environment profiles** for dev/staging/prod
4. **Document all configuration dependencies**

### Phase 2: Backend Migration (Week 2)
1. **Update config.py** to use new environment structure
2. **Replace all hardcoded values** with environment variables
3. **Update Docker configurations**
4. **Test with different profiles**

### Phase 3: Frontend Migration (Week 3)
1. **Update Vite configuration** for web-admin
2. **Implement config loader** for viewer
3. **Replace hardcoded API URLs**
4. **Test cross-origin requests**

### Phase 4: Deployment & Testing (Week 4)
1. **Update CI/CD pipelines**
2. **Deploy to staging** with new configuration
3. **Perform integration testing**
4. **Document deployment procedures**

### Phase 5: Production Rollout
1. **Prepare production .env**
2. **Backup current configuration**
3. **Deploy with gradual rollout**
4. **Monitor and validate**

---

## 6. Configuration Validation Script

```bash
#!/bin/bash
# validate-config.sh - Configuration validation script

set -e

echo "==================================="
echo "Configuration Validation"
echo "==================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Source the environment file
set -a
source .env
set +a

# Required variables
REQUIRED_VARS=(
    "ENVIRONMENT"
    "SERVER_HOST"
    "PORT_BACKEND_API"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
    "SECRET_KEY"
    "JWT_SECRET_KEY"
)

# Check required variables
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=($var)
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "ERROR: Missing required environment variables:"
    printf '%s\n' "${MISSING_VARS[@]}"
    exit 1
fi

# Validate environment value
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo "ERROR: Invalid ENVIRONMENT value: $ENVIRONMENT"
    echo "Must be one of: development, staging, production"
    exit 1
fi

# Check database connection
echo "Testing database connection..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null 2>&1 || {
    echo "ERROR: Cannot connect to PostgreSQL database"
    exit 1
}

# Check Redis connection
echo "Testing Redis connection..."
redis-cli -h ${REDIS_HOST:-localhost} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1 || {
    echo "WARNING: Cannot connect to Redis"
}

# Check API endpoints
echo "Testing API endpoints..."
curl -f -s -o /dev/null -w "%{http_code}" http://${SERVER_HOST}:${PORT_BACKEND_API}/health || {
    echo "WARNING: Backend API not responding"
}

echo ""
echo "==================================="
echo "Configuration validation complete!"
echo "Environment: $ENVIRONMENT"
echo "Server: $SERVER_HOST"
echo "==================================="
```

---

## 7. Docker Deployment Guide

### 7.1 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/signage.git
cd signage

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Validate configuration
./scripts/validate-config.sh

# 4. Start services
docker-compose up -d

# 5. Check status
docker-compose ps
docker-compose logs -f
```

### 7.2 Environment-Specific Deployment

```bash
# Development
cp envs/.env.development .env
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Staging
cp envs/.env.staging .env
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up

# Production
cp envs/.env.production .env
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### 7.3 Service Management

```bash
# View logs
docker-compose logs -f backend-api
docker-compose logs -f --tail=100 postgres

# Restart service
docker-compose restart backend-api

# Scale service
docker-compose up -d --scale backend-api=3

# Execute commands
docker-compose exec backend-api python manage.py migrate
docker-compose exec postgres psql -U signage_user signage_db
```

---

## 8. Security Best Practices

### 8.1 Secret Management

1. **Never commit .env files** to version control
2. **Use secret managers** in production (AWS Secrets Manager, HashiCorp Vault)
3. **Rotate secrets regularly**
4. **Use strong, unique passwords**
5. **Encrypt sensitive data** at rest

### 8.2 Environment Isolation

1. **Separate databases** per environment
2. **Network segmentation** between environments
3. **Different API keys** per environment
4. **Restricted CORS origins** in production
5. **Minimal logging** in production

### 8.3 Access Control

1. **Principle of least privilege**
2. **Service accounts** for inter-service communication
3. **API key rotation**
4. **Rate limiting** on all endpoints
5. **Audit logging** for configuration changes

---

## 9. Monitoring & Troubleshooting

### 9.1 Health Checks

```bash
# Check all services
curl http://localhost:8001/health  # Backend API
curl http://localhost:8000/health  # Anthias
curl http://localhost:8080/health  # Viewer
```

### 9.2 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Services won't start | Missing environment variables | Run validation script |
| Database connection failed | Wrong credentials or host | Check DATABASE_URL |
| CORS errors | Origins not configured | Update CORS_ORIGINS |
| Cannot find config | .env not in correct location | Check file paths |
| Docker network issues | Network not created | Run `docker network create signage-network` |

### 9.3 Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f --tail=1000

# Check environment variables
docker-compose exec backend-api env | sort
```

---

## 10. Maintenance & Updates

### 10.1 Updating Configuration

1. **Update .env.example** with new variables
2. **Document changes** in CHANGELOG
3. **Notify team** of required updates
4. **Update validation script**
5. **Test in development** first

### 10.2 Backup Procedures

```bash
# Backup current configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup database
docker-compose exec postgres pg_dump -U signage_user signage_db > backup.sql

# Backup volumes
docker run --rm -v signage_postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data.tar.gz /data
```

### 10.3 Version Migration

When upgrading to a new version:

1. **Read migration notes**
2. **Backup current configuration**
3. **Compare .env.example changes**
4. **Add new required variables**
5. **Run validation script**
6. **Test in staging first**

---

## Appendix A: Environment Variable Reference

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| ENVIRONMENT | string | development | Yes | Environment profile |
| DEBUG | boolean | false | Yes | Debug mode |
| SERVER_HOST | string | localhost | Yes | Primary server host |
| PORT_BACKEND_API | integer | 8001 | Yes | Backend API port |
| PORT_ANTHIAS | integer | 8000 | Yes | Anthias CMS port |
| POSTGRES_USER | string | - | Yes | Database user |
| POSTGRES_PASSWORD | string | - | Yes | Database password |
| SECRET_KEY | string | - | Yes | Application secret |
| JWT_SECRET_KEY | string | - | Yes | JWT signing key |
| CORS_ORIGINS | string | - | No | Allowed origins |

---

## Appendix B: Configuration Templates

### B.1 Nginx Proxy Configuration

```nginx
# /etc/nginx/sites-available/signage
server {
    listen 80;
    server_name ${SERVER_DOMAIN};

    location /api {
        proxy_pass http://localhost:${PORT_BACKEND_API};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /admin {
        proxy_pass http://localhost:${PORT_WEB_ADMIN};
    }

    location / {
        proxy_pass http://localhost:${PORT_VIEWER};
    }
}
```

### B.2 Systemd Service

```ini
# /etc/systemd/system/signage.service
[Unit]
Description=Smart TV Digital Signage
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/signage
EnvironmentFile=/opt/signage/.env
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

---

## Conclusion

This unified environment configuration architecture provides:

1. **Single source of truth** for all configuration
2. **Environment-specific profiles** for different deployments
3. **Zero hardcoding** across all components
4. **Secure defaults** with validation
5. **Easy deployment** to new environments
6. **Comprehensive documentation** and tooling

By implementing this architecture, the Smart TV Digital Signage system will be:
- **More maintainable** with centralized configuration
- **More secure** with proper secret management
- **Easier to deploy** with environment profiles
- **More reliable** with configuration validation
- **Better documented** with clear configuration structure

The migration can be completed in phases over 4 weeks with minimal disruption to existing deployments.