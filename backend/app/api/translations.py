"""
Multi-Language Content Translation API
Provides content translation management with smart fallback chains
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
import io
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_optional_user
from app.core.logging import StructuredLogger
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ValidationException,
    InternalServerException,
    ConflictException
)
from app.core.cache import invalidate_by_prefix, CACHE_KEY_PREFIXES
from app.schemas.common import success_response, APIResponse
from app.schemas.translation import (
    TranslationCreate,
    TranslationUpdate,
    TranslationResponse,
    TranslationListResponse,
    BulkImportResponse,
    ContentWithTranslation,
    LanguageInfo,
    SupportedLanguagesResponse,
    TranslationStatus,
    LanguageDirection
)
from app.services.translation_service import get_translation_service, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from app.middleware.request_id import get_request_id
from app.models.user import User
from app.models.content import Content

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/content", tags=["translations"])

# Standalone router for language endpoints (no prefix)
languages_router = APIRouter(prefix="/api", tags=["languages"])


@router.post("/{content_id}/translations", response_model=APIResponse[TranslationResponse])
async def add_translation(
    request: Request,
    content_id: int,
    data: TranslationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add translation for content

    Creates a new translation or updates existing one for the specified content.

    Features:
    - Automatic language validation (ISO 639-1)
    - RTL language support (Arabic, Hebrew)
    - Overlay text for video content
    - Translation status tracking

    Request body example:
    ```json
    {
        "language": "id",
        "title": "Selamat Datang",
        "description": "Deskripsi dalam Bahasa Indonesia",
        "overlay_text": {
            "line1": "Selamat Datang",
            "line2": "di Hotel Kami"
        },
        "is_primary": false,
        "status": "approved"
    }
    ```
    """
    request_id = get_request_id(request)

    logger.info(
        "Translation add requested",
        request_id=request_id,
        content_id=content_id,
        language=data.language,
        user=current_user.username
    )

    try:
        # Verify content exists
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise NotFoundException(
                message=f"Content {content_id} not found"
            )

        # Get translation service
        service = get_translation_service(db)

        # Add translation
        translation = await service.add_translation(
            content_id=content_id,
            language=data.language,
            data=data,
            user_id=current_user.id
        )

        # Build response
        lang_info = SUPPORTED_LANGUAGES.get(data.language, {})
        response = TranslationResponse(
            id=translation['id'],
            content_id=content_id,
            language=data.language,
            title=translation['title'],
            description=translation.get('description'),
            overlay_text=translation.get('overlay_text'),
            metadata=translation.get('metadata'),
            is_primary=translation.get('is_primary', False),
            status=translation.get('status', TranslationStatus.DRAFT),
            direction=lang_info.get('direction', LanguageDirection.LTR),
            created_at=translation['created_at'],
            updated_at=translation['updated_at'],
            created_by=current_user.username
        )

        # Clear content cache
        await invalidate_by_prefix(f"{CACHE_KEY_PREFIXES['content']}{content_id}")

        logger.info(
            "Translation added successfully",
            request_id=request_id,
            content_id=content_id,
            language=data.language,
            translation_id=response.id
        )

        return success_response(
            data=response,
            message=f"Translation added for language '{data.language}'"
        )

    except ValueError as e:
        raise BadRequestException(
            message=str(e),
            details={"content_id": content_id, "language": data.language}
        )
    except Exception as e:
        logger.error(
            "Failed to add translation",
            request_id=request_id,
            content_id=content_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to add translation",
            details={"error": str(e)}
        )


