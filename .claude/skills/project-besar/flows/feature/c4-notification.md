---
description: Create notification feature for PROJECT_BESAR
---

# Flow C4: Create Notification Feature

## Pre-requisites
- [ ] Notification type defined
- [ ] Channels identified (email/push/in-app)
- [ ] Template defined

## Step 1: Create Notification Service
Location: `modules/{module}/backend/app/services/notifications/{notification}_notification.py`

```python
from app.core.notifications import NotificationService, NotificationChannel

class {Notification}Notification:
    def __init__(self, service: NotificationService):
        self.service = service

    async def send(self, user_id: UUID, data: dict):
        # Get user preferences
        prefs = await self.service.get_preferences(user_id)

        # Send via enabled channels
        if prefs.email_enabled:
            await self.send_email(user_id, data)
        if prefs.push_enabled:
            await self.send_push(user_id, data)
        if prefs.inapp_enabled:
            await self.send_inapp(user_id, data)
```

## Step 2: Create Email Template
Location: `modules/{module}/backend/templates/email/{notification}.mjml`

```html
<mjml>
  <mj-body>
    <mj-section>
      <mj-column>
        <mj-text>Hello {{ user.name }},</mj-text>
        <mj-text>{{ message }}</mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

## Step 3: Trigger via Event
```python
@event_handler("{module}.{entity}.created")
async def handle_created(self, event):
    notification = {Notification}Notification(self.notification_service)
    await notification.send(
        user_id=event['actor_id'],
        data={'entity_id': event['entity_id']}
    )
```

## Step 4: Create In-App Notification UI
```typescript
const { notifications, markAsRead } = useNotifications();

<NotificationBell count={notifications.unreadCount} />

<NotificationList
  items={notifications.items}
  onRead={markAsRead}
/>
```

## Checklist Before Complete
- [ ] Multi-channel support
- [ ] User preferences respected
- [ ] Email template works
- [ ] In-app notifications real-time
- [ ] Mark as read works
