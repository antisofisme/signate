"""
Configuration Master Data Endpoints
Purpose: CRUD for customer-defined master data (governance, UI grouping)
NOT for decision evaluation logic

Endpoints:
- /api/config/functional-areas (CRUD)
- /api/config/decision-types (Read-only for system-defined, CRUD for custom)
- /api/config/approver-roles (CRUD)

SECURITY:
- All endpoints require authentication (JWT or API key)
- tenant_id is extracted from authenticated context, NOT from query params
- This prevents unauthorized access to other tenants' configuration
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime
from pydantic import BaseModel, Field

from ..repositories.config_models import (
    FunctionalAreaModel,
    DecisionTypeModel,
    ApproverRoleModel
)
from .dependencies import get_rls_session, get_authenticated_context, AuthenticatedContext

router = APIRouter(prefix="/api/config", tags=["configuration"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

# Functional Areas
class FunctionalAreaCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unique code (uppercase, snake_case)")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class FunctionalAreaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class FunctionalAreaResponse(BaseModel):
    functional_area_id: str
    tenant_id: str
    code: str
    name: str
    description: Optional[str]
    is_active: bool
    display_order: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# Decision Types
class DecisionTypeCreate(BaseModel):
    type_code: str = Field(..., min_length=1, max_length=100)
    type_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    context_schema: dict = Field(default_factory=dict, description="JSON Schema for context validation")
    is_active: bool = True


class DecisionTypeUpdate(BaseModel):
    type_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    context_schema: Optional[dict] = None
    is_active: Optional[bool] = None


class DecisionTypeResponse(BaseModel):
    decision_type_id: str
    tenant_id: str
    type_code: str
    type_name: str
    description: Optional[str]
    context_schema: dict
    is_system_defined: bool
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# Approver Roles
class ApproverRoleCreate(BaseModel):
    role_code: str = Field(..., min_length=1, max_length=100)
    role_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class ApproverRoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class ApproverRoleResponse(BaseModel):
    approver_role_id: str
    tenant_id: str
    role_code: str
    role_name: str
    description: Optional[str]
    is_active: bool
    display_order: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# FUNCTIONAL AREAS ENDPOINTS
# ============================================================================

@router.get("/functional-areas", response_model=dict)
async def list_functional_areas(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    active_only: bool = Query(True, description="Filter active only"),
    session: AsyncSession = Depends(get_rls_session)
):
    """List all functional areas for tenant.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    query = select(FunctionalAreaModel).where(FunctionalAreaModel.tenant_id == tenant_id)

    if active_only:
        query = query.where(FunctionalAreaModel.is_active == True)

    query = query.order_by(FunctionalAreaModel.display_order, FunctionalAreaModel.name)

    result = await session.execute(query)
    areas = result.scalars().all()

    return {
        "functional_areas": [
            {
                "functional_area_id": str(area.functional_area_id),
                "tenant_id": str(area.tenant_id),
                "code": area.code,
                "name": area.name,
                "description": area.description,
                "is_active": area.is_active,
                "display_order": area.display_order,
                "created_at": area.created_at.isoformat() if area.created_at else None,
                "updated_at": area.updated_at.isoformat() if area.updated_at else None
            }
            for area in areas
        ],
        "total": len(areas)
    }


