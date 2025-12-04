"""
Dashboard Repository Implementation

Data access layer for dashboard statistics and metrics.
Handles all database queries for the dashboard service.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone, date as date_type
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, and_, or_, Integer, case, cast, Date

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
    MenuStats,
    MenuViewsByDevice,
    TopMenu,
    ScheduleOverview,
    ActiveSchedule,
)

from services.auth.repositories.models import UserModel, AuditLogModel
from services.device.repositories.models import DeviceModel, DeviceHealthMetricModel, DeviceTagModel
from services.content.repositories.models import ContentModel, ContentAssignmentModel
from services.playlist.repositories.models import PlaylistModel, PlaylistContentModel, PlaylistAssignmentModel
from services.tag.repositories.models import ContentTag
from services.menu.repositories.models import MenuModel, MenuItemModel, MenuViewModel
from services.schedule.repositories.models import Schedule
from services.analytics.repositories.models import ContentPlaybackLog


class DashboardRepository:
    """Dashboard repository for data access"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_org_filter(self, model, organization_id: Optional[int]):
        """
        Get organization filter for queries.
        - If organization_id is None (superadmin), return True (no filter, show all)
        - If organization_id is set, filter by that organization
        """
        if organization_id is None:
            return True  # No filter for superadmin
        return model.organization_id == organization_id

    def _get_latest_health_metrics(self, device_id: int) -> Optional[DeviceHealthMetricModel]:
        """Get latest health metrics for a device"""
        return self.db.query(DeviceHealthMetricModel).filter(
            DeviceHealthMetricModel.device_id == device_id
        ).order_by(DeviceHealthMetricModel.recorded_at.desc()).first()

    def _get_batch_latest_health_metrics(self, device_ids: List[int]) -> Dict[int, DeviceHealthMetricModel]:
        """Get latest health metrics for multiple devices in a single query (N+1 fix)"""
        if not device_ids:
            return {}

        # Subquery to get max recorded_at per device
        subq = self.db.query(
            DeviceHealthMetricModel.device_id,
            func.max(DeviceHealthMetricModel.recorded_at).label('max_recorded_at')
        ).filter(
            DeviceHealthMetricModel.device_id.in_(device_ids)
        ).group_by(DeviceHealthMetricModel.device_id).subquery()

        # Main query joining with subquery to get full records
        latest_metrics = self.db.query(DeviceHealthMetricModel).join(
            subq,
            and_(
                DeviceHealthMetricModel.device_id == subq.c.device_id,
                DeviceHealthMetricModel.recorded_at == subq.c.max_recorded_at
            )
        ).all()

        return {m.device_id: m for m in latest_metrics}

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

    def _get_device_status_from_metrics(
        self, device: DeviceModel, metrics: Optional[DeviceHealthMetricModel], cutoff_time: datetime
    ) -> str:
        """Determine device status from pre-fetched metrics (N+1 fix version)"""
        if not self._is_device_online(device, cutoff_time):
            return 'offline'

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

    def get_dashboard_stats(self, organization_id: Optional[int]) -> DashboardStats:
        """Get overall dashboard statistics (N+1 FIXED + real playback data)"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)
        thirty_days_ago = now - timedelta(days=30)

        # Build base queries with optional org filter
        device_base = self.db.query(func.count(DeviceModel.id))
        if organization_id is not None:
            device_base = device_base.filter(DeviceModel.organization_id == organization_id)

        # Device counts
        total_devices = device_base.scalar() or 0

        online_query = self.db.query(func.count(DeviceModel.id)).filter(
            DeviceModel.last_seen_at >= five_minutes_ago
        )
        if organization_id is not None:
            online_query = online_query.filter(DeviceModel.organization_id == organization_id)
        online_devices = online_query.scalar() or 0

        offline_devices = total_devices - online_devices

        # Warning/Error devices - use batch query instead of N+1
        warning_count = 0
        error_count = 0

        online_ids_query = self.db.query(DeviceModel.id).filter(
            DeviceModel.last_seen_at >= five_minutes_ago
        )
        if organization_id is not None:
            online_ids_query = online_ids_query.filter(DeviceModel.organization_id == organization_id)
        online_device_ids = online_ids_query.all()

        if online_device_ids:
            device_ids = [d[0] for d in online_device_ids]
            health_metrics_map = self._get_batch_latest_health_metrics(device_ids)

            for device_id in device_ids:
                metrics = health_metrics_map.get(device_id)
                if metrics:
                    if metrics.overall_status == 'error':
                        error_count += 1
                    elif (metrics.cpu_usage and float(metrics.cpu_usage) > 80) or \
                         (metrics.memory_usage and float(metrics.memory_usage) > 80) or \
                         (metrics.disk_usage and float(metrics.disk_usage) > 80):
                        warning_count += 1

        # Content stats
        content_query = self.db.query(func.count(ContentModel.id)).filter(
            ContentModel.deleted_at == None
        )
        if organization_id is not None:
            content_query = content_query.filter(ContentModel.organization_id == organization_id)
        total_contents = content_query.scalar() or 0

        storage_query = self.db.query(func.coalesce(func.sum(ContentModel.file_size), 0)).filter(
            ContentModel.deleted_at == None
        )
        if organization_id is not None:
            storage_query = storage_query.filter(ContentModel.organization_id == organization_id)
        total_storage_bytes = storage_query.scalar() or 0

        # Playlist stats
        playlist_query = self.db.query(func.count(PlaylistModel.id)).filter(
            PlaylistModel.is_active == True,
            PlaylistModel.deleted_at == None
        )
        if organization_id is not None:
            playlist_query = playlist_query.filter(PlaylistModel.organization_id == organization_id)
        active_playlists = playlist_query.scalar() or 0

        # Playback stats from content_playback_logs (REAL DATA)
        playback_query = self.db.query(
            func.coalesce(func.sum(ContentPlaybackLog.duration_seconds), 0).label('total_watch_time'),
            func.count(ContentPlaybackLog.id).label('total_events'),
            func.count(case((ContentPlaybackLog.is_completed == True, 1))).label('completed_count')
        ).filter(
            ContentPlaybackLog.started_at >= thirty_days_ago
        )
        if organization_id is not None:
            playback_query = playback_query.filter(ContentPlaybackLog.organization_id == organization_id)
        playback_stats = playback_query.first()

        total_watch_time = int(playback_stats.total_watch_time or 0) if playback_stats else 0
        total_playback_events = int(playback_stats.total_events or 0) if playback_stats else 0
        completed_count = int(playback_stats.completed_count or 0) if playback_stats else 0

        # Calculate average completion rate
        avg_completion_rate = 0.0
        if total_playback_events > 0:
            avg_completion_rate = (completed_count / total_playback_events) * 100

        return DashboardStats(
            total_devices=total_devices,
            online_devices=online_devices,
            offline_devices=offline_devices,
            warning_devices=warning_count,
            error_devices=error_count,
            total_contents=total_contents,
            total_storage_bytes=int(total_storage_bytes),
            active_playlists=active_playlists,
            total_watch_time_seconds=total_watch_time,
            avg_completion_rate=round(avg_completion_rate, 1),
            total_playback_events=total_playback_events
        )

    # ========================================================================
    # Device Health
    # ========================================================================

    def get_device_health_summary(self, organization_id: Optional[int]) -> DeviceHealthSummary:
        """Get device health summary"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        # Get all devices (no filter for superadmin)
        query = self.db.query(DeviceModel)
        if organization_id is not None:
            query = query.filter(DeviceModel.organization_id == organization_id)
        devices = query.all()

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

    def get_live_devices(self, organization_id: Optional[int]) -> List[LiveDevice]:
        """Get live device status list (N+1 FIXED - uses batch queries)"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        # Get all devices
        query = self.db.query(DeviceModel)

        # Filter by organization (None = superadmin, show all)
        if organization_id is not None:
            query = query.filter(DeviceModel.organization_id == organization_id)

        devices = query.order_by(DeviceModel.device_name).all()

        if not devices:
            return []

        # Get all device IDs
        device_ids = [d.id for d in devices]

        # Batch fetch health metrics (single query instead of N queries)
        health_metrics_map = self._get_batch_latest_health_metrics(device_ids)

        # Batch fetch direct content IDs per device (for deduplication tracking)
        direct_content_ids_map = {}
        direct_rows = self.db.query(
            ContentAssignmentModel.device_id,
            ContentAssignmentModel.content_id
        ).filter(
            ContentAssignmentModel.device_id.in_(device_ids),
            ContentAssignmentModel.device_id != None,
            or_(
                ContentAssignmentModel.expires_at == None,
                ContentAssignmentModel.expires_at > now
            )
        ).all()
        for device_id, content_id in direct_rows:
            if device_id not in direct_content_ids_map:
                direct_content_ids_map[device_id] = []
            direct_content_ids_map[device_id].append(content_id)

        # Batch fetch device tags (for tag-based content assignments)
        device_tags_map = {}
        device_tag_rows = self.db.query(
            DeviceTagModel.device_id,
            DeviceTagModel.tag_id
        ).filter(DeviceTagModel.device_id.in_(device_ids)).all()

        all_tag_ids = set()
        for device_id, tag_id in device_tag_rows:
            if device_id not in device_tags_map:
                device_tags_map[device_id] = []
            device_tags_map[device_id].append(tag_id)
            all_tag_ids.add(tag_id)

        # Batch fetch tag-based content IDs (from content_tags table - same as client playlist)
        tag_content_ids_map = {}
        if all_tag_ids:
            tag_rows = self.db.query(
                ContentTag.tag_id,
                ContentTag.content_id
            ).filter(
                ContentTag.tag_id.in_(all_tag_ids)
            ).all()
            for tag_id, content_id in tag_rows:
                if tag_id not in tag_content_ids_map:
                    tag_content_ids_map[tag_id] = []
                tag_content_ids_map[tag_id].append(content_id)

        # Batch fetch playlist assignments (from playlist_assignments table)
        device_playlist_map = {}
        playlist_assignment_rows = self.db.query(
            PlaylistAssignmentModel.device_id,
            PlaylistAssignmentModel.playlist_id
        ).filter(PlaylistAssignmentModel.device_id.in_(device_ids)).all()

        all_playlist_ids = set()
        for device_id, playlist_id in playlist_assignment_rows:
            if device_id not in device_playlist_map:
                device_playlist_map[device_id] = []
            device_playlist_map[device_id].append(playlist_id)
            all_playlist_ids.add(playlist_id)

        # Also include legacy assigned_playlist_id
        for device in devices:
            if device.assigned_playlist_id:
                all_playlist_ids.add(device.assigned_playlist_id)

        # Batch fetch playlist content IDs
        playlist_content_ids_map = {}
        if all_playlist_ids:
            playlist_rows = self.db.query(
                PlaylistContentModel.playlist_id,
                PlaylistContentModel.content_id
            ).filter(
                PlaylistContentModel.playlist_id.in_(all_playlist_ids)
            ).all()
            for playlist_id, content_id in playlist_rows:
                if playlist_id not in playlist_content_ids_map:
                    playlist_content_ids_map[playlist_id] = []
                playlist_content_ids_map[playlist_id].append(content_id)

        result = []
        for device in devices:
            # Get metrics from batch result
            metrics = health_metrics_map.get(device.id)
            cpu_usage = float(metrics.cpu_usage) if metrics and metrics.cpu_usage else None
            memory_usage = float(metrics.memory_usage) if metrics and metrics.memory_usage else None
            storage_usage = float(metrics.disk_usage) if metrics and metrics.disk_usage else None

            # Determine status using batch metrics
            status = self._get_device_status_from_metrics(device, metrics, five_minutes_ago)

            # Get location
            location = device.room_number or device.location_type or None

            # Collect all content IDs from all sources (for deduplication tracking)
            all_content_ids = []

            # 1. Direct assignments (content assigned directly to device)
            direct_ids = direct_content_ids_map.get(device.id, [])
            all_content_ids.extend(direct_ids)

            # 2. Tag-based assignments (content assigned to tags that device has)
            device_tag_ids = device_tags_map.get(device.id, [])
            for tag_id in device_tag_ids:
                tag_ids = tag_content_ids_map.get(tag_id, [])
                all_content_ids.extend(tag_ids)

            # 3. Playlist content (from playlist_assignments + legacy assigned_playlist_id)
            device_playlists = device_playlist_map.get(device.id, [])
            for playlist_id in device_playlists:
                playlist_ids = playlist_content_ids_map.get(playlist_id, [])
                all_content_ids.extend(playlist_ids)
            # Check legacy assigned_playlist_id (if not already counted)
            if device.assigned_playlist_id and device.assigned_playlist_id not in device_playlists:
                playlist_ids = playlist_content_ids_map.get(device.assigned_playlist_id, [])
                all_content_ids.extend(playlist_ids)

            # Calculate total and unique counts
            total_content = len(all_content_ids)
            unique_content = len(set(all_content_ids))
            duplicate_count = total_content - unique_content

            # Format content count string with duplicate info
            if total_content == 0:
                current_content = None
            elif duplicate_count > 0:
                current_content = f"{unique_content} content ({duplicate_count} duplicate)"
            else:
                current_content = f"{total_content} content"

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

    def get_content_performance(self, organization_id: Optional[int], limit: int) -> List[ContentPerformance]:
        """Get content performance metrics"""
        # Get contents with basic stats
        query = self.db.query(ContentModel).filter(ContentModel.deleted_at == None)
        if organization_id is not None:
            query = query.filter(ContentModel.organization_id == organization_id)
        contents = query.order_by(ContentModel.created_at.desc()).limit(limit).all()

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

    def get_active_playlists(self, organization_id: Optional[int]) -> List[ActivePlaylistAssignment]:
        """Get active playlist assignments"""
        query = self.db.query(PlaylistModel).filter(
            PlaylistModel.is_active == True,
            PlaylistModel.deleted_at == None
        )
        if organization_id is not None:
            query = query.filter(PlaylistModel.organization_id == organization_id)
        playlists = query.all()

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

    def get_playback_timeline(self, organization_id: Optional[int], days: int) -> List[PlaybackTimeline]:
        """Get playback timeline for the last N days (REAL DATA from content_playback_logs)"""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        # Query aggregated playback data grouped by date
        query = self.db.query(
            cast(ContentPlaybackLog.started_at, Date).label('play_date'),
            func.count(ContentPlaybackLog.id).label('playback_count'),
            func.count(func.distinct(ContentPlaybackLog.device_id)).label('unique_devices'),
            func.coalesce(func.sum(ContentPlaybackLog.duration_seconds), 0).label('total_duration')
        ).filter(
            ContentPlaybackLog.started_at >= start_date
        )
        if organization_id is not None:
            query = query.filter(ContentPlaybackLog.organization_id == organization_id)
        playback_data = query.group_by(
            cast(ContentPlaybackLog.started_at, Date)
        ).all()

        # Create a map for quick lookup
        data_map = {
            str(row.play_date): {
                'playback_count': row.playback_count,
                'unique_devices': row.unique_devices,
                'total_duration': int(row.total_duration or 0)
            }
            for row in playback_data
        }

        # Build result for each day
        result = []
        for i in range(days - 1, -1, -1):
            date = now - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            day_data = data_map.get(date_str, {})

            result.append(PlaybackTimeline(
                date=date_str,
                playback_count=day_data.get('playback_count', 0),
                unique_devices=day_data.get('unique_devices', 0),
                total_duration_seconds=day_data.get('total_duration', 0)
            ))

        return result

    # ========================================================================
    # Recent Activity
    # ========================================================================

    def get_recent_activity(self, organization_id: Optional[int], limit: int) -> List[RecentActivity]:
        """Get recent activity from audit logs"""
        query = self.db.query(AuditLogModel)
        if organization_id is not None:
            query = query.filter(AuditLogModel.organization_id == organization_id)
        logs = query.order_by(AuditLogModel.created_at.desc()).limit(limit).all()

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

    def get_system_alerts(self, organization_id: Optional[int], max_alerts: int = 50) -> List[SystemAlert]:
        """Get system alerts"""
        now = datetime.now(timezone.utc)
        five_minutes_ago = now - timedelta(minutes=5)

        alerts = []

        # Check for offline devices
        offline_query = self.db.query(DeviceModel).filter(
            or_(
                DeviceModel.last_seen_at == None,
                DeviceModel.last_seen_at < five_minutes_ago
            )
        )
        if organization_id is not None:
            offline_query = offline_query.filter(DeviceModel.organization_id == organization_id)
        offline_devices = offline_query.all()

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
        online_query = self.db.query(DeviceModel).filter(
            DeviceModel.last_seen_at >= five_minutes_ago
        )
        if organization_id is not None:
            online_query = online_query.filter(DeviceModel.organization_id == organization_id)
        online_devices = online_query.all()

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

    def get_system_info(self, organization_id: Optional[int], storage_path: str) -> SystemInfo:
        """Get system information"""
        import os
        import time

        # Content storage by type
        content_query = self.db.query(
            ContentModel.content_type,
            func.count(ContentModel.id).label('count'),
            func.coalesce(func.sum(ContentModel.file_size), 0).label('size')
        ).filter(ContentModel.deleted_at == None)
        if organization_id is not None:
            content_query = content_query.filter(ContentModel.organization_id == organization_id)
        content_stats = content_query.group_by(ContentModel.content_type).all()

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

    # ========================================================================
    # Menu Statistics (NEW)
    # ========================================================================

    def get_menu_stats(self, organization_id: Optional[int]) -> MenuStats:
        """Get menu statistics for dashboard"""
        # Total menus count
        menus_query = self.db.query(func.count(MenuModel.id)).filter(MenuModel.deleted_at == None)
        if organization_id is not None:
            menus_query = menus_query.filter(MenuModel.organization_id == organization_id)
        total_menus = menus_query.scalar() or 0

        # Active menus count
        active_query = self.db.query(func.count(MenuModel.id)).filter(
            MenuModel.is_active == True,
            MenuModel.deleted_at == None
        )
        if organization_id is not None:
            active_query = active_query.filter(MenuModel.organization_id == organization_id)
        active_menus = active_query.scalar() or 0

        # Total menu items count
        items_query = self.db.query(func.count(MenuItemModel.id)).filter(MenuItemModel.deleted_at == None)
        if organization_id is not None:
            items_query = items_query.filter(MenuItemModel.organization_id == organization_id)
        total_items = items_query.scalar() or 0

        # Total views (all time)
        views_query = self.db.query(func.count(MenuViewModel.id))
        if organization_id is not None:
            views_query = views_query.filter(MenuViewModel.organization_id == organization_id)
        total_views = views_query.scalar() or 0

        # Total contact clicks
        clicks_query = self.db.query(func.count(MenuViewModel.id)).filter(MenuViewModel.contact_clicked == True)
        if organization_id is not None:
            clicks_query = clicks_query.filter(MenuViewModel.organization_id == organization_id)
        total_contact_clicks = clicks_query.scalar() or 0

        # Views by device type
        device_query = self.db.query(
            MenuViewModel.device_type,
            func.count(MenuViewModel.id)
        )
        if organization_id is not None:
            device_query = device_query.filter(MenuViewModel.organization_id == organization_id)
        device_type_counts = device_query.group_by(MenuViewModel.device_type).all()

        views_by_device = MenuViewsByDevice()
        for device_type, count in device_type_counts:
            if device_type == 'mobile':
                views_by_device.mobile = count
            elif device_type == 'tablet':
                views_by_device.tablet = count
            elif device_type == 'desktop':
                views_by_device.desktop = count
            else:
                views_by_device.unknown += count

        # Top 5 menus by views
        top_query = self.db.query(
            MenuModel.id,
            MenuModel.name,
            MenuModel.menu_type,
            func.count(MenuViewModel.id).label('view_count'),
            func.sum(func.cast(MenuViewModel.contact_clicked, Integer)).label('click_count')
        ).outerjoin(
            MenuViewModel, MenuModel.id == MenuViewModel.menu_id
        ).filter(MenuModel.deleted_at == None)
        if organization_id is not None:
            top_query = top_query.filter(MenuModel.organization_id == organization_id)
        top_menus_query = top_query.group_by(
            MenuModel.id, MenuModel.name, MenuModel.menu_type
        ).order_by(
            func.count(MenuViewModel.id).desc()
        ).limit(5).all()

        top_menus = [
            TopMenu(
                menu_id=menu.id,
                menu_name=menu.name,
                menu_type=menu.menu_type,
                views=menu.view_count or 0,
                contact_clicks=int(menu.click_count or 0)
            )
            for menu in top_menus_query
        ]

        return MenuStats(
            total_menus=total_menus,
            active_menus=active_menus,
            total_items=total_items,
            total_views=total_views,
            total_contact_clicks=total_contact_clicks,
            views_by_device=views_by_device,
            top_menus=top_menus
        )

    # ========================================================================
    # Schedule Overview (NEW)
    # ========================================================================

    def get_schedule_overview(self, organization_id: Optional[int]) -> ScheduleOverview:
        """Get schedule overview for dashboard"""
        from datetime import date, time as dt_time

        now = datetime.now(timezone.utc)
        today = now.date()
        current_time = now.time()
        seven_days_later = today + timedelta(days=7)

        # Helper function to add org filter
        def add_org_filter(query):
            if organization_id is not None:
                return query.filter(Schedule.organization_id == organization_id)
            return query

        # Total schedules count
        total_query = self.db.query(func.count(Schedule.id)).filter(Schedule.deleted_at == None)
        total_schedules = add_org_filter(total_query).scalar() or 0

        # Active schedules count
        active_query = self.db.query(func.count(Schedule.id)).filter(
            Schedule.is_active == True,
            Schedule.deleted_at == None
        )
        active_schedules = add_org_filter(active_query).scalar() or 0

        # Schedules running now (current time within schedule time range and date range)
        running_query = self.db.query(Schedule).filter(
            Schedule.is_active == True,
            Schedule.deleted_at == None,
            Schedule.start_date <= today,
            or_(Schedule.end_date == None, Schedule.end_date >= today)
        )
        running_now_schedules = add_org_filter(running_query).all()

        running_now = 0
        for schedule in running_now_schedules:
            # Check if current time is within the time range
            if schedule.start_time and schedule.end_time:
                if schedule.start_time <= current_time <= schedule.end_time:
                    running_now += 1
            elif schedule.start_time:
                if current_time >= schedule.start_time:
                    running_now += 1
            else:
                # No time restriction, counts as running
                running_now += 1

        # Schedules ending soon (within 7 days)
        ending_query = self.db.query(func.count(Schedule.id)).filter(
            Schedule.is_active == True,
            Schedule.deleted_at == None,
            Schedule.end_date != None,
            Schedule.end_date >= today,
            Schedule.end_date <= seven_days_later
        )
        ending_soon = add_org_filter(ending_query).scalar() or 0

        # Active schedules today
        today_query = self.db.query(Schedule).filter(
            Schedule.is_active == True,
            Schedule.deleted_at == None,
            Schedule.start_date <= today,
            or_(Schedule.end_date == None, Schedule.end_date >= today)
        ).order_by(Schedule.priority.desc()).limit(10)
        active_today_query = add_org_filter(today_query).all()

        active_today = []
        for schedule in active_today_query:
            # Get playlist name
            playlist_name = None
            if schedule.playlist_id:
                playlist = self.db.query(PlaylistModel.name).filter(
                    PlaylistModel.id == schedule.playlist_id
                ).first()
                if playlist:
                    playlist_name = playlist[0]

            active_today.append(ActiveSchedule(
                schedule_id=schedule.id,
                name=schedule.name,
                playlist_name=playlist_name,
                priority=schedule.priority,
                start_time=str(schedule.start_time) if schedule.start_time else None,
                end_time=str(schedule.end_time) if schedule.end_time else None
            ))

        return ScheduleOverview(
            total_schedules=total_schedules,
            active_schedules=active_schedules,
            running_now=running_now,
            ending_soon=ending_soon,
            active_today=active_today
        )
