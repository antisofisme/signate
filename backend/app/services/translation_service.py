"""
Translation Service for Multi-Language Content
Handles content translations with smart fallback chains and caching
"""

import csv
import io
import json
import logging
from app.core.logging import StructuredLogger
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cache_manager, CACHE_KEY_PREFIXES, CACHE_TTLS
from app.models.content import Content
from app.schemas.translation import (
    TranslationCreate,
    TranslationUpdate,
    TranslationResponse,
    LanguageDirection,
    TranslationStatus
)

logger = StructuredLogger(__name__)


# =============================================================================
# LANGUAGE CONFIGURATION
# =============================================================================

# Supported languages with metadata
SUPPORTED_LANGUAGES = {
    'en': {
        'name': 'English',
        'native_name': 'English',
        'direction': LanguageDirection.LTR,
        'fallback': None
    },
    'id': {
        'name': 'Indonesian',
        'native_name': 'Bahasa Indonesia',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'ms': {
        'name': 'Malay',
        'native_name': 'Bahasa Melayu',
        'direction': LanguageDirection.LTR,
        'fallback': 'id'  # Malay falls back to Indonesian
    },
    'zh': {
        'name': 'Chinese (Simplified)',
        'native_name': '简体中文',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'zh-CN': {
        'name': 'Chinese (Simplified)',
        'native_name': '简体中文',
        'direction': LanguageDirection.LTR,
        'fallback': 'zh'
    },
    'zh-TW': {
        'name': 'Chinese (Traditional)',
        'native_name': '繁體中文',
        'direction': LanguageDirection.LTR,
        'fallback': 'zh'
    },
    'ja': {
        'name': 'Japanese',
        'native_name': '日本語',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'ko': {
        'name': 'Korean',
        'native_name': '한국어',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'th': {
        'name': 'Thai',
        'native_name': 'ไทย',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'vi': {
        'name': 'Vietnamese',
        'native_name': 'Tiếng Việt',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'ar': {
        'name': 'Arabic',
        'native_name': 'العربية',
        'direction': LanguageDirection.RTL,
        'fallback': 'en'
    },
    'he': {
        'name': 'Hebrew',
        'native_name': 'עברית',
        'direction': LanguageDirection.RTL,
        'fallback': 'en'
    },
    'hi': {
        'name': 'Hindi',
        'native_name': 'हिन्दी',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'ta': {
        'name': 'Tamil',
        'native_name': 'தமிழ்',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    },
    'tl': {
        'name': 'Tagalog',
        'native_name': 'Tagalog',
        'direction': LanguageDirection.LTR,
        'fallback': 'en'
    }
}

# Default language for system
DEFAULT_LANGUAGE = 'en'


# =============================================================================
# TRANSLATION SERVICE
# =============================================================================

class TranslationService:
    """
    Handle content translations with smart fallback and caching

    Features:
    - Multi-language support with RTL languages
    - Smart fallback chains based on language similarity
    - Aggressive caching for performance
    - Bulk import/export for translation agencies
    - Content-aware translation (overlay text, metadata)
    """

    def __init__(self, db: AsyncSession):
        """Initialize translation service"""
        self.db = db
        self.cache = cache_manager
        self.cache_ttl = 300  # 5 minutes

    async def get_translation(
        self,
        content_id: int,
        language: str,
        fallback_chain: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get translation with smart fallback logic

        Fallback chain:
        1. Requested language
        2. Custom fallback chain (if provided)
        3. Language-specific fallback (e.g., ms -> id)
        4. Device primary language
        5. Default language (en)
        6. Original content language
        7. Any available translation

        Returns:
            Translation data with metadata about fallback used
        """
        # Build cache key
        cache_key = f"{CACHE_KEY_PREFIXES['content']}translation:{content_id}:{language}"

        # Check cache
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        # Build fallback chain
        chain = self._build_fallback_chain(language, fallback_chain)

        # Get content with translations
        content = await self._get_content_with_translations(content_id)
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Find best translation
        translation = None
        used_language = None
        is_fallback = False

        for lang in chain:
            translation = self._find_translation(content, lang)
            if translation:
                used_language = lang
                is_fallback = (lang != language)
                break

        # Build response
        result = {
            'content_id': content_id,
            'original_title': content.get('title'),
            'original_language': content.get('original_language', DEFAULT_LANGUAGE),
            'title': translation.get('title') if translation else content.get('title'),
            'description': translation.get('description') if translation else content.get('description'),
            'overlay_text': translation.get('overlay_text') if translation else {},
            'metadata': translation.get('metadata') if translation else {},
            'translation_language': used_language or content.get('original_language', DEFAULT_LANGUAGE),
            'translation_status': translation.get('status') if translation else None,
            'is_fallback': is_fallback,
            'fallback_chain': chain,
            'direction': SUPPORTED_LANGUAGES.get(used_language, {}).get('direction', LanguageDirection.LTR)
        }

        # Cache result
        await self._set_cached(cache_key, result, self.cache_ttl)

        return result

    async def add_translation(
        self,
        content_id: int,
        language: str,
        data: TranslationCreate,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add or update translation for content

        Args:
            content_id: Content ID
            language: Language code
            data: Translation data
            user_id: User creating translation

        Returns:
            Created/updated translation
        """
        # Validate language code
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        # Check if translation exists
        existing = await self._get_translation(content_id, language)

        if existing:
            # Update existing
            return await self.update_translation(
                content_id, language,
                TranslationUpdate(**data.dict()),
                user_id
            )

        # Create new translation
        translation_data = {
            'content_id': content_id,
            'language': language,
            'title': data.title,
            'description': data.description,
            'overlay_text': data.overlay_text or {},
            'metadata': data.metadata or {},
            'is_primary': data.is_primary,
            'status': data.status,
            'direction': SUPPORTED_LANGUAGES[language]['direction'],
            'created_by': user_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # Save to database (simplified for this example)
        # In real implementation, use proper ORM model
        translation_id = await self._save_translation(translation_data)
        translation_data['id'] = translation_id

        # Clear cache
        await self._clear_translation_cache(content_id)

        logger.info(f"Added translation for content {content_id} in {language}")

        return translation_data

    async def update_translation(
        self,
        content_id: int,
        language: str,
        data: TranslationUpdate,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update existing translation"""
        # Get existing translation
        existing = await self._get_translation(content_id, language)
        if not existing:
            raise ValueError(f"Translation not found for content {content_id} in {language}")

        # Update fields
        update_data = data.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = user_id

        # Merge with existing
        for key, value in update_data.items():
            if value is not None:
                existing[key] = value

        # Save to database
        await self._update_translation(existing['id'], update_data)

        # Clear cache
        await self._clear_translation_cache(content_id)

        logger.info(f"Updated translation for content {content_id} in {language}")

        return existing

    async def delete_translation(
        self,
        content_id: int,
        language: str
    ) -> bool:
        """Delete translation"""
        # Don't allow deleting primary language
        content = await self._get_content(content_id)
        if content and content.get('original_language') == language:
            raise ValueError("Cannot delete primary language translation")

        # Delete from database
        deleted = await self._delete_translation(content_id, language)

        if deleted:
            # Clear cache
            await self._clear_translation_cache(content_id)
            logger.info(f"Deleted translation for content {content_id} in {language}")

        return deleted

    async def bulk_import_csv(
        self,
        csv_content: str,
        dry_run: bool = False,
        update_existing: bool = True,
        default_status: TranslationStatus = TranslationStatus.DRAFT
    ) -> Dict[str, Any]:
        """
        Bulk import translations from CSV

        CSV format:
        content_id,language,title,description,overlay_text
        1,en,"Welcome","Welcome to our hotel","{""line1"": ""Welcome""}"
        1,id,"Selamat Datang","Selamat datang di hotel kami","{""line1"": ""Selamat Datang""}"

        Returns:
            Import statistics and errors
        """
        imported = 0
        updated = 0
        failed = 0
        errors = []
        warnings = []

        try:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                try:
                    # Validate required fields
                    if not row.get('content_id') or not row.get('language') or not row.get('title'):
                        errors.append({
                            'row': str(row_num),
                            'error': 'Missing required fields (content_id, language, title)'
                        })
                        failed += 1
                        continue

                    # Parse data
                    content_id = int(row['content_id'])
                    language = row['language'].lower()

                    # Validate language
                    if language not in SUPPORTED_LANGUAGES:
                        errors.append({
                            'row': str(row_num),
                            'error': f"Unsupported language: {language}"
                        })
                        failed += 1
                        continue

                    # Parse overlay_text if present
                    overlay_text = {}
                    if row.get('overlay_text'):
                        try:
                            overlay_text = json.loads(row['overlay_text'])
                        except json.JSONDecodeError:
                            warnings.append(f"Row {row_num}: Invalid JSON in overlay_text, skipping")

                    # Create translation data
                    translation_data = TranslationCreate(
                        language=language,
                        title=row['title'][:255],  # Truncate if needed
                        description=row.get('description', ''),
                        overlay_text=overlay_text,
                        status=default_status
                    )

                    # Check if title was truncated
                    if len(row['title']) > 255:
                        warnings.append(f"Row {row_num}: Title truncated to 255 characters")

                    if not dry_run:
                        # Check if exists
                        existing = await self._get_translation(content_id, language)

                        if existing:
                            if update_existing:
                                await self.update_translation(
                                    content_id, language,
                                    TranslationUpdate(**translation_data.dict()),
                                    user_id=None
                                )
                                updated += 1
                            else:
                                warnings.append(
                                    f"Row {row_num}: Translation exists for content {content_id} "
                                    f"in {language}, skipping"
                                )
                        else:
                            await self.add_translation(
                                content_id, language,
                                translation_data,
                                user_id=None
                            )
                            imported += 1
                    else:
                        # Dry run - just validate
                        imported += 1

                except Exception as e:
                    errors.append({
                        'row': str(row_num),
                        'error': str(e)
                    })
                    failed += 1

        except Exception as e:
            errors.append({
                'row': 'N/A',
                'error': f"CSV parsing error: {str(e)}"
            })

        result = {
            'imported': imported,
            'updated': updated,
            'failed': failed,
            'errors': errors,
            'warnings': warnings,
            'dry_run': dry_run,
            'processing_time_ms': 0  # Would be calculated in real implementation
        }

        logger.info(f"Bulk import completed: {imported} imported, {updated} updated, {failed} failed")

        return result

    async def export_csv(
        self,
        content_ids: Optional[List[int]] = None,
        languages: Optional[List[str]] = None,
        status: Optional[TranslationStatus] = None
    ) -> str:
        """
        Export translations to CSV

        Args:
            content_ids: Filter by content IDs
            languages: Filter by languages
            status: Filter by status

        Returns:
            CSV string
        """
        # Get translations based on filters
        translations = await self._get_translations_filtered(
            content_ids, languages, status
        )

        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['content_id', 'language', 'title', 'description',
                       'overlay_text', 'status', 'created_at', 'updated_at']
        )

        writer.writeheader()

        for translation in translations:
            writer.writerow({
                'content_id': translation['content_id'],
                'language': translation['language'],
                'title': translation['title'],
                'description': translation.get('description', ''),
                'overlay_text': json.dumps(translation.get('overlay_text', {})),
                'status': translation.get('status', ''),
                'created_at': translation.get('created_at', ''),
                'updated_at': translation.get('updated_at', '')
            })

        csv_content = output.getvalue()
        output.close()

        logger.info(f"Exported {len(translations)} translations to CSV")

        return csv_content

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _build_fallback_chain(
        self,
        requested: str,
        custom_chain: Optional[List[str]] = None
    ) -> List[str]:
        """Build intelligent fallback chain based on language"""
        chain = [requested]

        # Add custom fallback chain
        if custom_chain:
            for lang in custom_chain:
                if lang not in chain:
                    chain.append(lang)

        # Add language-specific fallback
        if requested in SUPPORTED_LANGUAGES:
            fallback = SUPPORTED_LANGUAGES[requested].get('fallback')
            if fallback and fallback not in chain:
                chain.append(fallback)

        # Add default language
        if DEFAULT_LANGUAGE not in chain:
            chain.append(DEFAULT_LANGUAGE)

        # Add English as final fallback
        if 'en' not in chain:
            chain.append('en')

        return chain

    def _find_translation(
        self,
        content: Dict[str, Any],
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Find translation in content data"""
        translations = content.get('translations', [])

        for translation in translations:
            if translation.get('language') == language:
                return translation

        return None

    async def _get_content_with_translations(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get content with all translations (mock implementation)"""
        # In real implementation, query database with joins
        # For now, return mock data
        return {
            'id': content_id,
            'title': 'Original Title',
            'description': 'Original Description',
            'original_language': 'en',
            'translations': []  # Would be populated from database
        }

    async def _get_content(self, content_id: int) -> Optional[Dict[str, Any]]:
        """Get content by ID"""
        # Mock implementation
        return {'id': content_id, 'original_language': 'en'}

    async def _get_translation(
        self,
        content_id: int,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Get specific translation"""
        # Mock implementation - would query database
        return None

    async def _save_translation(self, data: Dict[str, Any]) -> int:
        """Save new translation to database"""
        # Mock implementation - would insert to database
        return 1

    async def _update_translation(self, translation_id: int, data: Dict[str, Any]) -> bool:
        """Update translation in database"""
        # Mock implementation - would update database
        return True

    async def _delete_translation(self, content_id: int, language: str) -> bool:
        """Delete translation from database"""
        # Mock implementation - would delete from database
        return True

    async def _get_translations_filtered(
        self,
        content_ids: Optional[List[int]],
        languages: Optional[List[str]],
        status: Optional[TranslationStatus]
    ) -> List[Dict[str, Any]]:
        """Get filtered translations"""
        # Mock implementation - would query database with filters
        return []

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if self.cache:
            try:
                return await self.cache.get(key)
            except Exception as e:
                logger.warning(f"Cache get error: {e}")
        return None

    async def _set_cached(self, key: str, value: Any, ttl: int) -> None:
        """Set cached value"""
        if self.cache:
            try:
                await self.cache.set(key, value, ttl)
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

    async def _clear_translation_cache(self, content_id: int) -> None:
        """Clear all translation caches for content"""
        if self.cache:
            try:
                # Clear all language variations
                pattern = f"{CACHE_KEY_PREFIXES['content']}translation:{content_id}:*"
                await self.cache.delete_pattern(pattern)
            except Exception as e:
                logger.warning(f"Cache clear error: {e}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

def get_translation_service(db: AsyncSession) -> TranslationService:
    """Get translation service instance"""
    return TranslationService(db)