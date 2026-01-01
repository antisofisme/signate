# Development Standards V4

> Standards #20+ untuk Real-time, Background Jobs, dan Integration Patterns

**Contents:**
- **#20** - Real-time/WebSocket Standard
- **#21** - Background Job (Celery) Standard
- **#22** - Search (Meilisearch) Standard
- **#23** - Notification Standard

---

## 20. Real-time/WebSocket Standard

> Standard untuk real-time communication menggunakan Centrifugo

### 20.1 Overview

**Tech Stack:**
- **Server**: Centrifugo (self-hosted)
- **Protocol**: WebSocket + Server-Sent Events fallback
- **Auth**: JWT tokens

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  REAL-TIME ARCHITECTURE                                                    ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐         ║
║  │  Client  │     │  Backend │     │Centrifugo│     │  Client  │         ║
║  │ (React)  │     │ (FastAPI)│     │ (WS Hub) │     │ (Player) │         ║
║  └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘         ║
║       │                │                │                │               ║
║       │ 1. Login       │                │                │               ║
║       │───────────────▶│                │                │               ║
║       │                │                │                │               ║
║       │◀───────────────│                │                │               ║
║       │ 2. JWT + WS    │                │                │               ║
║       │    Token       │                │                │               ║
║       │                │                │                │               ║
║       │ 3. Connect WS with token        │                │               ║
║       │────────────────────────────────▶│                │               ║
║       │                │                │                │               ║
║       │ 4. Subscribe to channels        │                │               ║
║       │────────────────────────────────▶│◀───────────────│               ║
║       │                │                │  5. Also       │               ║
║       │                │                │     subscribed │               ║
║       │                │                │                │               ║
║       │                │ 6. Publish     │                │               ║
║       │                │    event       │                │               ║
║       │                │───────────────▶│                │               ║
║       │                │                │                │               ║
║       │◀───────────────────────────────▶│◀──────────────▶│               ║
║       │ 7. Broadcast to all subscribers │                │               ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 20.2 Channel Naming Convention

**Format:** `{tenant}:{module}:{scope}:{id?}`

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  CHANNEL NAMING CONVENTION                                                 ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Pattern: {tenant}:{module}:{scope}:{id?}                                 ║
║                                                                            ║
║  {tenant}  = org_123 (organization_id)                                    ║
║  {module}  = device, notification, chat, dashboard                        ║
║  {scope}   = status, updates, user, room                                  ║
║  {id}      = Optional specific ID                                         ║
║                                                                            ║
║  Examples:                                                                 ║
║  ─────────────────────────────────────────────────────────────────────    ║
║  org_123:device:status           → All device status updates              ║
║  org_123:device:status:456       → Specific device #456 status            ║
║  org_123:notification:user:789   → Notifications for user #789            ║
║  org_123:notification:broadcast  → Org-wide announcements                 ║
║  org_123:dashboard:updates       → Dashboard real-time metrics            ║
║  org_123:pms:reservation:101     → Reservation #101 updates               ║
║  org_123:pos:order:kitchen       → Kitchen display orders                 ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Channel Registry:**

```typescript
// shared/constants/wsChannels.ts
export const WS_CHANNELS = {
  // Device channels
  DEVICE: {
    STATUS: (orgId: string) => `${orgId}:device:status`,
    STATUS_SINGLE: (orgId: string, deviceId: number) => `${orgId}:device:status:${deviceId}`,
    COMMAND: (orgId: string, deviceId: number) => `${orgId}:device:command:${deviceId}`,
  },

  // Notification channels
  NOTIFICATION: {
    USER: (orgId: string, userId: number) => `${orgId}:notification:user:${userId}`,
    BROADCAST: (orgId: string) => `${orgId}:notification:broadcast`,
    ROLE: (orgId: string, role: string) => `${orgId}:notification:role:${role}`,
  },

  // Dashboard channels
  DASHBOARD: {
    UPDATES: (orgId: string) => `${orgId}:dashboard:updates`,
    METRICS: (orgId: string) => `${orgId}:dashboard:metrics`,
  },

  // PMS channels
  PMS: {
    RESERVATION: (orgId: string, reservationId: number) => `${orgId}:pms:reservation:${reservationId}`,
    ROOM_STATUS: (orgId: string) => `${orgId}:pms:room:status`,
    HOUSEKEEPING: (orgId: string) => `${orgId}:pms:housekeeping`,
  },

  // POS channels
  POS: {
    ORDER: (orgId: string, orderId: number) => `${orgId}:pos:order:${orderId}`,
    KITCHEN: (orgId: string, outletId: number) => `${orgId}:pos:kitchen:${outletId}`,
  },
} as const;
```

```python
# shared/constants/ws_channels.py
class WSChannels:
    class DEVICE:
        @staticmethod
        def STATUS(org_id: str) -> str:
            return f"{org_id}:device:status"

        @staticmethod
        def STATUS_SINGLE(org_id: str, device_id: int) -> str:
            return f"{org_id}:device:status:{device_id}"

        @staticmethod
        def COMMAND(org_id: str, device_id: int) -> str:
            return f"{org_id}:device:command:{device_id}"

    class NOTIFICATION:
        @staticmethod
        def USER(org_id: str, user_id: int) -> str:
            return f"{org_id}:notification:user:{user_id}"

        @staticmethod
        def BROADCAST(org_id: str) -> str:
            return f"{org_id}:notification:broadcast"

    class DASHBOARD:
        @staticmethod
        def UPDATES(org_id: str) -> str:
            return f"{org_id}:dashboard:updates"
```

---

### 20.3 Message Format

