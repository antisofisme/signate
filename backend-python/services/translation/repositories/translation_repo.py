"""
Translation Repository
Data access layer for translation operations
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from services.translation.repositories.models import Translation
from services.translation.dtos import AddTranslationRequest


class TranslationRepository:
    """Repository for translation data access"""

    def __init__(self, db: Session):
        self.db = db

    def add_translation(
        self,
        organization_id: int,
        request: AddTranslationRequest
    ) -> Translation:
        """Add or update translation"""
        # Check if translation exists
        translation = self.db.query(Translation).filter(
            and_(
                Translation.organization_id == organization_id,
                Translation.entity_type == request.entity_type,
                Translation.entity_id == request.entity_id,
                Translation.language_code == request.language_code,
                Translation.field_name == request.field_name
            )
        ).first()

        if translation:
            # Update existing
            translation.translated_value = request.translated_value
        else:
            # Create new
            translation = Translation(
                organization_id=organization_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                language_code=request.language_code,
                field_name=request.field_name,
                translated_value=request.translated_value
            )
            self.db.add(translation)

        self.db.commit()
        self.db.refresh(translation)
        return translation

    def get_translation_by_id(
        self,
        translation_id: int,
        organization_id: int
    ) -> Optional[Translation]:
        """Get translation by ID"""
        return self.db.query(Translation).filter(
            and_(
                Translation.id == translation_id,
                Translation.organization_id == organization_id
            )
        ).first()

    def get_translations(
        self,
        organization_id: int,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        language_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Translation], int]:
        """Get translations with filters"""
        query = self.db.query(Translation).filter(
            Translation.organization_id == organization_id
        )

        if entity_type:
            query = query.filter(Translation.entity_type == entity_type)
        if entity_id:
            query = query.filter(Translation.entity_id == entity_id)
        if language_code:
            query = query.filter(Translation.language_code == language_code)

        total = query.count()
        translations = query.order_by(Translation.created_at.desc()).offset(skip).limit(limit).all()

        return translations, total

    def get_entity_translations(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: int,
        language_code: str
    ) -> Dict[str, str]:
        """Get all translations for specific entity and language"""
        translations = self.db.query(Translation).filter(
            and_(
                Translation.organization_id == organization_id,
                Translation.entity_type == entity_type,
                Translation.entity_id == entity_id,
                Translation.language_code == language_code
            )
        ).all()

        return {
            t.field_name: t.translated_value
            for t in translations
        }

    def delete_translation(
        self,
        translation_id: int,
        organization_id: int
    ) -> bool:
        """Delete translation"""
        translation = self.get_translation_by_id(translation_id, organization_id)
        if not translation:
            return False

        self.db.delete(translation)
        self.db.commit()
        return True

    def delete_entity_translations(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: int,
        language_code: Optional[str] = None
    ) -> int:
        """Delete all translations for entity (optionally for specific language)"""
        query = self.db.query(Translation).filter(
            and_(
                Translation.organization_id == organization_id,
                Translation.entity_type == entity_type,
                Translation.entity_id == entity_id
            )
        )

        if language_code:
            query = query.filter(Translation.language_code == language_code)

        count = query.count()
        query.delete()
        self.db.commit()
        return count

    def get_supported_languages(
        self,
        organization_id: int
    ) -> List[str]:
        """Get list of language codes used by organization"""
        languages = self.db.query(Translation.language_code).filter(
            Translation.organization_id == organization_id
        ).distinct().all()

        return sorted([lang[0] for lang in languages])

    def get_translation_stats(
        self,
        organization_id: int
    ) -> Dict:
        """Get translation statistics"""
        # Total translations
        total = self.db.query(func.count(Translation.id)).filter(
            Translation.organization_id == organization_id
        ).scalar()

        # Count by entity type
        entity_counts = self.db.query(
            Translation.entity_type,
            func.count(Translation.id)
        ).filter(
            Translation.organization_id == organization_id
        ).group_by(Translation.entity_type).all()

        # Count by language
        language_counts = self.db.query(
            Translation.language_code,
            func.count(Translation.id)
        ).filter(
            Translation.organization_id == organization_id
        ).group_by(Translation.language_code).all()

        return {
            "total": total,
            "by_entity_type": dict(entity_counts),
            "by_language": dict(language_counts)
        }

    def check_translation_exists(
        self,
        organization_id: int,
        entity_type: str,
        entity_id: int,
        language_code: str,
        field_name: str
    ) -> bool:
        """Check if translation exists"""
        return self.db.query(Translation).filter(
            and_(
                Translation.organization_id == organization_id,
                Translation.entity_type == entity_type,
                Translation.entity_id == entity_id,
                Translation.language_code == language_code,
                Translation.field_name == field_name
            )
        ).first() is not None
