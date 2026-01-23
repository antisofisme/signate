"""
PHASE 1 BYPASS TESTS - NON-NEGOTIABLE GATE

These tests verify that the enforcement layer cannot be bypassed.
ALL tests MUST pass before Phase 1 is considered complete.

Source: Phase 1 Requirements
- Direct DB write → FAIL (or tracked in audit)
- UPDATE decision → FAIL
- DELETE decision → FAIL
- Cross-tenant access → empty result
- createDecision without rule → DENIED (fail-closed)
- Retry with idempotency_key → same decision_id

CRITICAL: If any of these tests fail, STOP implementation.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from ..domain.value_objects import TenantId, Context, Outcome
from ..domain.aggregates import Decision, Workflow
from ..use_cases.create_decision import CreateDecisionUseCase
from ..use_cases.dtos import CreateDecisionInput


# =============================================================================
# BYPASS TEST 1: UPDATE on decisions table MUST FAIL
# =============================================================================

class TestDecisionImmutability:
    """
    CRITICAL: Decisions are immutable. UPDATE and DELETE must fail at DB level.
    Source: INFRA-DEC-001 (Decision Immutability), Migration 002
    """

    @pytest.mark.asyncio
    async def test_update_decision_outcome_fails(self, test_db_session, seeded_decision):
        """
        BYPASS TEST: Attempting to UPDATE decision.outcome MUST raise exception
        """
        decision_id = seeded_decision["decision_id"]

        # Attempt to update outcome (should fail via trigger)
        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE decisions
                    SET outcome = 'ALLOWED'
                    WHERE decision_id = :decision_id
                """),
                {"decision_id": decision_id}
            )
            await test_db_session.commit()

        # Verify it's an immutability violation
        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_decision_context_fails(self, test_db_session, seeded_decision):
        """
        BYPASS TEST: Attempting to UPDATE decision.context MUST raise exception
        """
        decision_id = seeded_decision["decision_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE decisions
                    SET context = '{"tampered": true}'::jsonb
                    WHERE decision_id = :decision_id
                """),
                {"decision_id": decision_id}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_decision_fails(self, test_db_session, seeded_decision):
        """
        BYPASS TEST: Attempting to DELETE decision MUST raise exception
        """
        decision_id = seeded_decision["decision_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    DELETE FROM decisions
                    WHERE decision_id = :decision_id
                """),
                {"decision_id": decision_id}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()


# =============================================================================
# BYPASS TEST 2: UPDATE/DELETE on event_log MUST FAIL
# =============================================================================

class TestEventLogImmutability:
    """
    CRITICAL: Event log is immutable. UPDATE and DELETE must fail.
    Source: INFRA-DEC-006 (Event & Audit as Immutable Facts)
    """

    @pytest.mark.asyncio
    async def test_update_event_log_fails(self, test_db_session, seeded_event):
        """
        BYPASS TEST: Attempting to UPDATE event_log MUST raise exception
        """
        event_id = seeded_event["event_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE event_log
                    SET payload = '{"tampered": true}'::jsonb
                    WHERE event_id = :event_id
                """),
                {"event_id": event_id}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_event_log_fails(self, test_db_session, seeded_event):
        """
        BYPASS TEST: Attempting to DELETE event_log MUST raise exception
        """
        event_id = seeded_event["event_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    DELETE FROM event_log
                    WHERE event_id = :event_id
                """),
                {"event_id": event_id}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()


# =============================================================================
# BYPASS TEST 3: UPDATE/DELETE on workflow_transitions MUST FAIL
# =============================================================================

class TestWorkflowTransitionImmutability:
    """
    CRITICAL: Workflow transitions are immutable (audit trail).
    Source: INFRA-LAY3-002 §3
    """

    @pytest.mark.asyncio
    async def test_update_workflow_transition_fails(self, test_db_session, seeded_transition):
        """
        BYPASS TEST: Attempting to UPDATE workflow_transitions MUST raise exception
        """
        transition_id = seeded_transition["transition_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE workflow_transitions
                    SET to_state = 'TAMPERED'
                    WHERE transition_id = :transition_id
                """),
                {"transition_id": transition_id}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_workflow_transition_fails(self, test_db_session, seeded_transition):
        """
        BYPASS TEST: Attempting to DELETE workflow_transitions MUST raise exception
        """
        transition_id = seeded_transition["transition_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    DELETE FROM workflow_transitions
                    WHERE transition_id = :transition_id
                """),
                {"transition_id": transition_id}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()


# =============================================================================
# BYPASS TEST 4: CROSS-TENANT ACCESS MUST RETURN EMPTY
# =============================================================================

