"""
Integration Tests - End-to-End Flow

Tests full request-to-response flow through all layers.
Source: INFRA-LAY3-002 §6 (Integration Testing)
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient

from ..app import create_app
from ..api.dependencies import init_session_factory
from ..repositories import (
    DecisionRepository,
    WorkflowRepository,
    RuleRepository,
    IdempotencyRepository,
    UnitOfWork
)
from ..repositories.models import RuleModel
from ..domain.value_objects import Outcome


# Test database URL for integration tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_app():
    """Create test FastAPI application"""
    # Initialize session factory with test database
    init_session_factory(TEST_DATABASE_URL)

    # Create application
    app = create_app()

    yield app


@pytest.fixture(scope="function")
async def test_client(test_app):
    """Create test HTTP client"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def seed_test_rules(test_db_session):
    """Seed test rules into database"""
    tenant_id = uuid4()
    rule_id = uuid4()

    # Create test rule: ALLOWED for room_id=101
    rule = RuleModel(
        rule_id=rule_id,
        tenant_id=tenant_id,
        rule_name="Test Rule - Allow Room 101",
        evaluation_sequence=1,
        is_active=True,
        conditions={
            "room_id": {"equals": "101"}
        },
        action={
            "outcome": "ALLOWED"
        }
    )

    test_db_session.add(rule)
    await test_db_session.commit()

    return {
        "tenant_id": tenant_id,
        "rule_id": rule_id
    }


