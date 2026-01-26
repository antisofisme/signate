"""
User Domain Entity

Core business entity representing a user identity.
Framework-agnostic, pure Python.

Source: INFRA-DEC-007-identity-model.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class AuthProvider(str, Enum):
    """Authentication provider."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


@dataclass
class User:
    """
    User domain entity.

    Represents a global user identity in the SaaS platform.
    Users can belong to multiple tenants via memberships.
    """
    # Identity
    user_id: UUID
    email: str

    # Authentication
    auth_provider: AuthProvider
    password_hash: Optional[str] = None
    oauth_provider_id: Optional[str] = None

    # Profile
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

    # Status
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    email_verified_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None

    # Linked OAuth providers (for account linking)
    linked_providers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate user entity."""
        # Email must be lowercase
        self.email = self.email.lower().strip()

        # Local auth requires password
        if self.auth_provider == AuthProvider.LOCAL and not self.password_hash:
            raise ValueError("Local auth requires password_hash")

        # OAuth auth requires provider_id
        if self.auth_provider in (AuthProvider.GOOGLE, AuthProvider.GITHUB):
            if not self.oauth_provider_id:
                raise ValueError(f"{self.auth_provider.value} auth requires oauth_provider_id")

    @classmethod
    def create_local(
        cls,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> "User":
        """Create a new local auth user.

        Args:
            email: User's email address
            password_hash: Hashed password
            display_name: User's display name

        Returns:
            New User entity
        """
        return cls(
            user_id=uuid4(),
            email=email.lower().strip(),
            auth_provider=AuthProvider.LOCAL,
            password_hash=password_hash,
            display_name=display_name,
            status=UserStatus.PENDING_VERIFICATION,
        )

    @classmethod
    def create_oauth(
        cls,
        email: str,
        provider: AuthProvider,
        provider_id: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> "User":
        """Create a new OAuth user.

        OAuth users are auto-verified since email comes from trusted provider.

        Args:
            email: User's email from OAuth provider
            provider: OAuth provider (google, github)
            provider_id: Provider's unique user ID
            display_name: Display name from provider
            avatar_url: Avatar URL from provider

        Returns:
            New User entity (already verified)
        """
        now = datetime.utcnow()
        return cls(
            user_id=uuid4(),
            email=email.lower().strip(),
            auth_provider=provider,
            oauth_provider_id=provider_id,
            display_name=display_name,
            avatar_url=avatar_url,
            status=UserStatus.ACTIVE,  # OAuth users are auto-verified
            email_verified_at=now,
            linked_providers=[provider.value],
        )

    def is_active(self) -> bool:
        """Check if user can login."""
        return self.status == UserStatus.ACTIVE

    def is_verified(self) -> bool:
        """Check if email is verified."""
        return self.email_verified_at is not None

    def verify_email(self) -> None:
        """Mark email as verified and activate user."""
        self.email_verified_at = datetime.utcnow()
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_profile(
        self,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> None:
        """Update user profile."""
        if display_name is not None:
            self.display_name = display_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()

    def link_oauth(self, provider: str, provider_id: str) -> None:
        """Link an OAuth provider to this user."""
        if provider not in self.linked_providers:
            self.linked_providers.append(provider)
        self.oauth_provider_id = provider_id
        self.updated_at = datetime.utcnow()

    def can_unlink_oauth(self, provider: str) -> bool:
        """Check if OAuth provider can be unlinked.

        Must have at least one auth method remaining.
        """
        if provider not in self.linked_providers:
            return False

        # If local auth exists (has password), can unlink OAuth
        if self.password_hash:
            return True

        # If multiple OAuth providers linked, can unlink one
        return len(self.linked_providers) > 1

    def to_dict(self) -> dict:
        """Convert to dictionary (for API responses)."""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "auth_provider": self.auth_provider.value,
            "linked_providers": self.linked_providers,
            "status": self.status.value,
            "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
            "created_at": self.created_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
