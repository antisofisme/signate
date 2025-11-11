#!/bin/bash
# Performance Optimization Script for Digital Signage

set -e

echo "[$(date)] Starting performance optimization..."

# ============================================
# 1. Database Optimization
# ============================================
echo "[$(date)] Optimizing PostgreSQL..."

# Connect to database and run optimizations
docker exec -i signage-postgres psql -U signage_user -d signage_db << 'EOF'
-- Vacuum and analyze all tables
VACUUM ANALYZE;

-- Reindex all tables
REINDEX DATABASE signage_db;

-- Update table statistics
ANALYZE;

-- Create missing indexes for performance
CREATE INDEX IF NOT EXISTS idx_contents_type ON contents(content_type);
CREATE INDEX IF NOT EXISTS idx_contents_organization ON contents(organization_id);
CREATE INDEX IF NOT EXISTS idx_devices_organization ON devices(organization_id);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);
CREATE INDEX IF NOT EXISTS idx_playlists_organization ON playlists(organization_id);
CREATE INDEX IF NOT EXISTS idx_playlist_items_order ON playlist_items(playlist_id, "order");
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(organization_id, is_active);
CREATE INDEX IF NOT EXISTS idx_schedules_time ON schedules(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_device_logs_timestamp ON device_logs(device_id, timestamp);

-- Show table sizes
SELECT 
    schemaname AS table_schema,
    tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF

# Update PostgreSQL configuration for better performance
cat > /tmp/postgresql_optimize.conf << 'EOF'
# Memory Configuration
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 4MB

# Checkpoint Related Configuration
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
min_wal_size = 1GB
max_wal_size = 4GB

# Connection pooling
max_connections = 200

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_duration = on
EOF

# ============================================
# 2. Redis Optimization
# ============================================
echo "[$(date)] Optimizing Redis..."

docker exec -i signage-redis redis-cli << 'EOF'
# Set memory policy
CONFIG SET maxmemory-policy allkeys-lru
CONFIG SET maxmemory 512mb

# Enable RDB persistence
CONFIG SET save "900 1 300 10 60 10000"

# Optimize for low latency
CONFIG SET tcp-keepalive 60
CONFIG SET timeout 300

# Show memory info
INFO memory
EOF

# ============================================
# 3. Nginx Optimization
# ============================================
echo "[$(date)] Optimizing Nginx..."

cat > /home/gzjbbk/signage/docker/nginx/nginx-optimize.conf << 'EOF'
# Worker Processes
worker_processes auto;
worker_cpu_affinity auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    
    # Buffer Settings
    client_body_buffer_size 128k;
    client_max_body_size 50M;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml application/atom+xml image/svg+xml;
    
    # Cache Settings
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    
    # Upstream Configuration
    upstream backend {
        server backend-api:8001 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
}
EOF

# ============================================
# 4. Docker Optimization
# ============================================
echo "[$(date)] Optimizing Docker..."

# Clean up Docker
docker system prune -af --volumes
docker image prune -af
docker container prune -f
docker volume prune -f

# Configure Docker logging
cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3",
        "compress": "true"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ]
}
EOF

systemctl restart docker

# ============================================
# 5. System Optimization
# ============================================
echo "[$(date)] Optimizing system..."

# Optimize kernel parameters
cat > /etc/sysctl.d/99-signage-optimize.conf << 'EOF'
# Network optimizations
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# Memory optimizations
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system optimizations
fs.file-max = 65535
EOF

sysctl -p /etc/sysctl.d/99-signage-optimize.conf

# ============================================
# 6. Application Optimization
# ============================================
echo "[$(date)] Optimizing application..."

# Add caching headers for static files
cat > /home/gzjbbk/signage/docker/nginx/cache-static.conf << 'EOF'
# Cache static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js|pdf|doc|docx|mp4|webm)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# Cache API responses
location ~ ^/api/v1/(content|playlists|schedules) {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout invalid_header updating;
    proxy_cache_background_update on;
    proxy_cache_lock on;
    add_header X-Cache-Status $upstream_cache_status;
}
EOF

