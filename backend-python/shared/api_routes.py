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
    FORGOT_PASSWORD = f"{BASE}/forgot-password"
    RESET_PASSWORD = f"{BASE}/reset-password"


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
# USER MANAGEMENT SERVICE ROUTES
# =============================================================================
class UserRoutes:
    """User account management"""
    BASE = f"{API_V1}/users"

    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{user_id}}"
    UPDATE = f"{BASE}/{{user_id}}"
    DELETE = f"{BASE}/{{user_id}}"
    CHANGE_PASSWORD = f"{BASE}/{{user_id}}/change-password"


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
    CONTENT_RESOLVED = f"{BASE}/{{device_id}}/content/resolved"
    COMMANDS_PENDING = f"{BASE}/{{device_id}}/commands/pending"
    COMMAND = f"{BASE}/{{device_id}}/command"
    LOGS = f"{BASE}/{{device_id}}/logs"
    VALIDATE_RESET_PASSWORD = f"{BASE}/validate-reset-password"


# =============================================================================
# TAG SERVICE ROUTES
# =============================================================================
class TagRoutes:
    """Tag management endpoints"""
    BASE = f"{API_V1}/tags"

    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{tag_id}}"
    UPDATE = f"{BASE}/{{tag_id}}"
    DELETE = f"{BASE}/{{tag_id}}"
    USAGE = f"{BASE}/{{tag_id}}/usage"

    # Content-Tag Assignment
    ASSIGN_TO_CONTENT = f"{BASE}/{{tag_id}}/assign-content"
    ASSIGN_TO_CONTENTS = f"{BASE}/{{tag_id}}/assign-contents"
    UNASSIGN_FROM_CONTENT = f"{BASE}/{{tag_id}}/unassign-content"
    UNASSIGN_FROM_CONTENTS = f"{BASE}/{{tag_id}}/unassign-contents"
    GET_CONTENT_TAGS = f"{API_V1}/contents/{{content_id}}/tags"


# =============================================================================
# CONTENT SERVICE ROUTES
# =============================================================================
class ContentRoutes:
    """Content & Playlist management"""
    BASE = f"{API_V1}/contents"
    PLAYLISTS = f"{API_V1}/playlists"

    # Content
    LIST = BASE
    UPLOAD = f"{BASE}/upload"
    GET = f"{BASE}/{{content_id}}"
    UPDATE = f"{BASE}/{{content_id}}"
    DELETE = f"{BASE}/{{content_id}}"
    PREVIEW = f"{BASE}/{{content_id}}/preview"
    STATS = f"{BASE}/stats"  # Storage statistics

    # Playlists
    PLAYLIST_LIST = PLAYLISTS
    PLAYLIST_CREATE = PLAYLISTS
    PLAYLIST_GET = f"{PLAYLISTS}/{{playlist_id}}"
    PLAYLIST_UPDATE = f"{PLAYLISTS}/{{playlist_id}}"
    PLAYLIST_DELETE = f"{PLAYLISTS}/{{playlist_id}}"
    PLAYLIST_ASSIGN = f"{PLAYLISTS}/{{playlist_id}}/assign"


# =============================================================================
# AUDIT SERVICE ROUTES
# =============================================================================
class AuditRoutes:
    """Audit trail & activity logging"""
    BASE = f"{API_V1}/audit-logs"

    LIST = BASE
    GET = f"{BASE}/{{log_id}}"


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
        "users": {k: v for k, v in vars(UserRoutes).items() if not k.startswith("_")},
        "audit": {k: v for k, v in vars(AuditRoutes).items() if not k.startswith("_")},
        "devices": {k: v for k, v in vars(DeviceRoutes).items() if not k.startswith("_")},
        "tags": {k: v for k, v in vars(TagRoutes).items() if not k.startswith("_")},
        "content": {k: v for k, v in vars(ContentRoutes).items() if not k.startswith("_")},
        "analytics": {k: v for k, v in vars(AnalyticsRoutes).items() if not k.startswith("_")},
        "client": {k: v for k, v in vars(ClientRoutes).items() if not k.startswith("_")},
        "health": {k: v for k, v in vars(HealthRoutes).items() if not k.startswith("_")},
        "websocket": {k: v for k, v in vars(WebSocketRoutes).items() if not k.startswith("_")},
    }


# =============================================================================
# PLAYLIST SERVICE ROUTES
# =============================================================================
class PlaylistRoutes:
    """Playlist management endpoints"""
    BASE = f"{API_V1}/playlists"

    # Playlist CRUD
    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{playlist_id}}"
    UPDATE = f"{BASE}/{{playlist_id}}"
    DELETE = f"{BASE}/{{playlist_id}}"

    # Content Management
    GET_CONTENT = f"{BASE}/{{playlist_id}}/content"
    ADD_CONTENT = f"{BASE}/{{playlist_id}}/content"
    REMOVE_CONTENT = f"{BASE}/{{playlist_id}}/content/{{content_item_id}}"
    REORDER_CONTENT = f"{BASE}/{{playlist_id}}/reorder"

    # Device/Tag Assignments
    GET_ASSIGNMENTS = f"{BASE}/{{playlist_id}}/assignments"
    ASSIGN_TO_DEVICES = f"{BASE}/{{playlist_id}}/assign/devices"
    ASSIGN_TO_TAGS = f"{BASE}/{{playlist_id}}/assign/tags"
    UNASSIGN_FROM_DEVICES = f"{BASE}/{{playlist_id}}/assign/devices"
    UNASSIGN_FROM_TAGS = f"{BASE}/{{playlist_id}}/assign/tags"


# =============================================================================
# AUDIT SERVICE ROUTES  
# =============================================================================
class AuditRoutes:
    """Audit logging endpoints"""
    BASE = f"{API_V1}/audit-logs"

    LIST = BASE
    GET = f"{BASE}/{{log_id}}"
