---
description: Create background job with Celery for PROJECT_BESAR
---

# Flow A4: Create Background Job

## Pre-requisites
- [ ] Job purpose defined
- [ ] Trigger mechanism identified (event/schedule/manual)

## Step 1: Create Celery Task
Location: `modules/{module}/backend/app/jobs/{action}_{entity}.py`

```python
from celery import shared_task
from app.core.celery import celery_app

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    acks_late=True
)
def process_{entity}(self, entity_id: str, tenant_id: str):
    """
    Process {entity} in background.

    Args:
        entity_id: UUID of entity
        tenant_id: UUID of tenant
    """
    try:
        # Idempotency check
        if already_processed(entity_id):
            return {"status": "skipped", "reason": "already_processed"}

        # Process logic
        result = do_processing(entity_id, tenant_id)

        return {"status": "success", "result": result}
    except Exception as exc:
        self.retry(exc=exc)
```

## Step 2: Register Task
Location: `modules/{module}/backend/app/jobs/__init__.py`

```python
from app.jobs.{action}_{entity} import process_{entity}

__all__ = ["process_{entity}"]
```

## Step 3: Call Task
```python
# Async call
process_{entity}.delay(str(entity_id), str(tenant_id))

# With countdown
process_{entity}.apply_async(
    args=[str(entity_id), str(tenant_id)],
    countdown=10
)
```

## Step 4: Scheduled Task (Optional)
Location: `modules/{module}/backend/app/core/celery.py`

```python
celery_app.conf.beat_schedule = {
    "process-{entities}-daily": {
        "task": "app.jobs.{action}_{entity}.process_{entity}",
        "schedule": crontab(hour=2, minute=0),
    },
}
```

## Checklist Before Complete
- [ ] Task is idempotent
- [ ] Retry strategy configured
- [ ] Error handling proper
- [ ] Logging added
- [ ] Monitoring configured