@router.get("/{content_id}/translations", response_model=APIResponse[TranslationListResponse])
async def list_translations(
    request: Request,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    List all translations for content

    Returns all available translations with metadata about:
    - Available languages
    - Missing languages (suggested based on system configuration)
    - Primary language
    - Translation status

    Response includes language direction (LTR/RTL) for proper rendering.
    """
    request_id = get_request_id(request)

    logger.info(
        "Translation list requested",
        request_id=request_id,
        content_id=content_id
    )

    try:
        # Verify content exists
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise NotFoundException(
                message=f"Content {content_id} not found"
            )

        # TODO: Get actual translations from database
        # For now, return mock data
        translations = []
        available_languages = []

        # Suggest missing languages based on common hospitality languages
        suggested_languages = ['en', 'id', 'zh', 'ja', 'ar']
        missing_languages = [
            lang for lang in suggested_languages
            if lang not in available_languages
        ]

        response = TranslationListResponse(
            content_id=content_id,
            default_language=DEFAULT_LANGUAGE,
            translations=translations,
            available_languages=available_languages,
            missing_languages=missing_languages,
            total_count=len(translations)
        )

        logger.info(
            "Translations listed",
            request_id=request_id,
            content_id=content_id,
            count=len(translations)
        )

        return success_response(
            data=response,
            message=f"Found {len(translations)} translations"
        )

    except Exception as e:
        logger.error(
            "Failed to list translations",
            request_id=request_id,
            content_id=content_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to retrieve translations",
            details={"error": str(e)}
        )


@router.get("/{content_id}/translations/{language}", response_model=APIResponse[TranslationResponse])
async def get_translation(
    request: Request,
    content_id: int,
    language: str,
    use_fallback: bool = Query(True, description="Use fallback if translation not found"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get specific translation with fallback

    Retrieves translation for specified language with intelligent fallback:
    1. Requested language
    2. Language-specific fallback (e.g., ms -> id)
    3. Default language (en)
    4. Original content language
    5. Any available translation

    Query parameters:
    - use_fallback: Whether to use fallback chain (default: true)
    """
    request_id = get_request_id(request)

    logger.info(
        "Translation get requested",
        request_id=request_id,
        content_id=content_id,
        language=language,
        use_fallback=use_fallback
    )

    try:
        # Verify content exists
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise NotFoundException(
                message=f"Content {content_id} not found"
            )

        # Get translation service
        service = get_translation_service(db)

        # Get translation with fallback
        if use_fallback:
            translation_data = await service.get_translation(
                content_id=content_id,
                language=language
            )
        else:
            # Direct lookup only
            translation_data = await service._get_translation(content_id, language)
            if not translation_data:
                raise NotFoundException(
                    message=f"Translation not found for language '{language}'"
                )

        # Build response
        lang_info = SUPPORTED_LANGUAGES.get(
            translation_data.get('translation_language', language),
            {}
        )

        response = TranslationResponse(
            id=translation_data.get('id', 0),
            content_id=content_id,
            language=translation_data.get('translation_language', language),
            title=translation_data['title'],
            description=translation_data.get('description'),
            overlay_text=translation_data.get('overlay_text'),
            metadata=translation_data.get('metadata'),
            is_primary=translation_data.get('translation_language') == content.original_language if hasattr(content, 'original_language') else False,
            status=translation_data.get('translation_status', TranslationStatus.DRAFT),
            direction=lang_info.get('direction', LanguageDirection.LTR),
            created_at=datetime.utcnow(),  # Would come from database
            updated_at=datetime.utcnow()
        )

        # Add fallback info to response metadata
        if use_fallback and translation_data.get('is_fallback'):
            response.metadata = response.metadata or {}
            response.metadata['fallback_used'] = True
            response.metadata['fallback_chain'] = translation_data.get('fallback_chain', [])
            response.metadata['requested_language'] = language
            response.metadata['actual_language'] = translation_data.get('translation_language')

        logger.info(
            "Translation retrieved",
            request_id=request_id,
            content_id=content_id,
            requested_language=language,
            actual_language=response.language,
            is_fallback=translation_data.get('is_fallback', False)
        )

        return success_response(
            data=response,
            message="Translation retrieved successfully"
        )

    except NotFoundException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get translation",
            request_id=request_id,
            content_id=content_id,
            language=language,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to retrieve translation",
            details={"error": str(e)}
        )


