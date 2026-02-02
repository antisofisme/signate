"""
API Key Domain Entity

Service account credentials for machine-to-machine authentication.
Used by external applications integrating with PUGUH Platform.

Key Format:
- Production: pk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
- Test: pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum
import secrets
import hashlib


class ApiKeyStatus(str, Enum):
    """API key status."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class ApiKeyEnvironment(str, Enum):
    """API key environment."""
    LIVE = "live"  # Production
    TEST = "test"  # Development/testing


@dataclass
class ApiKey:
    """
    API Key domain entity.

    Represents a service account credential for programmatic access.
    API keys are scoped to a tenant and have specific permissions.
    """
    # Identity
    key_id: UUID
    tenant_id: UUID
    created_by_user_id: UUID

    # Key data (hashed for storage)
    key_prefix: str  # First 8 chars for display (e.g., "pk_live_a")
    key_hash: str    # SHA-256 hash of full key

    # Metadata
    name: str  # User-friendly name (e.g., "Production API Key")
    description: Optional[str] = None
    environment: ApiKeyEnvironment = ApiKeyEnvironment.LIVE

    # Permissions/Scopes
    scopes: List[str] = field(default_factory=list)  # e.g., ["read:tenants", "write:decisions"]

    # Status
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE
    revoked_at: Optional[datetime] = None
    revoked_by_user_id: Optional[UUID] = None

    # Expiration
    expires_at: Optional[datetime] = None  # None = never expires

    # Usage tracking
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    usage_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def generate_key(cls, environment: ApiKeyEnvironment = ApiKeyEnvironment.LIVE) -> str:
        """
        Generate a new API key string.

        Format: pk_{env}_{32_random_chars}
        Example: pk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

        Args:
            environment: live or test

        Returns:
            Full API key string (store securely, only shown once)
        """
        random_part = secrets.token_hex(16)  # 32 hex chars
        return f"pk_{environment.value}_{random_part}"

    @classmethod
    def hash_key(cls, full_key: str) -> str:
        """
        Hash API key for secure storage.

        Args:
            full_key: Full API key string

        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(full_key.encode()).hexdigest()

    @classmethod
    def get_prefix(cls, full_key: str) -> str:
        """
        Extract display prefix from key.

        Args:
            full_key: Full API key string

        Returns:
            First 12 chars for display (e.g., "pk_live_a1b2")
        """
        return full_key[:12] if len(full_key) >= 12 else full_key

    @classmethod
    def get_environment_from_key(cls, full_key: str) -> ApiKeyEnvironment:
        """
        Extract environment from key string.

        Args:
            full_key: Full API key string

        Returns:
            Environment (live or test)
        """
        if full_key.startswith("pk_test_"):
            return ApiKeyEnvironment.TEST
        return ApiKeyEnvironment.LIVE

    @classmethod
    def create(
        cls,
        full_key: str,
        tenant_id: UUID,
        created_by_user_id: UUID,
        name: str,
        description: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> "ApiKey":
        """
        Create a new API key entity.

        Args:
            full_key: Full API key string (from generate_key)
            tenant_id: Tenant this key belongs to
            created_by_user_id: User creating the key
            name: Display name for the key
            description: Optional description
            scopes: Permission scopes
            expires_in_days: Days until expiration (None = never)

        Returns:
            New ApiKey entity
        """
        environment = cls.get_environment_from_key(full_key)
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        return cls(
            key_id=uuid4(),
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            key_prefix=cls.get_prefix(full_key),
            key_hash=cls.hash_key(full_key),
            name=name,
            description=description,
            environment=environment,
            scopes=scopes or [],
            expires_at=expires_at,
        )

    def is_valid(self) -> bool:
        """Check if API key is valid for use."""
        if self.status != ApiKeyStatus.ACTIVE:
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        return True

    def verify(self, full_key: str) -> bool:
        """
        Verify a full key against this entity.

        Args:
            full_key: Full API key to verify

        Returns:
            True if key matches
        """
        return self.key_hash == self.hash_key(full_key)

    def revoke(self, revoked_by: UUID) -> None:
        """Revoke this API key."""
        self.status = ApiKeyStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_by_user_id = revoked_by
        self.updated_at = datetime.utcnow()

    def record_usage(self, ip_address: Optional[str] = None) -> None:
        """Record key usage."""
        self.last_used_at = datetime.utcnow()
        self.last_used_ip = ip_address
        self.usage_count += 1
        self.updated_at = datetime.utcnow()

    def has_scope(self, required_scope: str) -> bool:
        """
        Check if key has required scope.

        Supports wildcard matching:
        - "write:*" matches "write:tenants", "write:decisions"
        - "*" matches everything

        Args:
            required_scope: Required scope string

        Returns:
            True if key has scope
        """
        if not self.scopes:
            return True  # Empty scopes = full access

        for scope in self.scopes:
            if scope == "*":
                return True
            if scope == required_scope:
                return True
            # Wildcard matching (e.g., "read:*" matches "read:tenants")
            if scope.endswith(":*"):
                prefix = scope[:-1]  # "read:"
                if required_scope.startswith(prefix):
                    return True

        return False

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_sensitive: Include hash (for internal use)

        Returns:
            Dictionary representation
        """
        result = {
            "key_id": str(self.key_id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "description": self.description,
            "key_prefix": self.key_prefix,  # Only show prefix, never full key
            "environment": self.environment.value,
            "scopes": self.scopes,
            "status": self.status.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "created_by_user_id": str(self.created_by_user_id),
        }

        if include_sensitive:
            result["key_hash"] = self.key_hash

        return result


@dataclass
class ApiKeyWithSecret:
    """
    API Key with the secret key (only returned on creation).

    The secret is only shown once and should be stored securely by the user.
    """
    api_key: ApiKey
    secret_key: str  # Full key - only available at creation time

    def to_dict(self) -> dict:
        """Convert to dictionary with secret."""
        result = self.api_key.to_dict()
        result["secret_key"] = self.secret_key  # Only on creation!
        return result
