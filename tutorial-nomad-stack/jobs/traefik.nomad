job "traefik" {
  datacenters = ["dc1"]
  type        = "service"

  group "traefik" {
    count = 1

    network {
      mode = "host"  # Use host networking
      
      port "http" {
        static = 80
      }
      port "https" {
        static = 443
      }
      port "api" {
        static = 8081
      }
    }

    task "traefik" {
      driver = "docker"

      config {
        image = "traefik:v3.2"
        ports = ["http", "https", "api"]
        
        network_mode = "host"  # Critical: use host network

        args = [
          "--api.dashboard=true",
          "--api.insecure=true",

          # Consul provider
          "--providers.consulcatalog=true",
          "--providers.consulcatalog.endpoint.address=127.0.0.1:8500",
          "--providers.consulcatalog.exposedByDefault=false",
          "--providers.consulcatalog.prefix=traefik",

          # Entrypoints
          "--entrypoints.web.address=:80",
          "--entrypoints.websecure.address=:443",

          # Logging
          "--log.level=INFO",
          "--accesslog=true",
          
          # Ping endpoint for health check
          "--ping=true",
        ]
      }

      resources {
        cpu    = 500
        memory = 256
      }

      service {
        name = "traefik"
        port = "http"

        tags = [
          "traefik",
          "reverse-proxy"
        ]

        check {
          type     = "http"
          path     = "/ping"
          port     = "api"
          interval = "10s"
          timeout  = "2s"
        }
      }

      service {
        name = "traefik-dashboard"
        port = "api"

        tags = ["traefik-ui"]
      }
    }
  }
}
