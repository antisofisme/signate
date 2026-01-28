# ATLAS_MANTRA Async Processing Infrastructure - Nomad Job Definition
# Combined: RabbitMQ (Message Queue) + MCP Server + Workers
#
# PURPOSE:
#   Async processing infrastructure for MANTRA constitutional law system:
#   - RabbitMQ: Message broker for async validation and sync events
#   - MCP Server: Remote MCP protocol server for Claude CLI integration
#   - Workers: Background processors for validation and embedding sync
#
# GROUPING RATIONALE:
#   All services are part of the async/event processing pipeline:
#   - RabbitMQ: Event bus for workers
#   - Workers: Consume events from RabbitMQ
#   - MCP Server: Connects to backend API (stateless)
#   Strong dependencies and shared lifecycle
#
# Deploy: nomad job run -namespace=mantra mantra-rabbitmq-mcp-workers.nomad
# Stop:   nomad job stop -namespace=mantra mantra-rabbitmq-mcp-workers

job "mantra-rabbitmq-mcp-workers" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "MANTRA Async Processing - RabbitMQ + MCP Server + Workers"
    previous_jobs = "mantra-services (rabbitmq group), mantra-mcp"
  }

  # =========================================================================
  # RabbitMQ - Message Queue
  # =========================================================================
  group "rabbitmq" {
    count = 1

    network {
      mode = "host"
      port "amqp" {
        static = 5672
      }
      port "mgmt" {
        static = 15672
      }
    }

    service {
      name = "mantra-rabbitmq"
      port = "amqp"

      tags = [
        "mantra",
        "queue",
        "rabbitmq",
        "async-infrastructure",
      ]

      check {
        name     = "health"
        type     = "tcp"
        interval = "30s"
        timeout  = "5s"
      }
    }

    service {
      name = "mantra-rabbitmq-mgmt"
      port = "mgmt"

      tags = [
        "mantra",
        "management",
        "rabbitmq-ui",
      ]
    }

    task "rabbitmq" {
      driver = "docker"

      config {
        image        = "rabbitmq:3.12-management-alpine"
        network_mode = "host"

        # Persistent storage
        volumes = [
          "/opt/atlas-mantra/data/rabbitmq:/var/lib/rabbitmq"
        ]
      }

      env {
        RABBITMQ_DEFAULT_USER  = "mantra"
        RABBITMQ_DEFAULT_VHOST = "mantra"
      }

      template {
        data = <<EOF
RABBITMQ_DEFAULT_PASS={{ keyOrDefault "mantra/rabbitmq_password" "mantra_mq_password" }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 200
        memory = 256
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }

  # =========================================================================
  # MCP Server - Remote MCP Protocol for Claude CLI
  # =========================================================================
  group "mcp" {
    count = 1

    # Wait for backend to be available
    constraint {
      attribute = "${node.unique.id}"
      operator  = "is_set"
    }

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
        "async-infrastructure",
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
        image      = "mantra-mcp-server:v1.0.0"
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

  # =========================================================================
  # Workers - Background Processors
  # =========================================================================
  group "workers" {
    count = 1

    # Wait for RabbitMQ to be available
    constraint {
      attribute = "${node.unique.id}"
      operator  = "is_set"
    }

    # Restart policy - give time for RabbitMQ to be ready
    restart {
      attempts = 10
      interval = "5m"
      delay    = "30s"
      mode     = "delay"
    }

    task "validation-worker" {
      driver = "docker"

      config {
        image      = "atlas-mantra-api:v1.6.3"
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

        # Feature flags - workers need RabbitMQ enabled
        FEATURE_RABBITMQ_ENABLED = "true"
        FEATURE_MEILISEARCH_ENABLED = "false"
        FEATURE_REDIS_ENHANCED_CACHE = "true"
      }

      template {
        data = <<EOF
DATABASE_URL=postgresql://mantra_owner:{{ key "mantra/db_password" }}@{{ range service "mantra-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/atlas_mantra

# Vector Store
VECTOR_STORE=qdrant
QDRANT_URL=http://31.97.111.175:6335
QDRANT_COLLECTION=mantra_decisions

# Cache
CACHE=redis
REDIS_URL=redis://31.97.111.175:6380/0
CACHE_TTL=300

# RabbitMQ
RABBITMQ_URL=amqp://mantra:{{ keyOrDefault "mantra/rabbitmq_password" "mantra_mq_password" }}@31.97.111.175:5672/mantra
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
        image      = "atlas-mantra-api:v1.6.3"
        force_pull = false

        # Run worker instead of API
        command = "python"
        args    = ["-m", "workers", "--worker", "sync"]
      }

      env {
        LOG_LEVEL = "INFO"

        # Feature flags
        FEATURE_RABBITMQ_ENABLED = "true"
        FEATURE_MEILISEARCH_ENABLED = "true"
        FEATURE_REDIS_ENHANCED_CACHE = "true"
      }

      template {
        data = <<EOF
DATABASE_URL=postgresql://mantra_owner:{{ key "mantra/db_password" }}@{{ range service "mantra-postgres" }}{{ .Address }}:{{ .Port }}{{ end }}/atlas_mantra

# Vector Store
VECTOR_STORE=qdrant
QDRANT_URL=http://31.97.111.175:6335
QDRANT_COLLECTION=mantra_decisions

# Cache
CACHE=redis
REDIS_URL=redis://31.97.111.175:6380/0

# Meilisearch
MEILISEARCH_URL=http://31.97.111.175:7700
MEILISEARCH_INDEX_DECISIONS=mantra_decisions
{{- if keyExists "mantra/meilisearch_api_key" }}
MEILISEARCH_API_KEY={{ key "mantra/meilisearch_api_key" }}
{{- end }}

# RabbitMQ
RABBITMQ_URL=amqp://mantra:{{ keyOrDefault "mantra/rabbitmq_password" "mantra_mq_password" }}@31.97.111.175:5672/mantra
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
