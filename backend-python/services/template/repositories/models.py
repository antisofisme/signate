"""
Template Models
SQLAlchemy models for template system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from shared.database import Base


class Template(Base):
    """Template definitions for dynamic content"""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Template Info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50), nullable=False)  # 'text', 'image', 'video', 'html', 'greeting'

    # Template Content
    content = Column(Text, nullable=False)  # Template content with {{variables}}
    variables = Column(JSONB)  # Variable definitions: {"guest_name": "string", "room": "string"}
    preview_data = Column(JSONB)  # Sample data for preview

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uq_templates_org_name'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "content": self.content,
            "variables": self.variables,
            "preview_data": self.preview_data,
            "is_active": self.is_active,
            "created_by": self.created_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