**Aligned dengan Event Schema (#18):**

```typescript
// WebSocket message format
interface WSMessage<T = unknown> {
  // Message identification
  message_id: string;              // UUID
  message_type: string;            // "{module}.{entity}.{action}"
  timestamp: string;               // ISO8601 UTC

  // Context (aligned with Event Schema)
  tenant_id: string;
  user_id: number | null;
  correlation_id: string;

  // Payload
  payload: T;
}
```

**Examples:**

```json
// Device status update
{
  "message_id": "msg-550e8400-e29b-41d4",
  "message_type": "device.status.changed",
  "timestamp": "2025-12-09T10:30:00.123Z",
  "tenant_id": "org_123",
  "user_id": null,
  "correlation_id": "req-abc-123",
  "payload": {
    "device_id": 456,
    "status": "online",
    "last_seen_at": "2025-12-09T10:30:00.123Z"
  }
}

// Notification
{
  "message_id": "msg-660e8400-e29b-41d4",
  "message_type": "notification.created",
  "timestamp": "2025-12-09T10:30:00.123Z",
  "tenant_id": "org_123",
  "user_id": 789,
  "correlation_id": "req-xyz-456",
  "payload": {
    "notification_id": 101,
    "title": "New Order",
    "body": "Order #5001 received from Room 101",
    "type": "info",
    "action_url": "/orders/5001"
  }
}
```

---

### 20.4 Authentication

#### 20.4.1 Connection Token (JWT)

```python
# Backend: Generate WebSocket token
from shared.auth.jwt import create_ws_token

@router.get("/ws/token")
async def get_ws_token(current_user: User = Depends(get_current_user)):
    """Generate JWT token for WebSocket connection"""

    # Token payload
    payload = {
        "sub": str(current_user.id),
        "org": str(current_user.organization_id),
        "channels": get_user_channels(current_user),
        "exp": datetime.utcnow() + timedelta(hours=12)
    }

    token = create_ws_token(payload)

    return {"token": token}

def get_user_channels(user: User) -> list[str]:
    """Get channels user is allowed to subscribe"""
    org = user.organization_id
    channels = [
        # Personal notifications
        f"{org}:notification:user:{user.id}",
        # Org-wide broadcasts
        f"{org}:notification:broadcast",
        # Dashboard (if has permission)
        f"{org}:dashboard:updates",
    ]

    # Role-based channels
    if user.has_permission("device.view"):
        channels.append(f"{org}:device:status")

    if user.has_permission("pms.reservations.view"):
        channels.append(f"{org}:pms:room:status")

    return channels
```

#### 20.4.2 Centrifugo Config

```json
// centrifugo.json
{
  "token_hmac_secret_key": "${CENTRIFUGO_SECRET}",
  "api_key": "${CENTRIFUGO_API_KEY}",
  "admin": true,
  "admin_password": "${CENTRIFUGO_ADMIN_PASSWORD}",

  "namespaces": [
    {
      "name": "device",
      "presence": true,
      "join_leave": true,
      "history_size": 10,
      "history_ttl": "5m"
    },
    {
      "name": "notification",
      "presence": false,
      "history_size": 50,
      "history_ttl": "24h"
    },
    {
      "name": "dashboard",
      "presence": false,
      "history_size": 1,
      "history_ttl": "1m"
    }
  ]
}
```

---

### 20.5 Backend Publishing

```python
# shared/realtime/publisher.py
import httpx
from shared.constants.ws_channels import WSChannels

class RealtimePublisher:
    def __init__(self):
        self.api_url = settings.CENTRIFUGO_API_URL
        self.api_key = settings.CENTRIFUGO_API_KEY

    async def publish(
        self,
        channel: str,
        message_type: str,
        payload: dict,
        tenant_id: str,
        user_id: int | None = None,
        correlation_id: str | None = None
    ):
        """Publish message to Centrifugo channel"""

        message = {
            "message_id": f"msg-{uuid4()}",
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "correlation_id": correlation_id or f"pub-{uuid4()}",
            "payload": payload
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/publish",
                json={"channel": channel, "data": message},
                headers={"Authorization": f"apikey {self.api_key}"}
            )
            response.raise_for_status()

        # Also log for tracing
        logger.info(
            f"Published to {channel}",
            message_type=message_type,
            correlation_id=message["correlation_id"]
        )

# Usage
realtime = RealtimePublisher()

# Publish device status
await realtime.publish(
    channel=WSChannels.DEVICE.STATUS(org_id),
    message_type="device.status.changed",
    payload={"device_id": 456, "status": "online"},
    tenant_id=org_id
)

# Publish notification
await realtime.publish(
    channel=WSChannels.NOTIFICATION.USER(org_id, user_id),
    message_type="notification.created",
    payload={"title": "New Order", "body": "..."},
    tenant_id=org_id,
    user_id=user_id
)
```

---

### 20.6 Frontend Client

#### 20.6.1 React Hook

```typescript
// shared/hooks/useWebSocket.ts
import { Centrifuge } from 'centrifuge';
import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '@/features/auth/hooks/useAuth';

interface UseWebSocketOptions {
  channels: string[];
  onMessage?: (channel: string, message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const { channels, onMessage, onConnect, onDisconnect } = options;
  const { getWsToken } = useAuth();
  const centrifuge = useRef<Centrifuge | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function connect() {
      try {
        // Get WebSocket token
        const { token } = await getWsToken();

        // Create Centrifuge instance
        centrifuge.current = new Centrifuge(
          import.meta.env.VITE_WS_URL,
          { token }
        );

        // Connection handlers
        centrifuge.current.on('connected', () => {
          if (isMounted) {
            setIsConnected(true);
            setError(null);
            onConnect?.();
          }
        });

        centrifuge.current.on('disconnected', () => {
          if (isMounted) {
            setIsConnected(false);
            onDisconnect?.();
          }
        });

        centrifuge.current.on('error', (ctx) => {
          if (isMounted) {
            setError(ctx.error?.message || 'Connection error');
          }
        });

        // Subscribe to channels
        for (const channel of channels) {
          const sub = centrifuge.current.newSubscription(channel);

          sub.on('publication', (ctx) => {
            onMessage?.(channel, ctx.data as WSMessage);
          });

          sub.subscribe();
        }

        // Connect
        centrifuge.current.connect();

      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Failed to connect');
        }
      }
    }

    connect();

    // Cleanup
    return () => {
      isMounted = false;
      centrifuge.current?.disconnect();
    };
  }, [channels.join(',')]); // Reconnect if channels change

  // Publish method
  const publish = useCallback(async (channel: string, data: unknown) => {
    if (centrifuge.current?.state === 'connected') {
      const sub = centrifuge.current.getSubscription(channel);
      await sub?.publish(data);
    }
  }, []);

  return { isConnected, error, publish };
}
```

#### 20.6.2 Usage Example

```typescript
// features/devices/components/DeviceStatusMonitor.tsx
import { useWebSocket } from '@/shared/hooks/useWebSocket';
import { WS_CHANNELS } from '@/shared/constants/wsChannels';
import { useAuth } from '@/features/auth/hooks/useAuth';

export function DeviceStatusMonitor() {
  const { user } = useAuth();
  const [devices, setDevices] = useState<Device[]>([]);

  const { isConnected } = useWebSocket({
    channels: [WS_CHANNELS.DEVICE.STATUS(user.organization_id)],

    onMessage: (channel, message) => {
      if (message.message_type === 'device.status.changed') {
        const { device_id, status } = message.payload;

        setDevices(prev => prev.map(d =>
          d.id === device_id ? { ...d, status } : d
        ));
      }
    },

    onConnect: () => {
      console.log('WebSocket connected');
    },

    onDisconnect: () => {
      console.log('WebSocket disconnected, will reconnect...');
    }
  });

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span>{isConnected ? 'Live' : 'Connecting...'}</span>
      </div>

      <DeviceList devices={devices} />
    </div>
  );
}
```

#### 20.6.3 Notification Hook

```typescript
// features/notifications/hooks/useNotifications.ts
import { useWebSocket } from '@/shared/hooks/useWebSocket';
import { WS_CHANNELS } from '@/shared/constants/wsChannels';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { toast } from 'sonner';

export function useNotifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useWebSocket({
    channels: [
      WS_CHANNELS.NOTIFICATION.USER(user.organization_id, user.id),
      WS_CHANNELS.NOTIFICATION.BROADCAST(user.organization_id),
    ],

    onMessage: (channel, message) => {
      if (message.message_type === 'notification.created') {
        const notification = message.payload as Notification;

        // Add to list
        setNotifications(prev => [notification, ...prev]);
        setUnreadCount(prev => prev + 1);

        // Show toast
        toast(notification.title, {
          description: notification.body,
          action: notification.action_url ? {
            label: 'View',
            onClick: () => navigate(notification.action_url)
          } : undefined
        });
      }
    }
  });

  const markAsRead = async (notificationId: number) => {
    await api.patch(`/notifications/${notificationId}/read`);
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  return { notifications, unreadCount, markAsRead };
}
```

---

### 20.7 Reconnection Strategy

```typescript
// Centrifuge built-in reconnection with custom config
const centrifuge = new Centrifuge(wsUrl, {
  token,

  // Reconnection settings
  minReconnectDelay: 1000,      // Start with 1s
  maxReconnectDelay: 30000,     // Max 30s
  maxServerPingDelay: 10000,    // Server ping timeout

  // Token refresh
  getToken: async () => {
    const { token } = await api.get('/ws/token');
    return token;
  }
});
```

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  RECONNECTION FLOW                                                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  1. Disconnect detected                                                    ║
║     ↓                                                                      ║
║  2. Wait 1 second (minReconnectDelay)                                     ║
║     ↓                                                                      ║
║  3. Attempt reconnect                                                      ║
║     ↓ (fail)                                                               ║
║  4. Wait 2 seconds (exponential backoff)                                  ║
║     ↓                                                                      ║
║  5. Attempt reconnect                                                      ║
║     ↓ (fail)                                                               ║
║  6. Wait 4 seconds                                                         ║
║     ↓                                                                      ║
║  ... (continues until maxReconnectDelay = 30s)                            ║
║                                                                            ║
║  On token expiry:                                                          ║
║  → Automatically calls getToken() to refresh                              ║
║  → Reconnects with new token                                              ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 20.8 Channel Permissions

```python
# shared/realtime/permissions.py
from shared.constants.ws_channels import WSChannels

# Channel permission mapping
CHANNEL_PERMISSIONS = {
    "device:status": "core.devices.view",
    "device:command": "core.devices.manage",
    "pms:room:status": "pms.rooms.view",
    "pms:reservation": "pms.reservations.view",
    "pos:kitchen": "pos.orders.view",
    "dashboard:updates": "core.dashboard.view",
}

def can_subscribe(user: User, channel: str) -> bool:
    """Check if user can subscribe to channel"""

    # Extract org_id from channel
    parts = channel.split(":")
    channel_org = parts[0]

    # Must be same organization
    if channel_org != f"org_{user.organization_id}":
        return False

    # Personal notification channel
    if f":notification:user:{user.id}" in channel:
        return True

    # Broadcast channel - all org users
    if ":notification:broadcast" in channel:
        return True

    # Check permission for other channels
    channel_type = ":".join(parts[1:3])  # e.g., "device:status"

    required_permission = CHANNEL_PERMISSIONS.get(channel_type)
    if required_permission:
        return user.has_permission(required_permission)

    return False
```

---

### 20.9 Ringkasan Real-time Standard

| Aspect | Standard |
|--------|----------|
| **Server** | Centrifugo (self-hosted) |
| **Protocol** | WebSocket + SSE fallback |
| **Channel Format** | `{tenant}:{module}:{scope}:{id?}` |
| **Message Format** | Aligned with Event Schema (#18) |
| **Auth** | JWT token (12 hour expiry) |
| **Reconnection** | Exponential backoff (1s → 30s) |
| **Token Refresh** | Automatic via getToken() callback |
| **Permissions** | Channel-level based on RBAC |

---

## 21. Background Job (Celery) Standard

> Standard untuk async task processing menggunakan Celery

### 21.1 Overview

**Tech Stack:**
- **Task Queue**: Celery
- **Broker**: RabbitMQ
- **Result Backend**: Redis
- **Scheduler**: Celery Beat

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  CELERY ARCHITECTURE                                                       ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐         ║
║  │  Backend │     │ RabbitMQ │     │  Worker  │     │  Redis   │         ║
║  │ (FastAPI)│     │ (Broker) │     │ (Celery) │     │ (Result) │         ║
║  └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘         ║
║       │                │                │                │               ║
║       │ 1. Send task   │                │                │               ║
║       │───────────────▶│                │                │               ║
║       │                │ 2. Queue task  │                │               ║
║       │                │───────────────▶│                │               ║
║       │                │                │ 3. Execute     │               ║
║       │                │                │    task        │               ║
║       │                │                │                │               ║
║       │                │                │ 4. Store       │               ║
║       │                │                │    result      │               ║
║       │                │                │───────────────▶│               ║
║       │                │                │                │               ║
║       │ 5. Poll result (optional)       │                │               ║
║       │─────────────────────────────────────────────────▶│               ║
║                                                                            ║
║  ┌──────────┐                                                             ║
║  │  Celery  │ 6. Scheduled tasks (cron)                                  ║
║  │   Beat   │────────────────────────────▶ RabbitMQ ────▶ Worker         ║
║  └──────────┘                                                             ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 21.2 Task Naming Convention

**Format:** `{module}.tasks.{action}_{entity}`

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  TASK NAMING CONVENTION                                                    ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Pattern: {module}.tasks.{action}_{entity}                                ║
║                                                                            ║
║  {module}  = email, reports, files, sync, cleanup                         ║
║  {action}  = send, generate, process, sync, cleanup                       ║
║  {entity}  = welcome_email, daily_revenue, video, devices                 ║
║                                                                            ║
║  Examples:                                                                 ║
║  ─────────────────────────────────────────────────────────────────────    ║
║  email.tasks.send_welcome_email                                           ║
║  email.tasks.send_invoice_email                                           ║
║  email.tasks.send_password_reset                                          ║
║  reports.tasks.generate_daily_revenue                                     ║
║  reports.tasks.generate_monthly_summary                                   ║
║  reports.tasks.export_to_pdf                                              ║
║  files.tasks.process_image                                                ║
║  files.tasks.transcode_video                                              ║
║  files.tasks.cleanup_orphaned                                             ║
║  sync.tasks.sync_device_status                                            ║
║  sync.tasks.sync_inventory_levels                                         ║
║  notifications.tasks.send_push_notification                               ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 21.3 Task Structure

#### 21.3.1 Base Task Class

```python
# shared/tasks/base.py
from celery import Task
from shared.logging import get_logger
from shared.database import get_db_session
import contextvars

correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

class BaseTask(Task):
    """Base task with logging, retry, and error handling"""

    # Default settings
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True
    max_retries = 3
    soft_time_limit = 300  # 5 minutes
    time_limit = 360  # 6 minutes (hard limit)

    abstract = True

    def __init__(self):
        self.logger = get_logger(self.name)

    def before_start(self, task_id, args, kwargs):
        """Called before task starts"""
        correlation_id = kwargs.pop('correlation_id', None) or f"task-{task_id}"
        correlation_id_var.set(correlation_id)

        self.logger.info(
            f"Task started",
            task_id=task_id,
            correlation_id=correlation_id,
            args=str(args)[:200]  # Truncate for logging
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful completion"""
        self.logger.info(
            f"Task completed successfully",
            task_id=task_id,
            correlation_id=correlation_id_var.get()
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        self.logger.error(
            f"Task failed: {exc}",
            task_id=task_id,
            correlation_id=correlation_id_var.get(),
            exception=str(exc),
            traceback=str(einfo)
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        self.logger.warning(
            f"Task retrying: {exc}",
            task_id=task_id,
            correlation_id=correlation_id_var.get(),
            retry_count=self.request.retries
        )
```

#### 21.3.2 Task Implementation

```python
# tasks/email/tasks.py
from celery import shared_task
from shared.tasks.base import BaseTask
from shared.email import EmailService

@shared_task(
    bind=True,
    base=BaseTask,
    name="email.tasks.send_welcome_email",
    queue="default",
    max_retries=3
)
def send_welcome_email(self, user_id: int, tenant_id: str, correlation_id: str = None):
    """Send welcome email to new user"""

    try:
        # Get user
        user = await user_repo.get_by_id(user_id)
        if not user:
            self.logger.warning(f"User {user_id} not found, skipping email")
            return {"status": "skipped", "reason": "user_not_found"}

        # Send email
        email_service = EmailService(tenant_id)
        result = await email_service.send_template(
            to=user.email,
            template="welcome",
            context={
                "user_name": user.name,
                "organization": user.organization.name
            }
        )

        return {"status": "sent", "message_id": result.message_id}

    except EmailServiceError as e:
        # Retry on transient errors
        if e.is_transient:
            raise self.retry(exc=e, countdown=60)
        raise


@shared_task(
    bind=True,
    base=BaseTask,
    name="reports.tasks.generate_daily_revenue",
    queue="low",
    soft_time_limit=600,  # 10 minutes
    time_limit=660
)
def generate_daily_revenue(
    self,
    tenant_id: str,
    report_date: str,
    requested_by_id: int,
    correlation_id: str = None
):
    """Generate daily revenue report"""

    try:
        # Generate report
        report_service = ReportService(tenant_id)
        report = await report_service.generate_daily_revenue(
            date=report_date,
            requested_by_id=requested_by_id
        )

        # Store report file
        file_path = await storage.upload(
            f"{tenant_id}/reports/{report_date}/daily_revenue.pdf",
            report.pdf_bytes
        )

        # Notify user
        await notification_service.send(
            user_id=requested_by_id,
            title="Report Ready",
            body=f"Daily revenue report for {report_date} is ready",
            action_url=f"/reports/download/{report.id}"
        )

        return {"status": "completed", "file_path": file_path}

    except Exception as e:
        self.logger.error(f"Report generation failed: {e}")
        raise
```

---

### 21.4 Priority Queues

```python
# celery_config.py
from celery import Celery
from kombu import Queue

app = Celery('signage')

# Queue definitions
app.conf.task_queues = (
    # Critical: Payment, alerts - processed immediately
    Queue('critical', routing_key='critical.#'),

    # Default: Emails, notifications - normal priority
    Queue('default', routing_key='default.#'),

    # Low: Reports, cleanup - can wait
    Queue('low', routing_key='low.#'),

    # Scheduled: Beat tasks
    Queue('scheduled', routing_key='scheduled.#'),
)

# Default queue
app.conf.task_default_queue = 'default'

# Route tasks to queues
app.conf.task_routes = {
    # Critical tasks
    'payment.tasks.*': {'queue': 'critical'},
    'alerts.tasks.*': {'queue': 'critical'},

    # Default tasks
    'email.tasks.*': {'queue': 'default'},
    'notifications.tasks.*': {'queue': 'default'},
    'sync.tasks.*': {'queue': 'default'},

    # Low priority tasks
    'reports.tasks.*': {'queue': 'low'},
    'files.tasks.*': {'queue': 'low'},
    'cleanup.tasks.*': {'queue': 'low'},

    # Scheduled tasks
    'scheduled.tasks.*': {'queue': 'scheduled'},
}
```

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  QUEUE PRIORITY                                                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Queue        Workers    Concurrency    Use Cases                         ║
║  ──────────   ─────────  ───────────    ─────────────────────────────     ║
║  critical     2          4              Payment callbacks, alerts          ║
║  default      2          8              Emails, notifications, sync        ║
║  low          1          4              Reports, file processing           ║
║  scheduled    1          2              Cron jobs, periodic tasks          ║
║                                                                            ║
║  Worker startup:                                                           ║
║  celery -A app worker -Q critical -c 4 -n critical@%h                     ║
║  celery -A app worker -Q default -c 8 -n default@%h                       ║
║  celery -A app worker -Q low -c 4 -n low@%h                               ║
║  celery -A app beat -S django_celery_beat.schedulers.DatabaseScheduler    ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 21.5 Scheduling (Celery Beat)

#### 21.5.1 Static Schedules

```python
# celery_config.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Every minute
    'sync-device-status': {
        'task': 'sync.tasks.sync_device_status',
        'schedule': 60.0,  # Every 60 seconds
        'options': {'queue': 'scheduled'}
    },

    # Daily at 1 AM
    'cleanup-orphaned-files': {
        'task': 'cleanup.tasks.cleanup_orphaned_files',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'low'}
    },

    # Daily at 6 AM
    'generate-daily-reports': {
        'task': 'scheduled.tasks.trigger_daily_reports',
        'schedule': crontab(hour=6, minute=0),
        'options': {'queue': 'scheduled'}
    },

    # Weekly on Sunday at 2 AM
    'purge-deleted-files': {
        'task': 'cleanup.tasks.purge_deleted_files',
        'schedule': crontab(hour=2, minute=0, day_of_week='sunday'),
        'options': {'queue': 'low'}
    },

    # Monthly on 1st at 3 AM
    'generate-monthly-summary': {
        'task': 'scheduled.tasks.trigger_monthly_reports',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),
        'options': {'queue': 'scheduled'}
    },
}
```

#### 21.5.2 Per-Tenant Schedules

```python
# tasks/scheduled/tasks.py
@shared_task(
    bind=True,
    base=BaseTask,
    name="scheduled.tasks.trigger_daily_reports"
)
def trigger_daily_reports(self):
    """Trigger daily reports for all active tenants"""

    # Get all active organizations
    organizations = await org_repo.get_all_active()

    for org in organizations:
        # Check org settings for report preferences
        settings = await settings_repo.get_by_org(org.id)

        if settings.daily_report_enabled:
            # Queue report generation for this tenant
            generate_daily_revenue.apply_async(
                kwargs={
                    'tenant_id': str(org.id),
                    'report_date': (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'requested_by_id': settings.report_recipient_id,
                    'correlation_id': f"scheduled-daily-{org.id}"
                },
                queue='low'
            )

    return {"triggered_for": len(organizations)}
```

---

### 21.6 Task Invocation

```python
# From API endpoint
@router.post("/reports/daily")
async def request_daily_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user)
):
    """Request daily revenue report generation"""

    # Queue the task
    task = generate_daily_revenue.apply_async(
        kwargs={
            'tenant_id': str(current_user.organization_id),
            'report_date': request.date,
            'requested_by_id': current_user.id,
            'correlation_id': get_correlation_id()
        },
        queue='low'
    )

    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Report generation started. You will be notified when ready."
    }


# Check task status
@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a background task"""

    result = AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "error": str(result.result) if result.failed() else None
    }
```

---

### 21.7 Error Handling & Retry

```python
# Task with custom retry logic
@shared_task(
    bind=True,
    base=BaseTask,
    name="payment.tasks.process_callback",
    queue="critical",
    autoretry_for=(TransientError,),  # Only retry transient errors
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=5
)
def process_payment_callback(self, payment_id: int, callback_data: dict):
    """Process payment gateway callback"""

    try:
        payment = await payment_repo.get(payment_id)

        # Validate callback
        if not payment_gateway.verify_signature(callback_data):
            # Don't retry invalid signatures
            raise PermanentError("Invalid signature")

        # Process payment
        await payment_service.process_callback(payment, callback_data)

        return {"status": "processed"}

    except TransientError as e:
        # Transient errors will be auto-retried
        raise

    except PermanentError as e:
        # Log and don't retry
        self.logger.error(f"Permanent error: {e}")
        await payment_service.mark_failed(payment_id, str(e))
        return {"status": "failed", "error": str(e)}
```

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  RETRY STRATEGY                                                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Error Type          Retry?    Strategy                                   ║
║  ─────────────────   ─────     ─────────────────────────────────────      ║
║  Network timeout     Yes       Exponential backoff (1s, 2s, 4s, 8s...)   ║
║  Rate limited        Yes       Fixed delay (60s)                          ║
║  Service unavailable Yes       Exponential backoff                        ║
║  Invalid input       No        Fail immediately                           ║
║  Auth failure        No        Fail immediately                           ║
║  Business rule       No        Fail immediately                           ║
║                                                                            ║
║  Backoff formula: min(retry_backoff_max, 2^retry_count + jitter)         ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 21.8 Monitoring & Alerts

```python
# Docker compose for Flower (Celery monitoring)
# docker-compose.yml
services:
  flower:
    image: mher/flower
    command: celery flower --broker=amqp://rabbitmq:5672
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672
      - FLOWER_BASIC_AUTH=admin:password
```

```python
# Custom monitoring hooks
# shared/tasks/monitoring.py
from celery.signals import task_failure, task_success, task_retry

@task_failure.connect
def handle_task_failure(sender, task_id, exception, traceback, **kwargs):
    """Alert on task failure"""

    # Send alert for critical tasks
    if sender.queue == 'critical':
        alert_service.send_alert(
            level="critical",
            title=f"Critical task failed: {sender.name}",
            message=str(exception),
            context={
                "task_id": task_id,
                "task_name": sender.name,
                "traceback": str(traceback)
            }
        )

    # Log to monitoring
    metrics.increment('celery.task.failure', tags={
        'task': sender.name,
        'queue': sender.queue
    })


@task_success.connect
def handle_task_success(sender, result, **kwargs):
    """Track successful tasks"""

    metrics.increment('celery.task.success', tags={
        'task': sender.name,
        'queue': sender.queue
    })


@task_retry.connect
def handle_task_retry(sender, reason, **kwargs):
    """Track retries"""

    metrics.increment('celery.task.retry', tags={
        'task': sender.name,
        'queue': sender.queue
    })
```

---

### 21.9 Task Registry

```python
# shared/constants/tasks.py
class TaskNames:
    """Registry of all task names"""

    class EMAIL:
        SEND_WELCOME = "email.tasks.send_welcome_email"
        SEND_INVOICE = "email.tasks.send_invoice_email"
        SEND_PASSWORD_RESET = "email.tasks.send_password_reset"
        SEND_NOTIFICATION = "email.tasks.send_notification_email"

    class REPORTS:
        GENERATE_DAILY_REVENUE = "reports.tasks.generate_daily_revenue"
        GENERATE_MONTHLY_SUMMARY = "reports.tasks.generate_monthly_summary"
        EXPORT_TO_PDF = "reports.tasks.export_to_pdf"
        EXPORT_TO_EXCEL = "reports.tasks.export_to_excel"

    class FILES:
        PROCESS_IMAGE = "files.tasks.process_image"
        TRANSCODE_VIDEO = "files.tasks.transcode_video"
        CLEANUP_ORPHANED = "files.tasks.cleanup_orphaned"
        PURGE_DELETED = "files.tasks.purge_deleted"

    class SYNC:
        SYNC_DEVICE_STATUS = "sync.tasks.sync_device_status"
        SYNC_INVENTORY = "sync.tasks.sync_inventory_levels"

    class NOTIFICATIONS:
        SEND_PUSH = "notifications.tasks.send_push_notification"
        SEND_IN_APP = "notifications.tasks.send_in_app_notification"

    class PAYMENT:
        PROCESS_CALLBACK = "payment.tasks.process_callback"
        CHECK_PENDING = "payment.tasks.check_pending_payments"
```

---

### 21.10 Ringkasan Background Job Standard

| Aspect | Standard |
|--------|----------|
| **Framework** | Celery |
| **Broker** | RabbitMQ |
| **Result Backend** | Redis |
| **Task Naming** | `{module}.tasks.{action}_{entity}` |
| **Queues** | critical, default, low, scheduled |
| **Retry** | Exponential backoff, max 3-5 retries |
| **Timeout** | soft=5min, hard=6min (configurable) |
| **Scheduling** | Celery Beat with crontab |
| **Monitoring** | Flower + custom metrics |
| **Logging** | Correlation ID dari caller |

---

## 22. Search (Meilisearch) Standard

> Standard untuk full-text search menggunakan Meilisearch

### 22.1 Overview

**Tech Stack:**
- **Engine**: Meilisearch (self-hosted)
- **Protocol**: REST API
- **Features**: Typo-tolerance, faceted search, instant search

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  MEILISEARCH ARCHITECTURE                                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐         ║
║  │  Backend │     │Meilisearch│    │  Backend │     │  Celery  │         ║
║  │ (FastAPI)│     │ (Search) │     │  (CRUD)  │     │ (Reindex)│         ║
║  └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘         ║
║       │                │                │                │               ║
║       │ 1. Search      │                │                │               ║
║       │    request     │                │                │               ║
║       │───────────────▶│                │                │               ║
║       │                │                │                │               ║
║       │◀───────────────│                │                │               ║
║       │ 2. Search      │                │                │               ║
║       │    results     │                │                │               ║
║       │                │                │                │               ║
║       │                │                │ 3. Create/     │               ║
║       │                │                │    Update      │               ║
║       │                │◀───────────────│                │               ║
║       │                │ 4. Index       │                │               ║
║       │                │    document    │                │               ║
║       │                │                │                │               ║
║       │                │                │                │ 5. Bulk       ║
║       │                │◀───────────────────────────────│    reindex    ║
║       │                │                │                │               ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### 22.2 Index Naming Convention

**Format:** `{tenant_id}_{entity}`

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  INDEX NAMING CONVENTION                                                   ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Pattern: {tenant_id}_{entity}                                            ║
║                                                                            ║
║  {tenant_id}  = org_123 (organization_id)                                 ║
║  {entity}     = contents, devices, guests, products, reservations         ║
║                                                                            ║
║  Examples:                                                                 ║
║  ─────────────────────────────────────────────────────────────────────    ║
║  org_123_contents         → Content search for org 123                    ║
║  org_123_devices          → Device search for org 123                     ║
║  org_123_guests           → Guest search (PMS) for org 123                ║
║  org_123_products         → Product search (POS) for org 123              ║
║  org_123_reservations     → Reservation search for org 123                ║
║  org_123_employees        → Employee search (HRM) for org 123             ║
║  org_123_transactions     → Transaction search for org 123                ║
║                                                                            ║
║  Note: Each tenant has separate indexes for data isolation                ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

**Index Registry:**

```python
# shared/constants/search_indexes.py
class SearchIndexes:
    """Registry of all search indexes"""

    @staticmethod
    def CONTENTS(org_id: int) -> str:
        return f"org_{org_id}_contents"

    @staticmethod
    def DEVICES(org_id: int) -> str:
        return f"org_{org_id}_devices"

    @staticmethod
    def GUESTS(org_id: int) -> str:
        return f"org_{org_id}_guests"

    @staticmethod
    def PRODUCTS(org_id: int) -> str:
        return f"org_{org_id}_products"

    @staticmethod
    def RESERVATIONS(org_id: int) -> str:
        return f"org_{org_id}_reservations"

    @staticmethod
    def EMPLOYEES(org_id: int) -> str:
        return f"org_{org_id}_employees"

    @staticmethod
    def TRANSACTIONS(org_id: int) -> str:
        return f"org_{org_id}_transactions"
```

```typescript
// shared/constants/searchIndexes.ts
export const SearchIndexes = {
  CONTENTS: (orgId: number) => `org_${orgId}_contents`,
  DEVICES: (orgId: number) => `org_${orgId}_devices`,
  GUESTS: (orgId: number) => `org_${orgId}_guests`,
  PRODUCTS: (orgId: number) => `org_${orgId}_products`,
  RESERVATIONS: (orgId: number) => `org_${orgId}_reservations`,
  EMPLOYEES: (orgId: number) => `org_${orgId}_employees`,
  TRANSACTIONS: (orgId: number) => `org_${orgId}_transactions`,
} as const;
```

---

### 22.3 Document Schema

#### 22.3.1 Required Fields

Setiap searchable document HARUS memiliki field berikut:

```python
# Base document schema
class BaseSearchDocument(TypedDict):
    id: str                    # Unique identifier "{entity}_{id}"
    tenant_id: int             # Organization ID for filtering
    entity_type: str           # Type identifier (content, device, etc.)
    searchable_text: str       # Combined searchable text
    created_at: str            # ISO8601 timestamp
    updated_at: str            # ISO8601 timestamp
```

#### 22.3.2 Entity-Specific Schemas

```python
# Content document schema
class ContentSearchDocument(BaseSearchDocument):
    # Filterable fields
    content_type: str          # image, video, document
    status: str                # active, draft, archived
    folder_id: int | None

    # Sortable fields
    file_size: int
    duration: int | None       # For videos

    # Display fields
    name: str
    file_name: str
    thumbnail_url: str | None
    mime_type: str


# Guest document schema (PMS)
class GuestSearchDocument(BaseSearchDocument):
    # Filterable fields
    guest_type: str            # individual, company
    vip_status: str | None     # gold, platinum, etc.
    nationality: str | None

    # Sortable fields
    total_stays: int
    last_stay_at: str | None

    # Display fields
    full_name: str
    email: str | None
    phone: str | None
    company_name: str | None


# Product document schema (POS)
class ProductSearchDocument(BaseSearchDocument):
    # Filterable fields
    category_id: int
    outlet_ids: list[int]      # Available at outlets
    is_available: bool

    # Sortable fields
    price: float
    stock_quantity: int

    # Display fields
    name: str
    sku: str
    description: str | None
    image_url: str | None
```

---

### 22.4 Index Configuration

```python
# shared/search/config.py
from meilisearch import Client

# Index settings per entity
INDEX_SETTINGS = {
    "contents": {
        "searchableAttributes": [
            "name",
            "file_name",
            "searchable_text"
        ],
        "filterableAttributes": [
            "tenant_id",
            "content_type",
            "status",
            "folder_id"
        ],
        "sortableAttributes": [
            "name",
            "created_at",
            "updated_at",
            "file_size",
            "duration"
        ],
        "displayedAttributes": [
            "id",
            "name",
            "file_name",
            "content_type",
            "status",
            "thumbnail_url",
            "file_size",
            "duration",
            "created_at"
        ],
        "typoTolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8
            }
        },
        "pagination": {
            "maxTotalHits": 1000
        }
    },

    "guests": {
        "searchableAttributes": [
            "full_name",
            "email",
            "phone",
            "company_name",
            "searchable_text"
        ],
        "filterableAttributes": [
            "tenant_id",
            "guest_type",
            "vip_status",
            "nationality"
        ],
        "sortableAttributes": [
            "full_name",
            "created_at",
            "last_stay_at",
            "total_stays"
        ],
        "displayedAttributes": [
            "id",
            "full_name",
            "email",
            "phone",
            "guest_type",
            "vip_status",
            "total_stays",
            "last_stay_at"
        ]
    },

    "products": {
        "searchableAttributes": [
            "name",
            "sku",
            "description",
            "searchable_text"
        ],
        "filterableAttributes": [
            "tenant_id",
            "category_id",
            "outlet_ids",
            "is_available"
        ],
        "sortableAttributes": [
            "name",
            "price",
            "stock_quantity",
            "created_at"
        ],
        "displayedAttributes": [
            "id",
            "name",
            "sku",
            "price",
            "is_available",
            "image_url",
            "stock_quantity"
        ]
    }
}


def configure_index(client: Client, index_name: str, entity_type: str):
    """Configure index with predefined settings"""
    index = client.index(index_name)
    settings = INDEX_SETTINGS.get(entity_type, {})
    index.update_settings(settings)
```

---

### 22.5 Indexing Strategy

#### 22.5.1 Real-time Indexing (Create/Update/Delete)

```python
# shared/search/indexer.py
from meilisearch import Client
from shared.constants.search_indexes import SearchIndexes

class SearchIndexer:
    def __init__(self):
        self.client = Client(
            settings.MEILISEARCH_URL,
            settings.MEILISEARCH_API_KEY
        )

    async def index_document(
        self,
        tenant_id: int,
        entity_type: str,
        document: dict
    ) -> str:
        """Index a single document"""
        index_name = self._get_index_name(tenant_id, entity_type)
        index = self.client.index(index_name)

        # Ensure required fields
        document["tenant_id"] = tenant_id
        document["entity_type"] = entity_type
        document["updated_at"] = datetime.utcnow().isoformat()

        # Generate searchable_text if not provided
        if "searchable_text" not in document:
            document["searchable_text"] = self._generate_searchable_text(document)

        task = index.add_documents([document])
        return task.task_uid

    async def delete_document(
        self,
        tenant_id: int,
        entity_type: str,
        document_id: str
    ) -> str:
        """Delete a document from index"""
        index_name = self._get_index_name(tenant_id, entity_type)
        index = self.client.index(index_name)

        task = index.delete_document(document_id)
        return task.task_uid

    async def bulk_index(
        self,
        tenant_id: int,
        entity_type: str,
        documents: list[dict],
        batch_size: int = 1000
    ) -> list[str]:
        """Bulk index documents in batches"""
        index_name = self._get_index_name(tenant_id, entity_type)
        index = self.client.index(index_name)

        task_uids = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Add required fields to all documents
            for doc in batch:
                doc["tenant_id"] = tenant_id
                doc["entity_type"] = entity_type
                if "searchable_text" not in doc:
                    doc["searchable_text"] = self._generate_searchable_text(doc)

            task = index.add_documents(batch)
            task_uids.append(task.task_uid)

        return task_uids

    def _get_index_name(self, tenant_id: int, entity_type: str) -> str:
        return f"org_{tenant_id}_{entity_type}"

    def _generate_searchable_text(self, document: dict) -> str:
        """Generate searchable text from document fields"""
        searchable_fields = ["name", "description", "email", "phone", "sku"]
        parts = []
        for field in searchable_fields:
            if field in document and document[field]:
                parts.append(str(document[field]))
        return " ".join(parts)


# Usage in repository
class ContentRepository:
    def __init__(self):
        self.indexer = SearchIndexer()

    async def create(self, content: ContentCreate, user: User) -> Content:
        # Save to database
        db_content = await self._save_to_db(content, user)

        # Index for search
        await self.indexer.index_document(
            tenant_id=user.organization_id,
            entity_type="contents",
            document=self._to_search_document(db_content)
        )

        return db_content

    async def update(self, content_id: int, data: ContentUpdate, user: User) -> Content:
        # Update database
        db_content = await self._update_in_db(content_id, data)

        # Re-index
        await self.indexer.index_document(
            tenant_id=user.organization_id,
            entity_type="contents",
            document=self._to_search_document(db_content)
        )

        return db_content

    async def delete(self, content_id: int, user: User):
        # Delete from database
        await self._delete_from_db(content_id)

        # Remove from search index
        await self.indexer.delete_document(
            tenant_id=user.organization_id,
            entity_type="contents",
            document_id=f"content_{content_id}"
        )
```

#### 22.5.2 Bulk Reindexing (via Celery)

```python
# tasks/search/tasks.py
from celery import shared_task
from shared.tasks.base import BaseTask
from shared.search.indexer import SearchIndexer

@shared_task(
    bind=True,
    base=BaseTask,
    name="search.tasks.reindex_entity",
    queue="low",
    soft_time_limit=1800,  # 30 minutes
    time_limit=2000
)
def reindex_entity(
    self,
    tenant_id: int,
    entity_type: str,
    correlation_id: str = None
):
    """Full reindex of an entity for a tenant"""

    indexer = SearchIndexer()

    # Get all documents from database
    if entity_type == "contents":
        documents = content_repo.get_all_for_search(tenant_id)
    elif entity_type == "guests":
        documents = guest_repo.get_all_for_search(tenant_id)
    elif entity_type == "products":
        documents = product_repo.get_all_for_search(tenant_id)
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")

    self.logger.info(f"Reindexing {len(documents)} {entity_type} for tenant {tenant_id}")

    # Delete existing index
    index_name = f"org_{tenant_id}_{entity_type}"
    try:
        indexer.client.delete_index(index_name)
    except:
        pass  # Index might not exist

    # Create new index with settings
    indexer.client.create_index(index_name, {"primaryKey": "id"})
    configure_index(indexer.client, index_name, entity_type)

    # Bulk index
    task_uids = indexer.bulk_index(
        tenant_id=tenant_id,
        entity_type=entity_type,
        documents=documents,
        batch_size=500
    )

    return {
        "status": "completed",
        "indexed_count": len(documents),
        "task_uids": task_uids
    }


@shared_task(
    bind=True,
    base=BaseTask,
    name="search.tasks.reindex_all_tenants",
    queue="scheduled"
)
def reindex_all_tenants(self, entity_type: str):
    """Reindex entity for all tenants (scheduled task)"""

    organizations = org_repo.get_all_active()

    for org in organizations:
        reindex_entity.apply_async(
            kwargs={
                "tenant_id": org.id,
                "entity_type": entity_type,
                "correlation_id": f"scheduled-reindex-{org.id}"
            },
            queue="low"
        )

    return {"queued_for": len(organizations)}
```

---

### 22.6 Search API

#### 22.6.1 Backend Search Service

```python
# shared/search/service.py
from meilisearch import Client
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class SearchResult(BaseModel, Generic[T]):
    hits: list[T]
    total: int
    offset: int
    limit: int
    processing_time_ms: int
    query: str
    facets: dict | None = None


class SearchService:
    def __init__(self):
        self.client = Client(
            settings.MEILISEARCH_URL,
            settings.MEILISEARCH_API_KEY
        )

    async def search(
        self,
        tenant_id: int,
        entity_type: str,
        query: str,
        filters: dict | None = None,
        sort: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        facets: list[str] | None = None
    ) -> SearchResult:
        """Execute search query"""

        index_name = f"org_{tenant_id}_{entity_type}"
        index = self.client.index(index_name)

        # Build search params
        search_params = {
            "limit": min(limit, 100),  # Max 100 per request
            "offset": offset
        }

        # Build filter string
        filter_parts = [f"tenant_id = {tenant_id}"]  # Always filter by tenant
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_parts.append(f"{key} IN {value}")
                elif isinstance(value, bool):
                    filter_parts.append(f"{key} = {str(value).lower()}")
                else:
                    filter_parts.append(f"{key} = '{value}'")

        search_params["filter"] = " AND ".join(filter_parts)

        # Add sorting
        if sort:
            search_params["sort"] = sort

        # Add facets
        if facets:
            search_params["facets"] = facets

        # Execute search
        result = index.search(query, search_params)

        return SearchResult(
            hits=result["hits"],
            total=result["estimatedTotalHits"],
            offset=offset,
            limit=limit,
            processing_time_ms=result["processingTimeMs"],
            query=query,
            facets=result.get("facetDistribution")
        )


# Usage
search_service = SearchService()

results = await search_service.search(
    tenant_id=123,
    entity_type="contents",
    query="welcome video",
    filters={
        "content_type": "video",
        "status": "active"
    },
    sort=["created_at:desc"],
    limit=20,
    facets=["content_type", "status"]
)
```

#### 22.6.2 API Endpoint

```python
# services/search/routes.py
from fastapi import APIRouter, Depends, Query
from shared.search.service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/{entity_type}")
async def search(
    entity_type: str,
    q: str = Query(..., min_length=1, description="Search query"),
    filters: str | None = Query(None, description="JSON filters"),
    sort: str | None = Query(None, description="Sort field:direction"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    facets: str | None = Query(None, description="Comma-separated facet fields"),
    current_user: User = Depends(get_current_user)
):
    """
    Search endpoint

    - **entity_type**: contents, devices, guests, products, etc.
    - **q**: Search query (required)
    - **filters**: JSON object for filtering (e.g., {"status": "active"})
    - **sort**: Sort by field (e.g., "created_at:desc")
    - **facets**: Get facet counts (e.g., "content_type,status")
    """

    # Validate entity type
    allowed_entities = ["contents", "devices", "guests", "products", "reservations"]
    if entity_type not in allowed_entities:
        raise HTTPException(400, f"Invalid entity type. Allowed: {allowed_entities}")

    # Parse filters
    parsed_filters = None
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except:
            raise HTTPException(400, "Invalid filters JSON")

    # Parse sort
    parsed_sort = None
    if sort:
        parsed_sort = [sort]

    # Parse facets
    parsed_facets = None
    if facets:
        parsed_facets = facets.split(",")

    # Execute search
    results = await search_service.search(
        tenant_id=current_user.organization_id,
        entity_type=entity_type,
        query=q,
        filters=parsed_filters,
        sort=parsed_sort,
        limit=limit,
        offset=offset,
        facets=parsed_facets
    )

    return {
        "success": True,
        "data": {
            "hits": results.hits,
            "pagination": {
                "total": results.total,
                "limit": results.limit,
                "offset": results.offset,
                "has_more": results.offset + len(results.hits) < results.total
            },
            "facets": results.facets,
            "meta": {
                "query": results.query,
                "processing_time_ms": results.processing_time_ms
            }
        }
    }
```

---

### 22.7 Frontend Integration

#### 22.7.1 Search Hook

```typescript
// shared/hooks/useSearch.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface SearchParams {
  entityType: string;
  query: string;
  filters?: Record<string, unknown>;
  sort?: string;
  limit?: number;
  offset?: number;
  facets?: string[];
}

interface SearchResult<T> {
  hits: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
  facets?: Record<string, Record<string, number>>;
  meta: {
    query: string;
    processing_time_ms: number;
  };
}

export function useSearch<T>(params: SearchParams) {
  const { entityType, query, filters, sort, limit = 20, offset = 0, facets } = params;

  return useQuery({
    queryKey: ['search', entityType, query, filters, sort, limit, offset],
    queryFn: async (): Promise<SearchResult<T>> => {
      const response = await api.get(`/search/${entityType}`, {
        params: {
          q: query,
          filters: filters ? JSON.stringify(filters) : undefined,
          sort,
          limit,
          offset,
          facets: facets?.join(','),
        }
      });
      return response.data.data;
    },
    enabled: query.length > 0,
    staleTime: 30 * 1000, // 30 seconds
  });
}
```

#### 22.7.2 Search Component

```typescript
// shared/components/SearchInput.tsx
import { useState, useCallback } from 'react';
import { useDebounce } from '@/shared/hooks/useDebounce';
import { Input } from '@/shared/components/ui/input';
import { Search, X, Loader2 } from 'lucide-react';

interface SearchInputProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  isLoading?: boolean;
  debounceMs?: number;
}

export function SearchInput({
  placeholder = 'Search...',
  onSearch,
  isLoading = false,
  debounceMs = 300
}: SearchInputProps) {
  const [value, setValue] = useState('');
  const debouncedValue = useDebounce(value, debounceMs);

  // Trigger search when debounced value changes
  useEffect(() => {
    onSearch(debouncedValue);
  }, [debouncedValue, onSearch]);

  const handleClear = useCallback(() => {
    setValue('');
    onSearch('');
  }, [onSearch]);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="pl-10 pr-10"
      />
      {isLoading ? (
        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin" />
      ) : value && (
        <button
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2"
        >
          <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
        </button>
      )}
    </div>
  );
}
```

#### 22.7.3 Usage Example

```typescript
// features/contents/pages/ContentListPage.tsx
import { useState } from 'react';
import { useSearch } from '@/shared/hooks/useSearch';
import { SearchInput } from '@/shared/components/SearchInput';
import { ContentCard } from '../components/ContentCard';

interface ContentSearchResult {
  id: string;
  name: string;
  content_type: string;
  thumbnail_url: string;
  created_at: string;
}

export function ContentListPage() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, unknown>>({
    status: 'active'
  });

  const { data, isLoading, error } = useSearch<ContentSearchResult>({
    entityType: 'contents',
    query,
    filters,
    sort: 'created_at:desc',
    facets: ['content_type', 'status']
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <SearchInput
          placeholder="Search contents..."
          onSearch={setQuery}
          isLoading={isLoading}
        />

        {/* Facet filters */}
        {data?.facets?.content_type && (
          <FacetFilter
            label="Type"
            facet={data.facets.content_type}
            selected={filters.content_type}
            onChange={(value) => setFilters(prev => ({ ...prev, content_type: value }))}
          />
        )}
      </div>

      {/* Results */}
      {isLoading && <LoadingSpinner />}

      {error && <ErrorMessage error={error} />}

      {data && (
        <>
          <p className="text-sm text-muted-foreground">
            {data.pagination.total} results ({data.meta.processing_time_ms}ms)
          </p>

          <div className="grid grid-cols-4 gap-4">
            {data.hits.map(content => (
              <ContentCard key={content.id} content={content} />
            ))}
          </div>

          {data.pagination.has_more && (
            <LoadMoreButton onClick={() => {/* Load next page */}} />
          )}
        </>
      )}
    </div>
  );
}
```

---

### 22.8 Multi-Tenancy

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  MULTI-TENANCY STRATEGY: Index per Tenant                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Approach: Separate index per tenant per entity                           ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  Tenant 123                                                          │  ║
║  │  ├── org_123_contents                                               │  ║
║  │  ├── org_123_devices                                                │  ║
║  │  ├── org_123_guests                                                 │  ║
║  │  └── org_123_products                                               │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │  Tenant 456                                                          │  ║
║  │  ├── org_456_contents                                               │  ║
║  │  ├── org_456_devices                                                │  ║
║  │  ├── org_456_guests                                                 │  ║
║  │  └── org_456_products                                               │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  Benefits:                                                                 ║
║  ✓ Complete data isolation                                                ║
║  ✓ Per-tenant index settings                                              ║
║  ✓ Easy tenant deletion (just drop indexes)                              ║
║  ✓ No filter overhead (no tenant_id filter in every query)               ║
║                                                                            ║
║  Trade-offs:                                                               ║
║  ✗ More indexes to manage                                                 ║
║  ✗ Index creation on new tenant signup                                   ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

```python
# Tenant lifecycle hooks
async def on_tenant_created(tenant_id: int):
    """Create search indexes for new tenant"""
    client = Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)

    for entity_type in ["contents", "devices", "guests", "products"]:
        index_name = f"org_{tenant_id}_{entity_type}"
        client.create_index(index_name, {"primaryKey": "id"})
        configure_index(client, index_name, entity_type)


async def on_tenant_deleted(tenant_id: int):
    """Delete all search indexes for tenant"""
    client = Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)

    for entity_type in ["contents", "devices", "guests", "products"]:
        index_name = f"org_{tenant_id}_{entity_type}"
        try:
            client.delete_index(index_name)
        except:
            pass  # Index might not exist
```

---

### 22.9 Ringkasan Search Standard

| Aspect | Standard |
|--------|----------|
| **Engine** | Meilisearch (self-hosted) |
| **Index Format** | `{tenant_id}_{entity}` |
| **Multi-tenancy** | Separate index per tenant |
| **Indexing** | Real-time on CRUD + bulk via Celery |
| **Reindex Schedule** | Weekly (configurable per entity) |
| **Required Fields** | id, tenant_id, entity_type, searchable_text |
| **API Pattern** | `GET /search/{entity}?q=...&filters=...` |
| **Max Results** | 100 per request, 1000 total |
| **Typo Tolerance** | Enabled (1 typo for 4+ chars, 2 for 8+) |

---

*Last Updated: 2025-12-09*
