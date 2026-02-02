"""
MANTRA SDK - Python client for ARSAKA_MANTRA Decision System

Per MANTRA-LAW-006: AI assistants have ZERO authority for:
- Approval (must be human)
- Creation (must be human authored)
- Modification (append-only, human approved)

This SDK provides read-only access and proposal capabilities.
All proposals require human approval through the dashboard.
"""

from .client import MantraClient
from .models import (
    Decision,
    DecisionCreate,
    ValidationResult,
    RetrievalResult,
    TriggerCheckResult,
    DocumentGenerateRequest,
    GeneratedDocument,
)
from .exceptions import MantraError, ValidationError, AuthorizationError

__version__ = "0.1.0"
__all__ = [
    "MantraClient",
    "Decision",
    "DecisionCreate",
    "ValidationResult",
    "RetrievalResult",
    "TriggerCheckResult",
    "DocumentGenerateRequest",
    "GeneratedDocument",
    "MantraError",
    "ValidationError",
    "AuthorizationError",
]
