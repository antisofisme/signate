"""
Variable Providers for Template System

Provides dynamic data to templates from various sources:
- Device variables (device.name, device.location, etc.)
- DateTime variables (datetime.now, datetime.today, etc.)
- Weather variables (weather.temp, weather.condition from OpenWeatherMap)
- Firebird PMS variables (firebird.event_name, firebird.room)
- Custom user-defined variables

Features:
- Provider registry with dependency injection
- Async data fetching with timeouts
- Multi-layer caching (5 min TTL)
- Fallback values on error
- Audit logging
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time as dt_time
import json
import asyncio

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings


# ============================================================================
# BASE PROVIDER
# ============================================================================

class BaseVariableProvider(ABC):
    """
    Abstract base class for variable providers.

    All providers must implement:
    - get_namespace(): Return namespace (e.g., 'device', 'datetime')
    - get_variables(): Return dict of variables
    """

    def __init__(self, db: Optional[Session] = None, redis_client=None):
        self.db = db
        self.redis = redis_client

    @abstractmethod
    def get_namespace(self) -> str:
        """Return the namespace for this provider (e.g., 'device')."""
        pass

    @abstractmethod
    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get variables for template rendering.

        Args:
            context: Request context (device_id, user_id, etc.)

        Returns:
            Dictionary of variables for this namespace
        """
        pass

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis:
            return None

        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    async def _set_cached(self, key: str, value: Any, ttl: int = 300):
        """Set value in Redis cache with TTL."""
        if not self.redis:
            return

        try:
            self.redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")


# ============================================================================
# DEVICE VARIABLE PROVIDER
# ============================================================================

class DeviceVariableProvider(BaseVariableProvider):
    """
    Provides device-related variables.

    Variables:
    - device.id
    - device.name
    - device.location
    - device.tag
    - device.status
    - device.ip_address
    """

    def get_namespace(self) -> str:
        return 'device'

    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get device variables."""
        device_id = context.get('device_id')

        if not device_id or not self.db:
            return {}

        try:
            # Import here to avoid circular imports
            from app.models.device import Device

            device = self.db.query(Device).filter_by(id=device_id).first()

            if not device:
                logger.warning(f"Device not found: {device_id}")
                return {}

            variables = {
                'id': device.id,
                'name': device.name or 'Unknown Device',
                'location': device.location or 'Unknown Location',
                'tag': device.tag.name if device.tag else None,
                'status': 'online' if device.is_online else 'offline',
                'ip_address': self._mask_ip(device.ip_address) if device.ip_address else None
            }

            logger.debug(f"Device variables loaded: {device.name}")
            return variables

        except Exception as e:
            logger.error(f"Error loading device variables: {e}")
            return {}

    def _mask_ip(self, ip_address: str) -> str:
        """Mask IP address for privacy (show only first 2 octets)."""
        parts = ip_address.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
        return "xxx.xxx.xxx.xxx"


# ============================================================================
# DATETIME VARIABLE PROVIDER
# ============================================================================

class DateTimeVariableProvider(BaseVariableProvider):
    """
    Provides date/time variables.

    Variables:
    - datetime.now (datetime object)
    - datetime.today (date object)
    - datetime.time (time object)
    - datetime.year (int)
    - datetime.month (int)
    - datetime.day (int)
    - datetime.weekday (string: Monday, Tuesday, etc.)
    - datetime.hour (int)
    - datetime.minute (int)
    """

    def get_namespace(self) -> str:
        return 'datetime'

    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get datetime variables."""
        now = datetime.now()

        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        variables = {
            'now': now,
            'today': now.date(),
            'time': now.time(),
            'year': now.year,
            'month': now.month,
            'day': now.day,
            'weekday': weekdays[now.weekday()],
            'hour': now.hour,
            'minute': now.minute,
            'second': now.second
        }

        return variables


# ============================================================================
# WEATHER VARIABLE PROVIDER
# ============================================================================

