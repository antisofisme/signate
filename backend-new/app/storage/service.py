"""
Storage Service - Business Logic for File Management
===================================================

Service layer for file upload, storage, and management.
Uses StorageClient to communicate with Anthias and integrates
with ContentRepository for database operations.

Business Logic:
- File upload with validation
- Automatic metadata extraction (size, mimetype, hash)
- Integration with Content table
- File deletion with cleanup
- Storage quota management
"""

from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
from sqlalchemy.orm import Session
import logging
import mimetypes

from app.storage.client import StorageClient
from app.repositories.content_repository import ContentRepository
from app.repositories.organization_repository import OrganizationRepository
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException
)

logger = logging.getLogger(__name__)


class StorageService:
    """
    Storage Service for file management

    Handles file uploads, validation, and integration with
    Content model and organization quotas.

    Attributes:
        db: Database session
        storage_client: HTTP client for Anthias API
        content_repo: Content repository for database operations
        org_repo: Organization repository for quota checks
    """

    # Supported file types
    SUPPORTED_MIMETYPES = {
        # Video
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/x-msvideo",  # .avi
        "video/quicktime",  # .mov
        # Image
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        # Web
        "text/html",
        "application/pdf",
    }

    # Maximum file sizes (in MB)
    MAX_FILE_SIZE_MB = {
        "video": 500,  # 500 MB for video
        "image": 10,   # 10 MB for image
        "web": 5,      # 5 MB for HTML/PDF
    }

    def __init__(
        self,
        db: Session,
        storage_client: Optional[StorageClient] = None
    ):
        """
        Initialize storage service

        Args:
            db: Database session
            storage_client: Custom storage client (uses default if not provided)
        """
        self.db = db
        self.storage_client = storage_client or StorageClient()
        self.content_repo = ContentRepository(db)
        self.org_repo = OrganizationRepository(db)

        logger.info("StorageService initialized")

    async def upload_content(
        self,
        file: BinaryIO,
        filename: str,
        organization_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content_type: Optional[str] = None,
        check_quota: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file and create Content record

        Business Flow:
        1. Validate file type and size
        2. Check organization storage quota (optional)
        3. Upload to Anthias storage
        4. Create Content database record
        5. Return content metadata

        Args:
            file: File-like object (opened in binary mode)
            filename: Original filename
            organization_id: Organization ID
            title: Content title (defaults to filename)
            description: Content description
            content_type: Content type (video, image, web) - auto-detected if not provided
            check_quota: Whether to check storage quota

        Returns:
            Content dict with all metadata

        Raises:
            BadRequestException: Invalid file type or size
            ForbiddenException: Storage quota exceeded
        """
        # Validate file
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        if mimetype not in self.SUPPORTED_MIMETYPES:
            raise BadRequestException(
                message=f"Unsupported file type: {mimetype}",
                details={
                    "mimetype": mimetype,
                    "supported": list(self.SUPPORTED_MIMETYPES)
                }
            )

        # Determine content type if not provided
        if not content_type:
            if mimetype.startswith("video/"):
                content_type = "video"
            elif mimetype.startswith("image/"):
                content_type = "image"
            elif mimetype in ["text/html", "application/pdf"]:
                content_type = "web"
            else:
                content_type = "file"

        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        # Validate file size
        max_size_mb = self.MAX_FILE_SIZE_MB.get(content_type, 50)
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            raise BadRequestException(
                message=f"File too large. Max size: {max_size_mb} MB",
                details={
                    "file_size": file_size,
                    "max_size": max_size_bytes
                }
            )

        # Check storage quota
        if check_quota:
            file_size_gb = file_size / (1024 * 1024 * 1024)
            self.org_repo.check_storage_quota(
                organization_id,
                additional_gb=file_size_gb,
                raise_if_exceeded=True
            )

        # Upload to Anthias
        logger.info(f"Uploading file to Anthias: {filename} ({file_size} bytes)")

        upload_result = await self.storage_client.upload_file(file, filename)

        # Create Content record
        content_data = {
            "organization_id": organization_id,
            "title": title or Path(filename).stem,
            "description": description,
            "content_type": content_type,
            "file_size": file_size,
            "mime_type": mimetype,
            "anthias_asset_id": upload_result["asset_id"],
            "anthias_url": await self.storage_client.get_file_url(upload_result["asset_id"]),
            "is_active": True
        }

        content = self.content_repo.create(content_data)

        logger.info(f"Content created: {content.id} (asset_id: {upload_result['asset_id']})")

        return content.to_dict()

    async def delete_content(
        self,
        content_id: int,
        organization_id: int
    ) -> bool:
        """
        Delete content file and database record

        Business Flow:
        1. Get content from database
        2. Validate organization ownership
        3. Delete from Anthias storage
        4. Delete from database

        Args:
            content_id: Content ID
            organization_id: Organization ID (for validation)

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: Content not found
            ForbiddenException: Not authorized to delete
        """
        # Get content
        content = self.content_repo.get(content_id)
        if not content:
            raise NotFoundException(
                message=f"Content {content_id} not found",
                resource_type="Content",
                resource_id=content_id
            )

        # Validate organization ownership
        if content.organization_id != organization_id:
            raise ForbiddenException(
                message="Not authorized to delete this content",
                details={"content_id": content_id}
            )

        # Delete from Anthias storage
        if content.anthias_asset_id:
            try:
                await self.storage_client.delete_asset(content.anthias_asset_id)
                logger.info(f"Asset deleted from Anthias: {content.anthias_asset_id}")
            except Exception as e:
                logger.warning(f"Failed to delete asset from Anthias: {e}")
                # Continue with database deletion even if storage deletion fails

        # Delete from database
        deleted = self.content_repo.delete(content_id)

        logger.info(f"Content deleted: {content_id}")

        return deleted

    async def get_file_url(self, content_id: int) -> str:
        """
        Get public URL for serving content file

        Args:
            content_id: Content ID

        Returns:
            URL string for serving file

        Raises:
            NotFoundException: Content not found
        """
        content = self.content_repo.get(content_id)
        if not content:
            raise NotFoundException(
                message=f"Content {content_id} not found",
                resource_type="Content",
                resource_id=content_id
            )

        if not content.anthias_asset_id:
            raise BadRequestException(
                message="Content has no associated storage asset",
                details={"content_id": content_id}
            )

        return await self.storage_client.get_file_url(content.anthias_asset_id)

    async def check_storage_health(self) -> Dict[str, Any]:
        """
        Check Anthias storage service health

        Returns:
            Health status dict

        Raises:
            InternalServerException: Service unhealthy
        """
        return await self.storage_client.health_check()

    def get_organization_storage_usage(
        self,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Get storage usage statistics for organization

        Returns:
            {
                "organization_id": 1,
                "max_storage_gb": 10,
                "used_storage_gb": 2.5,
                "available_gb": 7.5,
                "usage_percentage": 25.0,
                "total_files": 50
            }
        """
        # Get storage quota from organization
        storage = self.org_repo.get_storage_usage(organization_id)

        # Get file count from content
        total_files = self.content_repo.count_by_organization(organization_id)

        storage["total_files"] = total_files

        return storage
