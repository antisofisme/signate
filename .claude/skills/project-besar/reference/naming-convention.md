---
description: Naming conventions for PROJECT_BESAR
---

# Naming Convention Reference

## Python (Backend)
| Type | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `user_count` |
| Functions | snake_case | `get_user_by_id()` |
| Classes | PascalCase | `UserService` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Files | snake_case | `user_service.py` |

## TypeScript (Frontend)
| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `userData` |
| Functions | camelCase | `getUserById()` |
| Components | PascalCase | `UserCard` |
| Interfaces | PascalCase | `UserData` |
| Types | PascalCase | `UserStatus` |
| Files (component) | PascalCase | `UserCard.tsx` |
| Files (other) | camelCase | `userService.ts` |

## Database
| Type | Convention | Example |
|------|------------|---------|
| Tables | snake_case, plural | `users`, `room_types` |
| Columns | snake_case | `created_at` |
| Indexes | `ix_{table}_{column}` | `ix_users_email` |
| Foreign Keys | `fk_{table}_{ref}` | `fk_orders_user_id` |

## API
| Type | Convention | Example |
|------|------------|---------|
| Endpoints | kebab-case | `/api/v1/room-types` |
| Query params | snake_case | `?page_size=20` |
| Request body | snake_case | `{ "room_type": "..." }` |

## Events
| Type | Convention | Example |
|------|------------|---------|
| Event type | `{module}.{entity}.{action}` | `pms.reservation.created` |
| Queue name | `{module}.{entity}` | `pms.reservation` |

## Permissions
Format: `{module}.{resource}.{action}`
Examples:
- `pms.reservation.create`
- `pms.reservation.view`
- `pos.order.delete`
