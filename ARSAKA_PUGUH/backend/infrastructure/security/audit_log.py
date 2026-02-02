"""
Security Audit Log Service

Provides security event logging for compliance and incident response.
Uses the security_audit_log table and log_security_event database function.

Source: Migration 015_security_audit_log.sql
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class EventCategory(str, Enum):
    """Security event categories."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    ADMIN_ACTION = "admin_action"
    SECURITY = "security"


class EventType(str, Enum):
    """Security event types."""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"

    # Authorization
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGE = "role_change"
    SCOPE_EXCEEDED = "scope_exceeded"

    # Data Access
    DATA_EXPORT = "data_export"
    BULK_READ = "bulk_read"
    SENSITIVE_ACCESS = "sensitive_access"

    # Admin Actions
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_SUSPENDED = "user_suspended"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    TENANT_CREATED = "tenant_created"
    TENANT_DELETED = "tenant_deleted"
    MEMBER_INVITED = "member_invited"
    MEMBER_REMOVED = "member_removed"

    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    SESSION_HIJACK_SUSPECTED = "session_hijack_suspected"
    IMPOSSIBLE_TRAVEL = "impossible_travel_detected"


class Severity(str, Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Status(str, Enum):
    """Event outcome status."""
    SUCCESS = "success"
    FAILURE = "failure"
    BLOCKED = "blocked"
    DENIED = "denied"
    PENDING = "pending"


@dataclass
class SecurityEvent:
    """Security event data."""
    event_type: EventType
    event_category: EventCategory
    status: Status = Status.SUCCESS
    severity: Severity = Severity.INFO
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    tenant_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    action: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SecurityAuditService:
    """Service for logging security events."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.

        Args:
            session: Async database session
        """
        self._session = session

    async def log_event(self, event: SecurityEvent) -> UUID:
        """Log a security event to the database.

        Args:
            event: Security event to log

        Returns:
            UUID of the created log entry
        """
        result = await self._session.execute(
            text("""
                SELECT log_security_event(
                    p_event_type := :event_type,
                    p_event_category := :event_category,
                    p_user_id := :user_id,
                    p_tenant_id := :tenant_id,
                    p_ip_address := :ip_address,
                    p_resource_type := :resource_type,
                    p_resource_id := :resource_id,
                    p_action := :action,
                    p_status := :status,
                    p_severity := :severity,
                    p_details := :details
                )
            """),
            {
                "event_type": event.event_type.value,
                "event_category": event.event_category.value,
                "user_id": str(event.user_id) if event.user_id else None,
                "tenant_id": str(event.tenant_id) if event.tenant_id else None,
                "ip_address": event.ip_address,
                "resource_type": event.resource_type,
                "resource_id": str(event.resource_id) if event.resource_id else None,
                "action": event.action,
                "status": event.status.value,
                "severity": event.severity.value,
                "details": self._build_details(event),
            }
        )
        await self._session.commit()

        log_id = result.scalar()
        return UUID(str(log_id))

    def _build_details(self, event: SecurityEvent) -> str:
        """Build JSONB details from event."""
        import json

        details = event.details or {}

        # Add optional fields to details
        if event.user_email:
            details["user_email"] = event.user_email
        if event.user_agent:
            details["user_agent"] = event.user_agent
        if event.request_id:
            details["request_id"] = event.request_id
        if event.session_id:
            details["session_id"] = event.session_id
        if event.error_code:
            details["error_code"] = event.error_code
        if event.error_message:
            details["error_message"] = event.error_message

        return json.dumps(details)

    # =========================================================================
    # Convenience Methods for Common Events
    # =========================================================================

    async def log_login_success(
        self,
        user_id: UUID,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ) -> UUID:
        """Log successful login."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.LOGIN_SUCCESS,
            event_category=EventCategory.AUTHENTICATION,
            status=Status.SUCCESS,
            severity=Severity.INFO,
            user_id=user_id,
            user_email=email,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login",
        ))

    async def log_login_failure(
        self,
        email: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> UUID:
        """Log failed login attempt."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.LOGIN_FAILURE,
            event_category=EventCategory.AUTHENTICATION,
            status=Status.FAILURE,
            severity=Severity.WARNING,
            user_id=user_id,
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login",
            error_message=reason,
            details={"reason": reason},
        ))

    async def log_account_locked(
        self,
        user_id: UUID,
        email: str,
        lock_duration_minutes: int,
        failed_attempts: int,
        ip_address: Optional[str] = None,
    ) -> UUID:
        """Log account lockout event."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.ACCOUNT_LOCKED,
            event_category=EventCategory.AUTHENTICATION,
            status=Status.BLOCKED,
            severity=Severity.WARNING,
            user_id=user_id,
            user_email=email,
            ip_address=ip_address,
            action="login",
            resource_type="user",
            resource_id=user_id,
            details={
                "lock_duration_minutes": lock_duration_minutes,
                "failed_attempts": failed_attempts,
            },
        ))

    async def log_permission_denied(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID],
        action: str,
        required_permission: str,
        tenant_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
    ) -> UUID:
        """Log permission denied event."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.PERMISSION_DENIED,
            event_category=EventCategory.AUTHORIZATION,
            status=Status.DENIED,
            severity=Severity.WARNING,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details={"required_permission": required_permission},
        ))

    async def log_api_key_created(
        self,
        user_id: UUID,
        tenant_id: UUID,
        api_key_id: UUID,
        key_name: str,
        ip_address: Optional[str] = None,
    ) -> UUID:
        """Log API key creation."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.API_KEY_CREATED,
            event_category=EventCategory.ADMIN_ACTION,
            status=Status.SUCCESS,
            severity=Severity.INFO,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            resource_type="api_key",
            resource_id=api_key_id,
            action="create",
            details={"key_name": key_name},
        ))

    async def log_api_key_revoked(
        self,
        user_id: UUID,
        tenant_id: UUID,
        api_key_id: UUID,
        key_name: str,
        ip_address: Optional[str] = None,
    ) -> UUID:
        """Log API key revocation."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.API_KEY_REVOKED,
            event_category=EventCategory.ADMIN_ACTION,
            status=Status.SUCCESS,
            severity=Severity.WARNING,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            resource_type="api_key",
            resource_id=api_key_id,
            action="revoke",
            details={"key_name": key_name},
        ))

    async def log_suspicious_activity(
        self,
        user_id: Optional[UUID],
        activity_type: str,
        description: str,
        ip_address: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """Log suspicious activity detection."""
        event_details = details or {}
        event_details["activity_type"] = activity_type
        event_details["description"] = description

        return await self.log_event(SecurityEvent(
            event_type=EventType.SUSPICIOUS_ACTIVITY,
            event_category=EventCategory.SECURITY,
            status=Status.BLOCKED,
            severity=Severity.ERROR,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            action=activity_type,
            error_message=description,
            details=event_details,
        ))

    async def log_rate_limit_exceeded(
        self,
        user_id: Optional[UUID],
        endpoint: str,
        limit: int,
        window_seconds: int,
        ip_address: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
    ) -> UUID:
        """Log rate limit exceeded event."""
        return await self.log_event(SecurityEvent(
            event_type=EventType.RATE_LIMIT_EXCEEDED,
            event_category=EventCategory.SECURITY,
            status=Status.BLOCKED,
            severity=Severity.WARNING,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            resource_type="endpoint",
            action="rate_limit",
            details={
                "endpoint": endpoint,
                "limit": limit,
                "window_seconds": window_seconds,
            },
        ))


# ============================================================================
# Dependency Injection Factory
# ============================================================================

def get_security_audit_service(session: AsyncSession) -> SecurityAuditService:
    """Factory function for dependency injection."""
    return SecurityAuditService(session)
