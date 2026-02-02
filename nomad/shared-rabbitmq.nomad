# Shared RabbitMQ - Nomad Job Definition
# Message broker shared between ATLAS services
#
# PURPOSE:
#   Central message broker for async processing:
#   - Event-driven architecture
#   - Background job queues
#   - Cross-service communication
#
# SETUP VHOSTS (manual, run after deploy):
#   docker exec -it <container> rabbitmqctl add_vhost mantra
#   docker exec -it <container> rabbitmqctl add_vhost puguh
#   docker exec -it <container> rabbitmqctl add_user mantra <password>
#   docker exec -it <container> rabbitmqctl set_permissions -p mantra mantra ".*" ".*" ".*"
#
# Deploy: nomad job run -namespace=shared shared-rabbitmq.nomad

job "shared-rabbitmq" {
  datacenters = ["dc1"]
  namespace   = "shared"
  type        = "service"

  meta {
    version     = "1.0.1"
    description = "Shared RabbitMQ message broker for ATLAS services"
  }

  group "rabbitmq" {
    count = 1

    network {
      mode = "host"
      port "amqp" {
        static = 5672
      }
      port "mgmt" {
        static = 15672
      }
    }

    service {
      name = "shared-rabbitmq"
      port = "amqp"

      tags = [
        "shared",
        "queue",
        "rabbitmq"
      ]

      check {
        name     = "amqp-health"
        type     = "tcp"
        interval = "30s"
        timeout  = "5s"
      }
    }

    service {
      name = "shared-rabbitmq-mgmt"
      port = "mgmt"

      tags = [
        "shared",
        "management",
        "rabbitmq-ui"
      ]
    }

    task "rabbitmq" {
      driver = "docker"

      config {
        image        = "rabbitmq:3.12-management-alpine"
        network_mode = "host"

        volumes = [
          "/opt/atlas-shared/data/rabbitmq:/var/lib/rabbitmq"
        ]
      }

      env {
        RABBITMQ_DEFAULT_USER  = "admin"
        RABBITMQ_DEFAULT_PASS  = "atlas_rabbitmq_admin_2026"
        RABBITMQ_DEFAULT_VHOST = "/"
      }

      resources {
        cpu    = 200
        memory = 384
      }

      logs {
        max_files     = 5
        max_file_size = 10
      }
    }
  }
}
