"""
User Management API Routes
HTTP endpoints for user management (CRUD operations)

Updated to use centralized utilities:
- shared.errors for error handling
- shared.responses for standardized responses
- shared.logging for request logging
"""

from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import UserRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from shared.middleware import get_current_active_user, require_admin, require_admin_or_manager
from typing import Optional
import time

from .dtos import (
    CreateUserRequest,
    UpdateUserRequest,
    ChangePasswordRequest,
    UserResponse,
    UserListResponse
)
from .use_cases.create_user import CreateUserUseCase
from .use_cases.list_users import ListUsersUseCase
from .use_cases.get_user import GetUserUseCase
from .use_cases.update_user import UpdateUserUseCase
from .use_cases.delete_user import DeleteUserUseCase
from .use_cases.change_password import ChangePasswordUseCase


router = APIRouter()

# Initialize request logger (audit logger will be created per-request)
request_logger = RequestLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_user_repository(db: Session = Depends(get_db)):
    """Get user repository instance"""
    from .repositories.user_repo import UserRepository
    return UserRepository(db)


def get_organization_repository(db: Session = Depends(get_db)):
    """Get organization repository instance"""
    from services.organization.repositories.organization_repo import OrganizationRepository
    return OrganizationRepository(db)


def get_audit_log_repository(db: Session = Depends(get_db)):
    """Get audit log repository instance"""
    from services.audit.repositories.audit_log_repo import AuditLogRepository
    return AuditLogRepository(db)


def get_create_audit_log_use_case(audit_repo = Depends(get_audit_log_repository)):
    """Get create audit log use case"""
    from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase
    return CreateAuditLogUseCase(audit_repo)


def get_audit_logger(create_audit_use_case = Depends(get_create_audit_log_use_case)) -> AuditLogger:
    """Get audit logger with database persistence"""
    return AuditLogger(create_audit_log_use_case=create_audit_use_case)


def get_create_user_use_case(
    user_repo = Depends(get_user_repository),
    org_repo = Depends(get_organization_repository)
) -> CreateUserUseCase:
    """Get create user use case"""
    return CreateUserUseCase(user_repo, org_repo)


def get_list_users_use_case(user_repo = Depends(get_user_repository)) -> ListUsersUseCase:
    """Get list users use case"""
    return ListUsersUseCase(user_repo)


def get_get_user_use_case(user_repo = Depends(get_user_repository)) -> GetUserUseCase:
    """Get single user use case"""
    return GetUserUseCase(user_repo)


def get_update_user_use_case(user_repo = Depends(get_user_repository)) -> UpdateUserUseCase:
    """Get update user use case"""
    return UpdateUserUseCase(user_repo)


def get_delete_user_use_case(user_repo = Depends(get_user_repository)) -> DeleteUserUseCase:
    """Get delete user use case"""
    return DeleteUserUseCase(user_repo)


def get_change_password_use_case(
    user_repo = Depends(get_user_repository),
    db: Session = Depends(get_db)
) -> ChangePasswordUseCase:
    """Get change password use case with session repository for revoking sessions (P0-16)"""
    from services.session.repositories.session_repo import SessionRepository
    session_repo = SessionRepository(db)
    return ChangePasswordUseCase(user_repo, session_repo)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get(UserRoutes.LIST, response_model=UserListResponse)
