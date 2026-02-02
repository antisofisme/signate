# ARSAKA_MANTRA MCP Server & Workers - Nomad Job Definition
# Async processing infrastructure (WITHOUT RabbitMQ - uses shared-rabbitmq)
#
# PURPOSE:
#   Async processing services for MANTRA:
#   - MCP Server: Remote MCP protocol server for Claude CLI integration
#   - Workers: Background processors for validation and embedding sync
#
# DEPENDENCIES:
#   - shared-rabbitmq (namespace: shared) - Message broker
#   - mantra-redis (namespace: mantra) - Cache layer
#   - mantra-postgres (namespace: mantra) - Database
#
# Deploy: nomad job run -namespace=mantra mantra-mcp-workers.nomad

job "mantra-mcp-workers" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.1.0"
    description = "MANTRA MCP Server + Workers (uses shared-rabbitmq)"
    depends_on  = "shared-rabbitmq"
  }

  # =========================================================================
  # MCP Server - Remote MCP Protocol for Claude CLI
  # =========================================================================
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
        "mantra",
        "mcp",
        "traefik.enable=true",
        "traefik.http.routers.mantra-mcp.rule=PathPrefix(`/mcp`)",
        "traefik.http.routers.mantra-mcp.entrypoints=http"
      ]

      check {
        name     = "mcp-health"
        type     = "http"
        path     = "/health"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "mcp-server" {
      driver = "docker"

      config {
        image      = "mantra-mcp-server:v1.0.0"
        ports      = ["http"]
        force_pull = false
      }

      env {
        NODE_ENV       = "production"
        HOST           = "0.0.0.0"
        PORT           = "8004"
        CORS_ORIGINS   = "http://localhost:3000,http://localhost:5173,https://mantra.arsaka.io,*"
      }

      template {
        data = <<EOF
MANTRA_API_URL=http://{{ range service "mantra-backend" }}{{ .Address }}:{{ .Port }}{{ end }}
MANTRA_MCP_MASTER_KEY={{ key "mantra/mcp_master_key" }}
EOF
        destination = "secrets/mcp.env"
        env         = true
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

  # =========================================================================
  # Workers - Background Processors
  # =========================================================================
  group "workers" {
    count = 1

    # Restart policy - give time for dependencies to be ready
    restart {
      attempts = 10
      interval = "5m"
      delay    = "30s"
      mode     = "delay"
    }

    task "validation-worker" {
      driver = "docker"

      config {
        image      = "arsaka-mantra-api:v2.0.0"
        force_pull = false

        # Run worker instead of API
        command = "python"
        args    = ["-m", "workers", "--worker", "validation"]
      }

      env {
        LOG_LEVEL = "INFO"

        # AI Configuration
        AI_PROVIDER = "openai"
        AI_MODEL    = "gpt-4o-mini"

        # Feature flags
        FEATURE_RABBITMQ_ENABLED    = "true"
        FEATURE_MEILISEARCH_ENABLED = "false"
        FEATURE_REDIS_ENHANCED_CACHE = "true"
      }

      template {
        data = <<EOF
# Database
DATABASE_URL=postgresql://mantra_owner:{{ key "mantra/db_password" }}@{{ range service "mantra-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/arsaka_mantra

# Vector Store - use Consul service discovery
VECTOR_STORE=qdrant
QDRANT_URL=http://{{ range service "mantra-qdrant" }}{{ .Address }}:{{ .Port }}{{ end }}
QDRANT_COLLECTION=mantra_decisions

# Cache - use Consul service discovery
CACHE=redis
REDIS_URL=redis://{{ range service "mantra-redis" }}{{ .Address }}:{{ .Port }}{{ end }}/0
CACHE_TTL=300

# RabbitMQ - use Consul service discovery
RABBITMQ_URL=amqp://mantra:{{ key "shared/rabbitmq_mantra_password" }}@{{ range service "shared-rabbitmq" }}{{ .Address }}:{{ .Port }}{{ end }}/mantra
RABBITMQ_EXCHANGE=mantra_events
RABBITMQ_QUEUE_VALIDATION=mantra_validation

# AI Keys
{{- if keyExists "mantra/openai_api_key" }}
OPENAI_API_KEY={{ key "mantra/openai_api_key" }}
{{- end }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 128
        memory = 384
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }

    task "sync-worker" {
      driver = "docker"

      config {
        image      = "arsaka-mantra-api:v2.0.0"
        force_pull = false

        # Run worker instead of API
        command = "python"
        args    = ["-m", "workers", "--worker", "sync"]
      }

      env {
        LOG_LEVEL = "INFO"

        # Feature flags
        FEATURE_RABBITMQ_ENABLED     = "true"
        FEATURE_MEILISEARCH_ENABLED  = "true"
        FEATURE_REDIS_ENHANCED_CACHE = "true"
      }

      template {
        data = <<EOF
# Database
DATABASE_URL=postgresql://mantra_owner:{{ key "mantra/db_password" }}@{{ range service "mantra-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/arsaka_mantra

# Vector Store - use Consul service discovery
VECTOR_STORE=qdrant
QDRANT_URL=http://{{ range service "mantra-qdrant" }}{{ .Address }}:{{ .Port }}{{ end }}
QDRANT_COLLECTION=mantra_decisions

# Cache - use Consul service discovery
CACHE=redis
REDIS_URL=redis://{{ range service "mantra-redis" }}{{ .Address }}:{{ .Port }}{{ end }}/0

# Meilisearch - use Consul service discovery
MEILISEARCH_URL=http://{{ range service "mantra-meilisearch" }}{{ .Address }}:{{ .Port }}{{ end }}
MEILISEARCH_INDEX_DECISIONS=mantra_decisions
{{- if keyExists "mantra/meilisearch_api_key" }}
MEILISEARCH_API_KEY={{ key "mantra/meilisearch_api_key" }}
{{- end }}

# RabbitMQ - use Consul service discovery
RABBITMQ_URL=amqp://mantra:{{ key "shared/rabbitmq_mantra_password" }}@{{ range service "shared-rabbitmq" }}{{ .Address }}:{{ .Port }}{{ end }}/mantra
RABBITMQ_EXCHANGE=mantra_events
RABBITMQ_QUEUE_SYNC=mantra_sync
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 128
        memory = 384
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }
}
