"""
Widget Schemas
Pydantic models for widget validation and serialization

Widget types supported:
- clock: Display time and date
- weather: Weather information
- calendar: Calendar events
- countdown: Countdown timers
- iframe: Embed external URLs
- text: Text message displays
- pms: Property Management System integration
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator


# =============================================================================
# WIDGET TYPE CONFIGURATION SCHEMAS
# =============================================================================

class ClockConfig(BaseModel):
    """Clock widget configuration"""
    format: str = Field(default="HH:mm:ss", description="Time format string")
    timezone: str = Field(default="UTC", description="Timezone (e.g., 'Asia/Jakarta')")
    show_date: bool = Field(default=True, description="Show date alongside time")
    date_format: str = Field(default="YYYY-MM-DD", description="Date format string")
    font_size: int = Field(default=48, ge=12, le=200, description="Font size in pixels")
    color: str = Field(default="#FFFFFF", description="Text color (hex)")


class WeatherConfig(BaseModel):
    """Weather widget configuration"""
    api_key: str = Field(..., description="Weather API key (e.g., OpenWeatherMap)")
    location: str = Field(..., description="Location (city name or coordinates)")
    units: str = Field(default="metric", description="Units: metric, imperial, or kelvin")
    show_forecast: bool = Field(default=True, description="Show forecast days")
    forecast_days: int = Field(default=3, ge=1, le=7, description="Number of forecast days")
    refresh_interval: int = Field(default=1800, ge=300, description="Refresh interval in seconds")


class CalendarConfig(BaseModel):
    """Calendar widget configuration"""
    calendar_url: Optional[HttpUrl] = Field(None, description="iCal/ICS feed URL")
    display_mode: str = Field(default="upcoming", description="Display mode: upcoming, month, week")
    max_events: int = Field(default=5, ge=1, le=20, description="Maximum events to display")
    show_past_events: bool = Field(default=False, description="Show past events")
    days_ahead: int = Field(default=7, ge=1, le=90, description="Days to look ahead")


class CountdownConfig(BaseModel):
    """Countdown timer configuration"""
    target_date: datetime = Field(..., description="Target date/time for countdown")
    title: str = Field(..., max_length=200, description="Countdown title")
    format: str = Field(default="DHms", description="Format: D=days, H=hours, m=minutes, s=seconds")
    show_when_passed: bool = Field(default=False, description="Show after target date passed")
    passed_message: Optional[str] = Field(None, description="Message when countdown reaches zero")


class IFrameConfig(BaseModel):
    """iFrame widget configuration"""
    url: HttpUrl = Field(..., description="URL to embed")
    refresh_interval: int = Field(default=0, ge=0, description="Auto-refresh interval (0=disabled)")
    allow_interaction: bool = Field(default=True, description="Allow user interaction with iframe")
    sandbox_mode: bool = Field(default=False, description="Enable iframe sandbox security")


class TextConfig(BaseModel):
    """Text message widget configuration"""
    message: str = Field(..., max_length=1000, description="Text message to display")
    font_size: int = Field(default=32, ge=12, le=200, description="Font size in pixels")
    color: str = Field(default="#FFFFFF", description="Text color (hex)")
    background_color: Optional[str] = Field(None, description="Background color (hex)")
    alignment: str = Field(default="center", description="Text alignment: left, center, right")
    animation: Optional[str] = Field(None, description="Animation type: fade, slide, scroll")


class PMSConfig(BaseModel):
    """Property Management System widget configuration"""
    firebird_config_id: int = Field(..., description="Firebird configuration ID")
    query_template: str = Field(..., description="SQL query template")
    display_fields: List[str] = Field(..., description="Fields to display from query result")
    refresh_interval: int = Field(default=60, ge=10, description="Refresh interval in seconds")
    format_template: Optional[str] = Field(None, description="HTML template for formatting data")


# =============================================================================
# BASE WIDGET SCHEMAS
# =============================================================================

class WidgetBase(BaseModel):
    """Base widget fields"""
    widget_type: str = Field(..., description="Widget type: clock, weather, calendar, countdown, iframe, text, pms")
    widget_name: str = Field(..., max_length=100, description="Display name for widget")
    data_source_type: str = Field(default="internal", description="Data source: internal, external, mixed")
    data_source_id: Optional[int] = Field(None, description="External data source ID if applicable")
    template: Optional[str] = Field(None, description="HTML template for rendering")
    styles: Optional[Dict[str, Any]] = Field(None, description="Custom CSS styles (JSON)")
    position: str = Field(default="top-left", description="Position: top-left, top-right, bottom-left, bottom-right, center")
    is_overlay: bool = Field(default=True, description="True=overlay on content, False=in sequence")
    refresh_interval: int = Field(default=300, ge=10, description="Refresh interval in seconds")
    is_active: bool = Field(default=True, description="Whether widget is active")

    @validator('widget_type')
    def validate_widget_type(cls, v):
        valid_types = ['clock', 'weather', 'calendar', 'countdown', 'iframe', 'text', 'pms']
        if v not in valid_types:
            raise ValueError(f"Invalid widget_type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('data_source_type')
    def validate_data_source_type(cls, v):
        valid_types = ['internal', 'external', 'mixed']
        if v not in valid_types:
            raise ValueError(f"Invalid data_source_type. Must be one of: {', '.join(valid_types)}")
        return v

    @validator('position')
    def validate_position(cls, v):
        valid_positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center', 'full']
        if v not in valid_positions:
            raise ValueError(f"Invalid position. Must be one of: {', '.join(valid_positions)}")
        return v


class WidgetCreate(WidgetBase):
    """Schema for creating a widget"""
    # Type-specific configuration (one of these should be provided)
    clock_config: Optional[ClockConfig] = None
    weather_config: Optional[WeatherConfig] = None
    calendar_config: Optional[CalendarConfig] = None
    countdown_config: Optional[CountdownConfig] = None
    iframe_config: Optional[IFrameConfig] = None
    text_config: Optional[TextConfig] = None
    pms_config: Optional[PMSConfig] = None

    @validator('clock_config', 'weather_config', 'calendar_config', 'countdown_config', 'iframe_config', 'text_config', 'pms_config')
    def validate_config_match(cls, v, values):
        """Ensure configuration matches widget_type"""
        if 'widget_type' not in values:
            return v

        widget_type = values['widget_type']
        config_map = {
            'clock': 'clock_config',
            'weather': 'weather_config',
            'calendar': 'calendar_config',
            'countdown': 'countdown_config',
            'iframe': 'iframe_config',
            'text': 'text_config',
            'pms': 'pms_config'
        }

        # Note: Validation logic can be enhanced to ensure correct config is provided
        return v


class WidgetUpdate(BaseModel):
    """Schema for updating a widget"""
    widget_name: Optional[str] = Field(None, max_length=100)
    data_source_type: Optional[str] = None
    data_source_id: Optional[int] = None
    template: Optional[str] = None
    styles: Optional[Dict[str, Any]] = None
    position: Optional[str] = None
    is_overlay: Optional[bool] = None
    refresh_interval: Optional[int] = Field(None, ge=10)
    is_active: Optional[bool] = None

    # Type-specific configuration updates
    clock_config: Optional[ClockConfig] = None
    weather_config: Optional[WeatherConfig] = None
    calendar_config: Optional[CalendarConfig] = None
    countdown_config: Optional[CountdownConfig] = None
    iframe_config: Optional[IFrameConfig] = None
    text_config: Optional[TextConfig] = None
    pms_config: Optional[PMSConfig] = None


class WidgetResponse(BaseModel):
    """Schema for widget response"""
    id: int
    widget_type: str
    widget_name: str
    data_source_type: str
    data_source_id: Optional[int]
    template: Optional[str]
    styles: Optional[Dict[str, Any]]
    position: str
    is_overlay: bool
    refresh_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Configuration (stored as JSON in styles or separate field)
    config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "widget_type": "clock",
                "widget_name": "Main Clock",
                "data_source_type": "internal",
                "data_source_id": None,
                "template": None,
                "styles": {"backgroundColor": "#000000"},
                "position": "top-right",
                "is_overlay": True,
                "refresh_interval": 60,
                "is_active": True,
                "created_at": "2025-10-27T10:00:00Z",
                "updated_at": "2025-10-27T10:00:00Z",
                "config": {
                    "format": "HH:mm:ss",
                    "timezone": "Asia/Jakarta",
                    "show_date": True
                }
            }
        }


# =============================================================================
# WIDGET ASSIGNMENT SCHEMAS
# =============================================================================

class WidgetAssignDevices(BaseModel):
    """Assign widget to devices"""
    device_ids: List[int] = Field(..., min_length=1, description="List of device IDs")


class WidgetUnassignDevices(BaseModel):
    """Unassign widget from devices"""
    device_ids: List[int] = Field(..., min_length=1, description="List of device IDs to unassign")


class WidgetAssignmentResponse(BaseModel):
    """Widget assignment information"""
    widget_id: int
    device_id: int
    device_name: str
    assigned_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# WIDGET TYPES INFO SCHEMA
# =============================================================================

class WidgetTypeInfo(BaseModel):
    """Information about a widget type"""
    type: str
    name: str
    description: str
    icon: str
    config_schema: Dict[str, Any]
    requires_external_service: bool


class WidgetTypesResponse(BaseModel):
    """Response containing all available widget types"""
    types: List[WidgetTypeInfo]

    class Config:
        json_schema_extra = {
            "example": {
                "types": [
                    {
                        "type": "clock",
                        "name": "Clock",
                        "description": "Display time and date",
                        "icon": "clock",
                        "config_schema": {"format": "string", "timezone": "string"},
                        "requires_external_service": False
                    }
                ]
            }
        }


# =============================================================================
# PREVIEW SCHEMA
# =============================================================================

class WidgetPreviewRequest(BaseModel):
    """Request to preview a widget configuration"""
    widget_type: str
    config: Dict[str, Any]


class WidgetPreviewResponse(BaseModel):
    """Preview response with rendered widget data"""
    rendered_html: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
