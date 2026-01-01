job "whoami" {
  datacenters = ["dc1"]
  type = "service"

  group "web" {
    count = 2  # Deploy 2 instances for load balancing demo

    network {
      port "http" {
        to = 80
      }
    }

    task "whoami" {
      driver = "docker"

      config {
        image = "traefik/whoami:latest"
        ports = ["http"]
      }

      resources {
        cpu    = 100
        memory = 64
      }

      service {
        name = "whoami"
        port = "http"

        tags = [
          "traefik.enable=true",
          "traefik.http.routers.whoami.rule=PathPrefix(`/`)",
          "traefik.http.routers.whoami.entrypoints=web",
        ]

        check {
          type     = "http"
          path     = "/"
          interval = "10s"
          timeout  = "2s"
        }
      }
    }
  }
}