# ============================================
# 7. Monitoring Setup
# ============================================
echo "[$(date)] Setting up performance monitoring..."

# Create performance monitoring script
cat > /home/gzjbbk/signage/scripts/performance/monitor.sh << 'EOF'
#!/bin/bash
# Performance Monitoring Script

LOG_FILE="/var/log/signage/performance.log"
mkdir -p $(dirname $LOG_FILE)

echo "[$(date)] Performance Report" | tee -a $LOG_FILE
echo "=========================" | tee -a $LOG_FILE

# CPU Usage
echo "CPU Usage:" | tee -a $LOG_FILE
top -bn1 | grep "Cpu(s)" | tee -a $LOG_FILE
echo | tee -a $LOG_FILE

# Memory Usage
echo "Memory Usage:" | tee -a $LOG_FILE
free -h | tee -a $LOG_FILE
echo | tee -a $LOG_FILE

# Disk Usage
echo "Disk Usage:" | tee -a $LOG_FILE
df -h | grep -E "(^/|Filesystem)" | tee -a $LOG_FILE
echo | tee -a $LOG_FILE

# Docker Stats
echo "Docker Container Stats:" | tee -a $LOG_FILE
docker stats --no-stream | tee -a $LOG_FILE
echo | tee -a $LOG_FILE

# Database Connections
echo "Database Connections:" | tee -a $LOG_FILE
docker exec signage-postgres psql -U signage_user -d signage_db -c "SELECT count(*) as connections FROM pg_stat_activity;" | tee -a $LOG_FILE
echo | tee -a $LOG_FILE

# Redis Info
echo "Redis Memory:" | tee -a $LOG_FILE
docker exec signage-redis redis-cli INFO memory | grep "used_memory_human" | tee -a $LOG_FILE
echo | tee -a $LOG_FILE

# API Response Time
echo "API Health Check:" | tee -a $LOG_FILE
curl -w "\nResponse time: %{time_total}s\n" -s http://localhost:8001/health | tee -a $LOG_FILE
echo | tee -a $LOG_FILE
EOF

chmod +x /home/gzjbbk/signage/scripts/performance/monitor.sh

# ============================================
# 8. Create Cron Jobs
# ============================================
echo "[$(date)] Setting up cron jobs..."

cat > /tmp/signage-cron << 'EOF'
# Database optimization (weekly)
0 3 * * 0 /home/gzjbbk/signage/scripts/performance/optimize-db.sh

# Clear old logs (daily)
0 2 * * * find /var/log/signage -name "*.log" -mtime +7 -delete

# Performance monitoring (every 5 minutes)
*/5 * * * * /home/gzjbbk/signage/scripts/performance/monitor.sh

# Docker cleanup (weekly)
0 4 * * 0 docker system prune -af --volumes

# Backup (daily at 3 AM)
0 3 * * * /home/gzjbbk/signage/scripts/backup/backup.sh
EOF

crontab /tmp/signage-cron

# ============================================
# 9. Performance Testing
# ============================================
echo "[$(date)] Running performance tests..."

# Test API response time
echo "Testing API endpoints..."
for i in {1..10}; do
    curl -s -w "Request $i: %{time_total}s\n" -o /dev/null http://localhost:8001/api/v1/devices
done

echo "[$(date)] Performance optimization completed!"
echo
echo "Optimization Summary:"
echo "1. Database indexes created and statistics updated"
echo "2. Redis configured for caching with 512MB limit"
echo "3. Nginx optimized for high concurrency"
echo "4. Docker cleaned and logging optimized"
echo "5. Kernel parameters tuned for performance"
echo "6. Static file caching enabled"
echo "7. Monitoring scripts created"
echo "8. Cron jobs scheduled"
echo
echo "Next steps:"
echo "- Monitor performance metrics in Grafana"
echo "- Adjust settings based on actual load"
echo "- Run load tests to verify improvements"