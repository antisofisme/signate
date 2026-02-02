"""
Infra SDK Client - THIN ADAPTER

This client is an ADAPTER to Core API.
It does NOT contain business logic.
It does NOT evaluate rules.
It does NOT store state.
It does NOT retry automatically.

PRINCIPLE: SDK is a pass-through with validation.

Source: Phase 2 Requirements
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
import httpx

from .types import (
    RequestContext,
    CreateDecisionRequest,
    CreateDecisionResponse,
    GetDecisionRequest,
    GetDecisionResponse,
    WorkflowActionRequest,
    WorkflowActionResponse,
    WorkflowAction,
)
from .exceptions import (
    InfraSDKError,
    MissingContextError,
    ValidationError,
    CoreAPIError,
    IdempotencyRequiredError,
    TenantMismatchError,
    ConnectionError,
)


class InfraClient:
    """
    Infra SDK Client - THIN ADAPTER

    SDK API:
    - create_decision()
    - get_decision()
    - submit_workflow_action()

    SDK does NOT provide:
    - Helper shortcuts
    - Implicit defaults
    - Fallback behavior
    - Retry logic
    - State management
    """

    def __init__(
        self,
        core_api_url: str,
        timeout_seconds: float = 30.0
    ):
        """
        Initialize SDK client.

        Args:
            core_api_url: Base URL of Core API (REQUIRED)
            timeout_seconds: Request timeout (default: 30s)

        NO implicit defaults for core_api_url.
        """
        if not core_api_url:
            raise ValidationError("core_api_url is REQUIRED")

        self._core_api_url = core_api_url.rstrip("/")
        self._timeout = timeout_seconds
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Enter async context - create HTTP client."""
        self._http_client = httpx.AsyncClient(
            base_url=self._core_api_url,
            timeout=self._timeout,
            # NO automatic retries
            # NO follow redirects (security)
            follow_redirects=False,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def create_decision(
        self,
        request: CreateDecisionRequest
    ) -> CreateDecisionResponse:
        """
        Create a decision.

        SDK responsibilities:
        1. Validate request structure
        2. Attach context headers
        3. Call Core API
        4. Return response (or raise exception)

        SDK does NOT:
        - Evaluate rules
        - Provide defaults
        - Retry on failure
        """
        # Validate request (SDK structural validation only)
        self._validate_context(request.context)
        self._require_idempotency_key(request.context, "create_decision")

        # Build Core API request
        payload = {
            "tenant_id": str(request.context.tenant.tenant_id),
            "decision_type": request.decision_type,
            "context": request.decision_context,
            "idempotency_key": request.context.idempotency_key,
            "trace_id": str(request.context.trace_id),
            "requester_user_id": str(request.context.subject.subject_id),
        }

        # Call Core API
        response = await self._call_core_api(
            method="POST",
            path="/api/v1/decisions",
            payload=payload,
            context=request.context
        )

        # Parse response (NO transformation, NO enrichment)
        return CreateDecisionResponse(
            decision_id=UUID(response["decision_id"]),
            outcome=response["outcome"],
            rule_matched_id=UUID(response["rule_matched_id"]) if response.get("rule_matched_id") else None,
            rule_version=response.get("rule_version"),
            workflow_id=UUID(response["workflow_id"]) if response.get("workflow_id") else None,
            created_at=datetime.fromisoformat(response["created_at"]),
            trace_id=request.context.trace_id,
        )

    async def get_decision(
        self,
        request: GetDecisionRequest
    ) -> GetDecisionResponse:
        """
        Get an existing decision.

        Read operation - idempotency key NOT required.
        """
        # Validate context (still required for tenant isolation)
        self._validate_context(request.context)
        # Note: idempotency_key NOT required for read operations

        # Call Core API
        response = await self._call_core_api(
            method="GET",
            path=f"/api/v1/decisions/{request.decision_id}",
            payload=None,
            context=request.context
        )

        # Verify tenant match (cross-tenant access check)
        response_tenant = UUID(response["tenant_id"])
        if response_tenant != request.context.tenant.tenant_id:
            raise TenantMismatchError(
                context_tenant=str(request.context.tenant.tenant_id),
                target_tenant=str(response_tenant)
            )

        # Parse response
        return GetDecisionResponse(
            decision_id=UUID(response["decision_id"]),
            tenant_id=response_tenant,
            decision_type=response["decision_type"],
            decision_context=response["context"],
            outcome=response["outcome"],
            rule_matched_id=UUID(response["rule_matched_id"]) if response.get("rule_matched_id") else None,
            rule_version=response.get("rule_version"),
            workflow_id=UUID(response["workflow_id"]) if response.get("workflow_id") else None,
            created_at=datetime.fromisoformat(response["created_at"]),
        )

    async def submit_workflow_action(
        self,
        request: WorkflowActionRequest
    ) -> WorkflowActionResponse:
        """
        Submit a workflow action (approve, reject, delegate, escalate).

        Idempotency key is REQUIRED.
        """
        # Validate request
        self._validate_context(request.context)
        self._require_idempotency_key(request.context, "submit_workflow_action")

        # Map action to endpoint
        action_endpoints = {
            WorkflowAction.APPROVE: "approve",
            WorkflowAction.REJECT: "reject",
            WorkflowAction.DELEGATE: "delegate",
            WorkflowAction.ESCALATE: "escalate",
        }

        endpoint = action_endpoints[request.action]

        # Build payload based on action
        payload = {
            "tenant_id": str(request.context.tenant.tenant_id),
            "idempotency_key": request.context.idempotency_key,
            "trace_id": str(request.context.trace_id),
            "acted_by_user_id": str(request.context.subject.subject_id),
        }

        if request.comment:
            payload["comment"] = request.comment

        if request.action == WorkflowAction.DELEGATE:
            payload["delegate_to_user_id"] = str(request.delegate_to_user_id)

        if request.action == WorkflowAction.ESCALATE:
            payload["escalate_to_role"] = request.escalate_to_role

        # Call Core API
        response = await self._call_core_api(
            method="POST",
            path=f"/api/v1/workflows/{request.workflow_id}/{endpoint}",
            payload=payload,
            context=request.context
        )

        # Parse response
        return WorkflowActionResponse(
            workflow_id=UUID(response["workflow_id"]),
            decision_id=UUID(response["decision_id"]),
            current_state=response["current_state"],
            completed_at=datetime.fromisoformat(response["completed_at"]) if response.get("completed_at") else None,
            trace_id=request.context.trace_id,
        )

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _validate_context(self, context: RequestContext) -> None:
        """
        Validate request context.

        All context fields are REQUIRED. NO defaults.
        """
        if context is None:
            raise MissingContextError("context")

        if context.tenant is None:
            raise MissingContextError("tenant")

        if context.tenant.tenant_id is None:
            raise MissingContextError("tenant.tenant_id")

        if context.subject is None:
            raise MissingContextError("subject")

        if context.subject.subject_id is None:
            raise MissingContextError("subject.subject_id")

        if context.trace_id is None:
            raise MissingContextError("trace_id")

    def _require_idempotency_key(self, context: RequestContext, operation: str) -> None:
        """
        Require idempotency key for mutating operations.

        NO exceptions. NO fallback.
        """
        if not context.idempotency_key:
            raise IdempotencyRequiredError(operation)

    async def _call_core_api(
        self,
        method: str,
        path: str,
        payload: Optional[dict],
        context: RequestContext
    ) -> dict:
        """
        Call Core API.

        SDK does NOT:
        - Retry on failure
        - Interpret errors
        - Modify responses

        SDK ONLY:
        - Sends request with headers
        - Returns response or raises exception
        """
        if not self._http_client:
            raise InfraSDKError(
                message="HTTP client not initialized. Use 'async with' context manager.",
                error_code="SDK_NOT_INITIALIZED"
            )

        # Build headers (context propagation)
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-ID": str(context.tenant.tenant_id),
            "X-Subject-ID": str(context.subject.subject_id),
            "X-Subject-Type": context.subject.subject_type,
            "X-Trace-ID": str(context.trace_id),
        }

        if context.idempotency_key:
            headers["X-Idempotency-Key"] = context.idempotency_key

        try:
            if method == "GET":
                response = await self._http_client.get(path, headers=headers)
            elif method == "POST":
                response = await self._http_client.post(path, json=payload, headers=headers)
            else:
                raise ValidationError(f"Unsupported HTTP method: {method}")

        except httpx.ConnectError as e:
            raise ConnectionError(str(e))
        except httpx.TimeoutException as e:
            raise ConnectionError(f"Request timeout: {e}")

        # Handle response
        if response.status_code >= 400:
            # Parse error response
            try:
                error_body = response.json()
                raise CoreAPIError(
                    message=error_body.get("message", "Unknown error"),
                    status_code=response.status_code,
                    core_error_code=error_body.get("error_code"),
                    core_details=error_body.get("details"),
                )
            except ValueError:
                raise CoreAPIError(
                    message=response.text,
                    status_code=response.status_code,
                )

        # Parse successful response
        return response.json()
