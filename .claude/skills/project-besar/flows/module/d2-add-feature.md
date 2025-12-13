---
description: Add feature to existing module for PROJECT_BESAR
---

# Flow D2: Add Feature to Module

## Pre-requisites
- [ ] Module exists and operational
- [ ] Feature requirements clear
- [ ] Integration points identified

## Feature Type Decision

| Feature Type | Use Flow |
|--------------|----------|
| CRUD operations | C1 |
| Reports/exports | C2 |
| Search | C3 |
| Notifications | C4 |
| File uploads | C5 |
| Complex workflow | Combine flows |

## Steps

1. **Analyze feature type** (see table above)
2. **Identify required flows**
3. **Execute flows in order**:
   - Database first (A1)
   - Service logic (A3)
   - API endpoints (A2)
   - Frontend components (B1-B5)
4. **Integrate with module**
   - Add routes
   - Add navigation
   - Register permissions
5. **Test and document**

## Complex Feature Example (Reservation)
```
1. A1 - Database models
2. A3 - Business logic
3. A2 - API endpoints
4. A5 - Events (reservation.created)
5. B3 - Reservation form
6. B4 - Reservations table
7. B2 - List/Detail pages
8. C4 - Confirmation notifications
```

## Checklist Before Complete
- [ ] Feature integrated with module router
- [ ] Navigation added
- [ ] Permissions registered
- [ ] Tests written
- [ ] Documentation updated
