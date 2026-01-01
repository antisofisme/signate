# Development Standards V5

> Standards #23+ untuk Notification, API Versioning, Feature Flags, dan Performance

**Contents:**
- **#23** - Notification Standard
- **#24** - API Versioning Standard
- **#25** - Feature Flags Standard
- **#26** - Performance SLA Standard

---

## 23. Notification Standard

> Standard untuk sistem notifikasi multi-channel (in-app, push, email)

### 23.1 Overview

**Delivery Channels:**
- **In-App**: Real-time via WebSocket (Centrifugo)
- **Push**: Firebase Cloud Messaging (FCM)
- **Email**: SMTP via Celery background job
- **SMS**: Future (Twilio/local provider)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  NOTIFICATION ARCHITECTURE                                                 ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │                         DOMAIN EVENT                                  │ ║
║  │  (e.g., pms.reservation.created, pos.order.received)                 │ ║
║  └────────────────────────────┬─────────────────────────────────────────┘ ║
║                               │                                            ║
║                               ▼                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │                    NOTIFICATION SERVICE                               │ ║
║  │  ┌────────────────────────────────────────────────────────────────┐  │ ║
║  │  │  1. Check user preferences                                      │  │ ║
║  │  │  2. Load notification template                                  │  │ ║
║  │  │  3. Render content (with i18n)                                  │  │ ║
║  │  │  4. Dispatch to channels                                        │  │ ║
║  │  └────────────────────────────────────────────────────────────────┘  │ ║
║  └────────────────────────────┬─────────────────────────────────────────┘ ║
║                               │                                            ║
║              ┌────────────────┼────────────────┐                          ║
║              │                │                │                          ║
║              ▼                ▼                ▼                          ║
║  ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐                  ║
║  │     IN-APP       │ │     PUSH     │ │    EMAIL     │                  ║
║  │                  │ │              │ │              │                  ║
║  │  WebSocket       │ │  FCM/APNs    │ │  SMTP        │                  ║
║  │  (Centrifugo)    │ │  via Celery  │ │  via Celery  │                  ║
║  │                  │ │              │ │              │                  ║
║  │  Instant ⚡      │ │  Async 📱    │ │  Async 📧    │                  ║
║  └──────────────────┘ └──────────────┘ └──────────────┘                  ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 23.2 Database Schema

#### 23.2.1 Notifications Table

```sql
-- notifications: Stores all notification records
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Tenant & recipient
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Content
    notification_type VARCHAR(50) NOT NULL,  -- order_received, reservation_confirmed, etc.
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,

    -- Action
    action_url VARCHAR(500),                  -- Deep link / URL to navigate
    action_data JSONB DEFAULT '{}',           -- Additional action context

    -- Metadata
    priority VARCHAR(20) DEFAULT 'normal',    -- low, normal, high, critical
    category VARCHAR(50),                     -- grouping: orders, reservations, system
    icon VARCHAR(100),                        -- Icon identifier
    image_url VARCHAR(500),                   -- Optional image

    -- Status tracking
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Delivery tracking
    channels_sent JSONB DEFAULT '[]',         -- ["in_app", "push", "email"]
    channels_delivered JSONB DEFAULT '[]',    -- Successfully delivered channels
    channels_failed JSONB DEFAULT '[]',       -- Failed channels with reason

    -- Source event
    source_event_type VARCHAR(100),           -- Domain event that triggered this
    source_event_id VARCHAR(100),             -- Event ID for tracing
    correlation_id VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,      -- Auto-delete after expiry

    -- Indexes
    CONSTRAINT chk_notification_priority CHECK (priority IN ('low', 'normal', 'high', 'critical'))
);

-- Indexes
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_org ON notifications(organization_id);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_expires ON notifications(expires_at) WHERE expires_at IS NOT NULL;

-- Comments
COMMENT ON TABLE notifications IS 'User notifications across all channels';
COMMENT ON COLUMN notifications.channels_sent IS 'Array of channels notification was sent to';
COMMENT ON COLUMN notifications.channels_delivered IS 'Array of channels that confirmed delivery';
```

#### 23.2.2 Notification Preferences Table

```sql
-- notification_preferences: User notification settings
CREATE TABLE notification_preferences (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- User
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Global settings
    is_notifications_enabled BOOLEAN DEFAULT TRUE NOT NULL,

    -- Channel preferences
    is_in_app_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    is_push_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    is_email_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    is_sms_enabled BOOLEAN DEFAULT FALSE NOT NULL,

    -- Quiet hours
    is_quiet_hours_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    quiet_hours_start TIME,                   -- e.g., 22:00
    quiet_hours_end TIME,                     -- e.g., 07:00
    quiet_hours_timezone VARCHAR(50),         -- e.g., Asia/Jakarta

    -- Per-type preferences (JSONB for flexibility)
    -- Format: { "order_received": ["in_app", "push"], "system_alert": ["in_app", "email"] }
    type_preferences JSONB DEFAULT '{}',

    -- Per-category preferences
    -- Format: { "orders": true, "marketing": false, "system": true }
    category_preferences JSONB DEFAULT '{}',

    -- Email digest
    email_digest_frequency VARCHAR(20) DEFAULT 'instant',  -- instant, daily, weekly, none
    email_digest_time TIME DEFAULT '09:00',

    -- Push token (for mobile)
    fcm_token VARCHAR(500),
    fcm_token_updated_at TIMESTAMP WITH TIME ZONE,
    apns_token VARCHAR(500),
    apns_token_updated_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(user_id)
);

-- Indexes
CREATE INDEX idx_notification_prefs_user ON notification_preferences(user_id);

-- Comments
COMMENT ON TABLE notification_preferences IS 'User notification preferences and device tokens';
COMMENT ON COLUMN notification_preferences.type_preferences IS 'Per notification type channel preferences';
```

#### 23.2.3 Notification Templates Table

```sql
-- notification_templates: Reusable notification templates
CREATE TABLE notification_templates (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Identification
    template_code VARCHAR(100) NOT NULL UNIQUE,  -- order_received, reservation_confirmed
    category VARCHAR(50) NOT NULL,               -- orders, reservations, system

    -- Content templates (support variables like {{guest_name}})
    title_template VARCHAR(200) NOT NULL,
    body_template TEXT NOT NULL,

    -- Channel-specific templates
    push_title_template VARCHAR(100),            -- Shorter for push
    push_body_template VARCHAR(200),
    email_subject_template VARCHAR(200),
    email_body_template TEXT,                    -- HTML template

    -- Localization
    -- Format: { "id": { "title": "...", "body": "..." }, "en": { ... } }
    translations JSONB DEFAULT '{}',

    -- Defaults
    default_priority VARCHAR(20) DEFAULT 'normal',
    default_channels JSONB DEFAULT '["in_app"]',  -- Default delivery channels
    default_icon VARCHAR(100),
    default_action_url_template VARCHAR(500),

    -- Settings
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_user_dismissible BOOLEAN DEFAULT TRUE NOT NULL,
    auto_expire_hours INTEGER,                   -- Auto-expire after N hours

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT chk_template_priority CHECK (default_priority IN ('low', 'normal', 'high', 'critical'))
);

-- Indexes
CREATE INDEX idx_notification_templates_code ON notification_templates(template_code);
CREATE INDEX idx_notification_templates_category ON notification_templates(category);

-- Seed default templates
INSERT INTO notification_templates (template_code, category, title_template, body_template, default_channels, default_priority) VALUES
('order_received', 'orders', 'New Order #{{order_number}}', 'Order received from {{source}}. Total: {{total}}', '["in_app", "push"]', 'high'),
('order_ready', 'orders', 'Order #{{order_number}} Ready', 'Order is ready for pickup/delivery', '["in_app", "push"]', 'high'),
('reservation_confirmed', 'reservations', 'Reservation Confirmed', 'Reservation #{{reservation_number}} for {{guest_name}} confirmed', '["in_app", "email"]', 'normal'),
('reservation_checkin', 'reservations', 'Guest Check-in', '{{guest_name}} has checked in to Room {{room_number}}', '["in_app"]', 'normal'),
('system_maintenance', 'system', 'Scheduled Maintenance', 'System maintenance scheduled for {{maintenance_time}}', '["in_app", "email"]', 'low'),
('system_alert', 'system', 'System Alert', '{{alert_message}}', '["in_app", "push", "email"]', 'critical'),
('device_offline', 'devices', 'Device Offline', 'Device "{{device_name}}" has gone offline', '["in_app", "push"]', 'high'),
('content_approved', 'content', 'Content Approved', 'Your content "{{content_name}}" has been approved', '["in_app"]', 'normal'),
('report_ready', 'reports', 'Report Ready', 'Your report "{{report_name}}" is ready for download', '["in_app", "email"]', 'normal');

-- Comments
COMMENT ON TABLE notification_templates IS 'Notification content templates with localization';
COMMENT ON COLUMN notification_templates.translations IS 'Localized versions: { "id": { "title": "...", "body": "..." } }';
```

---

### 23.3 Notification Types Registry

```python
# shared/constants/notification_types.py
from enum import Enum

class NotificationType(str, Enum):
    """Registry of all notification types"""

    # Orders (POS)
    ORDER_RECEIVED = "order_received"
    ORDER_READY = "order_ready"
    ORDER_COMPLETED = "order_completed"
    ORDER_CANCELLED = "order_cancelled"

    # Reservations (PMS)
    RESERVATION_CONFIRMED = "reservation_confirmed"
    RESERVATION_CHECKIN = "reservation_checkin"
    RESERVATION_CHECKOUT = "reservation_checkout"
    RESERVATION_CANCELLED = "reservation_cancelled"
    RESERVATION_MODIFIED = "reservation_modified"

    # Devices (Signage)
    DEVICE_OFFLINE = "device_offline"
    DEVICE_ONLINE = "device_online"
    DEVICE_ERROR = "device_error"

    # Content
    CONTENT_APPROVED = "content_approved"
    CONTENT_REJECTED = "content_rejected"
    CONTENT_PUBLISHED = "content_published"

    # Reports
    REPORT_READY = "report_ready"
    REPORT_FAILED = "report_failed"

    # System
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_ALERT = "system_alert"
    SYSTEM_UPDATE = "system_update"

    # User
    PASSWORD_CHANGED = "password_changed"
    LOGIN_NEW_DEVICE = "login_new_device"
    ACCOUNT_LOCKED = "account_locked"


class NotificationCategory(str, Enum):
    """Notification categories for grouping"""
    ORDERS = "orders"
    RESERVATIONS = "reservations"
    DEVICES = "devices"
    CONTENT = "content"
    REPORTS = "reports"
    SYSTEM = "system"
    SECURITY = "security"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"           # Informational, can wait
    NORMAL = "normal"     # Standard notifications
    HIGH = "high"         # Important, should see soon
    CRITICAL = "critical" # Urgent, bypass quiet hours


class DeliveryChannel(str, Enum):
    """Available delivery channels"""
    IN_APP = "in_app"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
```

```typescript
// shared/constants/notificationTypes.ts
export const NotificationType = {
  // Orders
  ORDER_RECEIVED: 'order_received',
  ORDER_READY: 'order_ready',
  ORDER_COMPLETED: 'order_completed',
  ORDER_CANCELLED: 'order_cancelled',

  // Reservations
  RESERVATION_CONFIRMED: 'reservation_confirmed',
  RESERVATION_CHECKIN: 'reservation_checkin',
  RESERVATION_CHECKOUT: 'reservation_checkout',

  // Devices
  DEVICE_OFFLINE: 'device_offline',
  DEVICE_ONLINE: 'device_online',

  // Content
  CONTENT_APPROVED: 'content_approved',
  CONTENT_REJECTED: 'content_rejected',

  // Reports
  REPORT_READY: 'report_ready',

  // System
  SYSTEM_ALERT: 'system_alert',
  SYSTEM_MAINTENANCE: 'system_maintenance',
} as const;

export type NotificationType = typeof NotificationType[keyof typeof NotificationType];

export const NotificationCategory = {
  ORDERS: 'orders',
  RESERVATIONS: 'reservations',
  DEVICES: 'devices',
  CONTENT: 'content',
  REPORTS: 'reports',
  SYSTEM: 'system',
} as const;

export const NotificationPriority = {
  LOW: 'low',
  NORMAL: 'normal',
  HIGH: 'high',
  CRITICAL: 'critical',
} as const;
```

