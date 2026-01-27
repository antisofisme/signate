# ATLAS_MANTRA Qdrant - Nomad Job Definition
# Vector database for semantic search
#
# PURPOSE:
#   High-performance vector similarity search for:
#   - Semantic search of decisions
#   - Alignment checking
#   - Finding related decisions

job "mantra-qdrant" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "Qdrant vector database for MANTRA semantic search"
  }

  group "vector" {
    count = 1

    network {
      port "http" {
        static = 6335
        to     = 6333
      }
      port "grpc" {
        static = 6336
        to     = 6334
      }
    }

    service {
      name = "mantra-qdrant"
      port = "http"

      tags = [
        "mantra",
        "vector-db",
        "qdrant"
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
        image = "qdrant/qdrant:v1.12.0"
        ports = ["http", "grpc"]

        # Use local directory for storage (will be lost if task moves)
        # For production, configure a proper host volume
        volumes = [
          "/opt/atlas-mantra/data/qdrant:/qdrant/storage"
        ]
      }

      env {
        QDRANT__SERVICE__GRPC_PORT = "6334"
        QDRANT__SERVICE__HTTP_PORT = "6333"
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