@router.patch("/{content_id}/translations/{language}", response_model=APIResponse[TranslationResponse])
async def update_translation(
    request: Request,
    content_id: int,
    language: str,
    data: TranslationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update existing translation

    Allows partial updates to translation fields.
    Only provided fields will be updated.

    Request body example:
    ```json
    {
        "title": "Updated Title",
        "status": "approved"
    }
    ```
    """
    request_id = get_request_id(request)

    logger.info(
        "Translation update requested",
        request_id=request_id,
        content_id=content_id,
        language=language,
        user=current_user.username,
        update_fields=list(data.dict(exclude_unset=True).keys())
    )

    try:
        # Get translation service
        service = get_translation_service(db)

        # Update translation
        updated = await service.update_translation(
            content_id=content_id,
            language=language,
            data=data,
            user_id=current_user.id
        )

        # Build response
        lang_info = SUPPORTED_LANGUAGES.get(language, {})
        response = TranslationResponse(
            id=updated['id'],
            content_id=content_id,
            language=language,
            title=updated['title'],
            description=updated.get('description'),
            overlay_text=updated.get('overlay_text'),
            metadata=updated.get('metadata'),
            is_primary=updated.get('is_primary', False),
            status=updated.get('status', TranslationStatus.DRAFT),
            direction=lang_info.get('direction', LanguageDirection.LTR),
            created_at=updated['created_at'],
            updated_at=updated['updated_at'],
            created_by=updated.get('created_by')
        )

        # Clear content cache
        await invalidate_by_prefix(f"{CACHE_KEY_PREFIXES['content']}{content_id}")

        logger.info(
            "Translation updated successfully",
            request_id=request_id,
            content_id=content_id,
            language=language
        )

        return success_response(
            data=response,
            message=f"Translation updated for language '{language}'"
        )

    except ValueError as e:
        raise NotFoundException(
            message=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to update translation",
            request_id=request_id,
            content_id=content_id,
            language=language,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to update translation",
            details={"error": str(e)}
        )


@router.delete("/{content_id}/translations/{language}")
async def delete_translation(
    request: Request,
    content_id: int,
    language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete translation

    Removes translation for specified language.
    Cannot delete the primary/original language translation.

    Returns 204 No Content on success.
    """
    request_id = get_request_id(request)

    logger.info(
        "Translation delete requested",
        request_id=request_id,
        content_id=content_id,
        language=language,
        user=current_user.username
    )

    try:
        # Get translation service
        service = get_translation_service(db)

        # Delete translation
        deleted = await service.delete_translation(content_id, language)

        if not deleted:
            raise NotFoundException(
                message=f"Translation not found for language '{language}'"
            )

        # Clear content cache
        await invalidate_by_prefix(f"{CACHE_KEY_PREFIXES['content']}{content_id}")

        logger.info(
            "Translation deleted successfully",
            request_id=request_id,
            content_id=content_id,
            language=language
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ValueError as e:
        raise BadRequestException(
            message=str(e)
        )
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete translation",
            request_id=request_id,
            content_id=content_id,
            language=language,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to delete translation",
            details={"error": str(e)}
        )


@router.post("/translations/bulk-import", response_model=APIResponse[BulkImportResponse])
async def bulk_import_translations(
    request: Request,
    file: UploadFile = File(..., description="CSV file with translations"),
    dry_run: bool = Query(False, description="Validate without importing"),
    update_existing: bool = Query(True, description="Update existing translations"),
    default_status: TranslationStatus = Query(TranslationStatus.DRAFT, description="Default status for new translations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Bulk import translations from CSV

    CSV format:
    ```csv
    content_id,language,title,description,overlay_text
    1,en,"Welcome","Welcome to our hotel","{""line1"": ""Welcome""}"
    1,id,"Selamat Datang","Selamat datang di hotel kami","{""line1"": ""Selamat Datang""}"
    2,en,"Services","Our hotel services",""
    2,zh,"服务","我们的酒店服务",""
    ```

    Features:
    - Dry run mode for validation
    - Update or skip existing translations
    - Detailed error reporting per row
    - Support for overlay_text JSON

    File size limit: 10MB
    """
    request_id = get_request_id(request)

    logger.info(
        "Bulk translation import requested",
        request_id=request_id,
        filename=file.filename,
        content_type=file.content_type,
        dry_run=dry_run,
        update_existing=update_existing,
        user=current_user.username
    )

    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise BadRequestException(
                message="Invalid file type. Please upload a CSV file."
            )

        # Read file content
        content = await file.read()

        # Check file size (10MB limit)
        if len(content) > 10 * 1024 * 1024:
            raise BadRequestException(
                message="File too large. Maximum size is 10MB."
            )

        # Decode content
        try:
            csv_content = content.decode('utf-8')
        except UnicodeDecodeError:
            # Try with different encoding
            csv_content = content.decode('latin-1')

        # Get translation service
        service = get_translation_service(db)

        # Perform import
        result = await service.bulk_import_csv(
            csv_content=csv_content,
            dry_run=dry_run,
            update_existing=update_existing,
            default_status=default_status
        )

        response = BulkImportResponse(
            imported=result['imported'],
            updated=result.get('updated', 0),
            failed=result['failed'],
            errors=result['errors'],
            warnings=result['warnings'],
            processing_time_ms=result.get('processing_time_ms', 0)
        )

        # Clear cache if any imports succeeded
        if not dry_run and (response.imported > 0 or response.updated > 0):
            await invalidate_by_prefix(CACHE_KEY_PREFIXES['content'])

        logger.info(
            "Bulk import completed",
            request_id=request_id,
            imported=response.imported,
            updated=response.updated,
            failed=response.failed,
            dry_run=dry_run
        )

        message = "Dry run validation completed" if dry_run else "Import completed"
        return success_response(
            data=response,
            message=f"{message}: {response.imported} imported, {response.updated} updated, {response.failed} failed"
        )

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(
            "Bulk import failed",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to import translations",
            details={"error": str(e)}
        )


@router.get("/translations/export")
async def export_translations(
    request: Request,
    content_ids: Optional[List[int]] = Query(None, description="Filter by content IDs"),
    languages: Optional[List[str]] = Query(None, description="Filter by languages"),
    status: Optional[TranslationStatus] = Query(None, description="Filter by status"),
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export translations to CSV or JSON

    Filters:
    - content_ids: Export specific content only
    - languages: Export specific languages only
    - status: Export by translation status
    - format: CSV or JSON

    Returns file download response.
    """
    request_id = get_request_id(request)

    logger.info(
        "Translation export requested",
        request_id=request_id,
        format=format,
        content_ids=content_ids,
        languages=languages,
        status=status,
        user=current_user.username
    )

    try:
        # Get translation service
        service = get_translation_service(db)

        # Export based on format
        if format == "csv":
            # Export as CSV
            csv_content = await service.export_csv(
                content_ids=content_ids,
                languages=languages,
                status=status
            )

            # Create response
            response = StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=translations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )

        else:
            # Export as JSON
            translations = await service._get_translations_filtered(
                content_ids, languages, status
            )

            # Create response
            import json
            json_content = json.dumps(translations, indent=2, default=str)
            response = StreamingResponse(
                io.StringIO(json_content),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=translations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )

        logger.info(
            "Translation export completed",
            request_id=request_id,
            format=format
        )

        return response

    except Exception as e:
        logger.error(
            "Translation export failed",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to export translations",
            details={"error": str(e)}
        )


@router.get("/languages", response_model=APIResponse[SupportedLanguagesResponse])
@languages_router.get("/languages", response_model=APIResponse[SupportedLanguagesResponse])
async def get_supported_languages(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get list of supported languages

    Returns all languages supported by the system with metadata:
    - Language code (ISO 639-1)
    - English name
    - Native name
    - Text direction (LTR/RTL)
    - Support status

    Available at both:
    - /api/languages (for viewer compatibility)
    - /api/content/languages (for admin panel)
    """
    request_id = get_request_id(request)

    logger.info(
        "Supported languages requested",
        request_id=request_id
    )

    try:
        # Build language list
        languages = []
        for code, info in SUPPORTED_LANGUAGES.items():
            languages.append(LanguageInfo(
                code=code,
                name=info['name'],
                native_name=info['native_name'],
                direction=info['direction'],
                is_supported=True
            ))

        response = SupportedLanguagesResponse(
            languages=languages,
            default_language=DEFAULT_LANGUAGE,
            total_count=len(languages)
        )

        logger.info(
            "Supported languages listed",
            request_id=request_id,
            count=len(languages)
        )

        return success_response(
            data=response,
            message=f"System supports {len(languages)} languages"
        )

    except Exception as e:
        logger.error(
            "Failed to get supported languages",
            request_id=request_id,
            error=str(e)
        )
        raise InternalServerException(
            message="Failed to retrieve supported languages",
            details={"error": str(e)}
        )