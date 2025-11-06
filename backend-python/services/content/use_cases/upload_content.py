"""
Upload Content Use Case
Main business logic for uploading content files
"""

from fastapi import UploadFile
from typing import Optional
import os

from ..domain.content import Content
from ..domain.interfaces import IContentRepository
from ..infrastructure.storage.interfaces import IStorageService
from ..infrastructure.storage.metadata_extractor import MetadataExtractor


class UploadContentUseCase:
    """Upload content with custom storage"""

    # Supported file extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.flv'}
    AUDIO_EXTENSIONS = {'.mp3', '.aac', '.m4a', '.ogg', '.wav', '.flac', '.wma'}

    # Max file sizes (bytes)
    MAX_SIZES = {
        'image': 50 * 1024 * 1024,   # 50 MB
        'video': 500 * 1024 * 1024,  # 500 MB
        'audio': 100 * 1024 * 1024,  # 100 MB
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

    async def execute(
        self,
        file: UploadFile,
        title: str,
        organization_id: int,
        uploaded_by: int,
        description: Optional[str] = None,
        duration: int = 10,
        is_active: bool = True
    ) -> Content:
        """
        Execute upload content use case

        Steps:
        1. Validate file (type, size, extension)
        2. Save to local filesystem via StorageService
        3. Check for duplicates (hash-based)
        4. Extract metadata via FFprobe/Pillow
        5. Create domain entity
        6. Save to database
        7. Queue background tasks (transcoding, thumbnail)

        Args:
            file: Uploaded file
            title: Content title
            organization_id: Organization ID
            uploaded_by: User ID who uploads
            description: Optional description
            duration: Display duration in seconds
            is_active: Active status

        Returns:
            Created Content entity

        Raises:
            ValueError: If validation fails
            DuplicateError: If file already exists
            StorageException: If storage operation fails
        """

        # 1. Validate file
        content_type = self._validate_file(file)

        # 2. Save file to storage
        storage_result = await self.storage.save_file(
            file=file,
            content_type=content_type,
            organization_id=organization_id
        )

        # 3. Check for duplicate files (same hash + org)
        existing = self.content_repo.find_by_hash(
            file_hash=storage_result['file_hash'],
            organization_id=organization_id
        )
        if existing:
            # Cleanup uploaded file
            await self.storage.delete_file(storage_result['storage_key'])
            raise ValueError(
                f"File already exists: {existing.title} (ID: {existing.id})"
            )

        # 4. Extract metadata
        metadata = await self.metadata.extract(
            file_path=storage_result['file_path'],
            content_type=content_type
        )

        # 5. Auto-set duration for video/audio (use actual media duration)
        if content_type in ['video', 'audio'] and metadata.get('duration'):
            duration = int(metadata['duration'])

        # 6. Create domain entity
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
            original_filename=file.filename,
            file_extension=os.path.splitext(file.filename)[1].lower(),
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

            # Status
            upload_status='completed',
            transcoding_status='pending',  # Will be processed by Celery

            # Multi-tenant
            organization_id=organization_id,
            uploaded_by=uploaded_by
        )

        # Validate business rules (raises ValueError if invalid)
        content.__post_init__()

        # 7. Save to database
        saved_content = self.content_repo.create(content)

        # 8. Queue background tasks
        if content_type == 'video':
            from tasks.content_tasks import transcode_to_hls
            transcode_to_hls.delay(saved_content.id)

        if content_type in ['video', 'image']:
            from tasks.content_tasks import generate_thumbnail
            generate_thumbnail.delay(saved_content.id)

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

        filename = file.filename.lower()
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

        # Validate MIME type
        mime = file.content_type or ''
        if content_type == 'image' and not mime.startswith('image/'):
            raise ValueError(f"MIME type mismatch. Expected image/*, got {mime}")
        elif content_type == 'video' and not mime.startswith('video/'):
            raise ValueError(f"MIME type mismatch. Expected video/*, got {mime}")
        elif content_type == 'audio' and not mime.startswith('audio/'):
            raise ValueError(f"MIME type mismatch. Expected audio/*, got {mime}")

        return content_type
