"""
Audit Service DTOs
Request/Response models for audit log endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# =============================================================================
# AUDIT LOG ACTIONS ENUM
# =============================================================================

class AuditLogAction(str, Enum):
    """Standard audit log action types"""

    # User actions
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    # Organization actions
    ORG_CREATE = "org.create"
    ORG_UPDATE = "org.update"
    ORG_DELETE = "org.delete"

    # Device actions
    DEVICE_CREATE = "device.create"
    DEVICE_UPDATE = "device.update"
    DEVICE_DELETE = "device.delete"
    DEVICE_ACTIVATE = "device.activate"
    DEVICE_DEACTIVATE = "device.deactivate"

    # Content actions
    CONTENT_CREATE = "content.create"
    CONTENT_UPDATE = "content.update"
    CONTENT_DELETE = "content.delete"
    CONTENT_UPLOAD = "content.upload"

    # Playlist actions
    PLAYLIST_CREATE = "playlist.create"
    PLAYLIST_UPDATE = "playlist.update"
    PLAYLIST_DELETE = "playlist.delete"
    PLAYLIST_ASSIGN = "playlist.assign"

    # Schedule actions
    SCHEDULE_CREATE = "schedule.create"
    SCHEDULE_UPDATE = "schedule.update"
    SCHEDULE_DELETE = "schedule.delete"

    # Menu actions
    MENU_CREATE = "menu.create"
    MENU_UPDATE = "menu.update"
    MENU_DELETE = "menu.delete"
    MENU_ADD_ITEM = "menu.add_item"
    MENU_UPDATE_ITEM = "menu.update_item"
    MENU_DELETE_ITEM = "menu.delete_item"
    MENU_IMPORT_ITEMS = "menu.import_items"
    MENU_EXPORT_ITEMS = "menu.export_items"

    # Widget actions
    WIDGET_CREATE = "widget.create"
    WIDGET_UPDATE = "widget.update"
    WIDGET_DELETE = "widget.delete"

    # Template actions
    TEMPLATE_CREATE = "template.create"
    TEMPLATE_UPDATE = "template.update"
    TEMPLATE_DELETE = "template.delete"


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class AuditLogResponse(BaseModel):
    """Audit log response DTO"""

    id: int
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    # Populated from relationships (optional)
    username: Optional[str] = None
    organization_name: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Audit log list response DTO"""

    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# =============================================================================
# FILTER DTOs (for query parameters)
# =============================================================================

class AuditLogFilters(BaseModel):
    """Query parameters for filtering audit logs"""

    user_id: Optional[int] = Field(None, description="Filter by user ID")
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    action: Optional[str] = Field(None, description="Filter by action (e.g., 'user.create')")
    resource_type: Optional[str] = Field(None, description="Filter by resource type (e.g., 'user')")
    resource_id: Optional[int] = Field(None, description="Filter by resource ID")
    start_date: Optional[datetime] = Field(None, description="Filter from this date")
    end_date: Optional[datetime] = Field(None, description="Filter until this date")
    limit: int = Field(100, ge=1, le=1000, description="Max results per page")
    offset: int = Field(0, ge=0, description="Number of results to skip")
