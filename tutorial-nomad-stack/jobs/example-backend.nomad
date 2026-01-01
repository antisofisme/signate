# Example: Backend API Service (Python FastAPI)
# Deploy dengan: nomad job run example-backend.nomad

job "backend-api" {
  datacenters = ["dc1"]
  type        = "service"

  # Update strategy
  update {
    max_parallel      = 1
    min_healthy_time  = "10s"
    healthy_deadline  = "3m"
    progress_deadline = "10m"
    auto_revert       = true
  }

  group "api" {
    count = 1

    network {
      port "http" {
        to = 8001
      }
    }

    # Restart policy
    restart {
      attempts = 3
      interval = "5m"
      delay    = "25s"
      mode     = "fail"
    }

    task "fastapi" {
      driver = "docker"

      config {
        image = "python:3.12-slim"
        ports = ["http"]

        # Command to run
        command = "sh"
        args = [
          "-c",
          "pip install fastapi uvicorn && uvicorn main:app --host 0.0.0.0 --port 8001"
        ]

        # Mount volumes (optional)
        # volumes = [
        #   "/opt/app:/app"
        # ]
      }

      # Environment variables
      env {
        APP_ENV      = "production"
        DATABASE_URL = "postgresql://user:pass@postgres.service.consul:5432/db"
        REDIS_URL    = "redis://redis.service.consul:6379"
        LOG_LEVEL    = "info"
      }

      # Resource requirements
      resources {
        cpu    = 500  # MHz
        memory = 512  # MB
      }

      # Service registration to Consul
      service {
        name = "backend-api"
        port = "http"

        tags = [
          "api",
          "v1",
          "traefik.enable=true",
          "traefik.http.routers.backend.rule=Host(`api.example.com`)"
        ]

        # Health check
        check {
          type     = "http"
          path     = "/health"
          interval = "10s"
          timeout  = "2s"
        }
      }

      # Logging
      logs {
        max_files     = 5
        max_file_size = 10  # MB
      }
    }
  }
}
