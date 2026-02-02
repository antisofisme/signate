# ARSAKA_PUGUH Redis - Nomad Job Definition
# Dedicated Redis for PUGUH authentication & rate limiting
#
# PURPOSE:
#   Security-critical caching for:
#   - JWT token blacklist
#   - Rate limiting counters
#   - Session data
#   - API key cache
#
# SECURITY NOTE:
#   This Redis is SEPARATE from MANTRA Redis for fault isolation.
#   Auth tokens must not be affected by other service's cache pressure.
#
# Deploy: nomad job run -namespace=puguh puguh-redis.nomad

job "puguh-redis" {
  datacenters = ["dc1"]
  namespace   = "puguh"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "Dedicated Redis for PUGUH auth & rate limiting"
    security    = "high"
  }

  group "cache" {
    count = 1

    network {
      port "redis" {
        static = 6381  # Different from mantra-redis (6380)
        to     = 6379
      }
    }

    service {
      name         = "puguh-redis"
      port         = "redis"
      address_mode = "host"

      tags = [
        "puguh",
        "cache",
        "redis",
        "auth-critical"
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
          "--port", "6381",
          "--bind", "0.0.0.0",
          # Memory settings - auth data is small but critical
          "--maxmemory", "128mb",
          "--maxmemory-policy", "volatile-lru",  # Only evict keys with TTL
          # Persistence - optional for auth tokens (they have TTL anyway)
          "--appendonly", "no",
          "--save", "",
          # Security
          "--protected-mode", "no",
          # Performance
          "--tcp-keepalive", "300"
        ]
      }

      resources {
        cpu    = 100
        memory = 128
      }

      logs {
        max_files     = 3
        max_file_size = 5
      }
    }
  }
}