---

### 23.4 Notification Service

#### 23.4.1 Core Service

```python
# shared/notifications/service.py
from shared.constants.notification_types import NotificationType, DeliveryChannel, NotificationPriority
from shared.notifications.channels import InAppChannel, PushChannel, EmailChannel
from shared.notifications.templates import TemplateRenderer

class NotificationService:
    """Central notification service"""

    def __init__(self):
        self.template_renderer = TemplateRenderer()
        self.channels = {
            DeliveryChannel.IN_APP: InAppChannel(),
            DeliveryChannel.PUSH: PushChannel(),
            DeliveryChannel.EMAIL: EmailChannel(),
        }

    async def send(
        self,
        user_id: int,
        notification_type: NotificationType,
        context: dict,
        channels: list[DeliveryChannel] | None = None,
        priority: NotificationPriority | None = None,
        action_url: str | None = None,
        correlation_id: str | None = None
    ) -> Notification:
        """
        Send notification to user

        Args:
            user_id: Target user ID
            notification_type: Type of notification
            context: Template variables (e.g., {"order_number": "123"})
            channels: Override default channels
            priority: Override default priority
            action_url: Deep link URL
            correlation_id: For tracing
        """

        # 1. Get user and preferences
        user = await user_repo.get(user_id)
        prefs = await self._get_user_preferences(user_id)

        # 2. Check if notifications enabled
        if not prefs.is_notifications_enabled:
            logger.info(f"Notifications disabled for user {user_id}")
            return None

        # 3. Load template
        template = await self._get_template(notification_type)
        if not template or not template.is_active:
            logger.warning(f"Template not found or inactive: {notification_type}")
            return None

        # 4. Render content
        locale = user.locale or "en"
        rendered = self.template_renderer.render(template, context, locale)

        # 5. Determine channels
        effective_channels = self._determine_channels(
            requested=channels,
            template_default=template.default_channels,
            user_prefs=prefs,
            notification_type=notification_type,
            priority=priority or template.default_priority
        )

        # 6. Check quiet hours (skip for critical)
        effective_priority = priority or template.default_priority
        if effective_priority != NotificationPriority.CRITICAL:
            if self._is_quiet_hours(prefs):
                # Only send in_app during quiet hours
                effective_channels = [c for c in effective_channels if c == DeliveryChannel.IN_APP]

        # 7. Create notification record
        notification = await notification_repo.create(
            organization_id=user.organization_id,
            user_id=user_id,
            notification_type=notification_type,
            title=rendered.title,
            body=rendered.body,
            priority=effective_priority,
            category=template.category,
            action_url=action_url or self._render_action_url(template, context),
            channels_sent=[c.value for c in effective_channels],
            source_event_type=context.get("_event_type"),
            source_event_id=context.get("_event_id"),
            correlation_id=correlation_id,
            expires_at=self._calculate_expiry(template)
        )

        # 8. Dispatch to channels
        for channel in effective_channels:
            await self._dispatch_to_channel(
                channel=channel,
                notification=notification,
                rendered=rendered,
                user=user,
                prefs=prefs
            )

        return notification

    async def send_bulk(
        self,
        user_ids: list[int],
        notification_type: NotificationType,
        context: dict,
        **kwargs
    ) -> list[Notification]:
        """Send notification to multiple users"""
        notifications = []
        for user_id in user_ids:
            try:
                notif = await self.send(user_id, notification_type, context, **kwargs)
                if notif:
                    notifications.append(notif)
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
        return notifications

    async def send_to_role(
        self,
        organization_id: int,
        role: str,
        notification_type: NotificationType,
        context: dict,
        **kwargs
    ) -> list[Notification]:
        """Send notification to all users with specific role"""
        users = await user_repo.get_by_role(organization_id, role)
        return await self.send_bulk([u.id for u in users], notification_type, context, **kwargs)

    async def send_broadcast(
        self,
        organization_id: int,
        notification_type: NotificationType,
        context: dict,
        **kwargs
    ) -> list[Notification]:
        """Send notification to all users in organization"""
        users = await user_repo.get_all_active(organization_id)
        return await self.send_bulk([u.id for u in users], notification_type, context, **kwargs)

    def _determine_channels(
        self,
        requested: list[DeliveryChannel] | None,
        template_default: list[str],
        user_prefs: NotificationPreferences,
        notification_type: str,
        priority: str
    ) -> list[DeliveryChannel]:
        """Determine effective delivery channels"""

        # Start with requested or template default
        channels = requested or [DeliveryChannel(c) for c in template_default]

        # Filter by user preferences
        enabled_channels = []
        for channel in channels:
            if channel == DeliveryChannel.IN_APP and user_prefs.is_in_app_enabled:
                enabled_channels.append(channel)
            elif channel == DeliveryChannel.PUSH and user_prefs.is_push_enabled:
                enabled_channels.append(channel)
            elif channel == DeliveryChannel.EMAIL and user_prefs.is_email_enabled:
                enabled_channels.append(channel)
            elif channel == DeliveryChannel.SMS and user_prefs.is_sms_enabled:
                enabled_channels.append(channel)

        # Check per-type preferences
        type_prefs = user_prefs.type_preferences.get(notification_type)
        if type_prefs:
            enabled_channels = [c for c in enabled_channels if c.value in type_prefs]

        # Critical priority: force at least in_app
        if priority == NotificationPriority.CRITICAL and not enabled_channels:
            enabled_channels = [DeliveryChannel.IN_APP]

        return enabled_channels

    def _is_quiet_hours(self, prefs: NotificationPreferences) -> bool:
        """Check if currently in quiet hours"""
        if not prefs.is_quiet_hours_enabled:
            return False

        tz = pytz.timezone(prefs.quiet_hours_timezone or "UTC")
        now = datetime.now(tz).time()

        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end

        if start <= end:
            return start <= now <= end
        else:
            # Quiet hours span midnight
            return now >= start or now <= end

    async def _dispatch_to_channel(
        self,
        channel: DeliveryChannel,
        notification: Notification,
        rendered: RenderedNotification,
        user: User,
        prefs: NotificationPreferences
    ):
        """Dispatch notification to specific channel"""
        try:
            handler = self.channels.get(channel)
            if not handler:
                logger.warning(f"No handler for channel: {channel}")
                return

            await handler.send(notification, rendered, user, prefs)

            # Update delivery status
            await notification_repo.mark_channel_delivered(notification.id, channel.value)

        except Exception as e:
            logger.error(f"Failed to deliver via {channel}: {e}")
            await notification_repo.mark_channel_failed(
                notification.id,
                channel.value,
                str(e)
            )


# Singleton instance
notification_service = NotificationService()
```

#### 23.4.2 Channel Handlers

```python
# shared/notifications/channels/in_app.py
from shared.realtime.publisher import RealtimePublisher
from shared.constants.ws_channels import WSChannels

class InAppChannel:
    """In-app notification via WebSocket"""

    def __init__(self):
        self.realtime = RealtimePublisher()

    async def send(
        self,
        notification: Notification,
        rendered: RenderedNotification,
        user: User,
        prefs: NotificationPreferences
    ):
        """Send in-app notification via WebSocket"""

        # Publish to user's notification channel
        await self.realtime.publish(
            channel=WSChannels.NOTIFICATION.USER(
                f"org_{user.organization_id}",
                user.id
            ),
            message_type="notification.created",
            payload={
                "id": notification.id,
                "type": notification.notification_type,
                "title": rendered.title,
                "body": rendered.body,
                "priority": notification.priority,
                "category": notification.category,
                "action_url": notification.action_url,
                "icon": notification.icon,
                "image_url": notification.image_url,
                "created_at": notification.created_at.isoformat(),
            },
            tenant_id=f"org_{user.organization_id}",
            user_id=user.id,
            correlation_id=notification.correlation_id
        )


# shared/notifications/channels/push.py
from firebase_admin import messaging

class PushChannel:
    """Push notification via Firebase Cloud Messaging"""

    async def send(
        self,
        notification: Notification,
        rendered: RenderedNotification,
        user: User,
        prefs: NotificationPreferences
    ):
        """Send push notification via FCM"""

        # Get FCM token
        fcm_token = prefs.fcm_token
        if not fcm_token:
            logger.info(f"No FCM token for user {user.id}")
            return

        # Build message
        message = messaging.Message(
            notification=messaging.Notification(
                title=rendered.push_title or rendered.title[:100],
                body=rendered.push_body or rendered.body[:200],
                image=notification.image_url
            ),
            data={
                "notification_id": str(notification.id),
                "type": notification.notification_type,
                "action_url": notification.action_url or "",
                "priority": notification.priority
            },
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority="high" if notification.priority in ["high", "critical"] else "normal",
                notification=messaging.AndroidNotification(
                    icon=notification.icon or "ic_notification",
                    color="#1976D2",
                    click_action="OPEN_NOTIFICATION"
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        badge=1
                    )
                )
            )
        )

        # Send via FCM
        response = messaging.send(message)
        logger.info(f"FCM sent: {response}")


# shared/notifications/channels/email.py
from tasks.email.tasks import send_notification_email

class EmailChannel:
    """Email notification via Celery background job"""

    async def send(
        self,
        notification: Notification,
        rendered: RenderedNotification,
        user: User,
        prefs: NotificationPreferences
    ):
        """Queue email notification via Celery"""

        # Check email digest preference
        if prefs.email_digest_frequency != "instant":
            # Queue for digest instead of immediate send
            await self._queue_for_digest(notification, user, prefs)
            return

        # Queue immediate email
        send_notification_email.apply_async(
            kwargs={
                "user_id": user.id,
                "notification_id": notification.id,
                "email": user.email,
                "subject": rendered.email_subject or rendered.title,
                "body_html": rendered.email_body or self._generate_email_html(rendered),
                "correlation_id": notification.correlation_id
            },
            queue="default"
        )

    def _generate_email_html(self, rendered: RenderedNotification) -> str:
        """Generate email HTML from notification content"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1976D2;">{rendered.title}</h2>
            <p style="color: #333; line-height: 1.6;">{rendered.body}</p>
            {f'<a href="{rendered.action_url}" style="display: inline-block; padding: 12px 24px; background: #1976D2; color: white; text-decoration: none; border-radius: 4px;">View Details</a>' if rendered.action_url else ''}
        </div>
        """
```

---

### 23.5 Template Rendering

```python
# shared/notifications/templates.py
import re
from typing import NamedTuple

class RenderedNotification(NamedTuple):
    title: str
    body: str
    push_title: str | None
    push_body: str | None
    email_subject: str | None
    email_body: str | None
    action_url: str | None


class TemplateRenderer:
    """Render notification templates with variables"""

    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def render(
        self,
        template: NotificationTemplate,
        context: dict,
        locale: str = "en"
    ) -> RenderedNotification:
        """Render template with context variables"""

        # Get localized content or fallback to default
        translations = template.translations or {}
        localized = translations.get(locale, {})

        # Determine templates to use
        title_template = localized.get("title") or template.title_template
        body_template = localized.get("body") or template.body_template
        push_title_template = localized.get("push_title") or template.push_title_template
        push_body_template = localized.get("push_body") or template.push_body_template
        email_subject_template = localized.get("email_subject") or template.email_subject_template
        email_body_template = localized.get("email_body") or template.email_body_template
        action_url_template = template.default_action_url_template

        # Render each template
        return RenderedNotification(
            title=self._render_string(title_template, context),
            body=self._render_string(body_template, context),
            push_title=self._render_string(push_title_template, context) if push_title_template else None,
            push_body=self._render_string(push_body_template, context) if push_body_template else None,
            email_subject=self._render_string(email_subject_template, context) if email_subject_template else None,
            email_body=self._render_string(email_body_template, context) if email_body_template else None,
            action_url=self._render_string(action_url_template, context) if action_url_template else None,
        )

    def _render_string(self, template: str, context: dict) -> str:
        """Replace {{variable}} with context values"""
        def replace_var(match):
            var_name = match.group(1)
            return str(context.get(var_name, f"{{{{unknown:{var_name}}}}}"))

        return self.VARIABLE_PATTERN.sub(replace_var, template)
```

---

### 23.6 Event-Driven Notifications

