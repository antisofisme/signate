"""
Shared Logging Configuration
Centralized logging setup for the application
"""

import logging
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path


# =============================================================================
# LOGGER CONFIGURATION
# =============================================================================

def setup_logger(
    name: str = "app",
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure logger

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Optional custom format string

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("my_app", level="DEBUG")
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Default format
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    formatter = logging.Formatter(format_string)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# =============================================================================
# REQUEST LOGGER
# =============================================================================

class RequestLogger:
    """
    Logger for HTTP requests with structured logging
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("request")

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log HTTP request with structured data

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            user_id: Optional user ID
            ip_address: Optional IP address
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "ip_address": ip_address
        }

        level = logging.INFO if status_code < 400 else logging.WARNING

        self.logger.log(
            level,
            f"{method} {path} - {status_code} - {duration_ms:.2f}ms",
            extra=log_data
        )


# =============================================================================
# ERROR LOGGER
# =============================================================================

class ErrorLogger:
    """
    Logger for errors with context and stack traces
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("error")

    def log_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        user_id: Optional[int] = None
    ):
        """
        Log error with context

        Args:
            error: Exception instance
            context: Optional context dictionary
            user_id: Optional user ID
        """
        import traceback

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "context": context or {},
            "stack_trace": traceback.format_exc()
        }

        self.logger.error(
            f"{type(error).__name__}: {str(error)}",
            extra=error_data,
            exc_info=True
        )


# =============================================================================
# AUDIT LOGGER
# =============================================================================

class AuditLogger:
    """
    Logger for audit trail (user actions, data changes)

    Logs to both console/file AND database (if use_case provided)
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        create_audit_log_use_case = None  # Optional: CreateAuditLogUseCase for DB persistence
    ):
        self.logger = logger or logging.getLogger("audit")
        self.create_audit_log_use_case = create_audit_log_use_case

    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        organization_id: Optional[int] = None
    ):
        """
        Log user action for audit trail (console + database if configured)

        Args:
            user_id: User ID performing the action (None for system actions)
            action: Action performed (e.g., 'user.create', 'org.update')
            resource_type: Type of resource ('user', 'organization', 'device', etc.)
            resource_id: Optional resource ID
            details: Optional additional details dictionary
            ip_address: Optional IP address
            user_agent: Optional user agent string
            organization_id: Optional organization context
        """
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "organization_id": organization_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }

        # Log to console/file
        self.logger.info(
            f"User {user_id} {action} {resource_type} {resource_id}",
            extra=audit_data
        )

        # Persist to database if use case provided
        if self.create_audit_log_use_case:
            try:
                self.create_audit_log_use_case.execute(
                    user_id=user_id,
                    organization_id=organization_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as e:
                # Don't fail the main request if audit logging fails
                self.logger.error(f"Failed to persist audit log to database: {str(e)}")


# =============================================================================
# PERFORMANCE LOGGER
# =============================================================================

class PerformanceLogger:
    """
    Logger for performance metrics
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("performance")

    def log_query(
        self,
        query: str,
        duration_ms: float,
        rows_affected: Optional[int] = None
    ):
        """
        Log database query performance

        Args:
            query: SQL query (can be truncated)
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
        """
        perf_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query[:200],  # Truncate long queries
            "duration_ms": duration_ms,
            "rows_affected": rows_affected
        }

        level = logging.WARNING if duration_ms > 1000 else logging.DEBUG

        self.logger.log(
            level,
            f"Query took {duration_ms:.2f}ms - {rows_affected} rows",
            extra=perf_data
        )


# =============================================================================
# GLOBAL LOGGER INSTANCES
# =============================================================================

# Create default logger instances
app_logger = setup_logger("app")
request_logger = RequestLogger()
error_logger = ErrorLogger()
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
