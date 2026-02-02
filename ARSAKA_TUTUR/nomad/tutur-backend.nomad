# ARSAKA_TUTUR Backend - Nomad Job Definition
# AI Chat Platform with RAG and Memory

job "tutur-backend" {
  datacenters = ["dc1"]
  namespace   = "tutur"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ARSAKA TUTUR - AI Chat Platform"
  }

  group "api" {
    count = 1

    network {
      port "http" {
        static = 8003
        to     = 8003
      }
    }

    service {
      name = "tutur-backend"
      port = "http"

      tags = [
        "tutur",
        "backend",
        "traefik.enable=true",
        "traefik.http.routers.tutur-api.rule=PathPrefix(`/api`)",
        "traefik.http.routers.tutur-api.entrypoints=http",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "backend" {
      driver = "docker"

      config {
        image      = "arsaka-tutur-api:v1.0.0"
        ports      = ["http"]
        force_pull = false
      }

      env {
        # App
        ENVIRONMENT = "production"
        DEBUG       = "false"
        APP_NAME    = "ARSAKA_TUTUR"
        APP_VERSION = "1.0.0"
        HOST        = "0.0.0.0"
        PORT        = "8003"
        LOG_LEVEL   = "INFO"
        LOG_FORMAT  = "json"

        # AI Providers
        OPENAI_MODEL           = "gpt-4o-mini"
        OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

        # CORS
        CORS_ORIGINS = "http://localhost:3003,https://tutur.arsaka.io"

        # Rate Limiting
        RATE_LIMIT_ENABLED = "true"
        RATE_LIMIT_CHAT    = "30"
        RATE_LIMIT_SEARCH  = "60"
        RATE_LIMIT_GENERAL = "120"
      }

      template {
        data = <<EOF
# Database - use Consul service discovery
DATABASE_URL=postgresql://tutur_owner:{{ key "tutur/db_password" }}@{{ range service "tutur-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/arsaka_tutur

# Vector Store (Qdrant) - use Consul service discovery
QDRANT_URL=http://{{ range service "mantra-qdrant" }}{{ .Address }}:{{ .Port }}{{ end }}

# Redis - use Consul service discovery
REDIS_URL=redis://{{ range service "mantra-redis" }}{{ .Address }}:{{ .Port }}{{ end }}/1

# AI API Keys
OPENAI_API_KEY={{ key "tutur/openai_api_key" }}

# JWT Secret
JWT_SECRET_KEY={{ key "tutur/jwt_secret" }}
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
