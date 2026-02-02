"""
API Request/Response Schemas

Pydantic models for HTTP transport.
Separate from domain models and use case DTOs.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CreateDecisionRequest(BaseModel):
    """Request schema for POST /decisions"""
    tenant_id: UUID
    decision_type: str = Field(..., min_length=1)
    context: Dict[str, Any]
    idempotency_key: Optional[str] = None
    trace_id: Optional[UUID] = None
    requester_user_id: Optional[UUID] = None


class CreateDecisionResponse(BaseModel):
    """Response schema for POST /decisions"""
    decision_id: UUID
    outcome: str
    rule_matched_id: Optional[UUID]
    rule_version: Optional[str]
    workflow_id: Optional[UUID]
    created_at: datetime


class ApproveWorkflowRequest(BaseModel):
    """Request schema for POST /workflows/{id}/approve"""
    tenant_id: UUID
    approver_role: str = Field(..., min_length=1)
    acted_by_user_id: Optional[UUID] = None
    comment: Optional[str] = None


class ApproveWorkflowResponse(BaseModel):
    """Response schema for POST /workflows/{id}/approve"""
    workflow_id: UUID
    current_state: str
    completed_at: datetime


class RejectWorkflowRequest(BaseModel):
    """Request schema for POST /workflows/{id}/reject"""
    tenant_id: UUID
    approver_role: str = Field(..., min_length=1)
    acted_by_user_id: Optional[UUID] = None
    reason: Optional[str] = None


class RejectWorkflowResponse(BaseModel):
    """Response schema for POST /workflows/{id}/reject"""
    workflow_id: UUID
    current_state: str
    completed_at: datetime


class DelegateWorkflowRequest(BaseModel):
    """Request schema for POST /workflows/{id}/delegate"""
    tenant_id: UUID
    approver_role: str = Field(..., min_length=1)
    delegated_to_user_id: UUID
    acted_by_user_id: Optional[UUID] = None
    reason: str = ""


class DelegateWorkflowResponse(BaseModel):
    """Response schema for POST /workflows/{id}/delegate"""
    workflow_id: UUID
    current_state: str
    delegated_to_user_id: UUID


class EscalateWorkflowRequest(BaseModel):
    """Request schema for POST /workflows/{id}/escalate"""
    tenant_id: UUID
    escalated_to_role: str = Field(..., min_length=1)
    escalation_reason: str = Field(..., min_length=1)


class EscalateWorkflowResponse(BaseModel):
    """Response schema for POST /workflows/{id}/escalate"""
    workflow_id: UUID
    current_state: str
    escalated_to_role: str


class ErrorResponse(BaseModel):
    """Standard error response"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
