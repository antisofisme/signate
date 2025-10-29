# BACKEND ARCHITECTURE DESIGN: ANTHIAS INTEGRATION STRATEGY

## Executive Summary

This document outlines the modular architecture design for integrating Anthias's best features into our backend system. Based on analysis, we recommend **Option C: Hybrid Architecture** - keeping Anthias as a specialized storage service while migrating core business logic to the backend.

---

## CURRENT STATE ANALYSIS

### Backend (FastAPI + PostgreSQL)
```
Current Capabilities:
✅ Device management with activation codes
✅ Content metadata tracking
✅ Playlist management with scheduling
✅ Tag-based grouping
✅ Activity logging
✅ WebSocket real-time updates
✅ Multi-tenant ready architecture

Missing Features:
❌ Intelligent deadline-based scheduling
❌ Non-disruptive playlist updates
❌ Advanced asset lifecycle management
❌ Efficient change detection
❌ Backup/recovery system
❌ Hardware diagnostics
```

### Anthias (Django + SQLite)
```
Strong Features:
✅ Deadline-based scheduling algorithm
✅ Efficient database change detection
✅ Non-disruptive playlist updates
✅ Asset lifecycle management
✅ Multi-version API compatibility
✅ Background job processing
✅ Backup/recovery system
✅ Hardware diagnostics

Current Usage:
- File storage only
- Asset upload endpoint
- Serving media files
- NOT using scheduling features
```

---

## RECOMMENDED STRATEGY: HYBRID ARCHITECTURE

### Core Principle
**"Best of Both Worlds"** - Keep Anthias for what it does best (file management), while migrating intelligent features to our backend.

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Web Admin│  │  Viewer  │  │ WebOS TV │  │  Mobile  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────────────┐
│                    BACKEND API LAYER                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │   Auth   │ │ Devices  │ │ Content  │ │Playlists │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER (NEW)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Business Logic Services                     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ Scheduler  │  │  Playlist  │  │   Asset    │     │  │
│  │  │  Service   │  │  Manager   │  │  Manager   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │   Backup   │  │ Diagnostic │  │   Cache    │     │  │
│  │  │  Service   │  │  Service   │  │  Service   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │   PostgreSQL    │              │     Anthias     │      │
│  │   (Metadata)    │◄────────────►│  (File Storage) │      │
│  └─────────────────┘              └─────────────────┘      │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │      Redis      │              │   File System   │      │
│  │    (Cache)      │              │  (Local Assets) │      │
│  └─────────────────┘              └─────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE-BY-PHASE MIGRATION PLAN

### Phase 1: Core Service Architecture Setup
**Goal:** Establish modular service layer without breaking existing functionality

```
backend/
├── app/
│   ├── models/           # Existing models
│   ├── schemas/          # Existing schemas
│   ├── api/              # Existing endpoints
│   ├── core/             # Core utilities
│   └── services/         # NEW: Service layer
│       ├── __init__.py
│       ├── base.py               # Base service class
│       ├── scheduler/            # Scheduling logic
│       │   ├── __init__.py
│       │   ├── deadline_scheduler.py
│       │   ├── change_detector.py
│       │   └── playlist_builder.py
│       ├── asset_manager/        # Asset lifecycle
│       │   ├── __init__.py
│       │   ├── asset_service.py
│       │   ├── metadata_extractor.py
│       │   └── storage_adapter.py
│       ├── playlist_manager/     # Playlist operations
│       │   ├── __init__.py
│       │   ├── playlist_service.py
│       │   ├── ordering_strategy.py
│       │   └── shuffle_algorithm.py
│       ├── backup/               # Backup/recovery
│       │   ├── __init__.py
│       │   ├── backup_service.py
│       │   └── recovery_service.py
│       └── diagnostics/          # System health
│           ├── __init__.py
│           ├── health_checker.py
│           └── metrics_collector.py
```

### Phase 2: Deadline-Based Scheduler Implementation
**Feature:** Port Anthias's intelligent scheduling algorithm

