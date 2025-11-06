"""
Tag API Routes
HTTP endpoints for tag management
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from shared.database import get_db
from shared.api_routes import TagRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from shared.middleware import get_current_active_user
import time

from .dtos import (
    CreateTagRequest,
    UpdateTagRequest,
    TagResponse,
    TagListResponse,
    TagDetailResponse,
    TagWithUsageDetailResponse,
    TagDeleteResponse,
    TagUsageResponse,
)
from .use_cases import (
    CreateTagUseCase,
    ListTagsUseCase,
    GetTagUseCase,
    UpdateTagUseCase,
    DeleteTagUseCase,
)
from .repositories.tag_repo import TagRepository


router = APIRouter()

# Initialize loggers
request_logger = RequestLogger()


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_tag_repository(db: Session = Depends(get_db)) -> TagRepository:
    """Get tag repository instance"""
    return TagRepository(db)


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


def get_create_tag_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> CreateTagUseCase:
    """Get create tag use case instance"""
    return CreateTagUseCase(tag_repo)


def get_list_tags_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> ListTagsUseCase:
    """Get list tags use case instance"""
    return ListTagsUseCase(tag_repo)


def get_get_tag_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> GetTagUseCase:
    """Get tag use case instance"""
    return GetTagUseCase(tag_repo)


def get_update_tag_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> UpdateTagUseCase:
    """Get update tag use case instance"""
    return UpdateTagUseCase(tag_repo)


def get_delete_tag_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> DeleteTagUseCase:
    """Get delete tag use case instance"""
    return DeleteTagUseCase(tag_repo)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    TagRoutes.CREATE,
    response_model=TagDetailResponse,
    status_code=status.HTTP_201_CREATED
)
@handle_errors
def create_tag(
    request_body: CreateTagRequest,
    use_case: CreateTagUseCase = Depends(get_create_tag_use_case),
    current_user: dict = Depends(get_current_active_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create a new tag

    Requires authentication. Tag name must be unique within organization.
    """
    start_time = time.time()

    # Execute use case
    tag = use_case.execute(
        tag_name=request_body.tag_name,
        organization_id=current_user["organization_id"],
        description=request_body.description,
        color=request_body.color,
    )

    # Convert to response
    tag_response = TagResponse.model_validate(tag)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=TagRoutes.CREATE,
        status_code=201,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="tag.create",
        resource_type="tag",
        resource_id=tag.id,
        details={"tag_name": tag.tag_name, "color": tag.color},
        organization_id=current_user["organization_id"]
    )

    return {
        "success": True,
        "data": tag_response
    }


@router.get(
    TagRoutes.LIST,
    response_model=TagListResponse
)
@handle_errors
def list_tags(
    sort_by: str = Query(default="newest", description="Sort order: newest, oldest, name_asc, name_desc"),
    use_case: ListTagsUseCase = Depends(get_list_tags_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List all tags for current organization

    Requires authentication. Supports sorting by creation date or name.
    """
    start_time = time.time()

    # Execute use case
    tags = use_case.execute(
        organization_id=current_user["organization_id"],
        sort_by=sort_by
    )

    # Convert to response
    tag_responses = [TagResponse.model_validate(tag) for tag in tags]

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=TagRoutes.LIST,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    return {
        "success": True,
        "data": tag_responses,
        "total": len(tag_responses)
    }


@router.get(
    TagRoutes.GET,
    response_model=TagDetailResponse
)
@handle_errors
def get_tag(
    tag_id: int,
    use_case: GetTagUseCase = Depends(get_get_tag_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a single tag by ID

    Requires authentication. Returns 404 if tag not found or doesn't belong to organization.
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(
        tag_id=tag_id,
        organization_id=current_user["organization_id"],
        include_usage=False
    )

    # Convert to response
    tag_response = TagResponse.model_validate(result["tag"])

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=TagRoutes.GET,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    return {
        "success": True,
        "data": tag_response
    }


@router.get(
    TagRoutes.USAGE,
    response_model=TagWithUsageDetailResponse
)
@handle_errors
def get_tag_usage(
    tag_id: int,
    use_case: GetTagUseCase = Depends(get_get_tag_use_case),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get tag with usage statistics

    Returns tag info plus counts of devices and content using this tag.
    """
    start_time = time.time()

    # Execute use case with usage stats
    result = use_case.execute(
        tag_id=tag_id,
        organization_id=current_user["organization_id"],
        include_usage=True
    )

    # Convert to response
    tag_response = TagResponse.model_validate(result["tag"])
    usage_response = TagUsageResponse(**result["usage"])

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=TagRoutes.USAGE,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    return {
        "success": True,
        "data": {
            "tag": tag_response,
            "usage": usage_response
        }
    }


@router.put(
    TagRoutes.UPDATE,
    response_model=TagDetailResponse
)
@handle_errors
def update_tag(
    tag_id: int,
    request_body: UpdateTagRequest,
    use_case: UpdateTagUseCase = Depends(get_update_tag_use_case),
    current_user: dict = Depends(get_current_active_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update an existing tag

    Requires authentication. Can update tag_name, description, and/or color.
    """
    start_time = time.time()

    # Execute use case
    tag = use_case.execute(
        tag_id=tag_id,
        organization_id=current_user["organization_id"],
        tag_name=request_body.tag_name,
        description=request_body.description,
        color=request_body.color,
    )

    # Convert to response
    tag_response = TagResponse.model_validate(tag)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="PUT",
        path=TagRoutes.UPDATE,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="tag.update",
        resource_type="tag",
        resource_id=tag.id,
        details={
            "tag_name": request_body.tag_name,
            "description": request_body.description,
            "color": request_body.color
        },
        organization_id=current_user["organization_id"]
    )

    return {
        "success": True,
        "data": tag_response
    }


@router.delete(
    TagRoutes.DELETE,
    response_model=TagDeleteResponse
)
@handle_errors
def delete_tag(
    tag_id: int,
    force: bool = Query(default=False, description="Force delete even if tag is in use"),
    use_case: DeleteTagUseCase = Depends(get_delete_tag_use_case),
    current_user: dict = Depends(get_current_active_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete a tag

    Requires authentication. By default, fails if tag is in use.
    Use force=true to delete regardless of usage.
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(
        tag_id=tag_id,
        organization_id=current_user["organization_id"],
        force=force
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="DELETE",
        path=TagRoutes.DELETE,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="tag.delete",
        resource_type="tag",
        resource_id=tag_id,
        details={"force": force},
        organization_id=current_user["organization_id"]
    )

    return {
        "success": True,
        "message": result["message"]
    }
