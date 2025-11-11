"""
Template Schemas for Template Variables API

Comprehensive Pydantic models for:
- Template validation and rendering
- Custom variable management
- Security and performance monitoring
- Available variables documentation

Updated for Phase 4.1 implementation with enhanced security.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Set
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class TemplateVariableType(str, Enum):
    """Types of template variables available"""
    SYSTEM = "system"  # System variables (device, datetime)
    EXTERNAL = "external"  # External data (weather, firebird)
    CUSTOM = "custom"  # User-defined variables


class TemplateEngineType(str, Enum):
    """Supported template engines"""
    JINJA2 = "jinja2"
    SIMPLE = "simple"  # Simple string.format style


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class TemplateValidationRequest(BaseModel):
    """Request for template validation with enhanced security checks"""
    template: str = Field(
        ...,
        min_length=1,
        max_length=51200,  # 50KB max
        description="Template string to validate"
    )
    engine: TemplateEngineType = Field(
        default=TemplateEngineType.JINJA2,
        description="Template engine to use"
    )
    strict_mode: bool = Field(
        default=True,
        description="Fail on undefined variables and security issues"
    )

    class Config:
        schema_extra = {
            "example": {
                "template": "Welcome {{device.name}}! Today is {{datetime.today|date('%Y-%m-%d')}}",
                "engine": "jinja2",
                "strict_mode": True
            }
        }


class TemplateRenderRequest(BaseModel):
    """Request for template rendering with security controls"""
    template: str = Field(
        ...,
        min_length=1,
        max_length=51200,  # 50KB max
        description="Template string to render"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom context variables (filtered by role)"
    )
    device_id: Optional[int] = Field(
        None,
        description="Device ID for device-specific variables"
    )
    content_id: Optional[int] = Field(
        None,
        description="Content ID for content-specific variables"
    )
    engine: TemplateEngineType = Field(
        default=TemplateEngineType.JINJA2,
        description="Template engine to use"
    )
    safe_mode: bool = Field(
        default=True,
        description="Enable sandboxed execution (REQUIRED for security)"
    )
    use_cache: bool = Field(
        default=True,
        description="Use multi-layer caching for performance"
    )
    timeout: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Maximum execution time in seconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "template": "Temperature: {{weather.temp}}°C, {{weather.condition}}",
                "context": {},
                "device_id": 1,
                "content_id": 5,
                "engine": "jinja2",
                "safe_mode": True,
                "use_cache": True,
                "timeout": 5
            }
        }


class TemplatePreviewRequest(BaseModel):
    """Request for template preview with sample data"""
    template: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Template string to preview"
    )
    use_sample_data: bool = Field(
        default=True,
        description="Use sample data for preview"
    )
    custom_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom context to merge with sample data"
    )
    engine: TemplateEngineType = Field(
        default=TemplateEngineType.JINJA2,
        description="Template engine to use"
    )

    class Config:
        schema_extra = {
            "example": {
                "template": "Welcome to {{ hotel_name }}! Today is {{ date }}",
                "use_sample_data": True,
                "custom_context": {
                    "hotel_name": "Grand Hotel"
                }
            }
        }


class CustomVariableCreate(BaseModel):
    """Create a custom template variable"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        regex="^[a-zA-Z][a-zA-Z0-9_]*$",
        description="Variable name (alphanumeric and underscore)"
    )
    value: Union[str, int, float, bool, List, Dict] = Field(
        ...,
        description="Variable value (any JSON-serializable type)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Variable description"
    )
    is_global: bool = Field(
        default=False,
        description="Make variable available globally"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Variable expiration time"
    )

    @validator('name')
    def validate_name(cls, v):
        """Ensure variable name doesn't conflict with system variables"""
        reserved = ['device', 'datetime', 'system', 'weather', 'firebird']
        if v.lower() in reserved:
            raise ValueError(f"Variable name '{v}' is reserved")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "special_offer",
                "value": "20% off all spa treatments",
                "description": "Current promotional offer",
                "is_global": True,
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }


