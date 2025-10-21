"""
Client schemas for device-facing API endpoints
"""

from pydantic import BaseModel
from typing import List


class PlaylistItem(BaseModel):
    """Schema for a single playlist item"""
    content_id: int
    title: str
    content_type: str
    url: str
    duration: int
    mime_type: str = None

    class Config:
        json_schema_extra = {
            "example": {
                "content_id": 1,
                "title": "Banner Promo",
                "content_type": "image",
                "url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
                "duration": 10,
                "mime_type": "image/jpeg"
            }
        }


class PlaylistResponse(BaseModel):
    """Schema for playlist response"""
    device_id: int
    device_name: str
    device_type: str
    total_items: int
    playlist: List[PlaylistItem]

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "device_name": "Lobby TV 1",
                "device_type": "tv",
                "total_items": 3,
                "playlist": [
                    {
                        "content_id": 1,
                        "title": "Banner Promo",
                        "content_type": "image",
                        "url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
                        "duration": 10,
                        "mime_type": "image/jpeg"
                    }
                ]
            }
        }


class DeviceStatusResponse(BaseModel):
    """Schema for device status check"""
    device_id: int
    status: str
    is_active: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "status": "active",
                "is_active": True,
                "message": "Device is active"
            }
        }