```python
# shared/notifications/event_handlers.py
from shared.events import event_bus
from shared.notifications.service import notification_service
from shared.constants.notification_types import NotificationType

# Register event handlers
@event_bus.on("pms.reservation.created")
async def on_reservation_created(event: DomainEvent):
    """Send notification when reservation is created"""

    payload = event.payload

    # Notify front desk staff
    await notification_service.send_to_role(
        organization_id=int(event.tenant_id.replace("org_", "")),
        role="front_desk",
        notification_type=NotificationType.RESERVATION_CONFIRMED,
        context={
            "reservation_number": payload["reservation_number"],
            "guest_name": payload["guest_name"],
            "check_in_date": payload["check_in_date"],
            "room_type": payload["room_type"],
            "_event_type": event.event_type,
            "_event_id": event.event_id,
        },
        action_url=f"/reservations/{payload['reservation_id']}",
        correlation_id=event.correlation_id
    )


@event_bus.on("pos.order.received")
async def on_order_received(event: DomainEvent):
    """Send notification when order is received"""

    payload = event.payload

    # Notify kitchen staff
    await notification_service.send_to_role(
        organization_id=int(event.tenant_id.replace("org_", "")),
        role="kitchen",
        notification_type=NotificationType.ORDER_RECEIVED,
        context={
            "order_number": payload["order_number"],
            "source": payload["source"],  # "Room 101", "Table 5", etc.
            "total": payload["total_formatted"],
            "items_count": len(payload["items"]),
            "_event_type": event.event_type,
            "_event_id": event.event_id,
        },
        priority=NotificationPriority.HIGH,
        action_url=f"/kitchen/orders/{payload['order_id']}",
        correlation_id=event.correlation_id
    )


@event_bus.on("device.status.offline")
async def on_device_offline(event: DomainEvent):
    """Send notification when device goes offline"""

    payload = event.payload

    # Notify device managers
    await notification_service.send_to_role(
        organization_id=int(event.tenant_id.replace("org_", "")),
        role="device_manager",
        notification_type=NotificationType.DEVICE_OFFLINE,
        context={
            "device_name": payload["device_name"],
            "device_id": payload["device_id"],
            "last_seen": payload["last_seen_at"],
            "location": payload.get("location", "Unknown"),
            "_event_type": event.event_type,
            "_event_id": event.event_id,
        },
        priority=NotificationPriority.HIGH,
        action_url=f"/devices/{payload['device_id']}",
        correlation_id=event.correlation_id
    )
```

---

### 23.7 API Endpoints

```python
# services/notifications/routes.py
from fastapi import APIRouter, Depends, Query
from shared.notifications.service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
async def list_notifications(
    is_read: bool | None = None,
    category: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """List user notifications"""

    notifications = await notification_repo.get_by_user(
        user_id=current_user.id,
        is_read=is_read,
        category=category,
        limit=limit,
        offset=offset
    )

    total = await notification_repo.count_by_user(
        user_id=current_user.id,
        is_read=is_read,
        category=category
    )

    return {
        "success": True,
        "data": {
            "items": [n.to_dict() for n in notifications],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user)
):
    """Get unread notification count"""

    count = await notification_repo.count_unread(current_user.id)

    return {
        "success": True,
        "data": {"count": count}
    }


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""

    notification = await notification_repo.get(notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(404, "Notification not found")

    await notification_repo.mark_as_read(notification_id)

    return {"success": True}


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""

    count = await notification_repo.mark_all_as_read(current_user.id)

    return {
        "success": True,
        "data": {"marked_count": count}
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""

    notification = await notification_repo.get(notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(404, "Notification not found")

    await notification_repo.delete(notification_id)

    return {"success": True}


# Preferences endpoints
@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get user notification preferences"""

    prefs = await notification_prefs_repo.get_or_create(current_user.id)

    return {
        "success": True,
        "data": prefs.to_dict()
    }


@router.patch("/preferences")
async def update_preferences(
    data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update notification preferences"""

    prefs = await notification_prefs_repo.update(current_user.id, data)

    return {
        "success": True,
        "data": prefs.to_dict()
    }


@router.post("/preferences/fcm-token")
async def update_fcm_token(
    data: FCMTokenUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update FCM push notification token"""

    await notification_prefs_repo.update_fcm_token(
        user_id=current_user.id,
        token=data.token
    )

    return {"success": True}
```

---

### 23.8 Frontend Integration

#### 23.8.1 Notification Hook

```typescript
// features/notifications/hooks/useNotifications.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from '@/shared/hooks/useWebSocket';
import { WS_CHANNELS } from '@/shared/constants/wsChannels';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { toast } from 'sonner';

interface Notification {
  id: number;
  type: string;
  title: string;
  body: string;
  priority: string;
  category: string;
  action_url: string | null;
  is_read: boolean;
  created_at: string;
}

export function useNotifications() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Fetch notifications
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['notifications', user?.id],
    queryFn: async () => {
      const response = await api.get('/notifications');
      return response.data.data;
    },
    enabled: !!user
  });

  // Unread count
  const { data: unreadData } = useQuery({
    queryKey: ['notifications', 'unread-count', user?.id],
    queryFn: async () => {
      const response = await api.get('/notifications/unread-count');
      return response.data.data.count;
    },
    enabled: !!user,
    refetchInterval: 60000 // Refresh every minute
  });

  // Real-time notifications
  useWebSocket({
    channels: user ? [
      WS_CHANNELS.NOTIFICATION.USER(`org_${user.organization_id}`, user.id),
      WS_CHANNELS.NOTIFICATION.BROADCAST(`org_${user.organization_id}`),
    ] : [],

    onMessage: (channel, message) => {
      if (message.message_type === 'notification.created') {
        const notification = message.payload as Notification;

        // Add to cache
        queryClient.setQueryData(
          ['notifications', user?.id],
          (old: any) => ({
            ...old,
            items: [notification, ...(old?.items || [])]
          })
        );

        // Update unread count
        queryClient.setQueryData(
          ['notifications', 'unread-count', user?.id],
          (old: number) => (old || 0) + 1
        );

        // Show toast
        toast(notification.title, {
          description: notification.body,
          action: notification.action_url ? {
            label: 'View',
            onClick: () => window.location.href = notification.action_url!
          } : undefined
        });
      }
    }
  });

  // Mark as read mutation
  const markAsRead = useMutation({
    mutationFn: async (notificationId: number) => {
      await api.patch(`/notifications/${notificationId}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });

  // Mark all read
  const markAllRead = useMutation({
    mutationFn: async () => {
      await api.post('/notifications/mark-all-read');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    }
  });

  return {
    notifications: data?.items || [],
    unreadCount: unreadData || 0,
    isLoading,
    refetch,
    markAsRead: markAsRead.mutate,
    markAllRead: markAllRead.mutate,
  };
}
```

#### 23.8.2 Notification Bell Component

```typescript
// features/notifications/components/NotificationBell.tsx
import { useState } from 'react';
import { Bell, Check, CheckCheck } from 'lucide-react';
import { useNotifications } from '../hooks/useNotifications';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/shared/components/ui/popover';
import { Button } from '@/shared/components/ui/button';
import { ScrollArea } from '@/shared/components/ui/scroll-area';
import { formatDistanceToNow } from 'date-fns';

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { notifications, unreadCount, markAsRead, markAllRead } = useNotifications();

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-80 p-0" align="end">
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h4 className="font-semibold">Notifications</h4>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markAllRead()}
              className="text-xs"
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          )}
        </div>

        <ScrollArea className="h-[400px]">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <Bell className="h-8 w-8 mb-2" />
              <p>No notifications</p>
            </div>
          ) : (
            <div className="divide-y">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onRead={() => markAsRead(notification.id)}
                  onClose={() => setOpen(false)}
                />
              ))}
            </div>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

