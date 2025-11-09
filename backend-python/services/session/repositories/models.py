"""
Session SQLAlchemy Models
Maps to database tables created by migration 011
"""
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, text, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database import Base


class UserSession(Base):
    """UserSession model for JWT token tracking and revocation"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # User reference
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Session identification (SHA256 hash of JWT)
    session_token = Column(String(64), unique=True, nullable=False, index=True)
    refresh_token = Column(String(64), unique=True, nullable=True, index=True)

    # Client metadata
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6 support
    user_agent = Column(String(500))
    device_info = Column(JSONB)  # Browser, OS, device type, etc.

    # Session lifecycle
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    last_activity = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)  # Manual logout/revocation

    # Session type
    session_type = Column(
        String(20),
        nullable=False,
        default='web',
        server_default='web'
    )

    # Check constraints
    __table_args__ = (
        CheckConstraint(
            "session_type IN ('web', 'api', 'mobile', 'device')",
            name='check_session_type'
        ),
        CheckConstraint(
            "refresh_token IS NULL OR expires_at > created_at",
            name='check_refresh_token_expires'
        ),
    )

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, type='{self.session_type}', active={self.is_active})>"

    @property
    def is_active(self) -> bool:
        """Check if session is active (not revoked and not expired)"""
        now = datetime.utcnow()
        return self.revoked_at is None and self.expires_at > now

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_info": self.device_info,
            "session_type": self.session_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_active": self.is_active,
        }
