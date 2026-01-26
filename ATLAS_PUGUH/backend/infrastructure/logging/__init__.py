"""
Structured Logging Infrastructure

Provides JSON-formatted logging with context injection.
Uses decorator pattern to wrap Phase 1 use cases WITHOUT modifying them.

Source: Phase 2 Design & Execution Plan - Section 3.1
"""

from .structured_logger import StructuredLogger, get_logger
from .logging_decorator import LoggingDecorator

__all__ = [
    "StructuredLogger",
    "get_logger",
    "LoggingDecorator",
]