class TestTenantIsolation:
    """
    CRITICAL: Tenant isolation via RLS. Cross-tenant queries return 0 rows.
    Source: INFRA-DEC-002 (Tenancy Model), Migration 003
    """

    @pytest.mark.asyncio
    async def test_cross_tenant_query_returns_empty(self, test_db_session):
        """
        BYPASS TEST: Query with wrong tenant_id MUST return 0 rows
        """
        tenant_a = uuid4()
        tenant_b = uuid4()  # Different tenant
        decision_id = uuid4()

        # Insert decision for tenant_a
        await test_db_session.execute(
            text("""
                INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome, created_at)
                VALUES (:decision_id, :tenant_id, 'test.decision', '{"key": "value"}'::jsonb, 'DENIED', NOW())
            """),
            {"decision_id": decision_id, "tenant_id": tenant_a}
        )
        await test_db_session.commit()

        # Set tenant context to tenant_b (different tenant)
        await test_db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_b)}
        )

        # Query should return 0 rows (RLS blocks access)
        result = await test_db_session.execute(
            text("SELECT * FROM decisions WHERE decision_id = :decision_id"),
            {"decision_id": decision_id}
        )
        rows = result.fetchall()

        # MUST return empty for cross-tenant access
        assert len(rows) == 0, "Cross-tenant query MUST return 0 rows"

    @pytest.mark.asyncio
    async def test_same_tenant_query_returns_data(self, test_db_session):
        """
        VERIFICATION: Same tenant query MUST return data
        """
        tenant_id = uuid4()
        decision_id = uuid4()

        # Insert decision
        await test_db_session.execute(
            text("""
                INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome, created_at)
                VALUES (:decision_id, :tenant_id, 'test.decision', '{"key": "value"}'::jsonb, 'DENIED', NOW())
            """),
            {"decision_id": decision_id, "tenant_id": tenant_id}
        )
        await test_db_session.commit()

        # Set tenant context to same tenant
        await test_db_session.execute(
            text("SET app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )

        # Query should return 1 row
        result = await test_db_session.execute(
            text("SELECT * FROM decisions WHERE decision_id = :decision_id"),
            {"decision_id": decision_id}
        )
        rows = result.fetchall()

        assert len(rows) == 1, "Same-tenant query MUST return data"


# =============================================================================
# BYPASS TEST 5: createDecision WITHOUT MATCHING RULE → DENIED (Fail-Closed)
# =============================================================================

class TestFailClosedBehavior:
    """
    CRITICAL: No matching rule → DENIED (fail-closed).
    Source: INFRA-DEC-001 (Fail-Closed Principle), INFRA-LAY3-002 §1.1
    """

    @pytest.mark.asyncio
    async def test_no_rules_returns_denied(self, mock_dependencies):
        """
        BYPASS TEST: createDecision with NO rules MUST return DENIED
        """
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()

        # Mock rule repository to return EMPTY rules list
        mock_dependencies["rule_repository"].find_active_rules.return_value = []
        mock_dependencies["idempotency_repository"].find.return_value = None

        # Execute
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="unknown.action",
            context={"any": "context"}
        )

        output = await use_case.execute(input_dto)

        # MUST return DENIED (fail-closed)
        assert output.outcome == "DENIED", "No rules MUST result in DENIED (fail-closed)"
        assert output.rule_matched_id is None, "No rule matched when no rules exist"

    @pytest.mark.asyncio
    async def test_no_matching_rule_returns_denied(self, mock_dependencies):
        """
        BYPASS TEST: createDecision with rules that DON'T MATCH MUST return DENIED
        """
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()
        rule_id = uuid4()

        # Mock rule repository to return rules that don't match context
        from ..use_cases.interfaces import Rule, RuleId, RuleVersion
        mock_dependencies["rule_repository"].find_active_rules.return_value = [
            Rule(
                rule_id=RuleId(rule_id),
                rule_name="Test Rule",
                version=RuleVersion("1.0"),
                conditions={"operator": "==", "field": "amount", "value": 1000},  # Only matches amount=1000
                action={"outcome": "ALLOWED"},
                evaluation_sequence=1
            )
        ]
        mock_dependencies["idempotency_repository"].find.return_value = None

        # Execute with context that doesn't match
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="payment.approval",
            context={"amount": 500}  # Rule expects 1000
        )

        output = await use_case.execute(input_dto)

        # MUST return DENIED (no rule matched)
        assert output.outcome == "DENIED", "Non-matching rules MUST result in DENIED"


# =============================================================================
# BYPASS TEST 6: IDEMPOTENCY - Same Key → Same Decision ID
# =============================================================================

class TestIdempotencyEnforcement:
    """
    CRITICAL: Idempotency key must deduplicate requests.
    Source: INFRA-LAY3-002 §2.2 (Idempotency)
    """

    @pytest.mark.asyncio
    async def test_same_idempotency_key_returns_same_decision(self, mock_dependencies):
        """
        BYPASS TEST: Same idempotency_key MUST return same decision_id
        """
        use_case = CreateDecisionUseCase(**mock_dependencies)

        tenant_id = uuid4()
        cached_decision_id = uuid4()
        idempotency_key = "idempotent-request-001"
        context = {"key": "value"}

        # Mock idempotency cache HIT
        mock_dependencies["idempotency_repository"].find.return_value = cached_decision_id
        mock_dependencies["idempotency_repository"].get_context_hash.return_value = use_case._compute_context_hash(
            Context(context)
        )

        # Mock cached decision retrieval
        cached_decision = Decision.create(
            tenant_id=TenantId(tenant_id),
            decision_type="test.decision",
            context=Context(context),
            outcome=Outcome.ALLOWED
        )
        # Override decision_id
        cached_decision._decision_id = cached_decision_id
        mock_dependencies["decision_repository"].find_by_id.return_value = cached_decision

        # Execute
        input_dto = CreateDecisionInput(
            tenant_id=tenant_id,
            decision_type="test.decision",
            context=context,
            idempotency_key=idempotency_key
        )

        output = await use_case.execute(input_dto)

        # MUST return cached decision (same decision_id)
        assert output.decision_id == cached_decision_id, "Idempotent request MUST return same decision_id"
        # Rule evaluation should NOT be called (cached)
        assert not mock_dependencies["rule_evaluation_service"].evaluate.called, \
            "Rule evaluation should NOT be called for cached idempotent request"


# =============================================================================
# BYPASS TEST 7: UPDATE/DELETE on idempotency_cache MUST FAIL
# =============================================================================

