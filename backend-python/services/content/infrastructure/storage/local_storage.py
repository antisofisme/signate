"""
Local Filesystem Storage Implementation
Custom storage system (NO Anthias!) with organized directory structure
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import UploadFile
import hashlib
import uuid

from .interfaces import IStorageService
from shared.file_security import SecureFileHandler


class LocalFilesystemStorage(IStorageService):
    """
    Local filesystem storage implementation

    Directory structure:
    /data/signage/content/
    ├── uploads/
    │   ├── images/
    │   │   └── 2025/
    │   │       └── 01/
    │   │           └── org_4/
    │   │               └── uuid.jpg
    │   ├── videos/
    │   └── audios/
    ├── thumbnails/
    ├── transcoded/
    └── temp/
    """

    def __init__(
        self,
        base_path: str = "/data/signage/content",
        base_url: str = "http://192.168.5.12:8001"
    ):
        self.base_path = Path(base_path)
        self.base_url = base_url

        # Define subdirectories
        self.uploads_dir = self.base_path / "uploads"
        self.thumbnails_dir = self.base_path / "thumbnails"
        self.transcoded_dir = self.base_path / "transcoded"
        self.temp_dir = self.base_path / "temp"

        # Ensure all directories exist
        for directory in [self.uploads_dir, self.thumbnails_dir, self.transcoded_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file: UploadFile,
        content_type: str,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Save uploaded file to local filesystem

        Path format: {type}s/{year}/{month}/org_{org_id}/{uuid}.{ext}
        Example: images/2025/01/org_4/abc123-def456.jpg

        Args:
            file: Uploaded file from FastAPI
            content_type: Type of content ('image', 'video', 'audio')
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Dictionary with storage metadata:
            {
                'storage_key': str,
                'file_path': str,
                'file_url': str,
                'file_hash': str,
                'file_size': int
            }
        """
        # Sanitize filename first
        try:
            safe_filename = SecureFileHandler.sanitize_filename(file.filename)
        except ValueError as e:
            raise ValueError(f"Invalid filename: {str(e)}")
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        file_extension = Path(safe_filename).suffix.lower()

        # Build organized directory structure
        now = datetime.now(timezone.utc)
        type_folder = f"{content_type}s"  # images, videos, audios
        year_folder = str(now.year)
        month_folder = f"{now.month:02d}"
        org_folder = f"org_{organization_id}"

        # Create full directory path
        target_dir = self.uploads_dir / type_folder / year_folder / month_folder / org_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        # Full file path with secure filename
        filename = f"{unique_id}{file_extension}"
        file_path = target_dir / filename
        
        # Verify path is within allowed directory
        file_path = SecureFileHandler.generate_safe_path(
            self.uploads_dir, 
            filename, 
            organization_id, 
            content_type
        )

        # Storage key (relative path from uploads/)
        storage_key = f"{type_folder}/{year_folder}/{month_folder}/{org_folder}/{filename}"

        # Calculate file hash and size while saving
        sha256_hash = hashlib.sha256()
        file_size = 0

        # Save file in chunks (memory efficient for large files)
        with file_path.open("wb") as f:
            while chunk := await file.read(8192):  # 8KB chunks
                f.write(chunk)
                sha256_hash.update(chunk)
                file_size += len(chunk)

        # Reset file pointer for potential re-reading
        await file.seek(0)
        
        # Validate file content matches expected type
        try:
            SecureFileHandler.validate_file_content(file_path, content_type)
        except ValueError as e:
            # Delete invalid file
            file_path.unlink(missing_ok=True)
            raise ValueError(f"File validation failed: {str(e)}")

        # Generate public URL
        file_url = f"{self.base_url}/content/{storage_key}"

        return {
            'storage_key': storage_key,
            'file_path': str(file_path),
            'file_url': file_url,
            'file_hash': sha256_hash.hexdigest(),
            'file_size': file_size
        }

    async def delete_file(self, storage_key: str) -> bool:
        """
        Delete file from local filesystem

        Args:
            storage_key: Relative path from uploads/ directory

        Returns:
            True if deleted, False if file not found
        """
        file_path = self.uploads_dir / storage_key

        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True

        return False

    async def file_exists(self, storage_key: str) -> bool:
        """
        Check if file exists

        Args:
            storage_key: Relative path from uploads/ directory

        Returns:
            True if exists, False otherwise
        """
        file_path = self.uploads_dir / storage_key
        return file_path.exists() and file_path.is_file()

    async def get_file_url(self, storage_key: str) -> str:
        """
        Get public URL for file

        Args:
            storage_key: Relative path from uploads/ directory

        Returns:
            Public URL
        """
        return f"{self.base_url}/content/{storage_key}"

    async def get_file_info(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from storage

        Args:
            storage_key: Relative path from uploads/ directory

        Returns:
            Dictionary with file information or None if not found
        """
        file_path = self.uploads_dir / storage_key

        if not file_path.exists() or not file_path.is_file():
            return None

        stat = file_path.stat()
        return {
            'storage_key': storage_key,
            'file_path': str(file_path),
            'file_url': f"{self.base_url}/content/{storage_key}",
            'file_size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
        }


# Dependency injection helper
def get_storage_service() -> IStorageService:
    """Get storage service instance for dependency injection"""
    return LocalFilesystemStorage()
