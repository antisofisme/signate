"""
Structured Logger Implementation

JSON-formatted logging with context propagation.
Sanitizes PII from context before logging.

Source: Phase 2 Design & Execution Plan - Section 3.1
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar


# Context variables for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format

    Output schema:
    {
        "timestamp": "2026-01-07T10:30:45.123Z",
        "level": "INFO",
        "logger": "core.use_cases",
        "message": "Decision created",
        "request_id": "req-abc123",
        "tenant_id": "550e8400-...",
        "trace_id": "trace-xyz789",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        tenant_id = tenant_id_var.get()
        if tenant_id:
            log_data["tenant_id"] = tenant_id

        trace_id = trace_id_var.get()
        if trace_id:
            log_data["trace_id"] = trace_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields (sanitized)
        if hasattr(record, "extra"):
            log_data["extra"] = self._sanitize_extra(record.extra)

        return json.dumps(log_data)

    def _sanitize_extra(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize extra fields to remove PII

        Strategy: Log keys only, not values (for context fields)
        """
        sanitized = {}
        for key, value in extra.items():
            if key == "context" and isinstance(value, dict):
                # Log context keys only, not values (PII protection)
                sanitized["context_keys"] = list(value.keys())
            elif key in ["input", "output"]:
                # Log shape, not full data
                sanitized[f"{key}_type"] = type(value).__name__
            else:
                # Safe fields (IDs, outcomes, etc.)
                sanitized[key] = value

        return sanitized


class StructuredLogger:
    """
    Structured logger with JSON output

    Usage:
        logger = StructuredLogger.get_logger(__name__)
        logger.info("Decision created", extra={"decision_id": "..."})
    """

    _configured = False

    @classmethod
    def configure(cls, level: str = "INFO", format_json: bool = True):
        """
        Configure structured logging globally

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_json: Use JSON formatter (True) or standard formatter (False)
        """
        if cls._configured:
            return

        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        root_logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)

        if format_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )

        root_logger.addHandler(console_handler)

        cls._configured = True
        root_logger.info("Structured logging configured", extra={"level": level, "json_format": format_json})

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get logger instance

        Args:
            name: Logger name (usually __name__)

        Returns:
            Configured logger instance
        """
        if not cls._configured:
            cls.configure()

        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get logger

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return StructuredLogger.get_logger(name)


def set_request_context(request_id: str, tenant_id: Optional[str] = None, trace_id: Optional[str] = None):
    """
    Set request context for logging

    Should be called at the beginning of each request (e.g., in middleware).

    Args:
        request_id: Unique request identifier
        tenant_id: Tenant identifier (optional)
        trace_id: Distributed trace identifier (optional)
    """
    request_id_var.set(request_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if trace_id:
        trace_id_var.set(trace_id)


def clear_request_context():
    """
    Clear request context after request completes

    Should be called at the end of each request (e.g., in middleware).
    """
    request_id_var.set(None)
    tenant_id_var.set(None)
    trace_id_var.set(None)
