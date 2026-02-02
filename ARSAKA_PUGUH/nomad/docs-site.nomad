/**
 * ARSAKA PUGUH - Documentation Site Nomad Job
 * Serves Docusaurus static documentation via Nginx
 */

job "puguh-docs" {
  datacenters = ["dc1"]
  namespace   = "puguh"
  type        = "service"

  meta {
    version = "1.0.0"
    description = "ARSAKA PUGUH Documentation Site"
  }

  group "docs" {
    count = 1

    network {
      
      port "http" {
        to     = 80
        static = 3002  # Port 3001 used by MANTRA frontend
      }
    }

    restart {
      attempts = 3
      interval = "5m"
      delay    = "30s"
      mode     = "fail"
    }

    update {
      max_parallel     = 1
      min_healthy_time = "30s"
      healthy_deadline = "5m"
      auto_revert      = true
    }

    task "nginx" {
      driver = "docker"

      config {
        image = "nginx:alpine"
        ports = ["http"]

        volumes = [
          "/root/arsaka-puguh/docs-site/build:/usr/share/nginx/html:ro",
          "local/nginx.conf:/etc/nginx/conf.d/default.conf:ro"
        ]
      }

      # Nginx configuration for SPA routing
      template {
        data = <<EOF
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 'OK';
        add_header Content-Type text/plain;
    }

    # Static assets caching
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /img/ {
        expires 7d;
        add_header Cache-Control "public";
    }

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
        internal;
    }
}
EOF
        destination = "local/nginx.conf"
        change_mode = "signal"
        change_signal = "SIGHUP"
      }

      resources {
        cpu    = 100
        memory = 128
      }

      service {
        name = "puguh-docs"
        port = "http"

        tags = [
          "docs",
          "docusaurus",
          "puguh",
          "traefik.enable=true",
          "traefik.http.routers.puguh-docs.rule=Host(`docs.puguh.arsaka.io`)",
          "traefik.http.routers.puguh-docs.entrypoints=websecure",
          "traefik.http.routers.puguh-docs.tls.certresolver=letsencrypt"
        ]

        check {
          name     = "http_health"
          type     = "http"
          path     = "/health"
          interval = "30s"
          timeout  = "5s"
        }

        check {
          name     = "tcp_alive"
          type     = "tcp"
          interval = "30s"
          timeout  = "5s"
        }
      }
    }
  }
}