class CustomVariableUpdate(BaseModel):
    """Update a custom variable"""
    value: Optional[Union[str, int, float, bool, List, Dict]] = None
    description: Optional[str] = Field(None, max_length=500)
    is_global: Optional[bool] = None
    expires_at: Optional[datetime] = None


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TemplateValidationResponse(BaseModel):
    """Response for template validation"""
    is_valid: bool = Field(..., description="Whether template is valid")
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warnings (non-fatal)"
    )
    required_variables: List[str] = Field(
        default_factory=list,
        description="Variables required by template"
    )
    detected_functions: List[str] = Field(
        default_factory=list,
        description="Functions/filters used in template"
    )

    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Variable 'optional_var' may be undefined"],
                "required_variables": ["guest_name", "room_number"],
                "detected_functions": ["upper", "date_format"]
            }
        }


class TemplateRenderResponse(BaseModel):
    """Response for template rendering"""
    success: bool = Field(..., description="Whether rendering succeeded")
    rendered: Optional[str] = Field(
        None,
        description="Rendered template output"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if rendering failed"
    )
    execution_time_ms: float = Field(
        ...,
        description="Rendering time in milliseconds"
    )
    truncated: bool = Field(
        default=False,
        description="Whether output was truncated"
    )

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "rendered": "Welcome John Doe! Room: 101",
                "error": None,
                "execution_time_ms": 12.5,
                "truncated": False
            }
        }


class TemplateVariable(BaseModel):
    """Template variable information"""
    name: str = Field(..., description="Variable name")
    type: TemplateVariableType = Field(..., description="Variable type")
    description: str = Field(..., description="Variable description")
    example: Any = Field(..., description="Example value")
    required: bool = Field(default=False, description="Whether required")
    path: Optional[str] = Field(
        None,
        description="Nested path (e.g., 'device.name')"
    )

    class Config:
        schema_extra = {
            "example": {
                "name": "device_name",
                "type": "system",
                "description": "Current device name",
                "example": "Lobby Display",
                "required": False,
                "path": "device.name"
            }
        }


class TemplateVariablesResponse(BaseModel):
    """Response listing available template variables"""
    system: List[TemplateVariable] = Field(
        ...,
        description="System variables"
    )
    external: List[TemplateVariable] = Field(
        ...,
        description="External data variables"
    )
    custom: List[TemplateVariable] = Field(
        ...,
        description="User-defined variables"
    )
    total_count: int = Field(..., description="Total number of variables")

    class Config:
        schema_extra = {
            "example": {
                "system": [
                    {
                        "name": "device_name",
                        "type": "system",
                        "description": "Device name",
                        "example": "Lobby Display",
                        "required": False,
                        "path": "device.name"
                    }
                ],
                "external": [
                    {
                        "name": "temperature",
                        "type": "external",
                        "description": "Current temperature",
                        "example": 25.5,
                        "required": False,
                        "path": "weather.temperature"
                    }
                ],
                "custom": [],
                "total_count": 2
            }
        }


class CustomVariableResponse(BaseModel):
    """Response for custom variable"""
    id: int = Field(..., description="Variable ID")
    name: str = Field(..., description="Variable name")
    value: Union[str, int, float, bool, List, Dict] = Field(
        ...,
        description="Variable value"
    )
    description: Optional[str] = Field(None, description="Description")
    is_global: bool = Field(..., description="Global availability")
    expires_at: Optional[datetime] = Field(None, description="Expiration")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    created_by: Optional[str] = Field(None, description="Creator username")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "special_offer",
                "value": "20% off spa treatments",
                "description": "Current promotion",
                "is_global": True,
                "expires_at": "2024-12-31T23:59:59Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin"
            }
        }


class TemplatePreviewResponse(BaseModel):
    """Response for template preview"""
    preview: str = Field(..., description="Rendered preview")
    sample_context: Dict[str, Any] = Field(
        ...,
        description="Sample data used"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Preview warnings"
    )

    class Config:
        schema_extra = {
            "example": {
                "preview": "Welcome to Grand Hotel! Today is Monday, January 1",
                "sample_context": {
                    "hotel_name": "Grand Hotel",
                    "date": "Monday, January 1"
                },
                "warnings": []
            }
        }