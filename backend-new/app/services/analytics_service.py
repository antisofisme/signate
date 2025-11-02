"""
Analytics Service
=================

Business logic for analytics and metrics.
Aggregates data from existing tables (devices, content, playlists, etc.)

Clean Architecture: API → Service → Repository → Database
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.repositories.device_repository import DeviceRepository
from app.repositories.content_repository import ContentRepository
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.organization_repository import OrganizationRepository
from app.models.device import Device
from app.models.content import Content
from app.models.playlist import Playlist
from app.models.assignment import Assignment


class AnalyticsService:
    """
    Analytics Service

    Handles analytics and metrics:
    - Dashboard overview metrics
    - Content performance stats
    - Device activity stats
    - Trending content
    - Organization statistics
    """

    def __init__(self, db: Session):
        """
        Initialize AnalyticsService

        Args:
            db: Database session
        """
        self.db = db
        self.device_repo = DeviceRepository(db)
        self.content_repo = ContentRepository(db)
        self.playlist_repo = PlaylistRepository(db)
        self.org_repo = OrganizationRepository(db)

    def get_dashboard_metrics(
        self,
        organization_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get dashboard overview metrics.

        Args:
            organization_id: Filter by organization (optional)

        Returns:
            Dict with dashboard metrics
        """
        # Build base queries
        device_query = self.db.query(Device)
        content_query = self.db.query(Content)
        playlist_query = self.db.query(Playlist)

        # Apply organization filter if provided
        if organization_id:
            device_query = device_query.filter(Device.organization_id == organization_id)
            content_query = content_query.filter(Content.organization_id == organization_id)
            playlist_query = playlist_query.filter(Playlist.organization_id == organization_id)

        # Count totals
        total_devices = device_query.count()
        total_content = content_query.count()
        total_playlists = playlist_query.count()

        # Active devices (last_seen within 5 minutes)
        active_threshold = datetime.utcnow() - timedelta(minutes=5)
        active_devices = device_query.filter(
            and_(
                Device.last_seen >= active_threshold,
                Device.status == "online"
            )
        ).count()

        offline_devices = total_devices - active_devices

        # Organization count (only if not filtered by org)
        if organization_id:
            total_organizations = 1
        else:
            total_organizations = self.db.query(func.count(func.distinct(Device.organization_id))).scalar() or 0

        # Calculate storage usage (sum of file sizes)
        storage_result = content_query.with_entities(
            func.sum(Content.file_size)
        ).scalar()
        storage_used_bytes = storage_result or 0
        storage_used_mb = storage_used_bytes / (1024 * 1024)

        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "offline_devices": offline_devices,
            "total_content": total_content,
            "total_playlists": total_playlists,
            "total_organizations": total_organizations,
            "storage_used_mb": round(storage_used_mb, 2)
        }

    def get_content_stats(self, content_id: int) -> Dict[str, Any]:
        """
        Get performance statistics for a specific content.

        Args:
            content_id: Content ID

        Returns:
            Dict with content stats

        Raises:
            NotFoundException: If content not found
        """
        content = self.content_repo.get(content_id)
        if not content:
            raise NotFoundException(message=f"Content {content_id} not found")

        # Count playlists using this content
        assigned_playlists = self.db.query(func.count(func.distinct(Assignment.playlist_id))).filter(
            Assignment.content_id == content_id
        ).scalar() or 0

        # Count devices showing this content (via playlists)
        devices_showing = self.db.query(func.count(func.distinct(Device.id))).join(
            Playlist, Playlist.id == Device.current_playlist_id
        ).join(
            Assignment, Assignment.playlist_id == Playlist.id
        ).filter(
            Assignment.content_id == content_id
        ).scalar() or 0

        # File size in MB
        file_size_mb = None
        if content.file_size:
            file_size_mb = round(content.file_size / (1024 * 1024), 2)

        content_performance = {
            "content_id": content.id,
            "title": content.title,
            "content_type": content.content_type,
            "assigned_playlists": assigned_playlists,
            "devices_showing": devices_showing,
            "file_size_mb": file_size_mb,
            "created_at": content.created_at
        }

        # Usage stats (placeholder - could be enhanced with actual view data)
        usage_stats = {
            "assigned_playlists": assigned_playlists,
            "devices_showing": devices_showing,
            "estimated_daily_views": devices_showing * 24  # Rough estimate
        }

        return {
            "content": content_performance,
            "usage_stats": usage_stats
        }

    def get_device_stats(self, device_id: int) -> Dict[str, Any]:
        """
        Get activity statistics for a specific device.

        Args:
            device_id: Device ID

        Returns:
            Dict with device stats

        Raises:
            NotFoundException: If device not found
        """
        device = self.device_repo.get(device_id)
        if not device:
            raise NotFoundException(message=f"Device {device_id} not found")

        # Get current playlist name
        current_playlist = None
        if device.current_playlist_id:
            playlist = self.playlist_repo.get(device.current_playlist_id)
            if playlist:
                current_playlist = playlist.title

        # Calculate uptime (rough estimate based on last_seen)
        uptime_hours = None
        if device.last_seen:
            time_diff = datetime.utcnow() - device.last_seen
            uptime_hours = round(time_diff.total_seconds() / 3600, 2)

        device_activity = {
            "device_id": device.id,
            "device_name": device.device_name,
            "status": device.status,
            "last_seen": device.last_seen,
            "current_playlist": current_playlist,
            "uptime_hours": uptime_hours,
            "location": device.location
        }

        # Activity summary
        activity_summary = {
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "registered_at": device.created_at.isoformat() if device.created_at else None
        }

        return {
            "device": device_activity,
            "activity_summary": activity_summary
        }

    def get_trending_content(
        self,
        organization_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending content based on usage.

        Args:
            organization_id: Filter by organization (optional)
            limit: Maximum results

        Returns:
            List of trending content items
        """
        # Query content with device count
        query = self.db.query(
            Content.id,
            Content.title,
            Content.content_type,
            func.count(func.distinct(Device.id)).label('devices_count')
        ).outerjoin(
            Assignment, Assignment.content_id == Content.id
        ).outerjoin(
            Playlist, Playlist.id == Assignment.playlist_id
        ).outerjoin(
            Device, Device.current_playlist_id == Playlist.id
        )

        # Apply organization filter
        if organization_id:
            query = query.filter(Content.organization_id == organization_id)

        # Group and order
        query = query.group_by(Content.id, Content.title, Content.content_type).order_by(
            func.count(func.distinct(Device.id)).desc()
        ).limit(limit)

        results = query.all()

        trending = []
        for content_id, title, content_type, devices_count in results:
            # Simple scoring based on device count
            score = min(devices_count * 10, 100)  # Cap at 100

            trending.append({
                "content_id": content_id,
                "title": title,
                "content_type": content_type,
                "score": round(score, 1),
                "devices_count": devices_count
            })

        return trending

    def get_organization_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific organization.

        Args:
            organization_id: Organization ID

        Returns:
            Dict with organization stats

        Raises:
            NotFoundException: If organization not found
        """
        org = self.org_repo.get(organization_id)
        if not org:
            raise NotFoundException(message=f"Organization {organization_id} not found")

        # Get counts
        device_count = self.db.query(Device).filter(Device.organization_id == organization_id).count()
        content_count = self.db.query(Content).filter(Content.organization_id == organization_id).count()
        playlist_count = self.db.query(Playlist).filter(Playlist.organization_id == organization_id).count()

        # Active devices
        active_threshold = datetime.utcnow() - timedelta(minutes=5)
        active_devices = self.db.query(Device).filter(
            and_(
                Device.organization_id == organization_id,
                Device.last_seen >= active_threshold,
                Device.status == "online"
            )
        ).count()

        # Storage usage
        storage_result = self.db.query(func.sum(Content.file_size)).filter(
            Content.organization_id == organization_id
        ).scalar()
        storage_used_bytes = storage_result or 0
        storage_used_mb = storage_used_bytes / (1024 * 1024)

        # Storage limit (from organization settings)
        storage_limit_mb = None
        if hasattr(org, 'storage_quota_bytes') and org.storage_quota_bytes:
            storage_limit_mb = org.storage_quota_bytes / (1024 * 1024)

        return {
            "organization_id": organization_id,
            "device_count": device_count,
            "active_devices": active_devices,
            "content_count": content_count,
            "playlist_count": playlist_count,
            "storage_used_mb": round(storage_used_mb, 2),
            "storage_limit_mb": round(storage_limit_mb, 2) if storage_limit_mb else None
        }
