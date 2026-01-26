"""
Tenant Module Exceptions

Domain-specific exceptions for tenant operations.
"""


class TenantError(Exception):
    """Base exception for tenant errors."""
    pass


class TenantNotFoundError(TenantError):
    """Tenant not found."""
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(f"Tenant not found: {tenant_id}")


class TenantSlugExistsError(TenantError):
    """Tenant slug already exists."""
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Tenant slug already exists: {slug}")


class MembershipError(TenantError):
    """Base exception for membership errors."""
    pass


class AlreadyMemberError(MembershipError):
    """User is already a member of the tenant."""
    def __init__(self, user_id: str, tenant_id: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        super().__init__(f"User {user_id} is already a member of tenant {tenant_id}")


class NotMemberError(MembershipError):
    """User is not a member of the tenant."""
    def __init__(self, user_id: str, tenant_id: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        super().__init__(f"User {user_id} is not a member of tenant {tenant_id}")


class CannotRemoveOwnerError(MembershipError):
    """Cannot remove the owner from tenant."""
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(f"Cannot remove owner from tenant {tenant_id}")


class CannotDemoteOwnerError(MembershipError):
    """Cannot demote the only owner."""
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(f"Cannot demote the only owner of tenant {tenant_id}")


class InsufficientPermissionError(MembershipError):
    """User does not have sufficient permissions."""
    def __init__(self, required_role: str):
        self.required_role = required_role
        super().__init__(f"Requires {required_role} role or higher")


class InvitationError(TenantError):
    """Base exception for invitation errors."""
    pass


class InvitationNotFoundError(InvitationError):
    """Invitation not found."""
    def __init__(self, invitation_id: str):
        self.invitation_id = invitation_id
        super().__init__(f"Invitation not found: {invitation_id}")


class InvitationExpiredError(InvitationError):
    """Invitation has expired."""
    def __init__(self, invitation_id: str):
        self.invitation_id = invitation_id
        super().__init__(f"Invitation has expired: {invitation_id}")


class InvitationAlreadyUsedError(InvitationError):
    """Invitation has already been used."""
    def __init__(self, invitation_id: str):
        self.invitation_id = invitation_id
        super().__init__(f"Invitation already used: {invitation_id}")


class InvitationAlreadyPendingError(InvitationError):
    """A pending invitation already exists for this email."""
    def __init__(self, email: str, tenant_id: str):
        self.email = email
        self.tenant_id = tenant_id
        super().__init__(f"Pending invitation already exists for {email} to tenant {tenant_id}")


class PlanLimitError(TenantError):
    """Plan limit exceeded."""
    pass


class MaxMembersExceededError(PlanLimitError):
    """Maximum number of members exceeded for plan."""
    def __init__(self, plan: str, max_members: int):
        self.plan = plan
        self.max_members = max_members
        super().__init__(f"Plan {plan} allows maximum {max_members} members")
