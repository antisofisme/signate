"""
Report Schemas for Quick Wins Pattern
Pydantic models for report generation, scheduling, and management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Report Generation Schemas
# ============================================================================

class ReportGenerateRequest(BaseModel):
    """Request model for report generation"""

    format: str = Field(
        ...,
        description="Report format: pdf, excel, or csv",
        pattern="^(pdf|excel|csv)$"
    )
    report_type: str = Field(
        default="custom",
        description="Report type: daily, weekly, monthly, or custom"
    )
    start_date: datetime = Field(..., description="Start date for report data")
    end_date: datetime = Field(..., description="End date for report data")
    sections: List[str] = Field(
        default=["overview", "content", "devices", "system"],
        description="Sections to include in report"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional filters (device_ids, content_ids, tag_ids)"
    )

    @field_validator('sections')
    @classmethod
    def validate_sections(cls, v):
        valid_sections = {"overview", "content", "devices", "system", "errors", "trends"}
        invalid = set(v) - valid_sections
        if invalid:
            raise ValueError(f"Invalid sections: {invalid}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "format": "pdf",
                "report_type": "monthly",
                "start_date": "2025-10-01T00:00:00",
                "end_date": "2025-10-31T23:59:59",
                "sections": ["overview", "content", "devices"],
                "filters": {
                    "device_ids": ["device-123", "device-456"],
                    "tag_ids": ["tag-789"]
                }
            }
        }


class ReportResponse(BaseModel):
    """Response model for report metadata"""

    id: str = Field(..., description="Unique report identifier")
    title: str = Field(..., description="Report title")
    format: str = Field(..., description="Report format (pdf, excel, csv)")
    status: str = Field(..., description="Report status: pending, processing, completed, failed")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL when completed")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    task_id: Optional[str] = Field(None, description="Celery task ID")
    estimated_time: Optional[str] = Field(None, description="Estimated completion time")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "report-123",
                "title": "Monthly Analytics Report - October 2025",
                "format": "pdf",
                "status": "completed",
                "file_size": 2048576,
                "download_url": "/api/reports/report-123/download",
                "created_at": "2025-10-28T10:00:00Z",
                "completed_at": "2025-10-28T10:02:30Z",
                "error_message": None,
                "task_id": "abc123def456",
                "estimated_time": None
            }
        }


# ============================================================================
# Report Scheduling Schemas
# ============================================================================

class ReportScheduleRequest(BaseModel):
    """Request model for scheduling recurring reports"""

    name: str = Field(..., description="Schedule name", min_length=1, max_length=100)
    report_type: str = Field(..., description="Report type to generate")
    format: str = Field(
        ...,
        description="Report format",
        pattern="^(pdf|excel|csv)$"
    )
    sections: List[str] = Field(
        default=["overview", "content", "devices"],
        description="Sections to include"
    )
    frequency: str = Field(
        ...,
        description="Schedule frequency: daily, weekly, monthly",
        pattern="^(daily|weekly|monthly)$"
    )
    time: str = Field(
        ...,
        description="Time to run (HH:MM format)",
        pattern="^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    )
    recipients: List[str] = Field(
        default=[],
        description="Email addresses to send reports to"
    )
    is_active: bool = Field(default=True, description="Whether schedule is active")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Weekly Analytics Report",
                "report_type": "weekly",
                "format": "pdf",
                "sections": ["overview", "content", "devices"],
                "frequency": "weekly",
                "time": "09:00",
                "recipients": ["admin@example.com"],
                "is_active": True,
                "filters": {"tag_ids": ["tag-production"]}
            }
        }


class ReportScheduleResponse(BaseModel):
    """Response model for scheduled report"""

    id: str = Field(..., description="Schedule identifier")
    name: str = Field(..., description="Schedule name")
    report_type: str = Field(..., description="Report type")
    format: str = Field(..., description="Report format")
    sections: List[str] = Field(..., description="Sections to include")
    frequency: str = Field(..., description="Schedule frequency")
    time: str = Field(..., description="Execution time")
    recipients: List[str] = Field(..., description="Email recipients")
    is_active: bool = Field(..., description="Whether schedule is active")
    last_run: Optional[datetime] = Field(None, description="Last execution time")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run")
    created_at: datetime = Field(..., description="Creation timestamp")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "schedule-789",
                "name": "Weekly Analytics Report",
                "report_type": "weekly",
                "format": "pdf",
                "sections": ["overview", "content"],
                "frequency": "weekly",
                "time": "09:00",
                "recipients": ["admin@example.com"],
                "is_active": True,
                "last_run": "2025-10-21T09:00:00Z",
                "next_run": "2025-10-28T09:00:00Z",
                "created_at": "2025-10-01T12:00:00Z",
                "filters": None
            }
        }


# ============================================================================
# Report Template Schemas
# ============================================================================

class ReportTemplateResponse(BaseModel):
    """Response model for report template"""

    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    sections: List[str] = Field(..., description="Available sections")
    supported_formats: List[str] = Field(..., description="Supported output formats")
    preview_url: Optional[str] = Field(None, description="Template preview URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "template-analytics",
                "name": "Analytics Summary",
                "description": "Comprehensive analytics report with device and content statistics",
                "sections": ["overview", "content", "devices", "system", "trends"],
                "supported_formats": ["pdf", "excel", "csv"],
                "preview_url": "/api/reports/templates/template-analytics/preview"
            }
        }


# ============================================================================
# Quick Export Schemas
# ============================================================================

class QuickExportRequest(BaseModel):
    """Request model for quick export (synchronous)"""

    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    orientation: Optional[str] = Field(
        "landscape",
        description="PDF orientation (landscape or portrait)",
        pattern="^(landscape|portrait)$"
    )
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-10-01T00:00:00",
                "end_date": "2025-10-31T23:59:59",
                "orientation": "landscape",
                "filters": {"device_ids": ["device-123"]}
            }
        }
