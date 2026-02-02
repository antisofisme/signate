"""
Rule Domain Entity

Represents a decision rule in the system.
Based on existing rules table from 001_initial_schema.sql
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID


class RuleStatus(str, Enum):
    """Rule status enum."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    DELETED = "DELETED"


@dataclass
class Rule:
    """Rule domain entity."""

    id: UUID
    tenant_id: UUID
    decision_type: str
    rule_name: str
    conditions: Dict[str, Any]
    action: Dict[str, Any]
    version: str
    status: RuleStatus = RuleStatus.DRAFT
    description: Optional[str] = None
    extension_hooks: Optional[Dict[str, Any]] = None
    evaluation_sequence: int = 0
    created_by_user_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    deactivation_reason: Optional[str] = None

    def is_draft(self) -> bool:
        """Check if rule is in draft status."""
        return self.status == RuleStatus.DRAFT

    def is_active(self) -> bool:
        """Check if rule is active."""
        return self.status == RuleStatus.ACTIVE

    def can_activate(self) -> bool:
        """Check if rule can be activated."""
        return self.status == RuleStatus.DRAFT

    def can_edit(self) -> bool:
        """Check if rule can be edited."""
        return self.status == RuleStatus.DRAFT

    def can_delete(self) -> bool:
        """Check if rule can be deleted."""
        return self.status in (RuleStatus.DRAFT, RuleStatus.DEPRECATED)

    def can_deactivate(self) -> bool:
        """Check if rule can be deactivated (deprecated)."""
        return self.status == RuleStatus.ACTIVE
