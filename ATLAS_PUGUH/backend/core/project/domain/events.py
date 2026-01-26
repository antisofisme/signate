"""
Project Domain Events

Events emitted by project operations for audit and integration.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional


@dataclass(frozen=True)
class ProjectEvent:
    """Base class for project events"""

    event_type: str
    tenant_id: UUID
    project_id: UUID
    timestamp: datetime
    actor_id: Optional[UUID] = None


@dataclass(frozen=True)
class ProjectCreatedEvent(ProjectEvent):
    """Project created"""

    name: str
    slug: str
    environment: str


@dataclass(frozen=True)
class ProjectUpdatedEvent(ProjectEvent):
    """Project updated"""

    changes: dict  # {"field": {"old": x, "new": y}}


@dataclass(frozen=True)
class ProjectDeletedEvent(ProjectEvent):
    """Project deleted"""

    name: str


@dataclass(frozen=True)
class ProjectMemberAddedEvent(ProjectEvent):
    """Member added to project"""

    user_id: UUID
    role: str


@dataclass(frozen=True)
class ProjectMemberRemovedEvent(ProjectEvent):
    """Member removed from project"""

    user_id: UUID
