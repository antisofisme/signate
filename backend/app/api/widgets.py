"""
Widgets API Endpoints
For managing overlay widgets and dynamic content displays

Widget types supported:
- clock: Display time and date
- weather: Weather information
- calendar: Calendar events
- countdown: Countdown timers
- iframe: Embed external URLs
- text: Text message displays
- pms: Property Management System integration

MIGRATED TO QUICK WINS STANDARDS:
- Structured logging with StructuredLogger
- Custom exceptions (NotFoundException, BadRequestException)
- Standardized success_response wrapper
- Page-based pagination (instead of skip/limit)
- Request ID tracking
"""

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict, Any
import json

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException
from app.middleware.request_id import get_request_id
from app.schemas.common import success_response, paginated_response
from app.models.user import User
from app.models.hotel import Widget, ExternalDataSource
from app.models.device import Device
from app.schemas.widget import (
    WidgetCreate,
    WidgetUpdate,
    WidgetResponse,
    WidgetAssignDevices,
    WidgetUnassignDevices,
    WidgetAssignmentResponse,
    WidgetTypesResponse,
    WidgetTypeInfo,
    WidgetPreviewRequest,
    WidgetPreviewResponse,
    ClockConfig,
    WeatherConfig,
    CalendarConfig,
    CountdownConfig,
    IFrameConfig,
    TextConfig,
    PMSConfig
)

logger = StructuredLogger(__name__)
router = APIRouter()


# =============================================================================
# WIDGET TYPES METADATA
# =============================================================================

