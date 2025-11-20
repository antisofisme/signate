"""
RBAC API Routes
HTTP endpoints for role management
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from shared.database import get_db
from shared.api_routes import RBACRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.auth import get_current_user, require_admin, require_manager, CurrentUser

from .dtos import (
    RoleCreateRequest, RoleUpdateRequest, RoleResponse, RoleListResponse,
    PermissionAddRequest, PermissionRemoveRequest, PermissionCheckRequest,
    PermissionCheckResponse, PermissionListResponse
)
from .repositories.role_repo import RoleRepository
from .use_cases.check_permission import CheckPermissionUseCase
from .use_cases.get_roles import GetRolesUseCase
from .use_cases.create_role import CreateRoleUseCase
from .use_cases.update_role import UpdateRoleUseCase
from .use_cases.delete_role import DeleteRoleUseCase
from .use_cases.manage_permissions import ManagePermissionsUseCase


router = APIRouter()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    """Get role repository instance"""
    return RoleRepository(db)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(RBACRoutes.LIST, response_model=RoleListResponse)
@handle_errors
def list_roles(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    include_system: bool = Query(True, description="Include system roles"),
    name: Optional[str] = Query(None, description="Filter by name"),
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """
    List roles with filtering

    Managers can see their organization's roles + system roles
    Admins can see all roles
    """
    use_case = GetRolesUseCase(role_repo)

    # Non-admins can only see their own organization
    if current_user.role not in ["super_admin", "admin"]:
        organization_id = current_user.organization_id

    result = use_case.execute(
        organization_id=organization_id,
        include_system=include_system,
        name_filter=name
    )

    return RoleListResponse(
        roles=[RoleResponse.model_validate(r) for r in result["roles"]],
        total=result["total"]
    )


@router.get(RBACRoutes.SYSTEM_ROLES, response_model=List[RoleResponse])
@handle_errors
def get_system_roles(
    current_user: CurrentUser = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Get all system roles (available to all authenticated users)"""
    use_case = GetRolesUseCase(role_repo)
    roles = use_case.get_system_roles()

    return [RoleResponse.model_validate(r) for r in roles]


