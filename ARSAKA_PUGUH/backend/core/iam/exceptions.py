"""
IAM Module Exceptions

Custom exceptions for Identity and Access Management operations.
"""


class IAMError(Exception):
    """Base class for IAM errors."""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class RoleNotFoundError(IAMError):
    """Raised when role is not found."""

    def __init__(self, role_id: str = None):
        super().__init__(
            message="Role not found",
            code="ROLE_NOT_FOUND"
        )
        self.role_id = role_id


class RoleNameExistsError(IAMError):
    """Raised when role name already exists in tenant."""

    def __init__(self, name: str):
        super().__init__(
            message=f"Role with name '{name}' already exists",
            code="ROLE_NAME_EXISTS"
        )
        self.name = name


class SystemRoleError(IAMError):
    """Raised when attempting to modify a system role."""

    def __init__(self, action: str = "modify"):
        super().__init__(
            message=f"Cannot {action} a system role",
            code="SYSTEM_ROLE_ERROR"
        )
        self.action = action


class RoleInUseError(IAMError):
    """Raised when attempting to delete a role that is assigned to users."""

    def __init__(self, role_id: str = None, user_count: int = 0):
        super().__init__(
            message=f"Cannot delete role: it is assigned to {user_count} user(s)",
            code="ROLE_IN_USE"
        )
        self.role_id = role_id
        self.user_count = user_count


class UserNotFoundError(IAMError):
    """Raised when user is not found in tenant."""

    def __init__(self, user_id: str = None):
        super().__init__(
            message="User not found in tenant",
            code="USER_NOT_FOUND"
        )
        self.user_id = user_id


class RoleAlreadyAssignedError(IAMError):
    """Raised when role is already assigned to user."""

    def __init__(self, user_id: str = None, role_id: str = None):
        super().__init__(
            message="Role is already assigned to this user",
            code="ROLE_ALREADY_ASSIGNED"
        )
        self.user_id = user_id
        self.role_id = role_id


class RoleNotAssignedError(IAMError):
    """Raised when trying to revoke a role that is not assigned."""

    def __init__(self, user_id: str = None, role_id: str = None):
        super().__init__(
            message="Role is not assigned to this user",
            code="ROLE_NOT_ASSIGNED"
        )
        self.user_id = user_id
        self.role_id = role_id


class PermissionNotFoundError(IAMError):
    """Raised when permission is not found."""

    def __init__(self, permission_id: str = None):
        super().__init__(
            message="Permission not found",
            code="PERMISSION_NOT_FOUND"
        )
        self.permission_id = permission_id


class TenantMismatchError(IAMError):
    """Raised when there is a tenant_id mismatch."""

    def __init__(self):
        super().__init__(
            message="Resource does not belong to the specified tenant",
            code="TENANT_MISMATCH"
        )
