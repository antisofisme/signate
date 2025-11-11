# Phase 1 Day 2: Architecture Diagram

## Clean Architecture - RBAC and Session Services

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                          │
│                            (main.py)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
┌───────────────────▼────────────┐  ┌──────────▼──────────────────────┐
│     RBAC Service                │  │    Session Service              │
│  /services/rbac/                │  │  /services/session/             │
└─────────────────────────────────┘  └─────────────────────────────────┘
         │                                      │
         │                                      │
    ┌────▼─────┐                           ┌───▼─────┐
    │  routes  │                           │  routes │
    │  .py     │                           │  .py    │
    └────┬─────┘                           └───┬─────┘
         │                                     │
    ┌────▼─────┐                          ┌───▼─────┐
    │  DTOs    │                          │  DTOs   │
    │  .py     │                          │  .py    │
    └────┬─────┘                          └───┬─────┘
         │                                     │
    ┌────▼──────────┐                    ┌────▼──────────┐
    │  Use Cases    │                    │  Use Cases    │
    │  /use_cases/  │                    │  /use_cases/  │
    │               │                    │               │
    │ - check_perm  │                    │ - create      │
    │ - get_roles   │                    │ - verify      │
    │ - create      │                    │ - revoke      │
    │ - update      │                    │ - get         │
    │ - delete      │                    │               │
    │ - manage_perm │                    │               │
    └────┬──────────┘                    └────┬──────────┘
         │                                     │
    ┌────▼───────────┐                   ┌────▼───────────┐
    │  Repositories  │                   │  Repositories  │
    │  /repositories/│                   │  /repositories/│
    │                │                   │                │
    │ - role_repo.py │                   │ - session_repo │
    └────┬───────────┘                   └────┬───────────┘
         │                                     │
    ┌────▼─────┐                          ┌───▼─────┐
    │  Models  │                          │  Models │
    │          │                          │         │
    │  Role    │                          │  Session│
    └────┬─────┘                          └───┬─────┘
         │                                     │
         └─────────────┬───────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │  PostgreSQL Database      │
         │                           │
         │  - roles table            │
         │  - user_sessions table    │
         └───────────────────────────┘
```

## Request Flow Examples

### RBAC: Create Custom Role

```
Client Request
    │
    ▼
POST /api/v1/roles
    │
    ▼
rbac_router.create_role()
    │
    ├─► Authenticate (require_manager)
    ├─► Validate DTO (RoleCreateRequest)
    │
    ▼
CreateRoleUseCase.execute()
    │
    ├─► Validate name
    ├─► Check conflicts
    │
    ▼
RoleRepository.create()
    │
    ▼
Database INSERT
    │
    ▼
Return RoleResponse
```

### Session: Logout from All Devices

```
Client Request
    │
    ▼
POST /api/v1/sessions/revoke-all
    │
    ▼
session_router.revoke_all_sessions()
    │
    ├─► Authenticate (get_current_user)
    │
    ▼
RevokeSessionUseCase.revoke_all_user_sessions()
    │
    ▼
SessionRepository.revoke_all_user_sessions()
    │
    ├─► Find all active sessions
    ├─► Set revoked_at = now()
    │
    ▼
Database UPDATE (bulk)
    │
    ▼
Return SessionRevokeResponse
{
  "success": true,
  "sessions_revoked": 3,
  "message": "Logged out from 3 device(s)"
}
```

## Authorization Hierarchy

```
┌────────────────────────────────────────────┐
│          SUPER_ADMIN (Level 4)             │
│  ✓ All permissions                         │
│  ✓ Create system roles                     │
│  ✓ Access all organizations                │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│            ADMIN (Level 3)                 │
│  ✓ Most permissions                        │
│  ✓ Create custom roles                     │
│  ✓ Access all organizations                │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│           MANAGER (Level 2)                │
│  ✓ Manage organization resources           │
│  ✓ Create org roles                        │
│  ✓ Own organization only                   │
└────────────────┬───────────────────────────┘
                 │
┌────────────────▼───────────────────────────┐
│            VIEWER (Level 1)                │
│  ✓ Read-only access                        │
│  ✓ Own organization only                   │
└────────────────────────────────────────────┘
```

## Session Security Flow

```
┌──────────────┐
│ User Login   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ LoginUseCase.execute()   │
│ - Verify credentials     │
│ - Generate JWT token     │
└──────┬───────────────────┘
       │
       ▼
┌────────────────────────────────┐
│ SessionRepository.create()     │
│ - Hash JWT (SHA256)            │
│ - Store: user, org, IP, device │
│ - Set expiry                   │
└──────┬─────────────────────────┘
       │
       ▼