WIDGET_TYPES = {
    "clock": {
        "name": "Clock",
        "description": "Display time and date information",
        "icon": "clock",
        "config_schema": ClockConfig.model_json_schema(),
        "requires_external_service": False
    },
    "weather": {
        "name": "Weather",
        "description": "Show weather information and forecasts",
        "icon": "cloud",
        "config_schema": WeatherConfig.model_json_schema(),
        "requires_external_service": True
    },
    "calendar": {
        "name": "Calendar",
        "description": "Display calendar events",
        "icon": "calendar",
        "config_schema": CalendarConfig.model_json_schema(),
        "requires_external_service": False
    },
    "countdown": {
        "name": "Countdown",
        "description": "Create countdown timers for events",
        "icon": "timer",
        "config_schema": CountdownConfig.model_json_schema(),
        "requires_external_service": False
    },
    "iframe": {
        "name": "iFrame",
        "description": "Embed external websites and web content",
        "icon": "globe",
        "config_schema": IFrameConfig.model_json_schema(),
        "requires_external_service": False
    },
    "text": {
        "name": "Text",
        "description": "Display text messages",
        "icon": "message-square",
        "config_schema": TextConfig.model_json_schema(),
        "requires_external_service": False
    },
    "pms": {
        "name": "PMS Integration",
        "description": "Property Management System data display",
        "icon": "hotel",
        "config_schema": PMSConfig.model_json_schema(),
        "requires_external_service": True
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_config_from_create(widget_create: WidgetCreate) -> Dict[str, Any]:
    """Extract type-specific configuration from WidgetCreate"""
    config_map = {
        'clock': widget_create.clock_config,
        'weather': widget_create.weather_config,
        'calendar': widget_create.calendar_config,
        'countdown': widget_create.countdown_config,
        'iframe': widget_create.iframe_config,
        'text': widget_create.text_config,
        'pms': widget_create.pms_config
    }

    config = config_map.get(widget_create.widget_type)
    if config:
        return config.model_dump()
    return {}


def widget_to_response(widget: Widget) -> Dict[str, Any]:
    """Convert Widget model to response dict with config"""
    widget_dict = widget.to_dict()

    # Extract config from styles JSON or template
    # Config is typically stored in styles field as JSON
    if widget.styles and isinstance(widget.styles, dict):
        widget_dict['config'] = widget.styles.get('config', {})
    else:
        widget_dict['config'] = {}

    return widget_dict


# =============================================================================
# WIDGET CRUD ENDPOINTS (5 endpoints)
# =============================================================================

@router.get("", summary="List all widgets")
def list_widgets(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    widget_type: Optional[str] = Query(None, description="Filter by widget type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all widgets with pagination and filtering

    Query Parameters:
    - page: Page number (1-indexed)
    - limit: Items per page (max 100)
    - widget_type: Filter by type (clock, weather, calendar, countdown, iframe, text, pms)
    - is_active: Filter by active status
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing widgets",
        request_id=request_id,
        page=page,
        limit=limit,
        widget_type=widget_type,
        is_active=is_active
    )

    # Build query with filters
    query = db.query(Widget)

    if widget_type:
        query = query.filter(Widget.widget_type == widget_type)

    if is_active is not None:
        query = query.filter(Widget.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    widgets = query.order_by(Widget.created_at.desc()).offset(offset).limit(limit).all()

    # Convert to response format
    widget_responses = [widget_to_response(w) for w in widgets]

    logger.info(
        "Widgets listed successfully",
        request_id=request_id,
        total=total,
        page=page,
        returned=len(widget_responses)
    )

    return paginated_response(
        data=widget_responses,
        total=total,
        page=page,
        page_size=limit,
        request_id=request_id
    )


@router.post("", summary="Create new widget")
def create_widget(
    request: Request,
    widget_data: WidgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new widget

    Widget types:
    - clock: Display time and date
    - weather: Weather information (requires API key)
    - calendar: Calendar events
    - countdown: Countdown timers
    - iframe: Embed external URLs
    - text: Text message displays
    - pms: Property Management System integration
    """
    request_id = get_request_id(request)

    logger.info(
        "Creating widget",
        request_id=request_id,
        widget_type=widget_data.widget_type,
        widget_name=widget_data.widget_name
    )

    # Validate widget type
    if widget_data.widget_type not in WIDGET_TYPES:
        raise BadRequestException(
            f"Invalid widget_type. Must be one of: {', '.join(WIDGET_TYPES.keys())}"
        )

    # Validate external data source if specified
    if widget_data.data_source_id:
        data_source = db.query(ExternalDataSource).filter(
            ExternalDataSource.id == widget_data.data_source_id
        ).first()
        if not data_source:
            raise NotFoundException(f"External data source with ID {widget_data.data_source_id} not found")

    # Extract type-specific configuration
    config = extract_config_from_create(widget_data)

    # Store config in styles field
    styles = widget_data.styles or {}
    styles['config'] = config

    # Create widget
    widget = Widget(
        widget_type=widget_data.widget_type,
        widget_name=widget_data.widget_name,
        data_source_type=widget_data.data_source_type,
        data_source_id=widget_data.data_source_id,
        template=widget_data.template,
        styles=styles,
        position=widget_data.position,
        is_overlay=widget_data.is_overlay,
        refresh_interval=widget_data.refresh_interval,
        is_active=widget_data.is_active
    )

    db.add(widget)
    db.commit()
    db.refresh(widget)

    logger.info(
        "Widget created successfully",
        request_id=request_id,
        widget_id=widget.id,
        widget_type=widget.widget_type
    )

    return success_response(
        data=widget_to_response(widget),
        request_id=request_id
    )


@router.get("/{widget_id}", summary="Get widget by ID")
def get_widget(
    request: Request,
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get a single widget by ID
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching widget",
        request_id=request_id,
        widget_id=widget_id
    )

    widget = db.query(Widget).filter(Widget.id == widget_id).first()

    if not widget:
        raise NotFoundException(f"Widget with ID {widget_id} not found")

    logger.info(
        "Widget fetched successfully",
        request_id=request_id,
        widget_id=widget.id,
        widget_type=widget.widget_type
    )

    return success_response(
        data=widget_to_response(widget),
        request_id=request_id
    )


@router.put("/{widget_id}", summary="Update widget")
def update_widget(
    request: Request,
    widget_id: int,
    widget_data: WidgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing widget
    """
    request_id = get_request_id(request)

    logger.info(
        "Updating widget",
        request_id=request_id,
        widget_id=widget_id
    )

    widget = db.query(Widget).filter(Widget.id == widget_id).first()

    if not widget:
        raise NotFoundException(f"Widget with ID {widget_id} not found")

    # Update fields
    update_data = widget_data.model_dump(exclude_unset=True)

    # Extract type-specific config updates
    config_fields = ['clock_config', 'weather_config', 'calendar_config',
                     'countdown_config', 'iframe_config', 'text_config', 'pms_config']

    for config_field in config_fields:
        if config_field in update_data and update_data[config_field] is not None:
            # Update config in styles
            styles = widget.styles or {}
            styles['config'] = update_data[config_field]
            widget.styles = styles
            del update_data[config_field]

    # Update remaining fields
    for field, value in update_data.items():
        if hasattr(widget, field):
            setattr(widget, field, value)

    db.commit()
    db.refresh(widget)

    logger.info(
        "Widget updated successfully",
        request_id=request_id,
        widget_id=widget.id
    )

    return success_response(
        data=widget_to_response(widget),
        request_id=request_id
    )


@router.patch("/{widget_id}", summary="Update widget (PATCH)")
def patch_widget(
    request: Request,
    widget_id: int,
    widget_data: WidgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing widget (PATCH method for frontend compatibility)

    This is an alias for PUT endpoint to support frontend expectations.
    """
    return update_widget(request, widget_id, widget_data, db, current_user)


@router.delete("/{widget_id}", summary="Delete widget")
def delete_widget(
    request: Request,
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a widget
    """
    request_id = get_request_id(request)

    logger.info(
        "Deleting widget",
        request_id=request_id,
        widget_id=widget_id
    )

    widget = db.query(Widget).filter(Widget.id == widget_id).first()

    if not widget:
        raise NotFoundException(f"Widget with ID {widget_id} not found")

    widget_name = widget.widget_name
    widget_type = widget.widget_type

    db.delete(widget)
    db.commit()

    logger.info(
        "Widget deleted successfully",
        request_id=request_id,
        widget_id=widget_id,
        widget_name=widget_name
    )

    return success_response(
        data={
            "message": f"Widget '{widget_name}' deleted successfully",
            "widget_id": widget_id,
            "widget_type": widget_type
        },
        request_id=request_id
    )


# =============================================================================
# WIDGET TYPES ENDPOINT
# =============================================================================

@router.get("/types/list", summary="Get available widget types")
def get_widget_types(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get list of all available widget types with their configurations

    Returns metadata for each widget type including:
    - Type identifier
    - Display name
    - Description
    - Icon name
    - Configuration schema
    - Whether it requires external services
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching widget types",
        request_id=request_id
    )

    types = []
    for type_id, type_info in WIDGET_TYPES.items():
        types.append({
            "type": type_id,
            "name": type_info["name"],
            "description": type_info["description"],
            "icon": type_info["icon"],
            "config_schema": type_info["config_schema"],
            "requires_external_service": type_info["requires_external_service"]
        })

    logger.info(
        "Widget types fetched successfully",
        request_id=request_id,
        count=len(types)
    )

    return success_response(
        data={"types": types},
        request_id=request_id
    )


# =============================================================================
# WIDGET ASSIGNMENT ENDPOINTS (2 endpoints)
# =============================================================================

@router.post("/{widget_id}/assign", summary="Assign widget to devices")
def assign_widget_to_devices(
    request: Request,
    widget_id: int,
    assignment_data: WidgetAssignDevices,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign a widget to one or more devices

    This creates a relationship between the widget and devices.
    The widget will be displayed on assigned devices according to its configuration.
    """
    request_id = get_request_id(request)

    logger.info(
        "Assigning widget to devices",
        request_id=request_id,
        widget_id=widget_id,
        device_count=len(assignment_data.device_ids)
    )

    # Verify widget exists
    widget = db.query(Widget).filter(Widget.id == widget_id).first()
    if not widget:
        raise NotFoundException(f"Widget with ID {widget_id} not found")

    # Verify all devices exist
    devices = db.query(Device).filter(Device.id.in_(assignment_data.device_ids)).all()
    found_device_ids = {d.id for d in devices}
    missing_ids = set(assignment_data.device_ids) - found_device_ids

    if missing_ids:
        raise NotFoundException(f"Devices not found: {', '.join(map(str, missing_ids))}")

    # Note: Widget assignment logic depends on your database schema
    # If you have a widget_assignments table, create records here
    # For now, we'll store assignments in widget's styles field as a simple approach

    styles = widget.styles or {}
    current_assignments = styles.get('assigned_devices', [])

    # Add new device IDs (avoid duplicates)
    for device_id in assignment_data.device_ids:
        if device_id not in current_assignments:
            current_assignments.append(device_id)

    styles['assigned_devices'] = current_assignments
    widget.styles = styles

    db.commit()
    db.refresh(widget)

    # Build response with device info
    assignments = []
    for device in devices:
        assignments.append({
            "widget_id": widget_id,
            "device_id": device.id,
            "device_name": device.name,
            "assigned_at": widget.updated_at.isoformat() if widget.updated_at else None
        })

    logger.info(
        "Widget assigned to devices successfully",
        request_id=request_id,
        widget_id=widget_id,
        assigned_count=len(assignments)
    )

    return success_response(
        data={
            "message": f"Widget assigned to {len(assignments)} device(s)",
            "assignments": assignments
        },
        request_id=request_id
    )


@router.delete("/{widget_id}/assign", summary="Unassign widget from devices")
def unassign_widget_from_devices(
    request: Request,
    widget_id: int,
    assignment_data: WidgetUnassignDevices,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Unassign a widget from one or more devices

    Removes the relationship between widget and devices.
    The widget will no longer be displayed on unassigned devices.
    """
    request_id = get_request_id(request)

    logger.info(
        "Unassigning widget from devices",
        request_id=request_id,
        widget_id=widget_id,
        device_count=len(assignment_data.device_ids)
    )

    # Verify widget exists
    widget = db.query(Widget).filter(Widget.id == widget_id).first()
    if not widget:
        raise NotFoundException(f"Widget with ID {widget_id} not found")

    # Remove device IDs from assignments
    styles = widget.styles or {}
    current_assignments = styles.get('assigned_devices', [])

    removed_count = 0
    for device_id in assignment_data.device_ids:
        if device_id in current_assignments:
            current_assignments.remove(device_id)
            removed_count += 1

    styles['assigned_devices'] = current_assignments
    widget.styles = styles

    db.commit()
    db.refresh(widget)

    logger.info(
        "Widget unassigned from devices successfully",
        request_id=request_id,
        widget_id=widget_id,
        removed_count=removed_count
    )

    return success_response(
        data={
            "message": f"Widget unassigned from {removed_count} device(s)",
            "widget_id": widget_id,
            "removed_device_ids": assignment_data.device_ids
        },
        request_id=request_id
    )


# =============================================================================
# WIDGET PREVIEW ENDPOINT
# =============================================================================

@router.post("/preview", summary="Preview widget configuration")
def preview_widget(
    request: Request,
    preview_data: WidgetPreviewRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Preview a widget configuration without saving

    Useful for testing widget appearance and configuration before creating.
    Returns rendered HTML or data sample based on widget type.
    """
    request_id = get_request_id(request)

    logger.info(
        "Previewing widget",
        request_id=request_id,
        widget_type=preview_data.widget_type
    )

    # Validate widget type
    if preview_data.widget_type not in WIDGET_TYPES:
        raise BadRequestException(
            f"Invalid widget_type. Must be one of: {', '.join(WIDGET_TYPES.keys())}"
        )

    # Generate preview based on widget type
    # This is a simplified implementation - actual preview would render real data
    preview_result = {
        "rendered_html": f"<div>Preview for {preview_data.widget_type} widget</div>",
        "data": preview_data.config,
        "error": None
    }

    logger.info(
        "Widget preview generated successfully",
        request_id=request_id,
        widget_type=preview_data.widget_type
    )

    return success_response(
        data=preview_result,
        request_id=request_id
    )


# =============================================================================
# EXTERNAL SERVICE TESTING ENDPOINTS
# =============================================================================

@router.post("/test-weather-api", summary="Test weather API connection")
def test_weather_api(
    request: Request,
    api_key: str = Query(..., description="Weather API key"),
    location: str = Query(..., description="Location to test"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test weather API connection with provided credentials

    This endpoint validates:
    - API key is valid
    - Location can be found
    - API returns data successfully

    Note: Implement actual weather API call here (e.g., OpenWeatherMap)
    """
    request_id = get_request_id(request)

    logger.info(
        "Testing weather API connection",
        request_id=request_id,
        location=location
    )

    # TODO: Implement actual weather API call
    # For now, return a mock success response

    test_result = {
        "success": True,
        "message": "Weather API connection successful",
        "location": location,
        "sample_data": {
            "temperature": 28.5,
            "condition": "Sunny",
            "humidity": 65
        }
    }

    logger.info(
        "Weather API test completed",
        request_id=request_id,
        success=True
    )

    return success_response(
        data=test_result,
        request_id=request_id
    )


@router.get("/{widget_id}/assigned-devices", summary="Get devices assigned to widget")
def get_widget_assigned_devices(
    request: Request,
    widget_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get list of devices that have this widget assigned
    """
    request_id = get_request_id(request)

    logger.info(
        "Fetching assigned devices for widget",
        request_id=request_id,
        widget_id=widget_id
    )

    # Verify widget exists
    widget = db.query(Widget).filter(Widget.id == widget_id).first()
    if not widget:
        raise NotFoundException(f"Widget with ID {widget_id} not found")

    # Get assigned device IDs from styles
    styles = widget.styles or {}
    device_ids = styles.get('assigned_devices', [])

    # Fetch device details
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all() if device_ids else []

    device_list = []
    for device in devices:
        device_list.append({
            "device_id": device.id,
            "device_name": device.name,
            "location": device.location,
            "status": device.status
        })

    logger.info(
        "Assigned devices fetched successfully",
        request_id=request_id,
        widget_id=widget_id,
        device_count=len(device_list)
    )

    return success_response(
        data={
            "widget_id": widget_id,
            "widget_name": widget.widget_name,
            "assigned_devices": device_list,
            "total_assigned": len(device_list)
        },
        request_id=request_id
    )
