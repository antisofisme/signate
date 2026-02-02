"""
Decision Domain Entity

Represents a decision record in the system.
Based on existing decisions table from 001_initial_schema.sql
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class DecisionOutcome(str, Enum):
    """Decision outcome enum."""
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class Decision:
    """Decision domain entity (immutable record)."""

    id: UUID
    tenant_id: UUID
    decision_type: str
    context: Dict[str, Any]
    outcome: DecisionOutcome
    rule_matched_id: Optional[UUID] = None
    rule_version: Optional[str] = None
    approval_workflow_id: Optional[UUID] = None
    idempotency_key: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def requires_approval(self) -> bool:
        """Check if decision requires approval workflow."""
        return self.outcome == DecisionOutcome.REQUIRE_APPROVAL

    def is_allowed(self) -> bool:
        """Check if decision was allowed."""
        return self.outcome == DecisionOutcome.ALLOWED

    def is_denied(self) -> bool:
        """Check if decision was denied."""
        return self.outcome == DecisionOutcome.DENIED
