---
description: Create event/message for PROJECT_BESAR
---

# Flow A5: Create Event/Message

## Pre-requisites
- [ ] Event type defined
- [ ] Payload structure defined
- [ ] Consumers identified

## Step 1: Define Event Schema
Location: `modules/{module}/backend/app/events/schemas.py`

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Literal

class {Entity}CreatedEvent(BaseModel):
    event_type: Literal["{module}.{entity}.created"] = "{module}.{entity}.created"
    event_id: UUID
    timestamp: datetime
    tenant_id: UUID
    actor_id: UUID | None

    # Payload
    entity_id: UUID
    data: dict
```

## Step 2: Create Publisher
Location: `modules/{module}/backend/app/events/publishers/{entity}_publisher.py`

```python
from app.core.event_bus import EventBus
from app.events.schemas import {Entity}CreatedEvent

class {Entity}Publisher:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def publish_created(self, entity_id: UUID, data: dict, tenant_id: UUID):
        event = {Entity}CreatedEvent(
            event_id=uuid4(),
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            entity_id=entity_id,
            data=data
        )
        await self.event_bus.publish(event)
```

## Step 3: Create Consumer
Location: `modules/{module}/backend/app/events/consumers/{entity}_consumer.py`

```python
from app.core.event_bus import EventConsumer, event_handler

class {Entity}EventConsumer(EventConsumer):

    @event_handler("{module}.{entity}.created")
    async def handle_created(self, event: dict):
        # Idempotency check
        if await self.already_processed(event["event_id"]):
            return

        # Process event
        await self.process_event(event)

        # Mark as processed
        await self.mark_processed(event["event_id"])
```

## Step 4: Register Consumer
```python
# In module startup
consumer = {Entity}EventConsumer()
await event_bus.subscribe("{module}.{entity}.*", consumer)
```

## Checklist Before Complete
- [ ] Event schema versioned
- [ ] Publisher uses correlation_id
- [ ] Consumer is idempotent
- [ ] Dead letter queue configured
- [ ] Error handling proper
