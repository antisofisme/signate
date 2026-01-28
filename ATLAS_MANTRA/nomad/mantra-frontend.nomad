# ATLAS_MANTRA Frontend - Nomad Job Definition
# Decision Matrix Constitutional Law System - UI

job "mantra-frontend" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.3.0"
    description = "Decision Matrix UI - Domain/Aspect Terminology Rename"
  }

  group "web" {
    count = 1

    network {
      port "http" {
        static = 3001
        to     = 3000
      }
    }

    service {
      name = "mantra-frontend"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.mantra-web.rule=PathPrefix(`/`)",
        "traefik.http.routers.mantra-web.entrypoints=http",
        "traefik.http.routers.mantra-web.priority=1",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "frontend" {
      driver = "docker"

      config {
        image      = "atlas-mantra-web:v1.3.0"
        ports      = ["http"]
        force_pull = false
      }

      resources {
        cpu    = 128
        memory = 256
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }
}
