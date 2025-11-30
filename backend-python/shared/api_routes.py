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

    # Quota management
    QUOTA = f"{BASE}/{{org_id}}/quota"
    QUOTA_USAGE = f"{BASE}/{{org_id}}/quota/usage"
    QUOTA_UPDATE = f"{BASE}/{{org_id}}/quota"


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

    # User-Role Assignment endpoints (P0-1 RBAC)
    GET_ROLE = f"{BASE}/{{user_id}}/role"
    ASSIGN_ROLE = f"{BASE}/{{user_id}}/role"


# =============================================================================
# DEVICE SERVICE ROUTES
# =============================================================================
class DeviceRoutes:
    """Device management endpoints"""
    BASE = f"{API_V1}/devices"

    # Basic CRUD
    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{device_id}}"
    UPDATE = f"{BASE}/{{device_id}}"
    DELETE = f"{BASE}/{{device_id}}"
    ME = f"{BASE}/me"  # Get current device info (for authenticated devices)

    # Registration endpoints
    REQUEST_CODE = f"{BASE}/request-code"  # Player endpoint (public)
    TV_REGISTER = f"{BASE}/tv"  # TV device registration
    MONITOR_REGISTER = f"{BASE}/monitor"  # Monitor device registration
    ACTIVATE = f"{BASE}/activate"  # CMS activation
    CHECK_ACTIVATION = f"{BASE}/check-activation/{{unique_code}}"  # Player polling (public)
    CHECK_ACTIVATION_BY_UUID = f"{BASE}/check-activation-by-uuid/{{device_uuid}}"  # Player check by fingerprint (public)
    VERIFY_FINGERPRINT = f"{BASE}/verify-fingerprint/{{device_uuid}}"  # Player cache recovery (public)

    # Device lifecycle
    HEARTBEAT = f"{BASE}/{{device_id}}/heartbeat"
    RELEASE = f"{BASE}/{{device_id}}/release"  # CMS admin release (soft)
    HARD_RESET = f"{BASE}/{{device_id}}/hard-reset"  # Player factory reset (public)

    # Content resolution
    CONTENT_RESOLVED = f"{BASE}/{{device_id}}/content/resolved"

    # Commands
    COMMANDS = f"{BASE}/{{device_id}}/commands"  # GET pending commands
    SEND_COMMAND = f"{BASE}/{{device_id}}/commands"  # POST to send command
    COMMAND_STATUS = f"{BASE}/{{device_id}}/commands/{{command_id}}"

    # Network testing
    SPEED_TEST = f"{BASE}/{{device_id}}/speed-test"  # POST to record test
    SPEED_TESTS = f"{BASE}/{{device_id}}/speed-tests"  # GET test history

    # Logging & monitoring
    LOGS = f"{BASE}/{{device_id}}/logs"
    DEVICE_LOGS_BATCH = "/api/client/logs/batch"  # Player batch logs (public)
    CONNECTION_LOGS = f"{BASE}/{{device_id}}/connection-logs"  # Connection activity logs

    # Security
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

    # Content CRUD
    LIST = BASE
    UPLOAD = f"{BASE}/upload"
    BULK_UPLOAD = f"{BASE}/bulk-upload"
    GET = f"{BASE}/{{content_id}}"
    UPDATE = f"{BASE}/{{content_id}}"
    DELETE = f"{BASE}/{{content_id}}"
    BULK_DELETE = f"{BASE}/bulk-delete"
    BULK_UPDATE = f"{BASE}/bulk-update"
    DOWNLOAD = f"{BASE}/{{content_id}}/download"

    # Content metadata & stats
    PREVIEW = f"{BASE}/{{content_id}}/preview"
    STATS = f"{BASE}/stats"  # Storage statistics

    # Deleted content (Recycle Bin)
    LIST_DELETED = f"{BASE}/deleted"
    RESTORE = f"{BASE}/{{content_id}}/restore"
    PERMANENT_DELETE = f"{BASE}/{{content_id}}/permanent"

    # Duplicate detection
    DUPLICATES = f"{BASE}/duplicates"

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
# RBAC (ROLES) SERVICE ROUTES
# =============================================================================
class RBACRoutes:
    """Role-Based Access Control endpoints"""
    BASE = f"{API_V1}/roles"

    # Role CRUD
    LIST = BASE
    CREATE = BASE
    GET = f"{BASE}/{{role_id}}"
    UPDATE = f"{BASE}/{{role_id}}"
    DELETE = f"{BASE}/{{role_id}}"

    # System roles
    SYSTEM_ROLES = f"{BASE}/system"

    # Organization roles
    ORG_ROLES = f"{API_V1}/organizations/{{org_id}}/roles"

    # Permission management
    CHECK_PERMISSION = f"{BASE}/{{role_id}}/permissions/check"
    GET_PERMISSIONS = f"{BASE}/{{role_id}}/permissions"
    ADD_PERMISSION = f"{BASE}/{{role_id}}/permissions"
    REMOVE_PERMISSION = f"{BASE}/{{role_id}}/permissions"


# =============================================================================
# SESSION SERVICE ROUTES
# =============================================================================
class SessionRoutes:
    """User session management endpoints"""
    BASE = f"{API_V1}/sessions"

    # Session management
    LIST = BASE  # GET user's sessions
    GET = f"{BASE}/{{session_id}}"
    REVOKE = f"{BASE}/{{session_id}}"  # DELETE - logout from specific session
    REVOKE_ALL = f"{BASE}/revoke-all"  # POST - logout from all devices

    # Session stats
    STATS = f"{BASE}/stats"
    ACTIVE = f"{BASE}/active"

    # Admin endpoints
    ALL_ACTIVE = f"{BASE}/all-active"  # Admin: get all active sessions (multi-tenancy)
    BY_USER = f"{BASE}/user/{{user_id}}"  # Admin: get user's sessions
    BY_IP = f"{BASE}/ip/{{ip_address}}"  # Admin: get sessions by IP


# =============================================================================
# PMS (Property Management System) SERVICE ROUTES
# =============================================================================
class PMSRoutes:
    """PMS Integration endpoints"""
    BASE = f"{API_V1}/pms"
    
    # Configuration
    CONFIG = f"{BASE}/config"
    GET_CONFIG = f"{BASE}/config"
    UPDATE_CONFIG = f"{BASE}/config"
    
    # Guest data
    GUESTS = f"{BASE}/guests"
    CURRENT_GUESTS = f"{BASE}/guests/current"
    DEVICE_CURRENT_GUEST = f"{BASE}/device/{{device_id}}/current-guest"
    
    # Room data
    ROOMS = f"{BASE}/rooms"
    
    # Stats
    STATS = f"{BASE}/stats"
    
    # Sync endpoints (for Bridge Agent)
    SYNC_GUESTS = f"{BASE}/sync/guests"
    SYNC_ROOMS = f"{BASE}/sync/rooms"
    
    # WebSocket
    WEBSOCKET_SYNC = "/ws/pms/sync"
    
    # Trigger sync
    TRIGGER_SYNC = f"{BASE}/trigger-sync/{{organization_id}}"
