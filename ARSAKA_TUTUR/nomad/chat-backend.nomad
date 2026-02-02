# ARSAKA_CHAT_AI Backend - Nomad Job Definition
# RAG Chat API with 4-Layer Memory

job "chat-backend" {
  datacenters = ["dc1"]
  namespace   = "chat"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ARSAKA Chat AI - RAG Chat with Memory"
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
      name = "chat-backend"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.chat-api.rule=Host(`api.tutur.arsaka.io`)",
        "traefik.http.routers.chat-api.entrypoints=websecure",
        "traefik.http.routers.chat-api.tls=true",
        "traefik.http.routers.chat-api.tls.certresolver=letsencrypt",
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
        image        = "arsaka-chat-api:v1.0.0"
        ports        = ["http"]
        force_pull   = false
        network_mode = "host"
      }

      env {
        # App
        ENVIRONMENT = "production"
        DEBUG       = "false"
        APP_NAME    = "ARSAKA_CHAT_AI"
        APP_VERSION = "1.0.0"
        HOST        = "0.0.0.0"
        PORT        = "8003"
        LOG_LEVEL   = "INFO"
        LOG_FORMAT  = "json"

        # AI Providers (set via Nomad variables or replace with actual keys)
        OPENAI_API_KEY         = "${OPENAI_API_KEY}"
        OPENAI_MODEL           = "gpt-4o-mini"
        OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
        DEEPSEEK_API_KEY       = "${DEEPSEEK_API_KEY}"

        # CORS
        CORS_ORIGINS = "https://tutur.arsaka.io,http://localhost:3003,http://31.97.111.175:3003"

        # Rate Limiting
        RATE_LIMIT_ENABLED = "true"
        RATE_LIMIT_CHAT    = "30"
        RATE_LIMIT_SEARCH  = "60"
        RATE_LIMIT_GENERAL = "120"
      }

      template {
        data = <<EOF
# Database - using IPv6 address (Nomad allocates IPv6)
DATABASE_URL=postgresql://chat_owner@[2a02:4780:59:ca9a::1]:5433/arsaka_tutur

# Vector Store
QDRANT_URL=http://31.97.111.175:6333

# Redis
REDIS_URL=redis://31.97.111.175:6380/0

# JWT Secret
JWT_SECRET_KEY={{ key "chat/jwt_secret" }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 512
        memory = 1024
      }

      logs {
        max_files     = 5
        max_file_size = 10
      }
    }
  }
}
