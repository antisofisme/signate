"""
DeviceConnectionLogRepository
Data access layer for device connection logs
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from .models import DeviceConnectionLogModel
from ..dtos import ConnectionLogEntryDTO


class DeviceConnectionLogRepository:
    """Repository for device connection logs"""

    def __init__(self, db: Session):
        self.db = db

    def save_logs_batch(
        self,
        device_id: int,
        logs: List[ConnectionLogEntryDTO]
    ) -> int:
        """
        Bulk insert connection logs

        Args:
            device_id: Device ID
            logs: List of log entries

        Returns:
            Number of logs saved
        """
        try:
            log_models = [
                DeviceConnectionLogModel(
                    device_id=device_id,
                    logged_at=log.logged_at,
                    event_type=log.event_type,
                    status=log.status,
                    latency_ms=log.latency_ms,
                    error_message=log.error_message,
                    download_speed_mbps=log.download_speed_mbps,
                    upload_speed_mbps=log.upload_speed_mbps,
                    # New dedicated fields (migration 046)
                    connection_type=log.connection_type,
                    effective_type=log.effective_type,
                    rtt_ms=log.rtt_ms,
                    endpoint=log.endpoint,
                    http_status=log.http_status,
                    test_trigger=log.test_trigger,
                    test_duration_ms=log.test_duration_ms,
                    extra_metadata=log.metadata
                )
                for log in logs
            ]

            self.db.add_all(log_models)
            self.db.commit()

            return len(log_models)

        except Exception as e:
            self.db.rollback()
            raise e

    def get_recent_logs(
        self,
        device_id: int,
        limit: int = 100,
        event_type: Optional[str] = None
    ) -> List[DeviceConnectionLogModel]:
        """
        Get recent logs for a device

        Args:
            device_id: Device ID
            limit: Maximum number of logs to return
            event_type: Filter by event type (optional)

        Returns:
            List of log models
        """
        query = self.db.query(DeviceConnectionLogModel).filter(
            DeviceConnectionLogModel.device_id == device_id
        )

        if event_type:
            query = query.filter(DeviceConnectionLogModel.event_type == event_type)

        return query.order_by(desc(DeviceConnectionLogModel.logged_at)).limit(limit).all()

    def get_logs_by_date_range(
        self,
        device_id: int,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None
    ) -> List[DeviceConnectionLogModel]:
        """
        Get logs within a date range

        Args:
            device_id: Device ID
            start_date: Start date
            end_date: End date
            event_type: Filter by event type (optional)

        Returns:
            List of log models
        """
        query = self.db.query(DeviceConnectionLogModel).filter(
            DeviceConnectionLogModel.device_id == device_id,
            DeviceConnectionLogModel.logged_at >= start_date,
            DeviceConnectionLogModel.logged_at <= end_date
        )

        if event_type:
            query = query.filter(DeviceConnectionLogModel.event_type == event_type)

        return query.order_by(desc(DeviceConnectionLogModel.logged_at)).all()

    def count_logs(
        self,
        device_id: int,
        event_type: Optional[str] = None
    ) -> int:
        """
        Count logs for a device

        Args:
            device_id: Device ID
            event_type: Filter by event type (optional)

        Returns:
            Number of logs
        """
        query = self.db.query(DeviceConnectionLogModel).filter(
            DeviceConnectionLogModel.device_id == device_id
        )

        if event_type:
            query = query.filter(DeviceConnectionLogModel.event_type == event_type)

        return query.count()

    def delete_old_logs(
        self,
        device_id: int,
        before_date: datetime
    ) -> int:
        """
        Delete logs older than a specific date

        Args:
            device_id: Device ID
            before_date: Delete logs before this date

        Returns:
            Number of logs deleted
        """
        try:
            result = self.db.query(DeviceConnectionLogModel).filter(
                DeviceConnectionLogModel.device_id == device_id,
                DeviceConnectionLogModel.logged_at < before_date
            ).delete()

            self.db.commit()
            return result

        except Exception as e:
            self.db.rollback()
            raise e