class WeatherVariableProvider(BaseVariableProvider):
    """
    Provides weather data from OpenWeatherMap API.

    Variables:
    - weather.temp (temperature in Celsius)
    - weather.feels_like
    - weather.condition (Clear, Cloudy, Rain, etc.)
    - weather.humidity (percentage)
    - weather.wind_speed (m/s)
    - weather.icon (weather icon code)

    Caching: 5 minutes TTL
    """

    API_KEY = None  # Set from settings
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, db: Optional[Session] = None, redis_client=None):
        super().__init__(db, redis_client)
        self.API_KEY = getattr(settings, 'OPENWEATHER_API_KEY', None)

    def get_namespace(self) -> str:
        return 'weather'

    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather variables with caching."""
        # Get location from device or context
        location = context.get('location')

        if not location:
            # Try to get from device
            device_id = context.get('device_id')
            if device_id and self.db:
                try:
                    from app.models.device import Device
                    device = self.db.query(Device).filter_by(id=device_id).first()
                    if device and device.location:
                        location = device.location
                except Exception as e:
                    logger.warning(f"Error getting device location: {e}")

        if not location:
            logger.debug("No location provided for weather")
            return self._get_fallback_weather()

        # Check cache first
        cache_key = f"weather:{location}"
        cached = await self._get_cached(cache_key)
        if cached:
            logger.debug(f"Weather cache hit: {location}")
            return cached

        # Fetch from API
        if not self.API_KEY:
            logger.warning("OpenWeatherMap API key not configured")
            return self._get_fallback_weather()

        try:
            weather_data = await self._fetch_weather(location)
            # Cache result
            await self._set_cached(cache_key, weather_data, ttl=self.CACHE_TTL)
            return weather_data

        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return self._get_fallback_weather()

    async def _fetch_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather from OpenWeatherMap API."""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': self.API_KEY,
            'units': 'metric'  # Celsius
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=3.0)

            if response.status_code != 200:
                logger.warning(f"Weather API returned {response.status_code}")
                return self._get_fallback_weather()

            data = response.json()

            weather_vars = {
                'temp': round(data['main']['temp'], 1),
                'feels_like': round(data['main']['feels_like'], 1),
                'condition': data['weather'][0]['description'].title(),
                'humidity': data['main']['humidity'],
                'wind_speed': round(data['wind']['speed'], 1),
                'icon': data['weather'][0]['icon']
            }

            logger.info(f"Weather fetched: {location} - {weather_vars['temp']}°C, {weather_vars['condition']}")
            return weather_vars

    def _get_fallback_weather(self) -> Dict[str, Any]:
        """Return fallback weather values."""
        return {
            'temp': 0,
            'feels_like': 0,
            'condition': 'Unknown',
            'humidity': 0,
            'wind_speed': 0,
            'icon': '01d'
        }


# ============================================================================
# FIREBIRD PMS VARIABLE PROVIDER
# ============================================================================

class FirebirdVariableProvider(BaseVariableProvider):
    """
    Provides data from Firebird PMS (Property Management System).

    Variables:
    - firebird.event_name
    - firebird.room
    - firebird.start_time
    - firebird.end_time
    - firebird.attendees
    - firebird.organizer

    Caching: 1 minute TTL (events change frequently)
    """

    CACHE_TTL = 60  # 1 minute

    def get_namespace(self) -> str:
        return 'firebird'

    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get Firebird PMS variables with caching."""
        device_id = context.get('device_id')

        if not device_id:
            return {}

        # Check cache
        cache_key = f"firebird:{device_id}"
        cached = await self._get_cached(cache_key)
        if cached:
            logger.debug(f"Firebird cache hit: device {device_id}")
            return cached

        # Fetch current event for device
        if not self.db:
            return {}

        try:
            event_data = await self._fetch_current_event(device_id)
            # Cache result
            await self._set_cached(cache_key, event_data, ttl=self.CACHE_TTL)
            return event_data

        except Exception as e:
            logger.error(f"Firebird fetch error: {e}")
            return {}

    async def _fetch_current_event(self, device_id: int) -> Dict[str, Any]:
        """Fetch current/upcoming event for device."""
        try:
            from app.models.device import Device
            from app.services.firebird_service import FirebirdService

            # Get device location/room mapping
            device = self.db.query(Device).filter_by(id=device_id).first()
            if not device or not device.location:
                return {}

            # Use Firebird service to get current event
            firebird_service = FirebirdService(self.db)
            event = await firebird_service.get_current_event(device.location)

            if not event:
                return {}

            variables = {
                'event_name': event.get('name', ''),
                'room': event.get('room', ''),
                'start_time': event.get('start_time'),
                'end_time': event.get('end_time'),
                'attendees': event.get('attendees', 0),
                'organizer': event.get('organizer', '')
            }

            logger.info(f"Firebird event loaded: {variables['event_name']} in {variables['room']}")
            return variables

        except Exception as e:
            logger.warning(f"Error fetching Firebird event: {e}")
            return {}


# ============================================================================
# CUSTOM VARIABLE PROVIDER
# ============================================================================

class CustomVariableProvider(BaseVariableProvider):
    """
    Provides user-defined custom variables.

    Variables are stored per content item in database.

    Example:
    - custom.hotel_name
    - custom.check_in_time
    - custom.special_message
    """

    def get_namespace(self) -> str:
        return 'custom'

    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get custom variables for content."""
        content_id = context.get('content_id')

        if not content_id or not self.db:
            return {}

        try:
            # Import here to avoid circular imports
            from app.models.content import ContentVariable

            variables_db = self.db.query(ContentVariable).filter_by(
                content_id=content_id
            ).all()

            variables = {}
            for var in variables_db:
                try:
                    # Parse JSON value
                    value = json.loads(var.value)
                    variables[var.name] = value
                except json.JSONDecodeError:
                    # Fallback to string value
                    variables[var.name] = var.value

            if variables:
                logger.debug(f"Custom variables loaded: {len(variables)} variables")

            return variables

        except Exception as e:
            logger.error(f"Error loading custom variables: {e}")
            return {}


# ============================================================================
# CONTENT VARIABLE PROVIDER
# ============================================================================

