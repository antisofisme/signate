"""
Add Translation Use Case
Business logic for adding/updating translations
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from services.translation.dtos import AddTranslationRequest, TranslationResponse
from services.translation.repositories.translation_repo import TranslationRepository


# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'id': 'Indonesian',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ar': 'Arabic',
    'th': 'Thai'
}

# Valid entity types
VALID_ENTITY_TYPES = ['content', 'playlist', 'template', 'widget']


def add_translation_use_case(
    organization_id: int,
    request: AddTranslationRequest,
    db: Session
) -> TranslationResponse:
    """
    Add or update translation

    Business Rules:
    - Language code must be supported
    - Entity type must be valid
    - Automatically creates or updates translation
    """
    repo = TranslationRepository(db)

    # Validate entity type
    if request.entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity_type. Must be one of: {', '.join(VALID_ENTITY_TYPES)}"
        )

    # Validate language code
    if request.language_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code. Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        )

    # Add or update translation
    translation = repo.add_translation(organization_id, request)

    return TranslationResponse.model_validate(translation)
