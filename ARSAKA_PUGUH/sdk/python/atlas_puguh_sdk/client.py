"""
Core Service SDK Client

Python client for ARSAKA_PUGUH Core Service HTTP API.
Source: INFRA-LAY3-002 (Core Service Implementation Standards)
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
import httpx

from .types import (
    CreateDecisionRequest,
    CreateDecisionResponse,
    ApproveWorkflowRequest,
    ApproveWorkflowResponse,
    RejectWorkflowRequest,
    RejectWorkflowResponse,
    DelegateWorkflowRequest,
    DelegateWorkflowResponse,
    EscalateWorkflowRequest,
    EscalateWorkflowResponse,
)
from .exceptions import (
    CoreServiceError,
    IdempotencyConflictError,
    WorkflowNotFoundError,
    ApproverRoleMismatchError,
    InvalidWorkflowTransitionError,
    TenantIsolationViolationError,
    NetworkError,
    ValidationError,
)


class CoreServiceClient:
    """
    HTTP client for Core Service API

    Provides methods for decision creation and workflow management.
    Thread-safe for concurrent use with async/await.

    Example:
        ```python
        from uuid import uuid4
        from arsaka_puguh_sdk import CoreServiceClient, CreateDecisionRequest

        client = CoreServiceClient(base_url="http://localhost:8001")

        request = CreateDecisionRequest(
            tenant_id=uuid4(),
            decision_type="check_in_approval",
            context={"room_id": "101", "guest_count": 2}
        )

        response = await client.create_decision(request)
        print(f"Decision: {response.outcome}")
        ```

    Source: INFRA-LAY3-002 §5 (SDK Contract)
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        api_key: Optional[str] = None
    ):
        """
        Initialize Core Service client

        Args:
            base_url: Base URL of Core Service API (e.g., "http://localhost:8001")
            timeout: Request timeout in seconds (default: 30.0)
            api_key: Optional API key for authentication (future use)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

        # HTTP client configuration
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers
        )

    async def close(self):
        """Close HTTP client and cleanup resources"""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    def _handle_error_response(self, response: httpx.Response):
        """
        Map HTTP error responses to SDK exceptions

        Args:
            response: HTTP response from API

        Raises:
            CoreServiceError: Appropriate exception based on error code
        """
        try:
            error_data = response.json()
            error_code = error_data.get("error_code", "UNKNOWN_ERROR")
            message = error_data.get("message", "An error occurred")
            details = error_data.get("details", {})
        except Exception:
            # Fallback if response is not valid JSON
            error_code = "UNKNOWN_ERROR"
            message = response.text or f"HTTP {response.status_code}"
            details = {}

        # Map error codes to exception classes
        if error_code == "IDEMPOTENCY_CONFLICT":
            existing_decision_id = details.get("existing_decision_id", "unknown")
            raise IdempotencyConflictError(message, existing_decision_id, details)
        elif error_code == "WORKFLOW_NOT_FOUND":
            workflow_id = details.get("workflow_id", "unknown")
            raise WorkflowNotFoundError(message, workflow_id, details)
        elif error_code == "APPROVER_ROLE_MISMATCH":
            expected = details.get("expected", "unknown")
            actual = details.get("actual", "unknown")
            raise ApproverRoleMismatchError(message, expected, actual, details)
        elif error_code == "INVALID_WORKFLOW_TRANSITION":
            from_state = details.get("from_state", "unknown")
            to_state = details.get("to_state", "unknown")
            raise InvalidWorkflowTransitionError(message, from_state, to_state, details)
        elif error_code == "TENANT_ISOLATION_VIOLATION":
            raise TenantIsolationViolationError(message, details)
        elif response.status_code == 422:
            raise ValidationError(message, details)
        else:
            raise CoreServiceError(message, error_code, details, response.status_code)

    async def create_decision(
        self,
        request: CreateDecisionRequest
    ) -> CreateDecisionResponse:
        """
        Create a new decision

        Args:
            request: Decision creation request

        Returns:
            Decision creation response

        Raises:
            IdempotencyConflictError: If idempotency key conflicts
            ValidationError: If request validation fails
            NetworkError: If network request fails
            CoreServiceError: For other API errors

        Source: INFRA-LAY3-002 §2.3 (Decision Creation)
        """
        try:
            response = await self._client.post(
                "/api/v1/decisions",
                json=request.to_dict()
            )

            if response.status_code != 201:
                self._handle_error_response(response)

            data = response.json()
            return CreateDecisionResponse(
                decision_id=UUID(data["decision_id"]),
                outcome=data["outcome"],
                rule_matched_id=UUID(data["rule_matched_id"]) if data.get("rule_matched_id") else None,
                rule_version=data.get("rule_version"),
                workflow_id=UUID(data["workflow_id"]) if data.get("workflow_id") else None,
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def approve_workflow(
        self,
        workflow_id: UUID,
        request: ApproveWorkflowRequest
    ) -> ApproveWorkflowResponse:
        """
        Approve a workflow

        Args:
            workflow_id: Workflow UUID
            request: Approval request

        Returns:
            Approval response

        Raises:
            WorkflowNotFoundError: If workflow not found
            ApproverRoleMismatchError: If approver role mismatches
            InvalidWorkflowTransitionError: If transition invalid
            NetworkError: If network request fails
            CoreServiceError: For other API errors

        Source: INFRA-LAY3-002 §3.2 (Workflow Approval)
        """
        try:
            response = await self._client.post(
                f"/api/v1/workflows/{workflow_id}/approve",
                json=request.to_dict()
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            return ApproveWorkflowResponse(
                workflow_id=UUID(data["workflow_id"]),
                current_state=data["current_state"],
                completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def reject_workflow(
        self,
        workflow_id: UUID,
        request: RejectWorkflowRequest
    ) -> RejectWorkflowResponse:
        """
        Reject a workflow

        Args:
            workflow_id: Workflow UUID
            request: Rejection request

        Returns:
            Rejection response

        Raises:
            WorkflowNotFoundError: If workflow not found
            ApproverRoleMismatchError: If approver role mismatches
            InvalidWorkflowTransitionError: If transition invalid
            NetworkError: If network request fails
            CoreServiceError: For other API errors

        Source: INFRA-LAY3-002 §3.2 (Workflow Rejection)
        """
        try:
            response = await self._client.post(
                f"/api/v1/workflows/{workflow_id}/reject",
                json=request.to_dict()
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            return RejectWorkflowResponse(
                workflow_id=UUID(data["workflow_id"]),
                current_state=data["current_state"],
                completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def delegate_workflow(
        self,
        workflow_id: UUID,
        request: DelegateWorkflowRequest
    ) -> DelegateWorkflowResponse:
        """
        Delegate a workflow

        Args:
            workflow_id: Workflow UUID
            request: Delegation request

        Returns:
            Delegation response

        Raises:
            WorkflowNotFoundError: If workflow not found
            ApproverRoleMismatchError: If approver role mismatches
            InvalidWorkflowTransitionError: If transition invalid
            NetworkError: If network request fails
            CoreServiceError: For other API errors

        Source: INFRA-LAY3-002 §3.3 (Workflow Delegation)
        """
        try:
            response = await self._client.post(
                f"/api/v1/workflows/{workflow_id}/delegate",
                json=request.to_dict()
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            return DelegateWorkflowResponse(
                workflow_id=UUID(data["workflow_id"]),
                current_state=data["current_state"],
                delegated_to_user_id=UUID(data["delegated_to_user_id"])
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def escalate_workflow(
        self,
        workflow_id: UUID,
        request: EscalateWorkflowRequest
    ) -> EscalateWorkflowResponse:
        """
        Escalate a workflow

        Args:
            workflow_id: Workflow UUID
            request: Escalation request

        Returns:
            Escalation response

        Raises:
            WorkflowNotFoundError: If workflow not found
            InvalidWorkflowTransitionError: If transition invalid
            NetworkError: If network request fails
            CoreServiceError: For other API errors

        Source: INFRA-LAY3-002 §3.3 (Workflow Escalation)
        """
        try:
            response = await self._client.post(
                f"/api/v1/workflows/{workflow_id}/escalate",
                json=request.to_dict()
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()
            return EscalateWorkflowResponse(
                workflow_id=UUID(data["workflow_id"]),
                current_state=data["current_state"],
                escalated_to_role=data["escalated_to_role"]
            )
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")
