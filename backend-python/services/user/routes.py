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

# Initialize loggers
request_logger = RequestLogger()
audit_logger = AuditLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_create_user_use_case(db: Session = Depends(get_db)) -> CreateUserUseCase:
    """Get create user use case"""
    return CreateUserUseCase(db)


def get_list_users_use_case(db: Session = Depends(get_db)) -> ListUsersUseCase:
    """Get list users use case"""
    return ListUsersUseCase(db)


def get_get_user_use_case(db: Session = Depends(get_db)) -> GetUserUseCase:
    """Get single user use case"""
    return GetUserUseCase(db)


def get_update_user_use_case(db: Session = Depends(get_db)) -> UpdateUserUseCase:
    """Get update user use case"""
    return UpdateUserUseCase(db)


def get_delete_user_use_case(db: Session = Depends(get_db)) -> DeleteUserUseCase:
    """Get delete user use case"""
    return DeleteUserUseCase(db)


def get_change_password_use_case(db: Session = Depends(get_db)) -> ChangePasswordUseCase:
    """Get change password use case"""
    return ChangePasswordUseCase(db)


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
    use_case: ListUsersUseCase = Depends(get_list_users_use_case)
):
    """
    List all users with filters

    Permission: Admin (all orgs) or Manager (own org only) - TODO: Add auth middleware
    """
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
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case)
):
    """
    Create new user

    Permission: Admin or Manager (can only create in own org) - TODO: Add auth middleware
    """
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
        user_id=None,  # TODO: Get from JWT token
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

    return success_response(
        data=response,
        message=f"User '{user.username}' berhasil dibuat"
    )


@router.get(UserRoutes.GET.replace("{user_id}", "{user_id:int}"), response_model=UserResponse)
@handle_errors
def get_user(
    user_id: int,
    http_request: Request,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case)
):
    """
    Get user by ID

    Permission: Admin (any user) or Manager (own org only) or Self - TODO: Add auth middleware
    """
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
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case)
):
    """
    Update user

    Permission: Admin (any user) or Manager (own org only) or Self (limited fields) - TODO: Add auth middleware
    """
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
        user_id=None,  # TODO: Get from JWT token
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

    return success_response(
        data=response,
        message=f"User '{user.username}' berhasil diupdate"
    )


@router.put(UserRoutes.CHANGE_PASSWORD.replace("{user_id}", "{user_id:int}"), response_model=UserResponse)
@handle_errors
def change_password(
    user_id: int,
    request_body: ChangePasswordRequest,
    http_request: Request,
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case),
    list_use_case: ListUsersUseCase = Depends(get_list_users_use_case)
):
    """
    Change user password

    Permission: Admin (any user) or Self - TODO: Add auth middleware
    """
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
        user_id=None,  # TODO: Get from JWT token
        action="user.change_password",
        resource_type="user",
        resource_id=user_id,
        details={
            "username": user.username,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return success_response(
        data=response,
        message=f"Password untuk user '{user.username}' berhasil diubah"
    )


@router.delete(UserRoutes.DELETE.replace("{user_id}", "{user_id:int}"), status_code=status.HTTP_204_NO_CONTENT)
@handle_errors
def delete_user(
    user_id: int,
    http_request: Request,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case)
):
    """
    Delete user (soft delete)

    Permission: Admin (any user) or Manager (own org only) - TODO: Add auth middleware
    """
    start_time = time.time()

    # Execute use case
    user = use_case.execute(user_id)

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
        user_id=None,  # TODO: Get from JWT token
        action="user.delete",
        resource_type="user",
        resource_id=user_id,
        details={
            "username": user.username,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return None
