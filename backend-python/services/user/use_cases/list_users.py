"""List Users Use Case"""

from typing import List, Dict, Any, Optional
from ..domain.user import User
from ..domain.interfaces import IUserRepository


class ListUsersUseCase:
    """Use case for listing users"""

    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    def execute(
        self,
        organization_id: Optional[int] = None,
        role: Optional[str] = None,
        active_only: bool = False
    ) -> Dict[str, Any]:
        """
        List users with filters

        Args:
            organization_id: Filter by organization
            role: Filter by role
            active_only: Only active users

        Returns:
            Dictionary with users list and stats
        """

        users = self.user_repo.get_all(
            organization_id=organization_id,
            role=role,
            active_only=active_only
        )

        # Calculate stats
        total = len(users)
        active = sum(1 for user in users if user.is_active)

        return {
            "users": users,
            "total": total,
            "active": active
        }

    def get_user_organization_name(self, user_id: int) -> Optional[str]:
        """Get organization name for user"""
        return self.user_repo.get_organization_name(user_id)
