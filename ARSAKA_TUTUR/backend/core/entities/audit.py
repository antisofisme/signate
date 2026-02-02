"""
Audit entities for logging and compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4


@dataclass
class AuditEntry:
    """
    Single audit log entry (APPEND-ONLY).

    Audit logs are immutable once created.
    """
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = ""

    # Actor information
    actor_type: str = ""  # "user", "api_key", "system"
    actor_id: str = ""

    # Action details
    action: str = ""  # e.g., "chat.message.create", "session.delete"
    resource_type: str = ""  # e.g., "message", "session", "fact"
    resource_id: Optional[str] = None

    # Request context
    request_id: Optional[str] = None
    ip_address: Optional[str] = None

    # Additional details
    details: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: str = "success"  # "success", "failure", "error"

    # Timestamp (NO updated_at - immutable!)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        tenant_id: str,
        actor_type: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> "AuditEntry":
        """Create a new audit entry."""
        return cls(
            tenant_id=tenant_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            ip_address=ip_address,
            details=details or {},
            status=status,
        )


@dataclass
class AuditLog:
    """
    Collection of audit entries with metadata.
    """
    entries: list = field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0

    # Filters applied
    filters: Dict[str, Any] = field(default_factory=dict)

    def add_entry(self, entry: AuditEntry) -> None:
        """Add entry to log."""
        self.entries.append(entry)
        self.total += 1


# Common audit actions
class AuditActions:
    """Constants for audit action names."""

    # Chat actions
    CHAT_MESSAGE_CREATE = "chat.message.create"
    CHAT_MESSAGE_REDACT = "chat.message.redact"

    # Session actions
    SESSION_CREATE = "session.create"
    SESSION_DELETE = "session.delete"

    # Memory actions
    FACT_CREATE = "memory.fact.create"
    FACT_DEACTIVATE = "memory.fact.deactivate"

    # Search actions
    SEARCH_EXECUTE = "search.execute"
    SEARCH_SESSION = "search.session"

    # Admin actions
    ADMIN_EMBED = "admin.embed"
    ADMIN_TENANT_UPDATE = "admin.tenant.update"

    # Auth actions
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_API_KEY_CREATE = "auth.api_key.create"
    AUTH_API_KEY_REVOKE = "auth.api_key.revoke"