```python
# backend/app/services/scheduler/deadline_scheduler.py

from datetime import datetime
from typing import List, Optional, Tuple
from app.models import Content, ContentAssignment, Playlist

class DeadlineScheduler:
    """
    Intelligent deadline-based content scheduler
    Ported from Anthias viewer/scheduling.py
    """

    def __init__(self):
        self.current_playlist: List[dict] = []
        self.next_deadline: Optional[datetime] = None
        self.last_db_check: datetime = datetime.now()

    def calculate_next_deadline(self) -> Optional[datetime]:
        """
        Calculate the next time playlist needs refresh
        Based on content start/end dates
        """
        deadlines = []

        # Get active content end dates
        active_content = ContentAssignment.query.filter(
            ContentAssignment.is_active == True,
            ContentAssignment.end_date > datetime.now()
        ).all()

        for assignment in active_content:
            if assignment.end_date:
                deadlines.append(assignment.end_date)

        # Get inactive content start dates
        inactive_content = ContentAssignment.query.filter(
            ContentAssignment.is_active == False,
            ContentAssignment.start_date > datetime.now()
        ).all()

        for assignment in inactive_content:
            if assignment.start_date:
                deadlines.append(assignment.start_date)

        # Return nearest deadline
        if deadlines:
            return min(deadlines)
        return None

    def should_refresh_playlist(self) -> bool:
        """
        Determine if playlist needs refreshing
        Checks: deadline reached, database changes, manual trigger
        """
        # Check deadline
        if self.next_deadline and datetime.now() >= self.next_deadline:
            return True

        # Check database modification (efficient change detection)
        if self.detect_database_changes():
            return True

        return False

    def build_playlist(self, device_id: int) -> List[dict]:
        """
        Build optimized playlist for device
        Non-disruptive: maintains current position if possible
        """
        new_playlist = self._generate_active_content(device_id)

        # Non-disruptive update logic
        if self._can_maintain_position(self.current_playlist, new_playlist):
            return self._merge_playlists(self.current_playlist, new_playlist)

        return new_playlist
```

### Phase 3: Database Schema Enhancements
**Goal:** Add missing fields for advanced scheduling

```sql
-- Add deadline tracking to content assignments
ALTER TABLE content_assignments ADD COLUMN next_deadline TIMESTAMP;
ALTER TABLE content_assignments ADD COLUMN last_played_at TIMESTAMP;
ALTER TABLE content_assignments ADD COLUMN play_count INTEGER DEFAULT 0;

-- Add scheduling metadata to playlists
ALTER TABLE playlists ADD COLUMN last_refresh_at TIMESTAMP;
ALTER TABLE playlists ADD COLUMN refresh_count INTEGER DEFAULT 0;
ALTER TABLE playlists ADD COLUMN is_shuffled BOOLEAN DEFAULT FALSE;

-- Add asset lifecycle tracking
ALTER TABLE contents ADD COLUMN is_processing BOOLEAN DEFAULT FALSE;
ALTER TABLE contents ADD COLUMN processing_started_at TIMESTAMP;
ALTER TABLE contents ADD COLUMN processing_error TEXT;

-- Add system diagnostics table
CREATE TABLE system_diagnostics (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    network_latency FLOAT,
    display_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Phase 4: API Endpoint Enhancements
**Goal:** Expose new scheduling features via REST API

```python
# New endpoints to add

@router.get("/api/scheduler/next-deadline/{device_id}")
async def get_next_deadline(device_id: int):
    """Get the next refresh deadline for device"""
    scheduler = DeadlineScheduler()
    deadline = scheduler.calculate_next_deadline_for_device(device_id)
    return {"deadline": deadline, "remaining_seconds": ...}

@router.post("/api/scheduler/refresh/{device_id}")
async def force_refresh(device_id: int):
    """Force playlist refresh for device"""
    scheduler = DeadlineScheduler()
    new_playlist = scheduler.build_playlist(device_id)
    return {"playlist": new_playlist, "next_deadline": ...}

@router.get("/api/playlists/{id}/efficiency-stats")
async def get_playlist_efficiency(id: int):
    """Get efficiency metrics for playlist"""
    return {
        "unnecessary_refreshes_avoided": 245,
        "average_refresh_interval": "4h 23m",
        "deadline_accuracy": 0.98
    }
