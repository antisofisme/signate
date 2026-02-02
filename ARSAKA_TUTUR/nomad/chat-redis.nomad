# ARSAKA_CHAT_AI Redis - Nomad Job Definition
# Cache and Queue

job "chat-redis" {
  datacenters = ["dc1"]
  namespace   = "chat"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ARSAKA Chat AI Cache and Queue"
  }

  group "cache" {
    count = 1

    network {
      port "redis" {
        static = 6380
        to     = 6379
      }
    }

    volume "redis_data" {
      type      = "host"
      source    = "chat-redis-data"
      read_only = false
    }

    service {
      name = "chat-redis"
      port = "redis"

      check {
        name     = "redis-health"
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "redis" {
      driver = "docker"

      config {
        image = "redis:7-alpine"
        ports = ["redis"]

        args = [
          "redis-server",
          "--maxmemory", "256mb",
          "--maxmemory-policy", "allkeys-lru",
          "--appendonly", "yes"
        ]
      }

      volume_mount {
        volume      = "redis_data"
        destination = "/data"
        read_only   = false
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
