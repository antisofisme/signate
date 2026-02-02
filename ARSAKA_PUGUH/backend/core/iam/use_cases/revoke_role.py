"""
Revoke Role from User Use Case
"""

from uuid import UUID

from ..interfaces import IIAMRepository


class RevokeRoleFromUserUseCase:
    """Use case for revoking a role from a user."""

    def __init__(self, repository: IIAMRepository):
        self._repository = repository

    async def execute(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> dict:
        """
        Revoke a role from a user.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            role_id: Role UUID

        Returns:
            Dict with revocation result

        Raises:
            UserNotFoundError: If user not found in tenant
            RoleNotFoundError: If role not found
            RoleNotAssignedError: If role not assigned to user
        """
        await self._repository.revoke_role_from_user(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
        )

        # Get updated user roles
        roles = await self._repository.get_user_roles(tenant_id, user_id)

        return {
            "user_id": str(user_id),
            "role_id": str(role_id),
            "revoked": True,
            "roles": [
                {
                    "id": str(role.id),
                    "name": role.name,
                    "display_name": role.display_name,
                    "is_system": role.is_system,
                }
                for role in roles
            ],
        }
