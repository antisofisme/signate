"""
Project API Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ============== Request Schemas ==============

class CreateProjectRequest(BaseModel):
    """Request to create a project"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    environment: str = Field("development", pattern="^(production|staging|development|testing)$")


class UpdateProjectRequest(BaseModel):
    """Request to update a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    environment: Optional[str] = Field(None, pattern="^(production|staging|development|testing)$")
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AddMemberRequest(BaseModel):
    """Request to add a member"""
    user_id: UUID
    role: str = Field("member", pattern="^(admin|member|viewer)$")


class UpdateMemberRoleRequest(BaseModel):
    """Request to update a member's role"""
    role: str = Field(..., pattern="^(admin|member|viewer)$")


# ============== Response Schemas ==============

class ProjectResponse(BaseModel):
    """Project in API response"""
    project_id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: Optional[str]
    environment: str
    settings: Dict[str, Any]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectMemberResponse(BaseModel):
    """Project member in API response"""
    project_id: UUID
    user_id: UUID
    role: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Paginated list of projects"""
    projects: List[ProjectResponse]
    total: int
    limit: int
    offset: int


class ProjectMemberListResponse(BaseModel):
    """List of project members"""
    members: List[ProjectMemberResponse]
    total: int


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
