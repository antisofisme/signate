"""
Device Health Metric Domain Model
Business logic for device health monitoring
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from decimal import Decimal


@dataclass
class DeviceHealthMetric:
    """
    Device Health Metric entity - represents health status of a device
    """
    id: int
    device_id: int
    organization_id: int

    # System metrics
    cpu_usage: Optional[Decimal] = None  # Percentage (0-100)
    memory_usage: Optional[Decimal] = None  # Percentage (0-100)
    memory_total_mb: Optional[int] = None
    memory_used_mb: Optional[int] = None
    disk_usage: Optional[Decimal] = None  # Percentage (0-100)
    disk_total_gb: Optional[int] = None
    disk_used_gb: Optional[int] = None

    # Network metrics
    network_latency_ms: Optional[int] = None
    network_download_mbps: Optional[Decimal] = None
    network_upload_mbps: Optional[Decimal] = None
    connection_quality: Optional[str] = None  # 'excellent', 'good', 'fair', 'poor'

    # Display metrics
    display_resolution: Optional[str] = None
    display_refresh_rate: Optional[int] = None
    gpu_usage: Optional[Decimal] = None

    # Player metrics
    player_version: Optional[str] = None
    player_uptime_hours: Optional[int] = None
    content_errors_count: int = 0
    last_error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None

    # Health status
    overall_status: str = 'healthy'  # 'healthy', 'warning', 'critical', 'offline'
    is_alert_triggered: bool = False
    alert_message: Optional[str] = None

    # Additional data
    metadata: Dict[str, Any] = None

    # Timestamps
    recorded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize defaults"""
        if self.metadata is None:
            self.metadata = {}

    def is_healthy(self) -> bool:
        """Check if device is in healthy state"""
        return self.overall_status == 'healthy'

    def is_warning(self) -> bool:
        """Check if device has warnings"""
        return self.overall_status == 'warning'

    def is_critical(self) -> bool:
        """Check if device is in critical state"""
        return self.overall_status == 'critical'

    def is_offline(self) -> bool:
        """Check if device is offline"""
        return self.overall_status == 'offline'

    def has_high_cpu(self, threshold: float = 80.0) -> bool:
        """Check if CPU usage is above threshold"""
        return self.cpu_usage is not None and float(self.cpu_usage) >= threshold

    def has_high_memory(self, threshold: float = 80.0) -> bool:
        """Check if memory usage is above threshold"""
        return self.memory_usage is not None and float(self.memory_usage) >= threshold

    def has_high_disk(self, threshold: float = 80.0) -> bool:
        """Check if disk usage is above threshold"""
        return self.disk_usage is not None and float(self.disk_usage) >= threshold

    def has_high_latency(self, threshold: int = 200) -> bool:
        """Check if network latency is above threshold (ms)"""
        return self.network_latency_ms is not None and self.network_latency_ms >= threshold

    def has_content_errors(self) -> bool:
        """Check if device has content loading errors"""
        return self.content_errors_count > 0

    def calculate_overall_status(self) -> str:
        """
        Calculate overall health status based on metrics

        Returns:
            'healthy', 'warning', 'critical', or 'offline'
        """
        # Check for critical conditions
        if (
            self.has_high_cpu(90.0) or
            self.has_high_memory(90.0) or
            self.has_high_disk(90.0) or
            self.has_high_latency(500)
        ):
            return 'critical'

        # Check for warning conditions
        if (
            self.has_high_cpu(80.0) or
            self.has_high_memory(80.0) or
            self.has_high_disk(80.0) or
            self.has_high_latency(200) or
            self.has_content_errors()
        ):
            return 'warning'

        return 'healthy'

    def determine_connection_quality(self) -> Optional[str]:
        """
        Determine connection quality based on latency and speed

        Returns:
            'excellent', 'good', 'fair', or 'poor'
        """
        if self.network_latency_ms is None:
            return None

        latency = self.network_latency_ms

        if latency < 50:
            return 'excellent'
        elif latency < 100:
            return 'good'
        elif latency < 200:
            return 'fair'
        else:
            return 'poor'

    @staticmethod
    def create_new(
        device_id: int,
        organization_id: int,
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
    ) -> 'DeviceHealthMetric':
        """
        Create a new health metric record

        Args:
            device_id: Device ID
            organization_id: Organization ID
            All other parameters are optional health metrics

        Returns:
            New DeviceHealthMetric instance
        """
        now = datetime.now(timezone.utc)

        # Convert float to Decimal for database storage
        metric = DeviceHealthMetric(
            id=0,  # Will be set by database
            device_id=device_id,
            organization_id=organization_id,
            cpu_usage=Decimal(str(cpu_usage)) if cpu_usage is not None else None,
            memory_usage=Decimal(str(memory_usage)) if memory_usage is not None else None,
            memory_total_mb=memory_total_mb,
            memory_used_mb=memory_used_mb,
            disk_usage=Decimal(str(disk_usage)) if disk_usage is not None else None,
            disk_total_gb=disk_total_gb,
            disk_used_gb=disk_used_gb,
            network_latency_ms=network_latency_ms,
            network_download_mbps=Decimal(str(network_download_mbps)) if network_download_mbps is not None else None,
            network_upload_mbps=Decimal(str(network_upload_mbps)) if network_upload_mbps is not None else None,
            display_resolution=display_resolution,
            display_refresh_rate=display_refresh_rate,
            gpu_usage=Decimal(str(gpu_usage)) if gpu_usage is not None else None,
            player_version=player_version,
            player_uptime_hours=player_uptime_hours,
            content_errors_count=content_errors_count,
            last_error_message=last_error_message,
            last_error_at=last_error_at,
            metadata=metadata or {},
            recorded_at=now,
            created_at=now
        )

        # Auto-calculate overall status and connection quality
        metric.overall_status = metric.calculate_overall_status()
        metric.connection_quality = metric.determine_connection_quality()

        return metric


@dataclass
class HealthAlert:
    """
    Health alert - represents a triggered health alert
    """
    alert_type: str  # 'cpu_high', 'memory_high', 'disk_high', 'network_slow'
    alert_level: str  # 'info', 'warning', 'critical'
    alert_message: str
    metric_value: Decimal
    threshold_value: Decimal
    recorded_at: datetime

    def is_critical(self) -> bool:
        """Check if alert is critical"""
        return self.alert_level == 'critical'

    def is_warning(self) -> bool:
        """Check if alert is warning"""
        return self.alert_level == 'warning'


@dataclass
class OrganizationHealthSummary:
    """
    Organization-wide health summary
    """
    total_devices: int
    healthy_devices: int
    warning_devices: int
    critical_devices: int
    offline_devices: int
    avg_cpu_usage: Optional[Decimal]
    avg_memory_usage: Optional[Decimal]
    avg_disk_usage: Optional[Decimal]
    devices_with_errors: int

    def get_health_percentage(self) -> float:
        """Get percentage of healthy devices"""
        if self.total_devices == 0:
            return 0.0
        return (self.healthy_devices / self.total_devices) * 100

    def has_critical_devices(self) -> bool:
        """Check if organization has any critical devices"""
        return self.critical_devices > 0

    def has_offline_devices(self) -> bool:
        """Check if organization has any offline devices"""
        return self.offline_devices > 0
