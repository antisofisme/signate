# ARSAKA_MANTRA Frontend - Nomad Job Definition
# Decision Matrix Constitutional Law System - UI

job "mantra-frontend" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.4.0"
    description = "Decision Matrix UI - Layer B Detailed Content Display"
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
        image      = "arsaka-mantra-web:v1.4.0"
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
