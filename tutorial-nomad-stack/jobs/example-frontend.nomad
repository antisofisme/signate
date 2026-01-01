# Example: Frontend Service (React/Vite)
# Deploy dengan: nomad job run example-frontend.nomad

job "frontend" {
  datacenters = ["dc1"]
  type        = "service"

  group "web" {
    count = 1

    network {
      port "http" {
        static = 3000
      }
    }

    task "react-app" {
      driver = "docker"

      config {
        image = "node:20-alpine"
        ports = ["http"]

        command = "sh"
        args = [
          "-c",
          "npm install -g serve && serve -s build -l 3000"
        ]
      }

      env {
        NODE_ENV         = "production"
        VITE_API_URL     = "http://api.example.com"
        VITE_PLAYER_URL  = "http://player.example.com"
      }

      resources {
        cpu    = 256
        memory = 256
      }

      service {
        name = "frontend"
        port = "http"

        tags = [
          "frontend",
          "traefik.enable=true",
          "traefik.http.routers.frontend.rule=Host(`app.example.com`)"
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
