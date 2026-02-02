# ARSAKA_TUTUR Nomad Deployment

## Prerequisites

1. Create namespace:
```bash
nomad namespace apply -description "ATLAS Chat AI Service" chat
```

2. Create host volumes:
```bash
# Add to /etc/nomad.d/client.hcl:
host_volume "chat-postgres-data" {
  path      = "/opt/nomad-data/chat/postgres"
  read_only = false
}
host_volume "chat-qdrant-data" {
  path      = "/opt/nomad-data/chat/qdrant"
  read_only = false
}
host_volume "chat-redis-data" {
  path      = "/opt/nomad-data/chat/redis"
  read_only = false
}

# Create directories
mkdir -p /opt/nomad-data/chat/{postgres,qdrant,redis}
chmod 777 /opt/nomad-data/chat/*

# Restart Nomad
systemctl restart nomad
```

3. Add secrets to Consul KV:
```bash
consul kv put chat/db_password "YOUR_DB_PASSWORD"
consul kv put chat/jwt_secret "YOUR_64_CHAR_JWT_SECRET"
```

## Docker Images

Build images on VPS:
```bash
# API
docker build -t atlas-chat-api:v1.0.0 -f docker/Dockerfile .

# Frontend
docker build -t atlas-chat-admin:v1.0.0 -f frontend/Dockerfile ./frontend
```

## Deployment Order

```bash
# 1. Infrastructure
nomad job run -namespace=chat chat-postgres.nomad
nomad job run -namespace=chat chat-qdrant.nomad
nomad job run -namespace=chat chat-redis.nomad

# Wait for healthy
sleep 30

# 2. Application
nomad job run -namespace=chat chat-backend.nomad
nomad job run -namespace=chat chat-frontend.nomad
```

## Ports

| Service | Port |
|---------|------|
| PostgreSQL | 5433 |
| Qdrant | 6333, 6334 |
| Redis | 6380 |
| Backend API | 8003 |
| Frontend | 3003 |

## URLs

- API: http://31.97.111.175:8003/docs
- Admin: http://31.97.111.175:3003
- Domain: https://tutur.arsaka.io (via Traefik)
