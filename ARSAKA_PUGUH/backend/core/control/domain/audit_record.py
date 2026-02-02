"""
Audit Record Domain Entity

Based on operations_audit table from 001_initial_schema.sql
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AuditRecord:
    """Audit record domain entity (immutable)."""

    id: UUID
    tenant_id: UUID
    operation_type: str  # CREATE, READ, UPDATE_ATTEMPT, DELETE_ATTEMPT, ACTIVATE, DEACTIVATE
    resource_type: str   # decision, workflow, rule, event_log
    resource_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    actor_role: Optional[str] = None
    action_status: Optional[str] = None  # SUCCESS, FAILURE, DENIED
    reason_if_denied: Optional[str] = None
    timestamp: Optional[datetime] = None
    trace_id: Optional[UUID] = None
