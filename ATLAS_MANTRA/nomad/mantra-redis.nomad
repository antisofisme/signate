# ATLAS_MANTRA Redis - Nomad Job Definition
# Cache layer for semantic search results
#
# PURPOSE:
#   High-performance caching for:
#   - Semantic search results
#   - Embedding lookups
#   - Rate limiting (future)

job "mantra-redis" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "Redis cache for MANTRA semantic search"
  }

  group "cache" {
    count = 1

    network {
      port "redis" {
        static = 6380
        to     = 6379
      }
    }

    service {
      name         = "mantra-redis"
      port         = "redis"
      address_mode = "host"

      tags = [
        "mantra",
        "cache",
        "redis"
      ]

      check {
        name         = "redis-health"
        type         = "tcp"
        interval     = "10s"
        timeout      = "2s"
        address_mode = "host"
      }
    }

    task "redis" {
      driver = "docker"

      config {
        image        = "redis:7-alpine"
        network_mode = "host"

        args = [
          "redis-server",
          "--port", "6380",
          "--bind", "0.0.0.0",
          "--maxmemory", "256mb",
          "--maxmemory-policy", "allkeys-lru",
          "--appendonly", "no",
          "--save", ""
        ]
      }

      resources {
        cpu    = 128
        memory = 256
      }

      logs {
        max_files     = 3
        max_file_size = 5
      }
    }
  }
}
