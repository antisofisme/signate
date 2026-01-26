"""
Domain Aggregates for ATLAS_PUGUH Core Service

Aggregates enforce invariants and emit domain events.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from .value_objects import (
    DecisionId,
    WorkflowId,
    TenantId,
    Outcome,
    WorkflowState,
    WorkflowAction,
    Context,
    IdempotencyKey,
    RuleId,
    RuleVersion,
    Metadata
)
from .events import (
    DomainEvent,
    DecisionCreated,
    WorkflowPendingApproval,
    WorkflowApproved,
    WorkflowRejected,
    WorkflowDelegated,
    WorkflowEscalated
)


class Decision:
    """
    Decision Aggregate - Immutable after creation
    Source: INFRA-LAY3-002 §2.1
    """

    def __init__(
        self,
        decision_id: DecisionId,
        tenant_id: TenantId,
        decision_type: str,
        context: Context,
        outcome: Outcome,
        rule_matched_id: Optional[RuleId],
        rule_version: Optional[RuleVersion],
        idempotency_key: Optional[IdempotencyKey],
        metadata: Metadata,
        created_at: datetime,
        latency_ms: Optional[int] = None
    ):
        self._decision_id = decision_id
        self._tenant_id = tenant_id
        self._decision_type = decision_type
        self._context = context
        self._outcome = outcome
        self._rule_matched_id = rule_matched_id
        self._rule_version = rule_version
        self._idempotency_key = idempotency_key
        self._metadata = metadata
        self._created_at = created_at
        self._latency_ms = latency_ms
        self._events: List[DomainEvent] = []

    @classmethod
    def create(
        cls,
        tenant_id: TenantId,
        decision_type: str,
        context: Context,
        outcome: Outcome,
        rule_matched_id: Optional[RuleId] = None,
        rule_version: Optional[RuleVersion] = None,
        idempotency_key: Optional[IdempotencyKey] = None,
        metadata: Optional[Metadata] = None,
        latency_ms: Optional[int] = None
    ) -> 'Decision':
        """
        Factory method for decision creation
        Source: INFRA-LAY3-002 §2.1
        """
        if not decision_type:
            raise ValueError("decision_type cannot be empty")

        decision_id = DecisionId(uuid4())
        created_at = datetime.utcnow()

        if metadata is None:
            metadata = Metadata()

        decision = cls(
            decision_id=decision_id,
            tenant_id=tenant_id,
            decision_type=decision_type,
            context=context,
            outcome=outcome,
            rule_matched_id=rule_matched_id,
            rule_version=rule_version,
            idempotency_key=idempotency_key,
            metadata=metadata,
            created_at=created_at,
            latency_ms=latency_ms
        )

        decision._add_event(
            DecisionCreated(
                decision_id=decision_id.value,
                tenant_id=tenant_id.value,
                decision_type=decision_type,
                outcome=outcome.value,
                rule_matched_id=rule_matched_id.value if rule_matched_id else None,
                rule_version=str(rule_version) if rule_version else None,
                context_summary=context.to_dict(),
                latency_ms=latency_ms
            )
        )

        return decision

    @property
    def decision_id(self) -> DecisionId:
        return self._decision_id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def decision_type(self) -> str:
        return self._decision_type

    @property
    def context(self) -> Context:
        return self._context

    @property
    def outcome(self) -> Outcome:
        return self._outcome

    @property
    def rule_matched_id(self) -> Optional[RuleId]:
        return self._rule_matched_id

    @property
    def rule_version(self) -> Optional[RuleVersion]:
        return self._rule_version

    @property
    def idempotency_key(self) -> Optional[IdempotencyKey]:
        return self._idempotency_key

    @property
    def metadata(self) -> Metadata:
        return self._metadata

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def latency_ms(self) -> Optional[int]:
        return self._latency_ms

    def requires_workflow(self) -> bool:
        """Check if decision requires approval workflow"""
        return self._outcome.requires_workflow()

    def collect_events(self) -> List[DomainEvent]:
        """Collect and clear domain events"""
        events = self._events.copy()
        self._events.clear()
        return events

    def _add_event(self, event: DomainEvent):
        """Add domain event to aggregate"""
        self._events.append(event)


class Workflow:
    """
    Workflow Aggregate - Mutable until terminal state
    Source: INFRA-LAY3-002 §3
    """

    def __init__(
        self,
        workflow_id: WorkflowId,
        decision_id: DecisionId,
        tenant_id: TenantId,
        current_state: WorkflowState,
        approver_role: str,
        created_at: datetime,
        delegated_to_user_id: Optional[UUID] = None,
        escalated_to_user_id: Optional[UUID] = None,
        escalated_to_role: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Metadata] = None
    ):
        self._workflow_id = workflow_id
        self._decision_id = decision_id
        self._tenant_id = tenant_id
        self._current_state = current_state
        self._approver_role = approver_role
        self._created_at = created_at
        self._delegated_to_user_id = delegated_to_user_id
        self._escalated_to_user_id = escalated_to_user_id
        self._escalated_to_role = escalated_to_role
        self._completed_at = completed_at
        self._metadata = metadata or Metadata()
        self._events: List[DomainEvent] = []

    @classmethod
    def create(
        cls,
        decision_id: DecisionId,
        tenant_id: TenantId,
        approver_role: str,
        metadata: Optional[Metadata] = None
    ) -> 'Workflow':
        """
        Factory method for workflow creation
        Source: INFRA-LAY3-002 §3.1
        Initial state: PENDING_APPROVAL
        """
        if not approver_role:
            raise ValueError("approver_role cannot be empty")

        workflow_id = WorkflowId(uuid4())
        created_at = datetime.utcnow()
        current_state = WorkflowState.PENDING_APPROVAL

        workflow = cls(
            workflow_id=workflow_id,
            decision_id=decision_id,
            tenant_id=tenant_id,
            current_state=current_state,
            approver_role=approver_role,
            created_at=created_at,
            metadata=metadata
        )

        workflow._add_event(
            WorkflowPendingApproval(
                workflow_id=workflow_id.value,
                decision_id=decision_id.value,
                tenant_id=tenant_id.value,
                approver_role=approver_role
            )
        )

        return workflow

    def approve(
        self,
        approver_role: str,
        acted_by_user_id: Optional[UUID] = None,
        comment: Optional[str] = None
    ):
        """
        Approve workflow
        Source: INFRA-LAY3-002 §3.2
        """
        self._validate_approver_role(approver_role)
        self._validate_transition(WorkflowState.APPROVED)

        self._current_state = WorkflowState.APPROVED
        self._completed_at = datetime.utcnow()

        self._add_event(
            WorkflowApproved(
                workflow_id=self._workflow_id.value,
                decision_id=self._decision_id.value,
                tenant_id=self._tenant_id.value,
                approver_role=approver_role,
                acted_by_user_id=acted_by_user_id,
                comment=comment
            )
        )

    def reject(
        self,
        approver_role: str,
        acted_by_user_id: Optional[UUID] = None,
        reason: Optional[str] = None
    ):
        """
        Reject workflow
        Source: INFRA-LAY3-002 §3.2
        """
        self._validate_approver_role(approver_role)
        self._validate_transition(WorkflowState.REJECTED)

        self._current_state = WorkflowState.REJECTED
        self._completed_at = datetime.utcnow()

        self._add_event(
            WorkflowRejected(
                workflow_id=self._workflow_id.value,
                decision_id=self._decision_id.value,
                tenant_id=self._tenant_id.value,
                approver_role=approver_role,
                acted_by_user_id=acted_by_user_id,
                reason=reason
            )
        )

    def delegate(
        self,
        approver_role: str,
        delegated_to_user_id: UUID,
        acted_by_user_id: Optional[UUID] = None,
        reason: str = ""
    ):
        """
        Delegate workflow to another user
        Source: INFRA-LAY3-002 §3.3
        """
        self._validate_approver_role(approver_role)
        self._validate_transition(WorkflowState.DELEGATED)

        if not delegated_to_user_id:
            raise ValueError("delegated_to_user_id cannot be empty")

        self._delegated_to_user_id = delegated_to_user_id
        self._current_state = WorkflowState.DELEGATED

        self._add_event(
            WorkflowDelegated(
                workflow_id=self._workflow_id.value,
                decision_id=self._decision_id.value,
                tenant_id=self._tenant_id.value,
                from_approver_role=approver_role,
                delegated_to_user_id=delegated_to_user_id,
                acted_by_user_id=acted_by_user_id,
                reason=reason
            )
        )

    def escalate(
        self,
        escalated_to_role: str,
        escalation_reason: str
    ):
        """
        Escalate workflow to higher authority
        Source: INFRA-LAY3-002 §3.3
        """
        self._validate_transition(WorkflowState.ESCALATED)

        if not escalated_to_role:
            raise ValueError("escalated_to_role cannot be empty")
        if not escalation_reason:
            raise ValueError("escalation_reason cannot be empty")

        self._escalated_to_role = escalated_to_role
        self._current_state = WorkflowState.ESCALATED

        self._add_event(
            WorkflowEscalated(
                workflow_id=self._workflow_id.value,
                decision_id=self._decision_id.value,
                tenant_id=self._tenant_id.value,
                from_approver_role=self._approver_role,
                escalated_to_role=escalated_to_role,
                escalation_reason=escalation_reason
            )
        )

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def decision_id(self) -> DecisionId:
        return self._decision_id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def current_state(self) -> WorkflowState:
        return self._current_state

    @property
    def approver_role(self) -> str:
        return self._approver_role

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def delegated_to_user_id(self) -> Optional[UUID]:
        return self._delegated_to_user_id

    @property
    def escalated_to_user_id(self) -> Optional[UUID]:
        return self._escalated_to_user_id

    @property
    def escalated_to_role(self) -> Optional[str]:
        return self._escalated_to_role

    @property
    def completed_at(self) -> Optional[datetime]:
        return self._completed_at

    @property
    def metadata(self) -> Metadata:
        return self._metadata

    def is_terminal(self) -> bool:
        """Check if workflow is in terminal state"""
        return self._current_state.is_terminal()

    def collect_events(self) -> List[DomainEvent]:
        """Collect and clear domain events"""
        events = self._events.copy()
        self._events.clear()
        return events

    def _validate_transition(self, target_state: WorkflowState):
        """Validate state transition per state machine"""
        if not self._current_state.can_transition_to(target_state):
            raise ValueError(
                f"Invalid workflow transition: {self._current_state.value} -> {target_state.value}"
            )

    def _validate_approver_role(self, approver_role: str):
        """Validate approver role matches workflow approver role"""
        if approver_role != self._approver_role:
            raise ValueError(
                f"Approver role mismatch: expected {self._approver_role}, got {approver_role}"
            )

    def _add_event(self, event: DomainEvent):
        """Add domain event to aggregate"""
        self._events.append(event)
