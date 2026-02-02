"""
Decision API Schemas

Pydantic models for rule and decision API requests and responses.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Rule Schemas
# =============================================================================

class CreateRuleRequest(BaseModel):
    """Create rule request."""
    rule_name: str = Field(..., min_length=1, max_length=256)
    decision_type: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    action: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(..., description="Required for mutations")


class UpdateRuleRequest(BaseModel):
    """Update rule request."""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None


class DeleteRuleRequest(BaseModel):
    """Delete rule request."""
    # Empty body - no fields required for delete


class ActivateRuleRequest(BaseModel):
    """Activate rule request."""
    idempotency_key: str = Field(..., description="Required for mutations")


class DeactivateRuleRequest(BaseModel):
    """Deactivate rule request."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deactivation")
    idempotency_key: str = Field(..., description="Required for mutations")


class RuleResponse(BaseModel):
    """Rule response model."""
    id: str
    rule_name: str
    decision_type: str
    description: Optional[str] = None
    status: str
    version: str
    evaluation_sequence: int = 0
    created_at: Optional[str] = None
    activated_at: Optional[str] = None


class RuleDetailResponse(RuleResponse):
    """Rule detail response with conditions and action."""
    conditions: Dict[str, Any] = Field(default_factory=dict)
    action: Dict[str, Any] = Field(default_factory=dict)
    extension_hooks: Optional[Dict[str, Any]] = None
    can_edit: bool = True
    can_delete: bool = True
    can_activate: bool = True
    created_by_user_id: Optional[str] = None
    deactivated_at: Optional[str] = None
    deactivation_reason: Optional[str] = None


class ListRulesResponse(BaseModel):
    """List rules response."""
    success: bool = True
    data: dict  # Contains items, total, page, limit, pages


# =============================================================================
# Decision Schemas
# =============================================================================

class DecisionResponse(BaseModel):
    """Decision response model."""
    id: str
    decision_type: str
    outcome: str
    rule_matched_id: Optional[str] = None
    rule_version: Optional[str] = None
    approval_workflow_id: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: Optional[str] = None


class DecisionDetailResponse(DecisionResponse):
    """Decision detail response with context."""
    context: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    requires_approval: bool = False


class ListDecisionsResponse(BaseModel):
    """List decisions response."""
    success: bool = True
    data: dict  # Contains items, total, page, limit, pages


# =============================================================================
# Generic Response Wrappers
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    data: dict


class CreateResponse(BaseModel):
    """Create operation response."""
    success: bool = True
    data: dict
    message: Optional[str] = None
