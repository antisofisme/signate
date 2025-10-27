"""
Activity Log Model
System activity and audit logging for tracking user actions and events
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.database import Base


class ActivityLog(Base):
    """
    Activity log model for system audit trail

    Tracks all significant actions in the system including:
    - Device management (registration, approval, release)
    - Content operations (upload, assignment, deletion)
    - Playlist operations (creation, updates, assignments)
    - Tag operations (creation, assignments)

    Attributes:
        id: Primary key
        timestamp: When the action occurred
        user_id: User who performed the action (nullable for system actions)
        action_type: Type of action performed
        entity_type: Type of entity affected
        entity_id: ID of the affected entity
        entity_name: Name of the affected entity
        details: Additional metadata as JSON
        ip_address: IP address of the request
        user_agent: User agent string
        created_at: Timestamp when log was created
    """

    __tablename__ = "activity_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # User reference (nullable for system/device actions)
    user_id = Column(Integer, index=True)

    # Action classification
    action_type = Column(String(50), nullable=False, index=True)

    # Entity information
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer)
    entity_name = Column(String(255))

    # Additional details as JSON
    details = Column(JSON)

    # Request metadata
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)

    # Created timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action_type}', entity='{self.entity_type}:{self.entity_id}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ===========================================================================
# ACTION TYPE CONSTANTS
# ===========================================================================

class ActivityAction:
    """Constants for activity log action types"""

    # Device actions
    DEVICE_REGISTERED = "DEVICE_REGISTERED"
    DEVICE_APPROVED = "DEVICE_APPROVED"
    DEVICE_REJECTED = "DEVICE_REJECTED"
    DEVICE_RELEASED = "DEVICE_RELEASED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    DEVICE_DELETED = "DEVICE_DELETED"

    # Content actions
    CONTENT_UPLOADED = "CONTENT_UPLOADED"
    CONTENT_UPDATED = "CONTENT_UPDATED"
    CONTENT_ASSIGNED = "CONTENT_ASSIGNED"
    CONTENT_UNASSIGNED = "CONTENT_UNASSIGNED"
    CONTENT_DELETED = "CONTENT_DELETED"

    # Playlist actions
    PLAYLIST_CREATED = "PLAYLIST_CREATED"
    PLAYLIST_UPDATED = "PLAYLIST_UPDATED"
    PLAYLIST_DELETED = "PLAYLIST_DELETED"
    PLAYLIST_ASSIGNED = "PLAYLIST_ASSIGNED"
    PLAYLIST_UNASSIGNED = "PLAYLIST_UNASSIGNED"

    # Tag actions
    TAG_CREATED = "TAG_CREATED"
    TAG_UPDATED = "TAG_UPDATED"
    TAG_DELETED = "TAG_DELETED"
    TAG_ASSIGNED = "TAG_ASSIGNED"
    TAG_UNASSIGNED = "TAG_UNASSIGNED"

    # User actions
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"

    # System actions
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"


class EntityType:
    """Constants for entity types"""
    DEVICE = "device"
    CONTENT = "content"
    PLAYLIST = "playlist"
    TAG = "tag"
    USER = "user"
    SYSTEM = "system"
    ASSIGNMENT = "assignment"
