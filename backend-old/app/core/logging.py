"""
Structured Logging Configuration
JSON-formatted logging for better parsing, searching, and monitoring
"""

import sys
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging

    Outputs logs in JSON format with consistent fields:
    - timestamp: ISO format timestamp
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - request_id: Request ID from middleware (if available)
    - Additional custom fields from 'extra' parameter

    Example output:
    {
        "timestamp": "2025-10-27T10:30:00.123456Z",
        "level": "INFO",
        "logger": "app.api.devices",
        "message": "Device registered successfully",
        "request_id": "a1b2c3d4-e5f6-7890",
        "device_id": 123,
        "device_name": "TV-001"
    }
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """
        Add custom fields to log record

        Args:
            log_record: Dictionary that will be converted to JSON
            record: Original LogRecord object
            message_dict: Additional fields from logger.info(..., extra={...})
        """
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add message
        if 'message' not in log_record:
            log_record['message'] = record.getMessage()

        # Add file location for debugging (only in development)
        if settings.DEBUG:
            log_record['file'] = f"{record.pathname}:{record.lineno}"
            log_record['function'] = record.funcName

        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


class RequestContextFilter(logging.Filter):
    """
    Logging filter to add request context to log records

    Attempts to extract request_id from current context and add to logs
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request context to log record

        Args:
            record: LogRecord to modify

        Returns:
            True (always allow log to pass through)
        """
        # Add default request_id if not present
        if not hasattr(record, 'request_id'):
            record.request_id = None

        # Add environment
        record.environment = settings.ENVIRONMENT

        return True


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')

    Usage in main.py:
        from app.core.logging import setup_logging
        setup_logging()
    """
    # Get configuration from settings
    level = log_level or settings.LOG_LEVEL
    format_type = log_format or settings.LOG_FORMAT

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Configure formatter based on format type
    if format_type.lower() == 'json':
        # JSON formatter for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        # Text formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)

    # Add request context filter
    request_filter = RequestContextFilter()
    console_handler.addFilter(request_filter)

    # Configure root logger
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": level,
            "log_format": format_type,
            "environment": settings.ENVIRONMENT
        }
    )


class StructuredLogger:
    """
    Wrapper class for structured logging with consistent format

    Provides convenience methods for logging with structured data

    Usage:
        from app.core.logging import StructuredLogger

        logger = StructuredLogger(__name__)

        logger.info(
            "Device registered",
            device_id=123,
            device_name="TV-001",
            request_id=request.state.request_id
        )
    """

    def __init__(self, name: str):
        """
        Initialize structured logger

        Args:
            name: Logger name (usually __name__ of the module)
        """
        self.logger = logging.getLogger(name)

    def _log(
        self,
        level: int,
        message: str,
        **kwargs
    ) -> None:
        """
        Internal logging method with structured data

        Args:
            level: Logging level (logging.INFO, logging.ERROR, etc.)
            message: Log message
            **kwargs: Additional structured fields
        """
        self.logger.log(level, message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with structured data"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with structured data"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured data"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Log error message with structured data

        Args:
            message: Error message
            exc_info: Include exception traceback (default: False)
            **kwargs: Additional structured fields
        """
        if exc_info:
            self.logger.error(message, extra=kwargs, exc_info=True)
        else:
            self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Log critical message with structured data

        Args:
            message: Critical error message
            exc_info: Include exception traceback (default: False)
            **kwargs: Additional structured fields
        """
        if exc_info:
            self.logger.critical(message, extra=kwargs, exc_info=True)
        else:
            self._log(logging.CRITICAL, message, **kwargs)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_api_call(
    endpoint: str,
    method: str,
    request_id: str,
    user_id: Optional[int] = None,
    **kwargs
) -> None:
    """
    Log API call with structured data

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        request_id: Request ID from middleware
        user_id: Optional authenticated user ID
        **kwargs: Additional context
    """
    logger = StructuredLogger(__name__)
    logger.info(
        f"API call: {method} {endpoint}",
        endpoint=endpoint,
        method=method,
        request_id=request_id,
        user_id=user_id,
        **kwargs
    )


def log_database_query(
    query_type: str,
    table: str,
    request_id: Optional[str] = None,
    duration: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log database query with structured data

    Args:
        query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
        table: Database table name
        request_id: Optional request ID
        duration: Query duration in seconds
        **kwargs: Additional context
    """
    logger = StructuredLogger(__name__)
    logger.debug(
        f"Database query: {query_type} on {table}",
        query_type=query_type,
        table=table,
        request_id=request_id,
        duration_seconds=duration,
        **kwargs
    )


def log_external_api_call(
    service: str,
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
    duration: Optional[float] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log external API call with structured data

    Args:
        service: External service name (e.g., "anthias", "firebird")
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration: Request duration in seconds
        request_id: Optional request ID
        **kwargs: Additional context
    """
    logger = StructuredLogger(__name__)

    log_level = logging.INFO if status_code and status_code < 400 else logging.WARNING

    logger._log(
        log_level,
        f"External API call: {service} - {method} {endpoint}",
        service=service,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_seconds=duration,
        request_id=request_id,
        **kwargs
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example usage of structured logging
    setup_logging(log_level="INFO", log_format="json")

    logger = StructuredLogger(__name__)

    logger.info(
        "Application started",
        version="1.0.0",
        environment="production"
    )

    logger.warning(
        "High memory usage detected",
        memory_mb=1024,
        threshold_mb=800
    )

    logger.error(
        "Failed to connect to database",
        database="postgresql",
        host="localhost",
        port=5432,
        exc_info=True
    )

    log_api_call(
        endpoint="/api/devices",
        method="GET",
        request_id="a1b2c3d4",
        user_id=123,
        response_time_ms=45
    )