@router.get(RBACRoutes.GET, response_model=RoleResponse)
@handle_errors
def get_role(
    role_id: int,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Get role by ID"""
    use_case = GetRolesUseCase(role_repo)
    role = use_case.get_by_id(role_id)

    # Check access: can only view own organization's roles (unless admin)
    if current_user.role not in ["super_admin", "admin"]:
        if role.organization_id != current_user.organization_id and not role.is_system_role:
            from shared.errors import AuthorizationError
            raise AuthorizationError(message="Access denied to this role")

    return RoleResponse.model_validate(role)


@router.post(RBACRoutes.CREATE, response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
@handle_errors
def create_role(
    request: RoleCreateRequest,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """
    Create new role

    Managers can create organization roles
    Admins can create system roles
    """
    # Only admins can create system roles
    if request.organization_id is None and current_user.role not in ["super_admin", "admin"]:
        from shared.errors import AuthorizationError
        raise AuthorizationError(message="Only admins can create system roles")

    # Managers can only create roles in their organization
    if current_user.role not in ["super_admin", "admin"]:
        request.organization_id = current_user.organization_id

    use_case = CreateRoleUseCase(role_repo)
    role = use_case.execute(
        name=request.name,
        description=request.description,
        organization_id=request.organization_id,
        permissions=request.permissions,
        created_by_id=current_user.id  # Audit trail (Migration 046)
    )

    return RoleResponse.model_validate(role)


@router.put(RBACRoutes.UPDATE, response_model=RoleResponse)
@handle_errors
def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Update role (only custom roles, not system roles)"""
    # Check access
    role = role_repo.find_by_id(role_id)
    if not role:
        from shared.errors import NotFoundError
        raise NotFoundError(message=f"Role with ID {role_id} not found")

    if current_user.role not in ["super_admin", "admin"]:
        if role.organization_id != current_user.organization_id:
            from shared.errors import AuthorizationError
            raise AuthorizationError(message="Access denied to this role")

    use_case = UpdateRoleUseCase(role_repo)
    updated_role = use_case.execute(
        role_id=role_id,
        name=request.name,
        description=request.description,
        permissions=request.permissions,
        updated_by_id=current_user.id  # Audit trail (Migration 046)
    )

    return RoleResponse.model_validate(updated_role)


@router.delete(RBACRoutes.DELETE, status_code=status.HTTP_204_NO_CONTENT)
@handle_errors
def delete_role(
    role_id: int,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Delete role (only custom roles, not system roles)"""
    # Check access
    role = role_repo.find_by_id(role_id)
    if not role:
        from shared.errors import NotFoundError
        raise NotFoundError(message=f"Role with ID {role_id} not found")

    if current_user.role not in ["super_admin", "admin"]:
        if role.organization_id != current_user.organization_id:
            from shared.errors import AuthorizationError
            raise AuthorizationError(message="Access denied to this role")

    use_case = DeleteRoleUseCase(role_repo)
    use_case.execute(role_id)


@router.post(RBACRoutes.CHECK_PERMISSION, response_model=PermissionCheckResponse)
@handle_errors
def check_permission(
    role_id: int,
    request: PermissionCheckRequest,
    current_user: CurrentUser = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Check if role has specific permission"""
    use_case = CheckPermissionUseCase(role_repo)
    result = use_case.execute(
        role_id=role_id,
        resource=request.resource,
        action=request.action
    )

    return PermissionCheckResponse(**result)


@router.get(RBACRoutes.GET_PERMISSIONS, response_model=PermissionListResponse)
@handle_errors
def get_permissions(
    role_id: int,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Get all permissions for role"""
    use_case = ManagePermissionsUseCase(role_repo)
    permissions = use_case.get_permissions(role_id)

    role = role_repo.find_by_id(role_id)

    return PermissionListResponse(
        role_id=role_id,
        role_name=role.name if role else "Unknown",
        permissions=permissions,
        total_resources=len(permissions),
        total_actions=sum(len(actions) for actions in permissions.values())
    )


@router.post(RBACRoutes.ADD_PERMISSION)
@handle_errors
def add_permission(
    role_id: int,
    request: PermissionAddRequest,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Add permission to role"""
    # Check access
    role = role_repo.find_by_id(role_id)
    if not role:
        from shared.errors import NotFoundError
        raise NotFoundError(message=f"Role with ID {role_id} not found")

    if current_user.role not in ["super_admin", "admin"]:
        if role.organization_id != current_user.organization_id:
            from shared.errors import AuthorizationError
            raise AuthorizationError(message="Access denied to this role")

    use_case = ManagePermissionsUseCase(role_repo)
    success = use_case.add_permission(
        role_id=role_id,
        resource=request.resource,
        action=request.action
    )

    return success_response(
        data={"success": success},
        message=f"Permission '{request.action}' added to resource '{request.resource}'"
    )


@router.delete(RBACRoutes.REMOVE_PERMISSION)
@handle_errors
def remove_permission(
    role_id: int,
    request: PermissionRemoveRequest,
    current_user: CurrentUser = Depends(require_manager),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Remove permission from role"""
    # Check access
    role = role_repo.find_by_id(role_id)
    if not role:
        from shared.errors import NotFoundError
        raise NotFoundError(message=f"Role with ID {role_id} not found")

    if current_user.role not in ["super_admin", "admin"]:
        if role.organization_id != current_user.organization_id:
            from shared.errors import AuthorizationError
            raise AuthorizationError(message="Access denied to this role")

    use_case = ManagePermissionsUseCase(role_repo)
    success = use_case.remove_permission(
        role_id=role_id,
        resource=request.resource,
        action=request.action
    )

    return success_response(
        data={"success": success},
        message=f"Permission '{request.action}' removed from resource '{request.resource}'"
    )
