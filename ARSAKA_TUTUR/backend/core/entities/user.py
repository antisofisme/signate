"""
User entities for authentication and authorization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4


@dataclass
class UserProfile:
    """User profile with preferences."""
    display_name: str = ""
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"


@dataclass
class User:
    """
    User entity for chat.

    Users are scoped to tenants and can have different permissions.
    """
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""
    external_user_id: str = ""  # ID from external auth system

    # Profile
    profile: UserProfile = field(default_factory=UserProfile)

    # Role and permissions
    role: str = "user"  # "admin", "user", "readonly"
    custom_permissions: List[str] = field(default_factory=list)

    # Status
    is_active: bool = True
    last_seen_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def display_name(self) -> str:
        """Get display name from profile."""
        return self.profile.display_name or self.external_user_id

    @property
    def email(self) -> Optional[str]:
        """Get email from profile."""
        return self.profile.email

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        if self.role == "admin":
            return True
        if permission in self.custom_permissions:
            return True

        # Default role permissions
        if self.role == "user":
            return permission in [
                "chat.read", "chat.write",
                "session.read", "session.write", "session.delete",
                "knowledge.read",
            ]
        if self.role == "readonly":
            return permission in [
                "chat.read", "session.read", "knowledge.read"
            ]

        return False

    def update_last_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


@dataclass
class APIKeyPayload:
    """
    Payload extracted from API key authentication.
    """
    key_id: UUID
    tenant_id: str
    name: str
    permissions: List[str] = field(default_factory=list)
    rate_limit_per_minute: int = 100

    def has_permission(self, permission: str) -> bool:
        """Check if API key has specific permission."""
        if "admin" in self.permissions:
            return True
        return permission in self.permissions
