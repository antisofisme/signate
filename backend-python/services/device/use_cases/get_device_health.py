"""
Get Device Health Use Case
Retrieve device health metrics and alerts
"""

from typing import Optional, List, Tuple

from ..domain.device_health import DeviceHealthMetric, HealthAlert, OrganizationHealthSummary
from ..repositories.device_health_repo import DeviceHealthRepository
from ..repositories.device_repo import DeviceRepository
from shared.errors import NotFoundError


class GetDeviceHealthUseCase:
    """
    Use case for getting latest device health metrics
    """

    def __init__(
        self,
        health_repo: DeviceHealthRepository,
        device_repo: DeviceRepository
    ):
        self.health_repo = health_repo
        self.device_repo = device_repo

    def execute(self, device_id: int) -> Optional[DeviceHealthMetric]:
        """
        Get latest health metrics for device

        Args:
            device_id: Device ID

        Returns:
            Latest DeviceHealthMetric or None

        Raises:
            NotFoundError: If device not found
        """

        # Verify device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device with ID {device_id} not found",
                resource_type="device",
                resource_id=device_id
            )

        # Get latest health metrics
        health_metric = self.health_repo.get_latest(device_id)

        return health_metric


class GetDeviceHealthWithAlertsUseCase:
    """
    Use case for getting device health with alerts
    """

    def __init__(
        self,
        health_repo: DeviceHealthRepository,
        device_repo: DeviceRepository
    ):
        self.health_repo = health_repo
        self.device_repo = device_repo

    def execute(self, device_id: int) -> Tuple[Optional[DeviceHealthMetric], List[HealthAlert]]:
        """
        Get latest health metrics with alerts for device

        Args:
            device_id: Device ID

        Returns:
            Tuple of (DeviceHealthMetric or None, List of HealthAlert)

        Raises:
            NotFoundError: If device not found
        """

        # Verify device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device with ID {device_id} not found",
                resource_type="device",
                resource_id=device_id
            )

        # Get latest health metrics
        health_metric = self.health_repo.get_latest(device_id)

        # Get health alerts
        alerts = self.health_repo.get_alerts(device_id)

        return health_metric, alerts


class GetDeviceHealthHistoryUseCase:
    """
    Use case for getting device health history
    """

    def __init__(
        self,
        health_repo: DeviceHealthRepository,
        device_repo: DeviceRepository
    ):
        self.health_repo = health_repo
        self.device_repo = device_repo

    def execute(self, device_id: int, hours: int = 24) -> List[DeviceHealthMetric]:
        """
        Get health history for device

        Args:
            device_id: Device ID
            hours: Number of hours of history to retrieve

        Returns:
            List of DeviceHealthMetric objects

        Raises:
            NotFoundError: If device not found
        """

        # Verify device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device with ID {device_id} not found",
                resource_type="device",
                resource_id=device_id
            )

        # Validate hours parameter
        if hours < 1 or hours > 168:  # Max 1 week
            hours = 24

        # Get health history
        history = self.health_repo.get_history(device_id, hours)

        return history


class GetOrganizationHealthSummaryUseCase:
    """
    Use case for getting organization-wide health summary
    """

    def __init__(self, health_repo: DeviceHealthRepository):
        self.health_repo = health_repo

    def execute(self, organization_id: int) -> Optional[OrganizationHealthSummary]:
        """
        Get organization-wide health summary

        Args:
            organization_id: Organization ID

        Returns:
            OrganizationHealthSummary or None
        """

        # Get organization health summary
        summary = self.health_repo.get_organization_summary(organization_id)

        return summary