┌───────────────────┐
│ Database INSERT   │
│ user_sessions     │
└──────┬────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Return to client:           │
│ - JWT token (unhashed)      │
│ - User info                 │
│ - Organizations             │
└─────────────────────────────┘

Later requests:
┌──────────────────┐
│ API Request      │
│ + JWT token      │
└──────┬───────────┘
       │
       ▼
┌───────────────────────────┐
│ get_current_user()        │
│ - Decode JWT              │
│ - Verify signature        │
└──────┬────────────────────┘
       │
       ▼
┌────────────────────────────┐
│ SessionRepo.verify()       │
│ - Hash token (SHA256)      │
│ - Find in DB               │
│ - Check: not revoked       │
│ - Check: not expired       │
│ - Update last_activity     │
└──────┬─────────────────────┘
       │
       ▼
┌──────────────────┐
│ Process Request  │
└──────────────────┘
```

## Database Schema

### roles table
```sql
┌──────────────────────────────────────────┐
│ roles                                    │
├──────────────────────────────────────────┤
│ id                 SERIAL PK             │
│ name               VARCHAR(50) NOT NULL  │
│ description        VARCHAR(200)          │
│ organization_id    INT FK (nullable)     │
│ is_system_role     BOOLEAN NOT NULL      │
│ permissions        JSONB NOT NULL        │
│ created_at         TIMESTAMP             │
│ updated_at         TIMESTAMP             │
└──────────────────────────────────────────┘

Example permissions JSONB:
{
  "content": ["read", "write", "delete"],
  "devices": ["read", "write"],
  "playlists": ["read"]
}
```

### user_sessions table
```sql
┌──────────────────────────────────────────┐
│ user_sessions                            │
├──────────────────────────────────────────┤
│ id                 SERIAL PK             │
│ user_id            INT FK NOT NULL       │
│ organization_id    INT FK NOT NULL       │
│ session_token      VARCHAR(64) UNIQUE    │  ← SHA256 hash
│ refresh_token      VARCHAR(64) UNIQUE    │  ← SHA256 hash
│ ip_address         VARCHAR(45)           │
│ user_agent         VARCHAR(500)          │
│ device_info        JSONB                 │
│ session_type       VARCHAR(20)           │  ← web/api/mobile/device
│ created_at         TIMESTAMP             │
│ last_activity      TIMESTAMP             │
│ expires_at         TIMESTAMP             │
│ revoked_at         TIMESTAMP (nullable)  │
└──────────────────────────────────────────┘

Example device_info JSONB:
{
  "browser": "Chrome",
  "os": "Windows 10",
  "device_type": "desktop"
}
```

## API Endpoints Summary

### RBAC Endpoints (10)
```
GET    /api/v1/roles                          List roles
GET    /api/v1/roles/system                   System roles
GET    /api/v1/roles/{id}                     Get role
POST   /api/v1/roles                          Create role
PUT    /api/v1/roles/{id}                     Update role
DELETE /api/v1/roles/{id}                     Delete role
POST   /api/v1/roles/{id}/permissions/check   Check permission
GET    /api/v1/roles/{id}/permissions         Get permissions
POST   /api/v1/roles/{id}/permissions         Add permission
DELETE /api/v1/roles/{id}/permissions         Remove permission
```

### Session Endpoints (9)
```
GET    /api/v1/sessions                       My sessions
GET    /api/v1/sessions/active                My active sessions
GET    /api/v1/sessions/stats                 My stats
DELETE /api/v1/sessions/{id}                  Logout device
POST   /api/v1/sessions/revoke-all            Logout all
GET    /api/v1/sessions/user/{id}             Admin: user sessions
GET    /api/v1/sessions/ip/{ip}               Admin: by IP
DELETE /api/v1/sessions/admin/{id}            Admin: force logout
POST   /api/v1/sessions/admin/user/{id}/...   Admin: force logout all
```

---

## Key Design Decisions

1. **SHA256 Token Hashing**: JWT tokens are hashed before storage for security
2. **Organization Scoping**: Roles can be system-wide or organization-specific
3. **Permission JSONB**: Flexible permission structure stored as JSON
4. **Session Types**: Support for web, api, mobile, device sessions
5. **Soft Revocation**: Sessions marked as revoked, not deleted (audit trail)
6. **Last Activity Tracking**: Session activity updated on each request
7. **Admin Override**: Admins can manage any user's sessions (security)
8. **IP Tracking**: Sessions record IP for security monitoring