class TestIdempotencyCacheImmutability:
    """
    CRITICAL: Idempotency cache entries are immutable.
    Source: Migration 002
    """

    @pytest.mark.asyncio
    async def test_update_idempotency_cache_fails(self, test_db_session, seeded_idempotency):
        """
        BYPASS TEST: Attempting to UPDATE idempotency_cache MUST raise exception
        """
        tenant_id = seeded_idempotency["tenant_id"]
        idempotency_key = seeded_idempotency["idempotency_key"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE idempotency_cache
                    SET context_hash = 'tampered_hash'
                    WHERE tenant_id = :tenant_id AND idempotency_key = :idempotency_key
                """),
                {"tenant_id": tenant_id, "idempotency_key": idempotency_key}
            )
            await test_db_session.commit()

        assert "immutability" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()


# =============================================================================
# BYPASS TEST 8: Terminal Workflow State Immutability
# =============================================================================

class TestTerminalWorkflowImmutability:
    """
    CRITICAL: Workflows in terminal state (APPROVED/REJECTED) cannot be modified.
    Source: Migration 002 (prevent_terminal_workflow_modification trigger)
    """

    @pytest.mark.asyncio
    async def test_approved_workflow_cannot_change_state(self, test_db_session, seeded_approved_workflow):
        """
        BYPASS TEST: Approved workflow.current_state CANNOT be changed
        """
        workflow_id = seeded_approved_workflow["workflow_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE workflows
                    SET current_state = 'REJECTED'
                    WHERE workflow_id = :workflow_id
                """),
                {"workflow_id": workflow_id}
            )
            await test_db_session.commit()

        assert "terminal" in str(exc_info.value).lower() or "cannot be modified" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_rejected_workflow_cannot_change_state(self, test_db_session, seeded_rejected_workflow):
        """
        BYPASS TEST: Rejected workflow.current_state CANNOT be changed
        """
        workflow_id = seeded_rejected_workflow["workflow_id"]

        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("""
                    UPDATE workflows
                    SET current_state = 'APPROVED'
                    WHERE workflow_id = :workflow_id
                """),
                {"workflow_id": workflow_id}
            )
            await test_db_session.commit()

        assert "terminal" in str(exc_info.value).lower() or "cannot be modified" in str(exc_info.value).lower()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for use case tests"""
    from unittest.mock import AsyncMock, MagicMock

    mock_uow = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None

    return {
        "uow": mock_uow,
        "decision_repository": AsyncMock(),
        "workflow_repository": AsyncMock(),
        "rule_repository": AsyncMock(),
        "idempotency_repository": AsyncMock(),
        "rule_evaluation_service": AsyncMock()
    }


@pytest.fixture
async def seeded_decision(test_db_session):
    """Seed a test decision into database"""
    decision_id = uuid4()
    tenant_id = uuid4()

    await test_db_session.execute(
        text("""
            INSERT INTO decisions (decision_id, tenant_id, decision_type, context, outcome, created_at)
            VALUES (:decision_id, :tenant_id, 'test.decision', '{"key": "value"}'::jsonb, 'DENIED', NOW())
        """),
        {"decision_id": decision_id, "tenant_id": tenant_id}
    )
    await test_db_session.commit()

    return {"decision_id": decision_id, "tenant_id": tenant_id}


@pytest.fixture
async def seeded_event(test_db_session, seeded_decision):
    """Seed a test event into database"""
    event_id = uuid4()

    await test_db_session.execute(
        text("""
            INSERT INTO event_log (event_id, event_type, tenant_id, aggregate_id, aggregate_type, payload, occurred_at, recorded_at)
            VALUES (:event_id, 'decision.created', :tenant_id, :aggregate_id, 'decision', '{"test": true}'::jsonb, NOW(), NOW())
        """),
        {
            "event_id": event_id,
            "tenant_id": seeded_decision["tenant_id"],
            "aggregate_id": seeded_decision["decision_id"]
        }
    )
    await test_db_session.commit()

    return {"event_id": event_id}


@pytest.fixture
async def seeded_transition(test_db_session, seeded_decision):
    """Seed a test workflow and transition"""
    workflow_id = uuid4()
    transition_id = uuid4()
    tenant_id = seeded_decision["tenant_id"]

    # Create workflow
    await test_db_session.execute(
        text("""
            INSERT INTO workflows (workflow_id, decision_id, tenant_id, current_state, approver_role, created_at)
            VALUES (:workflow_id, :decision_id, :tenant_id, 'PENDING_APPROVAL', 'manager', NOW())
        """),
        {
            "workflow_id": workflow_id,
            "decision_id": seeded_decision["decision_id"],
            "tenant_id": tenant_id
        }
    )

    # Create transition
    await test_db_session.execute(
        text("""
            INSERT INTO workflow_transitions (transition_id, workflow_id, tenant_id, from_state, to_state, created_at)
            VALUES (:transition_id, :workflow_id, :tenant_id, 'CREATED', 'PENDING_APPROVAL', NOW())
        """),
        {
            "transition_id": transition_id,
            "workflow_id": workflow_id,
            "tenant_id": tenant_id
        }
    )
    await test_db_session.commit()

    return {"transition_id": transition_id, "workflow_id": workflow_id}


@pytest.fixture
async def seeded_idempotency(test_db_session, seeded_decision):
    """Seed a test idempotency cache entry"""
    tenant_id = seeded_decision["tenant_id"]
    idempotency_key = "test-idempotency-key"

    await test_db_session.execute(
        text("""
            INSERT INTO idempotency_cache (tenant_id, idempotency_key, decision_id, context_hash, created_at)
            VALUES (:tenant_id, :idempotency_key, :decision_id, 'test_hash', NOW())
        """),
        {
            "tenant_id": tenant_id,
            "idempotency_key": idempotency_key,
            "decision_id": seeded_decision["decision_id"]
        }
    )
    await test_db_session.commit()

    return {"tenant_id": tenant_id, "idempotency_key": idempotency_key}


@pytest.fixture
async def seeded_approved_workflow(test_db_session, seeded_decision):
    """Seed an approved workflow"""
    workflow_id = uuid4()
    tenant_id = seeded_decision["tenant_id"]

    await test_db_session.execute(
        text("""
            INSERT INTO workflows (workflow_id, decision_id, tenant_id, current_state, approver_role, created_at, completed_at)
            VALUES (:workflow_id, :decision_id, :tenant_id, 'APPROVED', 'manager', NOW(), NOW())
        """),
        {
            "workflow_id": workflow_id,
            "decision_id": seeded_decision["decision_id"],
            "tenant_id": tenant_id
        }
    )
    await test_db_session.commit()

    return {"workflow_id": workflow_id}


@pytest.fixture
async def seeded_rejected_workflow(test_db_session, seeded_decision):
    """Seed a rejected workflow"""
    workflow_id = uuid4()
    tenant_id = seeded_decision["tenant_id"]

    await test_db_session.execute(
        text("""
            INSERT INTO workflows (workflow_id, decision_id, tenant_id, current_state, approver_role, created_at, completed_at)
            VALUES (:workflow_id, :decision_id, :tenant_id, 'REJECTED', 'manager', NOW(), NOW())
        """),
        {
            "workflow_id": workflow_id,
            "decision_id": seeded_decision["decision_id"],
            "tenant_id": tenant_id
        }
    )
    await test_db_session.commit()

    return {"workflow_id": workflow_id}
