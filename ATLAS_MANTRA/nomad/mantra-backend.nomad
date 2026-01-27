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
    version     = "1.3.1"
    description = "Decision Matrix Constitutional Law System - MICS 7-Stage Pipeline + YAML Agents"
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
        image      = "atlas-mantra-api:v1.3.1"
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

        # AI Configuration
        AI_PROVIDER = "openai"
        AI_MODEL    = "gpt-4o-mini"

        # Semantic Search Configuration
        ENABLE_SEMANTIC_SEARCH = "true"
        EMBEDDING_SERVICE      = "noop"
        EMBEDDING_MODEL        = "noop-embedding"
        EMBEDDING_DIMENSIONS   = "1536"
      }

      template {
        data = <<EOF
DATABASE_URL=postgresql://mantra_owner:{{ key "mantra/db_password" }}@{{ range service "mantra-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/atlas_mantra

# Vector Store (Qdrant) - use service port but hardcode IPv4 address for single-node setup
VECTOR_STORE=qdrant
QDRANT_URL=http://31.97.111.175:6335
QDRANT_COLLECTION=mantra_decisions

# Cache (Redis) - use service port but hardcode IPv4 address for single-node setup
CACHE=redis
REDIS_URL=redis://31.97.111.175:6380/0
CACHE_TTL=300

# AI API Keys (stored in Consul KV)
{{- if keyExists "mantra/openai_api_key" }}
OPENAI_API_KEY={{ key "mantra/openai_api_key" }}
{{- end }}
{{- if keyExists "mantra/deepseek_api_key" }}
DEEPSEEK_API_KEY={{ key "mantra/deepseek_api_key" }}
{{- end }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 200
        memory = 768
      }

      logs {
        max_files     = 5
        max_file_size = 10
      }
    }
  }
}
