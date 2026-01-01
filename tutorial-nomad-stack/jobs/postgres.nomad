# Example: PostgreSQL Database
# Deploy dengan: nomad job run postgres.nomad

job "postgres" {
  datacenters = ["dc1"]
  type        = "service"

  group "db" {
    count = 1

    network {
      port "db" {
        static = 5432
      }
    }

    # Use host volume for persistence
    volume "postgres_data" {
      type   = "host"
      source = "postgres_data"
    }

    task "postgresql" {
      driver = "docker"

      config {
        image = "postgres:15-alpine"
        ports = ["db"]

        volumes = [
          "postgres_data:/var/lib/postgresql/data"
        ]
      }

      env {
        POSTGRES_DB       = "myapp"
        POSTGRES_USER     = "dbuser"
        POSTGRES_PASSWORD = "dbpassword"  # Use Vault in production!
      }

      volume_mount {
        volume      = "postgres_data"
        destination = "/var/lib/postgresql/data"
      }

      resources {
        cpu    = 1000
        memory = 1024
      }

      service {
        name = "postgres"
        port = "db"

        tags = ["database", "postgresql"]

        check {
          type     = "tcp"
          interval = "10s"
          timeout  = "2s"
        }
      }
    }
  }
}
