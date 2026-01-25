# ATLAS_CHAT_AI Frontend - Nomad Job Definition
# Admin CMS Dashboard

job "chat-frontend" {
  datacenters = ["dc1"]
  namespace   = "chat"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ATLAS Chat AI Admin Dashboard"
  }

  group "web" {
    count = 1

    network {
      port "http" {
        static = 3003
        to     = 80
      }
    }

    service {
      name = "chat-frontend"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.chat-admin.rule=Host(`chat.atlashub.site`)",
        "traefik.http.routers.chat-admin.entrypoints=websecure",
        "traefik.http.routers.chat-admin.tls=true",
        "traefik.http.routers.chat-admin.tls.certresolver=letsencrypt",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/health"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "frontend" {
      driver = "docker"

      config {
        image      = "atlas-chat-admin:v1.0.0"
        ports      = ["http"]
        force_pull = false
      }

      resources {
        cpu    = 128
        memory = 128
      }

      logs {
        max_files     = 3
        max_file_size = 5
      }
    }
  }
}
