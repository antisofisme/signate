"""
Audit Log API Routes
HTTP endpoints for viewing audit trail
"""

from fastapi import APIRouter, Depends, Request, Query, HTTPException, status
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import AuditRoutes
from shared.errors import handle_errors
from shared.logging import RequestLogger
from shared.middleware import get_current_active_user, require_admin  # P0-5: Admin only access
from shared.pagination import PaginationParams
from typing import Optional
from datetime import datetime
import time
import math

from .dtos import AuditLogResponse, AuditLogListResponse
from .use_cases.list_audit_logs import ListAuditLogsUseCase
from .use_cases.get_audit_log import GetAuditLogUseCase


router = APIRouter()

# Initialize loggers
request_logger = RequestLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_audit_log_repository(db: Session = Depends(get_db)):
    """Get audit log repository instance"""
    from .repositories.audit_log_repo import AuditLogRepository
    return AuditLogRepository(db)


def get_user_repository(db: Session = Depends(get_db)):
    """Get user repository for username lookup"""
    from services.user.repositories.user_repo import UserRepository
    return UserRepository(db)


def get_organization_repository(db: Session = Depends(get_db)):
    """Get organization repository for org name lookup"""
    from services.organization.repositories.organization_repo import OrganizationRepository
    return OrganizationRepository(db)


def get_list_audit_logs_use_case(
    audit_log_repo = Depends(get_audit_log_repository)
) -> ListAuditLogsUseCase:
    """Get list audit logs use case"""
    return ListAuditLogsUseCase(audit_log_repo)


def get_get_audit_log_use_case(
    audit_log_repo = Depends(get_audit_log_repository)
) -> GetAuditLogUseCase:
    """Get single audit log use case"""
    return GetAuditLogUseCase(audit_log_repo)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get(AuditRoutes.LIST, response_model=AuditLogListResponse)
@handle_errors
def list_audit_logs(
    http_request: Request,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[int] = Query(None, description="Filter by resource ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter until date"),
    pagination: PaginationParams = Depends(PaginationParams.as_query),
    use_case: ListAuditLogsUseCase = Depends(get_list_audit_logs_use_case),
    user_repo = Depends(get_user_repository),
    org_repo = Depends(get_organization_repository),
    current_user: dict = Depends(require_admin)  # P0-5: Admin only access
):
    """
    List audit logs with filters and pagination

    Permission: Admin or Super Admin only (P0-5 security fix)
    Audit logs are sensitive security data and should not be accessible to managers/viewers
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit,
        offset=pagination.skip
    )

    # OPTIMIZATION: Batch fetch users and organizations to prevent N+1 queries
    # Instead of 1 + N*2 queries, we now do 1 + 2 queries (logs + users + orgs)
    logs = result["logs"]

    # Collect unique IDs
    user_ids = list({log.user_id for log in logs if log.user_id})
    org_ids = list({log.organization_id for log in logs if log.organization_id})

    # Batch fetch (2 queries total instead of N*2)
    users_map = user_repo.find_by_ids(user_ids) if user_ids else {}
    orgs_map = org_repo.find_by_ids(org_ids) if org_ids else {}

    # Convert to response and enrich from lookup dictionaries
    log_responses = []
    for log in logs:
        response = AuditLogResponse.model_validate(log)

        # Enrich with username from pre-fetched map
        if log.user_id and log.user_id in users_map:
            response.username = users_map[log.user_id].username

        # Enrich with organization name from pre-fetched map
        if log.organization_id and log.organization_id in orgs_map:
            response.organization_name = orgs_map[log.organization_id].name

        log_responses.append(response)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=AuditRoutes.LIST,
        status_code=200,
        duration_ms=duration_ms
    )

    # Calculate pagination info
    per_page = result["limit"]
    page = (result["offset"] // per_page) + 1 if per_page > 0 else 1
    total_pages = math.ceil(result["total"] / per_page) if per_page > 0 else 0

    return AuditLogListResponse(
        logs=log_responses,
        total=result["total"],
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get(AuditRoutes.GET.replace("{log_id}", "{log_id:int}"), response_model=AuditLogResponse)
@handle_errors
def get_audit_log(
    log_id: int,
    http_request: Request,
    use_case: GetAuditLogUseCase = Depends(get_get_audit_log_use_case),
    user_repo = Depends(get_user_repository),
    org_repo = Depends(get_organization_repository),
    current_user: dict = Depends(require_admin)  # P0-5: Admin only access
):
    """
    Get single audit log by ID

    Permission: Admin or Super Admin only (P0-5 security fix)
    Audit logs are sensitive security data and should not be accessible to managers/viewers
    """
    start_time = time.time()

    # Execute use case
    audit_log = use_case.execute(log_id)

    # Convert to response
    response = AuditLogResponse.model_validate(audit_log)

    # Enrich with username
    if audit_log.user_id:
        user = user_repo.find_by_id(audit_log.user_id)
        response.username = user.username if user else None

    # Enrich with organization name
    if audit_log.organization_id:
        org = org_repo.find_by_id(audit_log.organization_id)
        response.organization_name = org.name if org else None

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=AuditRoutes.GET.replace("{log_id}", str(log_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    return response
