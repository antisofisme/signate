# ARSAKA_TUTUR PostgreSQL - Nomad Job Definition
# Chat AI Database

job "tutur-postgres" {
  datacenters = ["dc1"]
  namespace   = "tutur"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ARSAKA TUTUR PostgreSQL Database"
  }

  group "database" {
    count = 1

    network {
      port "db" {
        static = 5435
        to     = 5432
      }
    }

    volume "postgres_data" {
      type      = "host"
      source    = "tutur-postgres-data"
      read_only = false
    }

    service {
      name = "tutur-postgres"
      port = "db"

      check {
        name     = "postgres-health"
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "postgres" {
      driver = "docker"

      config {
        image = "postgres:15-alpine"
        ports = ["db"]

        volumes = [
          "local/init.sql:/docker-entrypoint-initdb.d/init.sql:ro"
        ]
      }

      volume_mount {
        volume      = "postgres_data"
        destination = "/var/lib/postgresql/data"
        read_only   = false
      }

      env {
        POSTGRES_USER            = "tutur_owner"
        POSTGRES_DB              = "arsaka_tutur"
        PGDATA                   = "/var/lib/postgresql/data/pgdata"
        POSTGRES_HOST_AUTH_METHOD = "trust"
      }

      template {
        data = <<EOF
POSTGRES_PASSWORD={{ keyOrDefault "tutur/db_password" "tutur_secure_pass_2024" }}
EOF
        destination = "secrets/env"
        env         = true
      }

      template {
        data = <<EOF
-- Create app user with limited permissions
CREATE USER tutur_app WITH PASSWORD '{{ keyOrDefault "tutur/db_password" "tutur_secure_pass_2024" }}';

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO tutur_app;

-- Grant permissions on tables
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO tutur_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tutur_app;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO tutur_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO tutur_app;
EOF
        destination = "local/init.sql"
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
