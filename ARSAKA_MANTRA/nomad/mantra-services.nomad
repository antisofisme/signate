# ARSAKA_MANTRA Additional Services - Nomad Job Definition
# Meilisearch (Full-text Search) + RabbitMQ (Message Queue)
#
# Deploy: nomad job run -namespace=mantra mantra-services.nomad
# Stop:   nomad job stop -namespace=mantra mantra-services

job "mantra-services" {
  datacenters = ["dc1"]
  namespace   = "mantra"
  type        = "service"

  meta {
    version     = "1.0.0"
    description = "MANTRA Additional Services - Meilisearch + RabbitMQ"
  }

  # =========================================================================
  # Meilisearch - Full-text Search Engine
  # =========================================================================
  group "meilisearch" {
    count = 1

    network {
      port "http" {
        static = 7700
        to     = 7700
      }
    }

    service {
      name = "mantra-meilisearch"
      port = "http"

      tags = [
        "mantra",
        "search",
      ]

      check {
        name     = "health"
        type     = "http"
        path     = "/health"
        interval = "30s"
        timeout  = "5s"
      }
    }

    task "meilisearch" {
      driver = "docker"

      config {
        image = "getmeili/meilisearch:v1.6"
        ports = ["http"]

        # Use Docker volume for persistence
        volumes = [
          "mantra-meilisearch-data:/meili_data"
        ]
      }

      env {
        MEILI_NO_ANALYTICS = "true"
        MEILI_ENV          = "production"
      }

      template {
        data = <<EOF
{{- if keyExists "mantra/meilisearch_api_key" }}
MEILI_MASTER_KEY={{ key "mantra/meilisearch_api_key" }}
{{- else }}
MEILI_MASTER_KEY=mantra_meilisearch_master_key
{{- end }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 200
        memory = 512
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }

  # =========================================================================
  # RabbitMQ - Message Queue
  # =========================================================================
  group "rabbitmq" {
    count = 1

    network {
      port "amqp" {
        static = 5672
        to     = 5672
      }
      port "mgmt" {
        static = 15672
        to     = 15672
      }
    }

    service {
      name = "mantra-rabbitmq"
      port = "amqp"

      tags = [
        "mantra",
        "queue",
      ]

      check {
        name     = "health"
        type     = "tcp"
        interval = "30s"
        timeout  = "5s"
      }
    }

    service {
      name = "mantra-rabbitmq-mgmt"
      port = "mgmt"

      tags = [
        "mantra",
        "management",
      ]
    }

    task "rabbitmq" {
      driver = "docker"

      config {
        image = "rabbitmq:3.12-management-alpine"
        ports = ["amqp", "mgmt"]

        # Use Docker volume for persistence
        volumes = [
          "mantra-rabbitmq-data:/var/lib/rabbitmq"
        ]
      }

      env {
        RABBITMQ_DEFAULT_USER  = "mantra"
        RABBITMQ_DEFAULT_VHOST = "mantra"
      }

      template {
        data = <<EOF
RABBITMQ_DEFAULT_PASS={{ keyOrDefault "mantra/rabbitmq_password" "mantra_mq_password" }}
EOF
        destination = "secrets/env"
        env         = true
      }

      resources {
        cpu    = 200
        memory = 256
      }

      logs {
        max_files     = 3
        max_file_size = 10
      }
    }
  }
}