```

### Phase 5: Service Integration Points
**Goal:** Define clean interfaces between services

```python
# backend/app/services/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseService(ABC):
    """Base class for all services"""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources"""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean shutdown of service"""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return service health status"""
        pass

# Service Registry Pattern
class ServiceRegistry:
    """Central registry for all services"""

    _services: Dict[str, BaseService] = {}

    @classmethod
    def register(cls, name: str, service: BaseService):
        cls._services[name] = service

    @classmethod
    def get(cls, name: str) -> BaseService:
        return cls._services.get(name)

    @classmethod
    async def initialize_all(cls):
        for service in cls._services.values():
            await service.initialize()
```

---

## FEATURE MIGRATION MATRIX

| Feature | Current Location | Target Location | Priority | Complexity |
|---------|-----------------|-----------------|----------|------------|
| **Deadline Scheduler** | Anthias viewer/scheduling.py | backend/services/scheduler/ | HIGH | Medium |
| **Change Detection** | Anthias DB mtime check | backend/services/scheduler/change_detector.py | HIGH | Low |
| **Non-disruptive Updates** | Anthias scheduler | backend/services/playlist_manager/ | HIGH | Medium |
| **Asset Lifecycle** | Anthias models.py | backend/services/asset_manager/ | MEDIUM | Low |
| **Shuffle Algorithm** | Anthias viewer | backend/services/playlist_manager/ | MEDIUM | Low |
| **Backup/Recovery** | Anthias API mixins | backend/services/backup/ | LOW | High |
| **Hardware Diagnostics** | Anthias lib/diagnostics | backend/services/diagnostics/ | LOW | Medium |
| **Multi-version API** | Anthias v1/v1.1/v1.2/v2 | Keep in Anthias | N/A | N/A |
| **File Storage** | Anthias file system | Keep in Anthias | N/A | N/A |
| **Background Jobs** | Anthias Celery | backend (new Celery setup) | MEDIUM | Medium |

---

## IMPLEMENTATION STANDARDS

### 1. Dependency Injection Pattern
```python
# Use FastAPI's dependency injection
from fastapi import Depends

class PlaylistService:
    def __init__(self, scheduler: DeadlineScheduler = Depends()):
        self.scheduler = scheduler

    async def get_optimized_playlist(self, device_id: int):
        if self.scheduler.should_refresh_playlist():
            return await self.scheduler.build_playlist(device_id)
        return self.scheduler.current_playlist
```

### 2. Interface Contracts
```python
# Define clear interfaces using Protocol
from typing import Protocol

class SchedulerProtocol(Protocol):
    """Interface for scheduler implementations"""

    def calculate_next_deadline(self) -> datetime:
        ...

    def should_refresh_playlist(self) -> bool:
        ...

    def build_playlist(self, device_id: int) -> List[dict]:
        ...
```

### 3. Error Handling Pattern
```python
# Structured error handling
class SchedulerError(Exception):
    """Base scheduler exception"""
    pass

class DeadlineCalculationError(SchedulerError):
    """Failed to calculate deadline"""
    pass

class PlaylistBuildError(SchedulerError):
    """Failed to build playlist"""
    pass

# Usage
try:
    playlist = scheduler.build_playlist(device_id)
except DeadlineCalculationError as e:
    logger.error(f"Deadline calculation failed: {e}")
    # Fallback to time-based refresh
except PlaylistBuildError as e:
    logger.error(f"Playlist build failed: {e}")
    # Return cached playlist
```

### 4. Testing Strategy
```python
# Unit tests for each service
# backend/tests/services/test_scheduler.py

import pytest
from datetime import datetime, timedelta
from app.services.scheduler import DeadlineScheduler

@pytest.fixture
def scheduler():
    return DeadlineScheduler()

def test_deadline_calculation(scheduler, sample_content):
    """Test deadline calculation logic"""
    deadline = scheduler.calculate_next_deadline()
    assert deadline > datetime.now()
    assert deadline < datetime.now() + timedelta(days=1)

def test_non_disruptive_update(scheduler, current_playlist, new_content):
    """Test playlist maintains position when possible"""
    new_playlist = scheduler.build_playlist(device_id=1)
    # Assert current playing item position maintained
```

### 5. Observability Standards
```python
# Structured logging for all services
import structlog

logger = structlog.get_logger()

class DeadlineScheduler:
    def build_playlist(self, device_id: int):
        logger.info(
            "building_playlist",
            device_id=device_id,
            current_deadline=self.next_deadline,
            playlist_size=len(self.current_playlist)
        )

        # Metrics collection
        metrics.histogram(
            "playlist_build_duration",
            duration_ms,
            tags={"device_id": device_id}
        )
```

---

## MIGRATION PHASES TIMELINE

### Month 1: Foundation
- [ ] Set up service layer structure
- [ ] Create base service classes
- [ ] Implement service registry
- [ ] Add dependency injection
- [ ] Set up testing framework

### Month 2: Core Features
- [ ] Port deadline scheduler
- [ ] Implement change detection
- [ ] Add non-disruptive updates
- [ ] Create playlist builder
- [ ] Add shuffle algorithm

### Month 3: Advanced Features
- [ ] Asset lifecycle management
- [ ] Backup/recovery service
- [ ] Diagnostics service
- [ ] Performance optimization
- [ ] Load testing

### Month 4: Production Readiness
- [ ] Complete integration testing
- [ ] Performance benchmarking
- [ ] Documentation
- [ ] Migration scripts
- [ ] Rollback procedures

---

## BENEFITS OF THIS APPROACH

### 1. **Leverages Anthias Strengths**
- Keep proven file storage system
- Use stable asset management
- Maintain backward compatibility

### 2. **Adds Missing Intelligence**
- Deadline-based scheduling
- Efficient change detection
- Non-disruptive updates
- Advanced playlist algorithms

### 3. **Maintains System Boundaries**
- Clear separation of concerns
- Anthias = Storage layer
- Backend = Business logic
- Database = Metadata

### 4. **Enables Future Growth**
- Modular architecture
- Easy to extend
- Technology agnostic
- Cloud-ready design

### 5. **Minimizes Risk**
- Gradual migration
- Fallback options
- No big-bang changes
- Continuous operation

---

## KEY ARCHITECTURAL DECISIONS

### ADR-001: Keep Anthias as Storage Service
**Decision:** Maintain Anthias for file storage and serving
**Rationale:**
- Proven reliability over 10+ years
- Complex file handling already solved
- Multi-format support works well
- Migration would be high risk, low reward

### ADR-002: Port Scheduling Logic to Backend
**Decision:** Migrate deadline-based scheduling to our service layer
**Rationale:**
- Need custom business rules
- Want PostgreSQL integration
- Require multi-tenant support
- Better observability needed

### ADR-003: Use Service Registry Pattern
**Decision:** Implement central service registry
**Rationale:**
- Clean dependency management
- Easy service discovery
- Simplified testing
- Better lifecycle management

### ADR-004: Implement Non-Disruptive Updates
**Decision:** Port Anthias's smart update algorithm
**Rationale:**
- Better user experience
- Reduces jarring transitions
- Maintains playback continuity
- Professional presentation quality

---

## RISK MITIGATION

### Risk 1: Performance Degradation
**Mitigation:**
- Benchmark each service
- Use Redis caching
- Implement circuit breakers
- Monitor response times

### Risk 2: Data Consistency
**Mitigation:**
- Single source of truth principle
- Transaction boundaries
- Event sourcing for critical ops
- Regular consistency checks

### Risk 3: Migration Complexity
**Mitigation:**
- Phase-by-phase approach
- Feature flags for rollback
- Parallel run capability
- Comprehensive testing

### Risk 4: Integration Issues
**Mitigation:**
- Well-defined interfaces
- Contract testing
- Mock services for testing
- Gradual rollout

---

## SUCCESS METRICS

### Technical Metrics
- Playlist refresh time < 100ms
- Unnecessary refreshes reduced by 80%
- API response time < 200ms p95
- Zero data inconsistencies
- 99.9% uptime maintained

### Business Metrics
- Smoother content transitions
- Reduced bandwidth usage
- Lower CPU utilization
- Improved user satisfaction
- Faster feature delivery

---

## CONCLUSION

The hybrid architecture approach provides the best path forward:

1. **Preserves Investment** - Keeps working Anthias components
2. **Adds Intelligence** - Ports advanced algorithms to backend
3. **Maintains Stability** - Gradual, low-risk migration
4. **Enables Innovation** - Modular design for future features
5. **Professional Quality** - Enterprise-grade architecture

This design positions the system for long-term success while minimizing disruption to current operations.

---

## NEXT STEPS

1. **Review & Approve** - Get stakeholder buy-in on architecture
2. **Create Detailed Specs** - Write implementation specifications for Phase 1
3. **Set Up Development** - Create service layer structure
4. **Begin Phase 1** - Start with foundation components
5. **Iterate & Refine** - Adjust based on learnings

---

*Document Version: 1.0*
*Date: 2025-01-28*
*Author: Backend Architecture Team*