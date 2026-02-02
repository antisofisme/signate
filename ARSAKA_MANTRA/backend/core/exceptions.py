"""
MANTRA Domain Exceptions

Typed exceptions for better error handling across the MANTRA system.
Use these instead of generic Exception or ValueError.

Usage:
    from core.exceptions import (
        MantraError,
        ValidationError,
        DecisionNotFoundError,
        ImmutabilityViolationError,
        AuthorizationError,
    )

    # In use cases
    if not decision:
        raise DecisionNotFoundError(decision_id)

    # In routes
    try:
        result = use_case.execute()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except DecisionNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ErrorCode(str, Enum):
    """Error codes for MANTRA exceptions."""
    # Validation errors (4xx)
    VALIDATION_FAILED = "VALIDATION_FAILED"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    LAW_VIOLATION = "LAW_VIOLATION"
    DUPLICATE_DETECTED = "DUPLICATE_DETECTED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    QUALITY_TOO_LOW = "QUALITY_TOO_LOW"

    # Not found errors (404)
    DECISION_NOT_FOUND = "DECISION_NOT_FOUND"
    PROPOSAL_NOT_FOUND = "PROPOSAL_NOT_FOUND"
    APPROVAL_NOT_FOUND = "APPROVAL_NOT_FOUND"

    # Authorization errors (403)
    AI_NOT_AUTHORIZED = "AI_NOT_AUTHORIZED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    INSUFFICIENT_PERMISSION = "INSUFFICIENT_PERMISSION"

    # Immutability errors (409)
    IMMUTABILITY_VIOLATION = "IMMUTABILITY_VIOLATION"
    DECISION_ALREADY_EXISTS = "DECISION_ALREADY_EXISTS"
    SUPERSEDES_CHAIN_BROKEN = "SUPERSEDES_CHAIN_BROKEN"

    # Infrastructure errors (5xx)
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    QUEUE_ERROR = "QUEUE_ERROR"
    SEARCH_ERROR = "SEARCH_ERROR"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"

    # Generic
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class MantraError(Exception):
    """
    Base exception for all MANTRA domain errors.

    Provides structured error information that can be serialized to JSON.
    """
    code: ErrorCode
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }


# =============================================================================
# Validation Errors
# =============================================================================

@dataclass
class ValidationError(MantraError):
    """Decision validation failed."""
    violations: List[Dict[str, Any]] = field(default_factory=list)

    def __init__(
        self,
        message: str = "Decision validation failed",
        violations: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.VALIDATION_FAILED,
            message=message,
            details=details or {},
        )
        self.violations = violations or []

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["error"]["violations"] = self.violations
        return result


@dataclass
class SchemaError(MantraError):
    """Schema validation failed (S-rules)."""
    field: Optional[str] = None
    rule_id: Optional[str] = None

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        rule_id: Optional[str] = None,
    ):
        super().__init__(
            code=ErrorCode.SCHEMA_INVALID,
            message=message,
            details={"field": field, "rule_id": rule_id},
        )
        self.field = field
        self.rule_id = rule_id


@dataclass
class LawViolationError(MantraError):
    """MANTRA Law violation (L-rules)."""
    law_reference: str = ""

    def __init__(
        self,
        message: str,
        law_reference: str = "MANTRA-LAW-001",
    ):
        super().__init__(
            code=ErrorCode.LAW_VIOLATION,
            message=message,
            details={"law_reference": law_reference},
        )
        self.law_reference = law_reference


@dataclass
class DuplicateError(MantraError):
    """Duplicate decision detected."""
    existing_id: str = ""
    similarity: float = 0.0

    def __init__(
        self,
        message: str,
        existing_id: str,
        similarity: float = 1.0,
    ):
        super().__init__(
            code=ErrorCode.DUPLICATE_DETECTED,
            message=message,
            details={"existing_id": existing_id, "similarity": similarity},
        )
        self.existing_id = existing_id
        self.similarity = similarity


@dataclass
class ConflictError(MantraError):
    """Conflict with existing decision detected."""
    conflicting_ids: List[str] = field(default_factory=list)

    def __init__(
        self,
        message: str,
        conflicting_ids: Optional[List[str]] = None,
    ):
        super().__init__(
            code=ErrorCode.CONFLICT_DETECTED,
            message=message,
            details={"conflicting_ids": conflicting_ids or []},
        )
        self.conflicting_ids = conflicting_ids or []


@dataclass
class QualityError(MantraError):
    """Decision quality too low."""
    score: float = 0.0
    minimum: float = 0.0

    def __init__(
        self,
        message: str,
        score: float,
        minimum: float = 50.0,
    ):
        super().__init__(
            code=ErrorCode.QUALITY_TOO_LOW,
            message=message,
            details={"score": score, "minimum": minimum},
        )
        self.score = score
        self.minimum = minimum


# =============================================================================
# Not Found Errors
# =============================================================================

@dataclass
class DecisionNotFoundError(MantraError):
    """Decision not found."""
    decision_id: str = ""

    def __init__(self, decision_id: str):
        super().__init__(
            code=ErrorCode.DECISION_NOT_FOUND,
            message=f"Decision not found: {decision_id}",
            details={"decision_id": decision_id},
        )
        self.decision_id = decision_id


@dataclass
class ProposalNotFoundError(MantraError):
    """Proposal not found or expired."""
    proposal_id: str = ""

    def __init__(self, proposal_id: str):
        super().__init__(
            code=ErrorCode.PROPOSAL_NOT_FOUND,
            message=f"Proposal not found or expired: {proposal_id}",
            details={"proposal_id": proposal_id},
        )
        self.proposal_id = proposal_id


@dataclass
class ApprovalNotFoundError(MantraError):
    """Approval request not found."""
    request_id: str = ""

    def __init__(self, request_id: str):
        super().__init__(
            code=ErrorCode.APPROVAL_NOT_FOUND,
            message=f"Approval request not found: {request_id}",
            details={"request_id": request_id},
        )
        self.request_id = request_id


# =============================================================================
# Authorization Errors
# =============================================================================

@dataclass
class AuthorizationError(MantraError):
    """Base authorization error."""
    actor: str = ""

    def __init__(
        self,
        message: str,
        actor: str = "",
        code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSION,
    ):
        super().__init__(
            code=code,
            message=message,
            details={"actor": actor},
        )
        self.actor = actor


@dataclass
class AINotAuthorizedError(AuthorizationError):
    """
    AI attempted an action requiring human authority.

    Per MANTRA-LAW-006: AI has ZERO authority for approval/creation/modification.
    """
    action: str = ""

    def __init__(self, action: str, actor: str = "AI"):
        super().__init__(
            message=f"AI cannot {action}. Per MANTRA-LAW-006: AI has ZERO authority.",
            actor=actor,
            code=ErrorCode.AI_NOT_AUTHORIZED,
        )
        self.action = action
        self.details["action"] = action
        self.details["law_reference"] = "MANTRA-LAW-006"


@dataclass
class HumanRequiredError(AuthorizationError):
    """Action requires human authority."""
    action: str = ""

    def __init__(self, action: str):
        super().__init__(
            message=f"Human authority required for: {action}",
            code=ErrorCode.HUMAN_REQUIRED,
        )
        self.action = action
        self.details["action"] = action


# =============================================================================
# Immutability Errors
# =============================================================================

@dataclass
class ImmutabilityViolationError(MantraError):
    """Attempt to modify immutable decision."""
    decision_id: str = ""

    def __init__(self, decision_id: str):
        super().__init__(
            code=ErrorCode.IMMUTABILITY_VIOLATION,
            message=f"Cannot modify immutable decision: {decision_id}. "
                    "Per MANTRA-LAW-001 §10: Stored decisions are immutable.",
            details={
                "decision_id": decision_id,
                "law_reference": "MANTRA-LAW-001 §10",
            },
        )
        self.decision_id = decision_id


@dataclass
class DecisionAlreadyExistsError(MantraError):
    """Decision ID already exists."""
    decision_id: str = ""

    def __init__(self, decision_id: str):
        super().__init__(
            code=ErrorCode.DECISION_ALREADY_EXISTS,
            message=f"Decision already exists: {decision_id}. "
                    "Decisions are append-only.",
            details={"decision_id": decision_id},
        )
        self.decision_id = decision_id


@dataclass
class SupersedesChainError(MantraError):
    """Supersedes chain is broken or invalid."""
    decision_id: str = ""
    supersedes_id: str = ""
    reason: str = ""

    def __init__(
        self,
        decision_id: str,
        supersedes_id: str,
        reason: str,
    ):
        super().__init__(
            code=ErrorCode.SUPERSEDES_CHAIN_BROKEN,
            message=f"Invalid supersedes chain: {reason}",
            details={
                "decision_id": decision_id,
                "supersedes_id": supersedes_id,
                "reason": reason,
            },
        )
        self.decision_id = decision_id
        self.supersedes_id = supersedes_id
        self.reason = reason


# =============================================================================
# Infrastructure Errors
# =============================================================================

@dataclass
class DatabaseError(MantraError):
    """Database operation failed."""
    operation: str = ""

    def __init__(self, message: str, operation: str = ""):
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            details={"operation": operation},
        )
        self.operation = operation


@dataclass
class CacheError(MantraError):
    """Cache operation failed."""
    key: str = ""

    def __init__(self, message: str, key: str = ""):
        super().__init__(
            code=ErrorCode.CACHE_ERROR,
            message=message,
            details={"key": key},
        )
        self.key = key


@dataclass
class QueueError(MantraError):
    """Message queue operation failed."""
    queue_name: str = ""

    def __init__(self, message: str, queue_name: str = ""):
        super().__init__(
            code=ErrorCode.QUEUE_ERROR,
            message=message,
            details={"queue_name": queue_name},
        )
        self.queue_name = queue_name


@dataclass
class SearchError(MantraError):
    """Search operation failed."""
    query: str = ""

    def __init__(self, message: str, query: str = ""):
        super().__init__(
            code=ErrorCode.SEARCH_ERROR,
            message=message,
            details={"query": query},
        )
        self.query = query


@dataclass
class EmbeddingError(MantraError):
    """Embedding generation failed."""
    text_length: int = 0

    def __init__(self, message: str, text_length: int = 0):
        super().__init__(
            code=ErrorCode.EMBEDDING_ERROR,
            message=message,
            details={"text_length": text_length},
        )
        self.text_length = text_length


# =============================================================================
# Exception Handler Helpers
# =============================================================================

def to_http_status(error: MantraError) -> int:
    """Map MantraError to HTTP status code."""
    code_to_status = {
        # 400 Bad Request
        ErrorCode.VALIDATION_FAILED: 400,
        ErrorCode.SCHEMA_INVALID: 400,
        ErrorCode.LAW_VIOLATION: 400,
        ErrorCode.QUALITY_TOO_LOW: 400,

        # 403 Forbidden
        ErrorCode.AI_NOT_AUTHORIZED: 403,
        ErrorCode.HUMAN_REQUIRED: 403,
        ErrorCode.INSUFFICIENT_PERMISSION: 403,

        # 404 Not Found
        ErrorCode.DECISION_NOT_FOUND: 404,
        ErrorCode.PROPOSAL_NOT_FOUND: 404,
        ErrorCode.APPROVAL_NOT_FOUND: 404,

        # 409 Conflict
        ErrorCode.DUPLICATE_DETECTED: 409,
        ErrorCode.CONFLICT_DETECTED: 409,
        ErrorCode.IMMUTABILITY_VIOLATION: 409,
        ErrorCode.DECISION_ALREADY_EXISTS: 409,
        ErrorCode.SUPERSEDES_CHAIN_BROKEN: 409,

        # 500 Internal Server Error
        ErrorCode.DATABASE_ERROR: 500,
        ErrorCode.CACHE_ERROR: 500,
        ErrorCode.QUEUE_ERROR: 500,
        ErrorCode.SEARCH_ERROR: 500,
        ErrorCode.EMBEDDING_ERROR: 500,
        ErrorCode.INTERNAL_ERROR: 500,
    }
    return code_to_status.get(error.code, 500)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Base
    "ErrorCode",
    "MantraError",
    # Validation
    "ValidationError",
    "SchemaError",
    "LawViolationError",
    "DuplicateError",
    "ConflictError",
    "QualityError",
    # Not Found
    "DecisionNotFoundError",
    "ProposalNotFoundError",
    "ApprovalNotFoundError",
    # Authorization
    "AuthorizationError",
    "AINotAuthorizedError",
    "HumanRequiredError",
    # Immutability
    "ImmutabilityViolationError",
    "DecisionAlreadyExistsError",
    "SupersedesChainError",
    # Infrastructure
    "DatabaseError",
    "CacheError",
    "QueueError",
    "SearchError",
    "EmbeddingError",
    # Helpers
    "to_http_status",
]
