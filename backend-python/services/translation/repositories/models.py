"""
Translation Models
SQLAlchemy models for multi-language translation system
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func
from shared.database import Base


class Translation(Base):
    """Translations for multi-language support"""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Entity reference
    entity_type = Column(String(50), nullable=False)  # 'content', 'playlist', 'template', 'widget'
    entity_id = Column(Integer, nullable=False)

    # Translation
    language_code = Column(String(5), nullable=False)  # 'en', 'id', 'zh', 'ja', 'ko'
    field_name = Column(String(100), nullable=False)  # 'title', 'description', 'content'
    translated_value = Column(Text, nullable=False)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'language_code', 'field_name',
                        name='uq_translations_entity_lang_field'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "language_code": self.language_code,
            "field_name": self.field_name,
            "translated_value": self.translated_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
