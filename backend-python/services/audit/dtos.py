"""
Audit Service DTOs
Request/Response models for audit log endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class AuditLogResponse(BaseModel):
    """Audit log response DTO"""

    id: int
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    # Populated from relationships (optional)
    username: Optional[str] = None
    organization_name: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Audit log list response DTO"""

    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# =============================================================================
# FILTER DTOs (for query parameters)
# =============================================================================

class AuditLogFilters(BaseModel):
    """Query parameters for filtering audit logs"""

    user_id: Optional[int] = Field(None, description="Filter by user ID")
    organization_id: Optional[int] = Field(None, description="Filter by organization ID")
    action: Optional[str] = Field(None, description="Filter by action (e.g., 'user.create')")
    resource_type: Optional[str] = Field(None, description="Filter by resource type (e.g., 'user')")
    resource_id: Optional[int] = Field(None, description="Filter by resource ID")
    start_date: Optional[datetime] = Field(None, description="Filter from this date")
    end_date: Optional[datetime] = Field(None, description="Filter until this date")
    limit: int = Field(100, ge=1, le=1000, description="Max results per page")
    offset: int = Field(0, ge=0, description="Number of results to skip")
