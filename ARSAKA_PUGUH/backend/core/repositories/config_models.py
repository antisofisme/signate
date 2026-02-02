"""
Configuration Master Data Models
Purpose: Customer-defined master data for governance and UI
NOT for decision evaluation logic
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .models import Base


class FunctionalAreaModel(Base):
    """
    Functional Area - Customer-defined master data
    Purpose: UI grouping, governance boundary
    NOT used in decision evaluation logic
    """
    __tablename__ = "functional_areas"

    functional_area_id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Master data
    code = Column(String(50), nullable=False)  # FINANCE, HR, IT, etc.
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Metadata
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    display_order = Column(Integer, nullable=False, default=0)

    # Audit trail
    created_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships (will be defined in RuleModel)
    # rules = relationship("RuleModel", back_populates="functional_area")

    def __repr__(self):
        return f"<FunctionalArea {self.code}: {self.name}>"


class DecisionTypeModel(Base):
    """
    Decision Type - System-defined contract
    Purpose: Runtime evaluation contract, hard-coded in backend
    context_schema defines expected JSON structure for decision.context
    """
    __tablename__ = "decision_types"

    decision_type_id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Contract definition
    type_code = Column(String(100), nullable=False)  # purchase_request, leave_request, etc.
    type_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Schema definition (JSON Schema for context validation)
    context_schema = Column(JSONB, nullable=False, default={})

    # Metadata
    is_system_defined = Column(Boolean, nullable=False, default=False)  # Cannot delete if TRUE
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Audit trail
    created_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DecisionType {self.type_code}: {self.type_name}>"


class ApproverRoleModel(Base):
    """
    Approver Role - Customer-defined role definition
    Purpose: Define approval authority roles
    """
    __tablename__ = "approver_roles"

    approver_role_id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Role definition
    role_code = Column(String(100), nullable=False)  # finance_manager, cfo, etc.
    role_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Metadata
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    display_order = Column(Integer, nullable=False, default=0)

    # Audit trail
    created_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ApproverRole {self.role_code}: {self.role_name}>"


class RuleStatusChangeModel(Base):
    """
    Rule Status Change Audit
    Purpose: Track rule lifecycle with mandatory change_reason
    Governance requirement: Every status change must be explained
    """
    __tablename__ = "rule_status_changes"

    change_id = Column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    rule_id = Column(PG_UUID(as_uuid=True), ForeignKey("rules.rule_id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # Status transition
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)

    # MANDATORY: Change reason (governance requirement)
    change_reason = Column(
        Text,
        nullable=False,
        # CheckConstraint handled at DB level
    )

    # Audit
    changed_by_id = Column(PG_UUID(as_uuid=True), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship
    rule = relationship("RuleModel", foreign_keys=[rule_id])

    def __repr__(self):
        return f"<RuleStatusChange {self.old_status} → {self.new_status}>"
