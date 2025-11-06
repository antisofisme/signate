"""
Storage Service Interface
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import UploadFile


class IStorageService(ABC):
    """Interface for content storage"""

    @abstractmethod
    async def save_file(
        self,
        file: UploadFile,
        content_type: str,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Save uploaded file to storage

        Args:
            file: FastAPI UploadFile
            content_type: Type of content ('image', 'video', 'audio')
            organization_id: Organization ID for multi-tenant isolation

        Returns:
            Dictionary with storage information:
            {
                'storage_key': 'images/2025/01/org_4/abc123.jpg',
                'file_path': '/data/signage/content/uploads/...',
                'file_url': 'http://192.168.5.12:8001/content/...',
                'file_hash': 'sha256...',
                'file_size': 1234567
            }
        """
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """
        Delete file from storage

        Args:
            storage_key: Storage key identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def file_exists(self, storage_key: str) -> bool:
        """
        Check if file exists in storage

        Args:
            storage_key: Storage key identifier

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_file_info(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from storage

        Args:
            storage_key: Storage key identifier

        Returns:
            Dictionary with file information or None if not found
        """
        pass


class StorageException(Exception):
    """Storage operation exception"""
    pass
