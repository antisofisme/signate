"""
Device Health Repository
Data access layer for device health metrics
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from decimal import Decimal

from .models import DeviceHealthMetricModel
from ..domain.device_health import (
    DeviceHealthMetric,
    HealthAlert,
    OrganizationHealthSummary
)


class DeviceHealthRepository:
    """
    Repository for device health metrics persistence
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, health_metric: DeviceHealthMetric) -> DeviceHealthMetric:
        """
        Create new health metric record

        Args:
            health_metric: DeviceHealthMetric domain model

        Returns:
            Created DeviceHealthMetric with database ID
        """
        db_metric = DeviceHealthMetricModel(
            device_id=health_metric.device_id,
            organization_id=health_metric.organization_id,
            cpu_usage=health_metric.cpu_usage,
            memory_usage=health_metric.memory_usage,
            memory_total_mb=health_metric.memory_total_mb,
            memory_used_mb=health_metric.memory_used_mb,
            disk_usage=health_metric.disk_usage,
            disk_total_gb=health_metric.disk_total_gb,
            disk_used_gb=health_metric.disk_used_gb,
            network_latency_ms=health_metric.network_latency_ms,
            network_download_mbps=health_metric.network_download_mbps,
            network_upload_mbps=health_metric.network_upload_mbps,
            connection_quality=health_metric.connection_quality,
            display_resolution=health_metric.display_resolution,
            display_refresh_rate=health_metric.display_refresh_rate,
            gpu_usage=health_metric.gpu_usage,
            player_version=health_metric.player_version,
            player_uptime_hours=health_metric.player_uptime_hours,
            content_errors_count=health_metric.content_errors_count,
            last_error_message=health_metric.last_error_message,
            last_error_at=health_metric.last_error_at,
            overall_status=health_metric.overall_status,
            alert_triggered=health_metric.alert_triggered,
            alert_message=health_metric.alert_message,
            extra_data=health_metric.metadata,
            recorded_at=health_metric.recorded_at
        )

        self.db.add(db_metric)
        self.db.commit()
        self.db.refresh(db_metric)

        return self._to_domain(db_metric)

    def get_latest(self, device_id: int) -> Optional[DeviceHealthMetric]:
        """
        Get latest health metrics for device using stored procedure

        Args:
            device_id: Device ID

        Returns:
            Latest DeviceHealthMetric or None
        """
        result = self.db.execute(
            text("SELECT * FROM get_latest_device_health(:device_id)"),
            {"device_id": device_id}
        )

        row = result.first()
        if not row:
            return None

        return self._row_to_domain(row, device_id)

    def get_history(self, device_id: int, hours: int = 24) -> List[DeviceHealthMetric]:
        """
        Get health history for device using stored procedure

        Args:
            device_id: Device ID
            hours: Number of hours of history to retrieve

        Returns:
            List of DeviceHealthMetric objects
        """
        result = self.db.execute(
            text("SELECT * FROM get_device_health_history(:device_id, :hours)"),
            {"device_id": device_id, "hours": hours}
        )

        metrics = []
        for row in result:
            metric = DeviceHealthMetric(
                id=row.id,
                device_id=device_id,
                organization_id=0,  # Not included in history function
                cpu_usage=row.cpu_usage,
                memory_usage=row.memory_usage,
                disk_usage=row.disk_usage,
                network_latency_ms=row.network_latency_ms,
                connection_quality=row.connection_quality,
                overall_status=row.overall_status,
                recorded_at=row.recorded_at
            )
            metrics.append(metric)

        return metrics

    def get_alerts(self, device_id: int) -> List[HealthAlert]:
        """
        Get health alerts for device using stored procedure

        Args:
            device_id: Device ID

        Returns:
            List of HealthAlert objects
        """
        result = self.db.execute(
            text("SELECT * FROM check_device_health_alerts(:device_id)"),
            {"device_id": device_id}
        )

        alerts = []
        for row in result:
            alert = HealthAlert(
                alert_type=row.alert_type,
                alert_level=row.alert_level,
                alert_message=row.alert_message,
                metric_value=row.metric_value,
                threshold_value=row.threshold_value,
                recorded_at=row.recorded_at
            )
            alerts.append(alert)

        return alerts

    def get_organization_summary(self, organization_id: int) -> Optional[OrganizationHealthSummary]:
        """
        Get organization-wide health summary using stored procedure

        Args:
            organization_id: Organization ID

        Returns:
            OrganizationHealthSummary or None
        """
        result = self.db.execute(
            text("SELECT * FROM get_organization_health_summary(:organization_id)"),
            {"organization_id": organization_id}
        )

        row = result.first()
        if not row:
            return None

        return OrganizationHealthSummary(
            total_devices=row.total_devices,
            healthy_devices=row.healthy_devices,
            warning_devices=row.warning_devices,
            critical_devices=row.critical_devices,
            offline_devices=row.offline_devices,
            avg_cpu_usage=row.avg_cpu_usage,
            avg_memory_usage=row.avg_memory_usage,
            avg_disk_usage=row.avg_disk_usage,
            devices_with_errors=row.devices_with_errors
        )

    def cleanup_old_metrics(self, retention_days: int = 30) -> int:
        """
        Clean up old health metrics using stored procedure

        Args:
            retention_days: Number of days to retain metrics

        Returns:
            Number of deleted records
        """
        result = self.db.execute(
            text("SELECT cleanup_old_health_metrics(:retention_days)"),
            {"retention_days": retention_days}
        )

        self.db.commit()
        return result.scalar()

    def _to_domain(self, db_metric: DeviceHealthMetricModel) -> DeviceHealthMetric:
        """Convert database model to domain model"""
        return DeviceHealthMetric(
            id=db_metric.id,
            device_id=db_metric.device_id,
            organization_id=db_metric.organization_id,
            cpu_usage=db_metric.cpu_usage,
            memory_usage=db_metric.memory_usage,
            memory_total_mb=db_metric.memory_total_mb,
            memory_used_mb=db_metric.memory_used_mb,
            disk_usage=db_metric.disk_usage,
            disk_total_gb=db_metric.disk_total_gb,
            disk_used_gb=db_metric.disk_used_gb,
            network_latency_ms=db_metric.network_latency_ms,
            network_download_mbps=db_metric.network_download_mbps,
            network_upload_mbps=db_metric.network_upload_mbps,
            connection_quality=db_metric.connection_quality,
            display_resolution=db_metric.display_resolution,
            display_refresh_rate=db_metric.display_refresh_rate,
            gpu_usage=db_metric.gpu_usage,
            player_version=db_metric.player_version,
            player_uptime_hours=db_metric.player_uptime_hours,
            content_errors_count=db_metric.content_errors_count,
            last_error_message=db_metric.last_error_message,
            last_error_at=db_metric.last_error_at,
            overall_status=db_metric.overall_status,
            alert_triggered=db_metric.alert_triggered,
            alert_message=db_metric.alert_message,
            metadata=db_metric.extra_data or {},
            recorded_at=db_metric.recorded_at,
            created_at=db_metric.created_at
        )

    def _row_to_domain(self, row, device_id: int) -> DeviceHealthMetric:
        """Convert SQL row to domain model"""
        return DeviceHealthMetric(
            id=row.id,
            device_id=device_id,
            organization_id=0,  # Not included in stored function
            cpu_usage=row.cpu_usage,
            memory_usage=row.memory_usage,
            memory_total_mb=row.memory_total_mb,
            memory_used_mb=row.memory_used_mb,
            disk_usage=row.disk_usage,
            disk_total_gb=row.disk_total_gb,
            disk_used_gb=row.disk_used_gb,
            network_latency_ms=row.network_latency_ms,
            network_download_mbps=row.network_download_mbps,
            network_upload_mbps=row.network_upload_mbps,
            connection_quality=row.connection_quality,
            display_resolution=row.display_resolution,
            display_refresh_rate=row.display_refresh_rate,
            gpu_usage=row.gpu_usage,
            player_version=row.player_version,
            player_uptime_hours=row.player_uptime_hours,
            content_errors_count=row.content_errors_count,
            last_error_message=row.last_error_message,
            last_error_at=row.last_error_at,
            overall_status=row.overall_status,
            alert_triggered=row.alert_triggered,
            alert_message=row.alert_message,
            metadata=getattr(row, 'metadata', None) or getattr(row, 'extra_data', None) or {},
            recorded_at=row.recorded_at
        )
