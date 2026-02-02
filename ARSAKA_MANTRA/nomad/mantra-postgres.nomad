# ARSAKA_MANTRA PostgreSQL - Nomad Job Definition

job "mantra-postgres" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  group "database" {
    count = 1

    network {
      port "postgres" {
        static = 5434
        to     = 5432
      }
    }

    volume "postgres_data" {
      type      = "host"
      read_only = false
      source    = "mantra_postgres_data"
    }

    service {
      name = "mantra-postgres"
      port = "postgres"

      check {
        name     = "tcp"
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "postgres" {
      driver = "docker"

      config {
        image = "postgres:15-alpine"
        ports = ["postgres"]
      }

      volume_mount {
        volume      = "postgres_data"
        destination = "/var/lib/postgresql/data"
        read_only   = false
      }

      env {
        POSTGRES_USER = "mantra_owner"
        POSTGRES_DB   = "arsaka_mantra"
        PGDATA        = "/var/lib/postgresql/data/pgdata"
      }

      template {
        data = <<EOF
POSTGRES_PASSWORD={{ key "mantra/db_password" }}
EOF
        destination = "secrets/env"
        env         = true
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
