"""
Get Translations Use Case
Business logic for retrieving translations
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.translation.dtos import (
    TranslationResponse,
    TranslationListResponse,
    EntityTranslationsResponse,
    OrganizationLanguagesResponse,
    TranslationStatsResponse
)
from services.translation.repositories.translation_repo import TranslationRepository


def get_translation_by_id_use_case(
    translation_id: int,
    organization_id: int,
    db: Session
) -> TranslationResponse:
    """Get translation by ID"""
    repo = TranslationRepository(db)

    translation = repo.get_translation_by_id(translation_id, organization_id)
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation with id {translation_id} not found"
        )

    return TranslationResponse.model_validate(translation)


def get_translations_use_case(
    organization_id: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    language_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = None
) -> TranslationListResponse:
    """Get translations with filters"""
    repo = TranslationRepository(db)

    translations, total = repo.get_translations(
        organization_id=organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        language_code=language_code,
        skip=skip,
        limit=limit
    )

    return TranslationListResponse(
        translations=[TranslationResponse.model_validate(t) for t in translations],
        total=total
    )


def get_entity_translations_use_case(
    entity_type: str,
    entity_id: int,
    language_code: str,
    organization_id: int,
    db: Session
) -> EntityTranslationsResponse:
    """Get all translations for specific entity and language"""
    repo = TranslationRepository(db)

    translations = repo.get_entity_translations(
        organization_id=organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        language_code=language_code
    )

    return EntityTranslationsResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        language_code=language_code,
        translations=translations
    )


def get_organization_languages_use_case(
    organization_id: int,
    db: Session
) -> OrganizationLanguagesResponse:
    """Get languages used by organization"""
    repo = TranslationRepository(db)

    language_codes = repo.get_supported_languages(organization_id)

    return OrganizationLanguagesResponse(
        language_codes=language_codes,
        total=len(language_codes)
    )


def get_translation_stats_use_case(
    organization_id: int,
    db: Session
) -> TranslationStatsResponse:
    """Get translation statistics"""
    repo = TranslationRepository(db)

    stats = repo.get_translation_stats(organization_id)

    # Calculate completion rate (simplified - just percentage of translations per language)
    completion_rate = {}
    if stats["by_language"]:
        total_translations = stats["total"]
        for lang, count in stats["by_language"].items():
            completion_rate[lang] = round((count / total_translations) * 100, 2) if total_translations > 0 else 0

    return TranslationStatsResponse(
        total_translations=stats["total"],
        languages_count=len(stats["by_language"]),
        entity_types=stats["by_entity_type"],
        completion_rate=completion_rate
    )