class TestEndToEndDecisionFlow:
    """Test complete decision creation flow"""

    @pytest.mark.asyncio
    async def test_create_decision_allowed_happy_path(self, test_client, seed_test_rules):
        """
        Happy path: Create decision with ALLOWED outcome

        Flow: HTTP POST → Use Case → Repository → Database → HTTP Response
        """
        tenant_id = str(seed_test_rules["tenant_id"])

        # Make API request
        response = await test_client.post(
            "/api/v1/decisions",
            json={
                "tenant_id": tenant_id,
                "decision_type": "check_in_approval",
                "context": {"room_id": "101", "guest_count": 2},
                "idempotency_key": "test-req-001"
            }
        )

        # Verify HTTP response
        assert response.status_code == 201
        data = response.json()
        assert data["outcome"] == "ALLOWED"
        assert data["decision_id"] is not None
        assert data["rule_matched_id"] == str(seed_test_rules["rule_id"])
        assert data["workflow_id"] is None  # ALLOWED doesn't create workflow

    @pytest.mark.asyncio
    async def test_create_decision_require_approval_creates_workflow(
        self, test_client, test_db_session
    ):
        """
        Create decision with REQUIRE_APPROVAL outcome → Creates workflow

        Flow: HTTP POST → Decision Created → Workflow Created → HTTP Response
        """
        tenant_id = uuid4()
        rule_id = uuid4()

        # Seed rule: REQUIRE_APPROVAL for high amounts
        rule = RuleModel(
            rule_id=rule_id,
            tenant_id=tenant_id,
            rule_name="Require Approval for High Amounts",
            evaluation_sequence=1,
            is_active=True,
            conditions={
                "amount": {"greater_than": 500}
            },
            action={
                "outcome": "REQUIRE_APPROVAL",
                "required_approver_role": "finance_manager"
            }
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        # Make API request
        response = await test_client.post(
            "/api/v1/decisions",
            json={
                "tenant_id": str(tenant_id),
                "decision_type": "payment_approval",
                "context": {"amount": 1000, "currency": "USD"}
            }
        )

        # Verify HTTP response
        assert response.status_code == 201
        data = response.json()
        assert data["outcome"] == "REQUIRE_APPROVAL"
        assert data["workflow_id"] is not None  # Workflow created

        # Store workflow_id for next test
        workflow_id = data["workflow_id"]

        # Approve the workflow
        approve_response = await test_client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json={
                "tenant_id": str(tenant_id),
                "approver_role": "finance_manager",
                "comment": "Approved for testing"
            }
        )

        # Verify approval response
        assert approve_response.status_code == 200
        approve_data = approve_response.json()
        assert approve_data["current_state"] == "APPROVED"
        assert approve_data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_idempotency_same_key_same_context(self, test_client, seed_test_rules):
        """
        Idempotency: Same key + same context → Same decision (cached)

        Flow: First request creates, second request returns cached
        """
        tenant_id = str(seed_test_rules["tenant_id"])
        idempotency_key = "test-idempotent-001"

        request_payload = {
            "tenant_id": tenant_id,
            "decision_type": "check_in_approval",
            "context": {"room_id": "101"},
            "idempotency_key": idempotency_key
        }

        # First request: Creates decision
        response1 = await test_client.post("/api/v1/decisions", json=request_payload)
        assert response1.status_code == 201
        decision_id_1 = response1.json()["decision_id"]

        # Second request: Returns cached decision
        response2 = await test_client.post("/api/v1/decisions", json=request_payload)
        assert response2.status_code == 201
        decision_id_2 = response2.json()["decision_id"]

        # Should return same decision ID
        assert decision_id_1 == decision_id_2

    @pytest.mark.asyncio
    async def test_idempotency_same_key_different_context_conflict(
        self, test_client, seed_test_rules
    ):
        """
        Idempotency conflict: Same key + different context → 409 error

        Flow: First request creates, second request with different context raises conflict
        """
        tenant_id = str(seed_test_rules["tenant_id"])
        idempotency_key = "test-conflict-001"

        # First request: room_id=101
        response1 = await test_client.post(
            "/api/v1/decisions",
            json={
                "tenant_id": tenant_id,
                "decision_type": "check_in_approval",
                "context": {"room_id": "101"},
                "idempotency_key": idempotency_key
            }
        )
        assert response1.status_code == 201
        existing_decision_id = response1.json()["decision_id"]

        # Second request: room_id=102 (different context!)
        response2 = await test_client.post(
            "/api/v1/decisions",
            json={
                "tenant_id": tenant_id,
                "decision_type": "check_in_approval",
                "context": {"room_id": "102"},  # Different!
                "idempotency_key": idempotency_key
            }
        )

        # Should return 409 Conflict
        assert response2.status_code == 409
        error_data = response2.json()
        assert error_data["error_code"] == "IDEMPOTENCY_CONFLICT"
        assert error_data["details"]["existing_decision_id"] == existing_decision_id

    @pytest.mark.asyncio
    async def test_workflow_not_found_error(self, test_client):
        """
        Error handling: Non-existent workflow → 404
        """
        non_existent_workflow_id = str(uuid4())

        response = await test_client.post(
            f"/api/v1/workflows/{non_existent_workflow_id}/approve",
            json={
                "tenant_id": str(uuid4()),
                "approver_role": "manager"
            }
        )

        # Should return 404
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error_code"] == "WORKFLOW_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_workflow_approver_role_mismatch(
        self, test_client, test_db_session
    ):
        """
        Error handling: Wrong approver role → 403
        """
        tenant_id = uuid4()

        # Create rule requiring senior_manager approval
        rule = RuleModel(
            rule_id=uuid4(),
            tenant_id=tenant_id,
            rule_name="Require Senior Manager",
            evaluation_sequence=1,
            is_active=True,
            conditions={"amount": {"greater_than": 10000}},
            action={
                "outcome": "REQUIRE_APPROVAL",
                "required_approver_role": "senior_manager"
            }
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        # Create decision requiring senior_manager approval
        response = await test_client.post(
            "/api/v1/decisions",
            json={
                "tenant_id": str(tenant_id),
                "decision_type": "payment_approval",
                "context": {"amount": 15000}
            }
        )
        assert response.status_code == 201
        workflow_id = response.json()["workflow_id"]

        # Try to approve with junior_manager role (wrong!)
        approve_response = await test_client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json={
                "tenant_id": str(tenant_id),
                "approver_role": "junior_manager"  # Wrong role!
            }
        )

        # Should return 403
        assert approve_response.status_code == 403
        error_data = approve_response.json()
        assert error_data["error_code"] == "APPROVER_ROLE_MISMATCH"
        assert error_data["details"]["expected"] == "senior_manager"
        assert error_data["details"]["actual"] == "junior_manager"

    @pytest.mark.asyncio
    async def test_workflow_duplicate_approval_rejected(
        self, test_client, test_db_session
    ):
        """
        Error handling: Duplicate approval → 400 Invalid Transition
        """
        tenant_id = uuid4()

        # Create rule requiring approval
        rule = RuleModel(
            rule_id=uuid4(),
            tenant_id=tenant_id,
            rule_name="Require Manager Approval",
            evaluation_sequence=1,
            is_active=True,
            conditions={"key": {"equals": "value"}},
            action={
                "outcome": "REQUIRE_APPROVAL",
                "required_approver_role": "manager"
            }
        )
        test_db_session.add(rule)
        await test_db_session.commit()

        # Create decision requiring approval
        response = await test_client.post(
            "/api/v1/decisions",
            json={
                "tenant_id": str(tenant_id),
                "decision_type": "test_approval",
                "context": {"key": "value"}
            }
        )
        workflow_id = response.json()["workflow_id"]

        # First approval: Success
        approve1 = await test_client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json={
                "tenant_id": str(tenant_id),
                "approver_role": "manager"
            }
        )
        assert approve1.status_code == 200

        # Second approval attempt: Should fail
        approve2 = await test_client.post(
            f"/api/v1/workflows/{workflow_id}/approve",
            json={
                "tenant_id": str(tenant_id),
                "approver_role": "manager"
            }
        )

        # Should return 400 Invalid Transition
        assert approve2.status_code == 400
        error_data = approve2.json()
        assert error_data["error_code"] == "INVALID_WORKFLOW_TRANSITION"
        assert error_data["details"]["from_state"] == "APPROVED"


class TestHealthCheck:
    """Test application health check endpoint"""

    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        """Health check endpoint returns service status"""
        response = await test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "core"
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
