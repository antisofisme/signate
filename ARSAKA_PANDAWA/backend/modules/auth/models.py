"""
ARSAKA_PANDAWA Backend - Auth Module Models
Follows CORE-STD-01 standards (UUID, soft delete, timestamps, audit trail)
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base
import uuid


class UserModel(Base):
    """User database model (Global Identity - CORE-REF-01)"""

    __tablename__ = "users"

    # Primary key (UUID - CORE-STD-01)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User credentials
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # User profile
    full_name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete

    # Timestamps (CORE-STD-01)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # Note: Tenant-scoped roles will be in TenantMemberModel (CORE-REF-01)


class TenantModel(Base):
    """Tenant/Organization database model (Multi-tenancy - CORE-STD-07)"""

    __tablename__ = "tenants"

    # Primary key (UUID - CORE-STD-01)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Tenant info
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)

    # Subscription (CORE-REF-04)
    subscription_status = Column(String(50), nullable=False, default="trial")  # trial, active, suspended, cancelled

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete

    # Timestamps (CORE-STD-01)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Audit trail
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class TenantMemberModel(Base):
    """Tenant Membership model (Tenant-scoped roles - CORE-REF-01)"""

    __tablename__ = "tenant_members"

    # Primary key (UUID - CORE-STD-01)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign keys
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Role within tenant (RBAC - CORE-STD-01)
    role = Column(String(50), nullable=False, default="member")  # owner, admin, member, viewer

    # Permissions (JSON column for module-specific permissions)
    # Format: {"pms": ["read", "write"], "pos": ["read"]}
    # Will be added in Phase 2

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps (CORE-STD-01)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Audit trail
    added_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    tenant = relationship("TenantModel", foreign_keys=[tenant_id])
    user = relationship("UserModel", foreign_keys=[user_id])
