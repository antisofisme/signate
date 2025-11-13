"""
Translation Routes
REST API endpoints for translation management
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.auth import get_current_user, CurrentUser
from services.translation.dtos import (
    AddTranslationRequest,
    TranslationResponse,
    TranslationListResponse,
    EntityTranslationsResponse,
    BulkImportRequest,
    BulkImportResponse,
    SupportedLanguagesResponse,
    SupportedLanguage,
    OrganizationLanguagesResponse,
    TranslationStatsResponse
)
from services.translation.use_cases.add_translation import (
    add_translation_use_case,
    SUPPORTED_LANGUAGES
)
from services.translation.use_cases.get_translations import (
    get_translation_by_id_use_case,
    get_translations_use_case,
    get_entity_translations_use_case,
    get_organization_languages_use_case,
    get_translation_stats_use_case
)
from services.translation.use_cases.bulk_import import (
    bulk_import_translations_use_case,
    delete_translation_use_case,
    delete_entity_translations_use_case
)


router = APIRouter()


# ============================================================================
# Translation CRUD Endpoints
# ============================================================================

@router.post("/translations", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
def add_translation(
    request: AddTranslationRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add or update translation

    Business Rules:
    - Language code must be supported
    - Entity type must be valid (content, playlist, template, widget)
    - Automatically creates or updates translation
    - Scoped to current user's organization
    """
    return add_translation_use_case(
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )


@router.get("/translations", response_model=TranslationListResponse)
def get_translations(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[int] = Query(None, description="Filter by entity ID"),
    language_code: Optional[str] = Query(None, description="Filter by language code"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get translations with optional filters

    Supports filtering by:
    - entity_type (content, playlist, template, widget)
    - entity_id
    - language_code
    - Pagination with skip/limit
    """
    return get_translations_use_case(
        organization_id=current_user.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        language_code=language_code,
        skip=skip,
        limit=limit,
        db=db
    )


@router.get("/translations/{translation_id}", response_model=TranslationResponse)
def get_translation(
    translation_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get translation by ID"""
    return get_translation_by_id_use_case(
        translation_id=translation_id,
        organization_id=current_user.organization_id,
        db=db
    )


@router.delete("/translations/{translation_id}", status_code=status.HTTP_200_OK)
def delete_translation(
    translation_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete translation by ID"""
    return delete_translation_use_case(
        translation_id=translation_id,
        organization_id=current_user.organization_id,
        db=db
    )


# ============================================================================
# Language Support Endpoints
# ============================================================================

@router.get("/translations/languages/supported", response_model=SupportedLanguagesResponse)
def get_supported_languages():
    """
    Get list of all supported languages

    Returns language code, English name, and native name
    """
    languages = [
        SupportedLanguage(code="en", name="English", native_name="English"),
        SupportedLanguage(code="id", name="Indonesian", native_name="Bahasa Indonesia"),
        SupportedLanguage(code="zh", name="Chinese", native_name="中文"),
        SupportedLanguage(code="ja", name="Japanese", native_name="日本語"),
        SupportedLanguage(code="ko", name="Korean", native_name="한국어"),
        SupportedLanguage(code="es", name="Spanish", native_name="Español"),
        SupportedLanguage(code="fr", name="French", native_name="Français"),
        SupportedLanguage(code="de", name="German", native_name="Deutsch"),
        SupportedLanguage(code="ar", name="Arabic", native_name="العربية"),
        SupportedLanguage(code="th", name="Thai", native_name="ไทย")
    ]
    return SupportedLanguagesResponse(languages=languages)


@router.get("/translations/languages/organization", response_model=OrganizationLanguagesResponse)
def get_organization_languages(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get languages actually used by organization

    Returns list of language codes that have translations in the system
    """
    return get_organization_languages_use_case(
        organization_id=current_user.organization_id,
        db=db
    )


# ============================================================================

# Entity Translation Endpoints
# ============================================================================

@router.get("/translations/{entity_type}/{entity_id}", response_model=EntityTranslationsResponse)
def get_entity_translations(
    entity_type: str,
    entity_id: int,
    language_code: str = Query(..., description="Language code (en, id, zh, etc.)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all translations for specific entity and language

    Returns a dictionary of field_name -> translated_value
    Example: {"title": "Welcome", "description": "Welcome message"}
    """
    return get_entity_translations_use_case(
        entity_type=entity_type,
        entity_id=entity_id,
        language_code=language_code,
        organization_id=current_user.organization_id,
        db=db
    )


@router.delete("/translations/{entity_type}/{entity_id}", status_code=status.HTTP_200_OK)
def delete_entity_translations(
    entity_type: str,
    entity_id: int,
    language_code: Optional[str] = Query(None, description="Delete only specific language (optional)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete all translations for entity

    If language_code provided: deletes only that language
    If language_code omitted: deletes ALL translations for entity
    """
    return delete_entity_translations_use_case(
        entity_type=entity_type,
        entity_id=entity_id,
        organization_id=current_user.organization_id,
        language_code=language_code,
        db=db
    )


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/translations/bulk", response_model=BulkImportResponse)
def bulk_import_translations(
    request: BulkImportRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk import translations

    Business Rules:
    - Validates each translation before import
    - Continues on error and reports failed items
    - Returns count of imported, updated, and failed translations
    - Existing translations are updated, new ones are created
    """
    return bulk_import_translations_use_case(
        organization_id=current_user.organization_id,
        request=request,
        db=db
    )


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/translations/stats", response_model=TranslationStatsResponse)
def get_translation_stats(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get translation statistics for organization

    Returns:
    - Total translation count
    - Number of languages used
    - Count by entity type (content, playlist, template, widget)
    - Completion rate per language
    """
    return get_translation_stats_use_case(
        organization_id=current_user.organization_id,
        db=db
    )
