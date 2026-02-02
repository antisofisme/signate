# ARSAKA_CHAT_AI PostgreSQL - Nomad Job Definition
# Chat AI Database

job "chat-postgres" {
  datacenters = ["dc1"]
  namespace   = "chat"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "ARSAKA Chat AI PostgreSQL Database"
  }

  group "database" {
    count = 1

    network {
      port "db" {
        static = 5433
        to     = 5432
      }
    }

    volume "postgres_data" {
      type      = "host"
      source    = "chat-postgres-data"
      read_only = false
    }

    service {
      name = "chat-postgres"
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
        POSTGRES_USER            = "chat_owner"
        POSTGRES_DB              = "arsaka_tutur"
        PGDATA                   = "/var/lib/postgresql/data/pgdata"
        POSTGRES_HOST_AUTH_METHOD = "trust"
      }

      template {
        data = <<EOF
POSTGRES_PASSWORD={{ key "chat/db_password" }}
EOF
        destination = "secrets/env"
        env         = true
      }

      template {
        data = <<EOF
-- Create app user with limited permissions
CREATE USER chat_app WITH PASSWORD '{{ key "chat/db_password" }}';

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO chat_app;

-- Grant permissions on tables
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO chat_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO chat_app;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO chat_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO chat_app;
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
