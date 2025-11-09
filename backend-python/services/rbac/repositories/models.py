"""
RBAC SQLAlchemy Models
Maps to database tables created by migration 010
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from shared.database import Base


class Role(Base):
    """Role model for RBAC system"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    is_system_role = Column(Boolean, nullable=False, default=False)
    permissions = Column(JSONB, nullable=False, default={})
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True))

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', is_system={self.is_system_role})>"

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if role has specific permission"""
        if not isinstance(self.permissions, dict):
            return False

        resource_perms = self.permissions.get(resource, [])
        if isinstance(resource_perms, list):
            return action in resource_perms
        return False

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "organization_id": self.organization_id,
            "is_system_role": self.is_system_role,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
