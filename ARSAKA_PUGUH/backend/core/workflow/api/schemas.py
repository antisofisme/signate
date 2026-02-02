"""
Workflow API Schemas
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApproveWorkflowRequest(BaseModel):
    comment: Optional[str] = None
    idempotency_key: str = Field(..., description="Required for mutations")


class RejectWorkflowRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., description="Required for mutations")


class DelegateWorkflowRequest(BaseModel):
    delegate_to_user_id: UUID
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., description="Required for mutations")


class EscalateWorkflowRequest(BaseModel):
    escalate_to_user_id: UUID
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., description="Required for mutations")


class ListWorkflowsResponse(BaseModel):
    success: bool = True
    data: dict


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict
