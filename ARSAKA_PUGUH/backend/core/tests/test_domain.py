"""
Unit Tests - Domain Layer

Tests for value objects, aggregates, and domain events.
Source: INFRA-LAY3-002 §1 (Domain Layer)
"""

import pytest
from uuid import uuid4
from datetime import datetime

from ..domain.value_objects import (
    TenantId,
    DecisionId,
    WorkflowId,
    RuleId,
    IdempotencyKey,
    Outcome,
    WorkflowState,
    Context
)
from ..domain.aggregates import Decision, Workflow
from ..domain.events import (
    DecisionCreated,
    WorkflowApproved,
    WorkflowRejected,
    WorkflowDelegated,
    WorkflowEscalated
)


class TestValueObjects:
    """Test value objects immutability and validation"""

    def test_context_must_be_flat(self):
        """Context should reject nested structures"""
        # Valid flat context
        flat_context = Context({"room_id": "101", "guest_count": 2})
        assert flat_context.data == {"room_id": "101", "guest_count": 2}

        # Invalid nested context
        with pytest.raises(ValueError, match="Context must be flat"):
            Context({"nested": {"key": "value"}})

        with pytest.raises(ValueError, match="Context must be flat"):
            Context({"list": [1, 2, 3]})

    def test_context_to_dict(self):
        """Context should serialize to dictionary"""
        context = Context({"key": "value", "number": 42})
        assert context.to_dict() == {"key": "value", "number": 42}

    def test_idempotency_key_validation(self):
        """IdempotencyKey should validate format"""
        # Valid keys
        IdempotencyKey("valid-key-123")
        IdempotencyKey("a" * 255)  # Max length

        # Invalid keys
        with pytest.raises(ValueError, match="cannot be empty"):
            IdempotencyKey("")

        with pytest.raises(ValueError, match="exceeds maximum length"):
            IdempotencyKey("a" * 256)

    def test_workflow_state_transitions(self):
        """WorkflowState should validate allowed transitions"""
        # Valid transitions from PENDING_APPROVAL
        assert WorkflowState.PENDING_APPROVAL.can_transition_to(WorkflowState.APPROVED)
        assert WorkflowState.PENDING_APPROVAL.can_transition_to(WorkflowState.REJECTED)
        assert WorkflowState.PENDING_APPROVAL.can_transition_to(WorkflowState.DELEGATED)
        assert WorkflowState.PENDING_APPROVAL.can_transition_to(WorkflowState.ESCALATED)

        # Invalid transitions (terminal states)
        assert not WorkflowState.APPROVED.can_transition_to(WorkflowState.REJECTED)
        assert not WorkflowState.REJECTED.can_transition_to(WorkflowState.APPROVED)

        # Invalid self-transition
        assert not WorkflowState.PENDING_APPROVAL.can_transition_to(WorkflowState.PENDING_APPROVAL)


class TestDecisionAggregate:
    """Test Decision aggregate business logic"""

    def test_create_decision_allowed(self):
        """Decision creation with ALLOWED outcome"""
        tenant_id = TenantId(uuid4())
        decision_type = "check_in_approval"
        context = Context({"room_id": "101"})
        outcome = Outcome.ALLOWED
        rule_id = RuleId(uuid4())

        decision = Decision.create(
            tenant_id=tenant_id,
            decision_type=decision_type,
            context=context,
            outcome=outcome,
            rule_matched_id=rule_id,
            rule_version="v1.0"
        )

        # Verify aggregate state
        assert decision.tenant_id == tenant_id
        assert decision.decision_type == decision_type
        assert decision.outcome == outcome
        assert decision.rule_matched_id == rule_id
        assert decision.rule_version == "v1.0"
        assert decision.workflow_id is None

        # Verify domain events
        events = decision.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], DecisionCreated)
        assert events[0].decision_id == decision.decision_id.value
        assert events[0].outcome == "ALLOWED"

    def test_create_decision_require_approval(self):
        """Decision creation with REQUIRE_APPROVAL outcome should create workflow"""
        tenant_id = TenantId(uuid4())
        outcome = Outcome.REQUIRE_APPROVAL
        context = Context({"amount": 1000})

        decision = Decision.create(
            tenant_id=tenant_id,
            decision_type="payment_approval",
            context=context,
            outcome=outcome,
            rule_matched_id=RuleId(uuid4()),
            required_approver_role="finance_manager"
        )

        # Should indicate workflow is required
        assert decision.requires_workflow()
        assert decision.outcome == Outcome.REQUIRE_APPROVAL

        # Events collected
        events = decision.collect_events()
        assert len(events) == 1
        assert events[0].outcome == "REQUIRE_APPROVAL"

    def test_decision_immutability(self):
        """Decision should be immutable after creation"""
        decision = Decision.create(
            tenant_id=TenantId(uuid4()),
            decision_type="test",
            context=Context({"key": "value"}),
            outcome=Outcome.ALLOWED
        )

        # Attempting to modify should raise error (frozen dataclass)
        with pytest.raises(Exception):  # FrozenInstanceError
            decision.outcome = Outcome.DENIED


