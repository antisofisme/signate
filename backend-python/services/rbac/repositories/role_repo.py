"""
RBAC Role Repository
Data access layer for Role model
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .models import Role


class RoleRepository:
    """Repository for Role model with CRUD operations"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, role_id: int) -> Optional[Role]:
        """
        Find role by ID

        Args:
            role_id: Role ID

        Returns:
            Role model or None if not found
        """
        return self.db.query(Role).filter(Role.id == role_id).first()

    def find_by_name(self, name: str, organization_id: Optional[int] = None) -> Optional[Role]:
        """
        Find role by name within organization scope

        Args:
            name: Role name
            organization_id: Organization ID (None for system roles)

        Returns:
            Role model or None if not found
        """
        query = self.db.query(Role).filter(Role.name == name)

        if organization_id is None:
            # System roles
            query = query.filter(Role.is_system_role == True)
        else:
            # Organization roles
            query = query.filter(
                and_(
                    Role.organization_id == organization_id,
                    Role.is_system_role == False
                )
            )

        return query.first()

    def get_all(self, organization_id: Optional[int] = None, include_system: bool = True) -> List[Role]:
        """
        Get all roles

        Args:
            organization_id: Filter by organization (None = only system roles)
            include_system: Include system roles in results

        Returns:
            List of Role models
        """
        query = self.db.query(Role)

        if organization_id is None:
            # Only system roles
            query = query.filter(Role.is_system_role == True)
        else:
            # Organization roles + optionally system roles
            if include_system:
                query = query.filter(
                    (Role.organization_id == organization_id) |
                    (Role.is_system_role == True)
                )
            else:
                query = query.filter(
                    and_(
                        Role.organization_id == organization_id,
                        Role.is_system_role == False
                    )
                )

        return query.order_by(Role.is_system_role.desc(), Role.name).all()

    def get_system_roles(self) -> List[Role]:
        """
        Get all system roles

        Returns:
            List of system Role models
        """
        return self.db.query(Role).filter(Role.is_system_role == True).order_by(Role.name).all()

    def get_organization_roles(self, organization_id: int) -> List[Role]:
        """
        Get roles for specific organization (custom roles only)

        Args:
            organization_id: Organization ID

        Returns:
            List of Role models
        """
        return self.db.query(Role).filter(
            and_(
                Role.organization_id == organization_id,
                Role.is_system_role == False
            )
        ).order_by(Role.name).all()

    def create(self, role: Role) -> Role:
        """
        Create new role

        Args:
            role: Role model to create

        Returns:
            Created Role model with ID
        """
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def update(self, role: Role) -> Role:
        """
        Update existing role

        Args:
            role: Role model with updated data

        Returns:
            Updated Role model
        """
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role_id: int) -> bool:
        """
        Delete role

        Args:
            role_id: Role ID to delete

        Returns:
            True if deleted, False if not found
        """
        role = self.find_by_id(role_id)
        if not role:
            return False

        # Don't allow deleting system roles
        if role.is_system_role:
            return False

        self.db.delete(role)
        self.db.commit()
        return True

    def check_permission(self, role_id: int, resource: str, action: str) -> bool:
        """
        Check if role has specific permission

        Args:
            role_id: Role ID
            resource: Resource name (e.g., "devices", "content")
            action: Action name (e.g., "read", "write", "delete")

        Returns:
            True if role has permission, False otherwise
        """
        role = self.find_by_id(role_id)
        if not role:
            return False

        return role.has_permission(resource, action)

    def add_permission(self, role_id: int, resource: str, action: str) -> bool:
        """
        Add permission to role

        Args:
            role_id: Role ID
            resource: Resource name
            action: Action name

        Returns:
            True if added, False if role not found or is system role
        """
        role = self.find_by_id(role_id)
        if not role or role.is_system_role:
            return False

        if not isinstance(role.permissions, dict):
            role.permissions = {}

        if resource not in role.permissions:
            role.permissions[resource] = []

        if action not in role.permissions[resource]:
            role.permissions[resource].append(action)

        # Mark as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(role, "permissions")

        self.db.commit()
        return True

    def remove_permission(self, role_id: int, resource: str, action: str) -> bool:
        """
        Remove permission from role

        Args:
            role_id: Role ID
            resource: Resource name
            action: Action name

        Returns:
            True if removed, False if role not found or is system role
        """
        role = self.find_by_id(role_id)
        if not role or role.is_system_role:
            return False

        if not isinstance(role.permissions, dict):
            return False

        if resource in role.permissions and action in role.permissions[resource]:
            role.permissions[resource].remove(action)

            # Clean up empty resource
            if not role.permissions[resource]:
                del role.permissions[resource]

            # Mark as modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(role, "permissions")

            self.db.commit()
            return True

        return False

    def exists_by_name(self, name: str, organization_id: Optional[int] = None, exclude_id: Optional[int] = None) -> bool:
        """
        Check if role name exists

        Args:
            name: Role name
            organization_id: Organization ID (None for system roles)
            exclude_id: Exclude this role ID from check (for updates)

        Returns:
            True if exists, False otherwise
        """
        query = self.db.query(Role).filter(Role.name == name)

        if organization_id is None:
            query = query.filter(Role.is_system_role == True)
        else:
            query = query.filter(
                and_(
                    Role.organization_id == organization_id,
                    Role.is_system_role == False
                )
            )

        if exclude_id:
            query = query.filter(Role.id != exclude_id)

        return query.first() is not None
