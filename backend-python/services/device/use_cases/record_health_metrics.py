"""
Record Health Metrics Use Case
Record device health metrics from player
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ..domain.device_health import DeviceHealthMetric
from ..repositories.device_health_repo import DeviceHealthRepository
from ..repositories.device_repo import DeviceRepository
from shared.errors import NotFoundError, ValidationError


class RecordHealthMetricsUseCase:
    """
    Use case for recording device health metrics
    Called by player to report health status
    """

    def __init__(
        self,
        health_repo: DeviceHealthRepository,
        device_repo: DeviceRepository
    ):
        self.health_repo = health_repo
        self.device_repo = device_repo

    def execute(
        self,
        device_id: int,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        memory_total_mb: Optional[int] = None,
        memory_used_mb: Optional[int] = None,
        disk_usage: Optional[float] = None,
        disk_total_gb: Optional[int] = None,
        disk_used_gb: Optional[int] = None,
        network_latency_ms: Optional[int] = None,
        network_download_mbps: Optional[float] = None,
        network_upload_mbps: Optional[float] = None,
        display_resolution: Optional[str] = None,
        display_refresh_rate: Optional[int] = None,
        gpu_usage: Optional[float] = None,
        player_version: Optional[str] = None,
        player_uptime_hours: Optional[int] = None,
        content_errors_count: int = 0,
        last_error_message: Optional[str] = None,
        last_error_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeviceHealthMetric:
        """
        Record health metrics for device

        Args:
            device_id: Device ID
            All other parameters are optional health metrics

        Returns:
            Created DeviceHealthMetric

        Raises:
            NotFoundError: If device not found
            ValidationError: If validation fails
        """

        # Verify device exists
        device = self.device_repo.find_by_id(device_id)
        if not device:
            raise NotFoundError(
                message=f"Device with ID {device_id} not found",
                resource_type="device",
                resource_id=device_id
            )

        # Validate percentage metrics
        if cpu_usage is not None and not (0 <= cpu_usage <= 100):
            raise ValidationError(
                message="CPU usage must be between 0 and 100",
                details={"cpu_usage": cpu_usage}
            )

        if memory_usage is not None and not (0 <= memory_usage <= 100):
            raise ValidationError(
                message="Memory usage must be between 0 and 100",
                details={"memory_usage": memory_usage}
            )

        if disk_usage is not None and not (0 <= disk_usage <= 100):
            raise ValidationError(
                message="Disk usage must be between 0 and 100",
                details={"disk_usage": disk_usage}
            )

        if gpu_usage is not None and not (0 <= gpu_usage <= 100):
            raise ValidationError(
                message="GPU usage must be between 0 and 100",
                details={"gpu_usage": gpu_usage}
            )

        # Create health metric
        health_metric = DeviceHealthMetric.create_new(
            device_id=device_id,
            organization_id=device.organization_id,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            memory_total_mb=memory_total_mb,
            memory_used_mb=memory_used_mb,
            disk_usage=disk_usage,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            network_latency_ms=network_latency_ms,
            network_download_mbps=network_download_mbps,
            network_upload_mbps=network_upload_mbps,
            display_resolution=display_resolution,
            display_refresh_rate=display_refresh_rate,
            gpu_usage=gpu_usage,
            player_version=player_version,
            player_uptime_hours=player_uptime_hours,
            content_errors_count=content_errors_count,
            last_error_message=last_error_message,
            last_error_at=last_error_at,
            metadata=metadata
        )

        # Save to database
        created_metric = self.health_repo.create(health_metric)

        return created_metric
