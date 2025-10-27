"""
Role Model
Role-based access control for organizations
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Role(Base):
    """
    Role model for RBAC

    Attributes:
        id: Primary key
        name: Internal role name (e.g., 'admin', 'editor')
        display_name: User-friendly display name
        description: Role description
        organization_id: FK to organization (NULL for system roles)
        is_system_role: Whether this is a system-defined role
        permissions: JSON object containing permissions
        created_at: Timestamp when created
    """

    __tablename__ = "roles"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Role Info
    name = Column(String(50), nullable=False)
    display_name = Column(String(100))
    description = Column(String(500))

    # Organization-specific role or system role
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    is_system_role = Column(Boolean, default=False)

    # Permissions as JSON
    # Format: {"resource": ["action1", "action2"], ...}
    # Example: {"devices": ["create", "read", "update", "delete"], "content": ["read"]}
    permissions = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="roles")
    user_organizations = relationship("UserOrganization", back_populates="role")

    # Unique constraint: role name must be unique per organization
    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='_role_org_uc'),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', org_id={self.organization_id})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "organization_id": self.organization_id,
            "is_system_role": self.is_system_role,
            "permissions": self.permissions or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def has_permission(self, resource: str, action: str) -> bool:
        """
        Check if role has specific permission

        Args:
            resource: Resource name (e.g., 'devices', 'content')
            action: Action name (e.g., 'create', 'read', 'update', 'delete')

        Returns:
            bool: True if role has permission
        """
        if not self.permissions:
            return False

        # Check for wildcard permissions
        if "*" in self.permissions and "*" in self.permissions["*"]:
            return True  # Super admin with all permissions

        # Check for resource wildcard
        if resource in self.permissions:
            resource_perms = self.permissions[resource]
            if "*" in resource_perms:
                return True  # All actions on this resource
            if action in resource_perms:
                return True  # Specific action allowed

        return False

    def get_permission_list(self) -> list:
        """
        Get flat list of permissions in format 'resource:action'

        Returns:
            list: List of permission strings
        """
        permission_list = []

        if not self.permissions:
            return permission_list

        for resource, actions in self.permissions.items():
            if resource == "*":
                # Wildcard - all permissions
                return ["*:*"]

            for action in actions:
                if action == "*":
                    # All actions for this resource
                    permission_list.append(f"{resource}:*")
                else:
                    permission_list.append(f"{resource}:{action}")

        return permission_list

    @staticmethod
    def create_default_roles():
        """
        Create default system roles

        Returns:
            list: List of default Role objects (not committed to DB)
        """
        return [
            Role(
                name="super_admin",
                display_name="Super Admin",
                description="Full system access",
                is_system_role=True,
                permissions={"*": ["*"]}
            ),
            Role(
                name="admin",
                display_name="Admin",
                description="Organization administrator",
                is_system_role=True,
                permissions={
                    "organizations": ["read", "update"],
                    "users": ["create", "read", "update", "delete"],
                    "roles": ["read"],
                    "devices": ["create", "read", "update", "delete"],
                    "content": ["create", "read", "update", "delete"],
                    "playlists": ["create", "read", "update", "delete"],
                    "tags": ["create", "read", "update", "delete"],
                    "logs": ["read"],
                    "settings": ["read", "update"]
                }
            ),
            Role(
                name="editor",
                display_name="Editor",
                description="Content editor",
                is_system_role=True,
                permissions={
                    "devices": ["read", "update"],
                    "content": ["create", "read", "update", "delete"],
                    "playlists": ["create", "read", "update", "delete"],
                    "tags": ["create", "read", "update"],
                    "logs": ["read"]
                }
            ),
            Role(
                name="viewer",
                display_name="Viewer",
                description="Read-only access",
                is_system_role=True,
                permissions={
                    "devices": ["read"],
                    "content": ["read"],
                    "playlists": ["read"],
                    "tags": ["read"],
                    "logs": ["read"]
                }
            )
        ]


from datetime import DateTime  # Add this import at the top