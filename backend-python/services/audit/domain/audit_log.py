"""
AuditLog Domain Entity
Business logic for audit trail
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class AuditLog:
    """AuditLog domain entity - tracks user actions"""

    id: Optional[int]
    user_id: Optional[int]
    organization_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: Optional[datetime] = None

    # Valid action patterns
    VALID_ACTIONS = [
        'user.create', 'user.update', 'user.delete', 'user.change_password',
        'organization.create', 'organization.update', 'organization.delete',
        'device.create', 'device.update', 'device.delete', 'device.activate',
        'content.upload', 'content.delete', 'content.assign',
        'tag.create', 'tag.update', 'tag.delete', 'tag.list',
        'auth.login', 'auth.logout', 'auth.register'
    ]

    # Valid resource types
    VALID_RESOURCE_TYPES = ['user', 'organization', 'device', 'content', 'tag', 'auth']

    def __post_init__(self):
        """Validate audit log data"""
        if not self.action or len(self.action.strip()) == 0:
            raise ValueError("Action is required")

        if not self.resource_type or len(self.resource_type.strip()) == 0:
            raise ValueError("Resource type is required")

        if self.resource_type not in self.VALID_RESOURCE_TYPES:
            raise ValueError(
                f"Resource type must be one of: {', '.join(self.VALID_RESOURCE_TYPES)}"
            )

    def is_user_action(self) -> bool:
        """Check if this is a user-related action"""
        return self.resource_type == 'user'

    def is_organization_action(self) -> bool:
        """Check if this is an organization-related action"""
        return self.resource_type == 'organization'

    def is_device_action(self) -> bool:
        """Check if this is a device-related action"""
        return self.resource_type == 'device'

    def is_tag_action(self) -> bool:
        """Check if this is a tag-related action"""
        return self.resource_type == 'tag'

    def is_system_action(self) -> bool:
        """Check if this is a system action (no user_id)"""
        return self.user_id is None