function NotificationItem({
  notification,
  onRead,
  onClose
}: {
  notification: Notification;
  onRead: () => void;
  onClose: () => void;
}) {
  const handleClick = () => {
    if (!notification.is_read) {
      onRead();
    }
    if (notification.action_url) {
      window.location.href = notification.action_url;
      onClose();
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`px-4 py-3 cursor-pointer hover:bg-muted transition-colors ${
        !notification.is_read ? 'bg-blue-50' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <p className={`text-sm ${!notification.is_read ? 'font-semibold' : ''}`}>
            {notification.title}
          </p>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {notification.body}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
          </p>
        </div>
        {!notification.is_read && (
          <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
        )}
      </div>
    </div>
  );
}
```

---

### 23.9 Ringkasan Notification Standard

| Aspect | Standard |
|--------|----------|
| **Channels** | In-App, Push (FCM), Email, SMS (future) |
| **In-App Delivery** | WebSocket via Centrifugo (Standard #20) |
| **Async Delivery** | Celery background jobs (Standard #21) |
| **Templates** | Database-driven with {{variables}} |
| **Localization** | JSONB translations per template |
| **User Preferences** | Per-channel, per-type, quiet hours |
| **Priority Levels** | low, normal, high, critical |
| **Event Integration** | Event handlers trigger notifications |
| **Email Digest** | instant, daily, weekly options |

---

## 24. API Versioning Standard

> Standard untuk versioning API endpoints agar backward-compatible

### 24.1 Overview

**Strategy:** URL Path Versioning (`/api/v1/`, `/api/v2/`)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  API VERSIONING STRATEGY                                                   ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  URL Path Versioning (RECOMMENDED)                                         ║
║  ─────────────────────────────────                                        ║
║  GET /api/v1/users                                                        ║
║  GET /api/v2/users                                                        ║
║                                                                            ║
║  Pros:                                                                     ║
║  ✓ Explicit and visible in URL                                            ║
║  ✓ Easy to route to different handlers                                    ║
║  ✓ Simple to test with curl/browser                                       ║
║  ✓ Clear in logs and monitoring                                           ║
║                                                                            ║
║  Alternative Strategies (NOT USED):                                        ║
║  ─────────────────────────────────                                        ║
║  Header: Accept: application/vnd.api+json;version=1                       ║
║  Query:  GET /api/users?version=1                                         ║
║                                                                            ║
║  Decision: URL path versioning untuk simplicity dan clarity               ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 24.2 Version Lifecycle

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  VERSION LIFECYCLE                                                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │                                                                      │  ║
║  │   ACTIVE          DEPRECATED         SUNSET           REMOVED       │  ║
║  │   ──────          ──────────         ──────           ───────       │  ║
║  │                                                                      │  ║
║  │   v3 ●────────────────────────────────────────────────────────────▶ │  ║
║  │       Current                                                        │  ║
║  │       recommended                                                    │  ║
║  │                                                                      │  ║
║  │   v2 ●────────────●───────────────────●───────────────────────────▶ │  ║
║  │       │           │                   │                              │  ║
║  │       │           │ Deprecation       │ Sunset                       │  ║
║  │       │           │ announced         │ date reached                 │  ║
║  │       │           │ (headers added)   │ (410 Gone)                   │  ║
║  │       │           │                   │                              │  ║
║  │   v1 ●────────────●───────────────────●───────────────────●          │  ║
║  │                                                           │          │  ║
║  │                                                           Removed    │  ║
║  │                                                           from code  │  ║
║  │                                                                      │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  Timeline Guideline:                                                       ║
║  ─────────────────────                                                    ║
║  • Deprecation notice: 6 months before sunset                             ║
║  • Sunset period: 3 months (returns warnings)                             ║
║  • Removal: After sunset, keep for 3 more months then remove              ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Version States:**

| State | HTTP Status | Behavior |
|-------|-------------|----------|
| **Active** | 200 | Normal operation, recommended for use |
| **Deprecated** | 200 | Works normally + deprecation headers |
| **Sunset** | 410 Gone | Returns error with migration guide |
| **Removed** | 404 Not Found | Endpoint no longer exists |

---

### 24.3 Breaking vs Non-Breaking Changes

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  CHANGE CLASSIFICATION                                                     ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  NON-BREAKING (No version bump needed)                                    ║
║  ─────────────────────────────────────                                    ║
║  ✓ Adding new optional field to response                                  ║
║  ✓ Adding new endpoint                                                    ║
║  ✓ Adding new optional query parameter                                    ║
║  ✓ Adding new enum value (if client ignores unknown)                     ║
║  ✓ Increasing rate limit                                                  ║
║  ✓ Performance improvements                                               ║
║  ✓ Bug fixes that don't change contract                                  ║
║                                                                            ║
║  BREAKING (Requires new version)                                          ║
║  ───────────────────────────────                                          ║
║  ✗ Removing field from response                                           ║
║  ✗ Renaming field in response                                             ║
║  ✗ Changing field type (string → number)                                  ║
║  ✗ Changing field from optional to required                               ║
║  ✗ Removing endpoint                                                      ║
║  ✗ Changing endpoint URL path                                             ║
║  ✗ Changing HTTP method                                                   ║
║  ✗ Changing authentication method                                         ║
║  ✗ Removing enum value                                                    ║
║  ✗ Changing error response format                                         ║
║  ✗ Decreasing rate limit                                                  ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 24.4 Implementation

#### 24.4.1 Router Structure

```python
# backend-python/app/main.py
from fastapi import FastAPI
from app.api.v1 import router as v1_router
from app.api.v2 import router as v2_router

app = FastAPI(
    title="Platform API",
    description="Enterprise Hospitality Platform API",
    version="2.0.0"
)

# Mount versioned routers
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

# Redirect root to latest docs
@app.get("/api")
async def api_root():
    return {
        "versions": {
            "v1": {"status": "deprecated", "sunset": "2025-06-01"},
            "v2": {"status": "active", "docs": "/api/v2/docs"}
        },
        "current": "v2"
    }
```

#### 24.4.2 Version Directory Structure

```
backend-python/
├── app/
│   ├── api/
│   │   ├── v1/                      # Version 1 (deprecated)
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # v1 router aggregator
│   │   │   ├── users/
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py       # v1 specific schemas
│   │   │   │   └── transformers.py  # v1 → internal conversion
│   │   │   ├── devices/
│   │   │   └── ...
│   │   │
│   │   ├── v2/                      # Version 2 (active)
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── users/
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py       # v2 schemas
│   │   │   │   └── transformers.py
│   │   │   ├── devices/
│   │   │   └── ...
│   │   │
│   │   └── shared/                  # Shared between versions
│   │       ├── dependencies.py      # Auth, pagination
│   │       └── responses.py         # Common response helpers
│   │
│   ├── services/                    # Business logic (version-agnostic)
│   │   ├── users/
│   │   ├── devices/
│   │   └── ...
│   │
│   └── models/                      # Database models (version-agnostic)
```

#### 24.4.3 Versioned Schemas

```python
# app/api/v1/users/schemas.py
from pydantic import BaseModel

class UserResponseV1(BaseModel):
    """V1 user response - DEPRECATED"""
    id: int
    username: str
    email: str
    full_name: str        # Will be split in v2
    role: str             # Single role in v1
    created_at: datetime


# app/api/v2/users/schemas.py
from pydantic import BaseModel

class UserResponseV2(BaseModel):
    """V2 user response - CURRENT"""
    id: int
    username: str
    email: str
    first_name: str       # Split from full_name
    last_name: str        # Split from full_name
    roles: list[str]      # Multiple roles in v2
    permissions: list[str]  # New field
    created_at: datetime
    updated_at: datetime  # New field


# Transformer: Internal → V1
def to_v1_response(user: User) -> UserResponseV1:
    """Transform internal user to V1 response"""
    return UserResponseV1(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=f"{user.first_name} {user.last_name}",  # Combine
        role=user.roles[0] if user.roles else "user",     # Take first
        created_at=user.created_at
    )


# Transformer: Internal → V2
def to_v2_response(user: User) -> UserResponseV2:
    """Transform internal user to V2 response"""
    return UserResponseV2(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=user.roles,
        permissions=user.get_all_permissions(),
        created_at=user.created_at,
        updated_at=user.updated_at
    )
```

---

### 24.5 Deprecation Headers

```python
# app/api/shared/deprecation.py
from fastapi import Response
from datetime import datetime

def add_deprecation_headers(
    response: Response,
    sunset_date: str,
    successor_url: str | None = None,
    message: str | None = None
):
    """Add deprecation headers to response"""

    # Standard deprecation headers
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = sunset_date  # RFC 7231 date format

    # Link to successor
    if successor_url:
        response.headers["Link"] = f'<{successor_url}>; rel="successor-version"'

    # Custom deprecation message
    if message:
        response.headers["X-Deprecation-Message"] = message


# Usage in deprecated endpoint
@router.get("/users", deprecated=True)
async def list_users_v1(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    List users (DEPRECATED)

    **Deprecated**: This endpoint will be removed on 2025-06-01.
    Please migrate to `/api/v2/users`.
    """

    add_deprecation_headers(
        response=response,
        sunset_date="Sat, 01 Jun 2025 00:00:00 GMT",
        successor_url="/api/v2/users",
        message="Please migrate to v2. See /api/v2/docs for details."
    )

    users = await user_service.list_users(current_user.organization_id)
    return {
        "success": True,
        "data": [to_v1_response(u) for u in users]
    }
```

**Response Headers for Deprecated Endpoint:**

```http
HTTP/1.1 200 OK
Content-Type: application/json
Deprecation: true
Sunset: Sat, 01 Jun 2025 00:00:00 GMT
Link: </api/v2/users>; rel="successor-version"
X-Deprecation-Message: Please migrate to v2. See /api/v2/docs for details.
```

---

### 24.6 Sunset Handler

```python
# app/api/shared/sunset.py
from fastapi import HTTPException
from datetime import datetime

class SunsetMiddleware:
    """Middleware to handle sunset versions"""

    SUNSET_VERSIONS = {
        "v1": {
            "sunset_date": datetime(2025, 6, 1),
            "successor": "v2",
            "migration_guide": "https://docs.example.com/migration/v1-to-v2"
        }
    }

    async def __call__(self, request, call_next):
        # Extract version from path
        path = request.url.path
        version = self._extract_version(path)

        if version and version in self.SUNSET_VERSIONS:
            sunset_info = self.SUNSET_VERSIONS[version]

            if datetime.utcnow() >= sunset_info["sunset_date"]:
                # Version has sunset - return 410 Gone
                raise HTTPException(
                    status_code=410,
                    detail={
                        "error": "version_sunset",
                        "message": f"API {version} has been sunset and is no longer available.",
                        "successor": f"/api/{sunset_info['successor']}",
                        "migration_guide": sunset_info["migration_guide"]
                    }
                )

        return await call_next(request)

    def _extract_version(self, path: str) -> str | None:
        """Extract version from path like /api/v1/..."""
        import re
        match = re.match(r"/api/(v\d+)/", path)
        return match.group(1) if match else None
```

**Sunset Response:**

```json
{
  "error": "version_sunset",
  "message": "API v1 has been sunset and is no longer available.",
  "successor": "/api/v2",
  "migration_guide": "https://docs.example.com/migration/v1-to-v2"
}
```

---

### 24.7 Documentation per Version

```python
# app/main.py
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

# Separate OpenAPI specs per version
app_v1 = FastAPI(
    title="Platform API v1",
    description="**DEPRECATED** - Please migrate to v2",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    openapi_url="/api/v1/openapi.json"
)

app_v2 = FastAPI(
    title="Platform API v2",
    description="Enterprise Hospitality Platform API (Current)",
    version="2.0.0",
    docs_url=None,
    openapi_url="/api/v2/openapi.json"
)

# Mount versioned apps
main_app = FastAPI()
main_app.mount("/api/v1", app_v1)
main_app.mount("/api/v2", app_v2)

# Custom docs endpoints
@main_app.get("/api/v1/docs", include_in_schema=False)
async def v1_docs():
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title="API v1 Docs (Deprecated)"
    )

@main_app.get("/api/v2/docs", include_in_schema=False)
async def v2_docs():
    return get_swagger_ui_html(
        openapi_url="/api/v2/openapi.json",
        title="API v2 Docs"
    )

# Redirect /docs to latest version
@main_app.get("/docs", include_in_schema=False)
async def docs_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/v2/docs")
```

---

### 24.8 Version Logging

```python
# app/middleware/logging.py
import structlog

logger = structlog.get_logger()

class APIVersionLoggingMiddleware:
    """Log API version in all requests"""

    async def __call__(self, request, call_next):
        # Extract version
        path = request.url.path
        version = self._extract_version(path)

        # Bind to logger context
        structlog.contextvars.bind_contextvars(
            api_version=version or "unknown",
            endpoint=path
        )

        response = await call_next(request)

        # Log request with version
        logger.info(
            "api_request",
            method=request.method,
            path=path,
            api_version=version,
            status_code=response.status_code
        )

        return response
```

---

### 24.9 Migration Guide Template

```markdown
# Migration Guide: v1 → v2

## Overview
API v2 introduces several improvements including:
- Split `full_name` into `first_name` and `last_name`
- Multiple roles support
- Added `permissions` field
- Added `updated_at` timestamp

## Timeline
- **Deprecation announced**: 2024-12-01
- **Sunset date**: 2025-06-01
- **Removal date**: 2025-09-01

## Breaking Changes

### Users Endpoint

| v1 | v2 | Migration |
|----|----|----|
| `GET /api/v1/users` | `GET /api/v2/users` | Change URL |
| `full_name: string` | `first_name: string, last_name: string` | Split field |
| `role: string` | `roles: string[]` | Wrap in array |
| - | `permissions: string[]` | New field (ignore if not needed) |
| - | `updated_at: datetime` | New field (ignore if not needed) |

### Code Examples

**Before (v1):**
```javascript
const response = await fetch('/api/v1/users');
const users = await response.json();
users.forEach(user => {
  console.log(user.full_name);  // "John Doe"
  console.log(user.role);       // "admin"
});
```

**After (v2):**
```javascript
const response = await fetch('/api/v2/users');
const users = await response.json();
users.forEach(user => {
  console.log(`${user.first_name} ${user.last_name}`);  // "John Doe"
  console.log(user.roles);  // ["admin", "manager"]
});
```

## Support
If you have questions about migration, contact api-support@example.com
```

---

### 24.10 Frontend Version Handling

```typescript
// shared/lib/api/client.ts
import axios from 'axios';

const API_VERSION = 'v2';  // Current version

export const api = axios.create({
  baseURL: `/api/${API_VERSION}`,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercept deprecation warnings
api.interceptors.response.use(
  (response) => {
    // Check for deprecation headers
    const deprecation = response.headers['deprecation'];
    const sunset = response.headers['sunset'];
    const successor = response.headers['link'];

    if (deprecation === 'true') {
      console.warn(
        `[API Deprecation Warning] ${response.config.url} is deprecated.`,
        `Sunset: ${sunset}`,
        `Successor: ${successor}`
      );

      // Optional: Send to error tracking
      // errorTracker.captureWarning('API Deprecation', { ... });
    }

    return response;
  },
  (error) => {
    // Handle 410 Gone (sunset)
    if (error.response?.status === 410) {
      const detail = error.response.data;
      console.error(
        `[API Sunset] ${error.config.url} has been sunset.`,
        `Please migrate to ${detail.successor}`,
        `Guide: ${detail.migration_guide}`
      );

      // Redirect to migration notice or handle gracefully
    }

    return Promise.reject(error);
  }
);
```

---

### 24.11 Version Registry

```python
# shared/constants/api_versions.py
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

class VersionStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    REMOVED = "removed"


@dataclass
class APIVersion:
    version: str
    status: VersionStatus
    release_date: datetime
    deprecation_date: datetime | None = None
    sunset_date: datetime | None = None
    successor: str | None = None
    changelog_url: str | None = None


# Version registry
API_VERSIONS = {
    "v1": APIVersion(
        version="v1",
        status=VersionStatus.DEPRECATED,
        release_date=datetime(2024, 1, 1),
        deprecation_date=datetime(2024, 12, 1),
        sunset_date=datetime(2025, 6, 1),
        successor="v2",
        changelog_url="/docs/changelog/v1"
    ),
    "v2": APIVersion(
        version="v2",
        status=VersionStatus.ACTIVE,
        release_date=datetime(2024, 12, 1),
        changelog_url="/docs/changelog/v2"
    )
}


def get_current_version() -> str:
    """Get current active version"""
    for version, info in API_VERSIONS.items():
        if info.status == VersionStatus.ACTIVE:
            return version
    return "v2"  # fallback


def is_version_deprecated(version: str) -> bool:
    """Check if version is deprecated"""
    info = API_VERSIONS.get(version)
    return info and info.status == VersionStatus.DEPRECATED


def is_version_sunset(version: str) -> bool:
    """Check if version has sunset"""
    info = API_VERSIONS.get(version)
    if not info or not info.sunset_date:
        return False
    return datetime.utcnow() >= info.sunset_date
```

---

### 24.12 Ringkasan API Versioning Standard

| Aspect | Standard |
|--------|----------|
| **Strategy** | URL Path Versioning (`/api/v1/`, `/api/v2/`) |
| **Version Format** | `v{major}` (e.g., v1, v2, v3) |
| **Active Versions** | Max 2 versions active simultaneously |
| **Deprecation Notice** | 6 months before sunset |
| **Sunset Period** | 3 months (returns 410 Gone) |
| **Breaking Changes** | Field removal, rename, type change, required param |
| **Non-Breaking** | New optional field, new endpoint, bug fixes |
| **Headers** | `Deprecation`, `Sunset`, `Link` (successor) |
| **Documentation** | Separate OpenAPI spec per version |
| **Logging** | API version included in all request logs |

---

## 25. Feature Flags Standard

> Standard untuk enable/disable fitur secara dinamis tanpa deploy ulang

### 25.1 Overview

**Use Cases:**
- **Gradual Rollout**: Release fitur ke 10% user dulu, lalu 50%, lalu 100%
- **Kill Switch**: Disable fitur bermasalah tanpa deploy
- **A/B Testing**: Eksperimen dengan variant berbeda
- **Per-Tenant Features**: Premium fitur untuk tenant tertentu
- **Module Toggle**: Enable/disable module (Puzzle Architecture)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  FEATURE FLAGS ARCHITECTURE                                                ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │                      FLAG EVALUATION FLOW                            │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  Request with context:                                                     ║
║  { user_id: 123, tenant_id: "org_456", role: "admin" }                    ║
║                              │                                             ║
║                              ▼                                             ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │                    FEATURE FLAG SERVICE                              │  ║
║  │  ┌─────────────────────────────────────────────────────────────┐    │  ║
║  │  │  1. Check Redis cache                                        │    │  ║
║  │  │  2. If miss → Load from database                            │    │  ║
║  │  │  3. Evaluate rules against context                          │    │  ║
║  │  │  4. Return boolean/variant                                   │    │  ║
║  │  └─────────────────────────────────────────────────────────────┘    │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                              │                                             ║
║              ┌───────────────┴───────────────┐                            ║
║              ▼                               ▼                            ║
║      ┌──────────────┐               ┌──────────────┐                     ║
║      │   ENABLED    │               │   DISABLED   │                     ║
║      │              │               │              │                     ║
║      │  Show new    │               │  Show old    │                     ║
║      │  feature     │               │  behavior    │                     ║
║      └──────────────┘               └──────────────┘                     ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 25.2 Flag Types

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  FLAG TYPES                                                                ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Type          Purpose                    Example                         ║
║  ────────────  ─────────────────────────  ─────────────────────────────  ║
║                                                                            ║
║  RELEASE       New feature rollout        pms.new_booking_flow            ║
║                On/Off toggle              pos.kitchen_display_v2          ║
║                Gradual percentage         signage.player_v2               ║
║                                                                            ║
║  EXPERIMENT    A/B testing                checkout.button_color           ║
║                Returns variant (A/B/C)    dashboard.layout_variant        ║
║                                                                            ║
║  OPS           Kill switch                api.rate_limiting               ║
║                Emergency disable          payments.stripe_gateway         ║
║                Circuit breaker            external.weather_api            ║
║                                                                            ║
║  PERMISSION    Per-tenant features        module.pms_enabled              ║
║                Premium features           feature.advanced_reports        ║
║                Beta access                beta.ai_suggestions             ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 25.3 Flag Naming Convention

**Format:** `{module}.{feature}` atau `{module}.{feature}.{sub}`

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  FLAG NAMING CONVENTION                                                    ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Pattern: {module}.{feature}                                              ║
║                                                                            ║
║  {module}   = pms, pos, hrm, signage, core, api                          ║
║  {feature}  = descriptive_feature_name                                    ║
║                                                                            ║
║  Examples:                                                                 ║
║  ─────────────────────────────────────────────────────────────────────    ║
║  pms.new_reservation_flow       → New reservation UI                      ║
║  pms.dynamic_pricing            → Dynamic room pricing                    ║
║  pos.kitchen_display_v2         → New kitchen display                     ║
║  pos.split_bill                 → Split bill feature                      ║
║  signage.player_offline_mode    → Offline mode for player                 ║
║  core.dark_mode                 → Dark mode UI                            ║
║  core.ai_assistant              → AI chat assistant                       ║
║  api.graphql_endpoint           → GraphQL API                             ║
║  api.rate_limit_v2              → New rate limiting                       ║
║  module.pms_enabled             → PMS module toggle                       ║
║  module.pos_enabled             → POS module toggle                       ║
║  beta.experimental_dashboard    → Beta dashboard                          ║
║                                                                            ║
║  Naming Rules:                                                             ║
║  ─────────────────────────────────────────────────────────────────────    ║
║  ✓ Use snake_case                                                         ║
║  ✓ Be descriptive                                                         ║
║  ✓ Max 50 characters                                                      ║
║  ✗ No spaces or special characters                                        ║
║  ✗ No version numbers in name (use metadata instead)                     ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 25.4 Database Schema

```sql
-- feature_flags: Flag definitions
CREATE TABLE feature_flags (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Identification
    flag_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Type & configuration
    flag_type VARCHAR(20) NOT NULL DEFAULT 'release',  -- release, experiment, ops, permission

    -- Default state
    is_enabled BOOLEAN DEFAULT FALSE NOT NULL,

    -- Variants (for A/B testing)
    -- Format: [{"key": "control", "weight": 50}, {"key": "variant_a", "weight": 50}]
    variants JSONB DEFAULT '[]',

    -- Rollout percentage (0-100)
    rollout_percentage INTEGER DEFAULT 100,

    -- Targeting rules
    -- Format: {"tenants": [1,2,3], "users": [10,20], "roles": ["admin"]}
    targeting_rules JSONB DEFAULT '{}',

    -- Metadata
    tags JSONB DEFAULT '[]',           -- ["beta", "premium", "experimental"]
    owner VARCHAR(100),                 -- Team/person responsible

    -- Lifecycle
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT chk_flag_type CHECK (flag_type IN ('release', 'experiment', 'ops', 'permission')),
    CONSTRAINT chk_rollout_percentage CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100)
);

-- Indexes
CREATE INDEX idx_feature_flags_key ON feature_flags(flag_key);
CREATE INDEX idx_feature_flags_type ON feature_flags(flag_type);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(is_enabled) WHERE is_enabled = TRUE;

-- Comments
COMMENT ON TABLE feature_flags IS 'Feature flag definitions and rules';
COMMENT ON COLUMN feature_flags.targeting_rules IS 'JSON rules for tenant/user/role targeting';


-- feature_flag_overrides: Per-tenant/user overrides
CREATE TABLE feature_flag_overrides (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Flag reference
    flag_id INTEGER NOT NULL REFERENCES feature_flags(id) ON DELETE CASCADE,

    -- Target (one of these must be set)
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- Override value
    is_enabled BOOLEAN NOT NULL,
    variant_key VARCHAR(50),           -- For experiment flags

    -- Metadata
    reason VARCHAR(500),               -- Why this override exists
    expires_at TIMESTAMP WITH TIME ZONE,  -- Optional expiration

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Ensure only one type of target
    CONSTRAINT chk_single_target CHECK (
        (organization_id IS NOT NULL AND user_id IS NULL) OR
        (organization_id IS NULL AND user_id IS NOT NULL)
    ),

    -- Unique override per target
    UNIQUE(flag_id, organization_id),
    UNIQUE(flag_id, user_id)
);

-- Indexes
CREATE INDEX idx_flag_overrides_flag ON feature_flag_overrides(flag_id);
CREATE INDEX idx_flag_overrides_org ON feature_flag_overrides(organization_id);
CREATE INDEX idx_flag_overrides_user ON feature_flag_overrides(user_id);

-- Comments
COMMENT ON TABLE feature_flag_overrides IS 'Per-tenant or per-user flag overrides';


-- Seed some default flags
INSERT INTO feature_flags (flag_key, name, description, flag_type, is_enabled, rollout_percentage) VALUES
('core.dark_mode', 'Dark Mode', 'Enable dark mode UI', 'release', true, 100),
('core.ai_assistant', 'AI Assistant', 'AI chat assistant in dashboard', 'release', false, 0),
('module.pms_enabled', 'PMS Module', 'Enable PMS (Hotel Operations) module', 'permission', false, 100),
('module.pos_enabled', 'POS Module', 'Enable POS (F&B) module', 'permission', false, 100),
('module.hrm_enabled', 'HRM Module', 'Enable HRM (Payroll) module', 'permission', false, 100),
('api.rate_limiting', 'API Rate Limiting', 'Enable API rate limiting', 'ops', true, 100),
('beta.new_dashboard', 'New Dashboard', 'Beta: New dashboard layout', 'release', false, 10);
```

---

### 25.5 Feature Flag Service

```python
# shared/feature_flags/service.py
import hashlib
from typing import Any
from shared.cache import redis_client
from shared.database import get_db

class FeatureFlagService:
    """Central feature flag evaluation service"""

    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "ff:"

    async def is_enabled(
        self,
        flag_key: str,
        context: dict | None = None
    ) -> bool:
        """
        Check if feature flag is enabled

        Args:
            flag_key: Flag identifier (e.g., "pms.new_booking_flow")
            context: Evaluation context {"tenant_id": 123, "user_id": 456, "role": "admin"}

        Returns:
            Boolean indicating if flag is enabled
        """
        context = context or {}

        # Load flag (from cache or DB)
        flag = await self._get_flag(flag_key)
        if not flag:
            return False

        # Archived flags are always disabled
        if flag.is_archived:
            return False

        # Check for overrides first
        override = await self._get_override(flag.id, context)
        if override is not None:
            return override.is_enabled

        # Base enabled check
        if not flag.is_enabled:
            return False

        # Check targeting rules
        if not self._matches_targeting(flag, context):
            return False

        # Check rollout percentage
        if flag.rollout_percentage < 100:
            if not self._in_rollout(flag_key, context, flag.rollout_percentage):
                return False

        return True

    async def get_variant(
        self,
        flag_key: str,
        context: dict | None = None,
        default: str = "control"
    ) -> str:
        """
        Get variant for experiment flag

        Args:
            flag_key: Flag identifier
            context: Evaluation context
            default: Default variant if flag disabled

        Returns:
            Variant key (e.g., "control", "variant_a", "variant_b")
        """
        context = context or {}

        # Load flag
        flag = await self._get_flag(flag_key)
        if not flag or not flag.is_enabled:
            return default

        # Check for override with specific variant
        override = await self._get_override(flag.id, context)
        if override and override.variant_key:
            return override.variant_key

        # No variants defined
        if not flag.variants:
            return "control" if flag.is_enabled else default

        # Deterministic variant assignment based on user/tenant
        return self._assign_variant(flag_key, context, flag.variants)

    async def get_all_flags(
        self,
        context: dict | None = None
    ) -> dict[str, bool]:
        """Get all flags evaluated for context (for frontend bootstrap)"""
        context = context or {}

        flags = await self._get_all_flags()
        result = {}

        for flag in flags:
            result[flag.flag_key] = await self.is_enabled(flag.flag_key, context)

        return result

    def _matches_targeting(self, flag, context: dict) -> bool:
        """Check if context matches targeting rules"""
        rules = flag.targeting_rules or {}

        # No rules = match all
        if not rules:
            return True

        # Check tenant targeting
        if "tenants" in rules and rules["tenants"]:
            tenant_id = context.get("tenant_id")
            if tenant_id not in rules["tenants"]:
                return False

        # Check user targeting
        if "users" in rules and rules["users"]:
            user_id = context.get("user_id")
            if user_id not in rules["users"]:
                return False

        # Check role targeting
        if "roles" in rules and rules["roles"]:
            role = context.get("role")
            if role not in rules["roles"]:
                return False

        return True

    def _in_rollout(self, flag_key: str, context: dict, percentage: int) -> bool:
        """Deterministic percentage rollout based on user/tenant"""
        # Use user_id or tenant_id for consistent assignment
        identifier = str(context.get("user_id") or context.get("tenant_id") or "anonymous")

        # Create deterministic hash
        hash_input = f"{flag_key}:{identifier}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Map to 0-100
        bucket = hash_value % 100

        return bucket < percentage

    def _assign_variant(self, flag_key: str, context: dict, variants: list) -> str:
        """Deterministic variant assignment"""
        identifier = str(context.get("user_id") or context.get("tenant_id") or "anonymous")

        # Create deterministic hash
        hash_input = f"{flag_key}:variant:{identifier}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Calculate total weight
        total_weight = sum(v.get("weight", 0) for v in variants)
        if total_weight == 0:
            return variants[0]["key"] if variants else "control"

        # Map hash to weight range
        bucket = hash_value % total_weight

        # Find matching variant
        cumulative = 0
        for variant in variants:
            cumulative += variant.get("weight", 0)
            if bucket < cumulative:
                return variant["key"]

        return variants[-1]["key"]

    async def _get_flag(self, flag_key: str):
        """Get flag from cache or database"""
        cache_key = f"{self.CACHE_PREFIX}{flag_key}"

        # Try cache first
        cached = await redis_client.get(cache_key)
        if cached:
            return FeatureFlag.from_cache(cached)

        # Load from database
        flag = await flag_repo.get_by_key(flag_key)
        if flag:
            await redis_client.setex(cache_key, self.CACHE_TTL, flag.to_cache())

        return flag

    async def _get_override(self, flag_id: int, context: dict):
        """Get override for tenant or user"""
        tenant_id = context.get("tenant_id")
        user_id = context.get("user_id")

        # Check user override first (more specific)
        if user_id:
            override = await override_repo.get_by_user(flag_id, user_id)
            if override:
                return override

        # Check tenant override
        if tenant_id:
            override = await override_repo.get_by_tenant(flag_id, tenant_id)
            if override:
                return override

        return None


# Singleton instance
feature_flags = FeatureFlagService()
```

---

### 25.6 Backend Integration

#### 25.6.1 Decorator

```python
# shared/feature_flags/decorators.py
from functools import wraps
from fastapi import HTTPException, Depends
from shared.feature_flags.service import feature_flags

def require_feature(flag_key: str):
    """Decorator to require feature flag for endpoint"""

    async def dependency(current_user = Depends(get_current_user)):
        context = {
            "tenant_id": current_user.organization_id,
            "user_id": current_user.id,
            "role": current_user.role
        }

        is_enabled = await feature_flags.is_enabled(flag_key, context)

        if not is_enabled:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "feature_disabled",
                    "message": f"Feature '{flag_key}' is not enabled for your account",
                    "flag": flag_key
                }
            )

        return True

    return Depends(dependency)


# Usage in routes
@router.post("/reservations/dynamic-pricing")
async def calculate_dynamic_price(
    request: PriceRequest,
    _: bool = require_feature("pms.dynamic_pricing"),
    current_user: User = Depends(get_current_user)
):
    """Calculate dynamic room pricing (requires feature flag)"""
    return await pricing_service.calculate(request)
```

#### 25.6.2 Context Manager

```python
# shared/feature_flags/context.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def feature_enabled(flag_key: str, context: dict):
    """Context manager for conditional feature execution"""
    is_enabled = await feature_flags.is_enabled(flag_key, context)

    if is_enabled:
        yield True
    else:
        yield False


# Usage
async def process_order(order: Order, user: User):
    context = {"tenant_id": user.organization_id, "user_id": user.id}

    async with feature_enabled("pos.split_bill", context) as enabled:
        if enabled:
            # New flow with split bill
            await process_with_split_bill(order)
        else:
            # Legacy flow
            await process_legacy(order)
```

#### 25.6.3 Service Method

```python
# In any service
class ReservationService:
    async def create_reservation(self, data: ReservationCreate, user: User):
        context = {
            "tenant_id": user.organization_id,
            "user_id": user.id,
            "role": user.role
        }

        # Check which flow to use
        if await feature_flags.is_enabled("pms.new_reservation_flow", context):
            return await self._create_v2(data, user)
        else:
            return await self._create_v1(data, user)

    async def get_pricing(self, room_type_id: int, dates: DateRange, user: User):
        context = {"tenant_id": user.organization_id}

        # Check for dynamic pricing
        if await feature_flags.is_enabled("pms.dynamic_pricing", context):
            return await self._calculate_dynamic_price(room_type_id, dates)
        else:
            return await self._get_static_price(room_type_id)
```

---

### 25.7 Frontend Integration

#### 25.7.1 Feature Flag Hook

```typescript
// shared/hooks/useFeatureFlag.ts
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { api } from '@/lib/api';

interface FeatureFlagsResponse {
  flags: Record<string, boolean>;
}

// Fetch all flags on app load
export function useFeatureFlags() {
  const { user } = useAuth();

  return useQuery({
    queryKey: ['feature-flags', user?.id],
    queryFn: async (): Promise<Record<string, boolean>> => {
      const response = await api.get<FeatureFlagsResponse>('/feature-flags');
      return response.data.flags;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });
}

// Check single flag
export function useFeatureFlag(flagKey: string): boolean {
  const { data: flags, isLoading } = useFeatureFlags();

  if (isLoading || !flags) {
    return false; // Default to disabled while loading
  }

  return flags[flagKey] ?? false;
}

// Check multiple flags
export function useFeatureFlagsCheck(flagKeys: string[]): Record<string, boolean> {
  const { data: flags } = useFeatureFlags();

  const result: Record<string, boolean> = {};
  for (const key of flagKeys) {
    result[key] = flags?.[key] ?? false;
  }

  return result;
}
```

#### 25.7.2 Feature Flag Component

```typescript
// shared/components/FeatureFlag.tsx
import { useFeatureFlag } from '@/shared/hooks/useFeatureFlag';
import { ReactNode } from 'react';

interface FeatureFlagProps {
  flag: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function FeatureFlag({ flag, children, fallback = null }: FeatureFlagProps) {
  const isEnabled = useFeatureFlag(flag);

  if (isEnabled) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
}

// Usage
function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>

      {/* Show new widget only if flag enabled */}
      <FeatureFlag flag="core.ai_assistant">
        <AIAssistantWidget />
      </FeatureFlag>

      {/* Show with fallback */}
      <FeatureFlag
        flag="pms.new_booking_widget"
        fallback={<LegacyBookingWidget />}
      >
        <NewBookingWidget />
      </FeatureFlag>

      {/* Conditional rendering */}
      <FeatureFlag flag="beta.experimental_charts">
        <ExperimentalCharts />
      </FeatureFlag>
    </div>
  );
}
```

#### 25.7.3 Feature Flag Context Provider

```typescript
// shared/contexts/FeatureFlagContext.tsx
import { createContext, useContext, ReactNode } from 'react';
import { useFeatureFlags } from '@/shared/hooks/useFeatureFlag';

interface FeatureFlagContextValue {
  flags: Record<string, boolean>;
  isLoading: boolean;
  isEnabled: (flag: string) => boolean;
  getVariant: (flag: string) => string | null;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue | null>(null);

export function FeatureFlagProvider({ children }: { children: ReactNode }) {
  const { data: flags, isLoading } = useFeatureFlags();

  const value: FeatureFlagContextValue = {
    flags: flags ?? {},
    isLoading,
    isEnabled: (flag: string) => flags?.[flag] ?? false,
    getVariant: (flag: string) => flags?.[`${flag}:variant`] ?? null,
  };

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlagContext() {
  const context = useContext(FeatureFlagContext);
  if (!context) {
    throw new Error('useFeatureFlagContext must be used within FeatureFlagProvider');
  }
  return context;
}

// Usage in component
function MyComponent() {
  const { isEnabled, isLoading } = useFeatureFlagContext();

  if (isLoading) return <Spinner />;

  return (
    <div>
      {isEnabled('pms.dynamic_pricing') && <DynamicPricingSection />}
      {isEnabled('core.dark_mode') && <DarkModeToggle />}
    </div>
  );
}
```

---

### 25.8 Admin API

```python
# services/feature_flags/routes.py
from fastapi import APIRouter, Depends, HTTPException
from shared.auth import require_permission

router = APIRouter(prefix="/feature-flags", tags=["Feature Flags"])

@router.get("")
async def list_flags(
    current_user: User = Depends(get_current_user)
):
    """Get all feature flags evaluated for current user context"""
    context = {
        "tenant_id": current_user.organization_id,
        "user_id": current_user.id,
        "role": current_user.role
    }

    flags = await feature_flags.get_all_flags(context)

    return {
        "success": True,
        "data": {"flags": flags}
    }


@router.get("/admin")
async def list_all_flags(
    _: bool = Depends(require_permission("admin.feature_flags.view")),
    current_user: User = Depends(get_current_user)
):
    """List all flag definitions (admin only)"""
    flags = await flag_repo.get_all()

    return {
        "success": True,
        "data": {
            "items": [f.to_dict() for f in flags]
        }
    }


@router.post("/admin")
async def create_flag(
    data: FeatureFlagCreate,
    _: bool = Depends(require_permission("admin.feature_flags.manage")),
    current_user: User = Depends(get_current_user)
):
    """Create new feature flag (admin only)"""
    flag = await flag_repo.create(data, current_user.id)

    # Invalidate cache
    await redis_client.delete(f"ff:{flag.flag_key}")

    return {
        "success": True,
        "data": flag.to_dict()
    }


@router.patch("/admin/{flag_key}")
async def update_flag(
    flag_key: str,
    data: FeatureFlagUpdate,
    _: bool = Depends(require_permission("admin.feature_flags.manage")),
    current_user: User = Depends(get_current_user)
):
    """Update feature flag (admin only)"""
    flag = await flag_repo.get_by_key(flag_key)
    if not flag:
        raise HTTPException(404, "Flag not found")

    updated = await flag_repo.update(flag.id, data)

    # Invalidate cache
    await redis_client.delete(f"ff:{flag_key}")

    return {
        "success": True,
        "data": updated.to_dict()
    }


@router.post("/admin/{flag_key}/toggle")
async def toggle_flag(
    flag_key: str,
    _: bool = Depends(require_permission("admin.feature_flags.manage")),
    current_user: User = Depends(get_current_user)
):
    """Quick toggle flag on/off (admin only)"""
    flag = await flag_repo.get_by_key(flag_key)
    if not flag:
        raise HTTPException(404, "Flag not found")

    updated = await flag_repo.toggle(flag.id)

    # Invalidate cache
    await redis_client.delete(f"ff:{flag_key}")

    # Log the change
    logger.info(
        f"Feature flag toggled",
        flag_key=flag_key,
        new_state=updated.is_enabled,
        toggled_by=current_user.id
    )

    return {
        "success": True,
        "data": {
            "flag_key": flag_key,
            "is_enabled": updated.is_enabled
        }
    }


@router.post("/admin/{flag_key}/overrides")
async def create_override(
    flag_key: str,
    data: FlagOverrideCreate,
    _: bool = Depends(require_permission("admin.feature_flags.manage")),
    current_user: User = Depends(get_current_user)
):
    """Create override for tenant or user (admin only)"""
    flag = await flag_repo.get_by_key(flag_key)
    if not flag:
        raise HTTPException(404, "Flag not found")

    override = await override_repo.create(flag.id, data, current_user.id)

    # Invalidate related caches
    await redis_client.delete(f"ff:{flag_key}")

    return {
        "success": True,
        "data": override.to_dict()
    }
```

---

### 25.9 Flag Registry

```python
# shared/constants/feature_flags.py

class FeatureFlags:
    """Registry of all feature flag keys"""

    # Core features
    class CORE:
        DARK_MODE = "core.dark_mode"
        AI_ASSISTANT = "core.ai_assistant"
        NEW_NAVIGATION = "core.new_navigation"

    # Module toggles (Puzzle Architecture)
    class MODULE:
        PMS_ENABLED = "module.pms_enabled"
        POS_ENABLED = "module.pos_enabled"
        HRM_ENABLED = "module.hrm_enabled"
        INVENTORY_ENABLED = "module.inventory_enabled"
        ACCOUNTING_ENABLED = "module.accounting_enabled"

    # PMS features
    class PMS:
        NEW_RESERVATION_FLOW = "pms.new_reservation_flow"
        DYNAMIC_PRICING = "pms.dynamic_pricing"
        ROOM_UPGRADE_SUGGESTIONS = "pms.room_upgrade_suggestions"
        GUEST_PREFERENCES = "pms.guest_preferences"

    # POS features
    class POS:
        KITCHEN_DISPLAY_V2 = "pos.kitchen_display_v2"
        SPLIT_BILL = "pos.split_bill"
        QR_ORDERING = "pos.qr_ordering"

    # Signage features
    class SIGNAGE:
        PLAYER_V2 = "signage.player_v2"
        OFFLINE_MODE = "signage.offline_mode"
        ANALYTICS_DASHBOARD = "signage.analytics_dashboard"

    # API/Ops features
    class OPS:
        RATE_LIMITING = "api.rate_limiting"
        GRAPHQL_ENDPOINT = "api.graphql_endpoint"
        MAINTENANCE_MODE = "ops.maintenance_mode"

    # Beta/Experimental
    class BETA:
        NEW_DASHBOARD = "beta.new_dashboard"
        AI_REPORTS = "beta.ai_reports"
        VOICE_COMMANDS = "beta.voice_commands"
```

```typescript
// shared/constants/featureFlags.ts
export const FeatureFlags = {
  // Core
  CORE: {
    DARK_MODE: 'core.dark_mode',
    AI_ASSISTANT: 'core.ai_assistant',
    NEW_NAVIGATION: 'core.new_navigation',
  },

  // Modules
  MODULE: {
    PMS_ENABLED: 'module.pms_enabled',
    POS_ENABLED: 'module.pos_enabled',
    HRM_ENABLED: 'module.hrm_enabled',
  },

  // PMS
  PMS: {
    NEW_RESERVATION_FLOW: 'pms.new_reservation_flow',
    DYNAMIC_PRICING: 'pms.dynamic_pricing',
  },

  // POS
  POS: {
    KITCHEN_DISPLAY_V2: 'pos.kitchen_display_v2',
    SPLIT_BILL: 'pos.split_bill',
  },

  // Beta
  BETA: {
    NEW_DASHBOARD: 'beta.new_dashboard',
    AI_REPORTS: 'beta.ai_reports',
  },
} as const;
```

---

### 25.10 Module Integration (Puzzle Architecture)

```python
# shared/modules/loader.py
from shared.feature_flags.service import feature_flags

class ModuleLoader:
    """Load modules based on feature flags"""

    MODULE_FLAGS = {
        "pms": "module.pms_enabled",
        "pos": "module.pos_enabled",
        "hrm": "module.hrm_enabled",
        "inventory": "module.inventory_enabled",
        "accounting": "module.accounting_enabled",
    }

    async def get_enabled_modules(self, tenant_id: int) -> list[str]:
        """Get list of enabled modules for tenant"""
        context = {"tenant_id": tenant_id}
        enabled = []

        for module, flag_key in self.MODULE_FLAGS.items():
            if await feature_flags.is_enabled(flag_key, context):
                enabled.append(module)

        return enabled

    async def is_module_enabled(self, module: str, tenant_id: int) -> bool:
        """Check if specific module is enabled for tenant"""
        flag_key = self.MODULE_FLAGS.get(module)
        if not flag_key:
            return False

        context = {"tenant_id": tenant_id}
        return await feature_flags.is_enabled(flag_key, context)


# Usage in route protection
def require_module(module: str):
    """Decorator to require module to be enabled"""

    async def dependency(current_user = Depends(get_current_user)):
        loader = ModuleLoader()
        is_enabled = await loader.is_module_enabled(
            module,
            current_user.organization_id
        )

        if not is_enabled:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "module_disabled",
                    "message": f"Module '{module}' is not enabled for your organization",
                    "module": module
                }
            )

        return True

    return Depends(dependency)


# Usage
@router.get("/reservations")
async def list_reservations(
    _: bool = require_module("pms"),
    current_user: User = Depends(get_current_user)
):
    """List reservations (requires PMS module)"""
    pass
```

---

### 25.11 Ringkasan Feature Flags Standard

| Aspect | Standard |
|--------|----------|
| **Flag Types** | release, experiment, ops, permission |
| **Naming** | `{module}.{feature}` (snake_case, max 50 chars) |
| **Storage** | PostgreSQL (persistent) + Redis (cache) |
| **Cache TTL** | 5 minutes |
| **Evaluation Order** | Override → Targeting → Rollout → Default |
| **Targeting** | Per-tenant, per-user, per-role |
| **Rollout** | Percentage-based, deterministic hash |
| **Backend** | `@require_feature` decorator, service method |
| **Frontend** | `useFeatureFlag` hook, `<FeatureFlag>` component |
| **Module Toggle** | Integrated with Puzzle Architecture |

---

## 26. Performance SLA Standard

> Standard untuk target performa sistem dan cara mengukurnya

### 26.1 Overview

**Purpose:**
- Menetapkan target performa yang terukur
- Menentukan threshold untuk alerting
- Memberikan baseline untuk capacity planning
- Alignment dengan observability (Standard #15)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PERFORMANCE MONITORING STACK                                              ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │                           APPLICATION                                 │ ║
║  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │ ║
║  │  │ Backend │  │Frontend │  │ Worker  │  │ Player  │                 │ ║
║  │  │ FastAPI │  │  Vite   │  │ Celery  │  │  Vite   │                 │ ║
║  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                 │ ║
║  └───────┼────────────┼────────────┼────────────┼───────────────────────┘ ║
║          │            │            │            │                          ║
║          │ Metrics    │ RUM        │ Metrics    │ Metrics                 ║
║          ▼            ▼            ▼            ▼                          ║
║  ┌──────────────────────────────────────────────────────────────────────┐ ║
║  │                         PROMETHEUS                                    │ ║
║  │  • Response time histograms                                          │ ║
║  │  • Error rates                                                        │ ║
║  │  • Queue depths                                                       │ ║
║  │  • Resource usage                                                     │ ║
║  └─────────────────────────────┬────────────────────────────────────────┘ ║
║                                │                                           ║
║              ┌─────────────────┼─────────────────┐                        ║
║              ▼                 ▼                 ▼                        ║
║  ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐              ║
║  │     GRAFANA      │ │ ALERTMANAGER │ │     JAEGER       │              ║
║  │                  │ │              │ │                  │              ║
║  │  • Dashboards    │ │  • Slack     │ │  • Traces        │              ║
║  │  • SLA reports   │ │  • Email     │ │  • Latency       │              ║
║  │  • Trends        │ │  • PagerDuty │ │  • Dependencies  │              ║
║  └──────────────────┘ └──────────────┘ └──────────────────┘              ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 26.2 Response Time Targets

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  RESPONSE TIME SLA                                                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Endpoint Type          p50        p95        p99        Max              ║
║  ───────────────────    ─────      ─────      ─────      ─────            ║
║                                                                            ║
║  API - Read (GET)       50ms       200ms      500ms      2s               ║
║  API - Write (POST)     100ms      300ms      800ms      3s               ║
║  API - List/Paginated   100ms      300ms      1s         5s               ║
║  API - Report/Export    500ms      2s         5s         30s              ║
║                                                                            ║
║  Search (Meilisearch)   20ms       50ms       100ms      500ms            ║
║                                                                            ║
║  WebSocket Message      10ms       30ms       50ms       200ms            ║
║                                                                            ║
║  Database Query         10ms       50ms       100ms      500ms            ║
║  Cache Read (Redis)     1ms        5ms        10ms       50ms             ║
║  Cache Write (Redis)    2ms        10ms       20ms       100ms            ║
║                                                                            ║
║  File Upload (per MB)   200ms      500ms      1s         5s               ║
║  File Download          100ms      300ms      500ms      2s               ║
║                                                                            ║
║  Background Job Start   100ms      500ms      1s         5s               ║
║  Email Send (queued)    50ms       200ms      500ms      1s               ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Definition:**
- **p50**: 50% of requests complete within this time (median)
- **p95**: 95% of requests complete within this time
- **p99**: 99% of requests complete within this time
- **Max**: Timeout threshold, requests exceeding this are errors

---

### 26.3 Availability Targets

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  AVAILABILITY SLA                                                          ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Service              Target      Monthly         Yearly                  ║
║                       Uptime      Downtime        Downtime                ║
║  ──────────────────   ─────────   ─────────────   ─────────────           ║
║                                                                            ║
║  API Gateway          99.9%       43.8 minutes    8.76 hours              ║
║  Backend API          99.9%       43.8 minutes    8.76 hours              ║
║  Database (Primary)   99.95%      21.9 minutes    4.38 hours              ║
║  Redis Cache          99.9%       43.8 minutes    8.76 hours              ║
║  Meilisearch          99.5%       3.6 hours       43.8 hours              ║
║  Centrifugo (WS)      99.5%       3.6 hours       43.8 hours              ║
║  Celery Workers       99.5%       3.6 hours       43.8 hours              ║
║  File Storage (R2)    99.9%       43.8 minutes    8.76 hours              ║
║                                                                            ║
║  Overall Platform     99.5%       3.6 hours       43.8 hours              ║
║                                                                            ║
║  Notes:                                                                    ║
║  • Planned maintenance excluded (with 24h notice)                         ║
║  • Measured in rolling 30-day windows                                     ║
║  • Degraded performance counts as partial outage                          ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Availability Calculation:**

```
Availability % = (Total Minutes - Downtime Minutes) / Total Minutes × 100

Monthly Minutes = 30 days × 24 hours × 60 minutes = 43,200 minutes

99.9% availability = 43,200 - 43.2 = 43,156.8 minutes uptime
                   = 43.2 minutes downtime allowed
```

---

### 26.4 Resource Budgets

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  RESOURCE LIMITS PER SERVICE                                               ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Service              CPU        Memory      Replicas    Scaling          ║
║  ──────────────────   ─────────  ─────────   ─────────   ─────────        ║
║                                                                            ║
║  Backend API          2 cores    2 GB        2-8         Auto (CPU>70%)   ║
║  Celery Worker        1 core     1 GB        2-4         Queue depth      ║
║  Celery Beat          0.5 core   512 MB      1           Fixed            ║
║  PostgreSQL           4 cores    8 GB        1 (primary) Manual           ║
║  Redis                1 core     2 GB        1           Fixed            ║
║  Meilisearch          2 cores    4 GB        1           Manual           ║
║  Centrifugo           1 core     1 GB        2           Connection count ║
║  Nginx                0.5 core   512 MB      2           Fixed            ║
║                                                                            ║
║  Total (minimum)      12 cores   19 GB                                    ║
║  Total (recommended)  20 cores   32 GB                                    ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Per-Tenant Resource Guidelines:**

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PER-TENANT ESTIMATES                                                      ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Tenant Size     Users    Devices    Storage    DB Size    Bandwidth      ║
║  ─────────────   ──────   ─────────  ─────────  ─────────  ─────────      ║
║                                                                            ║
║  Small           1-10     1-10       5 GB       500 MB     10 GB/mo       ║
║  Medium          10-50    10-50      25 GB      2 GB       50 GB/mo       ║
║  Large           50-200   50-100     100 GB     10 GB      200 GB/mo      ║
║  Enterprise      200+     100+       500 GB+    50 GB+     1 TB+/mo       ║
║                                                                            ║
║  Concurrent Users per Tenant:                                              ║
║  • Small: 5 concurrent                                                     ║
║  • Medium: 20 concurrent                                                   ║
║  • Large: 100 concurrent                                                   ║
║  • Enterprise: 500+ concurrent                                             ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 26.5 Prometheus Metrics

```python
# shared/metrics/prometheus.py
from prometheus_client import Counter, Histogram, Gauge, Info
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'tenant_id'],
    buckets=[.01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 10.0]
)

# Database metrics
DB_QUERY_LATENCY = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['operation', 'table'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1.0]
)

DB_CONNECTION_POOL = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['pool_name', 'state']  # state: active, idle, waiting
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Cache hit count',
    ['cache_type', 'key_prefix']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Cache miss count',
    ['cache_type', 'key_prefix']
)

CACHE_LATENCY = Histogram(
    'cache_operation_duration_seconds',
    'Cache operation latency',
    ['operation', 'cache_type'],
    buckets=[.0001, .0005, .001, .005, .01, .05, .1]
)

# Queue metrics
QUEUE_SIZE = Gauge(
    'celery_queue_size',
    'Celery queue size',
    ['queue_name']
)

TASK_DURATION = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration',
    ['task_name', 'status'],
    buckets=[.1, .5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
)

# WebSocket metrics
WS_CONNECTIONS = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections',
    ['tenant_id']
)

WS_MESSAGES = Counter(
    'websocket_messages_total',
    'WebSocket messages sent',
    ['direction', 'message_type']  # direction: inbound, outbound
)

# Business metrics
ACTIVE_USERS = Gauge(
    'active_users_current',
    'Currently active users',
    ['tenant_id']
)

API_ERRORS = Counter(
    'api_errors_total',
    'API errors',
    ['error_type', 'endpoint', 'tenant_id']
)
```

---

### 26.6 FastAPI Middleware

```python
# shared/middleware/metrics.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from shared.metrics.prometheus import REQUEST_COUNT, REQUEST_LATENCY

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics"""

    async def dispatch(self, request: Request, call_next):
        # Extract labels
        method = request.method
        endpoint = self._get_endpoint(request)
        tenant_id = self._get_tenant_id(request)

        # Start timer
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=response.status_code,
            tenant_id=tenant_id
        ).inc()

        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint,
            tenant_id=tenant_id
        ).observe(duration)

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        # Log slow requests
        if duration > 1.0:  # > 1 second
            logger.warning(
                "Slow request detected",
                method=method,
                endpoint=endpoint,
                duration=duration,
                tenant_id=tenant_id
            )

        return response

    def _get_endpoint(self, request: Request) -> str:
        """Get normalized endpoint path"""
        # Replace IDs with placeholders for cardinality control
        path = request.url.path
        # /api/v1/users/123 -> /api/v1/users/{id}
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        return path

    def _get_tenant_id(self, request: Request) -> str:
        """Extract tenant ID from request"""
        # From JWT token or header
        tenant = getattr(request.state, 'tenant_id', None)
        return str(tenant) if tenant else 'unknown'
```

---

### 26.7 Database Query Tracking

```python
# shared/database/instrumentation.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
from shared.metrics.prometheus import DB_QUERY_LATENCY

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.perf_counter())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start_time = conn.info['query_start_time'].pop()
    duration = time.perf_counter() - start_time

    # Extract operation and table
    operation = statement.split()[0].upper()  # SELECT, INSERT, UPDATE, DELETE
    table = _extract_table_name(statement)

    # Record metric
    DB_QUERY_LATENCY.labels(
        operation=operation,
        table=table
    ).observe(duration)

    # Log slow queries
    if duration > 0.5:  # > 500ms
        logger.warning(
            "Slow query detected",
            operation=operation,
            table=table,
            duration=duration,
            query=statement[:200]  # Truncate
        )

def _extract_table_name(statement: str) -> str:
    """Extract table name from SQL statement"""
    import re
    # Simple extraction - works for most cases
    match = re.search(r'(?:FROM|INTO|UPDATE)\s+["\']?(\w+)["\']?', statement, re.IGNORECASE)
    return match.group(1) if match else 'unknown'
```

---

### 26.8 Alerting Rules

```yaml
# prometheus/alerts/performance.yml
groups:
  - name: performance_alerts
    rules:
      # API Latency Alerts
      - alert: APILatencyWarning
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
          > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API p95 latency > 200ms"
          description: "Endpoint {{ $labels.endpoint }} p95 latency is {{ $value }}s"

      - alert: APILatencyCritical
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))
          > 0.5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "API p95 latency > 500ms"
          description: "Endpoint {{ $labels.endpoint }} p95 latency is {{ $value }}s"

      # Error Rate Alerts
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m]))
          > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Error rate > 1%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: CriticalErrorRate
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m]))
          > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5%"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Database Alerts
      - alert: SlowDatabaseQueries
        expr: |
          histogram_quantile(0.95, sum(rate(db_query_duration_seconds_bucket[5m])) by (le, table))
          > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database p95 latency > 100ms"
          description: "Table {{ $labels.table }} query latency is {{ $value }}s"

      - alert: DatabaseConnectionPoolExhausted
        expr: |
          db_connection_pool_size{state="waiting"} > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhausted"
          description: "{{ $value }} connections waiting"

      # Cache Alerts
      - alert: LowCacheHitRate
        expr: |
          sum(rate(cache_hits_total[5m]))
          / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))
          < 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate < 80%"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"

      # Queue Alerts
      - alert: HighQueueDepth
        expr: celery_queue_size > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Celery queue depth > 100"
          description: "Queue {{ $labels.queue_name }} has {{ $value }} tasks"

      - alert: CriticalQueueDepth
        expr: celery_queue_size > 500
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Celery queue depth > 500"
          description: "Queue {{ $labels.queue_name }} has {{ $value }} tasks"

      # Resource Alerts
      - alert: HighMemoryUsage
        expr: |
          container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage > 85%"
          description: "Container {{ $labels.container }} memory at {{ $value | humanizePercentage }}"

      - alert: HighCPUUsage
        expr: |
          rate(container_cpu_usage_seconds_total[5m]) / container_spec_cpu_quota * 100000 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU usage > 80%"
          description: "Container {{ $labels.container }} CPU at {{ $value }}%"
```

---

### 26.9 Grafana Dashboard

```json
// grafana/dashboards/api-performance.json
{
  "title": "API Performance",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
          "legendFormat": "{{ endpoint }}"
        }
      ]
    },
    {
      "title": "p95 Latency",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
          "legendFormat": "{{ endpoint }}"
        }
      ],
      "yAxes": [{ "format": "s" }],
      "thresholds": [
        { "value": 0.2, "color": "yellow" },
        { "value": 0.5, "color": "red" }
      ]
    },
    {
      "title": "Error Rate",
      "type": "singlestat",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
        }
      ],
      "format": "percent",
      "thresholds": "1,5",
      "colors": ["green", "yellow", "red"]
    },
    {
      "title": "Database Query Latency",
      "type": "heatmap",
      "targets": [
        {
          "expr": "sum(rate(db_query_duration_seconds_bucket[5m])) by (le)"
        }
      ]
    },
    {
      "title": "Cache Hit Rate",
      "type": "gauge",
      "targets": [
        {
          "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) * 100"
        }
      ],
      "thresholds": "70,85",
      "colors": ["red", "yellow", "green"]
    },
    {
      "title": "Active WebSocket Connections",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(websocket_connections_active) by (tenant_id)",
          "legendFormat": "{{ tenant_id }}"
        }
      ]
    },
    {
      "title": "Celery Queue Depth",
      "type": "graph",
      "targets": [
        {
          "expr": "celery_queue_size",
          "legendFormat": "{{ queue_name }}"
        }
      ]
    }
  ]
}
```

---

### 26.10 SLA Reporting

```python
# shared/reports/sla_report.py
from datetime import datetime, timedelta
from typing import NamedTuple

class SLAMetrics(NamedTuple):
    period_start: datetime
    period_end: datetime
    availability_percent: float
    downtime_minutes: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    total_requests: int
    sla_met: bool


async def generate_sla_report(
    start_date: datetime,
    end_date: datetime,
    tenant_id: int | None = None
) -> SLAMetrics:
    """Generate SLA report for period"""

    # Query Prometheus for metrics
    prom_client = PrometheusClient()

    # Availability
    availability = await prom_client.query(
        f'avg_over_time(up{{job="backend"}}[{_period(start_date, end_date)}]) * 100'
    )

    # Latency percentiles
    p50 = await prom_client.query(
        f'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[{_period(start_date, end_date)}])) by (le)) * 1000'
    )
    p95 = await prom_client.query(
        f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[{_period(start_date, end_date)}])) by (le)) * 1000'
    )
    p99 = await prom_client.query(
        f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[{_period(start_date, end_date)}])) by (le)) * 1000'
    )

    # Error rate
    errors = await prom_client.query(
        f'sum(increase(http_requests_total{{status_code=~"5.."}}[{_period(start_date, end_date)}]))'
    )
    total = await prom_client.query(
        f'sum(increase(http_requests_total[{_period(start_date, end_date)}]))'
    )
    error_rate = (errors / total * 100) if total > 0 else 0

    # Calculate downtime
    period_minutes = (end_date - start_date).total_seconds() / 60
    downtime_minutes = period_minutes * (100 - availability) / 100

    # Check SLA compliance
    sla_met = (
        availability >= 99.5 and
        p95 <= 200 and
        error_rate <= 1.0
    )

    return SLAMetrics(
        period_start=start_date,
        period_end=end_date,
        availability_percent=availability,
        downtime_minutes=downtime_minutes,
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
        error_rate_percent=error_rate,
        total_requests=int(total),
        sla_met=sla_met
    )


# Monthly SLA report task
@shared_task(name="reports.tasks.generate_monthly_sla")
def generate_monthly_sla_report():
    """Generate monthly SLA report for all tenants"""

    # Calculate last month
    today = datetime.utcnow()
    first_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = first_of_month - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Generate platform-wide report
    report = await generate_sla_report(last_month_start, last_month_end)

    # Store report
    await sla_report_repo.create(report)

    # Send to stakeholders
    await email_service.send_template(
        to=settings.SLA_REPORT_RECIPIENTS,
        template="sla_monthly_report",
        context={
            "period": f"{last_month_start.strftime('%B %Y')}",
            "availability": f"{report.availability_percent:.2f}%",
            "downtime": f"{report.downtime_minutes:.1f} minutes",
            "p95_latency": f"{report.p95_latency_ms:.0f}ms",
            "error_rate": f"{report.error_rate_percent:.2f}%",
            "sla_met": report.sla_met
        }
    )
```

---

### 26.11 Performance Testing

```python
# tests/performance/load_test.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    """Load test user for API endpoints"""

    wait_time = between(1, 3)
    host = "http://localhost:8001"

    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        self.token = response.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def list_devices(self):
        """List devices - high frequency"""
        self.client.get("/api/v1/devices", headers=self.headers)

    @task(5)
    def get_device(self):
        """Get single device"""
        self.client.get("/api/v1/devices/1", headers=self.headers)

    @task(3)
    def list_contents(self):
        """List contents"""
        self.client.get("/api/v1/contents", headers=self.headers)

    @task(2)
    def search_contents(self):
        """Search contents"""
        self.client.get("/api/v1/search/contents?q=test", headers=self.headers)

    @task(1)
    def create_content(self):
        """Create content - lower frequency"""
        self.client.post("/api/v1/contents", json={
            "name": "Test Content",
            "content_type": "image"
        }, headers=self.headers)


# Run with:
# locust -f tests/performance/load_test.py --users 100 --spawn-rate 10 --run-time 5m
```

**Performance Test Targets:**

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  LOAD TEST TARGETS                                                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Scenario             Users    RPS      p95 Target    Error Target        ║
║  ──────────────────   ──────   ──────   ──────────    ─────────────       ║
║                                                                            ║
║  Normal Load          100      50       < 200ms       < 0.1%              ║
║  Peak Load            500      200      < 500ms       < 0.5%              ║
║  Stress Test          1000     500      < 1s          < 1%                ║
║  Spike Test           2000     1000     < 2s          < 5%                ║
║                                                                            ║
║  Database:                                                                 ║
║  • Connection pool: 100 connections                                        ║
║  • Max queries/sec: 1000                                                   ║
║                                                                            ║
║  Cache:                                                                    ║
║  • Hit rate target: > 85%                                                  ║
║  • Max operations/sec: 10000                                               ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 26.12 Ringkasan Performance SLA Standard

| Aspect | Standard |
|--------|----------|
| **API Read p95** | < 200ms |
| **API Write p95** | < 300ms |
| **Search p95** | < 50ms |
| **Database Query p95** | < 100ms |
| **Cache Operation p95** | < 10ms |
| **Platform Availability** | 99.5% |
| **API Availability** | 99.9% |
| **Error Rate Target** | < 1% |
| **Metrics Collection** | Prometheus |
| **Visualization** | Grafana |
| **Alerting** | Alertmanager |
| **Load Testing** | Locust |

---

*Last Updated: 2025-12-09*
