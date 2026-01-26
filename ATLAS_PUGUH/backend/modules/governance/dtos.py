"""
ATLAS_PUGUH Backend - Governance Module DTOs
Follows PANDAWA Clean Architecture standards (CORE-STD-02)

Request/Response DTOs for Decision, Rule, Workflow, Event
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


# ========================================
# Decision DTOs (Phase 1)
# ========================================

class DecisionRequest(BaseModel):
    """Request to execute a decision"""

    decision_type: str = Field(..., description="Type of decision to execute")
    context: Dict[str, Any] = Field(..., description="Decision context data")
    idempotency_key: Optional[str] = Field(None, description="For idempotent requests")


class DecisionResponse(BaseModel):
    """Decision execution result"""

    decision_id: int
    decision_type: str
    outcome: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================
# Rule DTOs (Phase 2)
# ========================================

class RuleRequest(BaseModel):
    """Request to create/update a rule"""

    rule_type: str
    decision_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 0
    is_active: bool = True


class RuleResponse(BaseModel):
    """Rule configuration"""

    id: int
    rule_type: str
    decision_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Workflow DTOs (Phase 2)
# ========================================

class WorkflowRequest(BaseModel):
    """Request to start a workflow"""

    workflow_type: str
    entity_type: str
    entity_id: str
    metadata: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """Workflow instance status"""

    id: int
    workflow_type: str
    entity_type: str
    entity_id: str
    status: str
    current_step: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Event DTOs (Phase 2)
# ========================================

class EventRequest(BaseModel):
    """Request to publish an event"""

    event_type: str
    source: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class EventResponse(BaseModel):
    """Published event"""

    id: int
    event_type: str
    source: str
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    is_processed: bool
    created_at: datetime

    class Config:
        from_attributes = True
