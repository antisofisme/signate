"""
Schedule Domain Interfaces
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime


class IScheduleRepository(ABC):
    """Interface for schedule repository"""
    
    @abstractmethod
    def find_active_schedules(
        self,
        organization_id: int,
        current_time: datetime
    ) -> List:
        """Find active schedules for organization at current time"""
        pass