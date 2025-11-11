"""
Bulk Import Translations Use Case
Business logic for bulk importing translations
"""

from sqlalchemy.orm import Session

from services.translation.dtos import BulkImportRequest, BulkImportResponse, AddTranslationRequest
from services.translation.repositories.translation_repo import TranslationRepository
from services.translation.use_cases.add_translation import (
    add_translation_use_case,
    SUPPORTED_LANGUAGES,
    VALID_ENTITY_TYPES
)


def bulk_import_translations_use_case(
    organization_id: int,
    request: BulkImportRequest,
    db: Session
) -> BulkImportResponse:
    """
    Bulk import translations

    Business Rules:
    - Validates each translation before import
    - Continues on error and reports failed items
    - Returns count of imported, updated, and failed translations
    """
    imported = 0
    updated = 0
    failed = 0
    errors = []

    repo = TranslationRepository(db)

    for idx, item in enumerate(request.translations):
        try:
            # Validate entity type
            if item.entity_type not in VALID_ENTITY_TYPES:
                raise ValueError(f"Invalid entity_type: {item.entity_type}")

            # Validate language code
            if item.language_code not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported language code: {item.language_code}")

            # Check if translation already exists
            exists = repo.check_translation_exists(
                organization_id=organization_id,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                language_code=item.language_code,
                field_name=item.field_name
            )

            # Add or update translation
            translation_request = AddTranslationRequest(
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                language_code=item.language_code,
                field_name=item.field_name,
                translated_value=item.translated_value
            )

            repo.add_translation(organization_id, translation_request)

            if exists:
                updated += 1
            else:
                imported += 1

        except Exception as e:
            failed += 1
            errors.append(f"Item {idx + 1}: {str(e)}")

    return BulkImportResponse(
        imported=imported,
        updated=updated,
        failed=failed,
        errors=errors
    )


def delete_translation_use_case(
    translation_id: int,
    organization_id: int,
    db: Session
) -> dict:
    """Delete translation"""
    repo = TranslationRepository(db)

    # Check if translation exists
    translation = repo.get_translation_by_id(translation_id, organization_id)
    if not translation:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation with id {translation_id} not found"
        )

    # Delete translation
    success = repo.delete_translation(translation_id, organization_id)
    if not success:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete translation"
        )

    return {"message": f"Translation {translation_id} deleted successfully"}


def delete_entity_translations_use_case(
    entity_type: str,
    entity_id: int,
    organization_id: int,
    language_code: str = None,
    db: Session = None
) -> dict:
    """Delete all translations for entity"""
    repo = TranslationRepository(db)

    count = repo.delete_entity_translations(
        organization_id=organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        language_code=language_code
    )

    message = f"Deleted {count} translations for {entity_type} {entity_id}"
    if language_code:
        message += f" (language: {language_code})"

    return {"message": message, "deleted_count": count}
