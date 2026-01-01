# Example: Redis Cache
# Deploy dengan: nomad job run redis.nomad

job "redis" {
  datacenters = ["dc1"]
  type        = "service"

  group "cache" {
    count = 1

    network {
      port "db" {
        static = 6379
      }
    }

    volume "redis_data" {
      type   = "host"
      source = "redis_data"
    }

    task "redis-server" {
      driver = "docker"

      config {
        image = "redis:7-alpine"
        ports = ["db"]

        args = [
          "--appendonly", "yes",
          "--maxmemory", "256mb",
          "--maxmemory-policy", "allkeys-lru"
        ]
      }

      volume_mount {
        volume      = "redis_data"
        destination = "/data"
      }

      resources {
        cpu    = 500
        memory = 512
      }

      service {
        name = "redis"
        port = "db"

        tags = ["cache", "redis"]

        check {
          type     = "tcp"
          interval = "10s"
          timeout  = "2s"
        }
      }
    }
  }
}
