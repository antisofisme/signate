---
description: Create external integration for PROJECT_BESAR
---

# Flow A6: Create External Integration

## Pre-requisites
- [ ] External service identified
- [ ] API documentation available
- [ ] Credentials secured

## Step 1: Create Client
Location: `modules/{module}/backend/app/integrations/{service}_client.py`

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.circuit_breaker import circuit_breaker

class {Service}Client:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def call_api(self, endpoint: str, data: dict) -> dict:
        response = await self.client.post(
            f"{self.base_url}/{endpoint}",
            json=data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()
```

## Step 2: Add Circuit Breaker
```python
from pybreaker import CircuitBreaker

circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    exclude=[httpx.HTTPStatusError]
)
```

## Step 3: Secrets Management
```python
# Use environment variables
from app.core.config import settings

client = {Service}Client(
    base_url=settings.{SERVICE}_BASE_URL,
    api_key=settings.{SERVICE}_API_KEY  # From env, NOT hardcoded
)
```

## Step 4: Handle Webhooks (if applicable)
Location: `modules/{module}/backend/app/api/v1/webhooks/{service}.py`

```python
@router.post("/webhooks/{service}")
async def handle_{service}_webhook(
    payload: dict,
    signature: str = Header(..., alias="X-Signature")
):
    # Verify signature
    if not verify_signature(payload, signature):
        raise HTTPException(401, "Invalid signature")

    # Process webhook
    await process_webhook(payload)
    return {"status": "ok"}
```

## Checklist Before Complete
- [ ] Circuit breaker configured
- [ ] Retry strategy implemented
- [ ] Secrets in environment variables
- [ ] Timeout configured
- [ ] Error handling proper
- [ ] Logging added
