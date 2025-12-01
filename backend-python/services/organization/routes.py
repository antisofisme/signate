"""
Organization API Routes
HTTP endpoints for organization management

Updated to use centralized utilities:
- shared.errors for error handling
- shared.responses for standardized responses
- shared.logging for request logging
"""

from fastapi import APIRouter, Depends, Request, status, Query, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import OrganizationRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from shared.middleware import get_current_active_user, require_admin
from typing import Optional
import time

from .dtos import (
    CreateOrganizationRequest,
    UpdateOrganizationRequest,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationQuotaResponse,
    QuotaCheckResponse,
    UpdateOrganizationQuotaRequest,
    UpdatePinRequest,
    RegeneratePinResponse,
)
from .use_cases.create_organization import CreateOrganizationUseCase
from .use_cases.list_organizations import ListOrganizationsUseCase
from .use_cases.get_organization import GetOrganizationUseCase
from .use_cases.update_organization import UpdateOrganizationUseCase
from .use_cases.delete_organization import DeleteOrganizationUseCase
from .use_cases.get_organization_quota import get_organization_quota_use_case
from .repositories.organization_repo import OrganizationRepository
from .domain.quota_service import OrganizationQuotaService


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
    use_case: ListOrganizationsUseCase = Depends(get_list_orgs_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List all organizations

    Permission:
    - SUPER_ADMIN: Can see all organizations
    - ADMIN: Can only see own organization
    - Manager: Can only see own organization
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(active_only=active_only)

    # Multi-tenancy: Non-SUPER_ADMIN users can only see their own organization
    user_role = current_user["role"].lower() if current_user.get("role") else ""
    if user_role != "super_admin":
        # Filter to only show user's own organization
        result["organizations"] = [
            org for org in result["organizations"]
            if org.id == current_user["organization_id"]
        ]
        result["total"] = len(result["organizations"])
        result["active"] = len([org for org in result["organizations"] if org.is_active])

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
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    """
    Create new organization

    Permission: Admin only
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
        user_id=current_user["user_id"],
        action="organization.create",
        resource_type="organization",
        resource_id=organization.id,
        details={
            "name": organization.name,
            # REMOVED: organization_pin from audit logs (security fix, No-PIN flow)
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=organization.id
    )

    return response


@router.get(OrganizationRoutes.GET.replace("{org_id}", "{org_id:int}"), response_model=OrganizationResponse)
@handle_errors
def get_organization(
    org_id: int,
    http_request: Request,
    use_case: GetOrganizationUseCase = Depends(get_get_org_use_case),
    list_use_case: ListOrganizationsUseCase = Depends(get_list_orgs_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get organization by ID

    Permission:
    - SUPER_ADMIN: Can view any organization
    - Others: Can only view own organization
    """
    # Multi-tenancy: Non-SUPER_ADMIN can only view their own organization
    user_role = current_user["role"].lower() if current_user.get("role") else ""
    if user_role != "super_admin":
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own organization"
            )

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
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    """
    Update organization

    Permission: Admin only
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
        user_id=current_user["user_id"],
        action="organization.update",
        resource_type="organization",
        resource_id=org_id,
        details={
            "name": organization.name,
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=org_id
    )

    return response


@router.delete(OrganizationRoutes.DELETE.replace("{org_id}", "{org_id:int}"), status_code=status.HTTP_204_NO_CONTENT)
@handle_errors
def delete_organization(
    org_id: int,
    http_request: Request,
    use_case: DeleteOrganizationUseCase = Depends(get_delete_org_use_case),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    """
    Delete organization (hard delete - permanent removal)

    Note: To disable/archive organization without deleting, use PUT with is_active=false

    Permission: Admin only
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
        user_id=current_user["user_id"],
        action="organization.delete",
        resource_type="organization",
        resource_id=org_id,
        details={
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=org_id
    )

    return None


# =============================================================================
# QUOTA ENDPOINTS
# =============================================================================

