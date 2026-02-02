"""
Database Models for ARSAKA_PUGUH Core Service

SQLAlchemy models mapping to database schema from migration 001-003.
Source: backend/migrations/001_initial_schema.sql
"""

from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DecisionModel(Base):
    """
    Decision database model - Immutable
    Maps to: decisions table
    """
    __tablename__ = 'decisions'

    decision_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    decision_type = Column(String(256), nullable=False)
    context = Column(JSONB, nullable=False)
    outcome = Column(String(32), nullable=False)
    rule_matched_id = Column(PG_UUID(as_uuid=True), nullable=True)
    rule_version = Column(String(32), nullable=True)
    approval_workflow_id = Column(PG_UUID(as_uuid=True), nullable=True)
    idempotency_key = Column(String(256), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    metadata_json = Column("metadata", JSONB, nullable=True)  # Map to 'metadata' column in DB
    evaluation_trace = Column(JSONB, nullable=True, default=[])  # Step-by-step rule evaluation for explainability
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archive_location = Column(String(512), nullable=True)

    __table_args__ = (
        CheckConstraint("outcome IN ('ALLOWED', 'DENIED', 'REQUIRE_APPROVAL')", name='outcome_valid'),
        CheckConstraint("outcome IS NOT NULL", name='outcome_not_null'),
        CheckConstraint("context IS NOT NULL", name='context_not_null'),
        CheckConstraint("length(decision_type) > 0", name='decision_type_not_empty'),
        Index('idx_decisions_tenant_decision_type', 'tenant_id', 'decision_type'),
        Index('idx_decisions_tenant_created_at', 'tenant_id', 'created_at'),
        Index('idx_decisions_idempotency_key', 'tenant_id', 'idempotency_key'),
    )


class WorkflowModel(Base):
    """
    Workflow database model - Mutable until terminal
    Maps to: workflows table
    """
    __tablename__ = 'workflows'

    workflow_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    decision_id = Column(PG_UUID(as_uuid=True), ForeignKey('decisions.decision_id', ondelete='RESTRICT'), nullable=False)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    current_state = Column(String(32), nullable=False)
    approver_role = Column(String(256), nullable=False)
    delegated_to_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    escalated_to_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    escalation_timeout_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column("metadata", JSONB, nullable=True)  # Map to 'metadata' column in DB

    __table_args__ = (
        CheckConstraint(
            "current_state IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'DELEGATED', 'ESCALATED')",
            name='state_valid'
        ),
        CheckConstraint(
            "completed_at IS NULL OR current_state IN ('APPROVED', 'REJECTED')",
            name='terminal_state_immutable'
        ),
        CheckConstraint("length(approver_role) > 0", name='approver_role_not_empty'),
        Index('idx_workflows_decision_id', 'decision_id'),
        Index('idx_workflows_tenant_decision_id', 'tenant_id', 'decision_id'),
    )


class RuleModel(Base):
    """
    Rule database model
    Maps to: rules table
    """
    __tablename__ = 'rules'

    rule_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    decision_type = Column(String(256), nullable=False)
    rule_name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    conditions = Column(JSONB, nullable=False)
    action = Column(JSONB, nullable=False)
    extension_hooks = Column(JSONB, nullable=True)
    version = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    evaluation_sequence = Column(Integer, nullable=False, default=0)

    # Governance metadata (UI grouping only, NOT for decision evaluation)
    functional_area_id = Column(PG_UUID(as_uuid=True), ForeignKey('functional_areas.functional_area_id', ondelete='SET NULL'), nullable=True, index=True)
    created_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivation_reason = Column(Text, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    final_audit_report_uri = Column(String(512), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archive_location = Column(String(512), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'DEPRECATED', 'DELETED')", name='status_valid'),
        CheckConstraint("length(version) > 0", name='version_not_empty'),
        CheckConstraint("length(rule_name) > 0", name='rule_name_not_empty'),
        CheckConstraint("conditions IS NOT NULL", name='conditions_not_null'),
        CheckConstraint("action IS NOT NULL", name='action_not_null'),
        Index('idx_rules_tenant_decision_type_status', 'tenant_id', 'decision_type', 'status'),
        Index('idx_rules_evaluation_order', 'tenant_id', 'decision_type', 'evaluation_sequence'),
    )

    # Relationships (will be available after FunctionalAreaModel is imported)
    # functional_area = relationship("FunctionalAreaModel", foreign_keys=[functional_area_id])


class IdempotencyCacheModel(Base):
    """
    Idempotency cache database model
    Maps to: idempotency_cache table
    """
    __tablename__ = 'idempotency_cache'

    tenant_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    idempotency_key = Column(String(256), primary_key=True)
    decision_id = Column(PG_UUID(as_uuid=True), ForeignKey('decisions.decision_id', ondelete='RESTRICT'), nullable=False)
    context_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ttl = Column(DateTime(timezone=True), nullable=True)


class EventLogModel(Base):
    """
    Event log database model - Immutable (append-only)
    Maps to: event_log table
    Source: INFRA-DEC-006 (Event & Audit as Immutable Facts)

    Phase 3 Addition: Outbox pattern columns for reliable event publishing
    """
    __tablename__ = 'event_log'

    event_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    event_type = Column(String(256), nullable=False)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    aggregate_id = Column(PG_UUID(as_uuid=True), nullable=False)
    aggregate_type = Column(String(32), nullable=False)
    payload = Column(JSONB, nullable=False)
    metadata_json = Column("metadata", JSONB, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    schema_version = Column(String(32), default='1.0')
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archive_location = Column(String(512), nullable=True)

    # Phase 3: Outbox pattern columns
    published_at = Column(DateTime(timezone=True), nullable=True)  # When published to event bus
    publish_attempts = Column(Integer, default=0)  # Number of publish attempts
    last_publish_error = Column(Text, nullable=True)  # Last error message
    dlq_at = Column(DateTime(timezone=True), nullable=True)  # When moved to DLQ

    __table_args__ = (
        CheckConstraint(
            "event_type IN ("
            "'decision.created', 'decision.allowed', 'decision.denied', 'decision.requires_approval', "
            "'workflow.created', 'workflow.pending_approval', 'workflow.approved', 'workflow.rejected', "
            "'workflow.delegated', 'workflow.escalated', 'workflow.completed')",
            name='event_type_valid'
        ),
        CheckConstraint("aggregate_type IN ('decision', 'workflow')", name='aggregate_type_valid'),
        CheckConstraint("payload IS NOT NULL", name='payload_not_null'),
        Index('idx_event_log_tenant_occurred', 'tenant_id', 'occurred_at'),
        Index('idx_event_log_aggregate', 'tenant_id', 'aggregate_id'),
        Index('idx_event_log_type', 'tenant_id', 'event_type'),
        # Phase 3: Outbox pattern indexes
        Index('idx_event_log_outbox_unpublished', 'recorded_at',
              postgresql_where="published_at IS NULL AND dlq_at IS NULL"),
        Index('idx_event_log_dlq', 'dlq_at',
              postgresql_where="dlq_at IS NOT NULL"),
    )


class WorkflowTransitionModel(Base):
    """
    Workflow transition database model - Immutable (append-only)
    Maps to: workflow_transitions table
    """
    __tablename__ = 'workflow_transitions'

    transition_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    workflow_id = Column(PG_UUID(as_uuid=True), ForeignKey('workflows.workflow_id', ondelete='RESTRICT'), nullable=False)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    from_state = Column(String(32), nullable=False)
    to_state = Column(String(32), nullable=False)
    action = Column(String(32), nullable=True)
    acted_by_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    approver_role = Column(String(256), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("length(from_state) > 0", name='from_state_not_empty'),
        CheckConstraint("length(to_state) > 0", name='to_state_not_empty'),
        Index('idx_workflow_transitions_workflow_id', 'workflow_id'),
        Index('idx_workflow_transitions_tenant_created', 'tenant_id', 'created_at'),
    )


class OperationsAuditModel(Base):
    """
    Operations audit database model - Immutable (append-only)
    Maps to: operations_audit table
    Source: INFRA-DEC-006 §5 (Audit Trail)
    """
    __tablename__ = 'operations_audit'

    audit_id = Column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    operation_type = Column(String(32), nullable=False)
    resource_type = Column(String(32), nullable=False)
    resource_id = Column(PG_UUID(as_uuid=True), nullable=True)
    actor_user_id = Column(PG_UUID(as_uuid=True), nullable=True)
    actor_role = Column(String(256), nullable=True)
    action_status = Column(String(32), nullable=True)
    reason_if_denied = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    trace_id = Column(PG_UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "operation_type IN ('CREATE', 'READ', 'UPDATE_ATTEMPT', 'DELETE_ATTEMPT', 'ACTIVATE', 'DEACTIVATE')",
            name='operation_type_valid'
        ),
        CheckConstraint("resource_type IN ('decision', 'workflow', 'rule', 'event_log')", name='resource_type_valid'),
        CheckConstraint("action_status IN ('SUCCESS', 'FAILURE', 'DENIED')", name='action_status_valid'),
        Index('idx_operations_audit_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('idx_operations_audit_resource', 'tenant_id', 'resource_id'),
    )
