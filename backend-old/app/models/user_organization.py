"""
User-Organization Relationship Model
Junction table for users belonging to organizations with roles
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserOrganization(Base):
    """
    User-Organization relationship model

    Attributes:
        id: Primary key
        user_id: FK to user
        organization_id: FK to organization
        role_id: FK to role
        is_primary: Whether this is user's primary organization
        is_active: Whether user is active in this organization
        invited_by: FK to user who invited this user
        invitation_token: Token for invitation acceptance
        invitation_expires_at: When invitation expires
        joined_at: When user joined organization
        left_at: When user left organization (soft delete)
    """

    __tablename__ = "user_organizations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Is this the user's primary/default organization?
    is_primary = Column(Boolean, default=False)

    # Status in organization
    is_active = Column(Boolean, default=True)

    # Invitation tracking
    invited_by = Column(Integer, ForeignKey("users.id"))
    invitation_token = Column(String(100))
    invitation_expires_at = Column(DateTime)

    # Timestamps
    joined_at = Column(DateTime, server_default=func.now())
    left_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="organizations", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="user_organizations")
    role = relationship("Role", back_populates="user_organizations")
    inviter = relationship("User", foreign_keys=[invited_by])

    # Unique constraint: user can only be in an organization once
    __table_args__ = (
        UniqueConstraint('user_id', 'organization_id', name='_user_org_uc'),
    )

    def __repr__(self):
        return f"<UserOrganization(user_id={self.user_id}, org_id={self.organization_id}, role_id={self.role_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "role_id": self.role_id,
            "is_primary": self.is_primary,
            "is_active": self.is_active,
            "invited_by": self.invited_by,
            "invitation_token": self.invitation_token,
            "invitation_expires_at": self.invitation_expires_at.isoformat() if self.invitation_expires_at else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
        }

    def is_invitation_valid(self) -> bool:
        """Check if invitation is still valid"""
        if not self.invitation_token:
            return False

        if not self.invitation_expires_at:
            return True  # No expiry set

        from datetime import datetime
        return datetime.utcnow() < self.invitation_expires_at

    def accept_invitation(self):
        """Accept invitation and activate membership"""
        self.is_active = True
        self.invitation_token = None
        self.invitation_expires_at = None
        self.joined_at = func.now()

    def leave_organization(self):
        """Soft delete - mark as left"""
        self.is_active = False
        self.is_primary = False
        self.left_at = func.now()