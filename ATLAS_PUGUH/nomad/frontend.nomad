# ATLAS_PUGUH - Frontend (Phase A+)
# Deploy: nomad job run -namespace=puguh frontend.nomad

job "puguh-frontend" {
  datacenters = ["dc1"]
  namespace   = "puguh"
  type        = "service"

  # Update strategy
  update {
    max_parallel      = 1
    min_healthy_time  = "10s"
    healthy_deadline  = "3m"
    progress_deadline = "5m"
    auto_revert       = true
    canary            = 0
  }

  group "web" {
    count = 1

    # Network configuration
    network {
      mode = "bridge"

      port "http" {
        to = 80
        static = 3000  # Static port untuk frontend
      }
    }

    # Restart policy
    restart {
      attempts = 3
      interval = "5m"
      delay    = "15s"
      mode     = "fail"
    }

    task "nginx" {
      driver = "docker"

      config {
        # Build image dari Dockerfile
        # Atau upload pre-built image ke registry
        image = "atlas-puguh-frontend:phase-a"

        ports = ["http"]

        # Build from Dockerfile (development)
        # Uncomment jika mau build di server
        # build {
        #   context = "/opt/atlas-puguh/frontend"
        # }
      }

      # Environment variables (minimal untuk nginx)
      env {
        NGINX_HOST = "0.0.0.0"
        NGINX_PORT = "80"
      }

      # Resource allocation
      resources {
        cpu    = 200   # 200 MHz
        memory = 256   # 256 MB
      }

      # Service registration in Consul
      service {
        name = "puguh-frontend"
        port = "http"

        tags = [
          "frontend",
          "nginx",
          "phase-a",
          "puguh",

          # Traefik tags (jika mau pakai domain)
          "traefik.enable=true",
          "traefik.http.routers.puguh-frontend.rule=Host(`puguh.atlashub.com`) || PathPrefix(`/`)",
          "traefik.http.routers.puguh-frontend.entrypoints=web",
        ]

        # Health check
        check {
          name     = "http-health"
          type     = "http"
          path     = "/health"
          interval = "30s"
          timeout  = "3s"

          check_restart {
            limit           = 3
            grace           = "10s"
            ignore_warnings = false
          }
        }

        # TCP check
        check {
          name     = "tcp-alive"
          type     = "tcp"
          interval = "30s"
          timeout  = "3s"
        }
      }

      # Logging
      logs {
        max_files     = 5
        max_file_size = 10
      }

      # Graceful shutdown
      kill_timeout = "10s"
      kill_signal  = "SIGTERM"
    }
  }
}
