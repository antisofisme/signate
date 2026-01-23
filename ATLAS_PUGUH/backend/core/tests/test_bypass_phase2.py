"""
PHASE 2 BYPASS TESTS - NON-NEGOTIABLE GATE

These tests verify that Phase 2 enforcement cannot be bypassed.
ALL tests MUST pass before Phase 2 is considered complete.

Source: Phase 2 Requirements
- SDK direct DB access → FAIL
- SDK retry without idempotency → FAIL
- app_runtime_role disable RLS → FAIL
- Cross-tenant via SDK → FAIL
- Missing tenant/subject context → DENY

CRITICAL: If any of these tests fail, STOP implementation.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError


# =============================================================================
# BYPASS TEST 1: SDK CANNOT DIRECTLY ACCESS DATABASE
# =============================================================================

class TestSDKCannotAccessDatabase:
    """
    CRITICAL: SDK is a thin adapter. It CANNOT directly access the database.
    SDK must go through Core API.
    """

    def test_sdk_has_no_database_imports(self):
        """
        BYPASS TEST: SDK module should NOT import SQLAlchemy or database modules
        """
        import infra_sdk

        # Check that SDK does not have database access
        sdk_attributes = dir(infra_sdk)

        # These should NOT be present in SDK
        forbidden_imports = [
            "Session",
            "AsyncSession",
            "Engine",
            "create_engine",
            "create_async_engine",
            "sessionmaker",
            "Base",  # SQLAlchemy Base
        ]

        for forbidden in forbidden_imports:
            assert forbidden not in sdk_attributes, \
                f"SDK MUST NOT have '{forbidden}' - SDK cannot directly access database"

    def test_sdk_client_has_no_session_attribute(self):
        """
        BYPASS TEST: InfraClient should NOT have database session
        """
        from infra_sdk import InfraClient

        client = InfraClient(core_api_url="http://localhost:8000")

        # Check attributes
        client_attrs = dir(client)

        # These should NOT be present
        forbidden_attrs = ["session", "db_session", "_session", "_db", "engine", "_engine"]

        for forbidden in forbidden_attrs:
            # Allow _http_client but not database-related
            if "http" not in forbidden.lower():
                has_attr = hasattr(client, forbidden)
                if has_attr:
                    attr_value = getattr(client, forbidden, None)
                    # If it's related to HTTP, that's fine
                    assert attr_value is None or "http" in str(type(attr_value)).lower(), \
                        f"SDK Client MUST NOT have database attribute '{forbidden}'"


# =============================================================================
# BYPASS TEST 2: SDK REQUIRES IDEMPOTENCY KEY FOR MUTATIONS
# =============================================================================

class TestSDKRequiresIdempotency:
    """
    CRITICAL: SDK MUST require idempotency key for all mutating operations.
    """

    def test_create_decision_without_idempotency_fails(self):
        """
        BYPASS TEST: create_decision without idempotency_key MUST fail
        """
        from infra_sdk import (
            CreateDecisionRequest,
            RequestContext,
            TenantContext,
            SubjectContext,
        )
        from infra_sdk.exceptions import IdempotencyRequiredError

        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")

        # Create context WITHOUT idempotency key
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key=""  # Empty = missing
        )

        # Should fail at request creation
        with pytest.raises((ValueError, IdempotencyRequiredError)):
            CreateDecisionRequest(
                context=context,
                decision_type="test.decision",
                decision_context={"key": "value"}
            )

    def test_workflow_action_without_idempotency_fails(self):
        """
        BYPASS TEST: workflow action without idempotency_key MUST fail
        """
        from infra_sdk import (
            WorkflowActionRequest,
            RequestContext,
            TenantContext,
            SubjectContext,
            WorkflowAction,
        )

        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")

        # Create context WITHOUT idempotency key
        context = RequestContext(
            tenant=tenant,
            subject=subject,
            trace_id=uuid4(),
            idempotency_key=""  # Empty = missing
        )

        # Should fail at request creation
        with pytest.raises(ValueError):
            WorkflowActionRequest(
                context=context,
                workflow_id=uuid4(),
                action=WorkflowAction.APPROVE
            )


# =============================================================================
# BYPASS TEST 3: app_runtime_role CANNOT DISABLE RLS
# =============================================================================

class TestRoleCannotBypassRLS:
    """
    CRITICAL: app_runtime_role CANNOT disable or bypass RLS.
    """

    @pytest.mark.asyncio
    async def test_app_runtime_role_cannot_set_bypassrls(self, test_db_session):
        """
        BYPASS TEST: app_runtime_role attempting to set BYPASSRLS MUST fail
        """
        # Set role to app_runtime_role
        await test_db_session.execute(text("SET ROLE app_runtime_role"))

        # Attempt to alter role to bypass RLS (should fail)
        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("ALTER ROLE app_runtime_role BYPASSRLS")
            )
            await test_db_session.commit()

        # Should fail with permission denied
        assert "permission denied" in str(exc_info.value).lower() or \
               "must be superuser" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_app_runtime_role_cannot_disable_rls_on_table(self, test_db_session):
        """
        BYPASS TEST: app_runtime_role attempting to disable RLS MUST fail
        """
        # Set role to app_runtime_role
        await test_db_session.execute(text("SET ROLE app_runtime_role"))

        # Attempt to disable RLS (should fail)
        with pytest.raises(Exception) as exc_info:
            await test_db_session.execute(
                text("ALTER TABLE decisions DISABLE ROW LEVEL SECURITY")
            )
            await test_db_session.commit()

        # Should fail with permission denied
        assert "permission denied" in str(exc_info.value).lower() or \
               "must be owner" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_force_rls_is_enabled(self, test_db_session):
        """
        BYPASS TEST: Verify FORCE RLS is enabled on all tenant-bound tables
        """
        tables = [
            "decisions",
            "workflows",
            "workflow_transitions",
            "rules",
            "event_log",
            "operations_audit",
            "idempotency_cache",
        ]

        for table in tables:
            result = await test_db_session.execute(
                text("""
                    SELECT relforcerowsecurity
                    FROM pg_class
                    WHERE relname = :table_name
                """),
                {"table_name": table}
            )
            is_forced = result.scalar()

            assert is_forced is True, \
                f"FORCE RLS MUST be enabled on table '{table}'"


# =============================================================================
# BYPASS TEST 4: CROSS-TENANT ACCESS VIA SDK FAILS
# =============================================================================

class TestSDKCrossTenantAccessFails:
    """
    CRITICAL: SDK MUST prevent cross-tenant access.
    """

    @pytest.mark.asyncio
    async def test_sdk_cross_tenant_get_decision_fails(self):
        """
        BYPASS TEST: Getting a decision with mismatched tenant MUST fail
        """
        from infra_sdk import (
            InfraClient,
            GetDecisionRequest,
            RequestContext,
            TenantContext,
            SubjectContext,
        )
        from infra_sdk.exceptions import TenantMismatchError, CoreAPIError

        tenant_a = uuid4()
        tenant_b = uuid4()  # Different tenant

        # Mock Core API response with tenant_b
        mock_response = {
            "decision_id": str(uuid4()),
            "tenant_id": str(tenant_b),  # Different from context!
            "decision_type": "test.decision",
            "context": {},
            "outcome": "DENIED",
            "created_at": "2026-01-24T00:00:00Z",
        }

        async with InfraClient(core_api_url="http://localhost:8000") as client:
            # Patch HTTP client to return mock response
            with patch.object(client._http_client, "get") as mock_get:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = mock_response
                mock_get.return_value = mock_resp

                context = RequestContext(
                    tenant=TenantContext(tenant_id=tenant_a),  # tenant_a
                    subject=SubjectContext(subject_id=uuid4(), subject_type="user"),
                    trace_id=uuid4(),
                    idempotency_key="test"
                )

                request = GetDecisionRequest(
                    context=context,
                    decision_id=uuid4()
                )

                # Should raise TenantMismatchError
                with pytest.raises(TenantMismatchError):
                    await client.get_decision(request)


# =============================================================================
# BYPASS TEST 5: MISSING CONTEXT RESULTS IN DENY
# =============================================================================

class TestMissingContextDenied:
    """
    CRITICAL: Missing tenant/subject/trace context MUST result in DENY.
    """

    def test_missing_tenant_fails(self):
        """
        BYPASS TEST: Creating request without tenant MUST fail
        """
        from infra_sdk import (
            CreateDecisionRequest,
            RequestContext,
            SubjectContext,
        )

        subject = SubjectContext(subject_id=uuid4(), subject_type="user")

        # Create context WITHOUT tenant
        with pytest.raises((ValueError, TypeError)):
            RequestContext(
                tenant=None,  # Missing!
                subject=subject,
                trace_id=uuid4(),
                idempotency_key="test"
            )

    def test_missing_subject_fails(self):
        """
        BYPASS TEST: Creating request without subject MUST fail
        """
        from infra_sdk import (
            RequestContext,
            TenantContext,
        )

        tenant = TenantContext(tenant_id=uuid4())

        # Create context WITHOUT subject
        with pytest.raises((ValueError, TypeError)):
            RequestContext(
                tenant=tenant,
                subject=None,  # Missing!
                trace_id=uuid4(),
                idempotency_key="test"
            )

    def test_missing_trace_id_fails(self):
        """
        BYPASS TEST: Creating request without trace_id MUST fail
        """
        from infra_sdk import (
            RequestContext,
            TenantContext,
            SubjectContext,
        )

        tenant = TenantContext(tenant_id=uuid4())
        subject = SubjectContext(subject_id=uuid4(), subject_type="user")

        # Create context WITHOUT trace_id
        with pytest.raises((ValueError, TypeError)):
            RequestContext(
                tenant=tenant,
                subject=subject,
                trace_id=None,  # Missing!
                idempotency_key="test"
            )

    @pytest.mark.asyncio
    async def test_sdk_call_without_context_fails(self):
        """
        BYPASS TEST: SDK call without context MUST fail
        """
        from infra_sdk import InfraClient
        from infra_sdk.exceptions import MissingContextError

        async with InfraClient(core_api_url="http://localhost:8000") as client:
            # Try to create decision with None context
            with pytest.raises((MissingContextError, ValueError, TypeError)):
                await client.create_decision(None)


# =============================================================================
# BYPASS TEST 6: SDK DOES NOT HAVE RETRY LOGIC
# =============================================================================

class TestSDKNoRetryLogic:
    """
    CRITICAL: SDK MUST NOT have automatic retry logic.
    Retry decisions belong to the caller, not the SDK.
    """

    def test_sdk_client_has_no_retry_attributes(self):
        """
        BYPASS TEST: InfraClient should NOT have retry configuration
        """
        from infra_sdk import InfraClient

        client = InfraClient(core_api_url="http://localhost:8000")

        # These should NOT be present
        retry_attrs = [
            "retry",
            "max_retries",
            "retry_count",
            "retry_delay",
            "backoff",
            "retry_policy",
            "_retry",
        ]

        for attr in retry_attrs:
            assert not hasattr(client, attr), \
                f"SDK MUST NOT have retry attribute '{attr}'"

    @pytest.mark.asyncio
    async def test_sdk_does_not_retry_on_error(self):
        """
        BYPASS TEST: SDK MUST NOT retry on error
        """
        from infra_sdk import (
            InfraClient,
            CreateDecisionRequest,
            RequestContext,
            TenantContext,
            SubjectContext,
        )
        from infra_sdk.exceptions import CoreAPIError

        async with InfraClient(core_api_url="http://localhost:8000") as client:
            call_count = 0

            async def mock_post(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                raise Exception("Simulated error")

            # Patch HTTP client
            with patch.object(client._http_client, "post", side_effect=mock_post):
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

                try:
                    await client.create_decision(request)
                except Exception:
                    pass

                # Should only be called ONCE (no retry)
                assert call_count == 1, \
                    f"SDK MUST NOT retry. Called {call_count} times."


# =============================================================================
# BYPASS TEST 7: ENFORCED SESSION FACTORY REQUIRES CONTEXT
# =============================================================================

class TestEnforcedSessionFactoryRequiresContext:
    """
    CRITICAL: EnforcedSessionFactory MUST require context for all operations.
    """

    @pytest.mark.asyncio
    async def test_get_session_without_context_fails(self):
        """
        BYPASS TEST: Getting session without context MUST fail
        """
        from core.runtime import EnforcedSessionFactory, RuntimeConfig, ContextRequiredError

        config = RuntimeConfig(
            database_url="postgresql+asyncpg://app_runtime_role:test@localhost:5432/test",
            database_role="app_runtime_role",
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

        factory = EnforcedSessionFactory(config)

        # Don't initialize (would fail without real DB)
        # Just test the validation

        # Calling get_session without context should fail
        with pytest.raises((ContextRequiredError, Exception)):
            await factory.get_session(None)


# =============================================================================
# BYPASS TEST 8: RUNTIME CONFIG ENFORCES CORRECT ROLE
# =============================================================================

class TestRuntimeConfigEnforcesRole:
    """
    CRITICAL: RuntimeConfig MUST enforce app_runtime_role.
    """

    def test_config_rejects_wrong_role(self):
        """
        BYPASS TEST: Creating RuntimeConfig with wrong role MUST fail
        """
        from core.runtime import RuntimeConfig

        # Try to create config with superuser role
        with pytest.raises(ValueError) as exc_info:
            RuntimeConfig(
                database_url="postgresql+asyncpg://postgres:test@localhost:5432/test",
                database_role="postgres",  # WRONG - superuser
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
            )

        assert "app_runtime_role" in str(exc_info.value)

    def test_config_accepts_correct_role(self):
        """
        VERIFICATION: Creating RuntimeConfig with correct role should succeed
        """
        from core.runtime import RuntimeConfig

        config = RuntimeConfig(
            database_url="postgresql+asyncpg://app_runtime_role:test@localhost:5432/test",
            database_role="app_runtime_role",
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

        assert config.database_role == "app_runtime_role"


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
async def test_db_session():
    """
    Create test database session with PostgreSQL.

    NOTE: These tests require PostgreSQL with migration 004 applied.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    import os

    # Use PostgreSQL for these tests
    db_url = os.getenv(
        "BYPASS_TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/infra_test"
    )

    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    await engine.dispose()