@router.post("/functional-areas", response_model=FunctionalAreaResponse, status_code=status.HTTP_201_CREATED)
async def create_functional_area(
    data: FunctionalAreaCreate,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Create new functional area.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    # Check if code already exists for tenant
    existing = await session.execute(
        select(FunctionalAreaModel).where(
            and_(
                FunctionalAreaModel.tenant_id == tenant_id,
                FunctionalAreaModel.code == data.code
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Functional area with code '{data.code}' already exists"
        )

    # Create new area
    area = FunctionalAreaModel(
        tenant_id=tenant_id,
        code=data.code.upper(),  # Enforce uppercase
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        display_order=data.display_order
    )

    session.add(area)
    await session.commit()
    await session.refresh(area)

    return FunctionalAreaResponse.model_validate(area)


@router.patch("/functional-areas/{area_id}", response_model=FunctionalAreaResponse)
async def update_functional_area(
    area_id: UUID,
    data: FunctionalAreaUpdate,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Update functional area.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    result = await session.execute(
        select(FunctionalAreaModel).where(
            and_(
                FunctionalAreaModel.functional_area_id == area_id,
                FunctionalAreaModel.tenant_id == tenant_id
            )
        )
    )
    area = result.scalar_one_or_none()

    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Functional area not found")

    # Update fields
    if data.name is not None:
        area.name = data.name
    if data.description is not None:
        area.description = data.description
    if data.is_active is not None:
        area.is_active = data.is_active
    if data.display_order is not None:
        area.display_order = data.display_order

    area.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(area)

    return FunctionalAreaResponse.model_validate(area)


@router.delete("/functional-areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_functional_area(
    area_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Delete functional area (sets foreign keys to NULL in rules).

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    result = await session.execute(
        select(FunctionalAreaModel).where(
            and_(
                FunctionalAreaModel.functional_area_id == area_id,
                FunctionalAreaModel.tenant_id == tenant_id
            )
        )
    )
    area = result.scalar_one_or_none()

    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Functional area not found")

    await session.delete(area)
    await session.commit()


# ============================================================================
# DECISION TYPES ENDPOINTS
# ============================================================================

@router.get("/decision-types", response_model=dict)
async def list_decision_types(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    active_only: bool = Query(True, description="Filter active only"),
    session: AsyncSession = Depends(get_rls_session)
):
    """List all decision types for tenant.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    query = select(DecisionTypeModel).where(DecisionTypeModel.tenant_id == tenant_id)

    if active_only:
        query = query.where(DecisionTypeModel.is_active == True)

    query = query.order_by(DecisionTypeModel.type_name)

    result = await session.execute(query)
    types = result.scalars().all()

    return {
        "decision_types": [
            {
                "decision_type_id": str(t.decision_type_id),
                "tenant_id": str(t.tenant_id),
                "type_code": t.type_code,
                "type_name": t.type_name,
                "description": t.description,
                "context_schema": t.context_schema,
                "is_system_defined": t.is_system_defined,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in types
        ],
        "total": len(types)
    }


@router.post("/decision-types", response_model=DecisionTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_decision_type(
    data: DecisionTypeCreate,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Create new custom decision type (customer-defined, not system).

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    # Check if code already exists
    existing = await session.execute(
        select(DecisionTypeModel).where(
            and_(
                DecisionTypeModel.tenant_id == tenant_id,
                DecisionTypeModel.type_code == data.type_code
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Decision type with code '{data.type_code}' already exists"
        )

    # Create new type (NOT system-defined)
    dtype = DecisionTypeModel(
        tenant_id=tenant_id,
        type_code=data.type_code,
        type_name=data.type_name,
        description=data.description,
        context_schema=data.context_schema,
        is_system_defined=False,  # Customer-created types
        is_active=data.is_active
    )

    session.add(dtype)
    await session.commit()
    await session.refresh(dtype)

    return DecisionTypeResponse.model_validate(dtype)


@router.patch("/decision-types/{type_id}", response_model=DecisionTypeResponse)
async def update_decision_type(
    type_id: UUID,
    data: DecisionTypeUpdate,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Update decision type (only custom types, not system-defined).

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    result = await session.execute(
        select(DecisionTypeModel).where(
            and_(
                DecisionTypeModel.decision_type_id == type_id,
                DecisionTypeModel.tenant_id == tenant_id
            )
        )
    )
    dtype = result.scalar_one_or_none()

    if not dtype:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision type not found")

    # Prevent editing system-defined types
    if dtype.is_system_defined:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit system-defined decision types"
        )

    # Update fields
    if data.type_name is not None:
        dtype.type_name = data.type_name
    if data.description is not None:
        dtype.description = data.description
    if data.context_schema is not None:
        dtype.context_schema = data.context_schema
    if data.is_active is not None:
        dtype.is_active = data.is_active

    dtype.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(dtype)

    return DecisionTypeResponse.model_validate(dtype)


@router.delete("/decision-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_decision_type(
    type_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Delete decision type (only custom types, not system-defined).

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    result = await session.execute(
        select(DecisionTypeModel).where(
            and_(
                DecisionTypeModel.decision_type_id == type_id,
                DecisionTypeModel.tenant_id == tenant_id
            )
        )
    )
    dtype = result.scalar_one_or_none()

    if not dtype:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision type not found")

    # Prevent deleting system-defined types
    if dtype.is_system_defined:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system-defined decision types"
        )

    await session.delete(dtype)
    await session.commit()


# ============================================================================
# APPROVER ROLES ENDPOINTS
# ============================================================================

@router.get("/approver-roles", response_model=dict)
async def list_approver_roles(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    active_only: bool = Query(True, description="Filter active only"),
    session: AsyncSession = Depends(get_rls_session)
):
    """List all approver roles for tenant.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    query = select(ApproverRoleModel).where(ApproverRoleModel.tenant_id == tenant_id)

    if active_only:
        query = query.where(ApproverRoleModel.is_active == True)

    query = query.order_by(ApproverRoleModel.display_order, ApproverRoleModel.role_name)

    result = await session.execute(query)
    roles = result.scalars().all()

    return {
        "approver_roles": [
            {
                "approver_role_id": str(role.approver_role_id),
                "tenant_id": str(role.tenant_id),
                "role_code": role.role_code,
                "role_name": role.role_name,
                "description": role.description,
                "is_active": role.is_active,
                "display_order": role.display_order,
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "updated_at": role.updated_at.isoformat() if role.updated_at else None
            }
            for role in roles
        ],
        "total": len(roles)
    }


@router.post("/approver-roles", response_model=ApproverRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_approver_role(
    data: ApproverRoleCreate,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Create new approver role.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    # Check if code already exists
    existing = await session.execute(
        select(ApproverRoleModel).where(
            and_(
                ApproverRoleModel.tenant_id == tenant_id,
                ApproverRoleModel.role_code == data.role_code
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approver role with code '{data.role_code}' already exists"
        )

    # Create new role
    role = ApproverRoleModel(
        tenant_id=tenant_id,
        role_code=data.role_code,
        role_name=data.role_name,
        description=data.description,
        is_active=data.is_active,
        display_order=data.display_order
    )

    session.add(role)
    await session.commit()
    await session.refresh(role)

    return ApproverRoleResponse.model_validate(role)


@router.patch("/approver-roles/{role_id}", response_model=ApproverRoleResponse)
async def update_approver_role(
    role_id: UUID,
    data: ApproverRoleUpdate,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Update approver role.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    result = await session.execute(
        select(ApproverRoleModel).where(
            and_(
                ApproverRoleModel.approver_role_id == role_id,
                ApproverRoleModel.tenant_id == tenant_id
            )
        )
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver role not found")

    # Update fields
    if data.role_name is not None:
        role.role_name = data.role_name
    if data.description is not None:
        role.description = data.description
    if data.is_active is not None:
        role.is_active = data.is_active
    if data.display_order is not None:
        role.display_order = data.display_order

    role.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(role)

    return ApproverRoleResponse.model_validate(role)


@router.delete("/approver-roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_approver_role(
    role_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    session: AsyncSession = Depends(get_rls_session)
):
    """Delete approver role.

    SECURITY: tenant_id is extracted from authenticated context.
    """
    tenant_id = UUID(ctx.tenant_id)
    result = await session.execute(
        select(ApproverRoleModel).where(
            and_(
                ApproverRoleModel.approver_role_id == role_id,
                ApproverRoleModel.tenant_id == tenant_id
            )
        )
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver role not found")

    await session.delete(role)
    await session.commit()
