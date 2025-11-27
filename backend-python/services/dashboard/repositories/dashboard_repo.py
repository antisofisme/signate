"""
Dashboard Repository Implementation

Data access layer for dashboard statistics and metrics.
Handles all database queries for the dashboard service.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..domain.dashboard_stats import (
    DashboardStats,
    DeviceHealthSummary,
    DeviceIssue,
    LiveDevice,
    ContentPerformance,
    ActivePlaylistAssignment,
    PlaybackTimeline,
    RecentActivity,
    SystemAlert,
    SystemInfo,
    ContentByType,
)

from services.auth.repositories.models import UserModel, AuditLogModel
from services.device.repositories.models import DeviceModel, DeviceHealthMetricModel
from services.content.repositories.models import ContentModel
from services.playlist.repositories.models import PlaylistModel, PlaylistContentModel


class DashboardRepository:
    """Dashboard repository for data access"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_latest_health_metrics(self, device_id: int) -> Optional[DeviceHealthMetricModel]:
        """Get latest health metrics for a device"""
        return self.db.query(DeviceHealthMetricModel).filter(
            DeviceHealthMetricModel.device_id == device_id
        ).order_by(DeviceHealthMetricModel.recorded_at.desc()).first()

    def _is_device_online(self, device: DeviceModel, cutoff_time: datetime) -> bool:
        """Check if device is online based on last_seen_at"""
        return device.last_seen_at and device.last_seen_at >= cutoff_time

    def _get_device_status(self, device: DeviceModel, cutoff_time: datetime) -> str:
        """Determine device status based on health metrics"""
        if not self._is_device_online(device, cutoff_time):
            return 'offline'

        metrics = self._get_latest_health_metrics(device.id)
        if not metrics:
            return 'online'

        if metrics.overall_status == 'error':
            return 'error'

        cpu_usage = float(metrics.cpu_usage) if metrics.cpu_usage else 0
        memory_usage = float(metrics.memory_usage) if metrics.memory_usage else 0
        storage_usage = float(metrics.disk_usage) if metrics.disk_usage else 0

        if cpu_usage > 80 or memory_usage > 80 or storage_usage > 80:
            return 'warning'

        return 'online'

    # ========================================================================
    # Dashboard Statistics
    # ========================================================================

    def get_dashboard_stats(self, organization_id: int) -> DashboardStats:
        """Get overall dashboard statistics"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        # Device counts
        total_devices = self.db.query(func.count(DeviceModel.id)).filter(
            DeviceModel.organization_id == organization_id
        ).scalar() or 0

        online_devices = self.db.query(func.count(DeviceModel.id)).filter(
            DeviceModel.organization_id == organization_id,
            DeviceModel.last_seen_at >= five_minutes_ago
        ).scalar() or 0

        offline_devices = total_devices - online_devices

        # Warning/Error devices - check health metrics
        warning_count = 0
        error_count = 0

        online_device_ids = self.db.query(DeviceModel.id).filter(
            DeviceModel.organization_id == organization_id,
            DeviceModel.last_seen_at >= five_minutes_ago
        ).all()

        for (device_id,) in online_device_ids:
            metrics = self._get_latest_health_metrics(device_id)
            if metrics:
                if metrics.overall_status == 'error':
                    error_count += 1
                elif (metrics.cpu_usage and float(metrics.cpu_usage) > 80) or \
                     (metrics.memory_usage and float(metrics.memory_usage) > 80) or \
                     (metrics.disk_usage and float(metrics.disk_usage) > 80):
                    warning_count += 1

        # Content stats
        total_contents = self.db.query(func.count(ContentModel.id)).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at == None
        ).scalar() or 0

        total_storage_bytes = self.db.query(func.coalesce(func.sum(ContentModel.file_size), 0)).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at == None
        ).scalar() or 0

        # Playlist stats
        active_playlists = self.db.query(func.count(PlaylistModel.id)).filter(
            PlaylistModel.organization_id == organization_id,
            PlaylistModel.is_active == True,
            PlaylistModel.deleted_at == None
        ).scalar() or 0

        return DashboardStats(
            total_devices=total_devices,
            online_devices=online_devices,
            offline_devices=offline_devices,
            warning_devices=warning_count,
            error_devices=error_count,
            total_contents=total_contents,
            total_storage_bytes=int(total_storage_bytes),
            active_playlists=active_playlists,
            total_watch_time_seconds=0,
            avg_completion_rate=0.0,
            total_playback_events=0
        )

    # ========================================================================
    # Device Health
    # ========================================================================

    def get_device_health_summary(self, organization_id: int) -> DeviceHealthSummary:
        """Get device health summary"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        # Get all devices
        devices = self.db.query(DeviceModel).filter(
            DeviceModel.organization_id == organization_id
        ).all()

        healthy = 0
        warning = 0
        error = 0
        offline = 0

        issues_map = {
            'high_cpu': [],
            'high_memory': [],
            'low_storage': [],
            'offline': [],
        }

        for device in devices:
            is_online = self._is_device_online(device, five_minutes_ago)

            if not is_online:
                offline += 1
                issues_map['offline'].append(device.device_name)
            else:
                # Get latest health metrics
                metrics = self._get_latest_health_metrics(device.id)
                has_warning = False

                if metrics:
                    if metrics.overall_status == 'error':
                        error += 1
                        continue

                    if metrics.cpu_usage and float(metrics.cpu_usage) > 80:
                        issues_map['high_cpu'].append(device.device_name)
                        has_warning = True

                    if metrics.memory_usage and float(metrics.memory_usage) > 80:
                        issues_map['high_memory'].append(device.device_name)
                        has_warning = True

                    if metrics.disk_usage and float(metrics.disk_usage) > 80:
                        issues_map['low_storage'].append(device.device_name)
                        has_warning = True

                if has_warning:
                    warning += 1
                else:
                    healthy += 1

        # Build issues list
        issues = []
        if issues_map['high_cpu']:
            issues.append(DeviceIssue(
                type='High CPU Usage',
                count=len(issues_map['high_cpu']),
                devices=issues_map['high_cpu'][:5]
            ))
        if issues_map['high_memory']:
            issues.append(DeviceIssue(
                type='High Memory Usage',
                count=len(issues_map['high_memory']),
                devices=issues_map['high_memory'][:5]
            ))
        if issues_map['low_storage']:
            issues.append(DeviceIssue(
                type='Low Storage',
                count=len(issues_map['low_storage']),
                devices=issues_map['low_storage'][:5]
            ))
        if issues_map['offline']:
            issues.append(DeviceIssue(
                type='Offline',
                count=len(issues_map['offline']),
                devices=issues_map['offline'][:5]
            ))

        return DeviceHealthSummary(
            healthy=healthy,
            warning=warning,
            error=error,
            offline=offline,
            issues=issues
        )

    # ========================================================================
    # Live Devices
    # ========================================================================

    def get_live_devices(self, organization_id: int) -> List[LiveDevice]:
        """Get live device status list"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        devices = self.db.query(DeviceModel).filter(
            DeviceModel.organization_id == organization_id
        ).order_by(DeviceModel.device_name).all()

        result = []
        for device in devices:
            # Get latest health metrics
            metrics = self._get_latest_health_metrics(device.id)
            cpu_usage = float(metrics.cpu_usage) if metrics and metrics.cpu_usage else None
            memory_usage = float(metrics.memory_usage) if metrics and metrics.memory_usage else None
            storage_usage = float(metrics.disk_usage) if metrics and metrics.disk_usage else None

            # Determine status
            status = self._get_device_status(device, five_minutes_ago)

            # Get location
            location = device.room_number or device.location_type or None

            # Get current playlist name
            current_content = None
            if device.assigned_playlist_id:
                playlist = self.db.query(PlaylistModel.name).filter(
                    PlaylistModel.id == device.assigned_playlist_id
                ).first()
                if playlist:
                    current_content = playlist[0]

            result.append(LiveDevice(
                id=device.id,
                name=device.device_name,
                status=status,
                location=location,
                current_content=current_content,
                last_seen_at=device.last_seen_at,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                storage_usage=storage_usage
            ))

        return result

    # ========================================================================
    # Content Performance
    # ========================================================================

    def get_content_performance(self, organization_id: int, limit: int) -> List[ContentPerformance]:
        """Get content performance metrics"""
        # Get contents with basic stats
        contents = self.db.query(ContentModel).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at == None
        ).order_by(ContentModel.created_at.desc()).limit(limit).all()

        result = []
        for content in contents:
            # Count how many playlist items use this content
            playlist_count = self.db.query(func.count(PlaylistContentModel.id)).filter(
                PlaylistContentModel.content_id == content.id
            ).scalar() or 0

            result.append(ContentPerformance(
                content_id=content.id,
                content_name=content.title,
                content_type=content.content_type,
                total_plays=0,  # Would need playback logs table
                unique_devices=playlist_count,
                total_duration_seconds=content.duration or 0,
                avg_completion_rate=0.0,
                last_played=content.updated_at
            ))

        return result

    # ========================================================================
    # Active Playlists
    # ========================================================================

    def get_active_playlists(self, organization_id: int) -> List[ActivePlaylistAssignment]:
        """Get active playlist assignments"""
        playlists = self.db.query(PlaylistModel).filter(
            PlaylistModel.organization_id == organization_id,
            PlaylistModel.is_active == True,
            PlaylistModel.deleted_at == None
        ).all()

        result = []
        for playlist in playlists:
            # Count items
            item_count = self.db.query(func.count(PlaylistContentModel.id)).filter(
                PlaylistContentModel.playlist_id == playlist.id
            ).scalar() or 0

            # Calculate total duration from content durations
            total_duration = self.db.query(
                func.coalesce(func.sum(
                    func.coalesce(PlaylistContentModel.duration, ContentModel.duration)
                ), 0)
            ).join(
                ContentModel, PlaylistContentModel.content_id == ContentModel.id
            ).filter(
                PlaylistContentModel.playlist_id == playlist.id
            ).scalar() or 0

            # Get assigned devices
            assigned_devices = self.db.query(DeviceModel.device_name).filter(
                DeviceModel.assigned_playlist_id == playlist.id
            ).all()
            device_names = [d[0] for d in assigned_devices]

            result.append(ActivePlaylistAssignment(
                playlist_id=playlist.id,
                playlist_name=playlist.name,
                device_count=len(device_names),
                content_count=item_count,
                total_duration_seconds=int(total_duration),
                last_updated=playlist.updated_at,
                devices=device_names[:10]
            ))

        return result

    # ========================================================================
    # Playback Timeline
    # ========================================================================

    def get_playback_timeline(self, days: int) -> List[PlaybackTimeline]:
        """Get playback timeline for the last N days"""
        now = datetime.now(timezone.utc)

        result = []
        for i in range(days - 1, -1, -1):
            date = now - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            # Placeholder - would need playback_logs table for real data
            result.append(PlaybackTimeline(
                date=date_str,
                playback_count=0,
                unique_devices=0,
                total_duration_seconds=0
            ))

        return result

    # ========================================================================
    # Recent Activity
    # ========================================================================

    def get_recent_activity(self, organization_id: int, limit: int) -> List[RecentActivity]:
        """Get recent activity from audit logs"""
        logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.organization_id == organization_id
        ).order_by(AuditLogModel.created_at.desc()).limit(limit).all()

        result = []
        for log in logs:
            # Get username
            user = self.db.query(UserModel.username).filter(UserModel.id == log.user_id).first()
            username = user[0] if user else 'System'

            result.append(RecentActivity(
                id=log.id,
                timestamp=log.created_at,
                action=log.action,
                user=username,
                resource_type=log.resource_type or '',
                resource_name=str(log.resource_id) if log.resource_id else '',
                details=str(log.details) if log.details else None
            ))

        return result

    # ========================================================================
    # System Alerts
    # ========================================================================

    def get_system_alerts(self, organization_id: int, max_alerts: int = 50) -> List[SystemAlert]:
        """Get system alerts"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        alerts = []

        # Check for offline devices
        offline_devices = self.db.query(DeviceModel).filter(
            DeviceModel.organization_id == organization_id,
            or_(
                DeviceModel.last_seen_at == None,
                DeviceModel.last_seen_at < five_minutes_ago
            )
        ).all()

        for device in offline_devices:
            last_seen_str = device.last_seen_at.isoformat() if device.last_seen_at else 'never'
            alerts.append(SystemAlert(
                id=device.id * 1000 + 1,
                severity='warning',
                title='Device Offline',
                message=f'Device "{device.device_name}" has been offline since {last_seen_str}',
                timestamp=device.last_seen_at or now,
                acknowledged=False,
                device_id=device.id,
                device_name=device.device_name
            ))

        # Check for devices with high resource usage
        online_devices = self.db.query(DeviceModel).filter(
            DeviceModel.organization_id == organization_id,
            DeviceModel.last_seen_at >= five_minutes_ago
        ).all()

        for device in online_devices:
            metrics = self._get_latest_health_metrics(device.id)
            if not metrics:
                continue

            message_parts = []
            if metrics.cpu_usage and float(metrics.cpu_usage) > 90:
                message_parts.append(f'CPU: {metrics.cpu_usage:.1f}%')
            if metrics.memory_usage and float(metrics.memory_usage) > 90:
                message_parts.append(f'Memory: {metrics.memory_usage:.1f}%')
            if metrics.disk_usage and float(metrics.disk_usage) > 90:
                message_parts.append(f'Storage: {metrics.disk_usage:.1f}%')

            if message_parts:
                alerts.append(SystemAlert(
                    id=device.id * 1000 + 2,
                    severity='error',
                    title='High Resource Usage',
                    message=f'Device "{device.device_name}" has critical resource usage: {", ".join(message_parts)}',
                    timestamp=now,
                    acknowledged=False,
                    device_id=device.id,
                    device_name=device.device_name
                ))

        return alerts[:max_alerts]

    # ========================================================================
    # System Info
    # ========================================================================

    def get_system_info(self, organization_id: int, storage_path: str) -> SystemInfo:
        """Get system information"""
        import os
        import time

        # Content storage by type
        content_stats = self.db.query(
            ContentModel.content_type,
            func.count(ContentModel.id).label('count'),
            func.coalesce(func.sum(ContentModel.file_size), 0).label('size')
        ).filter(
            ContentModel.organization_id == organization_id,
            ContentModel.deleted_at == None
        ).group_by(ContentModel.content_type).all()

        content_by_type = [
            ContentByType(type=stat[0], count=stat[1], size_bytes=int(stat[2]))
            for stat in content_stats
        ]

        # Calculate totals
        total_storage = sum(c.size_bytes for c in content_by_type)

        # Get storage path info
        try:
            stat = os.statvfs(storage_path)
            storage_total = stat.f_blocks * stat.f_frsize
            storage_free = stat.f_bavail * stat.f_frsize
            storage_used = storage_total - storage_free
        except:
            # Fallback values
            storage_total = 100 * 1024 * 1024 * 1024  # 100 GB
            storage_used = total_storage
            storage_free = storage_total - storage_used

        # Database size estimate
        database_size = total_storage // 10

        return SystemInfo(
            storage_total_bytes=storage_total,
            storage_used_bytes=storage_used,
            storage_free_bytes=storage_free,
            content_by_type=content_by_type,
            database_size_bytes=database_size,
            uptime_seconds=0  # Will be set by use case
        )
