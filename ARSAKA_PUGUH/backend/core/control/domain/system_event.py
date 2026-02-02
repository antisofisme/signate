"""
System Event Domain Entity

Based on event_log table from 001_initial_schema.sql
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass
class SystemEvent:
    """System event domain entity (immutable)."""

    id: UUID
    event_type: str
    tenant_id: UUID
    aggregate_id: UUID
    aggregate_type: str  # decision, workflow
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    occurred_at: Optional[datetime] = None
    recorded_at: Optional[datetime] = None
    schema_version: str = "1.0"

    def is_decision_event(self) -> bool:
        return self.aggregate_type == "decision"

    def is_workflow_event(self) -> bool:
        return self.aggregate_type == "workflow"
