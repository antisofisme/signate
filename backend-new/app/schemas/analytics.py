"""
Analytics Schemas
=================

Pydantic schemas for analytics and metrics endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, date


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class DateRangeFilter(BaseModel):
    """Date range filter for analytics queries"""
    start_date: Optional[date] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="End date (YYYY-MM-DD)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        }
    }


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class DashboardMetrics(BaseModel):
    """Dashboard overview metrics"""
    total_devices: int = Field(..., description="Total registered devices")
    active_devices: int = Field(..., description="Devices active in last 24h")
    offline_devices: int = Field(..., description="Devices offline")
    total_content: int = Field(..., description="Total content items")
    total_playlists: int = Field(..., description="Total playlists")
    total_organizations: int = Field(..., description="Total organizations")
    storage_used_mb: float = Field(..., description="Storage used in MB")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_devices": 50,
                "active_devices": 35,
                "offline_devices": 15,
                "total_content": 150,
                "total_playlists": 25,
                "total_organizations": 5,
                "storage_used_mb": 1024.5
            }
        }
    }


class ContentPerformance(BaseModel):
    """Content performance metrics"""
    content_id: int = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    content_type: str = Field(..., description="Content type (video, image, webpage)")
    assigned_playlists: int = Field(..., description="Number of playlists using this content")
    devices_showing: int = Field(..., description="Number of devices currently showing this content")
    file_size_mb: Optional[float] = Field(None, description="File size in MB")
    created_at: datetime = Field(..., description="Content creation date")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "content_id": 1,
                "title": "Product Showcase Video",
                "content_type": "video",
                "assigned_playlists": 3,
                "devices_showing": 10,
                "file_size_mb": 25.5,
                "created_at": "2024-01-01T12:00:00"
            }
        }
    }


class ContentStats(BaseModel):
    """Content statistics response"""
    content: ContentPerformance
    usage_stats: Dict[str, Any] = Field(default={}, description="Usage statistics")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": {},
                "usage_stats": {
                    "total_plays": 150,
                    "total_duration_hours": 25.5,
                    "avg_completion_rate": 85.3
                }
            }
        }
    }


class DeviceActivity(BaseModel):
    """Device activity metrics"""
    device_id: int = Field(..., description="Device ID")
    device_name: str = Field(..., description="Device name")
    status: str = Field(..., description="Device status (online, offline)")
    last_seen: Optional[datetime] = Field(None, description="Last heartbeat time")
    current_playlist: Optional[str] = Field(None, description="Currently assigned playlist")
    uptime_hours: Optional[float] = Field(None, description="Uptime in hours")
    location: Optional[str] = Field(None, description="Device location")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "device_id": 5,
                "device_name": "Lobby Display 1",
                "status": "online",
                "last_seen": "2024-01-01T12:00:00",
                "current_playlist": "Default Playlist",
                "uptime_hours": 72.5,
                "location": "Main Lobby"
            }
        }
    }


class DeviceStats(BaseModel):
    """Device statistics response"""
    device: DeviceActivity
    activity_summary: Dict[str, Any] = Field(default={}, description="Activity summary")

    model_config = {
        "json_schema_extra": {
            "example": {
                "device": {},
                "activity_summary": {
                    "total_heartbeats": 1440,
                    "avg_uptime_percent": 98.5,
                    "last_reboot": "2024-01-01T00:00:00"
                }
            }
        }
    }


class TrendingContent(BaseModel):
    """Trending content item"""
    content_id: int = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    content_type: str = Field(..., description="Content type")
    score: float = Field(..., description="Trending score")
    devices_count: int = Field(..., description="Number of devices showing this content")

    model_config = {
        "json_schema_extra": {
            "example": {
                "content_id": 1,
                "title": "New Product Launch",
                "content_type": "video",
                "score": 95.5,
                "devices_count": 25
            }
        }
    }


class TrendingResponse(BaseModel):
    """Trending content response"""
    trending: list[TrendingContent] = Field(default=[], description="List of trending content")
    period: str = Field(..., description="Time period (24h, 7d, 30d)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "trending": [],
                "period": "24h"
            }
        }
    }


class OrganizationStats(BaseModel):
    """Organization-specific statistics"""
    organization_id: int = Field(..., description="Organization ID")
    device_count: int = Field(..., description="Total devices")
    active_devices: int = Field(..., description="Active devices")
    content_count: int = Field(..., description="Total content items")
    playlist_count: int = Field(..., description="Total playlists")
    storage_used_mb: float = Field(..., description="Storage used in MB")
    storage_limit_mb: Optional[float] = Field(None, description="Storage limit in MB")

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_id": 1,
                "device_count": 10,
                "active_devices": 8,
                "content_count": 50,
                "playlist_count": 5,
                "storage_used_mb": 512.5,
                "storage_limit_mb": 5120.0
            }
        }
    }
