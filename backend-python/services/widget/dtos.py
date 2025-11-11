"""
Widget DTOs
Request and Response models for widget endpoints
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Widget DTOs
# ============================================================================

class CreateWidgetRequest(BaseModel):
    """Request to create a new widget"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    widget_type: str = Field(..., description="Widget type: clock, weather, news, hotel_info, custom")
    config: Dict[str, Any] = Field(..., description="Widget-specific configuration")
    layout: Optional[Dict[str, Any]] = Field(None, description="Position and size settings")
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Main Clock",
                "description": "Digital clock widget for lobby display",
                "widget_type": "clock",
                "config": {
                    "format": "24h",
                    "show_seconds": True,
                    "timezone": "Asia/Jakarta",
                    "font_size": 48,
                    "color": "#FFFFFF"
                },
                "layout": {
                    "position": "top-right",
                    "width": 300,
                    "height": 100,
                    "x": 10,
                    "y": 10
                },
                "is_active": True
            }
        }


class UpdateWidgetRequest(BaseModel):
    """Request to update existing widget"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    widget_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "config": {
                    "format": "12h",
                    "show_seconds": False
                },
                "is_active": True
            }
        }


class WidgetResponse(BaseModel):
    """Widget response model"""
    id: int
    organization_id: int
    name: str
    description: Optional[str]
    widget_type: str
    config: Dict[str, Any]
    layout: Optional[Dict[str, Any]]
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WidgetListResponse(BaseModel):
    """List of widgets response"""
    widgets: List[WidgetResponse]
    total: int


# ============================================================================
# Playlist Widget DTOs
# ============================================================================

class AssignWidgetToPlaylistRequest(BaseModel):
    """Request to assign widget to playlist"""
    widget_id: int
    position: int = 0
    display_duration: Optional[int] = Field(None, description="Duration in seconds, NULL for always show")
    z_index: int = Field(100, description="Layer order, higher = on top")

    class Config:
        json_schema_extra = {
            "example": {
                "widget_id": 1,
                "position": 0,
                "display_duration": None,
                "z_index": 100
            }
        }


class UpdatePlaylistWidgetRequest(BaseModel):
    """Request to update playlist widget settings"""
    position: Optional[int] = None
    display_duration: Optional[int] = None
    z_index: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "position": 1,
                "z_index": 150
            }
        }


class PlaylistWidgetResponse(BaseModel):
    """Playlist widget response model"""
    id: int
    playlist_id: int
    widget_id: int
    position: int
    display_duration: Optional[int]
    z_index: int
    created_at: datetime

    # Include widget details
    widget: Optional[WidgetResponse] = None

    class Config:
        from_attributes = True


class PlaylistWidgetListResponse(BaseModel):
    """List of playlist widgets"""
    playlist_widgets: List[PlaylistWidgetResponse]
    total: int


# ============================================================================
# Widget Type Configuration Schemas (for validation)
# ============================================================================

class ClockWidgetConfig(BaseModel):
    """Clock widget configuration schema"""
    format: str = Field("24h", description="12h or 24h")
    show_seconds: bool = True
    timezone: str = "Asia/Jakarta"
    font_size: int = 48
    color: str = "#FFFFFF"
    background_color: Optional[str] = None


class WeatherWidgetConfig(BaseModel):
    """Weather widget configuration schema"""
    location: str = Field(..., description="City name or coordinates")
    api_key: Optional[str] = Field(None, description="Weather API key")
    units: str = Field("metric", description="metric or imperial")
    refresh_interval: int = Field(1800, description="Refresh interval in seconds")
    show_forecast: bool = True
    font_size: int = 24


class HotelInfoWidgetConfig(BaseModel):
    """Hotel info widget configuration schema"""
    info_type: str = Field(..., description="checkin_time, checkout_time, wifi_info, etc")
    title: str
    content: str
    icon: Optional[str] = None
    font_size: int = 24
    auto_rotate: bool = False
    rotate_interval: Optional[int] = None


class NewsTickerWidgetConfig(BaseModel):
    """News ticker widget configuration schema"""
    source: str = Field("manual", description="manual, rss, api")
    items: List[str] = Field(default_factory=list, description="News items")
    rss_url: Optional[str] = None
    scroll_speed: int = Field(50, description="Pixels per second")
    direction: str = Field("left", description="left or right")
    font_size: int = 24


class CustomWidgetConfig(BaseModel):
    """Custom widget configuration schema"""
    html_content: Optional[str] = None
    css_styles: Optional[str] = None
    javascript: Optional[str] = None
    data_source: Optional[str] = None
