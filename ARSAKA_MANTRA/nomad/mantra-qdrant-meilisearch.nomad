# ARSAKA_MANTRA Search Infrastructure - Nomad Job Definition
# Combined: Qdrant (Vector Search) + Meilisearch (Full-text Search)
#
# PURPOSE:
#   Search infrastructure for MANTRA constitutional law system:
#   - Qdrant: Vector similarity search for semantic search, alignment checking
#   - Meilisearch: Full-text search for keyword/faceted search
#
# GROUPING RATIONALE:
#   Both services are search-focused, stateless queries, and share:
#   - Similar resource profiles (low CPU, moderate memory)
#   - Same scaling characteristics
#   - Both used by backend for search operations
#
# Deploy: nomad job run -namespace=mantra mantra-qdrant-meilisearch.nomad
# Stop:   nomad job stop -namespace=mantra mantra-qdrant-meilisearch

job "mantra-qdrant-meilisearch" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "MANTRA Search Infrastructure - Qdrant + Meilisearch"
    previous_jobs = "mantra-qdrant, mantra-services (meilisearch group)"
  }

  # =========================================================================
  # Qdrant - Vector Database for Semantic Search
  # =========================================================================
  group "qdrant" {
    count = 1

    network {
      mode = "host"
      port "http" {
        static = 6335
      }
      port "grpc" {
        static = 6336
      }
    }

    service {
      name = "mantra-qdrant"
      port = "http"

      tags = [
        "mantra",
        "vector-db",
        "qdrant",
        "search-infrastructure",
      ]

      check {
        name     = "qdrant-health"
        type     = "http"
        path     = "/readyz"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "qdrant" {
      driver = "docker"

      config {
        image        = "qdrant/qdrant:v1.12.0"
        network_mode = "host"

        # Persistent storage
        volumes = [
          "/opt/arsaka-mantra/data/qdrant:/qdrant/storage"
        ]
      }

      env {
        QDRANT__SERVICE__GRPC_PORT = "6336"
        QDRANT__SERVICE__HTTP_PORT = "6335"
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

  # =========================================================================
  # Meilisearch - Full-text Search Engine
  # =========================================================================
  group "meilisearch" {
    count = 1

    network {
      mode = "host"
      port "http" {
        static = 7700
      }
    }

    service {
      name = "mantra-meilisearch"
      port = "http"

      tags = [
        "mantra",
        "search",
        "meilisearch",
        "search-infrastructure",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/health"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "meilisearch" {
      driver = "docker"

      config {
        image        = "getmeili/meilisearch:v1.6"
        network_mode = "host"

        # Persistent storage
        volumes = [
          "/opt/arsaka-mantra/data/meilisearch:/meili_data"
        ]
      }

      env {
        MEILI_NO_ANALYTICS = "true"
        MEILI_ENV          = "production"
      }

      template {
        data = <<EOF
{{- if keyExists "mantra/meilisearch_api_key" }}
MEILI_MASTER_KEY={{ key "mantra/meilisearch_api_key" }}
{{- else }}
MEILI_MASTER_KEY=mantra_meilisearch_master_key
{{- end }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 200
        memory = 512
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }
}
