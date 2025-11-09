"""
RBAC Repositories
"""
from .models import Role
from .role_repo import RoleRepository

__all__ = ["Role", "RoleRepository"]
