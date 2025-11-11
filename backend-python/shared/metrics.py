"""
Prometheus Metrics for Digital Signage System
Tracks application performance and business metrics
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    'signage_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'signage_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_request_size_bytes = Histogram(
    'signage_http_request_size_bytes',
    'HTTP request body size',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'signage_http_response_size_bytes', 
    'HTTP response body size',
    ['method', 'endpoint']
)

# ============================================================================
# Database Metrics
# ============================================================================

db_query_duration_seconds = Histogram(
    'signage_db_query_duration_seconds',
    'Database query latency',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

db_query_total = Counter(
    'signage_db_query_total',
    'Total database queries',
    ['operation', 'table', 'status']
)

db_connections_active = Gauge(
    'signage_db_connections_active',
    'Active database connections'
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_operations_total = Counter(
    'signage_cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)

cache_hit_ratio = Gauge(
    'signage_cache_hit_ratio',
    'Cache hit ratio (hits / (hits + misses))'
)

# ============================================================================
# Business Metrics - Devices
# ============================================================================

devices_total = Gauge(
    'signage_devices_total',
    'Total registered devices',
    ['organization', 'status']
)

devices_online = Gauge(
    'signage_devices_online',
    'Currently online devices',
    ['organization']
)

device_heartbeats_total = Counter(
    'signage_device_heartbeats_total',
    'Total device heartbeats received',
    ['device_id']
)

# ============================================================================
# Business Metrics - Content
# ============================================================================

content_total = Gauge(
    'signage_content_total',
    'Total content items',
    ['organization', 'type', 'status']
)

content_plays_total = Counter(
    'signage_content_plays_total',
    'Total content plays',
    ['content_id', 'device_id']
)

content_upload_duration_seconds = Histogram(
    'signage_content_upload_duration_seconds',
    'Content upload duration',
    ['content_type'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

content_storage_bytes = Gauge(
    'signage_content_storage_bytes',
    'Total content storage used',
    ['organization']
)

# ============================================================================
# Business Metrics - Playlists
# ============================================================================

playlists_total = Gauge(
    'signage_playlists_total',
    'Total playlists',
    ['organization', 'status']
)

playlist_assignments_total = Gauge(
    'signage_playlist_assignments_total',
    'Total playlist assignments',
    ['organization']
)

# ============================================================================
# Application Metrics
# ============================================================================

app_info = Info(
    'signage_app_info',
    'Application version and environment info'
)

app_startup_time_seconds = Gauge(
    'signage_app_startup_time_seconds',
    'Application startup time'
)

websocket_connections_active = Gauge(
    'signage_websocket_connections_active',
    'Active WebSocket connections'
)

background_tasks_total = Counter(
    'signage_background_tasks_total',
    'Total background tasks executed',
    ['task_name', 'status']
)

# ============================================================================
# Helper Functions and Decorators
# ============================================================================

def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float, request_size: int = 0, response_size: int = 0):
    """Track HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    if request_size > 0:
        http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)
    
    if response_size > 0:
        http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)


def track_db_metrics(func):
    """Decorator to track database query metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation = func.__name__
        table = kwargs.get('table', 'unknown')
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
            db_query_total.labels(operation=operation, table=table, status='success').inc()
            
            return result
        except Exception as e:
            db_query_total.labels(operation=operation, table=table, status='error').inc()
            raise
    
    return wrapper


def track_cache_operation(operation: str, hit: bool = None):
    """Track cache operation metrics"""
    if hit is not None:
        status = 'hit' if hit else 'miss'
        cache_operations_total.labels(operation=operation, status=status).inc()
        
        # Update hit ratio
        hits = cache_operations_total.labels(operation='get', status='hit')._value.get()
        misses = cache_operations_total.labels(operation='get', status='miss')._value.get()
        
        if hits + misses > 0:
            ratio = hits / (hits + misses)
            cache_hit_ratio.set(ratio)
    else:
        cache_operations_total.labels(operation=operation, status='success').inc()


def update_device_metrics(organization_id: int, online_count: int, offline_count: int):
    """Update device-related metrics"""
    total = online_count + offline_count
    
    devices_total.labels(organization=str(organization_id), status='online').set(online_count)
    devices_total.labels(organization=str(organization_id), status='offline').set(offline_count)
    devices_total.labels(organization=str(organization_id), status='all').set(total)
    devices_online.labels(organization=str(organization_id)).set(online_count)


def update_content_metrics(organization_id: int, content_counts: dict):
    """Update content-related metrics"""
    for content_type, count in content_counts.items():
        content_total.labels(
            organization=str(organization_id),
            type=content_type,
            status='active'
        ).set(count)


def track_content_play(content_id: int, device_id: int):
    """Track content playback"""
    content_plays_total.labels(
        content_id=str(content_id),
        device_id=str(device_id)
    ).inc()


def track_device_heartbeat(device_id: int):
    """Track device heartbeat"""
    device_heartbeats_total.labels(device_id=str(device_id)).inc()


def track_background_task(task_name: str, success: bool = True):
    """Track background task execution"""
    status = 'success' if success else 'error'
    background_tasks_total.labels(task_name=task_name, status=status).inc()


# ============================================================================
# Middleware for automatic metric collection
# ============================================================================

class MetricsMiddleware:
    """Middleware to automatically collect HTTP metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        path = scope.get("path", "unknown")
        method = scope.get("method", "unknown")
        
        # Track request
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Record metrics
            duration = time.time() - start_time
            track_request_metrics(method, path, status_code, duration)


# ============================================================================
# Initialize application info
# ============================================================================

def init_app_metrics(version: str = "1.0.0", environment: str = "production"):
    """Initialize application metrics"""
    app_info.info({
        'version': version,
        'environment': environment,
        'python_version': '3.11'
    })
    
    app_startup_time_seconds.set(time.time())