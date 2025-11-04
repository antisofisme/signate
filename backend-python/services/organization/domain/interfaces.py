"""
Organization Repository Interface
Defines contract for data access
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .organization import Organization


class IOrganizationRepository(ABC):
    """Organization repository interface"""

    @abstractmethod
    def find_by_id(self, org_id: int) -> Optional[Organization]:
        """Find organization by ID"""
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Organization]:
        """Find organization by name"""
        pass

    @abstractmethod
    def find_by_pin(self, pin: str) -> Optional[Organization]:
        """Find organization by PIN"""
        pass

    @abstractmethod
    def get_all(self, active_only: bool = False) -> List[Organization]:
        """Get all organizations"""
        pass

    @abstractmethod
    def create(self, organization: Organization) -> Organization:
        """Create new organization"""
        pass

    @abstractmethod
    def update(self, organization: Organization) -> Organization:
        """Update existing organization"""
        pass

    @abstractmethod
    def delete(self, org_id: int) -> bool:
        """Delete organization"""
        pass

    @abstractmethod
    def count_users(self, org_id: int) -> int:
        """Count users in organization"""
        pass

    @abstractmethod
    def count_devices(self, org_id: int) -> int:
        """Count devices in organization"""
        pass
