"""
IAM API Routes

FastAPI router for Identity and Access Management endpoints.

Source: PUGUH UI_API_MAPPING.md - IAM Domain
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status

from .schemas import (
    ListUsersResponse,
    UserDetailResponse,
    ListRolesResponse,
    RoleDetailResponse,
    ListPermissionsResponse,
    PermissionMatrixResponse,
    ListServiceAccountsResponse,
    SuccessResponse,
    CreateRoleRequest,
    UpdateRoleRequest,
    AssignRoleRequest,
    RoleCreatedResponse,
    RoleUpdatedResponse,
    RoleDeletedResponse,
    RoleAssignmentResponse,
)
from .dependencies import (
    get_current_user_id,
    get_current_tenant_id,
    get_list_users_use_case,
    get_get_user_use_case,
    get_list_roles_use_case,
    get_get_role_use_case,
    get_get_permissions_use_case,
    get_list_service_accounts_use_case,
    get_create_role_use_case,
    get_update_role_use_case,
    get_delete_role_use_case,
    get_assign_role_use_case,
    get_revoke_role_use_case,
)
from ...auth.api.dependencies import require_scope, AuthenticatedContext
from ..use_cases import (
    ListUsersUseCase,
    GetUserUseCase,
    ListRolesUseCase,
    GetRoleUseCase,
    GetPermissionsUseCase,
    ListServiceAccountsUseCase,
    CreateRoleUseCase,
    UpdateRoleUseCase,
    DeleteRoleUseCase,
    AssignRoleToUserUseCase,
    RevokeRoleFromUserUseCase,
)
from ..exceptions import (
    IAMError,
    RoleNotFoundError,
    RoleNameExistsError,
    SystemRoleError,
    RoleInUseError,
    UserNotFoundError,
    RoleAlreadyAssignedError,
    RoleNotAssignedError,
)


router = APIRouter(prefix="/iam", tags=["iam"])


# =============================================================================
# User Endpoints
# =============================================================================

@router.get("/users", response_model=ListUsersResponse)
async def list_users(
    q: Optional[str] = Query(None, description="Search query"),
    role: Optional[UUID] = Query(None, description="Filter by role ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
):
    """
    List users in tenant.

    Returns paginated list of users with membership info.
    Optionally filter by role or search query.
    """
    result = await use_case.execute(
        tenant_id=tenant_id,
        role_id=role,
        search=q,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


@router.get("/users/stats", response_model=SuccessResponse)
async def get_user_stats(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
):
    """
    Get user statistics for tenant.

    Returns counts of active, inactive, and total users.
    """
    stats = await use_case.get_stats(tenant_id=tenant_id)
    return {"success": True, "data": stats}


@router.get("/users/{user_id}", response_model=SuccessResponse)
async def get_user(
    user_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
):
    """
    Get user detail.

    Returns user with their roles.
    """
    result = await use_case.execute(tenant_id=tenant_id, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"User {user_id} not found in tenant",
            }
        )
    return {"success": True, "data": result}


@router.get("/users/{user_id}/roles", response_model=ListRolesResponse)
async def get_user_roles(
    user_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
):
    """
    Get user's roles.

    Returns list of roles assigned to the user.
    """
    result = await use_case.execute(tenant_id=tenant_id, user_id=user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"User {user_id} not found in tenant",
            }
        )
    return {"success": True, "data": result.get("roles", [])}


# =============================================================================
# Role Endpoints
# =============================================================================

@router.get("/roles", response_model=ListRolesResponse)
async def list_roles(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListRolesUseCase = Depends(get_list_roles_use_case),
):
    """
    List roles in tenant.

    Returns all roles (system and custom).
    """
    result = await use_case.execute(tenant_id=tenant_id)
    return {"success": True, "data": result}


@router.get("/roles/{role_id}", response_model=SuccessResponse)
async def get_role(
    role_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetRoleUseCase = Depends(get_get_role_use_case),
):
    """
    Get role detail.

    Returns role with its permissions.
    """
    result = await use_case.execute(tenant_id=tenant_id, role_id=role_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Role {role_id} not found in tenant",
            }
        )
    return {"success": True, "data": result}


@router.get("/roles/{role_id}/permissions", response_model=ListPermissionsResponse)
async def get_role_permissions(
    role_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetRoleUseCase = Depends(get_get_role_use_case),
):
    """
    Get role's permissions.

    Returns list of permissions assigned to the role.
    """
    result = await use_case.execute(tenant_id=tenant_id, role_id=role_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Role {role_id} not found in tenant",
            }
        )
    return {"success": True, "data": result.get("permissions", [])}


@router.post("/roles", response_model=RoleCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: CreateRoleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: CreateRoleUseCase = Depends(get_create_role_use_case),
    _auth: AuthenticatedContext = Depends(require_scope("iam:roles:write")),
):
    """
    Create a new role.

    Creates a custom role in the tenant with optional permissions.
    Requires scope: iam:roles:write
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            permission_ids=request.permission_ids,
        )
        return {"success": True, "data": result}
    except RoleNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message}
        )