@handle_errors
def list_users(
    http_request: Request,
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    role: Optional[str] = Query(None, description="Filter by role"),
    active_only: bool = Query(False, description="Only show active users"),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List all users with filters

    Permission: Admin (all orgs) or Manager (own org only)
    """
    # If manager, can only see users from own organization
    if current_user["role"] == "manager":
        organization_id = current_user["organization_id"]
    start_time = time.time()

    # Execute use case
    result = use_case.execute(
        organization_id=organization_id,
        role=role,
        active_only=active_only
    )

    # Convert to response with organization names
    user_responses = []
    for user in result["users"]:
        response = UserResponse.model_validate(user)
        # Get organization name
        org_name = use_case.get_user_organization_name(user.id)
        response.organization_name = org_name
        user_responses.append(response)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=UserRoutes.LIST,
        status_code=200,
        duration_ms=duration_ms
    )

    return UserListResponse(
        users=user_responses,
        total=result["total"],
        active=result["active"]
    )


@router.post(UserRoutes.CREATE, response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@handle_errors
def create_user(
    request_body: CreateUserRequest,
    http_request: Request,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin_or_manager)
):
    """
    Create new user

    Permission: Admin or Manager (can only create in own org)
    """
    # If manager, can only create users in own organization
    if current_user["role"] == "manager":
        if request_body.organization_id != current_user["organization_id"]:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager can only create users in their own organization"
            )
    start_time = time.time()

    # Execute use case
    user = use_case.execute(
        username=request_body.username,
        email=request_body.email,
        password=request_body.password,
        full_name=request_body.full_name,
        role=request_body.role,
        organization_id=request_body.organization_id
    )

    # Convert to response
    response = UserResponse.model_validate(user)
    org_name = list_use_case.get_user_organization_name(user.id)
    response.organization_name = org_name

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=UserRoutes.CREATE,
        status_code=201,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="user.create",
        resource_type="user",
        resource_id=user.id,
        details={
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return response


@router.get(UserRoutes.GET.replace("{user_id}", "{user_id:int}"), response_model=UserResponse)
@handle_errors
def get_user(
    user_id: int,
    http_request: Request,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get user by ID

    Permission: Admin (any user) or Manager (own org only) or Self
    """
    # Get target user to check permissions
    target_user = use_case.execute(user_id)

    # Check permissions
    if current_user["role"] != "admin":
        # Manager can view users in own org
        if current_user["role"] == "manager":
            if target_user.organization_id != current_user["organization_id"]:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view users in your organization"
                )
        # Regular user can only view self
        elif current_user["user_id"] != user_id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile"
            )
    start_time = time.time()

    # Execute use case
    user = use_case.execute(user_id)

    # Convert to response
    response = UserResponse.model_validate(user)
    org_name = list_use_case.get_user_organization_name(user.id)
    response.organization_name = org_name

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=UserRoutes.GET.replace("{user_id}", str(user_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    return response


@router.put(UserRoutes.UPDATE.replace("{user_id}", "{user_id:int}"), response_model=UserResponse)
@handle_errors
def update_user(
    user_id: int,
    request_body: UpdateUserRequest,
    http_request: Request,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(get_current_active_user),
    user_repo = Depends(get_user_repository)
):
    """
    Update user

    Permission: Admin (any user) or Manager (own org only) or Self (limited fields)
    """
    # Get target user to check permissions
    target_user = user_repo.find_by_id(user_id)

    if not target_user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    # Check permissions
    if current_user["role"] != "admin":
        # Manager can update users in own org (except role changes)
        if current_user["role"] == "manager":
            if target_user.organization_id != current_user["organization_id"]:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update users in your organization"
                )
            # Manager cannot change roles
            if request_body.role and request_body.role != target_user.role:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager cannot change user roles"
                )
        # Regular user can only update self (limited fields)
        elif current_user["user_id"] != user_id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )
        else:
            # User cannot change role or is_active
            if request_body.role or request_body.is_active is not None:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot change role or active status"
                )
    start_time = time.time()

    # Execute use case
    user = use_case.execute(
        user_id=user_id,
        email=request_body.email,
        full_name=request_body.full_name,
        role=request_body.role,
        is_active=request_body.is_active
    )

    # Convert to response
    response = UserResponse.model_validate(user)
    org_name = list_use_case.get_user_organization_name(user.id)
    response.organization_name = org_name

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="PUT",
        path=UserRoutes.UPDATE.replace("{user_id}", str(user_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="user.update",
        resource_type="user",
        resource_id=user_id,
        details={
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return response


@router.put(UserRoutes.CHANGE_PASSWORD.replace("{user_id}", "{user_id:int}"), response_model=UserResponse)
@handle_errors
def change_password(
    user_id: int,
    request_body: ChangePasswordRequest,
    http_request: Request,
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user password

    Permission: Admin (any user) or Self
    """
    # Check permissions - only admin or self can change password
    if current_user["role"] != "admin" and current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )
    start_time = time.time()

    # Execute use case
    user = use_case.execute(
        user_id=user_id,
        new_password=request_body.new_password
    )

    # Convert to response
    response = UserResponse.model_validate(user)
    org_name = list_use_case.get_user_organization_name(user.id)
    response.organization_name = org_name

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="PUT",
        path=UserRoutes.CHANGE_PASSWORD.replace("{user_id}", str(user_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="user.change_password",
        resource_type="user",
        resource_id=user_id,
        details={
            "username": user.username,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return response


@router.delete(UserRoutes.DELETE.replace("{user_id}", "{user_id:int}"), status_code=status.HTTP_204_NO_CONTENT)
@handle_errors
def delete_user(
    user_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin_or_manager)
):
    """
    Delete user (hard delete - permanent removal)

    Note: To disable/archive user without deleting, use PUT with is_active=false

    Permission: Admin (any user) or Manager (own org only)
    """
    # Get target user to check permissions
    get_use_case = get_get_user_use_case(db)
    user = get_use_case.execute(user_id)

    # Manager can only delete users in own organization
    if current_user["role"] == "manager":
        if user.organization_id != current_user["organization_id"]:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager can only delete users in their own organization"
            )
    start_time = time.time()

    # Execute delete use case
    use_case.execute(user_id)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="DELETE",
        path=UserRoutes.DELETE.replace("{user_id}", str(user_id)),
        status_code=204,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="user.delete",
        resource_type="user",
        resource_id=user_id,
        details={
            "username": user.username,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return None
