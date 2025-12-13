---
description: Create real-time feature for PROJECT_BESAR
---

# Flow B5: Create Real-time Feature

## Pre-requisites
- [ ] Real-time requirement defined
- [ ] Channel/event identified
- [ ] Centrifugo configured

## Step 1: Create Subscription Hook
Location: `modules/{module}/frontend/src/hooks/use{Entity}Subscription.ts`

```typescript
import { useEffect, useCallback } from 'react';
import { useCentrifuge } from '@/providers/CentrifugeProvider';
import { useQueryClient } from '@tanstack/react-query';

export const use{Entity}Subscription = (entityId: string) => {
  const centrifuge = useCentrifuge();
  const queryClient = useQueryClient();

  const handleUpdate = useCallback((data: any) => {
    // Invalidate relevant queries
    queryClient.invalidateQueries({ queryKey: ['{entities}', entityId] });

    // Or update cache directly
    queryClient.setQueryData(['{entities}', entityId], (old: any) => ({
      ...old,
      ...data,
    }));
  }, [entityId, queryClient]);

  useEffect(() => {
    const channel = `{entity}:${entityId}`;
    const subscription = centrifuge.subscribe(channel, handleUpdate);

    return () => {
      subscription.unsubscribe();
    };
  }, [centrifuge, entityId, handleUpdate]);
};
```

## Step 2: Create Notification Hook
```typescript
export const use{Entity}Notifications = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useCentrifugeSubscription('notifications:{userId}', (data) => {
    setNotifications(prev => [data, ...prev]);
    toast.info(data.message);
  });

  return { notifications };
};
```

## Step 3: Use in Component
```typescript
export const {Entity}Detail: FC<{ id: string }> = ({ id }) => {
  const { data } = use{Entity}Query(id);

  // Subscribe to real-time updates
  use{Entity}Subscription(id);

  return <div>{/* Render data - auto-updates on changes */}</div>;
};
```

## Step 4: Handle Connection Status
```typescript
const { connectionStatus } = useCentrifuge();

{connectionStatus === 'disconnected' && (
  <Banner type="warning">
    Real-time updates unavailable. Reconnecting...
  </Banner>
)}
```

## Checklist Before Complete
- [ ] Subscription cleanup on unmount
- [ ] Cache invalidation/update works
- [ ] Connection status handled
- [ ] Error handling
- [ ] Reconnection logic
