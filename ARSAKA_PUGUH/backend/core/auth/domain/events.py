"""
Auth Domain Events

Immutable events emitted by auth operations.
Used for audit logging and event-driven workflows.

Source: INFRA-DEC-006-event-audit-immutable-facts.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


@dataclass(frozen=True, kw_only=True)
class AuthDomainEvent:
    """Base class for auth domain events."""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class UserRegistered(AuthDomainEvent):
    """Emitted when a new user registers."""
    user_id: UUID
    email: str
    auth_provider: str
    display_name: Optional[str] = None


@dataclass(frozen=True)
class UserVerified(AuthDomainEvent):
    """Emitted when user verifies their email."""
    user_id: UUID
    email: str


@dataclass(frozen=True)
class UserLoggedIn(AuthDomainEvent):
    """Emitted when user successfully logs in."""
    user_id: UUID
    email: str
    auth_provider: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass(frozen=True)
class UserLoggedOut(AuthDomainEvent):
    """Emitted when user logs out."""
    user_id: UUID


@dataclass(frozen=True)
class PasswordReset(AuthDomainEvent):
    """Emitted when user resets their password."""
    user_id: UUID
    email: str


@dataclass(frozen=True)
class PasswordChanged(AuthDomainEvent):
    """Emitted when user changes their password."""
    user_id: UUID


@dataclass(frozen=True)
class OAuthLinked(AuthDomainEvent):
    """Emitted when OAuth provider is linked to account."""
    user_id: UUID
    provider: str


@dataclass(frozen=True)
class OAuthUnlinked(AuthDomainEvent):
    """Emitted when OAuth provider is unlinked from account."""
    user_id: UUID
    provider: str


@dataclass(frozen=True)
class UserSuspended(AuthDomainEvent):
    """Emitted when user account is suspended."""
    user_id: UUID
    reason: Optional[str] = None


@dataclass(frozen=True)
class LoginFailed(AuthDomainEvent):
    """Emitted when login attempt fails."""
    email: str
    reason: str  # "invalid_credentials", "account_suspended", etc.
    ip_address: Optional[str] = None
