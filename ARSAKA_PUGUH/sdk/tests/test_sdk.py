"""
SDK Unit Tests

Tests for SDK validation and behavior.
SDK is a THIN ADAPTER - it does NOT contain business logic.

Source: Phase 2 Requirements
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from infra_sdk import (
    InfraClient,
    TenantContext,
    SubjectContext,
    RequestContext,
    CreateDecisionRequest,
    CreateDecisionResponse,
    GetDecisionRequest,
    WorkflowActionRequest,
    WorkflowAction,
)
from infra_sdk.exceptions import (
    InfraSDKError,
    MissingContextError,
    ValidationError,
    CoreAPIError,
    IdempotencyRequiredError,
)


# =============================================================================
# CONTEXT VALIDATION TESTS
# =============================================================================

class TestTenantContext:
    """Test TenantContext validation"""

    def test_tenant_id_required(self):
        """TenantContext requires tenant_id"""
        with pytest.raises(ValueError):
            TenantContext(tenant_id=None)

    def test_valid_tenant_context(self):
        """Valid TenantContext creation"""
        tenant_id = uuid4()
        ctx = TenantContext(tenant_id=tenant_id)
        assert ctx.tenant_id == tenant_id


class TestSubjectContext:
    """Test SubjectContext validation"""

    def test_subject_id_required(self):
        """SubjectContext requires subject_id"""
        with pytest.raises(ValueError):
            SubjectContext(subject_id=None, subject_type="user")

    def test_subject_type_must_be_valid(self):
        """SubjectContext requires valid subject_type"""
        with pytest.raises(ValueError):
            SubjectContext(subject_id=uuid4(), subject_type="invalid")

    def test_valid_subject_context(self):
        """Valid SubjectContext creation"""
        subject_id = uuid4()
        ctx = SubjectContext(subject_id=subject_id, subject_type="user")
        assert ctx.subject_id == subject_id
        assert ctx.subject_type == "user"


class TestRequestContext:
    """Test RequestContext validation"""

    def test_tenant_required(self):
        """RequestContext requires tenant"""
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        with pytest.raises(ValueError):
            RequestContext(
                tenant=None,
                subject=subject,
                trace_id=uuid4(),
                idempotency_key="test"
            )

    def test_subject_required(self):
        """RequestContext requires subject"""
        tenant = TenantContext(tenant_id=uuid4())
        with pytest.raises(ValueError):
            RequestContext(
                tenant=tenant,
                subject=None,
                trace_id=uuid4(),
                idempotency_key="test"
            )

    def test_trace_id_required(self):
        """RequestContext requires trace_id"""
        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        with pytest.raises(ValueError):
            RequestContext(
                tenant=tenant,
                subject=subject,
                trace_id=None,
                idempotency_key="test"
            )


# =============================================================================
# CREATE DECISION REQUEST TESTS
# =============================================================================

class TestCreateDecisionRequest:
    """Test CreateDecisionRequest validation"""

    def test_idempotency_key_required(self):
        """CreateDecisionRequest requires idempotency_key"""
        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key=""  # Empty
        )

        with pytest.raises(ValueError):
            CreateDecisionRequest(
                context=context,
                decision_type="test.decision",
                decision_context={"key": "value"}
            )

    def test_decision_type_required(self):
        """CreateDecisionRequest requires decision_type"""
        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key="test-key"
        )

        with pytest.raises(ValueError):
            CreateDecisionRequest(
                context=context,
                decision_type="",  # Empty
                decision_context={"key": "value"}
            )

    def test_valid_create_decision_request(self):
        """Valid CreateDecisionRequest creation"""
        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key="test-key"
        )

        request = CreateDecisionRequest(
            context=context,
            decision_type="test.decision",
            decision_context={"key": "value"}
        )

        assert request.decision_type == "test.decision"


# =============================================================================
# WORKFLOW ACTION REQUEST TESTS
# =============================================================================

class TestWorkflowActionRequest:
    """Test WorkflowActionRequest validation"""

    def test_delegate_requires_user_id(self):
        """DELEGATE action requires delegate_to_user_id"""
        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key="test-key"
        )

        with pytest.raises(ValueError):
            WorkflowActionRequest(
                context=context,
                workflow_id=uuid4(),
                action=WorkflowAction.DELEGATE,
                delegate_to_user_id=None  # Missing!
            )

    def test_escalate_requires_role(self):
        """ESCALATE action requires escalate_to_role"""
        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key="test-key"
        )

        with pytest.raises(ValueError):
            WorkflowActionRequest(
                context=context,
                workflow_id=uuid4(),
                action=WorkflowAction.ESCALATE,
                escalate_to_role=None  # Missing!
            )


# =============================================================================
# INFRA CLIENT TESTS
# =============================================================================

class TestInfraClient:
    """Test InfraClient behavior"""

    def test_core_api_url_required(self):
        """InfraClient requires core_api_url"""
        with pytest.raises(ValidationError):
            InfraClient(core_api_url="")

    def test_valid_client_creation(self):
        """Valid InfraClient creation"""
        client = InfraClient(core_api_url="http://localhost:8000")
        assert client._core_api_url == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """InfraClient works as async context manager"""
        async with InfraClient(core_api_url="http://localhost:8000") as client:
            assert client._http_client is not None

    @pytest.mark.asyncio
    async def test_create_decision_propagates_headers(self):
        """create_decision propagates context as headers"""
        tenant_id = uuid4()
        subject_id = uuid4()
        trace_id = uuid4()

        async with InfraClient(core_api_url="http://localhost:8000") as client:
            # Mock HTTP client
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "decision_id": str(uuid4()),
                "outcome": "DENIED",
                "rule_matched_id": None,
                "workflow_id": None,
                "created_at": datetime.utcnow().isoformat(),
            }

            with patch.object(client._http_client, "post", return_value=mock_response) as mock_post:
                context = RequestContext(
                    tenant=TenantContext(tenant_id=tenant_id),
                    subject=SubjectContext(subject_id=subject_id, subject_type="user"),
                    trace_id=trace_id,
                    idempotency_key="test-key"
                )

                request = CreateDecisionRequest(
                    context=context,
                    decision_type="test.decision",
                    decision_context={"key": "value"}
                )

                await client.create_decision(request)

                # Verify headers were set
                call_kwargs = mock_post.call_args[1]
                headers = call_kwargs["headers"]

                assert headers["X-Tenant-ID"] == str(tenant_id)
                assert headers["X-Subject-ID"] == str(subject_id)
                assert headers["X-Trace-ID"] == str(trace_id)
                assert headers["X-Idempotency-Key"] == "test-key"

    @pytest.mark.asyncio
    async def test_error_response_raises_core_api_error(self):
        """Error response from Core raises CoreAPIError"""
        async with InfraClient(core_api_url="http://localhost:8000") as client:
            # Mock error response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "message": "Bad request",
                "error_code": "VALIDATION_ERROR",
            }

            with patch.object(client._http_client, "post", return_value=mock_response):
                context = RequestContext(
                    tenant=TenantContext(tenant_id=uuid4()),
                    subject=SubjectContext(subject_id=uuid4(), subject_type="user"),
                    trace_id=uuid4(),
                    idempotency_key="test-key"
                )

                request = CreateDecisionRequest(
                    context=context,
                    decision_type="test.decision",
                    decision_context={"key": "value"}
                )

                with pytest.raises(CoreAPIError) as exc_info:
                    await client.create_decision(request)

                assert exc_info.value.status_code == 400
                assert exc_info.value.core_error_code == "VALIDATION_ERROR"
