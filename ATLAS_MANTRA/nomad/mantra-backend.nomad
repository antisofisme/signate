# ATLAS_MANTRA Backend - Nomad Job Definition
# Decision Matrix Constitutional Law System
#
# SECURITY MODEL:
#   Backend connects as mantra_app (restricted role).
#   mantra_app has SELECT + INSERT only.
#   NO UPDATE. NO DELETE. NO ALTER. NO TRIGGER.

job "mantra-backend" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "Decision Matrix Constitutional Law System"
  }

  group "api" {
    count = 1

    network {
      port "http" {
        static = 8002
        to     = 8001
      }
    }

    service {
      name = "mantra-backend"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.mantra-api.rule=PathPrefix(`/api`)",
        "traefik.http.routers.mantra-api.entrypoints=http",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/health"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "backend" {
      driver = "docker"

      config {
        image      = "atlas-mantra-api:v1.0.0"
        ports      = ["http"]

        # Use local image, don't try to pull from registry
        force_pull = false
      }

      env {
        HOST        = "0.0.0.0"
        PORT        = "8001"
        LOG_LEVEL   = "INFO"
        ENABLE_DOCS = "true"
        CORS_ORIGINS = "http://localhost:3000,http://localhost:5173,http://31.97.111.175:3001"
      }

      template {
        data = <<EOF
DATABASE_URL=postgresql://mantra_owner:{{ key "mantra/db_password" }}@{{ range service "mantra-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/atlas_mantra
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 256
        memory = 512
      }

      logs {
        max_files     = 5
        max_file_size = 10
      }
    }
  }
}
