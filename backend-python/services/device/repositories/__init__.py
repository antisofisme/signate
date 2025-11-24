"""
Device Repositories
Data access layer for device domain
"""

from .device_repo import DeviceRepository
from .device_log_repository import DeviceLogRepository

__all__ = ["DeviceRepository", "DeviceLogRepository"]