@router.put("/roles/{role_id}", response_model=RoleUpdatedResponse)
async def update_role(
    role_id: UUID,
    request: UpdateRoleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: UpdateRoleUseCase = Depends(get_update_role_use_case),
    _auth: AuthenticatedContext = Depends(require_scope("iam:roles:write")),
):
    """
    Update an existing role.

    Updates role name, display name, description, or permissions.
    System roles cannot be modified.
    Requires scope: iam:roles:write
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            role_id=role_id,
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            permission_ids=request.permission_ids,
        )
        return {"success": True, "data": result}
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except SystemRoleError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.message}
        )
    except RoleNameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message}
        )


@router.delete("/roles/{role_id}", response_model=RoleDeletedResponse)
async def delete_role(
    role_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
    use_case: DeleteRoleUseCase = Depends(get_delete_role_use_case),
    _auth: AuthenticatedContext = Depends(require_scope("iam:roles:delete")),
):
    """
    Delete a role.

    Deletes a custom role. System roles and roles assigned to users cannot be deleted.
    Requires scope: iam:roles:delete
    """
    try:
        await use_case.execute(tenant_id=tenant_id, role_id=role_id)
        return {"success": True, "data": {"deleted": True, "role_id": str(role_id)}}
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except SystemRoleError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.message}
        )
    except RoleInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": e.code,
                "message": e.message,
                "user_count": e.user_count,
            }
        )


# =============================================================================
# User-Role Assignment Endpoints
# =============================================================================

@router.post("/users/{user_id}/roles", response_model=RoleAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: UUID,
    request: AssignRoleRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user_id: UUID = Depends(get_current_user_id),
    use_case: AssignRoleToUserUseCase = Depends(get_assign_role_use_case),
    _auth: AuthenticatedContext = Depends(require_scope("iam:users:write")),
):
    """
    Assign a role to a user.

    Assigns the specified role to the user in the current tenant.
    Requires scope: iam:users:write
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=request.role_id,
            assigned_by=current_user_id,
        )
        return {"success": True, "data": result}
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except RoleAlreadyAssignedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message}
        )


@router.delete("/users/{user_id}/roles/{role_id}", response_model=RoleAssignmentResponse)
async def revoke_role_from_user(
    user_id: UUID,
    role_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user_id: UUID = Depends(get_current_user_id),
    use_case: RevokeRoleFromUserUseCase = Depends(get_revoke_role_use_case),
    _auth: AuthenticatedContext = Depends(require_scope("iam:users:write")),
):
    """
    Revoke a role from a user.

    Removes the specified role from the user in the current tenant.
    Requires scope: iam:users:write
    """
    try:
        result = await use_case.execute(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
        )
        return {"success": True, "data": result}
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except RoleNotAssignedError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )


# =============================================================================
# Service Account Endpoints
# =============================================================================

@router.get("/service-accounts", response_model=ListServiceAccountsResponse)
async def list_service_accounts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: ListServiceAccountsUseCase = Depends(get_list_service_accounts_use_case),
):
    """
    List service accounts in tenant.

    Returns paginated list of service accounts.
    """
    result = await use_case.execute(
        tenant_id=tenant_id,
        page=page,
        limit=limit,
    )
    return {"success": True, "data": result}


# =============================================================================
# Permission Endpoints
# =============================================================================

@router.get("/permissions", response_model=ListPermissionsResponse)
async def list_permissions(
    use_case: GetPermissionsUseCase = Depends(get_get_permissions_use_case),
):
    """
    List all available permissions.

    Returns global list of permissions (not tenant-scoped).
    """
    result = await use_case.list_all()
    return {"success": True, "data": result}


@router.get("/permissions/matrix", response_model=PermissionMatrixResponse)
async def get_permission_matrix(
    tenant_id: UUID = Depends(get_current_tenant_id),
    use_case: GetPermissionsUseCase = Depends(get_get_permissions_use_case),
):
    """
    Get permission matrix.

    Returns matrix showing all roles and their permissions.
    """
    result = await use_case.get_matrix(tenant_id=tenant_id)
    return {"success": True, "data": result}
