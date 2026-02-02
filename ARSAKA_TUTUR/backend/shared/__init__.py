"""
Shared utilities and helpers.
"""

from .logging import get_logger, setup_logging
from .exceptions import (
    ChatAIError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ExternalServiceError,
)
from .tokens import count_tokens, truncate_to_tokens

__all__ = [
    # Logging
    "get_logger", "setup_logging",
    # Exceptions
    "ChatAIError", "NotFoundError", "ValidationError",
    "AuthenticationError", "AuthorizationError",
    "RateLimitError", "ExternalServiceError",
    # Tokens
    "count_tokens", "truncate_to_tokens",
]
