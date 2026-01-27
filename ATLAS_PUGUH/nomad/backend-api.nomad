# ATLAS_PUGUH - Backend API (Phase A)
# Deploy: nomad job run -namespace=puguh backend-api.nomad

job "puguh-backend" {
  datacenters = ["dc1"]
  namespace   = "puguh"
  type        = "service"

  # Update strategy (rolling update)
  update {
    max_parallel      = 1
    min_healthy_time  = "30s"
    healthy_deadline  = "5m"
    progress_deadline = "10m"
    auto_revert       = true  # Rollback on failure
    canary            = 0     # No canary deployment in Phase A
  }

  group "api" {
    count = 1  # Phase A: Single instance

    # Network configuration
    network {
      mode = "bridge"  # Use bridge network for Consul Connect readiness

      port "http" {
        to     = 8001  # Container internal port
        static = 8001  # Static host port for stable frontend connection
      }
    }

    # Restart policy
    restart {
      attempts = 3
      interval = "5m"
      delay    = "30s"
      mode     = "fail"
    }

    task "fastapi" {
      driver = "docker"

      config {
        # Use custom built image (build and push to registry first)
        # OR use generic Python image + install deps at runtime (slower)

        # Option 1: Custom image (recommended)
        # image = "your-registry/atlas-puguh-backend:phase-a"

        # Option 2: Build from source (development)
        image = "python:3.11-slim"

        ports = ["http"]

        # Command to run (Option 2 only - install deps + run)
        command = "sh"
        args = [
          "-c",
          "apt-get update && apt-get install -y --no-install-recommends gcc postgresql-client curl && cd /app && pip install --no-cache-dir -r requirements-phase-a.txt && uvicorn core.app:app --host 0.0.0.0 --port 8001 --log-level debug"
        ]

        # Mount application code
        # OPTION A: Build Docker image with code baked in (recommended)
        # OPTION B: Mount from host (development only)
        volumes = [
          "/root/atlas-puguh/backend:/app:ro"  # Mount from host
        ]

        # Force pull image
        force_pull = false  # Set to true in production
      }

      # Application code as artifact (Option 3: download from repo)
      # artifact {
      #   source      = "https://github.com/your-org/atlas-puguh/archive/main.zip"
      #   destination = "local/app"
      #   mode        = "dir"
      # }

      # Environment variables (Phase A Configuration)
      env {
        # Environment
        ENVIRONMENT = "phase-a-staging"

        # Database (direct IP - Consul DNS not available in Docker bridge mode)
        DATABASE_URL = "postgresql+asyncpg://atlas_user:TBBQrXTZezvF8cybncpno686lSDA9_E6@31.97.111.175:5433/atlas_puguh"

        # JWT Authentication
        JWT_SECRET_KEY = "CHANGE_THIS_TO_RANDOM_32_CHAR_STRING_PRODUCTION"
        JWT_ALGORITHM = "HS256"
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES = "60"

        # Tenant (Hardcoded for Phase A)
        ALLOWED_TENANT_IDS = "550e8400-e29b-41d4-a716-446655440000"

        # Infrastructure - CACHING (DISABLED)
        REDIS_ENABLED = "false"
        REDIS_URL = ""

        # Infrastructure - RATE LIMITING (DISABLED)
        RATE_LIMIT_ENABLED = "false"

        # Infrastructure - OBSERVABILITY (MINIMAL)
        LOG_LEVEL = "DEBUG"
        LOG_FORMAT = "json"
        ENABLE_METRICS = "false"
        ENABLE_TRACING = "false"
        JAEGER_ENDPOINT = ""

        # Infrastructure - DATABASE CONNECTION POOLING (MINIMAL)
        POOL_SIZE = "2"
        MAX_OVERFLOW = "3"
        POOL_TIMEOUT = "10"
        POOL_RECYCLE = "3600"
        POOL_PRE_PING = "true"

        # API Configuration
        CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://31.97.111.175:3000,http://puguh-frontend.service.consul,https://admin-puguh.atlashub.com,https://puguh.atlashub.com"
        API_BASE_URL = "http://puguh-backend.service.consul:8001"

        # Phase A Warnings
        PHASE_A_WARNING = "⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED WITHOUT NOTICE"
        API_VERSION = "phase-a-unstable"
      }

      # Template for secrets (TODO: Use Vault in Phase B)
      # template {
      #   data = <<EOF
      # DATABASE_URL={{ with secret "secret/data/puguh/database" }}{{ .Data.data.url }}{{ end }}
      # JWT_SECRET_KEY={{ with secret "secret/data/puguh/jwt" }}{{ .Data.data.secret }}{{ end }}
      # EOF
      #   destination = "secrets/app.env"
      #   env         = true
      # }

      # Resource allocation (Phase A: minimal)
      resources {
        cpu    = 500   # 500 MHz (0.25 core)
        memory = 512   # 512 MB RAM
      }

      # Service registration in Consul
      service {
        name = "puguh-backend"
        port = "http"

        tags = [
          "api",
          "fastapi",
          "phase-a",
          "puguh",

          # Traefik tags for auto-discovery
          "traefik.enable=true",
          "traefik.http.routers.puguh-backend.rule=Host(`api-puguh.atlashub.com`) || PathPrefix(`/api/v1`)",
          "traefik.http.routers.puguh-backend.entrypoints=web",
          # TODO Phase B: Add HTTPS
          # "traefik.http.routers.puguh-backend.entrypoints=websecure",
          # "traefik.http.routers.puguh-backend.tls=true",
          # "traefik.http.routers.puguh-backend.tls.certresolver=letsencrypt",
        ]

        # Health check
        check {
          name     = "http-health"
          type     = "http"
          path     = "/health"
          interval = "30s"
          timeout  = "5s"

          check_restart {
            limit           = 3
            grace           = "15s"
            ignore_warnings = false
          }
        }

        # Additional TCP check (port availability)
        check {
          name     = "tcp-alive"
          type     = "tcp"
          interval = "30s"
          timeout  = "5s"
        }
      }

      # Logging configuration
      logs {
        max_files     = 10
        max_file_size = 20  # MB
      }

      # Graceful shutdown
      kill_timeout = "30s"
      kill_signal  = "SIGTERM"
    }
  }
}
