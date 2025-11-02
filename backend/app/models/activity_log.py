"""
Activity Log Model (FIXED)
System activity and audit logging for tracking user actions and events
Fixed to match actual database schema - resolves 500 errors
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.database import Base


class ActivityLog(Base):
    """
    Activity log model for system audit trail - FIXED VERSION

    Tracks all significant actions in the system including:
    - Device management (registration, approval, release)
    - Content operations (upload, assignment, deletion)
    - Playlist operations (creation, updates, assignments)
    - Tag operations (creation, assignments)

    FIXED: Column names now match actual database schema
    """

    __tablename__ = "activity_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # User reference (nullable for system/device actions)
    user_id = Column(Integer, index=True)

    # Action classification - FIXED: Changed from action_type to action
    action = Column(String(100), nullable=False, index=True)

    # Entity information
    entity_type = Column(String(50), index=True)
    entity_id = Column(Integer)

    # NOTE: These columns exist in model but NOT in database
    # Commented out to prevent errors - add to DB if needed
    # entity_name = Column(String(255))
    # user_agent = Column(Text)

    # Additional details as JSONB (matches database)
    details = Column(JSONB)

    # Request metadata
    ip_address = Column(String(45))  # IPv4 or IPv6

    # Created timestamp - FIXED: Removed timezone to match database
    created_at = Column(DateTime, server_default=func.now())

    # Backward compatibility properties
    @property
    def action_type(self):
        """Property for backward compatibility - maps to action column"""
        return self.action

    @action_type.setter
    def action_type(self, value):
        """Setter for backward compatibility - maps to action column"""
        self.action = value

    # Optional properties for missing columns
    @property
    def entity_name(self):
        """Returns entity name from details if available"""
        if self.details and isinstance(self.details, dict):
            return self.details.get('entity_name')
        return None

    @entity_name.setter
    def entity_name(self, value):
        """Store entity_name in details JSON"""
        if not self.details:
            self.details = {}
        self.details['entity_name'] = value

    @property
    def user_agent(self):
        """Returns user agent from details if available"""
        if self.details and isinstance(self.details, dict):
            return self.details.get('user_agent')
        return None

    @user_agent.setter
    def user_agent(self, value):
        """Store user_agent in details JSON"""
        if not self.details:
            self.details = {}
        self.details['user_agent'] = value

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "action_type": self.action,  # Include for backward compatibility
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,  # Will get from details if available
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,  # Will get from details if available
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