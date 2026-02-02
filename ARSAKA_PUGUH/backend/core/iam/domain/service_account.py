"""
Service Account Domain Entity

Represents a service account for SDK/API authentication.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class ServiceAccountStatus(str, Enum):
    """Service account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class ServiceAccount:
    """Service account domain entity."""

    id: UUID
    tenant_id: UUID
    name: str
    client_id: str
    status: ServiceAccountStatus = ServiceAccountStatus.ACTIVE
    description: Optional[str] = None
    last_used_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Note: client_secret_hash is not exposed in domain entity
    # It's only used during creation and authentication

    def is_active(self) -> bool:
        """Check if service account is active."""
        return self.status == ServiceAccountStatus.ACTIVE

    def suspend(self) -> None:
        """Suspend the service account."""
        self.status = ServiceAccountStatus.SUSPENDED

    def revoke(self) -> None:
        """Revoke the service account."""
        self.status = ServiceAccountStatus.REVOKED

    def reactivate(self) -> None:
        """Reactivate the service account."""
        self.status = ServiceAccountStatus.ACTIVE
