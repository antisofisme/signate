"""
Organization API Routes
HTTP endpoints for organization management

Updated to use centralized utilities:
- shared.errors for error handling
- shared.responses for standardized responses
- shared.logging for request logging
"""

from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import OrganizationRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from typing import Optional
import time

from .dtos import (
    CreateOrganizationRequest,
    UpdateOrganizationRequest,
    OrganizationResponse,
    OrganizationListResponse
)
from .use_cases.create_organization import CreateOrganizationUseCase
from .use_cases.list_organizations import ListOrganizationsUseCase
from .use_cases.get_organization import GetOrganizationUseCase
from .use_cases.update_organization import UpdateOrganizationUseCase
from .use_cases.delete_organization import DeleteOrganizationUseCase
from .repositories.organization_repo import OrganizationRepository


router = APIRouter()

# Initialize request logger (audit logger will be created per-request)
request_logger = RequestLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_organization_repository(db: Session = Depends(get_db)) -> OrganizationRepository:
    """Get organization repository instance"""
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


def get_create_org_use_case(
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> CreateOrganizationUseCase:
    """Get create organization use case"""
    return CreateOrganizationUseCase(org_repo)


def get_list_orgs_use_case(
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> ListOrganizationsUseCase:
    """Get list organizations use case"""
    return ListOrganizationsUseCase(org_repo)


def get_get_org_use_case(
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> GetOrganizationUseCase:
    """Get single organization use case"""
    return GetOrganizationUseCase(org_repo)


def get_update_org_use_case(
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> UpdateOrganizationUseCase:
    """Get update organization use case"""
    return UpdateOrganizationUseCase(org_repo)


def get_delete_org_use_case(
    org_repo: OrganizationRepository = Depends(get_organization_repository)
) -> DeleteOrganizationUseCase:
    """Get delete organization use case"""
    return DeleteOrganizationUseCase(org_repo)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get(OrganizationRoutes.LIST, response_model=OrganizationListResponse)
@handle_errors
def list_organizations(
    http_request: Request,
    active_only: bool = Query(False, description="Show all organizations (set true for active only)"),
    use_case: ListOrganizationsUseCase = Depends(get_list_orgs_use_case)
):
    """
    List all organizations

    Permission: Admin only (TODO: Add auth middleware)
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(active_only=active_only)

    # Convert to response with stats
    org_responses = []
    for org in result["organizations"]:
        stats = use_case.get_organization_stats(org.id)
        response = OrganizationResponse.model_validate(org)
        response.user_count = stats["user_count"]
        response.device_count = stats["device_count"]
        org_responses.append(response)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=OrganizationRoutes.LIST,
        status_code=200,
        duration_ms=duration_ms
    )

    return OrganizationListResponse(
        organizations=org_responses,
        total=result["total"],
        active=result["active"]
    )


@router.post(OrganizationRoutes.CREATE, response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
@handle_errors
def create_organization(
    request_body: CreateOrganizationRequest,
    http_request: Request,
    use_case: CreateOrganizationUseCase = Depends(get_create_org_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create new organization

    Permission: Admin only (TODO: Add auth middleware)
    """
    start_time = time.time()

    # Execute use case
    organization = use_case.execute(
        name=request_body.name,
        pin=request_body.organization_pin,
        description=request_body.description,
        address=request_body.address,
        contact_email=request_body.contact_email,
        contact_phone=request_body.contact_phone,
        logo_url=request_body.logo_url
    )

    # Convert to response
    response = OrganizationResponse.model_validate(organization)
    response.user_count = 0
    response.device_count = 0

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=OrganizationRoutes.CREATE,
        status_code=201,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=None,  # TODO: Get from JWT token
        action="organization.create",
        resource_type="organization",
        resource_id=organization.id,
        details={
            "name": organization.name,
            "pin": organization.organization_pin,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return response


@router.get(OrganizationRoutes.GET.replace("{org_id}", "{org_id:int}"), response_model=OrganizationResponse)
@handle_errors
def get_organization(
    org_id: int,
    http_request: Request,
    use_case: GetOrganizationUseCase = Depends(get_get_org_use_case),
    list_use_case: ListOrganizationsUseCase = Depends(get_list_orgs_use_case)
):
    """
    Get organization by ID

    Permission: Admin or Manager of that org (TODO: Add auth middleware)
    """
    start_time = time.time()

    # Execute use case
    organization = use_case.execute(org_id)

    # Get stats
    stats = list_use_case.get_organization_stats(org_id)

    # Convert to response
    response = OrganizationResponse.model_validate(organization)
    response.user_count = stats["user_count"]
    response.device_count = stats["device_count"]

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=OrganizationRoutes.GET.replace("{org_id}", str(org_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    return response


@router.put(OrganizationRoutes.UPDATE.replace("{org_id}", "{org_id:int}"), response_model=OrganizationResponse)
@handle_errors
def update_organization(
    org_id: int,
    request_body: UpdateOrganizationRequest,
    http_request: Request,
    use_case: UpdateOrganizationUseCase = Depends(get_update_org_use_case),
    list_use_case: ListOrganizationsUseCase = Depends(get_list_orgs_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update organization

    Permission: Admin only (TODO: Add auth middleware)
    """
    start_time = time.time()

    # Execute use case
    organization = use_case.execute(
        org_id=org_id,
        name=request_body.name,
        description=request_body.description,
        address=request_body.address,
        contact_email=request_body.contact_email,
        contact_phone=request_body.contact_phone,
        logo_url=request_body.logo_url,
        is_active=request_body.is_active
    )

    # Get stats
    stats = list_use_case.get_organization_stats(org_id)

    # Convert to response
    response = OrganizationResponse.model_validate(organization)
    response.user_count = stats["user_count"]
    response.device_count = stats["device_count"]

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="PUT",
        path=OrganizationRoutes.UPDATE.replace("{org_id}", str(org_id)),
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=None,  # TODO: Get from JWT token
        action="organization.update",
        resource_type="organization",
        resource_id=org_id,
        details={
            "name": organization.name,
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return response


@router.delete(OrganizationRoutes.DELETE.replace("{org_id}", "{org_id:int}"), status_code=status.HTTP_204_NO_CONTENT)
@handle_errors
def delete_organization(
    org_id: int,
    http_request: Request,
    use_case: DeleteOrganizationUseCase = Depends(get_delete_org_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete organization (hard delete - permanent removal)

    Note: To disable/archive organization without deleting, use PUT with is_active=false

    Permission: Admin only (TODO: Add auth middleware)
    """
    start_time = time.time()

    # Execute use case
    success = use_case.execute(org_id)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="DELETE",
        path=OrganizationRoutes.DELETE.replace("{org_id}", str(org_id)),
        status_code=204,
        duration_ms=duration_ms
    )

    # Audit log
    audit_logger.log_action(
        user_id=None,  # TODO: Get from JWT token
        action="organization.delete",
        resource_type="organization",
        resource_id=org_id,
        details={
            "ip_address": http_request.client.host if http_request.client else None
        }
    )

    return None
