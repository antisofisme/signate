"""
Unit Tests - Use Case Layer

Tests for use case orchestration logic, idempotency, and error handling.
Source: INFRA-LAY3-002 §2 (Use Case Layer)
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from ..use_cases.create_decision import CreateDecisionUseCase, CreateDecisionInput
from ..use_cases.approve_workflow import ApproveWorkflowUseCase, ApproveWorkflowInput
from ..use_cases.reject_workflow import RejectWorkflowUseCase, RejectWorkflowInput
from ..use_cases.exceptions import (
    IdempotencyConflictError,
    WorkflowNotFoundError,
    ApproverRoleMismatchError,
    InvalidWorkflowTransitionError
)
from ..domain.value_objects import Outcome, WorkflowState, Context
from ..domain.aggregates import Decision, Workflow


class TestCreateDecisionUseCase:
    """Test CreateDecision use case orchestration"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for CreateDecisionUseCase"""
        return {
            "uow": AsyncMock(),
            "decision_repository": AsyncMock(),
            "workflow_repository": AsyncMock(),
            "rule_repository": AsyncMock(),
            "idempotency_repository": AsyncMock(),
            "rule_evaluation_service": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_create_decision_allowed_no_workflow(self, mock_dependencies):
        """Create decision with ALLOWED outcome (no workflow)"""
        # Setup
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()
        rule_id = uuid4()

        # Mock rule evaluation to return ALLOWED
        mock_dependencies["rule_repository"].find_active_rules.return_value = []
        mock_dependencies["rule_evaluation_service"].evaluate.return_value = MagicMock(
            outcome=Outcome.ALLOWED,
            rule_matched_id=rule_id,
            rule_version="v1.0"
        )
        mock_dependencies["idempotency_repository"].find.return_value = None

        # Execute
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="check_in_approval",
            context={"room_id": "101", "guest_count": 2}
        )

        output = await use_case.execute(input_dto)

        # Verify
        assert output.outcome == "ALLOWED"
        assert output.rule_matched_id == rule_id
        assert output.workflow_id is None
        assert mock_dependencies["decision_repository"].save.called
        assert not mock_dependencies["workflow_repository"].save.called

    @pytest.mark.asyncio
    async def test_create_decision_require_approval_creates_workflow(self, mock_dependencies):
        """Create decision with REQUIRE_APPROVAL outcome (creates workflow)"""
        # Setup
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()
        rule_id = uuid4()

        # Mock rule evaluation to return REQUIRE_APPROVAL
        mock_dependencies["rule_repository"].find_active_rules.return_value = []
        mock_dependencies["rule_evaluation_service"].evaluate.return_value = MagicMock(
            outcome=Outcome.REQUIRE_APPROVAL,
            rule_matched_id=rule_id,
            rule_version="v1.0",
            required_approver_role="manager"
        )
        mock_dependencies["idempotency_repository"].find.return_value = None

        # Execute
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="payment_approval",
            context={"amount": 1000}
        )

        output = await use_case.execute(input_dto)

        # Verify
        assert output.outcome == "REQUIRE_APPROVAL"
        assert output.workflow_id is not None
        assert mock_dependencies["decision_repository"].save.called
        assert mock_dependencies["workflow_repository"].save.called

    @pytest.mark.asyncio
    async def test_idempotency_cache_hit_same_context(self, mock_dependencies):
        """Idempotency: Same key + same context = cached decision"""
        # Setup
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()
        decision_id = uuid4()
        idempotency_key = "req-12345"
        context = {"room_id": "101"}

        # Mock idempotency cache hit
        mock_dependencies["idempotency_repository"].find.return_value = decision_id
        mock_dependencies["idempotency_repository"].get_context_hash.return_value = use_case._compute_context_hash(
            Context(context)
        )

        # Mock decision retrieval
        cached_decision = Decision.create(
            tenant_id=tenant_id,
            decision_type="check_in",
            context=Context(context),
            outcome=Outcome.ALLOWED
        )
        mock_dependencies["decision_repository"].find_by_id.return_value = cached_decision

        # Execute
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="check_in",
            context=context,
            idempotency_key=idempotency_key
        )

        output = await use_case.execute(input_dto)

        # Verify: Should return cached decision without creating new one
        assert output.decision_id == decision_id
        assert not mock_dependencies["rule_evaluation_service"].evaluate.called

    @pytest.mark.asyncio
    async def test_idempotency_conflict_different_context(self, mock_dependencies):
        """Idempotency: Same key + different context = conflict error"""
        # Setup
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()
        decision_id = uuid4()
        idempotency_key = "req-12345"

        # Mock idempotency cache hit with different context
        mock_dependencies["idempotency_repository"].find.return_value = decision_id

        # Original context hash (different from current)
        original_context = {"room_id": "101"}
        mock_dependencies["idempotency_repository"].get_context_hash.return_value = use_case._compute_context_hash(
            Context(original_context)
        )

        # Execute with different context
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="check_in",
            context={"room_id": "102"},  # Different context!
            idempotency_key=idempotency_key
        )

        # Verify: Should raise IdempotencyConflictError
        with pytest.raises(IdempotencyConflictError) as exc_info:
            await use_case.execute(input_dto)

        assert exc_info.value.existing_decision_id == decision_id

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self, mock_dependencies):
        """Transaction should rollback on repository error"""
        # Setup
        use_case = CreateDecisionUseCase(**mock_dependencies)

        # Mock UOW to track rollback
        mock_dependencies["uow"].__aenter__.return_value = mock_dependencies["uow"]
        mock_dependencies["uow"].__aexit__.return_value = None

        # Mock repository to raise error
        mock_dependencies["rule_repository"].find_active_rules.side_effect = Exception("Database error")

        # Execute
        input_dto = CreateDecisionInput(
            tenant_id=uuid4(),
            decision_type="test",
            context={"key": "value"}
        )

        # Verify: Should propagate exception and rollback
        with pytest.raises(Exception, match="Database error"):
            await use_case.execute(input_dto)

        # UOW should have been entered and exited (rollback)
        assert mock_dependencies["uow"].__aenter__.called
        assert mock_dependencies["uow"].__aexit__.called


