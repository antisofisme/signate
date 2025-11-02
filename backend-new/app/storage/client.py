"""
Storage Client - HTTP Wrapper for Anthias API
==============================================

Provides HTTP client for communicating with Anthias storage service.
Anthias runs as separate Django service (port 8000) for file storage.

API Endpoints:
- POST /api/storage/upload - Upload file
- GET /api/storage/serve/{asset_id} - Serve file
- GET /api/storage/{asset_id} - Get asset info
- DELETE /api/storage/{asset_id} - Delete file
- GET /api/storage/health - Health check
"""

import httpx
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import logging

from app.core.config import settings
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    InternalServerException
)

logger = logging.getLogger(__name__)


class StorageClient:
    """
    HTTP Client for Anthias Storage API

    Handles file upload, download, and management through Anthias service.
    All file storage operations go through this client.

    Attributes:
        base_url: Base URL of Anthias service (default: http://localhost:8000)
        timeout: HTTP request timeout in seconds
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize storage client

        Args:
            base_url: Anthias API base URL (from settings if not provided)
            timeout: HTTP timeout in seconds
        """
        self.base_url = base_url or getattr(
            settings,
            "ANTHIAS_URL",
            "http://localhost:8000"
        )
        self.timeout = timeout

        logger.info(f"StorageClient initialized with base_url: {self.base_url}")

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str
    ) -> Dict[str, Any]:
        """
        Upload file to Anthias storage

        Args:
            file: File-like object (opened in binary mode)
            filename: Original filename

        Returns:
            {
                "asset_id": "uuid",
                "uri": "/data/screenly_assets/uuid_filename.ext",
                "md5": "md5hash",
                "size": 12345,
                "mimetype": "video/mp4"
            }

        Raises:
            BadRequestException: Invalid file or upload failed
            InternalServerException: Anthias service error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                files = {"file": (filename, file)}

                response = await client.post(
                    f"{self.base_url}/api/storage/upload",
                    files=files
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        logger.info(f"File uploaded successfully: {result['data']['asset_id']}")
                        return result["data"]
                    else:
                        raise BadRequestException(
                            message="Upload failed",
                            details=result
                        )

                elif response.status_code == 400:
                    error = response.json().get("error", "Bad request")
                    raise BadRequestException(message=error)

                else:
                    raise InternalServerException(
                        message=f"Anthias upload failed: {response.status_code}",
                        details={"status_code": response.status_code}
                    )

        except httpx.RequestError as e:
            logger.error(f"HTTP request error uploading file: {e}")
            raise InternalServerException(
                message="Failed to connect to storage service",
                details={"error": str(e)}
            )

    async def get_asset_info(self, asset_id: str) -> Dict[str, Any]:
        """
        Get asset metadata from Anthias

        Args:
            asset_id: Asset UUID

        Returns:
            {
                "asset_id": "uuid",
                "name": "filename.mp4",
                "uri": "/data/screenly_assets/...",
                "md5": "hash",
                "mimetype": "video/mp4"
            }

        Raises:
            NotFoundException: Asset not found
            InternalServerException: Anthias service error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/storage/{asset_id}"
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return result["data"]
                    else:
                        raise InternalServerException("Invalid response from storage service")

                elif response.status_code == 404:
                    raise NotFoundException(
                        message=f"Asset {asset_id} not found in storage",
                        resource_type="Asset",
                        resource_id=asset_id
                    )

                else:
                    raise InternalServerException(
                        message=f"Anthias get_asset failed: {response.status_code}"
                    )

        except httpx.RequestError as e:
            logger.error(f"HTTP request error getting asset info: {e}")
            raise InternalServerException(
                message="Failed to connect to storage service",
                details={"error": str(e)}
            )

    async def delete_asset(self, asset_id: str) -> bool:
        """
        Delete asset from Anthias storage

        Deletes both the file and database record.

        Args:
            asset_id: Asset UUID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundException: Asset not found
            InternalServerException: Anthias service error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/storage/{asset_id}"
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        logger.info(f"Asset deleted successfully: {asset_id}")
                        return True
                    else:
                        return False

                elif response.status_code == 404:
                    raise NotFoundException(
                        message=f"Asset {asset_id} not found in storage",
                        resource_type="Asset",
                        resource_id=asset_id
                    )

                else:
                    raise InternalServerException(
                        message=f"Anthias delete failed: {response.status_code}"
                    )

        except httpx.RequestError as e:
            logger.error(f"HTTP request error deleting asset: {e}")
            raise InternalServerException(
                message="Failed to connect to storage service",
                details={"error": str(e)}
            )

    async def get_file_url(self, asset_id: str) -> str:
        """
        Get public URL for serving file

        Args:
            asset_id: Asset UUID

        Returns:
            URL string for serving file
        """
        return f"{self.base_url}/api/storage/serve/{asset_id}"

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Anthias storage service health

        Returns:
            {
                "status": "ok",
                "mode": "minimal_storage",
                "version": "1.0",
                "storage_path": "/data/screenly_assets",
                "storage_exists": true
            }

        Raises:
            InternalServerException: Service unreachable or unhealthy
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/api/storage/health"
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise InternalServerException(
                        message="Storage service unhealthy",
                        details={"status_code": response.status_code}
                    )

        except httpx.RequestError as e:
            logger.error(f"Storage service health check failed: {e}")
            raise InternalServerException(
                message="Storage service unreachable",
                details={"error": str(e)}
            )


# Global storage client instance
storage_client = StorageClient()
