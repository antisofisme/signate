# Device Management - Implementation Plan

**Architecture:** Clean Architecture (Backend) + Feature-based (Frontend)
**Integration:** Auth, Organization, Content, Playlist, Tag, Audit
**Reference:** Analysis from backend-old + web-admin-old

---

## Table of Contents

1. [Overview](#overview)
2. [Backend Implementation](#backend-implementation)
3. [Frontend Implementation](#frontend-implementation)
4. [Database Schema](#database-schema)
5. [Integration Points](#integration-points)
6. [Implementation Phases](#implementation-phases)
7. [Testing Checklist](#testing-checklist)
8. [API Endpoints Reference](#api-endpoints-reference)

---

## Overview

### Device System Features

**Core Functionality:**
- ✅ Device registration with 6-digit activation codes
- ✅ Device authentication (JWT tokens)
- ✅ Device monitoring (heartbeat, online/offline status)
- ✅ Remote device management (commands)
- ✅ Content assignment (direct, tag-based, playlist-based)
- ✅ Device logs & analytics
- ✅ Network speed testing
- ✅ Multi-tenant isolation

**Device Types:**
1. **TV Devices** - WebOS/Native apps (direct IP registration)
2. **Monitor Devices** - Browser-based (auto-detection)

**Device Lifecycle:**
```
Registration (Viewer) → Pending (CMS) → Activation (Admin)
  → Active (Operational) → Release (Reset) → Pending (Re-activation)
```

**Content Priority (3-tier):**
1. Direct assignment (highest)
2. Tag-based assignment
3. Playlist assignment (lowest)

---

## Backend Implementation

**Location:** `backend-python/services/device/`

### Structure (Clean Architecture)

```
services/device/
├── domain/
│   ├── __init__.py
│   ├── device.py              # Device entity
│   ├── device_command.py      # DeviceCommand entity
│   ├── device_log.py          # DeviceLog entity
│   └── interfaces.py          # Repository contracts
├── repositories/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models (7 tables)
│   ├── device_repo.py         # Device CRUD + queries
│   ├── device_command_repo.py # Command queue management
│   └── device_log_repo.py     # Log storage & retrieval
├── use_cases/
│   ├── __init__.py
│   # Registration & Activation (3 files)
│   ├── register_device.py     # Create activation code
│   ├── activate_device.py     # Admin approval
│   ├── authenticate_device.py # JWT token generation
│   # CRUD Operations (4 files)
│   ├── list_devices.py        # List with filters
│   ├── get_device.py          # Single device details
│   ├── update_device.py       # Update settings
│   ├── delete_device.py       # Hard delete
│   # Monitoring (2 files)
│   ├── process_heartbeat.py   # Heartbeat handling
│   ├── get_device_status.py   # Online/offline check
│   # Content Assignment (3 files)
│   ├── assign_content.py      # Direct content assignment
│   ├── assign_tags.py         # Tag-based assignment
│   ├── get_device_content.py  # Resolve content (3-tier)
│   # Remote Management (2 files)
│   ├── send_command.py        # Queue command
│   ├── get_pending_commands.py # Poll commands
│   # Analytics (3 files)
│   ├── create_device_log.py   # Store log entry
│   ├── get_device_logs.py     # Retrieve logs
│   └── run_speed_test.py      # Network test
├── dtos.py                    # Request/Response schemas
└── routes.py                  # FastAPI endpoints (21 endpoints)
```

### Domain Layer (Pure Python)

#### `domain/device.py`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class DeviceType(Enum):
    TV = "tv"
    MONITOR = "monitor"

class DeviceStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

@dataclass
class Device:
    """Device entity - Pure business logic"""
    id: Optional[int]
    organization_id: int
    device_name: str
    device_type: DeviceType
    activation_code: Optional[str]
    code_expires_at: Optional[datetime]
    status: DeviceStatus
    platform: Optional[str]
    ip_address: Optional[str]
    display_width: Optional[int]
    display_height: Optional[int]
    rotation: int = 0
    volume: int = 50
    last_seen: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_online(self, timeout_seconds: int = 60) -> bool:
        """Check if device is online based on last_seen"""
        if not self.last_seen:
            return False
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.last_seen < timedelta(seconds=timeout_seconds)

    def can_activate(self) -> bool:
        """Check if device can be activated"""
        if self.status != DeviceStatus.PENDING:
            return False
        if not self.activation_code or not self.code_expires_at:
            return False
        return datetime.utcnow() < self.code_expires_at

    def generate_activation_code(self) -> str:
        """Generate 6-digit activation code"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def activate(self, user_id: int):
        """Activate device - business logic"""
        if not self.can_activate():
            raise ValueError("Cannot activate device")
        self.status = DeviceStatus.ACTIVE
        self.activation_code = None
        self.code_expires_at = None
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()

    def release(self, user_id: int):
        """Release device (reset to pending with new code)"""
        self.status = DeviceStatus.PENDING
        self.activation_code = self.generate_activation_code()
        self.code_expires_at = datetime.utcnow() + timedelta(minutes=10)
        self.last_seen = None
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()
```

#### `domain/device_command.py`
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class CommandType(Enum):
    RESET = "reset"
    REFRESH = "refresh"
    RELOAD = "reload"
    SPEED_TEST = "speed_test"
    UPDATE_CONTENT = "update_content"

class CommandStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class DeviceCommand:
    """Device command entity"""
    id: Optional[int]
    device_id: int
    organization_id: int
    command_type: CommandType
    parameters: Optional[dict] = None
    status: CommandStatus = CommandStatus.PENDING
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Check if command has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def mark_sent(self):
        """Mark command as sent to device"""
        self.status = CommandStatus.SENT
        self.sent_at = datetime.utcnow()

    def mark_executed(self):
        """Mark command as executed"""
        self.status = CommandStatus.EXECUTED
        self.executed_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark command as failed"""
        self.status = CommandStatus.FAILED
        self.error_message = error
        self.executed_at = datetime.utcnow()
```

#### `domain/interfaces.py`
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from .device import Device, DeviceStatus
from .device_command import DeviceCommand, CommandType
from .device_log import DeviceLog

class IDeviceRepository(ABC):
    """Device repository contract"""

    @abstractmethod
    def create(self, device: Device) -> Device:
        """Create new device"""
        pass

    @abstractmethod
    def get_by_id(self, device_id: int, organization_id: int) -> Optional[Device]:
        """Get device by ID (with org filter)"""
        pass

    @abstractmethod
    def get_by_code(self, activation_code: str) -> Optional[Device]:
        """Get device by activation code"""
        pass

    @abstractmethod
    def list(
        self,
        organization_id: int,
        status: Optional[DeviceStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Device], int]:
        """List devices with filters (returns items, total)"""
        pass

    @abstractmethod
    def update(self, device: Device) -> Device:
        """Update device"""
        pass

    @abstractmethod
    def delete(self, device_id: int, organization_id: int) -> bool:
        """Delete device"""
        pass

    @abstractmethod
    def update_heartbeat(self, device_id: int) -> bool:
        """Update last_seen timestamp"""
        pass

class IDeviceCommandRepository(ABC):
    """Device command repository contract"""

    @abstractmethod
    def create(self, command: DeviceCommand) -> DeviceCommand:
        """Create new command"""
        pass

    @abstractmethod
    def get_pending_for_device(self, device_id: int) -> List[DeviceCommand]:
        """Get pending commands for device"""
        pass

    @abstractmethod
    def update(self, command: DeviceCommand) -> DeviceCommand:
        """Update command status"""
        pass

    @abstractmethod
    def expire_old_commands(self) -> int:
        """Expire commands older than 7 days (returns count)"""
        pass

class IDeviceLogRepository(ABC):
    """Device log repository contract"""

    @abstractmethod
    def create(self, log: DeviceLog) -> DeviceLog:
        """Create log entry"""
        pass

    @abstractmethod
    def list(
        self,
        device_id: int,
        organization_id: int,
        level: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[DeviceLog], int]:
        """List logs with filters"""
        pass

    @abstractmethod
    def delete_for_device(self, device_id: int) -> int:
        """Delete all logs for device (returns count)"""
        pass
```

### Repository Layer (SQLAlchemy)

#### `repositories/models.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database import Base
import enum

class DeviceType(str, enum.Enum):
    TV = "tv"
    MONITOR = "monitor"

class DeviceStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class CommandType(str, enum.Enum):
    RESET = "reset"
    REFRESH = "refresh"
    RELOAD = "reload"
    SPEED_TEST = "speed_test"
    UPDATE_CONTENT = "update_content"

class CommandStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"

class DeviceModel(Base):
    """Device table"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    activation_code = Column(String(6), unique=True, index=True)
    code_expires_at = Column(DateTime)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.PENDING, index=True)

    # Connection info
    platform = Column(String(100))
    ip_address = Column(String(45))

    # Display settings
    display_width = Column(Integer)
    display_height = Column(Integer)
    rotation = Column(Integer, default=0)
    volume = Column(Integer, default=50)

    # Monitoring
    last_seen = Column(DateTime, index=True)

    # Audit
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("OrganizationModel", back_populates="devices")
    tags = relationship("TagModel", secondary="device_tags", back_populates="devices")
    commands = relationship("DeviceCommandModel", back_populates="device", cascade="all, delete-orphan")
    logs = relationship("DeviceLogModel", back_populates="device", cascade="all, delete-orphan")
    speed_tests = relationship("DeviceSpeedTestModel", back_populates="device", cascade="all, delete-orphan")
    content_assignments = relationship("ContentAssignmentModel", back_populates="device", cascade="all, delete-orphan")

class DeviceCommandModel(Base):
    """Device command queue"""
    __tablename__ = "device_commands"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    command_type = Column(SQLEnum(CommandType), nullable=False)
    parameters = Column(JSON)
    status = Column(SQLEnum(CommandStatus), default=CommandStatus.PENDING, index=True)
    sent_at = Column(DateTime)
    executed_at = Column(DateTime)
    error_message = Column(String(500))
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    expires_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship("DeviceModel", back_populates="commands")

class DeviceLogModel(Base):
    """Device console logs"""
    __tablename__ = "device_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(10), index=True)  # info, warn, error, log
    message = Column(String(1000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    device = relationship("DeviceModel", back_populates="logs")

class DeviceSpeedTestModel(Base):
    """Network speed test results"""
    __tablename__ = "device_speed_tests"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    download_speed = Column(Integer)  # Mbps
    upload_speed = Column(Integer)    # Mbps
    latency = Column(Integer)         # ms
    jitter = Column(Integer)          # ms
    packet_loss = Column(Integer)     # percentage
    dns_server = Column(String(45))
    tested_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    device = relationship("DeviceModel", back_populates="speed_tests")

class DeviceTagModel(Base):
    """Many-to-many: devices and tags"""
    __tablename__ = "device_tags"

    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

class ContentAssignmentModel(Base):
    """Direct content assignment to device"""
    __tablename__ = "content_assignments"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    priority = Column(Integer, default=1)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    assigned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship("DeviceModel", back_populates="content_assignments")
    content = relationship("ContentModel", back_populates="device_assignments")
```

### Use Cases (Application Logic)

#### Example: `use_cases/register_device.py`
```python
from datetime import datetime, timedelta
from ..domain.device import Device, DeviceType, DeviceStatus
from ..domain.interfaces import IDeviceRepository

class RegisterDeviceUseCase:
    """Register new device - generates activation code"""

    def __init__(self, device_repo: IDeviceRepository):
        self.device_repo = device_repo

    def execute(
        self,
        organization_id: int,
        device_name: str,
        device_type: DeviceType,
        platform: str = None,
        ip_address: str = None,
        display_width: int = None,
        display_height: int = None
    ) -> Device:
        """
        Register device with activation code

        Returns: Device with 6-digit activation code (10-min expiry)
        """
        # Create device entity
        device = Device(
            id=None,
            organization_id=organization_id,
            device_name=device_name,
            device_type=device_type,
            activation_code=None,
            code_expires_at=None,
            status=DeviceStatus.PENDING,
            platform=platform,
            ip_address=ip_address,
            display_width=display_width,
            display_height=display_height,
        )

        # Generate activation code
        device.activation_code = device.generate_activation_code()
        device.code_expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Save to database
        created_device = self.device_repo.create(device)

        return created_device
```

#### Example: `use_cases/get_device_content.py`
```python
from typing import List
from ..domain.interfaces import IDeviceRepository
from services.content.domain.content import Content

class GetDeviceContentUseCase:
    """Get device content (3-tier priority resolution)"""

    def __init__(
        self,
        device_repo: IDeviceRepository,
        content_repo: IContentRepository,
        tag_repo: ITagRepository,
        playlist_repo: IPlaylistRepository
    ):
        self.device_repo = device_repo
        self.content_repo = content_repo
        self.tag_repo = tag_repo
        self.playlist_repo = playlist_repo

    def execute(self, device_id: int, organization_id: int) -> List[Content]:
        """
        Resolve content for device using 3-tier priority:
        1. Direct content assignments (highest priority)
        2. Tag-based content assignments
        3. Playlist-based content

        Returns: List of Content sorted by priority
        """
        # Get device
        device = self.device_repo.get_by_id(device_id, organization_id)
        if not device:
            raise ValueError("Device not found")

        content_list = []

        # Priority 1: Direct assignments
        direct_content = self.content_repo.get_assigned_to_device(device_id, organization_id)
        content_list.extend([(c, 1) for c in direct_content])  # (content, priority)

        # Priority 2: Tag-based assignments
        device_tags = self.tag_repo.get_for_device(device_id, organization_id)
        for tag in device_tags:
            tag_content = self.content_repo.get_assigned_to_tag(tag.id, organization_id)
            content_list.extend([(c, 2) for c in tag_content])

        # Priority 3: Playlist assignments
        device_playlists = self.playlist_repo.get_assigned_to_device(device_id, organization_id)
        for playlist in device_playlists:
            playlist_content = self.content_repo.get_in_playlist(playlist.id, organization_id)
            content_list.extend([(c, 3) for c in playlist_content])

        # Remove duplicates (keep highest priority)
        seen = {}
        for content, priority in content_list:
            if content.id not in seen or priority < seen[content.id][1]:
                seen[content.id] = (content, priority)

        # Sort by priority
        sorted_content = sorted(seen.values(), key=lambda x: x[1])

        return [c for c, _ in sorted_content]
```

### DTOs (Request/Response Schemas)

#### `dtos.py`
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DeviceType(str, Enum):
    TV = "tv"
    MONITOR = "monitor"

class DeviceStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

# === Registration ===
class RegisterDeviceRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=255)
    device_type: DeviceType
    platform: Optional[str] = None
    ip_address: Optional[str] = None
    display_width: Optional[int] = None
    display_height: Optional[int] = None

class ActivateDeviceRequest(BaseModel):
    activation_code: str = Field(..., min_length=6, max_length=6)

# === Update ===
class UpdateDeviceRequest(BaseModel):
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[DeviceStatus] = None
    rotation: Optional[int] = Field(None, ge=0, le=270)
    volume: Optional[int] = Field(None, ge=0, le=100)

# === Content Assignment ===
class AssignContentRequest(BaseModel):
    content_ids: List[int]

class AssignTagsRequest(BaseModel):
    tag_ids: List[int]

# === Commands ===
class SendCommandRequest(BaseModel):
    command_type: str  # reset, refresh, reload, speed_test
    parameters: Optional[dict] = None

# === Logs ===
class CreateDeviceLogRequest(BaseModel):
    level: str  # info, warn, error, log
    message: str = Field(..., max_length=1000)

# === Responses ===
class DeviceResponse(BaseModel):
    id: int
    organization_id: int
    device_name: str
    device_type: DeviceType
    activation_code: Optional[str]
    code_expires_at: Optional[datetime]
    status: DeviceStatus
    platform: Optional[str]
    ip_address: Optional[str]
    display_width: Optional[int]
    display_height: Optional[int]
    rotation: int
    volume: int
    last_seen: Optional[datetime]
    is_online: bool
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DeviceListResponse(BaseModel):
    total: int
    items: List[DeviceResponse]

class DeviceCommandResponse(BaseModel):
    id: int
    device_id: int
    command_type: str
    parameters: Optional[dict]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceLogResponse(BaseModel):
    id: int
    device_id: int
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

class DeviceContentResponse(BaseModel):
    content_id: int
    content_name: str
    content_type: str
    file_path: str
    duration: int
    priority: int  # 1=direct, 2=tag, 3=playlist
    assigned_via: str  # "direct", "tag", "playlist"
```

### Routes (FastAPI Endpoints)

#### `routes.py`
```python
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from .dtos import *
from .use_cases import *
from shared.responses import success_response, error_response
from shared.database import get_session

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])

# === Registration & Activation ===
@router.post("/register", response_model=DeviceResponse)
async def register_device(
    request: RegisterDeviceRequest,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: RegisterDeviceUseCase = Depends(get_register_device_use_case)
):
    """Register new device - generates activation code"""
    device = use_case.execute(
        organization_id=x_organization_id,
        device_name=request.device_name,
        device_type=request.device_type,
        platform=request.platform,
        ip_address=request.ip_address,
        display_width=request.display_width,
        display_height=request.display_height
    )
    return success_response(device)

@router.post("/activate", response_model=DeviceResponse)
async def activate_device(
    request: ActivateDeviceRequest,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    user_id: int = Depends(get_current_user_id),
    use_case: ActivateDeviceUseCase = Depends(get_activate_device_use_case)
):
    """Activate pending device (admin only)"""
    device = use_case.execute(
        activation_code=request.activation_code,
        organization_id=x_organization_id,
        user_id=user_id
    )
    return success_response(device)

# === CRUD ===
@router.get("", response_model=DeviceListResponse)
async def list_devices(
    status: Optional[DeviceStatus] = None,
    skip: int = 0,
    limit: int = 100,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: ListDevicesUseCase = Depends(get_list_devices_use_case)
):
    """List devices with filters"""
    items, total = use_case.execute(
        organization_id=x_organization_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return success_response({"total": total, "items": items})

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: GetDeviceUseCase = Depends(get_device_use_case)
):
    """Get device by ID"""
    device = use_case.execute(device_id, x_organization_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return success_response(device)

@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    request: UpdateDeviceRequest,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    user_id: int = Depends(get_current_user_id),
    use_case: UpdateDeviceUseCase = Depends(get_update_device_use_case)
):
    """Update device settings"""
    device = use_case.execute(
        device_id=device_id,
        organization_id=x_organization_id,
        user_id=user_id,
        **request.dict(exclude_unset=True)
    )
    return success_response(device)

@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    user_id: int = Depends(get_current_user_id),
    use_case: DeleteDeviceUseCase = Depends(get_delete_device_use_case)
):
    """Delete device (hard delete)"""
    success = use_case.execute(device_id, x_organization_id, user_id)
    return success_response({"deleted": success})

# === Monitoring ===
@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: int,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: ProcessHeartbeatUseCase = Depends(get_process_heartbeat_use_case)
):
    """Device heartbeat (updates last_seen)"""
    success = use_case.execute(device_id, x_organization_id)
    return success_response({"heartbeat_recorded": success})

# === Content Assignment ===
@router.post("/{device_id}/assign-content")
async def assign_content(
    device_id: int,
    request: AssignContentRequest,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    user_id: int = Depends(get_current_user_id),
    use_case: AssignContentUseCase = Depends(get_assign_content_use_case)
):
    """Assign content directly to device"""
    result = use_case.execute(
        device_id=device_id,
        organization_id=x_organization_id,
        content_ids=request.content_ids,
        user_id=user_id
    )
    return success_response(result)

@router.get("/{device_id}/content", response_model=List[DeviceContentResponse])
async def get_device_content(
    device_id: int,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: GetDeviceContentUseCase = Depends(get_device_content_use_case)
):
    """Get device content (3-tier resolution)"""
    content = use_case.execute(device_id, x_organization_id)
    return success_response(content)

# === Remote Management ===
@router.post("/{device_id}/commands")
async def send_command(
    device_id: int,
    request: SendCommandRequest,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    user_id: int = Depends(get_current_user_id),
    use_case: SendCommandUseCase = Depends(get_send_command_use_case)
):
    """Send command to device"""
    command = use_case.execute(
        device_id=device_id,
        organization_id=x_organization_id,
        command_type=request.command_type,
        parameters=request.parameters,
        user_id=user_id
    )
    return success_response(command)

@router.get("/{device_id}/commands/pending", response_model=List[DeviceCommandResponse])
async def get_pending_commands(
    device_id: int,
    use_case: GetPendingCommandsUseCase = Depends(get_pending_commands_use_case)
):
    """Get pending commands for device (polled by device)"""
    commands = use_case.execute(device_id)
    return success_response(commands)

# === Logs ===
@router.post("/{device_id}/logs")
async def create_device_log(
    device_id: int,
    request: CreateDeviceLogRequest,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: CreateDeviceLogUseCase = Depends(get_create_log_use_case)
):
    """Create device log entry"""
    log = use_case.execute(
        device_id=device_id,
        organization_id=x_organization_id,
        level=request.level,
        message=request.message
    )
    return success_response(log)

@router.get("/{device_id}/logs", response_model=List[DeviceLogResponse])
async def get_device_logs(
    device_id: int,
    level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    x_organization_id: int = Header(..., alias="X-Organization-Id"),
    use_case: GetDeviceLogsUseCase = Depends(get_device_logs_use_case)
):
    """Get device logs with filters"""
    logs, total = use_case.execute(
        device_id=device_id,
        organization_id=x_organization_id,
        level=level,
        skip=skip,
        limit=limit
    )
    return success_response({"total": total, "items": logs})
```

---

## Frontend Implementation

**Location:** `cms-vite/src/features/devices/`

### Structure (Feature-based Architecture)

```
features/devices/
├── components/
│   ├── DeviceTable.tsx           # Main device list table
│   ├── DeviceTableRow.tsx        # Memoized row component
│   ├── PendingDeviceCard.tsx     # Pending device approval card
│   ├── DeviceStatusBadge.tsx     # Online/offline indicator
│   ├── DeviceDetailModal.tsx     # Comprehensive device dashboard
│   ├── DeviceEditModal.tsx       # Settings & configuration
│   ├── DeviceLogsModal.tsx       # Real-time log viewer
│   ├── DeviceAssignmentModal.tsx # Content/tag/playlist assignment
│   ├── SpeedHistoryModal.tsx     # Speed test history
│   └── DeviceActionsMenu.tsx     # Action dropdown (kebab menu)
├── hooks/
│   ├── useDevice.ts              # React Query hooks (CRUD)
│   ├── useDeviceContent.ts       # Content assignment hooks
│   ├── useDeviceCommands.ts      # Remote command hooks
│   ├── useDeviceLogs.ts          # Log retrieval hooks
│   └── useDeviceMonitoring.ts    # Real-time status hooks
├── services/
│   └── deviceApi.ts              # API client (21 endpoints)
└── types/
    └── device.ts                 # TypeScript types
```

### Components

#### `components/DeviceTable.tsx`
```typescript
/**
 * Device Table Component
 *
 * Features:
 * - Auto-refresh every 5 seconds
 * - Status filtering (all, pending, active, inactive)
 * - Search by name/IP
 * - Sort by name, last_seen
 * - Action menu per device
 * - Sticky header
 */

import { useState, useEffect } from 'react';
import { useDeviceList } from '../hooks/useDevice';
import DeviceTableRow from './DeviceTableRow';
import DeviceStatusBadge from './DeviceStatusBadge';
import { Filter, Search, RefreshCw } from 'lucide-react';

export default function DeviceTable() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch devices
  const { data, isLoading, refetch } = useDeviceList({
    status: statusFilter !== 'all' ? statusFilter : undefined,
  });

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      refetch();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, refetch]);

  // Filter devices by search query
  const filteredDevices = data?.items.filter(device =>
    device.device_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    device.ip_address?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="space-y-4">
      {/* Filters & Search */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All Devices</option>
            <option value="pending">Pending</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        <div className="flex items-center gap-2 flex-1 max-w-md">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search devices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-lg"
          />
        </div>

        <button
          onClick={() => refetch()}
          className="px-4 py-2 flex items-center gap-2 border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Device Table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Device Name</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Platform</th>
              <th className="px-4 py-3 text-left">IP Address</th>
              <th className="px-4 py-3 text-left">Last Seen</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-gray-500">
                  Loading devices...
                </td>
              </tr>
            ) : filteredDevices.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-gray-500">
                  No devices found
                </td>
              </tr>
            ) : (
              filteredDevices.map((device) => (
                <DeviceTableRow key={device.id} device={device} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

#### `components/DeviceDetailModal.tsx`
```typescript
/**
 * Device Detail Modal
 *
 * Comprehensive device dashboard with:
 * - Online/offline status indicator
 * - Quick actions (logs, speed test, commands)
 * - Tags section
 * - Playlists section
 * - Content section (direct + inherited)
 * - Device info block
 * - Speed history chart
 */

import { useState } from 'react';
import { useDevice, useDeviceContent } from '../hooks/useDevice';
import { useSendCommand } from '../hooks/useDeviceCommands';
import { X, Activity, Zap, Terminal, Settings } from 'lucide-react';
import DeviceStatusBadge from './DeviceStatusBadge';
import DeviceLogsModal from './DeviceLogsModal';
import SpeedHistoryModal from './SpeedHistoryModal';

interface DeviceDetailModalProps {
  deviceId: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function DeviceDetailModal({
  deviceId,
  isOpen,
  onClose
}: DeviceDetailModalProps) {
  const [showLogs, setShowLogs] = useState(false);
  const [showSpeedHistory, setShowSpeedHistory] = useState(false);

  const { data: device } = useDevice(deviceId, isOpen);
  const { data: content } = useDeviceContent(deviceId, isOpen);
  const sendCommand = useSendCommand();

  if (!isOpen || !device) return null;

  const handleCommand = async (commandType: string) => {
    try {
      await sendCommand.mutateAsync({
        deviceId,
        commandType,
      });
    } catch (error) {
      // Error handled by hook
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">{device.device_name}</h2>
              <div className="flex items-center gap-2 mt-1">
                <DeviceStatusBadge
                  isOnline={device.is_online}
                  lastSeen={device.last_seen}
                />
              </div>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Quick Actions */}
            <div className="grid grid-cols-4 gap-2">
              <button
                onClick={() => setShowLogs(true)}
                className="p-3 border rounded-lg hover:bg-gray-50 flex flex-col items-center gap-2"
              >
                <Terminal className="w-5 h-5" />
                <span className="text-sm">Logs</span>
              </button>
              <button
                onClick={() => handleCommand('speed_test')}
                className="p-3 border rounded-lg hover:bg-gray-50 flex flex-col items-center gap-2"
                disabled={sendCommand.isPending}
              >
                <Zap className="w-5 h-5" />
                <span className="text-sm">Speed Test</span>
              </button>
              <button
                onClick={() => setShowSpeedHistory(true)}
                className="p-3 border rounded-lg hover:bg-gray-50 flex flex-col items-center gap-2"
              >
                <Activity className="w-5 h-5" />
                <span className="text-sm">History</span>
              </button>
              <button
                onClick={() => handleCommand('refresh')}
                className="p-3 border rounded-lg hover:bg-gray-50 flex flex-col items-center gap-2"
                disabled={sendCommand.isPending}
              >
                <Settings className="w-5 h-5" />
                <span className="text-sm">Refresh</span>
              </button>
            </div>

            {/* Device Info */}
            <div className="border rounded-lg p-4 space-y-2">
              <h3 className="font-semibold mb-2">Device Information</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-gray-500">Type:</div>
                <div className="font-medium">{device.device_type}</div>

                <div className="text-gray-500">Platform:</div>
                <div className="font-medium">{device.platform || 'N/A'}</div>

                <div className="text-gray-500">IP Address:</div>
                <div className="font-medium">{device.ip_address || 'N/A'}</div>

                <div className="text-gray-500">Resolution:</div>
                <div className="font-medium">
                  {device.display_width && device.display_height
                    ? `${device.display_width}x${device.display_height}`
                    : 'N/A'}
                </div>

                <div className="text-gray-500">Rotation:</div>
                <div className="font-medium">{device.rotation}°</div>

                <div className="text-gray-500">Volume:</div>
                <div className="font-medium">{device.volume}%</div>
              </div>
            </div>

            {/* Content Section */}
            <div className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">
                Assigned Content ({content?.length || 0})
              </h3>
              {content && content.length > 0 ? (
                <div className="space-y-2">
                  {content.map((item) => (
                    <div
                      key={item.content_id}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div>
                        <p className="font-medium">{item.content_name}</p>
                        <p className="text-sm text-gray-500">
                          {item.content_type} • via {item.assigned_via}
                        </p>
                      </div>
                      <span className="text-sm text-gray-500">
                        Priority: {item.priority}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No content assigned</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sub-modals */}
      <DeviceLogsModal
        deviceId={deviceId}
        isOpen={showLogs}
        onClose={() => setShowLogs(false)}
      />
      <SpeedHistoryModal
        deviceId={deviceId}
        isOpen={showSpeedHistory}
        onClose={() => setShowSpeedHistory(false)}
      />
    </>
  );
}
```

### Hooks (React Query)

#### `hooks/useDevice.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deviceApi } from '../services/deviceApi';
import { toast } from 'sonner';

// List devices
export function useDeviceList(filters?: {
  status?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['devices', 'list', filters],
    queryFn: () => deviceApi.list(filters),
    staleTime: 30000, // 30 seconds
  });
}

// Get single device
export function useDevice(deviceId: number, enabled: boolean = true) {
  return useQuery({
    queryKey: ['devices', deviceId],
    queryFn: () => deviceApi.get(deviceId),
    enabled,
  });
}

// Activate device
export function useActivateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deviceApi.activate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      toast.success('Device activated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to activate device');
    },
  });
}

// Update device
export function useUpdateDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      deviceApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['devices', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['devices', 'list'] });
      toast.success('Device updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update device');
    },
  });
}

// Delete device
export function useDeleteDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deviceApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      toast.success('Device deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to delete device');
    },
  });
}

// Release device (reset to pending)
export function useReleaseDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deviceApi.release,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      toast.success('Device released - new activation code generated');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to release device');
    },
  });
}
```

#### `hooks/useDeviceContent.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { deviceApi } from '../services/deviceApi';
import { toast } from 'sonner';

// Get device content (3-tier resolution)
export function useDeviceContent(deviceId: number, enabled: boolean = true) {
  return useQuery({
    queryKey: ['devices', deviceId, 'content'],
    queryFn: () => deviceApi.getContent(deviceId),
    enabled,
  });
}

// Assign content directly to device
export function useAssignContent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, contentIds }: { deviceId: number; contentIds: number[] }) =>
      deviceApi.assignContent(deviceId, { content_ids: contentIds }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['devices', variables.deviceId, 'content'] });
      toast.success('Content assigned successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to assign content');
    },
  });
}

// Assign tags to device
export function useAssignTags() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ deviceId, tagIds }: { deviceId: number; tagIds: number[] }) =>
      deviceApi.assignTags(deviceId, { tag_ids: tagIds }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['devices', variables.deviceId] });
      queryClient.invalidateQueries({ queryKey: ['devices', variables.deviceId, 'content'] });
      toast.success('Tags assigned successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to assign tags');
    },
  });
}
```

### Services (API Client)

#### `services/deviceApi.ts`
```typescript
import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

export const deviceApi = {
  // === Registration & Activation ===
  register: async (data: RegisterDeviceRequest) => {
    const response = await apiClient.post(API_ENDPOINTS.DEVICES.REGISTER, data);
    return response.data.data;
  },

  activate: async (activationCode: string) => {
    const response = await apiClient.post(API_ENDPOINTS.DEVICES.ACTIVATE, {
      activation_code: activationCode,
    });
    return response.data.data;
  },

  // === CRUD ===
  list: async (filters?: { status?: string; skip?: number; limit?: number }) => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.skip) params.append('skip', String(filters.skip));
    if (filters?.limit) params.append('limit', String(filters.limit));

    const url = `${API_ENDPOINTS.DEVICES.LIST}${params.toString() ? `?${params}` : ''}`;
    const response = await apiClient.get(url);
    return response.data.data;
  },

  get: async (deviceId: number) => {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GET(deviceId));
    return response.data.data;
  },

  update: async (deviceId: number, data: UpdateDeviceRequest) => {
    const response = await apiClient.patch(API_ENDPOINTS.DEVICES.UPDATE(deviceId), data);
    return response.data.data;
  },

  delete: async (deviceId: number) => {
    const response = await apiClient.delete(API_ENDPOINTS.DEVICES.DELETE(deviceId));
    return response.data.data;
  },

  release: async (deviceId: number) => {
    const response = await apiClient.post(API_ENDPOINTS.DEVICES.RELEASE(deviceId));
    return response.data.data;
  },

  // === Content Assignment ===
  getContent: async (deviceId: number) => {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GET_CONTENT(deviceId));
    return response.data.data;
  },

  assignContent: async (deviceId: number, data: { content_ids: number[] }) => {
    const response = await apiClient.post(
      API_ENDPOINTS.DEVICES.ASSIGN_CONTENT(deviceId),
      data
    );
    return response.data.data;
  },

  assignTags: async (deviceId: number, data: { tag_ids: number[] }) => {
    const response = await apiClient.post(
      API_ENDPOINTS.DEVICES.ASSIGN_TAGS(deviceId),
      data
    );
    return response.data.data;
  },

  // === Remote Management ===
  sendCommand: async (deviceId: number, data: { command_type: string; parameters?: any }) => {
    const response = await apiClient.post(
      API_ENDPOINTS.DEVICES.SEND_COMMAND(deviceId),
      data
    );
    return response.data.data;
  },

  getPendingCommands: async (deviceId: number) => {
    const response = await apiClient.get(
      API_ENDPOINTS.DEVICES.GET_PENDING_COMMANDS(deviceId)
    );
    return response.data.data;
  },

  // === Logs ===
  createLog: async (deviceId: number, data: { level: string; message: string }) => {
    const response = await apiClient.post(
      API_ENDPOINTS.DEVICES.CREATE_LOG(deviceId),
      data
    );
    return response.data.data;
  },

  getLogs: async (
    deviceId: number,
    filters?: { level?: string; skip?: number; limit?: number }
  ) => {
    const params = new URLSearchParams();
    if (filters?.level) params.append('level', filters.level);
    if (filters?.skip) params.append('skip', String(filters.skip));
    if (filters?.limit) params.append('limit', String(filters.limit));

    const url = `${API_ENDPOINTS.DEVICES.GET_LOGS(deviceId)}${
      params.toString() ? `?${params}` : ''
    }`;
    const response = await apiClient.get(url);
    return response.data.data;
  },

  // === Speed Test ===
  runSpeedTest: async (deviceId: number) => {
    const response = await apiClient.post(API_ENDPOINTS.DEVICES.SPEED_TEST(deviceId));
    return response.data.data;
  },

  getSpeedHistory: async (deviceId: number, limit?: number) => {
    const url = `${API_ENDPOINTS.DEVICES.SPEED_HISTORY(deviceId)}${
      limit ? `?limit=${limit}` : ''
    }`;
    const response = await apiClient.get(url);
    return response.data.data;
  },
};
```

---

## Database Schema

**Migration File:** `backend-python/migrations/006_create_device_tables.sql`

```sql
-- ========================================
-- DEVICE MANAGEMENT TABLES
-- Migration 006: Device registration, monitoring, and management
-- ========================================

-- Main device table
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('tv', 'monitor')),
    activation_code VARCHAR(6) UNIQUE,
    code_expires_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'inactive', 'maintenance')),

    -- Connection info
    platform VARCHAR(100),
    ip_address VARCHAR(45),

    -- Display settings
    display_width INTEGER,
    display_height INTEGER,
    rotation INTEGER DEFAULT 0 CHECK (rotation IN (0, 90, 180, 270)),
    volume INTEGER DEFAULT 50 CHECK (volume >= 0 AND volume <= 100),

    -- Monitoring
    last_seen TIMESTAMP,

    -- Audit
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_devices_org (organization_id),
    INDEX idx_devices_status (status),
    INDEX idx_devices_code (activation_code),
    INDEX idx_devices_last_seen (last_seen)
);

-- Device commands (remote management queue)
CREATE TABLE IF NOT EXISTS device_commands (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    command_type VARCHAR(50) NOT NULL CHECK (command_type IN ('reset', 'refresh', 'reload', 'speed_test', 'update_content')),
    parameters JSON,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'executed', 'failed', 'expired')),
    sent_at TIMESTAMP,
    executed_at TIMESTAMP,
    error_message VARCHAR(500),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_commands_device (device_id),
    INDEX idx_commands_status (status),
    INDEX idx_commands_expires (expires_at)
);

-- Device console logs
CREATE TABLE IF NOT EXISTS device_logs (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    level VARCHAR(10) NOT NULL CHECK (level IN ('info', 'warn', 'error', 'log')),
    message VARCHAR(1000) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_logs_device (device_id),
    INDEX idx_logs_level (level),
    INDEX idx_logs_timestamp (timestamp)
);

-- Device speed test results
CREATE TABLE IF NOT EXISTS device_speed_tests (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    download_speed INTEGER,  -- Mbps
    upload_speed INTEGER,    -- Mbps
    latency INTEGER,         -- ms
    jitter INTEGER,          -- ms
    packet_loss INTEGER,     -- percentage
    dns_server VARCHAR(45),
    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_speed_device (device_id),
    INDEX idx_speed_tested (tested_at)
);

-- Device-Tag many-to-many
CREATE TABLE IF NOT EXISTS device_tags (
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    PRIMARY KEY (device_id, tag_id),
    INDEX idx_device_tags_device (device_id),
    INDEX idx_device_tags_tag (tag_id)
);

-- Direct content assignment to device
CREATE TABLE IF NOT EXISTS content_assignments (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 1,
    assigned_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_content_assign_device (device_id),
    INDEX idx_content_assign_content (content_id),
    INDEX idx_content_assign_org (organization_id)
);

-- Playlist-Device assignment (already exists in playlist tables)
-- But we'll add index for better performance
CREATE INDEX IF NOT EXISTS idx_playlist_devices_device ON playlist_devices(device_id);

-- ========================================
-- SAMPLE DATA (Development only)
-- ========================================
-- INSERT INTO devices (organization_id, device_name, device_type, status, platform, ip_address)
-- VALUES (1, 'Lobby TV', 'tv', 'active', 'WebOS 6.0', '192.168.1.100');
```

---

## Integration Points

### 1. With Auth Service

**Integration:**
- Device JWT authentication (30-day tokens)
- User tracking (created_by, updated_by)
- Organization filtering on all queries

**Implementation:**
```python
# In device routes.py
from services.auth.use_cases.authenticate_device import AuthenticateDeviceUseCase

@router.post("/auth/device")
async def authenticate_device(
    activation_code: str,
    use_case: AuthenticateDeviceUseCase = Depends(...)
):
    """Authenticate device and generate JWT token"""
    token = use_case.execute(activation_code)
    return {"token": token}
```

### 2. With Organization Service

**Integration:**
- All devices belong to organization
- Organization PIN used in registration
- Multi-tenant isolation (organization_id filter)

**Database FK:**
```sql
organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE
```

### 3. With Content Service

**Integration:**
- Direct content assignment to device
- Content resolution (3-tier priority)
- Content preview on device

**Shared Tables:**
- `content_assignments` - Direct device-content relationship

### 4. With Playlist Service

**Integration:**
- Playlist assignment to device
- Playlist content playback
- Priority-based scheduling

**Shared Tables:**
- `playlist_devices` - Device-playlist assignment

### 5. With Tag Service

**Integration:**
- Tag-based device grouping
- Bulk content assignment via tags
- Content inheritance from tags

**Shared Tables:**
- `device_tags` - Many-to-many relationship

### 6. With Audit Service

**Integration:**
- All device operations logged
- User tracking for accountability
- Change history

**Audit Events:**
- `device.register`, `device.activate`, `device.update`, `device.delete`
- `device.assign_content`, `device.assign_tag`, `device.command_sent`

**Implementation:**
```python
# In device use cases
from shared.logging import AuditLogger

audit_logger = AuditLogger(create_audit_log_use_case)

# After device activation
audit_logger.log_action(
    user_id=user.id,
    organization_id=device.organization_id,
    action="device.activate",
    resource_type="device",
    resource_id=device.id,
    details={"device_name": device.device_name, "device_type": device.device_type}
)
```

---

## Implementation Phases

### Phase 1: Core Device Management (Week 1-2)

**Backend:**
- ✅ Database migration (006_create_device_tables.sql)
- ✅ Device models (repositories/models.py)
- ✅ Device entity (domain/device.py)
- ✅ Device repository (repositories/device_repo.py)
- ✅ CRUD use cases (register, activate, list, get, update, delete)
- ✅ Basic routes (registration, activation, CRUD)
- ✅ Integration with Auth (JWT tokens)
- ✅ Integration with Organization (multi-tenant filtering)

**Frontend:**
- ✅ Device types & API endpoints config
- ✅ Device API client (deviceApi.ts)
- ✅ Device React Query hooks (useDevice.ts)
- ✅ DevicesPage layout
- ✅ DeviceTable component
- ✅ DeviceTableRow component
- ✅ DeviceStatusBadge component
- ✅ Basic CRUD operations (activate, update, delete)

**Testing:**
- ✅ Device registration flow
- ✅ Device activation with code expiry
- ✅ Multi-tenant isolation (cross-org access blocked)
- ✅ Device CRUD operations

### Phase 2: Content Assignment (Week 3)

**Backend:**
- ✅ Content assignment use cases (assign_content, assign_tags)
- ✅ Content resolution use case (get_device_content with 3-tier)
- ✅ Content assignment routes
- ✅ Integration with Content service
- ✅ Integration with Tag service
- ✅ Integration with Playlist service

**Frontend:**
- ✅ DeviceAssignmentModal component
- ✅ Content assignment hooks (useDeviceContent.ts)
- ✅ DeviceDetailModal (content display)
- ✅ Content preview integration

**Testing:**
- ✅ Direct content assignment
- ✅ Tag-based content inheritance
- ✅ Playlist-based content
- ✅ Priority resolution (3-tier)

### Phase 3: Monitoring & Remote Management (Week 4)

**Backend:**
- ✅ Device command models & repository
- ✅ Command use cases (send_command, get_pending_commands)
- ✅ Heartbeat use case (process_heartbeat)
- ✅ Command routes
- ✅ Command expiration cleanup (scheduled task)

**Frontend:**
- ✅ DeviceActionsMenu component
- ✅ Remote command hooks (useDeviceCommands.ts)
- ✅ DeviceEditModal (settings)
- ✅ Real-time status monitoring hooks
- ✅ Auto-refresh (5-second interval)

**Testing:**
- ✅ Command queue system
- ✅ Heartbeat mechanism
- ✅ Online/offline detection
- ✅ Command execution flow

### Phase 4: Logs & Analytics (Week 5)

**Backend:**
- ✅ Device log models & repository
- ✅ Log use cases (create_log, get_logs)
- ✅ Speed test models & repository
- ✅ Speed test use cases (run_speed_test, get_history)
- ✅ Analytics routes

**Frontend:**
- ✅ DeviceLogsModal component (WebSocket streaming)
- ✅ SpeedHistoryModal component
- ✅ Log filtering & export
- ✅ Speed test history chart

**Testing:**
- ✅ Log creation & retrieval
- ✅ Log filtering by level
- ✅ Speed test execution
- ✅ Speed test history tracking

### Phase 5: Polish & Production (Week 6)

**Backend:**
- ✅ Performance optimization (indexes, queries)
- ✅ Error handling improvements
- ✅ API documentation (OpenAPI)
- ✅ Background tasks (cleanup, expiration)

**Frontend:**
- ✅ UI polish (animations, loading states)
- ✅ Error handling improvements
- ✅ Accessibility (ARIA labels, keyboard nav)
- ✅ Mobile responsiveness

**Testing:**
- ✅ End-to-end testing
- ✅ Performance testing (100+ devices)
- ✅ Security testing
- ✅ User acceptance testing

---

## Testing Checklist

### Backend Tests

**Device Registration:**
- [ ] Register device generates 6-digit code
- [ ] Code expires after 10 minutes
- [ ] Can't register with invalid organization
- [ ] Platform and IP detection works

**Device Activation:**
- [ ] Can activate with valid code before expiry
- [ ] Can't activate with expired code
- [ ] Can't activate same device twice
- [ ] Status changes from pending → active
- [ ] Activation code cleared after activation

**Device CRUD:**
- [ ] List devices filtered by organization
- [ ] List devices filtered by status
- [ ] Get device returns 404 for cross-org access
- [ ] Update device settings works
- [ ] Delete device cascades to related tables
- [ ] Release device generates new code

**Content Assignment:**
- [ ] Direct assignment works
- [ ] Tag-based assignment works
- [ ] Playlist assignment works
- [ ] 3-tier priority resolution correct
- [ ] Duplicates removed (highest priority kept)

**Monitoring:**
- [ ] Heartbeat updates last_seen
- [ ] is_online calculated correctly (60s timeout)
- [ ] Command queue works (pending → sent → executed)
- [ ] Expired commands cleaned up (7 days)

**Logs:**
- [ ] Log creation works
- [ ] Log filtering by level works
- [ ] Logs cascade deleted with device

**Security:**
- [ ] Multi-tenant isolation enforced
- [ ] JWT authentication required for device endpoints
- [ ] Activation code unique across all devices
- [ ] User tracking (created_by, updated_by) works

### Frontend Tests

**Device List:**
- [ ] Auto-refresh every 5 seconds
- [ ] Status filter works (all, pending, active, inactive)
- [ ] Search by name/IP works
- [ ] Sorting by columns works
- [ ] Online/offline badge shows correctly

**Device Activation:**
- [ ] Pending devices show with activation code
- [ ] Approve button works
- [ ] Activation moves device to active table
- [ ] Code expiry countdown shows

**Device Detail Modal:**
- [ ] All device info displays
- [ ] Quick actions work (logs, speed test, commands)
- [ ] Content section shows 3-tier content
- [ ] Tags section shows assigned tags
- [ ] Playlists section shows assignments

**Device Edit Modal:**
- [ ] Settings update works (rotation, volume)
- [ ] Display info shows (resolution, platform)
- [ ] Release button generates new code
- [ ] Replace device (monitor only) works

**Device Logs Modal:**
- [ ] Logs stream via WebSocket
- [ ] Log filtering by level works
- [ ] Export logs works
- [ ] Clear logs works (with confirmation)

**Content Assignment:**
- [ ] Two-column interface works
- [ ] Multi-select assignment works
- [ ] Unassignment works
- [ ] Content updates immediately

**Remote Commands:**
- [ ] Refresh command works
- [ ] Reset command works
- [ ] Speed test command works
- [ ] Command execution feedback shows

---

## API Endpoints Reference

### Device Management (21 endpoints total)

```
POST   /api/v1/devices/register               - Register new device
POST   /api/v1/devices/activate               - Activate pending device
GET    /api/v1/devices                        - List devices (filtered)
GET    /api/v1/devices/{id}                   - Get device by ID
PATCH  /api/v1/devices/{id}                   - Update device settings
DELETE /api/v1/devices/{id}                   - Delete device
POST   /api/v1/devices/{id}/release           - Release device (reset)
POST   /api/v1/devices/{id}/heartbeat         - Device heartbeat
POST   /api/v1/devices/{id}/assign-content    - Assign content directly
GET    /api/v1/devices/{id}/content           - Get device content (3-tier)
POST   /api/v1/devices/{id}/assign-tags       - Assign tags
POST   /api/v1/devices/{id}/commands          - Send command
GET    /api/v1/devices/{id}/commands/pending  - Get pending commands
POST   /api/v1/devices/{id}/logs              - Create log entry
GET    /api/v1/devices/{id}/logs              - Get device logs
POST   /api/v1/devices/{id}/speed-test        - Run speed test
GET    /api/v1/devices/{id}/speed-history     - Get speed test history
POST   /api/v1/auth/device                    - Device JWT authentication
GET    /api/v1/devices/{id}/status            - Get online status
POST   /api/v1/devices/{id}/screenshot        - Request screenshot
GET    /api/v1/devices/{id}/info              - Get detailed info
```

### Frontend Routes

```
/devices                    - Main device list page
/devices/pending            - Pending device approvals
/devices/{id}              - Device detail view
/devices/{id}/preview      - Full-screen content preview
```

---

## Summary

**Total Scope:**
- **7 Database Tables** (devices, device_commands, device_logs, device_speed_tests, device_tags, content_assignments, + integration with playlist_devices)
- **21 Backend Endpoints** (registration, CRUD, monitoring, content, logs, analytics)
- **18 Use Cases** (Clean Architecture business logic)
- **8 Frontend Screens** (list, detail, edit, logs, speed, assignment, preview)
- **11 User Workflows** (activation, assignment, monitoring, management)

**Integration:**
- ✅ Auth (JWT, user tracking)
- ✅ Organization (multi-tenancy)
- ✅ Content (assignment, 3-tier resolution)
- ✅ Playlist (scheduling, priority)
- ✅ Tag (grouping, bulk assignment)
- ✅ Audit (change tracking)

**Timeline:** 6 weeks (phased implementation)

**Ready to implement!** 🚀

---

**Next Steps:**
1. Review and approve this plan
2. Create migration file (006_create_device_tables.sql)
3. Start Phase 1: Core Device Management
4. Iterate through phases with testing at each step

