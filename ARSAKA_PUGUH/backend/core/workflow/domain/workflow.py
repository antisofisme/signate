"""
Workflow Domain Entity

Based on existing workflows table from 001_initial_schema.sql
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class WorkflowStatus(str, Enum):
    """Workflow status enum."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"
    ESCALATED = "ESCALATED"


@dataclass
class Workflow:
    """Workflow domain entity."""

    id: UUID
    decision_id: UUID
    tenant_id: UUID
    current_state: WorkflowStatus
    approver_role: str
    delegated_to_user_id: Optional[UUID] = None
    escalated_to_user_id: Optional[UUID] = None
    escalation_timeout_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_pending(self) -> bool:
        return self.current_state == WorkflowStatus.PENDING_APPROVAL

    def is_terminal(self) -> bool:
        return self.current_state in (WorkflowStatus.APPROVED, WorkflowStatus.REJECTED)

    def can_approve(self) -> bool:
        return self.current_state in (WorkflowStatus.PENDING_APPROVAL, WorkflowStatus.DELEGATED, WorkflowStatus.ESCALATED)

    def can_reject(self) -> bool:
        return self.can_approve()

    def can_delegate(self) -> bool:
        return self.current_state == WorkflowStatus.PENDING_APPROVAL

    def can_escalate(self) -> bool:
        return self.current_state in (WorkflowStatus.PENDING_APPROVAL, WorkflowStatus.DELEGATED)
