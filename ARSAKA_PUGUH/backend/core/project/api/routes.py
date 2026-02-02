"""
Project API Routes

Security: All endpoints require authentication via JWT or API key.
Tenant isolation is enforced by extracting tenant_id from the authenticated context.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    CreateProjectRequest,
    UpdateProjectRequest,
    AddMemberRequest,
    UpdateMemberRoleRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectMemberResponse,
    ProjectMemberListResponse,
    SuccessResponse,
)
from .dependencies import (
    get_session_factory,
    get_create_project_use_case,
    get_update_project_use_case,
    get_delete_project_use_case,
    get_get_project_use_case,
    get_list_projects_use_case,
    get_add_member_use_case,
    get_remove_member_use_case,
    get_update_member_role_use_case,
)
from ...auth.api.dependencies import (
    AuthenticatedContext,
    get_authenticated_context,
)
from ..use_cases import (
    CreateProjectInput,
    UpdateProjectInput,
    DeleteProjectInput,
    GetProjectInput,
    ListProjectsInput,
    AddMemberInput,
    RemoveMemberInput,
    UpdateMemberRoleInput,
)
from ..exceptions import (
    ProjectNotFoundError,
    ProjectSlugExistsError,
    ProjectLimitExceededError,
    ProjectAccessDeniedError,
    ProjectError,
)
from ..adapters import PostgresMembershipRepository


router = APIRouter(prefix="/projects", tags=["Projects"])


# Helper to get session
async def get_db_session():
    """Get database session from factory"""
    factory = get_session_factory()
    async with factory() as session:
        yield session


# ============== Project CRUD ==============

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new project within a tenant.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)
    user_id = UUID(ctx.user_id)

    try:
        use_case = await get_create_project_use_case(session)
        result = await use_case.execute(
            CreateProjectInput(
                tenant_id=tenant_id,
                name=request.name,
                description=request.description,
                environment=request.environment,
                created_by=user_id,
            )
        )

        return ProjectResponse(
            project_id=result.project.project_id,
            tenant_id=result.project.tenant_id,
            name=result.project.name,
            slug=result.project.slug,
            description=result.project.description,
            environment=result.project.environment.value,
            settings=result.project.settings,
            is_active=result.project.is_active,
            created_at=result.project.created_at,
            updated_at=result.project.updated_at,
        )

    except ProjectLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": e.code, "message": e.message},
        )
    except ProjectSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    include_deleted: bool = Query(False, description="Include deleted projects"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """List all projects for a tenant.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    use_case = await get_list_projects_use_case(session)
    result = await use_case.execute(
        ListProjectsInput(
            tenant_id=tenant_id,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset,
        )
    )

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                project_id=p.project_id,
                tenant_id=p.tenant_id,
                name=p.name,
                slug=p.slug,
                description=p.description,
                environment=p.environment.value,
                settings=p.settings,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in result.projects
        ],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a project by ID.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_get_project_use_case(session)
        project = await use_case.execute(
            GetProjectInput(
                tenant_id=tenant_id,
                project_id=project_id,
            )
        )

        return ProjectResponse(
            project_id=project.project_id,
            tenant_id=project.tenant_id,
            name=project.name,
            slug=project.slug,
            description=project.description,
            environment=project.environment.value,
            settings=project.settings,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/by-slug/{slug}", response_model=ProjectResponse)
async def get_project_by_slug(
    slug: str,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Get a project by slug.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_get_project_use_case(session)
        project = await use_case.execute(
            GetProjectInput(
                tenant_id=tenant_id,
                slug=slug,
            )
        )

        return ProjectResponse(
            project_id=project.project_id,
            tenant_id=project.tenant_id,
            name=project.name,
            slug=project.slug,
            description=project.description,
            environment=project.environment.value,
            settings=project.settings,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Update a project.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_update_project_use_case(session)
        result = await use_case.execute(
            UpdateProjectInput(
                project_id=project_id,
                tenant_id=tenant_id,
                name=request.name,
                description=request.description,
                environment=request.environment,
                settings=request.settings,
                is_active=request.is_active,
            )
        )

        return ProjectResponse(
            project_id=result.project.project_id,
            tenant_id=result.project.tenant_id,
            name=result.project.name,
            slug=result.project.slug,
            description=result.project.description,
            environment=result.project.environment.value,
            settings=result.project.settings,
            is_active=result.project.is_active,
            created_at=result.project.created_at,
            updated_at=result.project.updated_at,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )
    except ProjectSlugExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(
    project_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a project (soft delete).

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_delete_project_use_case(session)
        result = await use_case.execute(
            DeleteProjectInput(
                project_id=project_id,
                tenant_id=tenant_id,
            )
        )

        return SuccessResponse(
            success=result.success,
            message=result.message,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )


# ============== Project Members ==============

@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: UUID,
    request: AddMemberRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Add a member to a project.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_add_member_use_case(session)
        result = await use_case.execute(
            AddMemberInput(
                project_id=project_id,
                tenant_id=tenant_id,
                user_id=request.user_id,
                role=request.role,
            )
        )

        return ProjectMemberResponse(
            project_id=result.membership.project_id,
            user_id=result.membership.user_id,
            role=result.membership.role.value,
            created_at=result.membership.created_at,
            updated_at=result.membership.updated_at,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/{project_id}/members", response_model=ProjectMemberListResponse)
async def list_project_members(
    project_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """List all members of a project.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    # Verify project exists
    get_use_case = await get_get_project_use_case(session)
    try:
        await get_use_case.execute(GetProjectInput(tenant_id=tenant_id, project_id=project_id))
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )

    membership_repo = PostgresMembershipRepository(session)
    members = await membership_repo.list_by_project(project_id)

    return ProjectMemberListResponse(
        members=[
            ProjectMemberResponse(
                project_id=m.project_id,
                user_id=m.user_id,
                role=m.role.value,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in members
        ],
        total=len(members),
    )


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: UUID,
    user_id: UUID,
    request: UpdateMemberRoleRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Update a member's role.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_update_member_role_use_case(session)
        result = await use_case.execute(
            UpdateMemberRoleInput(
                project_id=project_id,
                tenant_id=tenant_id,
                user_id=user_id,
                new_role=request.role,
            )
        )

        return ProjectMemberResponse(
            project_id=result.membership.project_id,
            user_id=result.membership.user_id,
            role=result.membership.role.value,
            created_at=result.membership.created_at,
            updated_at=result.membership.updated_at,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


@router.delete("/{project_id}/members/{user_id}", response_model=SuccessResponse)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    """Remove a member from a project.

    Security: tenant_id is extracted from authenticated context (JWT or API key).
    """
    tenant_id = UUID(ctx.tenant_id)

    try:
        use_case = await get_remove_member_use_case(session)
        result = await use_case.execute(
            RemoveMemberInput(
                project_id=project_id,
                tenant_id=tenant_id,
                user_id=user_id,
            )
        )

        return SuccessResponse(
            success=result.success,
            message=result.message,
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )
    except ProjectError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
