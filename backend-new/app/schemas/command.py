"""
Command Schemas
===============

Pydantic schemas for device command operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommandExecute(BaseModel):
    """Execute command request"""
    device_id: int = Field(..., gt=0, description="Device ID")
    command_type: str = Field(..., description="Command type (reset, refresh, reload)")
    reason: Optional[str] = Field(None, max_length=100, description="Reason for command")
    expires_in_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Command expiration time in minutes (default: 60, max: 1440/24h)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": 5,
                "command_type": "reset",
                "reason": "Manual reset by admin",
                "expires_in_minutes": 60
            }
        }
    }


class BatchCommandExecute(BaseModel):
    """Execute command on multiple devices"""
    device_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of device IDs (max 100)")
    command_type: str = Field(..., description="Command type (reset, refresh, reload)")
    reason: Optional[str] = Field(None, max_length=100, description="Reason for command")
    expires_in_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Command expiration time in minutes"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_ids": [5, 8, 12],
                "command_type": "refresh",
                "reason": "Content update",
                "expires_in_minutes": 30
            }
        }
    }


class CommandResponse(BaseModel):
    """Command response schema"""
    id: int = Field(..., description="Command ID")
    device_id: int = Field(..., description="Device ID")
    command_type: str = Field(..., description="Command type")
    reason: Optional[str] = Field(None, description="Reason for command")
    status: str = Field(..., description="Command status (pending, executed, expired)")
    created_at: datetime = Field(..., description="When command was created")
    executed_at: Optional[datetime] = Field(None, description="When command was executed")
    expires_at: datetime = Field(..., description="When command will expire")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 123,
                "device_id": 5,
                "command_type": "reset",
                "reason": "Manual reset by admin",
                "status": "pending",
                "created_at": "2024-01-01T12:00:00",
                "executed_at": None,
                "expires_at": "2024-01-01T13:00:00"
            }
        }
    }


class BatchCommandResponse(BaseModel):
    """Batch command execution response"""
    total: int = Field(..., description="Total devices targeted")
    successful: int = Field(..., description="Successfully queued commands")
    failed: int = Field(..., description="Failed to queue commands")
    commands: List[CommandResponse] = Field(default=[], description="List of queued commands")
    errors: List[str] = Field(default=[], description="List of errors for failed commands")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 3,
                "successful": 2,
                "failed": 1,
                "commands": [],
                "errors": ["Device 999 not found"]
            }
        }
    }


class CommandListResponse(BaseModel):
    """Command list response with pagination"""
    commands: List[CommandResponse] = Field(default=[], description="List of commands")
    total: int = Field(..., description="Total commands count")
    skip: int = Field(..., description="Pagination offset")
    limit: int = Field(..., description="Pagination limit")
    status_counts: dict = Field(default={}, description="Count by status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "commands": [],
                "total": 50,
                "skip": 0,
                "limit": 20,
                "status_counts": {
                    "pending": 5,
                    "executed": 40,
                    "expired": 5
                }
            }
        }
    }


class CommandStatusUpdate(BaseModel):
    """Update command status (called by device)"""
    status: str = Field(..., description="New status (executed or expired)")
    error_message: Optional[str] = Field(None, max_length=500, description="Error message if failed")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "executed",
                "error_message": None
            }
        }
    }
