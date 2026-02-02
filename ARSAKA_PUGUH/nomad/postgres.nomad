# ARSAKA_PUGUH - PostgreSQL Database (Phase A)
# Deploy: nomad job run -namespace=puguh postgres.nomad

job "puguh-postgres" {
  datacenters = ["dc1"]
  namespace   = "puguh"
  type        = "service"

  # Update strategy (careful with database)
  update {
    max_parallel      = 1
    min_healthy_time  = "30s"
    healthy_deadline  = "5m"
    progress_deadline = "10m"
    auto_revert       = false  # Manual intervention for database
  }

  group "db" {
    count = 1

    # Network configuration
    network {
      port "db" {
        static = 5433
        to     = 5432
      }
    }

    # Host volume for data persistence
    # IMPORTANT: Configure this in Nomad client config:
    # client {
    #   host_volume "puguh_postgres_data" {
    #     path = "/opt/nomad/volumes/puguh/postgres"
    #   }
    # }
    volume "postgres_data" {
      type      = "host"
      source    = "puguh_postgres_data"
      read_only = false
    }

    # Restart policy (database needs careful restart)
    restart {
      attempts = 2
      interval = "10m"
      delay    = "1m"
      mode     = "fail"  # Don't auto-restart forever
    }

    task "postgresql" {
      driver = "docker"

      config {
        image = "postgres:15-alpine"
        ports = ["db"]

        # Volume mount for persistence
        volumes = [
          "local/migrations:/docker-entrypoint-initdb.d:ro"  # Auto-run init scripts
        ]

        # Force image pull (ensure latest security patches)
        force_pull = false  # Set to true for production
      }

      # Volume mount configuration
      volume_mount {
        volume      = "postgres_data"
        destination = "/var/lib/postgresql/data"
        read_only   = false
      }

      # Environment variables
      env {
        # Database configuration
        POSTGRES_DB       = "arsaka_puguh"
        POSTGRES_USER     = "arsaka_user"

        # Performance tuning (Phase A: minimal)
        POSTGRES_INITDB_ARGS = "-E UTF8 --locale=C"
        POSTGRES_HOST_AUTH_METHOD = "md5"  # Require password

        # Logging
        POSTGRES_LOG_STATEMENT = "all"  # Phase A: debug mode
        POSTGRES_LOG_CONNECTIONS = "on"
        POSTGRES_LOG_DISCONNECTIONS = "on"
      }

      # Password from Consul KV
      template {
        data = <<EOF
POSTGRES_PASSWORD={{ key "puguh/db_password" }}
EOF
        destination = "secrets/db.env"
        env         = true
      }

      # Template for init SQL (seed data)
      # This runs ONCE on first startup
      template {
        data = <<EOF
-- Phase A Seed Data
-- This runs automatically on first database initialization

-- Create schema if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Note: Main tables created via migrations (run manually)
-- This is just for initial setup
EOF
        destination = "local/migrations/00_init.sql"
        change_mode = "noop"  # Don't restart on template change
      }

      # Resource allocation (Phase A: minimal)
      resources {
        cpu    = 500   # 500 MHz (0.25 core)
        memory = 512   # 512 MB RAM
      }

      # Service registration in Consul
      service {
        name = "puguh-postgres"
        port = "db"

        tags = [
          "database",
          "postgresql",
          "phase-a",
          "puguh"
        ]

        # Health check
        check {
          name     = "postgresql-health"
          type     = "tcp"
          interval = "30s"
          timeout  = "5s"

          check_restart {
            limit           = 3
            grace           = "10s"
            ignore_warnings = false
          }
        }

        # Additional HTTP health check (if pg_isready exposed)
        check {
          name     = "postgresql-ready"
          type     = "script"
          command  = "/bin/sh"
          args     = ["-c", "pg_isready -U arsaka_user -d arsaka_puguh"]
          interval = "30s"
          timeout  = "5s"
        }
      }

      # Logging configuration
      logs {
        max_files     = 5
        max_file_size = 10  # MB
      }

      # Lifecycle hooks
      lifecycle {
        hook    = "prestart"
        sidecar = false
      }
    }
  }
}