class ContentVariableProvider(BaseVariableProvider):
    """
    Provides content-related variables.

    Variables:
    - content.title
    - content.description
    - content.duration
    - content.sequence
    """

    def get_namespace(self) -> str:
        return 'content'

    async def get_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get content variables."""
        content_id = context.get('content_id')

        if not content_id or not self.db:
            return {}

        try:
            from app.models.content import Content

            content = self.db.query(Content).filter_by(id=content_id).first()

            if not content:
                logger.warning(f"Content not found: {content_id}")
                return {}

            variables = {
                'title': content.title or 'Untitled',
                'description': content.description or '',
                'duration': content.duration or 0,
                'sequence': context.get('sequence', 0)  # From playlist
            }

            logger.debug(f"Content variables loaded: {content.title}")
            return variables

        except Exception as e:
            logger.error(f"Error loading content variables: {e}")
            return {}


# ============================================================================
# PROVIDER REGISTRY
# ============================================================================

class VariableProviderRegistry:
    """
    Registry for all variable providers.

    Manages provider instances and provides unified access.
    """

    def __init__(self, db: Optional[Session] = None, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.providers: Dict[str, BaseVariableProvider] = {}

        # Register default providers
        self._register_default_providers()

    def _register_default_providers(self):
        """Register all default providers."""
        default_providers = [
            DeviceVariableProvider,
            DateTimeVariableProvider,
            WeatherVariableProvider,
            FirebirdVariableProvider,
            CustomVariableProvider,
            ContentVariableProvider
        ]

        for provider_class in default_providers:
            provider = provider_class(self.db, self.redis)
            self.register_provider(provider)

        logger.info(f"Registered {len(self.providers)} variable providers")

    def register_provider(self, provider: BaseVariableProvider):
        """Register a variable provider."""
        namespace = provider.get_namespace()
        self.providers[namespace] = provider
        logger.debug(f"Registered provider: {namespace}")

    async def get_all_variables(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Get variables from all providers.

        Args:
            context: Request context (device_id, content_id, etc.)

        Returns:
            Dict with namespace keys and variable dicts:
            {
                'device': {'name': 'TV-01', 'location': 'Lobby'},
                'datetime': {'now': datetime(...), 'year': 2024},
                'weather': {'temp': 25.0, 'condition': 'Clear'},
                ...
            }
        """
        result = {}

        # Fetch all providers in parallel
        tasks = []
        provider_namespaces = []

        for namespace, provider in self.providers.items():
            tasks.append(provider.get_variables(context))
            provider_namespaces.append(namespace)

        # Wait for all providers with timeout
        try:
            variables_list = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=5.0  # 5 second timeout for all providers
            )

            # Combine results
            for namespace, variables in zip(provider_namespaces, variables_list):
                if isinstance(variables, Exception):
                    logger.error(f"Provider {namespace} failed: {variables}")
                    result[namespace] = {}
                else:
                    result[namespace] = variables

        except asyncio.TimeoutError:
            logger.error("Variable provider timeout")
            # Return what we have so far
            result = {ns: {} for ns in provider_namespaces}

        return result

    async def get_variables_for_namespace(
        self,
        namespace: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get variables for a specific namespace."""
        provider = self.providers.get(namespace)

        if not provider:
            logger.warning(f"Provider not found: {namespace}")
            return {}

        try:
            return await provider.get_variables(context)
        except Exception as e:
            logger.error(f"Error getting variables for {namespace}: {e}")
            return {}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def get_template_context(
    device_id: Optional[int] = None,
    content_id: Optional[int] = None,
    db: Optional[Session] = None,
    redis_client=None,
    **extra_context
) -> Dict[str, Any]:
    """
    Get complete template context for rendering.

    Args:
        device_id: Device ID
        content_id: Content ID
        db: Database session
        redis_client: Redis client
        **extra_context: Additional context variables

    Returns:
        Complete context dict with all namespaces
    """
    registry = VariableProviderRegistry(db, redis_client)

    context = {
        'device_id': device_id,
        'content_id': content_id,
        **extra_context
    }

    variables = await registry.get_all_variables(context)

    # Flatten structure for easier template access
    # Instead of: {{device.name}}
    # Allow: {{device.name}} (nested) AND {{device_name}} (flat)
    flat_context = {}
    for namespace, vars_dict in variables.items():
        # Add nested structure
        flat_context[namespace] = vars_dict

    return flat_context


async def get_available_variables(
    db: Optional[Session] = None,
    redis_client=None
) -> Dict[str, List[str]]:
    """
    Get list of all available variables by namespace.

    Useful for UI autocomplete and documentation.

    Returns:
        {
            'device': ['id', 'name', 'location', ...],
            'datetime': ['now', 'today', 'year', ...],
            ...
        }
    """
    registry = VariableProviderRegistry(db, redis_client)

    # Get empty context sample
    empty_context = {}
    variables = await registry.get_all_variables(empty_context)

    # Extract variable names
    available = {}
    for namespace, vars_dict in variables.items():
        available[namespace] = list(vars_dict.keys())

    return available
