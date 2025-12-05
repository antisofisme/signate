# Microservices-Ready Architecture Plan

> **Status**: Planning Document
> **Created**: 2025-12-05
> **Last Updated**: 2025-12-05
> **Author**: Development Team

---

## Executive Summary

Dokumen ini menjelaskan rencana refactoring backend dari **tightly-coupled monolith** menjadi **loosely-coupled monolith** yang siap untuk di-scale ke microservices kapan saja diperlukan.

**Key Principle**: Refactoring ini TIDAK mengharuskan deployment sebagai microservices. Sistem tetap bisa berjalan sebagai monolith dengan kode yang lebih terstruktur.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Target Architecture](#2-target-architecture)
3. [Implementation Phases](#3-implementation-phases)
4. [Interface Definitions](#4-interface-definitions)
5. [Event Bus Design](#5-event-bus-design)
6. [Service Boundaries](#6-service-boundaries)
7. [Migration Strategy](#7-migration-strategy)
8. [Risk Assessment](#8-risk-assessment)
9. [Timeline Estimate](#9-timeline-estimate)
10. [Checklist](#10-checklist)

---

## 1. Current Architecture Analysis

### 1.1 Directory Structure
```
backend-python/
├── services/
│   ├── analytics/      # Playback analytics
│   ├── audit/          # Audit logging ⚠️ imports user, organization
│   ├── auth/           # Authentication & authorization
│   ├── content/        # Content management
│   ├── dashboard/      # Dashboard data ⚠️ imports user, device, content
│   ├── device/         # Device management
│   ├── menu/           # Menu management
│   ├── organization/   # Organization management
│   ├── playlist/       # Playlist management
│   ├── pms/            # Property Management System ⚠️ imports device
│   ├── rbac/           # Role-based access control
│   ├── schedule/       # Schedule management
│   ├── session/        # Session management
│   ├── tag/            # Tag management ⚠️ imports device, content
│   ├── template/       # Template management
│   ├── translation/    # i18n translations
│   ├── user/           # User management
│   └── widget/         # Widget management
└── shared/
    ├── auth.py
    ├── cache.py
    ├── database.py
    ├── errors.py
    └── ...
```

### 1.2 Cross-Service Dependencies (Problems)

| Service | Imports From | Type | Priority |
|---------|--------------|------|----------|
| `audit` | user, organization | Repository | HIGH |
| `tag` | device, content | Models | HIGH |
| `pms` | device | Repository | MEDIUM |
| `dashboard` | user, device, content, playlist | Repository | MEDIUM |
| `content` | tag, playlist | Repository | MEDIUM |
| `device` | playlist, content | Repository | LOW |
| `session` | auth (user model) | Models | LOW |

### 1.3 Current Communication Pattern

```
┌─────────────────────────────────────────────────────────┐
│                   CURRENT: Direct Import                 │
│                                                         │
│  ┌─────────┐      direct import      ┌─────────┐       │
│  │ Audit   │ ──────────────────────► │  User   │       │
│  │ Service │                         │  Repo   │       │
│  └─────────┘                         └─────────┘       │
│       │                                                 │
│       │ direct import                                   │
│       ▼                                                 │
│  ┌─────────────┐                                       │
│  │Organization │                                       │
│  │    Repo     │                                       │
│  └─────────────┘                                       │
│                                                         │
│  Problem: Tight coupling, cannot split to microservice  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Target Architecture

### 2.1 Loosely-Coupled Monolith

```
┌─────────────────────────────────────────────────────────┐
│              TARGET: Interface + Event Bus               │
│                                                         │
│  ┌─────────┐      IUserService       ┌─────────┐       │
│  │ Audit   │ ◄──────────────────────►│  User   │       │
│  │ Service │      (interface)        │ Adapter │       │
│  └────┬────┘                         └─────────┘       │
│       │                                                 │
│       │ publish(AuditLogCreated)                       │
│       ▼                                                 │
│  ┌─────────────┐                                       │
│  │  Event Bus  │ ←── In-memory (monolith)              │
│  │  (local)    │     or Redis (distributed)            │
│  └─────────────┘                                       │
│                                                         │
│  Benefit: Can deploy as monolith OR microservices      │
└─────────────────────────────────────────────────────────┘
```

### 2.2 New Directory Structure

```
backend-python/
├── services/
│   └── [same as before]
├── shared/
│   ├── interfaces/           # NEW: Service interfaces
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── device_service.py
│   │   ├── content_service.py
│   │   ├── organization_service.py
│   │   └── ...
│   ├── events/               # NEW: Domain events
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_events.py
│   │   ├── device_events.py
│   │   ├── content_events.py
│   │   └── ...
│   ├── adapters/             # NEW: Interface implementations
│   │   ├── __init__.py
│   │   ├── user_adapter.py
│   │   ├── device_adapter.py
│   │   └── ...
│   ├── event_bus/            # NEW: Event bus
│   │   ├── __init__.py
│   │   ├── local_bus.py      # For monolith
│   │   ├── redis_bus.py      # For distributed
│   │   └── bus.py            # Factory
│   └── [existing files]
└── config/
    └── service_config.py     # NEW: Service configuration
```

---

## 3. Implementation Phases

### Phase 1: Infrastructure Setup (Week 1-2)

**Goal**: Create shared infrastructure without changing existing code.

```
Tasks:
├── [ ] Create shared/interfaces/ directory
├── [ ] Create shared/events/ directory
├── [ ] Create shared/adapters/ directory
├── [ ] Create shared/event_bus/ directory
├── [ ] Implement LocalEventBus (in-memory)
├── [ ] Create base interface (Protocol)
├── [ ] Create base event class
├── [ ] Add configuration for bus mode
└── [ ] Write unit tests for event bus
```

**Files to Create**:
- `shared/interfaces/__init__.py`
- `shared/interfaces/base.py`
- `shared/events/__init__.py`
- `shared/events/base.py`
- `shared/event_bus/__init__.py`
- `shared/event_bus/local_bus.py`
- `shared/event_bus/bus.py`

### Phase 2: Audit Service Refactoring (Week 3)

**Goal**: Refactor audit service as pilot project.

```
Tasks:
├── [ ] Create IUserService interface
├── [ ] Create IOrganizationService interface
├── [ ] Create UserServiceAdapter
├── [ ] Create OrganizationServiceAdapter
├── [ ] Update audit routes to use interfaces
├── [ ] Create AuditLogCreated event
├── [ ] Test backward compatibility
└── [ ] Deploy and monitor
```

**Before**:
```python
# services/audit/routes.py
from services.user.repositories.user_repo import UserRepository
from services.organization.repositories.organization_repo import OrganizationRepository
```

**After**:
```python
# services/audit/routes.py
from shared.interfaces import IUserService, IOrganizationService
from shared.adapters import get_user_service, get_organization_service
```

### Phase 3: Tag Service Refactoring (Week 4)

**Goal**: Refactor tag service (more complex cross-dependencies).

```
Tasks:
├── [ ] Create IDeviceService interface
├── [ ] Create IContentService interface
├── [ ] Create DeviceServiceAdapter
├── [ ] Create ContentServiceAdapter
├── [ ] Update tag repository to use interfaces
├── [ ] Create TagCreated, TagDeleted events
├── [ ] Test backward compatibility
└── [ ] Deploy and monitor
```

### Phase 4: Dashboard & PMS Service (Week 5-6)

**Goal**: Refactor dashboard and PMS services.

```
Tasks:
├── [ ] Update dashboard to use all interfaces
├── [ ] Update PMS to use device interface
├── [ ] Create dashboard-specific events
├── [ ] Create PMS sync events
├── [ ] Test all integrations
└── [ ] Deploy and monitor
```

### Phase 5: Remaining Services (Week 7-10)

**Goal**: Refactor remaining services incrementally.

```
Services to refactor:
├── [ ] content service
├── [ ] device service
├── [ ] playlist service
├── [ ] schedule service
├── [ ] menu service
└── [ ] session service
```

### Phase 6: Event-Driven Features (Week 11-12)

**Goal**: Add event subscribers for cross-cutting concerns.

```
Tasks:
├── [ ] Cache invalidation via events
├── [ ] Audit logging via events
├── [ ] WebSocket notifications via events
├── [ ] Analytics tracking via events
└── [ ] Documentation update
```

---

## 4. Interface Definitions

### 4.1 Base Interface

```python
# shared/interfaces/base.py
from typing import Protocol, TypeVar, Generic, Optional, List
from datetime import datetime

T = TypeVar('T')

class IRepository(Protocol[T]):
    """Base repository interface"""
    def get_by_id(self, id: int) -> Optional[T]: ...
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]: ...
    def create(self, entity: T) -> T: ...
    def update(self, id: int, entity: T) -> Optional[T]: ...
    def delete(self, id: int) -> bool: ...
```

### 4.2 User Service Interface

```python
# shared/interfaces/user_service.py
from typing import Protocol, Optional, List
from dataclasses import dataclass

@dataclass
class UserDTO:
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    organization_id: Optional[int]
    is_active: bool

class IUserService(Protocol):
    """User service interface"""

    def get_user(self, user_id: int) -> Optional[UserDTO]:
        """Get user by ID"""
        ...

    def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        """Get user by username"""
        ...

    def get_users_by_organization(self, org_id: int) -> List[UserDTO]:
        """Get all users in organization"""
        ...

    def is_user_active(self, user_id: int) -> bool:
        """Check if user is active"""
        ...
```

### 4.3 Device Service Interface

```python
# shared/interfaces/device_service.py
from typing import Protocol, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DeviceDTO:
    id: int
    device_name: str
    device_type: str
    organization_id: int
    status: str
    last_seen_at: Optional[datetime]
    ip_address: Optional[str]

class IDeviceService(Protocol):
    """Device service interface"""

    def get_device(self, device_id: int) -> Optional[DeviceDTO]:
        """Get device by ID"""
        ...

    def get_devices_by_organization(self, org_id: int) -> List[DeviceDTO]:
        """Get all devices in organization"""
        ...

    def is_device_online(self, device_id: int) -> bool:
        """Check if device is online (last_seen < 5 min)"""
        ...

    def get_device_count(self, org_id: int) -> int:
        """Get total device count for organization"""
        ...
```

### 4.4 Content Service Interface

```python
# shared/interfaces/content_service.py
from typing import Protocol, Optional, List
from dataclasses import dataclass

@dataclass
class ContentDTO:
    id: int
    name: str
    content_type: str
    file_path: str
    organization_id: int
    duration: Optional[int]
    is_active: bool

class IContentService(Protocol):
    """Content service interface"""

    def get_content(self, content_id: int) -> Optional[ContentDTO]:
        """Get content by ID"""
        ...

    def get_contents_by_organization(self, org_id: int) -> List[ContentDTO]:
        """Get all contents in organization"""
        ...

    def get_content_count(self, org_id: int) -> int:
        """Get total content count for organization"""
        ...
```

### 4.5 Organization Service Interface

```python
# shared/interfaces/organization_service.py
from typing import Protocol, Optional, List
from dataclasses import dataclass

@dataclass
class OrganizationDTO:
    id: int
    name: str
    slug: str
    is_active: bool
    max_devices: int
    max_storage_mb: int

class IOrganizationService(Protocol):
    """Organization service interface"""

    def get_organization(self, org_id: int) -> Optional[OrganizationDTO]:
        """Get organization by ID"""
        ...

    def get_organization_by_slug(self, slug: str) -> Optional[OrganizationDTO]:
        """Get organization by slug"""
        ...

    def is_within_quota(self, org_id: int, resource: str) -> bool:
        """Check if organization is within quota"""
        ...
```

---

## 5. Event Bus Design

### 5.1 Base Event Class

```python
# shared/events/base.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class DomainEvent:
    """Base class for all domain events"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None

    @property
    def event_type(self) -> str:
        return self.__class__.__name__
```

### 5.2 Domain Events

```python
# shared/events/user_events.py
from dataclasses import dataclass
from .base import DomainEvent

@dataclass
class UserCreated(DomainEvent):
    user_id: int
    username: str
    organization_id: int

@dataclass
class UserUpdated(DomainEvent):
    user_id: int
    changes: dict

@dataclass
class UserDeleted(DomainEvent):
    user_id: int
    deleted_by_id: int

# shared/events/device_events.py
@dataclass
class DeviceActivated(DomainEvent):
    device_id: int
    organization_id: int
    activation_code: str

@dataclass
class DeviceOffline(DomainEvent):
    device_id: int
    last_seen_at: datetime

@dataclass
class DevicePlaylistAssigned(DomainEvent):
    device_id: int
    playlist_id: int
    assigned_by_id: int

# shared/events/content_events.py
@dataclass
class ContentUploaded(DomainEvent):
    content_id: int
    organization_id: int
    content_type: str
    file_size: int

@dataclass
class ContentDeleted(DomainEvent):
    content_id: int
    deleted_by_id: int

# shared/events/audit_events.py
@dataclass
class AuditLogCreated(DomainEvent):
    action: str
    entity_type: str
    entity_id: int
    user_id: int
    organization_id: int
    changes: dict
```

### 5.3 Event Bus Implementation

```python
# shared/event_bus/local_bus.py
from typing import Callable, Dict, List, Type
from ..events.base import DomainEvent
import asyncio
import logging

logger = logging.getLogger(__name__)

class LocalEventBus:
    """
    In-memory event bus for monolith deployment.
    Events are processed synchronously in the same process.
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to {event_type.__name__}")

    async def publish(self, event: DomainEvent):
        """Publish an event to all subscribers"""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in handler {handler.__name__}: {e}")

    def unsubscribe(self, event_type: Type[DomainEvent], handler: Callable):
        """Unsubscribe a handler from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)


# shared/event_bus/redis_bus.py (for future microservices)
class RedisEventBus:
    """
    Redis-based event bus for distributed deployment.
    Events are published to Redis Pub/Sub.
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        # Implementation for microservices
        pass

    async def publish(self, event: DomainEvent):
        # Serialize and publish to Redis
        pass

    async def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        # Subscribe to Redis channel
        pass


# shared/event_bus/bus.py
import os

def get_event_bus():
    """Factory function to get appropriate event bus"""
    mode = os.getenv("EVENT_BUS_MODE", "local")

    if mode == "local":
        from .local_bus import LocalEventBus
        return LocalEventBus()
    elif mode == "redis":
        from .redis_bus import RedisEventBus
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return RedisEventBus(redis_url)
    else:
        raise ValueError(f"Unknown event bus mode: {mode}")

# Global event bus instance
event_bus = get_event_bus()
```

---

## 6. Service Boundaries

### 6.1 Core Services (Should NOT depend on others)

| Service | Responsibility | Dependencies |
|---------|---------------|--------------|
| `auth` | Authentication, JWT | None (core) |
| `rbac` | Roles, Permissions | auth |
| `organization` | Organization CRUD | None (core) |
| `user` | User CRUD | auth, rbac, organization |

### 6.2 Business Services (Can depend on core)

| Service | Responsibility | Allowed Dependencies |
|---------|---------------|---------------------|
| `content` | Content management | organization (via interface) |
| `device` | Device management | organization (via interface) |
| `playlist` | Playlist management | content, organization (via interface) |
| `schedule` | Schedule management | playlist, device (via interface) |
| `menu` | Menu management | organization (via interface) |

### 6.3 Supporting Services (Can depend on any via events)

| Service | Responsibility | Communication |
|---------|---------------|---------------|
| `audit` | Audit logging | Events only |
| `analytics` | Analytics tracking | Events only |
| `dashboard` | Aggregated data | Read-only queries |
| `session` | Session management | auth (same boundary) |

### 6.4 Service Dependency Rules

```
ALLOWED:
✅ Business Service → Core Service (via Interface)
✅ Supporting Service → Any (via Events)
✅ Same-boundary direct import (auth ↔ session)

NOT ALLOWED:
❌ Core Service → Business Service
❌ Direct repository import across boundaries
❌ Circular dependencies
```

---

## 7. Migration Strategy

### 7.1 Strangler Fig Pattern

```
Step 1: Create interface alongside existing code
┌─────────────────────────────────────────┐
│  ┌─────────┐     ┌─────────────────┐   │
│  │ Old     │     │ New Interface   │   │
│  │ Import  │     │ (not used yet)  │   │
│  └─────────┘     └─────────────────┘   │
└─────────────────────────────────────────┘

Step 2: Create adapter that wraps old code
┌─────────────────────────────────────────┐
│  ┌─────────┐     ┌─────────────────┐   │
│  │ Old     │ ◄── │    Adapter      │   │
│  │ Import  │     │ (wraps old)     │   │
│  └─────────┘     └─────────────────┘   │
└─────────────────────────────────────────┘

Step 3: Switch to use adapter
┌─────────────────────────────────────────┐
│  ┌─────────┐     ┌─────────────────┐   │
│  │ Old     │ ◄── │    Adapter      │ ◄─┼── New code uses this
│  │ Import  │     │                 │   │
│  └─────────┘     └─────────────────┘   │
└─────────────────────────────────────────┘

Step 4: Remove old direct imports
┌─────────────────────────────────────────┐
│                  ┌─────────────────┐   │
│                  │    Adapter      │ ◄─┼── All code uses this
│                  │                 │   │
│                  └─────────────────┘   │
└─────────────────────────────────────────┘
```

### 7.2 Backward Compatibility Rules

1. **Never delete before replace** - Old code must work until new code is tested
2. **Feature flags** - Use environment variables to switch implementations
3. **Dual-write** - Write to both old and new during transition
4. **Shadow testing** - Run new code in parallel, compare results

### 7.3 Rollback Strategy

```python
# config/service_config.py
import os

# Feature flags for gradual rollout
USE_INTERFACE_USER_SERVICE = os.getenv("USE_INTERFACE_USER_SERVICE", "false") == "true"
USE_INTERFACE_DEVICE_SERVICE = os.getenv("USE_INTERFACE_DEVICE_SERVICE", "false") == "true"
USE_EVENT_BUS = os.getenv("USE_EVENT_BUS", "false") == "true"

# Usage in code
if USE_INTERFACE_USER_SERVICE:
    user_service = get_user_service()  # New interface
else:
    user_service = UserRepository(db)  # Old direct import
```

---

## 8. Risk Assessment

### 8.1 Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes | LOW | HIGH | Adapter pattern, feature flags |
| Performance degradation | LOW | MEDIUM | Benchmark before/after |
| Increased complexity | MEDIUM | LOW | Good documentation |
| Team learning curve | MEDIUM | LOW | Training sessions |
| Incomplete migration | MEDIUM | MEDIUM | Clear phases, checkpoints |

### 8.2 Mitigation Strategies

**Breaking Changes**:
- Use adapter pattern (wrap old code, don't replace)
- Feature flags for gradual rollout
- Extensive testing before each phase

**Performance**:
- Benchmark critical paths before refactoring
- LocalEventBus has minimal overhead (in-memory)
- Interface calls same as direct calls (Python duck typing)

**Complexity**:
- Clear documentation (this document)
- Code examples for each pattern
- Code review for all changes

---

## 9. Timeline Estimate

```
┌────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TIMELINE                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Week 1-2: Infrastructure Setup                            │
│  ├── Create directory structure                            │
│  ├── Implement LocalEventBus                               │
│  ├── Create base interfaces                                │
│  └── Write unit tests                                      │
│                                                            │
│  Week 3: Audit Service (Pilot)                             │
│  ├── Create IUserService, IOrganizationService             │
│  ├── Create adapters                                       │
│  ├── Refactor audit service                                │
│  └── Test & deploy                                         │
│                                                            │
│  Week 4: Tag Service                                       │
│  ├── Create IDeviceService, IContentService                │
│  ├── Refactor tag service                                  │
│  └── Test & deploy                                         │
│                                                            │
│  Week 5-6: Dashboard & PMS                                 │
│  ├── Refactor dashboard service                            │
│  ├── Refactor PMS service                                  │
│  └── Test & deploy                                         │
│                                                            │
│  Week 7-10: Remaining Services                             │
│  ├── content, device, playlist                             │
│  ├── schedule, menu, session                               │
│  └── Incremental deploy                                    │
│                                                            │
│  Week 11-12: Event-Driven Features                         │
│  ├── Cache invalidation via events                         │
│  ├── Audit logging via events                              │
│  ├── WebSocket notifications                               │
│  └── Final documentation                                   │
│                                                            │
└────────────────────────────────────────────────────────────┘

Total: ~12 weeks (3 months) for full migration
Can be done part-time alongside feature development
```

---

## 10. Checklist

### Phase 1: Infrastructure Setup
- [ ] Create `shared/interfaces/` directory
- [ ] Create `shared/interfaces/__init__.py`
- [ ] Create `shared/interfaces/base.py`
- [ ] Create `shared/events/` directory
- [ ] Create `shared/events/__init__.py`
- [ ] Create `shared/events/base.py`
- [ ] Create `shared/adapters/` directory
- [ ] Create `shared/adapters/__init__.py`
- [ ] Create `shared/event_bus/` directory
- [ ] Create `shared/event_bus/__init__.py`
- [ ] Create `shared/event_bus/local_bus.py`
- [ ] Create `shared/event_bus/bus.py`
- [ ] Add `EVENT_BUS_MODE` to `.env.example`
- [ ] Write unit tests for LocalEventBus
- [ ] Update CLAUDE.md with new architecture

### Phase 2: Audit Service
- [ ] Create `shared/interfaces/user_service.py`
- [ ] Create `shared/interfaces/organization_service.py`
- [ ] Create `shared/adapters/user_adapter.py`
- [ ] Create `shared/adapters/organization_adapter.py`
- [ ] Create `shared/events/audit_events.py`
- [ ] Refactor `services/audit/routes.py`
- [ ] Add feature flag `USE_INTERFACE_USER_SERVICE`
- [ ] Test backward compatibility
- [ ] Deploy to staging
- [ ] Deploy to production
- [ ] Remove feature flag (make default)

### Phase 3: Tag Service
- [ ] Create `shared/interfaces/device_service.py`
- [ ] Create `shared/interfaces/content_service.py`
- [ ] Create `shared/adapters/device_adapter.py`
- [ ] Create `shared/adapters/content_adapter.py`
- [ ] Create `shared/events/tag_events.py`
- [ ] Refactor `services/tag/repositories/tag_repo.py`
- [ ] Test backward compatibility
- [ ] Deploy to staging
- [ ] Deploy to production

### Phase 4-6: Remaining Services
- [ ] Dashboard service refactored
- [ ] PMS service refactored
- [ ] Content service refactored
- [ ] Device service refactored
- [ ] Playlist service refactored
- [ ] Schedule service refactored
- [ ] Menu service refactored
- [ ] Session service refactored

### Final Steps
- [ ] All direct cross-service imports removed
- [ ] All services use interfaces
- [ ] Event bus integrated for cross-cutting concerns
- [ ] Documentation updated
- [ ] Team trained on new patterns
- [ ] Performance benchmarks validated

---

## Appendix A: Example Adapter Implementation

```python
# shared/adapters/user_adapter.py
from typing import Optional, List
from shared.interfaces.user_service import IUserService, UserDTO
from services.user.repositories.user_repo import UserRepository
from shared.database import SessionLocal

class UserServiceAdapter(IUserService):
    """
    Adapter that implements IUserService using existing UserRepository.
    This allows gradual migration without breaking existing code.
    """

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal()
        self.repo = UserRepository(self.db)

    def get_user(self, user_id: int) -> Optional[UserDTO]:
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        return UserDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.name if user.role else None,
            organization_id=user.organization_id,
            is_active=user.is_active
        )

    def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        user = self.repo.get_by_username(username)
        if not user:
            return None
        return self._to_dto(user)

    def get_users_by_organization(self, org_id: int) -> List[UserDTO]:
        users = self.repo.get_by_organization(org_id)
        return [self._to_dto(u) for u in users]

    def is_user_active(self, user_id: int) -> bool:
        user = self.repo.get_by_id(user_id)
        return user.is_active if user else False

    def _to_dto(self, user) -> UserDTO:
        return UserDTO(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.name if user.role else None,
            organization_id=user.organization_id,
            is_active=user.is_active
        )


# Factory function
def get_user_service(db_session=None) -> IUserService:
    return UserServiceAdapter(db_session)
```

---

## Appendix B: Event Subscriber Example

```python
# services/audit/subscribers.py
from shared.event_bus import event_bus
from shared.events.user_events import UserCreated, UserUpdated, UserDeleted
from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase

async def handle_user_created(event: UserCreated):
    """Log user creation to audit trail"""
    use_case = CreateAuditLogUseCase()
    await use_case.execute(
        action="CREATE",
        entity_type="user",
        entity_id=event.user_id,
        user_id=event.user_id,  # Created by self (registration)
        organization_id=event.organization_id,
        changes={"username": event.username}
    )

async def handle_user_deleted(event: UserDeleted):
    """Log user deletion to audit trail"""
    use_case = CreateAuditLogUseCase()
    await use_case.execute(
        action="DELETE",
        entity_type="user",
        entity_id=event.user_id,
        user_id=event.deleted_by_id,
        organization_id=None,
        changes={}
    )

# Register subscribers on app startup
def register_audit_subscribers():
    event_bus.subscribe(UserCreated, handle_user_created)
    event_bus.subscribe(UserDeleted, handle_user_deleted)
```

---

## Appendix C: Future Microservices Deployment

When ready to split into microservices:

```yaml
# docker-compose.microservices.yml (future)
version: '3.8'

services:
  # Core Services
  auth-service:
    build: ./services/auth
    environment:
      - EVENT_BUS_MODE=redis
      - DATABASE_URL=postgresql://auth_db/auth

  user-service:
    build: ./services/user
    environment:
      - EVENT_BUS_MODE=redis
      - DATABASE_URL=postgresql://user_db/users

  # Business Services
  content-service:
    build: ./services/content
    environment:
      - EVENT_BUS_MODE=redis
      - DATABASE_URL=postgresql://content_db/content
      - USER_SERVICE_URL=http://user-service:8001

  device-service:
    build: ./services/device
    environment:
      - EVENT_BUS_MODE=redis
      - DATABASE_URL=postgresql://device_db/devices

  # Supporting Services
  audit-service:
    build: ./services/audit
    environment:
      - EVENT_BUS_MODE=redis
      - DATABASE_URL=postgresql://audit_db/audit

  # Infrastructure
  redis:
    image: redis:7-alpine

  api-gateway:
    image: nginx
    ports:
      - "8001:80"
```

---

**End of Document**

*This document will be updated as implementation progresses.*
