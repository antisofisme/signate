"""
CENTRALIZED API ROUTES DEFINITION
� SINGLE SOURCE OF TRUTH untuk semua API endpoints
"""

# API Version
API_V1 = "/api/v1"

# =============================================================================
# AUTH SERVICE ROUTES
# =============================================================================
class AuthRoutes:
    """Authentication & Authorization endpoints"""
    BASE = f"{API_V1}/auth"

    LOGIN = f"{BASE}/login"
    LOGOUT = f"{BASE}/logout"
    REGISTER = f"{BASE}/register"
    ME = f"{BASE}/me"
    REFRESH = f"{BASE}/refresh"


# =============================================================================
# ORGANIZATION (TENANT) SERVICE ROUTES
# =============================================================================
class OrganizationRoutes:
    """Multi-tenant organization management"""
    BASE = f"{API_V1}/organizations"

    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{org_id}}"
    UPDATE = f"{BASE}/{{org_id}}"
    DELETE = f"{BASE}/{{org_id}}"
    VALIDATE_PIN = f"{BASE}/{{org_id}}/validate-pin"


# =============================================================================
# DEVICE SERVICE ROUTES
# =============================================================================
class DeviceRoutes:
    """Device management endpoints"""
    BASE = f"{API_V1}/devices"

    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{device_id}}"
    UPDATE = f"{BASE}/{{device_id}}"
    DELETE = f"{BASE}/{{device_id}}"

    # Device actions
    ACTIVATE = f"{BASE}/activate"
    HEARTBEAT = f"{BASE}/{{device_id}}/heartbeat"
    COMMAND = f"{BASE}/{{device_id}}/command"
    LOGS = f"{BASE}/{{device_id}}/logs"


# =============================================================================
# CONTENT SERVICE ROUTES
# =============================================================================
class ContentRoutes:
    """Content & Playlist management"""
    BASE = f"{API_V1}/content"
    PLAYLISTS = f"{API_V1}/playlists"

    # Content
    LIST = BASE
    UPLOAD = f"{BASE}/upload"
    GET = f"{BASE}/{{content_id}}"
    UPDATE = f"{BASE}/{{content_id}}"
    DELETE = f"{BASE}/{{content_id}}"
    PREVIEW = f"{BASE}/{{content_id}}/preview"

    # Playlists
    PLAYLIST_LIST = PLAYLISTS
    PLAYLIST_CREATE = PLAYLISTS
    PLAYLIST_GET = f"{PLAYLISTS}/{{playlist_id}}"
    PLAYLIST_UPDATE = f"{PLAYLISTS}/{{playlist_id}}"
    PLAYLIST_DELETE = f"{PLAYLISTS}/{{playlist_id}}"
    PLAYLIST_ASSIGN = f"{PLAYLISTS}/{{playlist_id}}/assign"


# =============================================================================
# ANALYTICS SERVICE ROUTES
# =============================================================================
class AnalyticsRoutes:
    """Analytics, Logs, & Reports"""
    BASE = f"{API_V1}/analytics"

    DASHBOARD = f"{BASE}/dashboard"
    ACTIVITY_LOGS = f"{BASE}/activity-logs"
    DEVICE_LOGS = f"{BASE}/device-logs"
    REPORTS = f"{BASE}/reports"


# =============================================================================
# CLIENT (VIEWER/PLAYER) ROUTES
# =============================================================================
class ClientRoutes:
    """Public endpoints for viewer/player"""
    BASE = f"{API_V1}/client"

    PLAYLIST = f"{BASE}/playlist/{{device_id}}"
    CONTENT = f"{BASE}/content/{{content_id}}"


# =============================================================================
# HEALTH & MONITORING
# =============================================================================
class HealthRoutes:
    """Health check & monitoring"""
    HEALTH = "/health"
    PING = "/api/ping"
    READY = "/ready"


# =============================================================================
# WEBSOCKET ROUTES
# =============================================================================
class WebSocketRoutes:
    """WebSocket endpoints"""
    DEVICE = "/api/ws/{device_id}"
    ADMIN = "/api/ws/admin"


# =============================================================================
# HELPER: Get all routes as dict
# =============================================================================
def get_all_routes():
    """Get all routes as dictionary for documentation"""
    return {
        "auth": {k: v for k, v in vars(AuthRoutes).items() if not k.startswith("_")},
        "organizations": {k: v for k, v in vars(OrganizationRoutes).items() if not k.startswith("_")},
        "devices": {k: v for k, v in vars(DeviceRoutes).items() if not k.startswith("_")},
        "content": {k: v for k, v in vars(ContentRoutes).items() if not k.startswith("_")},
        "analytics": {k: v for k, v in vars(AnalyticsRoutes).items() if not k.startswith("_")},
        "client": {k: v for k, v in vars(ClientRoutes).items() if not k.startswith("_")},
        "health": {k: v for k, v in vars(HealthRoutes).items() if not k.startswith("_")},
        "websocket": {k: v for k, v in vars(WebSocketRoutes).items() if not k.startswith("_")},
    }
