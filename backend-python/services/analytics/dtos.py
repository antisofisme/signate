"""
Analytics DTOs (Data Transfer Objects)
Request and Response models for Analytics API
Phase 2 Day 2 - Analytics Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# REQUEST DTOs
# ============================================================================

class AnalyticsQueryRequest(BaseModel):
    """Request model for analytics queries"""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")


class TimelineQueryRequest(BaseModel):
    """Request model for timeline analytics"""
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    interval: Optional[str] = Field("day", description="Grouping interval (day, week, month)")


class PlaybackLogRequest(BaseModel):
    """Request model for logging playback"""
    content_id: int = Field(..., description="Content ID being played")
    device_id: int = Field(..., description="Device ID playing content")
    playlist_id: Optional[int] = Field(None, description="Playlist ID (if part of playlist)")
    organization_id: int = Field(..., description="Organization ID")
    expected_duration: Optional[int] = Field(None, description="Expected duration in seconds")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")
    playback_quality: Optional[str] = Field(None, description="Playback quality (SD, HD, FHD)")


class PlaybackEndRequest(BaseModel):
    """Request model for ending playback"""
    duration_seconds: int = Field(..., ge=0, description="Actual playback duration in seconds")
    completed: bool = Field(False, description="Whether playback completed successfully")
    error_count: Optional[int] = Field(0, description="Number of errors during playback")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")


# ============================================================================
# RESPONSE DTOs
# ============================================================================

class ContentPerformanceResponse(BaseModel):
    """Response model for content performance"""
    content_id: int
    title: str
    content_type: str
    total_plays: int
    completed_plays: int
    avg_duration_seconds: Optional[float]
    last_played_at: Optional[datetime]
    unique_devices: int
    completion_rate: Optional[float]


class DeviceEngagementResponse(BaseModel):
    """Response model for device engagement"""
    device_id: int
    device_name: str
    total_plays: int
    unique_content: int
    last_playback_at: Optional[datetime]
    total_watch_time_seconds: int
    total_watch_time_hours: float


class PlaybackStatsResponse(BaseModel):
    """Response model for overall playback statistics"""
    total_plays: int
    completed_plays: int
    unique_content: int
    unique_devices: int
    total_watch_time_seconds: int
    total_watch_time_hours: float
    completion_rate: float
    period_start: str
    period_end: str


class TimelineDataPoint(BaseModel):
    """Single data point in timeline"""
    period: datetime
    total_plays: int
    completed_plays: int
    unique_content: int
    unique_devices: int
    total_watch_time_seconds: int


class PlaybackTimelineResponse(BaseModel):
    """Response model for playback timeline"""
    data: List[TimelineDataPoint]
    interval: str
    start_date: str
    end_date: str


class PlaybackLogResponse(BaseModel):
    """Response model for playback log"""
    id: int
    content_id: int
    device_id: int
    playlist_id: Optional[int]
    organization_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    expected_duration: Optional[int]
    completed: bool
    playback_quality: Optional[str]
    error_count: int
    created_at: datetime


class AnalyticsDashboardResponse(BaseModel):
    """Complete analytics dashboard response"""
    stats: PlaybackStatsResponse
    top_content: List[ContentPerformanceResponse]
    top_devices: List[DeviceEngagementResponse]
