"""
Session API Routes
HTTP endpoints for session management
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from typing import Optional, List
from shared.database import get_db
from shared.api_routes import SessionRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.auth import get_current_user, require_admin, require_super_admin, CurrentUser, is_super_admin
from shared.pagination import PaginationParams
from shared.middleware import require_permission

from .dtos import (
    SessionResponse, SessionListResponse, SessionStatsResponse,
    SessionRevokeResponse, SessionFilterParams, AllSessionResponse,
    AllSessionsListResponse
)
from .repositories.session_repo import SessionRepository
from .use_cases.get_sessions import GetSessionsUseCase
from .use_cases.revoke_session import RevokeSessionUseCase


router = APIRouter()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_session_repository(db: Session = Depends(get_db)) -> SessionRepository:
    """Get session repository instance"""
    return SessionRepository(db)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(SessionRoutes.LIST, response_model=SessionListResponse)
@handle_errors
def list_sessions(
    include_revoked: bool = Query(False, description="Include revoked sessions"),
    include_expired: bool = Query(False, description="Include expired sessions"),
    current_user: CurrentUser = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Get current user's sessions

    Returns all sessions for authenticated user with filtering
    """
    use_case = GetSessionsUseCase(session_repo)
    result = use_case.get_user_sessions(
        user_id=current_user.id,
        include_revoked=include_revoked,
        include_expired=include_expired
    )

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in result["sessions"]],
        total=result["total"],
        active=result["active"],
        expired=result["expired"],
        revoked=result["revoked"]
    )


@router.get(SessionRoutes.ACTIVE, response_model=List[SessionResponse])
@handle_errors
def get_active_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Get only active sessions for current user"""
    use_case = GetSessionsUseCase(session_repo)
    sessions = use_case.get_active_sessions(current_user.id)

    return [SessionResponse.model_validate(s) for s in sessions]


@router.get(SessionRoutes.STATS, response_model=SessionStatsResponse)
@handle_errors
def get_session_stats(
    current_user: CurrentUser = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """Get session statistics for current user"""
    use_case = GetSessionsUseCase(session_repo)
    stats = use_case.get_session_stats(user_id=current_user.id)

    return SessionStatsResponse(**stats)


@router.delete(SessionRoutes.REVOKE, response_model=SessionRevokeResponse)
@handle_errors
def revoke_session(
    session_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Revoke specific session (logout from specific device)

    Users can only revoke their own sessions
    """
    from services.session.repositories.models import UserSession

    # Verify session belongs to current user
    session = session_repo.db.query(UserSession).filter_by(id=session_id).first()

    if not session or session.user_id != current_user.id:
        from shared.errors import AuthorizationError
        raise AuthorizationError(message="Access denied to this session")

    use_case = RevokeSessionUseCase(session_repo)
    result = use_case.revoke_by_id(session_id)

    return SessionRevokeResponse(**result)


@router.post(SessionRoutes.REVOKE_ALL, response_model=SessionRevokeResponse)
@handle_errors
def revoke_all_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Revoke all sessions for current user (logout from all devices)

    Useful for security: logout from all devices if account compromised
    """
    use_case = RevokeSessionUseCase(session_repo)
    result = use_case.revoke_all_user_sessions(current_user.id)

    return SessionRevokeResponse(**result)


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.get(SessionRoutes.BY_USER, response_model=SessionListResponse)
@handle_errors
def get_user_sessions_admin(
    user_id: int,
    include_revoked: bool = Query(False),
    include_expired: bool = Query(False),
    current_user: CurrentUser = Depends(require_admin),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Admin: Get sessions for any user

    Requires admin role
    """
    use_case = GetSessionsUseCase(session_repo)
    result = use_case.get_user_sessions(
        user_id=user_id,
        include_revoked=include_revoked,
        include_expired=include_expired
    )

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in result["sessions"]],
        total=result["total"],
        active=result["active"],
        expired=result["expired"],
        revoked=result["revoked"]
    )


@router.get(SessionRoutes.BY_IP, response_model=List[SessionResponse])
@handle_errors
def get_sessions_by_ip_admin(
    ip_address: str,
    pagination: PaginationParams = Depends(PaginationParams.as_query),
    current_user: CurrentUser = Depends(require_admin),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Admin: Get sessions by IP address

    Useful for security monitoring and abuse detection
    """
    use_case = GetSessionsUseCase(session_repo)
    sessions = use_case.get_sessions_by_ip(ip_address, pagination.limit)

    return [SessionResponse.model_validate(s) for s in sessions]


@router.delete("/api/v1/sessions/admin/{session_id}", response_model=SessionRevokeResponse)
@handle_errors
def revoke_session_admin(
    session_id: int,
    current_user: CurrentUser = Depends(require_admin),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Admin: Revoke any user's session

    Requires admin role
    """
    use_case = RevokeSessionUseCase(session_repo)
    result = use_case.revoke_by_id(session_id)

    return SessionRevokeResponse(**result)


@router.post("/api/v1/sessions/admin/user/{user_id}/revoke-all", response_model=SessionRevokeResponse)
@handle_errors
def revoke_all_user_sessions_admin(
    user_id: int,
    current_user: CurrentUser = Depends(require_admin),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Admin: Revoke all sessions for any user

    Useful for security actions (e.g., account compromised)
    """
    use_case = RevokeSessionUseCase(session_repo)
    result = use_case.revoke_all_user_sessions(user_id)

    return SessionRevokeResponse(**result)


@router.post("/api/v1/sessions/admin/cleanup")
@handle_errors
def cleanup_old_sessions(
    days_old: int = Query(7, ge=1, le=30, description="Delete sessions older than X days"),
    current_user: CurrentUser = Depends(require_super_admin),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Admin: Clean up old sessions (expired and revoked)

    Requires super admin role.
    Deletes sessions that are expired or revoked and older than specified days.
    """
    result = session_repo.cleanup_old_sessions(days_old=days_old)

    return success_response(
        data={
            "message": f"Cleaned up {result['total_deleted']} old sessions",
            "expired_deleted": result["expired_deleted"],
            "revoked_deleted": result["revoked_deleted"],
            "total_deleted": result["total_deleted"],
            "cutoff_date": result["cutoff_date"]
        }
    )


@router.get(SessionRoutes.ALL_ACTIVE)
@handle_errors
async def get_all_active_sessions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    current_user: dict = Depends(require_permission("sessions", "read")),
    session_repo: SessionRepository = Depends(get_session_repository)
):
    """
    Get all active sessions with user and organization info (multi-tenancy)

    Permission required: sessions:read

    - Super Admin: sees all sessions from all organizations
    - Users with sessions:read permission: sees sessions from their organization only
    """
    # Check if super admin (can see all organizations)
    user_role = current_user.get("role", "").upper()

    if user_role == "SUPER_ADMIN":
        # Super Admin sees all sessions from all organizations
        sessions, total = session_repo.get_all_active_sessions(
            organization_id=None,
            skip=skip,
            limit=limit
        )
    else:
        # Other users with sessions:read permission see their organization only
        sessions, total = session_repo.get_all_active_sessions(
            organization_id=current_user.get("organization_id"),
            skip=skip,
            limit=limit
        )

    return success_response(
        data=AllSessionsListResponse(
            items=[AllSessionResponse(**s) for s in sessions],
            total=total,
            skip=skip,
            limit=limit
        ).model_dump()
    )
