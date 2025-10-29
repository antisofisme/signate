"""
Translation Schemas for Multi-Language Content API
Provides validation for content translations and language management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class LanguageDirection(str, Enum):
    """Text direction for languages"""
    LTR = "ltr"  # Left-to-right
    RTL = "rtl"  # Right-to-left (Arabic, Hebrew)


class TranslationStatus(str, Enum):
    """Translation status"""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class TranslationCreate(BaseModel):
    """Create a new translation for content"""
    language: str = Field(
        ...,
        min_length=2,
        max_length=5,
        regex="^[a-z]{2}(-[A-Z]{2})?$",
        description="ISO 639-1 language code (e.g., 'en', 'id', 'zh-CN')"
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Translated title"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Translated description"
    )
    overlay_text: Optional[Dict[str, str]] = Field(
        None,
        description="Translated overlay text (key-value pairs)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional translation metadata"
    )
    is_primary: bool = Field(
        default=False,
        description="Set as primary language for this content"
    )
    status: TranslationStatus = Field(
        default=TranslationStatus.DRAFT,
        description="Translation status"
    )

    @validator('language')
    def validate_language_code(cls, v):
        """Validate ISO 639-1 language code"""
        valid_codes = [
            'en', 'id', 'ms', 'zh', 'zh-CN', 'zh-TW', 'ja', 'ko',
            'th', 'vi', 'ar', 'he', 'fr', 'de', 'es', 'pt', 'ru',
            'hi', 'ta', 'tl'  # Common in hospitality
        ]
        base_code = v.split('-')[0]
        if base_code not in valid_codes:
            raise ValueError(f"Unsupported language code: {v}")
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "language": "id",
                "title": "Selamat Datang di Hotel Grand",
                "description": "Nikmati pengalaman menginap yang tak terlupakan",
                "overlay_text": {
                    "line1": "Selamat Datang",
                    "line2": "Hotel Grand"
                },
                "is_primary": False,
                "status": "approved"
            }
        }


class TranslationUpdate(BaseModel):
    """Update an existing translation"""
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        None,
        max_length=2000
    )
    overlay_text: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_primary: Optional[bool] = None
    status: Optional[TranslationStatus] = None


class BulkTranslationImport(BaseModel):
    """Bulk import translation request"""
    dry_run: bool = Field(
        default=False,
        description="Validate without importing"
    )
    update_existing: bool = Field(
        default=True,
        description="Update existing translations"
    )
    default_status: TranslationStatus = Field(
        default=TranslationStatus.DRAFT,
        description="Default status for new translations"
    )

    class Config:
        schema_extra = {
            "example": {
                "dry_run": False,
                "update_existing": True,
                "default_status": "draft"
            }
        }


class TranslationExportRequest(BaseModel):
    """Export translations request"""
    content_ids: Optional[List[int]] = Field(
        None,
        description="Specific content IDs to export"
    )
    languages: Optional[List[str]] = Field(
        None,
        description="Specific languages to export"
    )
    status: Optional[TranslationStatus] = Field(
        None,
        description="Filter by status"
    )
    format: str = Field(
        default="csv",
        regex="^(csv|json|xlsx)$",
        description="Export format"
    )

    class Config:
        schema_extra = {
            "example": {
                "content_ids": [1, 2, 3],
                "languages": ["en", "id", "zh"],
                "status": "approved",
                "format": "csv"
            }
        }


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TranslationResponse(BaseModel):
    """Translation response"""
    id: int = Field(..., description="Translation ID")
    content_id: int = Field(..., description="Content ID")
    language: str = Field(..., description="Language code")
    title: str = Field(..., description="Translated title")
    description: Optional[str] = Field(None, description="Translated description")
    overlay_text: Optional[Dict[str, str]] = Field(
        None,
        description="Translated overlay text"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Translation metadata"
    )
    is_primary: bool = Field(..., description="Is primary language")
    status: TranslationStatus = Field(..., description="Translation status")
    direction: LanguageDirection = Field(
        ...,
        description="Text direction"
    )
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    created_by: Optional[str] = Field(None, description="Creator username")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "content_id": 123,
                "language": "id",
                "title": "Selamat Datang",
                "description": "Deskripsi dalam Bahasa Indonesia",
                "overlay_text": {"line1": "Teks Overlay"},
                "is_primary": False,
                "status": "approved",
                "direction": "ltr",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "created_by": "admin"
            }
        }


class TranslationListResponse(BaseModel):
    """List of translations for content"""
    content_id: int = Field(..., description="Content ID")
    default_language: str = Field(..., description="Default language")
    translations: List[TranslationResponse] = Field(
        ...,
        description="Available translations"
    )
    available_languages: List[str] = Field(
        ...,
        description="List of available language codes"
    )
    missing_languages: List[str] = Field(
        default_factory=list,
        description="Suggested missing languages"
    )
    total_count: int = Field(..., description="Total translations")

    class Config:
        schema_extra = {
            "example": {
                "content_id": 123,
                "default_language": "en",
                "translations": [
                    {
                        "id": 1,
                        "language": "en",
                        "title": "Welcome",
                        "is_primary": True
                    },
                    {
                        "id": 2,
                        "language": "id",
                        "title": "Selamat Datang",
                        "is_primary": False
                    }
                ],
                "available_languages": ["en", "id"],
                "missing_languages": ["zh", "ja"],
                "total_count": 2
            }
        }


class BulkImportResponse(BaseModel):
    """Response for bulk import operation"""
    imported: int = Field(..., description="Successfully imported count")
    updated: int = Field(..., description="Updated existing count")
    failed: int = Field(..., description="Failed import count")
    errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Import errors with details"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Import warnings"
    )
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "imported": 145,
                "updated": 20,
                "failed": 5,
                "errors": [
                    {
                        "row": "10",
                        "error": "Invalid language code: 'xx'"
                    }
                ],
                "warnings": [
                    "Row 15: Title truncated to 255 characters"
                ],
                "processing_time_ms": 1250.5
            }
        }


class ContentWithTranslation(BaseModel):
    """Content with translation based on language preference"""
    id: int = Field(..., description="Content ID")
    original_title: str = Field(..., description="Original title")
    original_language: str = Field(..., description="Original language")

    # Translated fields
    title: str = Field(..., description="Title in requested language")
    description: Optional[str] = Field(None, description="Description")
    overlay_text: Optional[Dict[str, str]] = Field(None, description="Overlay text")

    # Translation metadata
    translation_language: str = Field(..., description="Applied translation language")
    translation_status: Optional[TranslationStatus] = Field(
        None,
        description="Translation status"
    )
    is_fallback: bool = Field(
        ...,
        description="Whether using fallback translation"
    )
    fallback_chain: List[str] = Field(
        default_factory=list,
        description="Fallback chain used"
    )

    # Content metadata
    file_type: str = Field(..., description="Content type")
    url: str = Field(..., description="Content URL")
    duration: int = Field(..., description="Duration in seconds")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 123,
                "original_title": "Welcome Video",
                "original_language": "en",
                "title": "Video Selamat Datang",
                "description": "Video promosi hotel",
                "translation_language": "id",
                "translation_status": "approved",
                "is_fallback": False,
                "fallback_chain": ["id", "en"],
                "file_type": "video",
                "url": "https://example.com/video.mp4",
                "duration": 30,
                "is_active": True
            }
        }


class LanguageInfo(BaseModel):
    """Language information"""
    code: str = Field(..., description="Language code")
    name: str = Field(..., description="Language name")
    native_name: str = Field(..., description="Native language name")
    direction: LanguageDirection = Field(..., description="Text direction")
    is_supported: bool = Field(..., description="System support status")

    class Config:
        schema_extra = {
            "example": {
                "code": "id",
                "name": "Indonesian",
                "native_name": "Bahasa Indonesia",
                "direction": "ltr",
                "is_supported": True
            }
        }


class SupportedLanguagesResponse(BaseModel):
    """List of supported languages"""
    languages: List[LanguageInfo] = Field(
        ...,
        description="Supported languages"
    )
    default_language: str = Field(
        ...,
        description="System default language"
    )
    total_count: int = Field(..., description="Total count")

    class Config:
        schema_extra = {
            "example": {
                "languages": [
                    {
                        "code": "en",
                        "name": "English",
                        "native_name": "English",
                        "direction": "ltr",
                        "is_supported": True
                    },
                    {
                        "code": "id",
                        "name": "Indonesian",
                        "native_name": "Bahasa Indonesia",
                        "direction": "ltr",
                        "is_supported": True
                    }
                ],
                "default_language": "en",
                "total_count": 2
            }
        }