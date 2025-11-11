"""
Translation DTOs
Request and Response models for translation endpoints
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Translation DTOs
# ============================================================================

class AddTranslationRequest(BaseModel):
    """Request to add or update translation"""
    entity_type: str = Field(..., description="Entity type: content, playlist, template, widget")
    entity_id: int = Field(..., description="Entity ID")
    language_code: str = Field(..., min_length=2, max_length=5, description="Language code: en, id, zh, ja, ko")
    field_name: str = Field(..., description="Field name: title, description, content")
    translated_value: str = Field(..., description="Translated text")

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "content",
                "entity_id": 1,
                "language_code": "id",
                "field_name": "title",
                "translated_value": "Selamat Datang"
            }
        }


class UpdateTranslationRequest(BaseModel):
    """Request to update translation"""
    translated_value: str = Field(..., description="Updated translated text")


class TranslationResponse(BaseModel):
    """Translation response model"""
    id: int
    organization_id: int
    entity_type: str
    entity_id: int
    language_code: str
    field_name: str
    translated_value: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranslationListResponse(BaseModel):
    """List of translations response"""
    translations: List[TranslationResponse]
    total: int


# ============================================================================
# Entity Translation DTOs
# ============================================================================

class EntityTranslationsResponse(BaseModel):
    """Translations for a specific entity"""
    entity_type: str
    entity_id: int
    language_code: str
    translations: Dict[str, str]  # field_name -> translated_value

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "content",
                "entity_id": 1,
                "language_code": "id",
                "translations": {
                    "title": "Selamat Datang",
                    "description": "Deskripsi dalam Bahasa Indonesia"
                }
            }
        }


# ============================================================================
# Bulk Import DTOs
# ============================================================================

class BulkTranslationItem(BaseModel):
    """Single translation item for bulk import"""
    entity_type: str
    entity_id: int
    language_code: str
    field_name: str
    translated_value: str


class BulkImportRequest(BaseModel):
    """Request to bulk import translations"""
    translations: List[BulkTranslationItem] = Field(..., description="List of translations to import")

    class Config:
        json_schema_extra = {
            "example": {
                "translations": [
                    {
                        "entity_type": "content",
                        "entity_id": 1,
                        "language_code": "id",
                        "field_name": "title",
                        "translated_value": "Selamat Datang"
                    },
                    {
                        "entity_type": "content",
                        "entity_id": 1,
                        "language_code": "zh",
                        "field_name": "title",
                        "translated_value": "欢迎"
                    }
                ]
            }
        }


class BulkImportResponse(BaseModel):
    """Bulk import result"""
    imported: int
    updated: int
    failed: int
    errors: List[str] = []


# ============================================================================
# Language Support DTOs
# ============================================================================

class SupportedLanguage(BaseModel):
    """Supported language info"""
    code: str
    name: str
    native_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "code": "id",
                "name": "Indonesian",
                "native_name": "Bahasa Indonesia"
            }
        }


class SupportedLanguagesResponse(BaseModel):
    """List of supported languages"""
    languages: List[SupportedLanguage]


class OrganizationLanguagesResponse(BaseModel):
    """Languages used by organization"""
    language_codes: List[str]
    total: int


# ============================================================================
# Translation Statistics DTOs
# ============================================================================

class TranslationStatsResponse(BaseModel):
    """Translation statistics for organization"""
    total_translations: int
    languages_count: int
    entity_types: Dict[str, int]  # entity_type -> count
    completion_rate: Dict[str, float]  # language_code -> percentage
