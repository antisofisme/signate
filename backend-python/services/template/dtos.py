"""
Template DTOs
Request and Response models for template endpoints
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Template DTOs
# ============================================================================

class CreateTemplateRequest(BaseModel):
    """Request to create a new template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: str = Field(..., description="Template type: text, image, video, html, greeting")
    content: str = Field(..., description="Template content with {{variables}}")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variable definitions")
    preview_data: Optional[Dict[str, Any]] = Field(None, description="Sample data for preview")
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Welcome Message",
                "description": "Welcome message for hotel guests",
                "template_type": "text",
                "content": "Welcome {{guest_name}} to room {{room_number}}! Check-out time is {{checkout_time}}.",
                "variables": {
                    "guest_name": "string",
                    "room_number": "string",
                    "checkout_time": "string"
                },
                "preview_data": {
                    "guest_name": "John Doe",
                    "room_number": "101",
                    "checkout_time": "12:00 PM"
                },
                "is_active": True
            }
        }


class UpdateTemplateRequest(BaseModel):
    """Request to update existing template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    template_type: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    preview_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Template response model"""
    id: int
    organization_id: int
    name: str
    description: Optional[str]
    template_type: str
    content: str
    variables: Optional[Dict[str, Any]]
    preview_data: Optional[Dict[str, Any]]
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """List of templates response"""
    templates: List[TemplateResponse]
    total: int


# ============================================================================
# Template Rendering DTOs
# ============================================================================

class RenderTemplateRequest(BaseModel):
    """Request to render template with data"""
    data: Dict[str, Any] = Field(..., description="Data to render template with")

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "guest_name": "John Doe",
                    "room_number": "101",
                    "checkout_time": "12:00 PM"
                }
            }
        }


class RenderTemplateResponse(BaseModel):
    """Rendered template response"""
    rendered_content: str
    template_id: int
    template_name: str


class ValidateTemplateRequest(BaseModel):
    """Request to validate template"""
    content: str = Field(..., description="Template content to validate")
    variables: Optional[Dict[str, Any]] = Field(None, description="Sample data for validation")


class ValidateTemplateResponse(BaseModel):
    """Template validation response"""
    valid: bool
    message: str
    extracted_variables: Optional[List[str]] = None
    rendered_preview: Optional[str] = None


# ============================================================================
# Template Variable Extraction
# ============================================================================

class ExtractVariablesRequest(BaseModel):
    """Request to extract variables from template content"""
    content: str = Field(..., description="Template content")


class ExtractVariablesResponse(BaseModel):
    """Extracted variables response"""
    variables: List[str]
    variable_count: int