@router.get("/organizations/{org_id:int}/quota", response_model=OrganizationQuotaResponse)
@handle_errors
def get_organization_quota(
    org_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get organization quota status

    Shows current usage and limits for:
    - Devices
    - Users
    - Content (items and storage)
    - Playlists

    Permission:
    - SUPER_ADMIN: Can view any organization's quota
    - Others: Can only view own organization's quota
    """
    # Multi-tenancy: Non-SUPER_ADMIN can only view their own organization's quota
    user_role = current_user["role"].lower() if current_user.get("role") else ""
    if user_role != "super_admin":
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own organization's quota"
            )
    
    start_time = time.time()
    
    # Get quota status
    quota_response = get_organization_quota_use_case(org_id, db)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log request
    request_logger.log_request(
        method="GET",
        path=f"/organizations/{org_id}/quota",
        status_code=200,
        duration_ms=duration_ms
    )
    
    return quota_response


@router.get("/api/v1/organizations/{org_id:int}/quota/check/device", response_model=QuotaCheckResponse)
@handle_errors
def check_device_quota(
    org_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Check if organization can add more devices
    
    Permission: Manager/Admin
    """
    # Check permissions
    if current_user["role"] not in ["admin", "super_admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can check device quota"
        )
    
    if current_user["role"] == "manager" and current_user["organization_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check your own organization's quota"
        )
    
    # Check quota
    quota_service = OrganizationQuotaService(db)
    result = quota_service.check_device_quota(org_id)
    
    return QuotaCheckResponse(**result)


@router.get("/api/v1/organizations/{org_id:int}/quota/check/user", response_model=QuotaCheckResponse)
@handle_errors
def check_user_quota(
    org_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Check if organization can add more users
    
    Permission: Manager/Admin
    """
    # Check permissions
    if current_user["role"] not in ["admin", "super_admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can check user quota"
        )
    
    if current_user["role"] == "manager" and current_user["organization_id"] != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check your own organization's quota"
        )
    
    # Check quota
    quota_service = OrganizationQuotaService(db)
    result = quota_service.check_user_quota(org_id)
    
    return QuotaCheckResponse(**result)


@router.get("/api/v1/organizations/{org_id:int}/quota/check/content", response_model=QuotaCheckResponse)
@handle_errors
def check_content_quota(
    org_id: int,
    file_size_bytes: int = Query(..., description="File size in bytes to check"),
    http_request: Request = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Check if organization can add content with specified size

    Permission:
    - SUPER_ADMIN: Can check any organization
    - Others: Can only check own organization
    """
    # Multi-tenancy: Non-SUPER_ADMIN can only check their own organization's quota
    user_role = current_user["role"].lower() if current_user.get("role") else ""
    if user_role != "super_admin":
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only check your own organization's quota"
            )
    
    # Check quota
    quota_service = OrganizationQuotaService(db)
    result = quota_service.check_content_quota(org_id, file_size_bytes)
    
    return QuotaCheckResponse(**result)


@router.put("/api/v1/organizations/{org_id:int}/quota", response_model=OrganizationQuotaResponse)
@handle_errors
def update_organization_quota(
    org_id: int,
    request_body: UpdateOrganizationQuotaRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    """
    Update organization quota limits

    Permission: Admin only
    """
    from services.auth.repositories.models import OrganizationModel

    start_time = time.time()

    # Get organization with row lock to prevent race conditions
    # with_for_update() ensures atomic read-modify-write operation
    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == org_id
    ).with_for_update().first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )
    
    # Update limits
    if request_body.max_devices is not None:
        org.max_devices = request_body.max_devices
    
    if request_body.max_users is not None:
        org.max_users = request_body.max_users
    
    # Update settings JSON for extended quotas
    settings = org.settings or {}
    
    if request_body.max_content_size_gb is not None:
        settings['max_content_size_gb'] = request_body.max_content_size_gb
        
    if request_body.max_content_items is not None:
        settings['max_content_items'] = request_body.max_content_items
        
    if request_body.max_playlists is not None:
        settings['max_playlists'] = request_body.max_playlists
    
    org.settings = settings
    db.commit()
    
    # Get updated quota status
    quota_response = get_organization_quota_use_case(org_id, db)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log request
    request_logger.log_request(
        method="PUT",
        path=f"/organizations/{org_id}/quota",
        status_code=200,
        duration_ms=duration_ms
    )
    
    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="organization.update_quota",
        resource_type="organization",
        resource_id=org_id,
        details={
            "max_devices": request_body.max_devices,
            "max_users": request_body.max_users,
            "max_content_size_gb": request_body.max_content_size_gb,
            "max_content_items": request_body.max_content_items,
            "max_playlists": request_body.max_playlists,
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=org_id
    )

    return quota_response


# =============================================================================
# PIN MANAGEMENT ENDPOINTS
# =============================================================================

@router.post(f"{OrganizationRoutes.BASE}/{{org_id:int}}/pin/regenerate", response_model=RegeneratePinResponse)
@handle_errors
def regenerate_organization_pin(
    org_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    """
    Regenerate organization PIN with a new random 6-digit PIN

    Permission: Admin only
    """
    import random
    from services.auth.repositories.models import OrganizationModel

    start_time = time.time()

    # Get organization
    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == org_id
    ).with_for_update().first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )

    # Multi-tenancy: Non-SUPER_ADMIN can only regenerate PIN for their own organization
    user_role = current_user["role"].lower() if current_user.get("role") else ""
    if user_role != "super_admin":
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage PIN for your own organization"
            )

    # Generate new 6-digit PIN
    new_pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    # Update organization
    org.pin = new_pin
    db.commit()

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=f"/organizations/{org_id}/pin/regenerate",
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log (don't log the actual PIN for security)
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="organization.pin_regenerate",
        resource_type="organization",
        resource_id=org_id,
        details={
            "organization_name": org.name,
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=org_id
    )

    return RegeneratePinResponse(
        organization_id=org_id,
        new_pin=new_pin,
        message="PIN regenerated successfully"
    )


@router.put(f"{OrganizationRoutes.BASE}/{{org_id:int}}/pin", response_model=RegeneratePinResponse)
@handle_errors
def update_organization_pin(
    org_id: int,
    request_body: UpdatePinRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    current_user: dict = Depends(require_admin)
):
    """
    Update organization PIN with a custom PIN

    Permission: Admin only
    """
    from services.auth.repositories.models import OrganizationModel

    start_time = time.time()

    # Get organization
    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == org_id
    ).with_for_update().first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found"
        )

    # Multi-tenancy: Non-SUPER_ADMIN can only update PIN for their own organization
    user_role = current_user["role"].lower() if current_user.get("role") else ""
    if user_role != "super_admin":
        if current_user["organization_id"] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage PIN for your own organization"
            )

    # Update organization PIN
    org.pin = request_body.new_pin
    db.commit()

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="PUT",
        path=f"/organizations/{org_id}/pin",
        status_code=200,
        duration_ms=duration_ms
    )

    # Audit log (don't log the actual PIN for security)
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="organization.pin_update",
        resource_type="organization",
        resource_id=org_id,
        details={
            "organization_name": org.name,
            "ip_address": http_request.client.host if http_request.client else None
        },
        organization_id=org_id
    )

    return RegeneratePinResponse(
        organization_id=org_id,
        new_pin=request_body.new_pin,
        message="PIN updated successfully"
    )