class TestApproveWorkflowUseCase:
    """Test ApproveWorkflow use case orchestration"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for ApproveWorkflowUseCase"""
        return {
            "uow": AsyncMock(),
            "workflow_repository": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_approve_workflow_success(self, mock_dependencies):
        """Approve workflow successfully"""
        # Setup
        use_case = ApproveWorkflowUseCase(**mock_dependencies)

        workflow_id = uuid4()
        tenant_id = uuid4()

        # Create mock workflow
        workflow = Workflow.create(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            decision_id=uuid4(),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )
        mock_dependencies["workflow_repository"].find_by_id.return_value = workflow

        # Execute
        input_dto = ApproveWorkflowInput(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            approver_role="manager"
        )

        output = await use_case.execute(input_dto)

        # Verify
        assert output.workflow_id == workflow_id
        assert output.current_state == "APPROVED"
        assert output.completed_at is not None
        assert mock_dependencies["workflow_repository"].save.called

    @pytest.mark.asyncio
    async def test_approve_workflow_not_found(self, mock_dependencies):
        """Approve non-existent workflow raises error"""
        # Setup
        use_case = ApproveWorkflowUseCase(**mock_dependencies)

        workflow_id = uuid4()
        mock_dependencies["workflow_repository"].find_by_id.return_value = None

        # Execute
        input_dto = ApproveWorkflowInput(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            approver_role="manager"
        )

        # Verify
        with pytest.raises(WorkflowNotFoundError) as exc_info:
            await use_case.execute(input_dto)

        assert exc_info.value.workflow_id == workflow_id

    @pytest.mark.asyncio
    async def test_approve_workflow_role_mismatch(self, mock_dependencies):
        """Approve workflow with wrong role raises error"""
        # Setup
        use_case = ApproveWorkflowUseCase(**mock_dependencies)

        workflow_id = uuid4()
        workflow = Workflow.create(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            decision_id=uuid4(),
            required_approver_role="senior_manager",  # Required role
            decision_context=Context({"key": "value"})
        )
        mock_dependencies["workflow_repository"].find_by_id.return_value = workflow

        # Execute with wrong role
        input_dto = ApproveWorkflowInput(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            approver_role="junior_manager"  # Wrong role!
        )

        # Verify
        with pytest.raises(ApproverRoleMismatchError) as exc_info:
            await use_case.execute(input_dto)

        assert exc_info.value.expected == "senior_manager"
        assert exc_info.value.actual == "junior_manager"

    @pytest.mark.asyncio
    async def test_approve_workflow_duplicate_approval(self, mock_dependencies):
        """Duplicate approval of already-approved workflow raises error"""
        # Setup
        use_case = ApproveWorkflowUseCase(**mock_dependencies)

        workflow_id = uuid4()
        workflow = Workflow.create(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            decision_id=uuid4(),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Approve workflow first time
        workflow.approve(approver_role="manager")

        mock_dependencies["workflow_repository"].find_by_id.return_value = workflow

        # Execute: Try to approve again
        input_dto = ApproveWorkflowInput(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            approver_role="manager"
        )

        # Verify: Should raise InvalidWorkflowTransitionError
        with pytest.raises(InvalidWorkflowTransitionError) as exc_info:
            await use_case.execute(input_dto)

        assert exc_info.value.from_state == "APPROVED"


class TestRejectWorkflowUseCase:
    """Test RejectWorkflow use case orchestration"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for RejectWorkflowUseCase"""
        return {
            "uow": AsyncMock(),
            "workflow_repository": AsyncMock()
        }

    @pytest.mark.asyncio
    async def test_reject_workflow_success(self, mock_dependencies):
        """Reject workflow successfully"""
        # Setup
        use_case = RejectWorkflowUseCase(**mock_dependencies)

        workflow_id = uuid4()
        tenant_id = uuid4()

        # Create mock workflow
        workflow = Workflow.create(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            decision_id=uuid4(),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )
        mock_dependencies["workflow_repository"].find_by_id.return_value = workflow

        # Execute
        input_dto = RejectWorkflowInput(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            approver_role="manager",
            reason="Insufficient documentation"
        )

        output = await use_case.execute(input_dto)

        # Verify
        assert output.workflow_id == workflow_id
        assert output.current_state == "REJECTED"
        assert output.completed_at is not None
        assert mock_dependencies["workflow_repository"].save.called

    @pytest.mark.asyncio
    async def test_reject_workflow_after_approval_fails(self, mock_dependencies):
        """Cannot reject an already-approved workflow"""
        # Setup
        use_case = RejectWorkflowUseCase(**mock_dependencies)

        workflow_id = uuid4()
        workflow = Workflow.create(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            decision_id=uuid4(),
            required_approver_role="manager",
            decision_context=Context({"key": "value"})
        )

        # Approve workflow first
        workflow.approve(approver_role="manager")

        mock_dependencies["workflow_repository"].find_by_id.return_value = workflow

        # Execute: Try to reject after approval
        input_dto = RejectWorkflowInput(
            workflow_id=workflow_id,
            tenant_id=uuid4(),
            approver_role="manager",
            reason="Changed my mind"
        )

        # Verify: Should raise InvalidWorkflowTransitionError
        with pytest.raises(InvalidWorkflowTransitionError) as exc_info:
            await use_case.execute(input_dto)

        assert exc_info.value.from_state == "APPROVED"
        assert exc_info.value.to_state == "REJECTED"