class TestWorkflowAggregate:
    """Test Workflow aggregate business logic"""

    def test_create_workflow(self):
        """Workflow creation"""
        workflow_id = WorkflowId(uuid4())
        tenant_id = TenantId(uuid4())
        decision_id = DecisionId(uuid4())

        workflow = Workflow.create(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            decision_id=decision_id,
            required_approver_role="manager",
            decision_context=Context({"amount": 500})
        )

        # Verify initial state
        assert workflow.workflow_id == workflow_id
        assert workflow.current_state == WorkflowState.PENDING_APPROVAL
        assert workflow.required_approver_role == "manager"
        assert workflow.completed_at is None

    def test_workflow_approve(self):
        """Workflow approval transition"""
        workflow = Workflow.create(
            workflow_id=WorkflowId(uuid4()),
            tenant_id=TenantId(uuid4()),
            decision_id=DecisionId(uuid4()),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Approve workflow
        user_id = uuid4()
        workflow.approve(
            approver_role="manager",
            acted_by_user_id=user_id,
            comment="Looks good"
        )

        # Verify state change
        assert workflow.current_state == WorkflowState.APPROVED
        assert workflow.completed_at is not None

        # Verify domain events
        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], WorkflowApproved)
        assert events[0].acted_by_user_id == user_id
        assert events[0].comment == "Looks good"

    def test_workflow_reject(self):
        """Workflow rejection transition"""
        workflow = Workflow.create(
            workflow_id=WorkflowId(uuid4()),
            tenant_id=TenantId(uuid4()),
            decision_id=DecisionId(uuid4()),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Reject workflow
        workflow.reject(
            approver_role="manager",
            reason="Insufficient documentation"
        )

        # Verify state change
        assert workflow.current_state == WorkflowState.REJECTED
        assert workflow.completed_at is not None

        # Verify domain events
        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], WorkflowRejected)
        assert events[0].reason == "Insufficient documentation"

    def test_workflow_approver_role_mismatch(self):
        """Workflow should reject wrong approver role"""
        workflow = Workflow.create(
            workflow_id=WorkflowId(uuid4()),
            tenant_id=TenantId(uuid4()),
            decision_id=DecisionId(uuid4()),
            required_approver_role="senior_manager",
            decision_context=Context({"key": "value"})
        )

        # Attempt approval with wrong role
        with pytest.raises(ValueError, match="Approver role mismatch"):
            workflow.approve(approver_role="junior_manager")

    def test_workflow_invalid_transition(self):
        """Workflow should reject invalid state transitions"""
        workflow = Workflow.create(
            workflow_id=WorkflowId(uuid4()),
            tenant_id=TenantId(uuid4()),
            decision_id=DecisionId(uuid4()),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Approve workflow (terminal state)
        workflow.approve(approver_role="manager")

        # Attempt to reject after approval should fail
        with pytest.raises(ValueError, match="Invalid workflow transition"):
            workflow.reject(approver_role="manager", reason="Too late")

    def test_workflow_delegate(self):
        """Workflow delegation"""
        workflow = Workflow.create(
            workflow_id=WorkflowId(uuid4()),
            tenant_id=TenantId(uuid4()),
            decision_id=DecisionId(uuid4()),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Delegate to another user
        delegated_to = uuid4()
        workflow.delegate(
            approver_role="manager",
            delegated_to_user_id=delegated_to,
            reason="Out of office"
        )

        # Verify state change
        assert workflow.current_state == WorkflowState.DELEGATED

        # Verify domain events
        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], WorkflowDelegated)
        assert events[0].delegated_to_user_id == delegated_to

    def test_workflow_escalate(self):
        """Workflow escalation"""
        workflow = Workflow.create(
            workflow_id=WorkflowId(uuid4()),
            tenant_id=TenantId(uuid4()),
            decision_id=DecisionId(uuid4()),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Escalate to higher role
        workflow.escalate(
            escalated_to_role="senior_manager",
            escalation_reason="Requires senior approval"
        )

        # Verify state change
        assert workflow.current_state == WorkflowState.ESCALATED

        # Verify domain events
        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], WorkflowEscalated)
        assert events[0].escalated_to_role == "senior_manager"


class TestDomainEvents:
    """Test domain event structure and serialization"""

    def test_decision_created_event(self):
        """DecisionCreated event structure"""
        event = DecisionCreated(
            decision_id=uuid4(),
            tenant_id=uuid4(),
            decision_type="test",
            outcome="ALLOWED",
            rule_matched_id=uuid4(),
            rule_version="v1.0",
            context_summary={"key": "value"},
            latency_ms=50
        )

        # Verify event attributes
        assert event.outcome == "ALLOWED"
        assert event.latency_ms == 50
        assert isinstance(event.occurred_at, datetime)

    def test_workflow_approved_event(self):
        """WorkflowApproved event structure"""
        event = WorkflowApproved(
            workflow_id=uuid4(),
            tenant_id=uuid4(),
            approver_role="manager",
            acted_by_user_id=uuid4(),
            comment="Approved"
        )

        # Verify event attributes
        assert event.approver_role == "manager"
        assert event.comment == "Approved"
        assert isinstance(event.occurred_at, datetime)
