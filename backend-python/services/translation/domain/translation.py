"""
Translation Domain Entity
Pure business logic for i18n/translation management
"""

from typing import Optional, Dict
from datetime import datetime, timezone


class Translation:
    """Translation entity - pure Python domain object"""

    VALID_ENTITY_TYPES = ["content", "playlist", "template", "widget", "menu"]
    VALID_LANGUAGES = ["en", "id", "zh", "ja", "ko", "es", "fr", "de", "ar", "th", "vi"]
    VALID_FIELD_NAMES = ["title", "description", "content", "name", "subtitle", "caption"]

    def __init__(
        self,
        entity_type: str,
        entity_id: int,
        language_code: str,
        field_name: str,
        translated_value: str,
        organization_id: int,
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.language_code = language_code
        self.field_name = field_name
        self.translated_value = translated_value
        self.organization_id = organization_id
        self.created_at = created_at
        self.updated_at = updated_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if self.entity_type not in self.VALID_ENTITY_TYPES:
            raise ValueError(f"Invalid entity type. Must be one of: {', '.join(self.VALID_ENTITY_TYPES)}")

        if not self.entity_id or self.entity_id < 1:
            raise ValueError("Invalid entity ID")

        if self.language_code not in self.VALID_LANGUAGES:
            raise ValueError(f"Unsupported language code. Supported: {', '.join(self.VALID_LANGUAGES)}")

        if self.field_name not in self.VALID_FIELD_NAMES:
            raise ValueError(f"Invalid field name. Allowed: {', '.join(self.VALID_FIELD_NAMES)}")

        if not self.translated_value or len(self.translated_value.strip()) == 0:
            raise ValueError("Translated value cannot be empty")

        if not self.organization_id:
            raise ValueError("Organization ID is required")

    def update_translation(self, new_value: str):
        """Update translated value"""
        if not new_value or len(new_value.strip()) == 0:
            raise ValueError("Translated value cannot be empty")

        self.translated_value = new_value
        self.updated_at = datetime.now(timezone.utc)

    def is_english(self) -> bool:
        """Check if translation is in English"""
        return self.language_code == "en"

    def is_indonesian(self) -> bool:
        """Check if translation is in Indonesian"""
        return self.language_code == "id"

    def is_chinese(self) -> bool:
        """Check if translation is in Chinese"""
        return self.language_code == "zh"

    def is_content_translation(self) -> bool:
        """Check if this translates content entity"""
        return self.entity_type == "content"

    def is_playlist_translation(self) -> bool:
        """Check if this translates playlist entity"""
        return self.entity_type == "playlist"

    def is_template_translation(self) -> bool:
        """Check if this translates template entity"""
        return self.entity_type == "template"

    def get_language_name(self) -> str:
        """Get full language name"""
        language_names = {
            "en": "English",
            "id": "Indonesian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ar": "Arabic",
            "th": "Thai",
            "vi": "Vietnamese",
        }
        return language_names.get(self.language_code, "Unknown")

    def __repr__(self):
        return f"<Translation(id={self.id}, {self.entity_type}:{self.entity_id}, lang={self.language_code})>"


class TranslationSet:
    """Collection of translations for a single entity"""

    def __init__(
        self,
        entity_type: str,
        entity_id: int,
        organization_id: int,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.organization_id = organization_id
        self.translations: Dict[str, Dict[str, str]] = {}  # {lang_code: {field_name: value}}

    def add_translation(self, translation: Translation):
        """Add translation to the set"""
        if translation.entity_type != self.entity_type or translation.entity_id != self.entity_id:
            raise ValueError("Translation does not match entity")

        if translation.language_code not in self.translations:
            self.translations[translation.language_code] = {}

        self.translations[translation.language_code][translation.field_name] = translation.translated_value

    def get_translation(self, language_code: str, field_name: str) -> Optional[str]:
        """Get specific translation"""
        return self.translations.get(language_code, {}).get(field_name)

    def get_all_for_language(self, language_code: str) -> Dict[str, str]:
        """Get all field translations for a language"""
        return self.translations.get(language_code, {})

    def get_supported_languages(self) -> list[str]:
        """Get list of languages that have translations"""
        return list(self.translations.keys())

    def has_translation(self, language_code: str, field_name: Optional[str] = None) -> bool:
        """Check if translation exists"""
        if field_name:
            return field_name in self.translations.get(language_code, {})
        return language_code in self.translations

    def is_complete_for_language(self, language_code: str, required_fields: list[str]) -> bool:
        """Check if all required fields are translated for a language"""
        if language_code not in self.translations:
            return False

        translated_fields = set(self.translations[language_code].keys())
        return all(field in translated_fields for field in required_fields)

    def get_completion_rate(self, required_fields: list[str]) -> Dict[str, float]:
        """Get completion rate for each language"""
        rates = {}
        total_fields = len(required_fields)

        for lang_code in self.translations:
            translated_count = sum(
                1 for field in required_fields
                if field in self.translations[lang_code]
            )
            rates[lang_code] = (translated_count / total_fields * 100) if total_fields > 0 else 0.0

        return rates

    def __repr__(self):
        return f"<TranslationSet({self.entity_type}:{self.entity_id}, langs={len(self.translations)})>"
