# ARSAKA_PUGUH - Frontend (Phase A+)
# Deploy: nomad job run -namespace=puguh frontend.nomad

job "puguh-frontend" {
  datacenters = ["dc1"]
  namespace   = "puguh"
  type        = "service"

  # Update strategy
  update {
    max_parallel      = 1
    min_healthy_time  = "10s"
    healthy_deadline  = "3m"
    progress_deadline = "5m"
    auto_revert       = true
    canary            = 0
  }

  group "web" {
    count = 1

    # Network configuration
    network {
      

      port "http" {
        to = 80
        static = 3000  # Static port untuk frontend
      }
    }

    # Restart policy
    restart {
      attempts = 3
      interval = "5m"
      delay    = "15s"
      mode     = "fail"
    }

    task "nginx" {
      driver = "docker"

      config {
        image = "nginx:alpine"
        ports = ["http"]

        # Mount dist folder dan nginx config
        volumes = [
          "/root/arsaka-puguh/frontend/dist:/usr/share/nginx/html:ro",
          "local/nginx.conf:/etc/nginx/conf.d/default.conf:ro"
        ]
      }

      # Nginx config untuk SPA routing
      template {
        data = <<EOF
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 'healthy';
        add_header Content-Type text/plain;
    }

    # Static assets with cache
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback - semua route diarahkan ke index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
        destination = "local/nginx.conf"
      }

      # Environment variables
      env {
        NGINX_HOST = "0.0.0.0"
        NGINX_PORT = "80"
      }

      # Resource allocation
      resources {
        cpu    = 200   # 200 MHz
        memory = 256   # 256 MB
      }

      # Service registration in Consul
      service {
        name = "puguh-frontend"
        port = "http"

        tags = [
          "frontend",
          "nginx",
          "phase-a",
          "puguh",

          # Traefik tags
          "traefik.enable=true",
          "traefik.http.routers.puguh-frontend.rule=Host(`puguh.arsaka.io`) || Host(`puguh.arsaka.io`)",
          "traefik.http.routers.puguh-frontend.entrypoints=web",
        ]

        # Health check
        check {
          name     = "http-health"
          type     = "http"
          path     = "/health"
          interval = "30s"
          timeout  = "3s"

          check_restart {
            limit           = 3
            grace           = "10s"
            ignore_warnings = false
          }
        }
      }

      # Logging
      logs {
        max_files     = 5
        max_file_size = 10
      }

      # Graceful shutdown
      kill_timeout = "10s"
      kill_signal  = "SIGTERM"
    }
  }
}
