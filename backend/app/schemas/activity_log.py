"""
Activity Log schemas for API request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ActivityLogCreate(BaseModel):
    """Schema for creating an activity log entry"""
    action_type: str = Field(..., description="Type of action performed (e.g., DEVICE_APPROVED)")
    entity_type: str = Field(..., description="Type of entity affected (e.g., device, content)")
    entity_id: Optional[int] = Field(None, description="ID of the affected entity")
    entity_name: Optional[str] = Field(None, description="Name of the affected entity")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON")
    user_id: Optional[int] = Field(None, description="User who performed the action (auto-populated if not provided)")
    ip_address: Optional[str] = Field(None, description="IP address (auto-populated if not provided)")
    user_agent: Optional[str] = Field(None, description="User agent (auto-populated if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "DEVICE_APPROVED",
                "entity_type": "device",
                "entity_id": 123,
                "entity_name": "Conference Room TV",
                "details": {"approved_by": "admin", "reason": "Verified device"}
            }
        }


class ActivityLogResponse(BaseModel):
    """Schema for activity log response with user info"""
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    action_type: str
    entity_type: str
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    user: Optional[Dict[str, Any]] = None  # Populated with user info if user_id exists

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "timestamp": "2025-10-28T10:30:00Z",
                "user_id": 1,
                "action_type": "DEVICE_APPROVED",
                "entity_type": "device",
                "entity_id": 123,
                "entity_name": "Conference Room TV",
                "details": {"approved_by": "admin"},
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "created_at": "2025-10-28T10:30:00Z",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@example.com"
                }
            }
        }


class ActivityLogListResponse(BaseModel):
    """Schema for paginated activity log list (old format - deprecated)"""
    total: int
    items: list[ActivityLogResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "items": [
                    {
                        "id": 1,
                        "timestamp": "2025-10-28T10:30:00Z",
                        "action_type": "DEVICE_APPROVED",
                        "entity_type": "device"
                    }
                ]
            }
        }


class ActivityStatsResponse(BaseModel):
    """Schema for activity statistics response"""
    today: int = Field(..., description="Number of activities today")
    this_week: int = Field(..., description="Number of activities this week")
    this_month: int = Field(..., description="Number of activities this month")
    by_type: Dict[str, int] = Field(..., description="Activity count by action type")
    by_entity: Dict[str, int] = Field(..., description="Activity count by entity type")

    class Config:
        json_schema_extra = {
            "example": {
                "today": 42,
                "this_week": 187,
                "this_month": 823,
                "by_type": {
                    "DEVICE_APPROVED": 25,
                    "CONTENT_UPLOADED": 103,
                    "PLAYLIST_CREATED": 15
                },
                "by_entity": {
                    "device": 45,
                    "content": 120,
                    "playlist": 22
                }
            }
        }
