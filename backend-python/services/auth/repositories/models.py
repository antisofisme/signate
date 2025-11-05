"""
SQLAlchemy Models
Database representation
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class OrganizationModel(Base):
    """Organization database model"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    organization_pin = Column(String(8), unique=True, nullable=False, index=True)  # Fixed: 8 digits
    description = Column(String(500), nullable=True)
    address = Column(String(500), nullable=True)
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    users = relationship("UserModel", back_populates="organization")


class UserModel(Base):
    """User database model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="ADMIN")
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    organization = relationship("OrganizationModel", back_populates="users")


class AuditLogModel(Base):
    """Audit log database model - tracks all user actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action (nullable for system actions)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Which organization (nullable for cross-org or when org deleted)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    # What action was performed
    action = Column(String(100), nullable=False, index=True)  # e.g., 'user.create', 'org.update', 'device.delete'

    # What resource type
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., 'user', 'organization', 'device'

    # What specific resource (nullable if resource deleted)
    resource_id = Column(Integer, nullable=True, index=True)

    # Additional context (JSONB for PostgreSQL, JSON for others)
    details = Column(JSON, nullable=True)  # e.g., {"old_email": "...", "new_email": "..."}

    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id])
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
