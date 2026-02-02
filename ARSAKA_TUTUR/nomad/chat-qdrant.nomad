# ARSAKA_CHAT_AI Qdrant - Nomad Job Definition
# Vector Database for RAG

job "chat-qdrant" {
  datacenters = ["dc1"]
  namespace   = "chat"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ARSAKA Chat AI Vector Database"
  }

  group "vector" {
    count = 1

    network {
      port "http" {
        static = 6333
        to     = 6333
      }
      port "grpc" {
        static = 6334
        to     = 6334
      }
    }

    volume "qdrant_data" {
      type      = "host"
      source    = "chat-qdrant-data"
      read_only = false
    }

    service {
      name = "chat-qdrant"
      port = "http"

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
      }

      volume_mount {
        volume      = "qdrant_data"
        destination = "/qdrant/storage"
        read_only   = false
      }

      env {
        QDRANT__SERVICE__GRPC_PORT = "6334"
        QDRANT__LOG_LEVEL          = "INFO"
      }

      resources {
        cpu    = 256
        memory = 512
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }
}
