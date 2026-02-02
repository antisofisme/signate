# PUGUH SDK for Python

Python SDK for PUGUH Platform - Infrastructure for SaaS applications including authentication, multi-tenancy, billing, and decision engine.

## Installation

```bash
pip install puguh-sdk
```

## Quick Start

### Platform Features (Auth, Tenants, Billing)

```python
from puguh_sdk import PuguhClient
import asyncio

async def main():
    # User token authentication
    client = PuguhClient(
        base_url="https://api.puguh.io",
        access_token="your_jwt_token"
    )

    async with client:
        # Get current user
        user = await client.auth.get_me()
        print(f"Logged in as: {user.display_name}")

        # List organizations
        tenants = await client.tenants.list()
        for tenant in tenants:
            print(f"- {tenant.name} ({tenant.plan.value})")

        # Get billing plans
        plans = await client.billing.get_plans(product="mantra")
        for plan in plans:
            print(f"- {plan.name}: ${plan.price}/mo")

asyncio.run(main())
```

### Service Account (Backend Integration)

```python
from puguh_sdk import PuguhClient

# API key for service-to-service communication
client = PuguhClient(
    base_url="https://api.puguh.io",
    api_key="pk_live_xxxxxxxxxxxx"
)

# Set tenant context for operations
client.set_tenant_context(tenant_id="tenant_uuid")

async with client:
    # Validate user tokens from your frontend
    user_context = await client.auth.validate_token("user_jwt_from_request")
    print(f"User: {user_context.user_id}, Tenant: {user_context.tenant_id}")
```

### Token Validation Middleware (FastAPI)

```python
from puguh_sdk import PuguhClient, AuthError
from fastapi import Request, HTTPException, Depends

puguh = PuguhClient(
    base_url="https://api.puguh.io",
    api_key="pk_live_xxxxxxxxxxxx"
)

async def validate_token(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization")

    token = auth.replace("Bearer ", "")
    try:
        user_context = await puguh.auth.validate_token(token)
        request.state.user = user_context
        return user_context
    except AuthError:
        raise HTTPException(401, "Invalid token")

@app.get("/api/protected")
async def protected_route(user=Depends(validate_token)):
    return {"user_id": user.user_id, "tenant_id": user.tenant_id}
```

---

## Core Service (Decision Engine)

For decision engine and workflow orchestration:

```python
from uuid import uuid4
from puguh_sdk.core import CoreServiceClient, CreateDecisionRequest
import asyncio

async def main():
    async with CoreServiceClient(base_url="http://localhost:8001") as client:
        request = CreateDecisionRequest(
            tenant_id=uuid4(),
            decision_type="check_in_approval",
            context={"room_id": "101", "guest_count": 2},
            idempotency_key="req-12345"
        )

        response = await client.create_decision(request)
        print(f"Decision: {response.outcome}")

asyncio.run(main())
```

## API Reference

### Client

#### `CoreServiceClient(base_url, timeout=30.0, api_key=None)`

Main client for Core Service API.

**Parameters:**
- `base_url` (str): Base URL of Core Service API
- `timeout` (float): Request timeout in seconds (default: 30.0)
- `api_key` (str, optional): API key for authentication (future use)

**Methods:**
- `create_decision(request: CreateDecisionRequest) -> CreateDecisionResponse`
- `approve_workflow(workflow_id: UUID, request: ApproveWorkflowRequest) -> ApproveWorkflowResponse`
- `reject_workflow(workflow_id: UUID, request: RejectWorkflowRequest) -> RejectWorkflowResponse`
- `delegate_workflow(workflow_id: UUID, request: DelegateWorkflowRequest) -> DelegateWorkflowResponse`
- `escalate_workflow(workflow_id: UUID, request: EscalateWorkflowRequest) -> EscalateWorkflowResponse`

### Request Types

#### `CreateDecisionRequest`

```python
CreateDecisionRequest(
    tenant_id: UUID,
    decision_type: str,
    context: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    trace_id: Optional[UUID] = None,
    requester_user_id: Optional[UUID] = None
)
```

#### `ApproveWorkflowRequest`

```python
ApproveWorkflowRequest(
    tenant_id: UUID,
    approver_role: str,
    acted_by_user_id: Optional[UUID] = None,
    comment: Optional[str] = None
)
```

### Response Types

#### `CreateDecisionResponse`

```python
@dataclass
class CreateDecisionResponse:
    decision_id: UUID
    outcome: str  # "ALLOWED" | "DENIED" | "REQUIRE_APPROVAL"
    rule_matched_id: Optional[UUID]
    rule_version: Optional[str]
    workflow_id: Optional[UUID]
    created_at: datetime
```

### Exceptions

All exceptions inherit from `CoreServiceError`.

- `IdempotencyConflictError` (HTTP 409): Idempotency key conflicts with different context
- `WorkflowNotFoundError` (HTTP 404): Workflow not found
- `ApproverRoleMismatchError` (HTTP 403): Approver role mismatch
- `InvalidWorkflowTransitionError` (HTTP 400): Invalid workflow state transition
- `TenantIsolationViolationError` (HTTP 403): Tenant isolation violated
- `ValidationError` (HTTP 422): Request validation failed
- `NetworkError`: Network request failed

## Error Handling

```python
from arsaka_puguh_sdk import (
    CoreServiceClient,
    CreateDecisionRequest,
    IdempotencyConflictError,
    NetworkError
)

async def safe_create_decision():
    async with CoreServiceClient(base_url="http://localhost:8001") as client:
        try:
            request = CreateDecisionRequest(
                tenant_id=uuid4(),
                decision_type="test",
                context={"key": "value"},
                idempotency_key="unique-key"
            )

            response = await client.create_decision(request)
            return response

        except IdempotencyConflictError as e:
            print(f"Conflict: {e.message}")
            print(f"Existing decision: {e.existing_decision_id}")

        except NetworkError as e:
            print(f"Network error: {e.message}")

        except CoreServiceError as e:
            print(f"API error: {e.error_code} - {e.message}")
```

## Idempotency

Use `idempotency_key` to ensure exactly-once processing:

```python
request = CreateDecisionRequest(
    tenant_id=tenant_id,
    decision_type="payment_approval",
    context={"amount": 1000, "currency": "USD"},
    idempotency_key=f"payment-{payment_id}"  # Unique per payment
)

# Same key + same context = same decision (cached)
response1 = await client.create_decision(request)
response2 = await client.create_decision(request)
assert response1.decision_id == response2.decision_id

# Same key + different context = conflict error
request.context["amount"] = 2000
await client.create_decision(request)  # Raises IdempotencyConflictError
```

## Requirements

- Python 3.11+
- httpx >= 0.27.0

## License

MIT License - See LICENSE file for details.
