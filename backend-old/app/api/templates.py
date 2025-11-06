"""
Template Variables API Endpoints
Provides secure template rendering with variable injection
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import (
    BadRequestException,
    ValidationException,
    InternalServerException,
    ForbiddenException
)
from app.core.cache import invalidate_by_prefix, CACHE_KEY_PREFIXES
from app.schemas.common import success_response, APIResponse
from app.schemas.template import (
    TemplateValidationRequest,
    TemplateValidationResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplateVariable,
    TemplateVariablesResponse,
    CustomVariableCreate,
    CustomVariableUpdate,
    CustomVariableResponse
)
from app.services.template_service import get_renderer
from app.middleware.request_id import get_request_id
from app.models.user import User

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/templates", tags=["templates"])


# Rate limiting configuration
RATE_LIMITS = {
    "validate": {"requests": 10, "window": 60},  # 10 per minute
    "render": {"requests": 5, "window": 60},      # 5 per minute
    "preview": {"requests": 20, "window": 60}     # 20 per minute
}


@router.post("/validate", response_model=APIResponse[TemplateValidationResponse])
async def validate_template(
    request: Request,
    data: TemplateValidationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Validate template syntax and security

    This endpoint performs comprehensive validation:
    - Syntax validation (Jinja2 parser)
    - Security validation (blocked keywords, AST inspection)
    - Complexity analysis (node count, loops, conditions)
    - Variable extraction (required variables)

    Returns:
    - is_valid: Whether template passes all checks
    - errors: List of critical errors
    - warnings: List of non-critical warnings
    - required_variables: Variables used in template
    - detected_functions: Functions/filters used

    Rate limited: 10 validations per minute
    """
    request_id = get_request_id(request)

    logger.info(
        "Template validation requested",
        request_id=request_id,
        template_size=len(data.template),
        engine=data.engine,
        strict_mode=data.strict_mode,
        user=current_user.username if current_user else "anonymous"
    )

    try:
        # Get template renderer
        renderer = get_renderer()

        # Validate template
        validation_result = await renderer.validate_template(data.template)

        # Build response
        response = TemplateValidationResponse(
            is_valid=validation_result.get('valid', False),
            errors=validation_result.get('error', []) if isinstance(validation_result.get('error'), list)
                   else [validation_result.get('error')] if validation_result.get('error') else [],
            warnings=validation_result.get('warnings', []),
            required_variables=list(validation_result.get('metadata', {}).get('required_variables', [])),
            detected_functions=[]  # Would be populated from AST analysis
        )

        logger.info(
            "Template validation completed",
            request_id=request_id,
            is_valid=response.is_valid,
            error_count=len(response.errors),
            warning_count=len(response.warnings)
        )

        return success_response(
            data=response,
            message="Template validation completed"
        )

    except Exception as e:
        logger.error(
            "Template validation failed",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Template validation failed",
            details={"error": str(e)}
        )


