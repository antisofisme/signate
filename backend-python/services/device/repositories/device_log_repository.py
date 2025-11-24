"""
Device Log Repository
Data access layer for device console logs
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from .models import DeviceLogModel


class DeviceLogRepository:
    """Repository for device log operations"""

    def __init__(self, db: Session):
        self.db = db

    def save_logs_batch(
        self,
        device_id: int,
        organization_id: int,
        logs: List[dict]
    ) -> int:
        """
        Bulk insert device logs

        Args:
            device_id: Device ID
            organization_id: Organization ID for multi-tenancy
            logs: List of log dictionaries with keys:
                - level: str (log, info, warn, error, debug)
                - message: str
                - timestamp: str (ISO format)
                - source: Optional[str] (file:line)
                - stack_trace: Optional[str]
                - user_agent: Optional[str]
                - url: Optional[str]

        Returns:
            Number of logs inserted
        """
        try:
            log_models = []
            for log in logs:
                # Parse timestamp
                recorded_at = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))

                log_model = DeviceLogModel(
                    device_id=device_id,
                    organization_id=organization_id,
                    log_level=log['level'],
                    message=log['message'],
                    source=log.get('source'),
                    stack_trace=log.get('stack_trace'),
                    user_agent=log.get('user_agent'),
                    url=log.get('url'),
                    recorded_at=recorded_at
                )
                log_models.append(log_model)

            # Bulk insert with single SQL statement
            self.db.add_all(log_models)
            self.db.commit()

            return len(log_models)

        except Exception as e:
            self.db.rollback()
            raise e

    def find_by_device_id(
        self,
        device_id: int,
        log_level: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> tuple[List[DeviceLogModel], int]:
        """
        Find logs by device ID with pagination

        Args:
            device_id: Device ID
            log_level: Optional filter by log level
            limit: Number of logs to return
            skip: Number of logs to skip

        Returns:
            Tuple of (logs, total_count)
        """
        query = self.db.query(DeviceLogModel).filter(
            DeviceLogModel.device_id == device_id
        )

        # Filter by log level if specified
        if log_level:
            query = query.filter(DeviceLogModel.log_level == log_level)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        logs = query.order_by(desc(DeviceLogModel.recorded_at)).offset(skip).limit(limit).all()

        return logs, total

    def find_by_organization_id(
        self,
        organization_id: int,
        log_level: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> tuple[List[DeviceLogModel], int]:
        """
        Find logs by organization ID with pagination

        Args:
            organization_id: Organization ID
            log_level: Optional filter by log level
            limit: Number of logs to return
            skip: Number of logs to skip

        Returns:
            Tuple of (logs, total_count)
        """
        query = self.db.query(DeviceLogModel).filter(
            DeviceLogModel.organization_id == organization_id
        )

        # Filter by log level if specified
        if log_level:
            query = query.filter(DeviceLogModel.log_level == log_level)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        logs = query.order_by(desc(DeviceLogModel.recorded_at)).offset(skip).limit(limit).all()

        return logs, total

    def delete_by_device_id(self, device_id: int) -> int:
        """
        Delete all logs for a device

        Args:
            device_id: Device ID

        Returns:
            Number of logs deleted
        """
        count = self.db.query(DeviceLogModel).filter(
            DeviceLogModel.device_id == device_id
        ).delete()

        self.db.commit()
        return count

    def delete_old_logs(self, days: int = 30) -> int:
        """
        Delete logs older than specified days (for retention policy)

        Args:
            days: Number of days to keep

        Returns:
            Number of logs deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        count = self.db.query(DeviceLogModel).filter(
            DeviceLogModel.recorded_at < cutoff_date
        ).delete()

        self.db.commit()
        return count

    def count_by_device_id(self, device_id: int, log_level: Optional[str] = None) -> int:
        """
        Count logs for a device

        Args:
            device_id: Device ID
            log_level: Optional filter by log level

        Returns:
            Number of logs
        """
        query = self.db.query(DeviceLogModel).filter(
            DeviceLogModel.device_id == device_id
        )

        if log_level:
            query = query.filter(DeviceLogModel.log_level == log_level)

        return query.count()
