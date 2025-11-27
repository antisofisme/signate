"""
Tag API Routes
HTTP endpoints for tag management
"""

from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.orm import Session
from typing import List
from shared.database import get_db
from shared.api_routes import TagRoutes
from shared.errors import handle_errors
from shared.responses import success_response
from shared.logging import RequestLogger, AuditLogger
from shared.middleware import get_current_active_user, require_permission
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
    AssignTagRequest,
    AssignTagToContentsRequest,
    UnassignTagRequest,
    UnassignTagFromContentsRequest,
    TagAssignmentResponse,
    BulkTagAssignmentResponse,
    BulkTagUnassignmentResponse,
    ContentTagsResponse,
)
from .use_cases import (
    CreateTagUseCase,
    ListTagsUseCase,
    GetTagUseCase,
    UpdateTagUseCase,
    DeleteTagUseCase,
    AssignTagToContentUseCase,
    AssignTagToContentsUseCase,
    UnassignTagFromContentUseCase,
    UnassignTagFromContentsUseCase,
    GetContentTagsUseCase,
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


def get_assign_tag_to_content_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> AssignTagToContentUseCase:
    """Get assign tag to content use case instance"""
    return AssignTagToContentUseCase(tag_repo)


def get_assign_tag_to_contents_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> AssignTagToContentsUseCase:
    """Get bulk assign tag to contents use case instance"""
    return AssignTagToContentsUseCase(tag_repo)


def get_unassign_tag_from_content_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> UnassignTagFromContentUseCase:
    """Get unassign tag from content use case instance"""
    return UnassignTagFromContentUseCase(tag_repo)


def get_unassign_tag_from_contents_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> UnassignTagFromContentsUseCase:
    """Get bulk unassign tag from contents use case instance"""
    return UnassignTagFromContentsUseCase(tag_repo)


def get_get_content_tags_use_case(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> GetContentTagsUseCase:
    """Get content tags use case instance"""
    return GetContentTagsUseCase(tag_repo)


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
    http_request: Request,
    use_case: CreateTagUseCase = Depends(get_create_tag_use_case),
    current_user: dict = Depends(require_permission("tags", "create")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create a new tag

    Requires 'tags:create' permission. Tag name must be unique within organization.
    """
    start_time = time.time()

    # Execute use case with audit tracking
    tag = use_case.execute(
        tag_name=request_body.tag_name,
        organization_id=current_user["organization_id"],
        description=request_body.description,
        color=request_body.color,
        created_by_id=current_user["user_id"],
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
        ip_address=http_request.client.host if http_request.client else None,
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
    current_user: dict = Depends(require_permission("tags", "read"))
):
    """
    List all tags for current organization

    Requires 'tags:read' permission. Supports sorting by creation date or name.
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
    current_user: dict = Depends(require_permission("tags", "read"))
):
    """
    Get a single tag by ID

    Requires 'tags:read' permission. Returns 404 if tag not found or doesn't belong to organization.
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
    current_user: dict = Depends(require_permission("tags", "read"))
):
    """
    Get tag with usage statistics

    Requires 'tags:read' permission. Returns tag info plus counts of devices and content using this tag.
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
    http_request: Request,
    use_case: UpdateTagUseCase = Depends(get_update_tag_use_case),
    current_user: dict = Depends(require_permission("tags", "update")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update an existing tag

    Requires 'tags:update' permission. Can update tag_name, description, and/or color.
    """
    start_time = time.time()

    # Execute use case with audit tracking
    tag = use_case.execute(
        tag_id=tag_id,
        organization_id=current_user["organization_id"],
        tag_name=request_body.tag_name,
        description=request_body.description,
        color=request_body.color,
        updated_by_id=current_user["user_id"],
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
        ip_address=http_request.client.host if http_request.client else None,
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
    http_request: Request,
    force: bool = Query(default=False, description="Force delete even if tag is in use"),
    use_case: DeleteTagUseCase = Depends(get_delete_tag_use_case),
    current_user: dict = Depends(require_permission("tags", "delete")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete a tag (soft delete)

    Requires 'tags:delete' permission. By default, fails if tag is in use.
    Use force=true to delete regardless of usage.
    """
    start_time = time.time()

    # Execute use case with audit tracking
    result = use_case.execute(
        tag_id=tag_id,
        organization_id=current_user["organization_id"],
        force=force,
        deleted_by_id=current_user["user_id"],
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
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return {
        "success": True,
        "message": result["message"]
    }


# =============================================================================
# CONTENT-TAG ASSIGNMENT ENDPOINTS
# =============================================================================

@router.post(
    TagRoutes.ASSIGN_TO_CONTENT,
    response_model=TagAssignmentResponse,
    status_code=status.HTTP_200_OK
)
@handle_errors
def assign_tag_to_content(
    tag_id: int,
    request_body: AssignTagRequest,
    http_request: Request,
    use_case: AssignTagToContentUseCase = Depends(get_assign_tag_to_content_use_case),
    current_user: dict = Depends(require_permission("tags", "update")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Assign a tag to a single content item

    Requires 'tags:update' permission. Both tag and content must belong to the same organization.
    """
    start_time = time.time()

    # Execute use case with audit tracking
    result = use_case.execute(
        tag_id=tag_id,
        content_id=request_body.content_id,
        organization_id=current_user["organization_id"],
        assigned_by_id=current_user["user_id"],
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=TagRoutes.ASSIGN_TO_CONTENT,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    if result["success"]:
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="tag.assign_content",
            resource_type="tag",
            resource_id=tag_id,
            details={"content_id": request_body.content_id},
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"]
        )

    return result


@router.post(
    TagRoutes.ASSIGN_TO_CONTENTS,
    response_model=BulkTagAssignmentResponse,
    status_code=status.HTTP_200_OK
)
@handle_errors
def assign_tag_to_contents(
    tag_id: int,
    request_body: AssignTagToContentsRequest,
    http_request: Request,
    use_case: AssignTagToContentsUseCase = Depends(get_assign_tag_to_contents_use_case),
    current_user: dict = Depends(require_permission("tags", "update")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Bulk assign a tag to multiple content items

    Requires 'tags:update' permission. Returns counts of successful/skipped/failed assignments.
    """
    start_time = time.time()

    # Execute use case with audit tracking
    result = use_case.execute(
        tag_id=tag_id,
        content_ids=request_body.content_ids,
        organization_id=current_user["organization_id"],
        assigned_by_id=current_user["user_id"],
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="POST",
        path=TagRoutes.ASSIGN_TO_CONTENTS,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="tag.bulk_assign_contents",
        resource_type="tag",
        resource_id=tag_id,
        details={
            "content_count": len(request_body.content_ids),
            "assigned": result["assigned"],
            "skipped": result["skipped"],
            "failed": result["failed"]
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return result


@router.delete(
    TagRoutes.UNASSIGN_FROM_CONTENT,
    response_model=TagAssignmentResponse,
    status_code=status.HTTP_200_OK
)
@handle_errors
def unassign_tag_from_content(
    tag_id: int,
    request_body: UnassignTagRequest,
    http_request: Request,
    use_case: UnassignTagFromContentUseCase = Depends(get_unassign_tag_from_content_use_case),
    current_user: dict = Depends(require_permission("tags", "update")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Unassign a tag from a single content item

    Requires 'tags:update' permission. Both tag and content must belong to the same organization.
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(
        tag_id=tag_id,
        content_id=request_body.content_id,
        organization_id=current_user["organization_id"]
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="DELETE",
        path=TagRoutes.UNASSIGN_FROM_CONTENT,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    if result["success"]:
        audit_logger.log_action(
            user_id=current_user["user_id"],
            action="tag.unassign_content",
            resource_type="tag",
            resource_id=tag_id,
            details={"content_id": request_body.content_id},
            ip_address=http_request.client.host if http_request.client else None,
            organization_id=current_user["organization_id"]
        )

    return result


@router.delete(
    TagRoutes.UNASSIGN_FROM_CONTENTS,
    response_model=BulkTagUnassignmentResponse,
    status_code=status.HTTP_200_OK
)
@handle_errors
def unassign_tag_from_contents(
    tag_id: int,
    request_body: UnassignTagFromContentsRequest,
    http_request: Request,
    use_case: UnassignTagFromContentsUseCase = Depends(get_unassign_tag_from_contents_use_case),
    current_user: dict = Depends(require_permission("tags", "update")),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Bulk unassign a tag from multiple content items

    Requires 'tags:update' permission. Returns counts of successful/not found unassignments.
    """
    start_time = time.time()

    # Execute use case
    result = use_case.execute(
        tag_id=tag_id,
        content_ids=request_body.content_ids,
        organization_id=current_user["organization_id"]
    )

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="DELETE",
        path=TagRoutes.UNASSIGN_FROM_CONTENTS,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    # Audit log
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action="tag.bulk_unassign_contents",
        resource_type="tag",
        resource_id=tag_id,
        details={
            "content_count": len(request_body.content_ids),
            "unassigned": result["unassigned"],
            "not_found": result["not_found"]
        },
        ip_address=http_request.client.host if http_request.client else None,
        organization_id=current_user["organization_id"]
    )

    return result


@router.get(
    TagRoutes.GET_CONTENT_TAGS,
    response_model=ContentTagsResponse
)
@handle_errors
def get_content_tags(
    content_id: int,
    use_case: GetContentTagsUseCase = Depends(get_get_content_tags_use_case),
    current_user: dict = Depends(require_permission("tags", "read"))
):
    """
    Get all tags assigned to a content item

    Requires 'tags:read' permission. Content must belong to the user's organization.
    """
    start_time = time.time()

    # Execute use case
    tags = use_case.execute(
        content_id=content_id,
        organization_id=current_user["organization_id"]
    )

    # Convert to response
    tag_responses = [TagResponse.model_validate(tag) for tag in tags]

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    request_logger.log_request(
        method="GET",
        path=TagRoutes.GET_CONTENT_TAGS,
        status_code=200,
        duration_ms=duration_ms,
        user_id=current_user["user_id"]
    )

    return {
        "success": True,
        "data": tag_responses,
        "total": len(tag_responses)
    }
