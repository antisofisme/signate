"""
Upload Content Use Case
Main business logic for uploading content files
"""

from fastapi import UploadFile
from typing import Optional
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from ..domain.content import Content
from ..domain.interfaces import IContentRepository
from ..infrastructure.storage.interfaces import IStorageService
from ..infrastructure.storage.metadata_extractor import MetadataExtractor
from shared.file_security import SecureFileHandler
from shared.virus_scanner import get_virus_scanner
from shared.websocket_manager import websocket_manager, WebSocketEventType
from shared.config import settings
from services.organization.domain.quota_service import OrganizationQuotaService
import asyncio


class UploadContentUseCase:
    """Upload content with custom storage"""

    # Supported file extensions
    IMAGE_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp',
        '.tiff', '.tif',   # Print quality
        '.heic', '.heif',  # Apple/iPhone photos
        '.avif',           # Modern format
    }
    VIDEO_EXTENSIONS = {
        '.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.flv',
        '.wmv',            # Windows Media Video
        '.mpg',            # Legacy MPEG Video (use .mpg for video, .mpeg for audio)
        '.3gp', '.3g2',    # Mobile video
        '.mts', '.m2ts',   # HD Camcorder (AVCHD)
        '.ts',             # MPEG Transport Stream
        '.ogv',            # Ogg Video
    }
    AUDIO_EXTENSIONS = {
        '.mp3', '.aac', '.m4a', '.ogg', '.wav', '.flac', '.wma',
        '.mpeg',           # MPEG Audio (WhatsApp)
        '.opus',           # Modern codec
        '.amr',            # Mobile recordings
        '.aiff', '.aif',   # Apple format
        '.oga',            # Ogg Audio
        '.weba',           # WebM Audio
    }

    # Max file sizes (bytes) - configurable via environment variables
    @staticmethod
    def get_max_sizes():
        return {
            'image': int(os.getenv('MAX_IMAGE_SIZE_MB', '50')) * 1024 * 1024,   # Default: 50 MB
            'video': int(os.getenv('MAX_VIDEO_SIZE_MB', '500')) * 1024 * 1024,  # Default: 500 MB
            'audio': int(os.getenv('MAX_AUDIO_SIZE_MB', '100')) * 1024 * 1024,  # Default: 100 MB
        }

    def __init__(
        self,
        content_repo: IContentRepository,
        storage_service: IStorageService,
        metadata_extractor: MetadataExtractor
    ):
        self.content_repo = content_repo
        self.storage = storage_service
        self.metadata = metadata_extractor

    def _generate_image_thumbnail_sync(self, source_path: str) -> Optional[dict]:
        """
        Generate thumbnail synchronously for images.
        Images are fast to process (<500ms), so we do it inline for immediate response.

        Returns:
            dict with thumbnail_path and thumbnail_url, or None if failed
        """
        try:
            from PIL import Image

            source = Path(source_path)
            if not source.exists():
                logger.warning(f"Source file not found for thumbnail: {source_path}")
                return None

            # Create thumbnails directory
            thumb_dir = Path("/data/signage/content/thumbnails")
            thumb_dir.mkdir(parents=True, exist_ok=True)

            # Thumbnail output path
            thumb_filename = f"{source.stem}_thumb.jpg"
            thumb_path = thumb_dir / thumb_filename

            # Generate thumbnail
            with Image.open(source) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background

                # Create thumbnail
                img.thumbnail((320, 320), Image.Resampling.LANCZOS)
                img.save(thumb_path, 'JPEG', quality=85, optimize=True)

            print(f"[Upload] Image thumbnail generated synchronously: {thumb_path}")

            return {
                'thumbnail_path': str(thumb_path),
                'thumbnail_url': f"{settings.PUBLIC_BASE_URL}/thumbnails/{thumb_filename}"
            }

        except Exception as e:
            logger.warning(f"Failed to generate image thumbnail synchronously: {e}")
            return None

    async def execute(
        self,
        file: UploadFile,
        title: str,
        organization_id: int,
        uploaded_by_id: int,
        description: Optional[str] = None,
        duration: int = 10,
        is_active: bool = True
    ) -> Content:
        """
        Execute upload content use case

        Steps:
        1. Validate file (type, size, extension)
        2. Save to local filesystem via StorageService
        3. Scan for viruses
        4. Extract metadata via FFprobe/Pillow
        5. Create domain entity
        6. Save to database
        7. Queue background tasks (transcoding, thumbnail)

        Note: If a file with the same hash exists, we REUSE the storage
        to save disk space, but create a new content record with new ID.
        This allows multiple content entries pointing to the same file.

        Args:
            file: Uploaded file
            title: Content title
            organization_id: Organization ID
            uploaded_by_id: User ID who uploads
            description: Optional description
            duration: Display duration in seconds
            is_active: Active status

        Returns:
            Created Content entity

        Raises:
            ValueError: If validation fails (type, size, virus)
            StorageException: If storage operation fails
        """

        # 1. Validate file
        content_type = self._validate_file(file)

        # 1.5. Check organization content quota
        # Get file size first
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        # Get database session from repository
        db_session = self.content_repo.db
        quota_service = OrganizationQuotaService(db_session)
        
        # Enforce content quota atomically to prevent race conditions
        try:
            quota_service.enforce_content_quota_atomic(organization_id, file_size)
        except ValueError as e:
            raise ValueError(f"Quota exceeded: {str(e)}")

        # 2. Save file to storage
        storage_result = await self.storage.save_file(
            file=file,
            content_type=content_type,
            organization_id=organization_id
        )

        # 2.5. Scan for viruses (CRITICAL FIX P0-14) - Now async for non-blocking
        try:
            scanner = get_virus_scanner()
            # Use async version for non-blocking operation
            is_clean, scan_result = await scanner.scan_file_async(storage_result['file_path'])

            if not is_clean:
                # Virus detected - cleanup uploaded file
                await self.storage.delete_file(storage_result['storage_key'])
                raise ValueError(f"File rejected: {scan_result}")

            print(f"[Virus Scan] {os.path.basename(storage_result['file_path'])}: {scan_result}")

        except (ConnectionError, TimeoutError) as e:
            # ClamAV unavailable - log warning but allow upload
            # This prevents blocking uploads if ClamAV is down
            logger.warning(f"Virus scan unavailable, allowing upload: {e}")
            print(f"[Virus Scan] WARNING: Scan unavailable - {e}")

        # 3. Check for existing file with same hash - REUSE physical file if exists
        # This saves disk space while allowing multiple content records
        # NOTE: storage_key must be UNIQUE per record, but file_path can be shared
        existing = self.content_repo.find_by_hash(
            file_hash=storage_result['file_hash'],
            organization_id=organization_id
        )

        # Track if we're reusing existing file (to skip transcoding later)
        is_duplicate = False
        existing_hls_info = None
        existing_thumbnail_info = None

        if existing:
            is_duplicate = True

            # Reuse storage from existing file (save disk space)
            # Delete the newly uploaded file since we'll use the existing one
            new_storage_key = storage_result['storage_key']  # Keep unique key for this record
            await self.storage.delete_file(new_storage_key)

            # Use existing file's path/url but KEEP unique storage_key for DB uniqueness
            storage_result = {
                'file_path': existing.file_path,
                'file_url': existing.file_url,
                'storage_key': new_storage_key,  # Keep NEW unique key (not existing's key!)
                'file_hash': existing.file_hash,
                'file_size': existing.file_size,
            }

            # Copy HLS info from existing (if transcoded)
            if existing.hls_master_playlist_path:
                existing_hls_info = {
                    'master_playlist_path': existing.hls_master_playlist_path,
                    'master_playlist_url': existing.hls_master_playlist_url,
                    'hls_variants': existing.hls_variants,
                }

            # Copy thumbnail info from existing (check URL since path might be empty)
            if existing.thumbnail_url or existing.thumbnail_path:
                existing_thumbnail_info = {
                    'thumbnail_path': existing.thumbnail_path,
                    'thumbnail_url': existing.thumbnail_url,
                }
                print(f"[Upload] Copying thumbnail from existing: {existing.thumbnail_url}")

            logger.info(f"[Upload] Reusing storage from existing content ID {existing.id}")
            print(f"[Upload] Reusing storage from content ID {existing.id} (same file hash)")

        # 4. Extract metadata
        metadata = await self.metadata.extract(
            file_path=storage_result['file_path'],
            content_type=content_type
        )

        # 5. Auto-set duration for video/audio (use actual media duration)
        if content_type in ['video', 'audio'] and metadata.get('duration'):
            duration = int(metadata['duration'])

        # 6. Create domain entity
        # Determine transcoding status based on duplicate detection
        if is_duplicate and existing_hls_info:
            # Duplicate with existing HLS - mark as completed
            transcoding_status = 'completed'
        elif is_duplicate and content_type == 'image':
            # Duplicate image - no transcoding needed
            transcoding_status = 'not_required'
        else:
            # New file - needs transcoding
            transcoding_status = 'pending'

        # 6b. Generate thumbnail synchronously for images (fast, <500ms)
        # For non-duplicates, generate now so it's included in the initial response
        if content_type == 'image' and not is_duplicate:
            sync_thumbnail = self._generate_image_thumbnail_sync(storage_result['file_path'])
            if sync_thumbnail:
                existing_thumbnail_info = sync_thumbnail
                print(f"[Upload] Thumbnail ready immediately: {sync_thumbnail['thumbnail_url']}")

        content = Content(
            id=None,
            title=title,
            description=description,
            content_type=content_type,

            # Storage fields (custom system)
            file_path=storage_result['file_path'],
            file_url=storage_result['file_url'],
            storage_key=storage_result['storage_key'],
            file_hash=storage_result['file_hash'],
            file_size=storage_result['file_size'],

            # Display settings
            duration=duration,
            is_active=is_active,

            # File metadata
            mime_type=file.content_type or 'application/octet-stream',
            original_filename=file.filename,  # Original filename
            file_extension=os.path.splitext(file.filename)[1].lower() if file.filename else '',
            resolution=metadata.get('resolution'),
            width=metadata.get('width'),
            height=metadata.get('height'),
            codec=metadata.get('codec'),
            fps=metadata.get('fps'),
            bitrate=metadata.get('bitrate'),

            # Media specific
            media_duration=metadata.get('duration'),
            audio_codec=metadata.get('audio_codec'),
            audio_bitrate=metadata.get('audio_bitrate'),
            audio_sample_rate=metadata.get('audio_sample_rate'),
            audio_channels=metadata.get('audio_channels', 2),

            # HLS info (copied from existing if duplicate)
            hls_master_playlist_path=existing_hls_info['master_playlist_path'] if existing_hls_info else None,
            hls_master_playlist_url=existing_hls_info['master_playlist_url'] if existing_hls_info else None,
            hls_variants=existing_hls_info['hls_variants'] if existing_hls_info else None,

            # Thumbnail info (copied from existing if duplicate)
            thumbnail_path=existing_thumbnail_info['thumbnail_path'] if existing_thumbnail_info else None,
            thumbnail_url=existing_thumbnail_info['thumbnail_url'] if existing_thumbnail_info else None,

            # Status
            upload_status='completed',
            transcoding_status=transcoding_status,

            # Multi-tenant
            organization_id=organization_id,
            uploaded_by_id=uploaded_by_id
        )

        # Validate business rules (raises ValueError if invalid)
        content.__post_init__()

        # 7. Save to database (CRITICAL FIX P0-11: Cleanup file on failure)
        try:
            saved_content = self.content_repo.create(content)
        except Exception as e:
            # Database save failed - cleanup uploaded file to prevent orphans
            try:
                await self.storage.delete_file(storage_result['storage_key'])
                print(f"[Upload Cleanup] Deleted orphaned file: {storage_result['storage_key']}")
            except Exception as cleanup_error:
                print(f"[Upload Cleanup] Failed to delete orphaned file: {cleanup_error}")

            # Re-raise original exception
            raise

        # 8. Queue background tasks (only if NOT duplicate - duplicates reuse existing)
        if is_duplicate:
            print(f"[Upload] Skipping background tasks - duplicate file reuses existing HLS/thumbnail")
        else:
            if content_type == 'video':
                from tasks.content_tasks import transcode_to_hls, generate_thumbnail
                transcode_to_hls.delay(saved_content.id)
                # Video thumbnails still async (require ffmpeg, takes longer)
                generate_thumbnail.delay(saved_content.id)
            # Note: Image thumbnails are now generated synchronously in step 6b
            
        # 9. Send WebSocket notification (if manager is initialized)
        if websocket_manager is not None:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(
                    websocket_manager.broadcast_to_organization(
                        organization_id=saved_content.organization_id,
                        event_type=WebSocketEventType.CONTENT_UPLOADED,
                        data={
                            "content_id": saved_content.id,
                            "title": saved_content.title,
                            "content_type": saved_content.content_type,
                            "file_size": saved_content.file_size,
                            "duration": saved_content.duration,
                            "uploaded_by": saved_content.uploaded_by
                        }
                    )
                )
            except Exception as e:
                # Don't fail upload if WebSocket notification fails
                logger.warning(f"WebSocket notification failed: {e}")

        return saved_content

    def _validate_file(self, file: UploadFile) -> str:
        """
        Validate file type and extension

        Returns:
            content_type: 'image', 'video', or 'audio'

        Raises:
            ValueError: If file is invalid
        """
        if not file.filename:
            raise ValueError("Filename is required")

        # Sanitize filename to prevent path traversal
        try:
            safe_filename = SecureFileHandler.sanitize_filename(file.filename)
        except ValueError as e:
            raise ValueError(f"Invalid filename: {str(e)}")
        
        filename = safe_filename.lower()
        ext = os.path.splitext(filename)[1]

        # Determine content type
        if ext in self.IMAGE_EXTENSIONS:
            content_type = 'image'
        elif ext in self.VIDEO_EXTENSIONS:
            content_type = 'video'
        elif ext in self.AUDIO_EXTENSIONS:
            content_type = 'audio'
        else:
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Supported: {', '.join(list(self.IMAGE_EXTENSIONS)[:5])}... "
                f"and {len(self.IMAGE_EXTENSIONS) + len(self.VIDEO_EXTENSIONS) + len(self.AUDIO_EXTENSIONS)} more"
            )

        # Validate MIME type (with fallback for application/octet-stream)
        # Some browsers/clients don't set correct MIME type for less common formats
        mime = file.content_type or ''

        # Allow application/octet-stream as fallback since we already validated extension
        if mime == 'application/octet-stream' or mime == '':
            # Extension is already validated, allow it
            logger.info(f"[Upload] Allowing {ext} with MIME '{mime}' (extension-based validation passed)")
        elif content_type == 'image' and not mime.startswith('image/'):
            raise ValueError(f"MIME type mismatch. Expected image/*, got {mime}")
        elif content_type == 'video' and not mime.startswith('video/'):
            raise ValueError(f"MIME type mismatch. Expected video/*, got {mime}")
        elif content_type == 'audio' and not mime.startswith('audio/'):
            raise ValueError(f"MIME type mismatch. Expected audio/*, got {mime}")

        return content_type
