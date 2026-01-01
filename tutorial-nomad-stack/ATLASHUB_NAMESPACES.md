# ATLASHUB - Nomad Namespace Architecture

> **Namespace organization untuk ATLASHUB platform products**

---

## 🏢 Brand Structure

**ATLASHUB** - Enterprise Hospitality Technology Platform

```
ATLASHUB
├── PUGUH Control Plane   ← Governance & orchestration layer
├── SEMAR Console        ← Voice & command interface
└── PANDAWA Suite        ← Domain-specific applications
```

---

## 🎯 Nomad Namespace Mapping

### Namespace: `puguh`

**Purpose**: PUGUH Control Plane services
**Description**: Rules, policy, approval, event bus, multi-tenancy

**Services**:
- `auth-service` - Authentication & authorization
- `rbac-service` - Role-based access control
- `audit-service` - Audit logging & compliance
- `event-bus` - Event-driven architecture backbone
- `tenant-manager` - Multi-tenancy management
- `approval-workflow` - Approval & workflow engine
- `policy-engine` - Business rules & policies

**Example Job**:
```hcl
job "auth-service" {
  namespace = "puguh"  # ← PUGUH namespace

  datacenters = ["dc1"]
  type = "service"

  group "auth" {
    task "api" {
      driver = "docker"
      config {
        image = "atlashub/puguh-auth:v1.0.0"
      }

      service {
        name = "puguh-auth"
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.puguh-auth.rule=Host(`auth.atlashub.com`)"
        ]
      }
    }
  }
}
```

**Deploy**:
```bash
nomad job run -namespace=puguh auth-service.nomad
```

**List jobs**:
```bash
nomad job status -namespace=puguh
```

---

### Namespace: `semar`

**Purpose**: SEMAR Console services
**Description**: Voice assistant, command surface, AI-powered control

**Services**:
- `jarvis-backend` - Main voice assistant backend
- `stt-service` - Speech-to-text (local + cloud hybrid)
- `tts-service` - Text-to-speech
- `command-executor` - Command processing & execution
- `audio-processor` - Audio capture & processing
- `nlp-service` - Natural language processing

**Example Job**:
```hcl
job "jarvis-backend" {
  namespace = "semar"  # ← SEMAR namespace

  datacenters = ["dc1"]
  type = "service"

  group "jarvis" {
    task "api" {
      driver = "docker"
      config {
        image = "atlashub/semar-jarvis:v1.0.0"
      }

      env {
        PUGUH_AUTH_URL = "http://puguh-auth.service.consul:8001"
      }

      service {
        name = "semar-jarvis"
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.semar-jarvis.rule=Host(`voice.atlashub.com`)"
        ]
      }
    }
  }
}
```

**Deploy**:
```bash
nomad job run -namespace=semar jarvis-backend.nomad
```

---

### Namespace: `pandawa`

**Purpose**: PANDAWA Suite applications
**Description**: Domain-specific business applications (PMS, POS, Accounting, Signage, etc)

**Services**:
- `pms-backend` - Property Management System
- `pos-backend` - Point of Sale
- `accounting-backend` - Accounting & finance
- `inventory-backend` - Inventory management
- `hrm-backend` - Human Resource Management
- `signage-cms` - Digital signage CMS
- `signage-player` - Digital signage player
- `guest-portal` - Guest self-service portal
- `channel-manager` - Channel management

**Example Job**:
```hcl
job "pms-backend" {
  namespace = "pandawa"  # ← PANDAWA namespace

  datacenters = ["dc1"]
  type = "service"

  group "pms" {
    task "api" {
      driver = "docker"
      config {
        image = "atlashub/pandawa-pms:v2.0.0"
      }

      env {
        PUGUH_AUTH_URL = "http://puguh-auth.service.consul:8001"
        PUGUH_RBAC_URL = "http://puguh-rbac.service.consul:8002"
      }

      service {
        name = "pandawa-pms"
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.pandawa-pms.rule=Host(`pms.atlashub.com`)"
        ]
      }
    }
  }
}
```

**Deploy**:
```bash
nomad job run -namespace=pandawa pms-backend.nomad
```

---

### Namespace: `shared`

**Purpose**: Shared infrastructure services
**Description**: Traefik, monitoring, logging, databases (shared across products)

**Services**:
- `traefik` - Reverse proxy & load balancer
- `consul` - Service discovery (run outside Nomad)
- `postgres-shared` - Shared PostgreSQL (if needed)
- `redis-shared` - Shared Redis cache
- `prometheus` - Metrics collection
- `grafana` - Monitoring dashboards
- `loki` - Log aggregation
- `tempo` - Distributed tracing

**Example Job**:
```hcl
job "postgres-shared" {
  namespace = "shared"  # ← Shared infrastructure

  datacenters = ["dc1"]
  type = "service"

  group "db" {
    volume "postgres_data" {
      type   = "host"
      source = "postgres_shared_data"
    }

    task "postgresql" {
      driver = "docker"
      config {
        image = "postgres:15-alpine"
      }

      service {
        name = "postgres-shared"
        tags = ["database", "shared"]
      }
    }
  }
}
```

---

## 🎯 Namespace Isolation Benefits

### 1. **Resource Quotas** (Optional)

Limit resources per namespace:

```hcl
# For production cluster
namespace "semar" {
  quota = "semar-quota"
}

# Quota definition
quota "semar-quota" {
  limit {
    region = "global"

    region_limit {
      cpu       = 10000  # 10 GHz total
      memory_mb = 20000  # 20 GB total
    }
  }
}
```

