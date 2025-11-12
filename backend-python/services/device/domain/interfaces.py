"""
Repository Interfaces
Contracts for data access
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from .device import Device


class IDeviceRepository(ABC):
    """Interface for device repository"""

    @abstractmethod
    def find_by_id(self, device_id: int, organization_id: Optional[int] = None) -> Optional[Device]:
        """Find device by ID with optional organization isolation"""
        pass

    @abstractmethod
    def find_by_code(self, unique_code: str) -> Optional[Device]:
        """Find device by unique activation code"""
        pass

    @abstractmethod
    def find_by_uuid(self, device_uuid: str, organization_id: Optional[int] = None) -> Optional[Device]:
        """Find device by UUID (for WebOS) with optional organization isolation"""
        pass

    @abstractmethod
    def list_by_organization(self, organization_id: int) -> List[Device]:
        """List all devices for an organization"""
        pass

    @abstractmethod
    def create(self, device: Device) -> Device:
        """Create new device"""
        pass

    @abstractmethod
    def update(self, device: Device) -> Device:
        """Update existing device"""
        pass

    @abstractmethod
    def delete(self, device_id: int) -> bool:
        """Delete device"""
        pass

    @abstractmethod
    def update_heartbeat(self, unique_code: str, last_seen) -> bool:
        """Update device last_seen timestamp"""
        pass

    @abstractmethod
    def count_by_organization(self, organization_id: int) -> int:
        """Count devices for organization"""
        pass

    @abstractmethod
    def find_online_devices(self, organization_id: int) -> List[Device]:
        """Find online devices (last_seen < 5 minutes ago)"""
        pass
