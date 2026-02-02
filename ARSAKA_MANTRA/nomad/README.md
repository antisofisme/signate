# ARSAKA_MANTRA Nomad Deployment

## Overview

Nomad job definitions for deploying ARSAKA_MANTRA to production.

## Jobs

| Job | Description | Port |
|-----|-------------|------|
| `mantra-postgres` | PostgreSQL database | 5433 |
| `mantra-backend` | FastAPI backend | Dynamic |

## Prerequisites

1. Nomad cluster with namespace `mantra`
2. Consul for service discovery
3. Docker registry with `arsaka-mantra-api` image

## Deployment

### 1. Create Namespace

```bash
nomad namespace apply mantra
```

### 2. Set Secrets in Consul KV

```bash
consul kv put mantra/db_password "your_secure_password"
```

### 3. Create Host Volume

```bash
# On each Nomad client
mkdir -p /opt/mantra/postgres_data
```

Update `/etc/nomad.d/client.hcl`:

```hcl
client {
  host_volume "mantra_postgres_data" {
    path      = "/opt/mantra/postgres_data"
    read_only = false
  }
}
```

### 4. Deploy Jobs

```bash
# Deploy database first
nomad job run mantra-postgres.nomad

# Wait for database to be healthy
nomad job status -namespace=mantra mantra-postgres

# Deploy backend
nomad job run mantra-backend.nomad
```

### 5. Verify

```bash
# Check jobs
nomad job status -namespace=mantra

# Check services
consul catalog services | grep mantra

# Test health
curl http://<nomad-client>:<port>/health
```

## Scaling

```bash
# Scale backend
nomad job scale -namespace=mantra mantra-backend api 3
```

## Monitoring

```bash
# View logs
nomad alloc logs -namespace=mantra <alloc-id>

# View metrics
curl http://<backend>/api/v1/health
```

## Cleanup

```bash
nomad job stop -namespace=mantra mantra-backend
nomad job stop -namespace=mantra mantra-postgres
```
