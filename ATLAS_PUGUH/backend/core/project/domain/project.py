"""
Project Domain Entity
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
import re


class ProjectEnvironment(str, Enum):
    """Project deployment environment"""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"

    @property
    def is_production(self) -> bool:
        return self == ProjectEnvironment.PRODUCTION


@dataclass
class Project:
    """
    Project Entity

    Projects provide resource isolation within a tenant.
    Rules can be tenant-level (shared) or project-level (isolated).
    Decisions and Workflows are always project-scoped.
    """

    project_id: UUID
    tenant_id: UUID

    # Identification
    name: str
    slug: str
    description: Optional[str] = None

    # Environment
    environment: ProjectEnvironment = ProjectEnvironment.DEVELOPMENT

    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)

    # Status
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    # Audit
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-safe slug from name"""
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        return slug[:100]  # Max 100 chars

    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate slug format"""
        return bool(re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", slug))

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        environment: Optional[ProjectEnvironment] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update project fields"""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if environment is not None:
            self.environment = environment
        if settings is not None:
            self.settings = settings
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete the project"""
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the project"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the project"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value"""
        self.settings[key] = value
        self.updated_at = datetime.utcnow()

    @property
    def display_name(self) -> str:
        """Display name with environment badge"""
        if self.environment == ProjectEnvironment.PRODUCTION:
            return self.name
        return f"{self.name} ({self.environment.value})"
