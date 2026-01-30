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
    version     = "1.7.0"
    description = "Decision Matrix - CORE Implementation (Schema Facade, Exceptions, Monitoring, Jobs)"
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
        image      = "atlas-mantra-api:v1.7.0"
        ports      = ["http"]
        force_pull = false

        # Ensure binding to all interfaces including IPv4
        port_map {
          http = 8001
        }
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
        EMBEDDING_SERVICE      = "openai"
        EMBEDDING_MODEL        = "text-embedding-3-small"
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

# Meilisearch (Full-text Search)
MEILISEARCH_URL=http://31.97.111.175:7700
MEILISEARCH_INDEX_DECISIONS=mantra_decisions
{{- if keyExists "mantra/meilisearch_api_key" }}
MEILISEARCH_API_KEY={{ key "mantra/meilisearch_api_key" }}
{{- end }}

# RabbitMQ (Message Queue)
RABBITMQ_URL=amqp://mantra:{{ keyOrDefault "mantra/rabbitmq_password" "mantra_mq" }}@31.97.111.175:5672/mantra
RABBITMQ_EXCHANGE=mantra_events
RABBITMQ_QUEUE_VALIDATION=mantra_validation
RABBITMQ_QUEUE_SYNC=mantra_sync

# Feature Flags (services disabled by default, enable via Consul KV)
FEATURE_REDIS_ENHANCED_CACHE={{ keyOrDefault "mantra/feature_redis_enhanced" "true" }}
FEATURE_MEILISEARCH_ENABLED={{ keyOrDefault "mantra/feature_meilisearch" "false" }}
FEATURE_RABBITMQ_ENABLED={{ keyOrDefault "mantra/feature_rabbitmq" "false" }}

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