### 2. **RBAC per Namespace** (with ACL)

```hcl
# Team SEMAR hanya bisa akses namespace semar
policy "semar-team" {
  namespace "semar" {
    policy = "write"  # Full access to semar namespace
  }

  namespace "puguh" {
    policy = "read"   # Read-only access to puguh
  }

  namespace "pandawa" {
    policy = "deny"   # No access to pandawa
  }
}
```

### 3. **Job Naming Freedom**

Same job name bisa ada di namespace berbeda:

```bash
# SEMAR namespace
nomad job run -namespace=semar backend-api.nomad  # Job: backend-api

# PANDAWA namespace
nomad job run -namespace=pandawa backend-api.nomad  # Job: backend-api (different!)

# No conflict! ✅
```

---

## 📊 Service Discovery dengan Consul

Consul tags untuk cross-namespace service discovery:

```hcl
service {
  name = "puguh-auth"
  tags = [
    "product=puguh",
    "component=auth",
    "version=v1.0.0"
  ]
}
```

**Access dari namespace lain:**
```python
# SEMAR service calling PUGUH auth
AUTH_URL = "http://puguh-auth.service.consul:8001"
```

---

## 🚀 Deployment Workflow

### Deploy to specific namespace:

```bash
# Deploy SEMAR service
nomad job run -namespace=semar jarvis-backend.nomad

# Deploy PANDAWA service
nomad job run -namespace=pandawa pms-backend.nomad

# Deploy shared infra
nomad job run -namespace=shared traefik.nomad
```

### List jobs per namespace:

```bash
# All SEMAR jobs
nomad job status -namespace=semar

# All PANDAWA jobs
nomad job status -namespace=pandawa

# All jobs across all namespaces
nomad job status -namespace='*'
```

### Monitor specific namespace in UI:

```
http://31.97.111.175:4646/ui/jobs?namespace=semar
http://31.97.111.175:4646/ui/jobs?namespace=pandawa
http://31.97.111.175:4646/ui/jobs?namespace=puguh
```

---

## 🎨 Traefik Routing per Product

### URL Structure:

```
# PUGUH Control Plane
https://auth.atlashub.com       → puguh-auth service
https://rbac.atlashub.com       → puguh-rbac service
https://audit.atlashub.com      → puguh-audit service

# SEMAR Console
https://voice.atlashub.com      → semar-jarvis service
https://stt.atlashub.com        → semar-stt service

# PANDAWA Suite
https://pms.atlashub.com        → pandawa-pms service
https://pos.atlashub.com        → pandawa-pos service
https://signage.atlashub.com    → pandawa-signage-cms service
https://player.atlashub.com     → pandawa-signage-player service
```

### Traefik Tags Example:

```hcl
service {
  name = "pandawa-pms"
  tags = [
    "traefik.enable=true",
    "traefik.http.routers.pms.rule=Host(`pms.atlashub.com`)",
    "traefik.http.routers.pms.entrypoints=websecure",
    "traefik.http.routers.pms.tls.certresolver=letsencrypt"
  ]
}
```

---

## 📁 Folder Structure (Recommended)

```
atlashub-deployments/
├── namespaces/
│   ├── puguh.hcl
│   ├── semar.hcl
│   ├── pandawa.hcl
│   └── shared.hcl
│
├── jobs/
│   ├── puguh/
│   │   ├── auth-service.nomad
│   │   ├── rbac-service.nomad
│   │   └── audit-service.nomad
│   │
│   ├── semar/
│   │   ├── jarvis-backend.nomad
│   │   ├── stt-service.nomad
│   │   └── tts-service.nomad
│   │
│   ├── pandawa/
│   │   ├── pms-backend.nomad
│   │   ├── pos-backend.nomad
│   │   ├── signage-cms.nomad
│   │   └── signage-player.nomad
│   │
│   └── shared/
│       ├── traefik.nomad
│       ├── postgres.nomad
│       └── redis.nomad
│
└── scripts/
    ├── deploy-puguh.sh
    ├── deploy-semar.sh
    ├── deploy-pandawa.sh
    └── deploy-all.sh
```

---

## ✅ Best Practices

1. **Naming Convention**:
   - Service names: `{product}-{component}` (e.g., `puguh-auth`, `semar-jarvis`)
   - Job names: `{component}` (namespace already identifies product)

2. **Cross-Product Communication**:
   - Use Consul DNS: `{service-name}.service.consul`
   - SEMAR & PANDAWA always call PUGUH for auth/rbac

3. **Resource Allocation**:
   - PUGUH: Critical services, higher priority
   - SEMAR: Medium priority, moderate resources
   - PANDAWA: Largest resource allocation (most services)
   - Shared-infra: Always-on, high reliability

4. **Deployment Order**:
   ```bash
   1. shared (Traefik, databases)
   2. puguh (auth, rbac first!)
   3. semar (depends on puguh)
   4. pandawa (depends on puguh)
   ```

---

## 🎯 Summary

**ATLASHUB Platform** organized into:
- ✅ 4 Nomespaces (puguh, semar, pandawa, shared)
- ✅ Clear product separation
- ✅ Flexible resource management
- ✅ Easy RBAC implementation
- ✅ Clean service discovery
- ✅ Professional branding

**Next Steps**:
1. Create namespaces on Nomad cluster
2. Migrate existing jobs to appropriate namespaces
3. Setup Traefik routing per product
4. Implement RBAC (optional, for production)

---

**Last Updated**: 2026-01-01
**Version**: 1.0.0