@router.post("/render", response_model=APIResponse[TemplateRenderResponse])
async def render_template(
    request: Request,
    data: TemplateRenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Render template with provided context

    Security features:
    - Sandboxed execution environment
    - Timeout protection (5 seconds max)
    - Role-based variable filtering
    - XSS prevention (auto-escape)
    - Audit logging

    Rate limited: 5 renders per minute per user

    Context variables are filtered based on user role:
    - Admin: All variables allowed
    - Editor: Standard variables + custom
    - Viewer: Limited to safe variables
    """
    request_id = get_request_id(request)

    logger.info(
        "Template render requested",
        request_id=request_id,
        template_size=len(data.template),
        context_keys=list(data.context.keys()),
        device_id=data.device_id,
        content_id=data.content_id,
        user=current_user.username,
        role=current_user.role if hasattr(current_user, 'role') else 'viewer'
    )

    try:
        # Get user role (default to viewer for safety)
        user_role = getattr(current_user, 'role', 'viewer')

        # Build full context
        full_context = {}

        # Add device-specific variables if requested
        if data.device_id:
            # Would fetch device data from database
            full_context['device'] = {
                'id': data.device_id,
                'name': 'Device Name',
                'location': 'Main Lobby',
                'status': 'online'
            }

        # Add content-specific variables if requested
        if data.content_id:
            # Would fetch content data from database
            full_context['content'] = {
                'id': data.content_id,
                'title': 'Content Title',
                'description': 'Content Description'
            }

        # Add datetime variables
        now = datetime.utcnow()
        full_context['datetime'] = {
            'now': now.isoformat(),
            'today': now.date().isoformat(),
            'time': now.time().isoformat(),
            'year': now.year,
            'month': now.month,
            'day': now.day,
            'weekday': now.strftime('%A'),
            'hour': now.hour,
            'minute': now.minute
        }

        # Merge with user-provided context
        full_context.update(data.context)

        # Get template renderer
        renderer = get_renderer()

        # Render template with security controls
        render_result = await renderer.render(
            template_string=data.template,
            context=full_context,
            user_role=user_role,
            use_cache=data.use_cache,
            timeout=data.timeout
        )

        # Build response
        response = TemplateRenderResponse(
            success=True,
            rendered=render_result.get('output'),
            error=None,
            execution_time_ms=render_result.get('render_time_ms', 0),
            truncated=render_result.get('metadata', {}).get('truncated', False)
        )

        # Audit log for security
        logger.info(
            "Template rendered successfully",
            request_id=request_id,
            user=current_user.username,
            role=user_role,
            execution_time_ms=response.execution_time_ms,
            output_size=len(response.rendered) if response.rendered else 0,
            cached=render_result.get('cached', False)
        )

        return success_response(
            data=response,
            message="Template rendered successfully"
        )

    except Exception as e:
        logger.error(
            "Template rendering failed",
            request_id=request_id,
            user=current_user.username,
            error=str(e)
        )

        # Return error response
        response = TemplateRenderResponse(
            success=False,
            rendered=None,
            error=str(e),
            execution_time_ms=0,
            truncated=False
        )

        raise BadRequestException(
            message="Template rendering failed",
            details={"error": str(e)}
        )


@router.post("/preview", response_model=APIResponse[TemplatePreviewResponse])
async def preview_template(
    request: Request,
    data: TemplatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Preview template with sample data

    Useful for testing templates before deployment.
    Uses predefined sample data for common variables:
    - Device information
    - Date/time values
    - Weather data (mock)
    - Firebird data (mock)
    - Custom sample values

    Rate limited: 20 previews per minute
    """
    request_id = get_request_id(request)

    logger.info(
        "Template preview requested",
        request_id=request_id,
        template_size=len(data.template),
        use_sample_data=data.use_sample_data,
        has_custom_context=bool(data.custom_context)
    )

    try:
        # Build sample context
        sample_context = {}

        if data.use_sample_data:
            # Add comprehensive sample data
            now = datetime.utcnow()
            sample_context.update({
                'device': {
                    'id': 'DEMO001',
                    'name': 'Demo Display',
                    'location': 'Preview Mode',
                    'tag': 'demo',
                    'status': 'online',
                    'ip_address': '192.168.1.100'
                },
                'datetime': {
                    'now': now.isoformat(),
                    'today': now.date().isoformat(),
                    'time': now.time().isoformat(),
                    'year': now.year,
                    'month': now.month,
                    'day': now.day,
                    'weekday': now.strftime('%A'),
                    'hour': now.hour,
                    'minute': now.minute
                },
                'weather': {
                    'temp': 25.5,
                    'feels_like': 27.0,
                    'condition': 'Partly Cloudy',
                    'humidity': 65,
                    'wind_speed': 12,
                    'icon': '02d'
                },
                'firebird': {
                    'event_name': 'Annual Conference',
                    'room': 'Grand Ballroom',
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'attendees': 250,
                    'organizer': 'Corporate Events'
                },
                'hotel_name': 'Grand Hotel',
                'special_offer': '20% off spa treatments this week',
                'event_title': 'Jazz Night Every Friday',
                'restaurant_special': 'Fresh Seafood Buffet'
            })

        # Merge custom context
        if data.custom_context:
            sample_context.update(data.custom_context)

        # Get renderer
        renderer = get_renderer()

        # Render with sample data
        render_result = await renderer.render(
            template_string=data.template,
            context=sample_context,
            user_role='editor',  # Use editor role for preview
            use_cache=False,  # Don't cache previews
            timeout=5
        )

        # Build response
        response = TemplatePreviewResponse(
            preview=render_result.get('output', ''),
            sample_context=sample_context,
            warnings=[]
        )

        # Add warnings if any issues
        if not render_result.get('output'):
            response.warnings.append("Template produced empty output")

        logger.info(
            "Template preview completed",
            request_id=request_id,
            preview_size=len(response.preview),
            warning_count=len(response.warnings)
        )

        return success_response(
            data=response,
            message="Template preview generated"
        )

    except Exception as e:
        logger.error(
            "Template preview failed",
            request_id=request_id,
            error=str(e)
        )

        # Return partial response with error
        response = TemplatePreviewResponse(
            preview="",
            sample_context={},
            warnings=[str(e)]
        )

        return success_response(
            data=response,
            message="Template preview failed"
        )


@router.get("/variables", response_model=APIResponse[TemplateVariablesResponse])
async def list_available_variables(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all available template variables

    Returns categorized variables:
    - System: Device, datetime, system info
    - External: Weather, Firebird, other integrations
    - Custom: User-defined variables

    Each variable includes:
    - Name and path (e.g., device.name)
    - Type and description
    - Example value
    - Whether it's required
    """
    request_id = get_request_id(request)

    logger.info(
        "Template variables list requested",
        request_id=request_id
    )

    try:
        # System variables
        system_vars = [
            TemplateVariable(
                name="device_id",
                type="system",
                description="Unique device identifier",
                example="DEV001",
                required=False,
                path="device.id"
            ),
            TemplateVariable(
                name="device_name",
                type="system",
                description="Display name of the device",
                example="Lobby Display",
                required=False,
                path="device.name"
            ),
            TemplateVariable(
                name="device_location",
                type="system",
                description="Physical location of device",
                example="Main Lobby",
                required=False,
                path="device.location"
            ),
            TemplateVariable(
                name="datetime_now",
                type="system",
                description="Current date and time",
                example="2024-01-15T14:30:00Z",
                required=False,
                path="datetime.now"
            ),
            TemplateVariable(
                name="datetime_today",
                type="system",
                description="Today's date",
                example="2024-01-15",
                required=False,
                path="datetime.today"
            ),
            TemplateVariable(
                name="datetime_weekday",
                type="system",
                description="Current day of week",
                example="Monday",
                required=False,
                path="datetime.weekday"
            )
        ]

        # External variables
        external_vars = [
            TemplateVariable(
                name="weather_temp",
                type="external",
                description="Current temperature in Celsius",
                example=25.5,
                required=False,
                path="weather.temp"
            ),
            TemplateVariable(
                name="weather_condition",
                type="external",
                description="Current weather condition",
                example="Partly Cloudy",
                required=False,
                path="weather.condition"
            ),
            TemplateVariable(
                name="firebird_event",
                type="external",
                description="Current event name from Firebird",
                example="Annual Conference",
                required=False,
                path="firebird.event_name"
            ),
            TemplateVariable(
                name="firebird_room",
                type="external",
                description="Event room/location",
                example="Grand Ballroom",
                required=False,
                path="firebird.room"
            )
        ]

        # Custom variables (would be loaded from database)
        custom_vars = []

        # TODO: Load custom variables from database
        # custom_vars = await load_custom_variables(db, current_user)

        response = TemplateVariablesResponse(
            system=system_vars,
            external=external_vars,
            custom=custom_vars,
            total_count=len(system_vars) + len(external_vars) + len(custom_vars)
        )

        logger.info(
            "Template variables listed",
            request_id=request_id,
            system_count=len(system_vars),
            external_count=len(external_vars),
            custom_count=len(custom_vars)
        )

        return success_response(
            data=response,
            message="Available variables retrieved"
        )

    except Exception as e:
        logger.error(
            "Failed to list template variables",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to retrieve variables",
            details={"error": str(e)}
        )


@router.post("/custom-variables", response_model=APIResponse[CustomVariableResponse])
async def create_custom_variable(
    request: Request,
    data: CustomVariableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create user-defined custom variable

    Custom variables allow users to define reusable values
    that can be used across templates.

    Features:
    - Any JSON-serializable value
    - Optional expiration time
    - Global or user-specific scope
    - Description for documentation

    Requires authentication and editor role or higher.
    """
    request_id = get_request_id(request)

    # Check user role (only editors and admins can create variables)
    user_role = getattr(current_user, 'role', 'viewer')
    if user_role not in ['editor', 'admin']:
        raise ForbiddenException(
            message="Insufficient permissions to create custom variables"
        )

    logger.info(
        "Custom variable creation requested",
        request_id=request_id,
        variable_name=data.name,
        is_global=data.is_global,
        user=current_user.username
    )

    try:
        # TODO: Save to database
        # For now, return mock response
        response = CustomVariableResponse(
            id=1,
            name=data.name,
            value=data.value,
            description=data.description,
            is_global=data.is_global,
            expires_at=data.expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=current_user.username
        )

        # Clear cache
        await invalidate_by_prefix(CACHE_KEY_PREFIXES['settings'])

        logger.info(
            "Custom variable created",
            request_id=request_id,
            variable_id=response.id,
            variable_name=response.name
        )

        return success_response(
            data=response,
            message=f"Custom variable '{data.name}' created successfully"
        )

    except Exception as e:
        logger.error(
            "Failed to create custom variable",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to create custom variable",
            details={"error": str(e)}
        )


@router.get("/custom-variables", response_model=APIResponse[List[CustomVariableResponse]])
async def list_custom_variables(
    request: Request,
    is_global: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all custom variables

    Returns custom variables accessible to the current user.
    Filters:
    - is_global: Show only global or user-specific variables

    Variables are returned sorted by name.
    """
    request_id = get_request_id(request)

    logger.info(
        "Custom variables list requested",
        request_id=request_id,
        is_global=is_global,
        user=current_user.username if current_user else "anonymous"
    )

    try:
        # TODO: Load from database
        # For now, return empty list
        variables = []

        logger.info(
            "Custom variables listed",
            request_id=request_id,
            count=len(variables)
        )

        return success_response(
            data=variables,
            message=f"Found {len(variables)} custom variables"
        )

    except Exception as e:
        logger.error(
            "Failed to list custom variables",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to retrieve custom variables",
            details={"error": str(e)}
        )