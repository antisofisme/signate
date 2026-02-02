# MANTRA MCP Server - Nomad Job Definition
# Remote MCP Server for Constitutional Law Decision System

job "mantra-mcp" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "2.0.0"
    description = "MANTRA MCP Server - Dual Transport (STDIO + Streamable HTTP)"
  }

  group "mcp" {
    count = 1

    network {
      port "http" {
        static = 8004
        to     = 8004
      }
    }

    service {
      name = "mantra-mcp"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.mantra-mcp.rule=PathPrefix(`/mcp`)",
        "traefik.http.routers.mantra-mcp.entrypoints=http",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/health"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "mcp-server" {
      driver = "docker"

      config {
        image      = "mantra-mcp-server:v2.0.0"
        ports      = ["http"]
        force_pull = false
      }

      env {
        NODE_ENV       = "production"
        HOST           = "0.0.0.0"
        PORT           = "8004"
        MANTRA_API_URL = "http://31.97.111.175:8002"
        CORS_ORIGINS   = "http://localhost:3000,http://localhost:5173,http://31.97.111.175:3001,*"

        # Master API key for admin access
        MANTRA_MCP_MASTER_KEY = "mk_master_mantra_constitutional_law_2026"
      }

      resources {
        cpu    = 128
        memory = 256
      }

      logs {
        max_files     = 5
        max_file_size = 10
      }
    }
  }
}
