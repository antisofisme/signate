"""
Anthias Integration Service
Handles communication with Anthias API for content management
"""

import httpx
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnthiasService:
    """
    Service for interacting with Anthias API

    Anthias is the digital signage platform that handles actual file storage
    and serving. This service provides methods to:
    - Upload assets (images/videos)
    - List assets
    - Get asset details
    - Delete assets
    """

    def __init__(self):
        # Use ANTHIAS_INTERNAL_URL for backend-to-Anthias communication (Docker network)
        self.base_url = settings.ANTHIAS_INTERNAL_URL
        self.public_url = settings.ANTHIAS_PUBLIC_URL
        self.api_version = "v1"
        self.timeout = 30.0  # 30 seconds timeout

    def _get_api_url(self, endpoint: str) -> str:
        """
        Construct full API URL

        Args:
            endpoint: API endpoint path

        Returns:
            str: Full API URL
        """
        return f"{self.base_url}/api/{self.api_version}/{endpoint}"

    async def upload_asset(
        self,
        file: UploadFile,
        name: Optional[str] = None,
        duration: int = 10,
        is_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Upload an asset (image or video) to Anthias using 2-step process:
        1. Upload file to /file_asset endpoint
        2. Create asset with file URI using /assets endpoint

        Args:
            file: File to upload (from FastAPI UploadFile)
            name: Display name for asset (defaults to filename)
            duration: Display duration in seconds (default 10)
            is_enabled: Whether asset is enabled (default True)

        Returns:
            dict: Asset information from Anthias

        Raises:
            HTTPException: If upload fails
        """
        try:
            import json

            # Read file content
            file_content = await file.read()

            # Determine mimetype
            mimetype = "image" if file.content_type.startswith("image/") else "video"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # STEP 1: Upload file to get URI
                files = {
                    "file_upload": (file.filename, file_content, file.content_type)
                }

                upload_response = await client.post(
                    self._get_api_url("file_asset"),
                    files=files
                )

                if upload_response.status_code != 200:
                    logger.error(f"Anthias file upload failed: {upload_response.status_code} - {upload_response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload file to Anthias: {upload_response.text}"
                    )

                file_data = upload_response.json()
                file_uri = file_data.get("uri")

                if not file_uri:
                    raise HTTPException(
                        status_code=500,
                        detail="Anthias did not return file URI"
                    )

                logger.info(f"File uploaded to Anthias: {file_uri}")

                # STEP 2: Create asset with the file URI
                # Anthias v1 API expects 'model' field with JSON string
                model_data = {
                    "name": name or file.filename,
                    "uri": file_uri,
                    "mimetype": mimetype,
                    "duration": str(duration),
                    "is_enabled": 1 if is_enabled else 0,
                    "skip_asset_check": 1  # Skip URL check since it's a local file
                }

                create_response = await client.post(
                    self._get_api_url("assets"),
                    data={"model": json.dumps(model_data)}
                )

                if create_response.status_code not in [200, 201]:
                    logger.error(f"Anthias asset creation failed: {create_response.status_code} - {create_response.text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create asset in Anthias: {create_response.text}"
                    )

                asset_data = create_response.json()

                # Add file_size to response
                asset_data["file_size"] = len(file_content)

                logger.info(f"Asset created in Anthias: {asset_data.get('asset_id')}")
                return asset_data

        except httpx.RequestError as e:
            logger.error(f"Anthias connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Anthias service"
            )
        except Exception as e:
            logger.error(f"Unexpected error uploading to Anthias: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Upload error: {str(e)}"
            )

    async def list_assets(self) -> List[Dict[str, Any]]:
        """
        Get list of all assets from Anthias

        Returns:
            list: List of asset dictionaries

        Raises:
            HTTPException: If list retrieval fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self._get_api_url("assets"))

                if response.status_code != 200:
                    logger.error(f"Anthias list failed: {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to retrieve assets from Anthias"
                    )

                assets = response.json()
                logger.info(f"Retrieved {len(assets)} assets from Anthias")
                return assets

        except httpx.RequestError as e:
            logger.error(f"Anthias connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Anthias service"
            )
        except Exception as e:
            logger.error(f"Unexpected error listing Anthias assets: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"List error: {str(e)}"
            )

    async def get_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Get details of a specific asset from Anthias

        Args:
            asset_id: Anthias asset ID

        Returns:
            dict: Asset information

        Raises:
            HTTPException: If asset not found or retrieval fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self._get_api_url(f"assets/{asset_id}")
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Asset {asset_id} not found in Anthias"
                    )

                if response.status_code != 200:
                    logger.error(f"Anthias get asset failed: {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to retrieve asset from Anthias"
                    )

                asset_data = response.json()
                return asset_data

        except HTTPException:
            raise
        except httpx.RequestError as e:
            logger.error(f"Anthias connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Anthias service"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting Anthias asset: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Get asset error: {str(e)}"
            )

    async def delete_asset(self, asset_id: str) -> bool:
        """
        Delete an asset from Anthias

        Args:
            asset_id: Anthias asset ID

        Returns:
            bool: True if deleted successfully

        Raises:
            HTTPException: If deletion fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    self._get_api_url(f"assets/{asset_id}")
                )

                if response.status_code == 404:
                    logger.warning(f"Asset {asset_id} not found in Anthias (already deleted?)")
                    return True  # Consider already deleted as success

                if response.status_code not in [200, 204]:
                    logger.error(f"Anthias delete failed: {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to delete asset from Anthias"
                    )

                logger.info(f"Asset {asset_id} deleted from Anthias")
                return True

        except HTTPException:
            raise
        except httpx.RequestError as e:
            logger.error(f"Anthias connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Anthias service"
            )
        except Exception as e:
            logger.error(f"Unexpected error deleting Anthias asset: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Delete error: {str(e)}"
            )

    async def update_asset(
        self,
        asset_id: str,
        name: Optional[str] = None,
        duration: Optional[int] = None,
        is_enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update asset metadata in Anthias

        Args:
            asset_id: Anthias asset ID
            name: New name (optional)
            duration: New duration in seconds (optional)
            is_enabled: New enabled status (optional)

        Returns:
            dict: Updated asset information

        Raises:
            HTTPException: If update fails
        """
        try:
            # Build update data
            data = {}
            if name is not None:
                data["name"] = name
            if duration is not None:
                data["duration"] = str(duration)
            if is_enabled is not None:
                data["is_enabled"] = "1" if is_enabled else "0"

            if not data:
                raise HTTPException(
                    status_code=400,
                    detail="No update data provided"
                )

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    self._get_api_url(f"assets/{asset_id}"),
                    data=data
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Asset {asset_id} not found in Anthias"
                    )

                if response.status_code != 200:
                    logger.error(f"Anthias update failed: {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to update asset in Anthias"
                    )

                asset_data = response.json()
                logger.info(f"Asset {asset_id} updated in Anthias")
                return asset_data

        except HTTPException:
            raise
        except httpx.RequestError as e:
            logger.error(f"Anthias connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Anthias service"
            )
        except Exception as e:
            logger.error(f"Unexpected error updating Anthias asset: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Update error: {str(e)}"
            )

    async def get_asset_url(self, asset_id: str) -> str:
        """
        Get public URL for an asset

        Args:
            asset_id: Anthias asset ID

        Returns:
            str: Public URL to access the asset

        Raises:
            HTTPException: If asset not found
        """
        try:
            # Get asset info to find URI
            asset = await self.get_asset(asset_id)
            uri = asset.get("uri")

            if not uri:
                raise HTTPException(
                    status_code=500,
                    detail="Asset URI not found"
                )

            # Construct full URL using public URL (accessible from browser)
            # Anthias serves assets at public_url + uri
            asset_url = f"{self.public_url}{uri}"
            return asset_url

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting asset URL: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"URL error: {str(e)}"
            )

    async def get_asset_content(self, asset_id: str) -> bytes:
        """
        Get asset file content from Anthias content API

        Args:
            asset_id: Anthias asset ID

        Returns:
            bytes: File content (decoded from base64)

        Raises:
            HTTPException: If asset not found or fetch fails
        """
        try:
            import base64

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self._get_api_url(f"assets/{asset_id}/content")
                )

                if response.status_code == 404:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Asset {asset_id} not found"
                    )

                if response.status_code != 200:
                    logger.error(f"Anthias content fetch failed: {response.status_code}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to fetch asset content from Anthias"
                    )

                data = response.json()
                content_base64 = data.get("content")

                if not content_base64:
                    raise HTTPException(
                        status_code=500,
                        detail="No content in Anthias response"
                    )

                # Decode base64 to bytes
                content_bytes = base64.b64decode(content_base64)
                return content_bytes

        except HTTPException:
            raise
        except httpx.RequestError as e:
            logger.error(f"Anthias connection error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Cannot connect to Anthias service"
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching content: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Content fetch error: {str(e)}"
            )

    async def check_connection(self) -> bool:
        """
        Check if Anthias service is accessible

        Returns:
            bool: True if Anthias is accessible

        Raises:
            HTTPException: If connection check fails
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._get_api_url("assets"))
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Anthias connection check failed: {e}")
            return False


# Singleton instance
anthias_service = AnthiasService()
