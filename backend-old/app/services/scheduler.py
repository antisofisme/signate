"""
Deadline-Based Scheduler Service
Port of Anthias scheduling algorithm for content deadline management

This service implements the deadline-based scheduling algorithm from Anthias:
1. Map content to deadlines (end_date if active, start_date if inactive)
2. Find nearest deadline
3. Smart refresh detection (database changes, shuffle counter, deadline reached)
4. Non-disruptive updates (maintain position in playlist)

MIGRATED TO QUICK WINS STANDARDS:
- Structured logging with StructuredLogger
- Custom exceptions (NotFoundException, BadRequestException)
- Type hints throughout
- Async patterns
- Production-ready error handling
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment
from app.models.content import Content
from app.models.device import Device
from app.models.assignment import ContentAssignment
from app.models.tag import DeviceTag

logger = StructuredLogger(__name__)


class ContentScheduler:
    """
    Deadline-based content scheduler

    Manages content scheduling using deadline algorithm:
    - Active content: deadline = end_date (when it expires)
    - Inactive content: deadline = start_date (when it becomes active)
    - Nearest deadline triggers playlist refresh

    Attributes:
        db: Database session
        device_id: Device ID for which to schedule content
        shuffle_enabled: Whether to shuffle playlist
        shuffle_counter: Counter for shuffle refresh (refresh every 5 cycles)
        current_index: Current position in playlist
        last_content_hash: Hash of last playlist to detect changes
    """

    def __init__(
        self,
        db: Session,
        device_id: int,
        shuffle_enabled: bool = False,
        request_id: Optional[str] = None
    ):
        """Initialize scheduler for a specific device"""
        self.db = db
        self.device_id = device_id
        self.shuffle_enabled = shuffle_enabled
        self.shuffle_counter = 0
        self.current_index = 0
        self.last_content_hash = None
        self.request_id = request_id or "scheduler"

        logger.info(
            "Initializing ContentScheduler",
            request_id=self.request_id,
            device_id=device_id,
            shuffle_enabled=shuffle_enabled
        )

    def calculate_deadline(
        self,
        content: Content,
        assignment_start: Optional[datetime] = None,
        assignment_end: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Calculate deadline for content item

        Deadline logic:
        - If content is currently active: deadline = end_date
        - If content is not yet active: deadline = start_date
        - If no scheduling dates: deadline = None (always active)

        Args:
            content: Content object
            assignment_start: Optional start date from assignment
            assignment_end: Optional end date from assignment

        Returns:
            Deadline datetime or None
        """
        now = datetime.now(timezone.utc)

        # Use assignment dates if available, otherwise no scheduling
        start_date = assignment_start
        end_date = assignment_end

        if not start_date or not end_date:
            # No scheduling - content is always active
            return None

        # Check if content is currently active
        is_active = start_date <= now < end_date

        if is_active:
            # Content is active, deadline is when it expires
            deadline = end_date
        else:
            # Content is not yet active, deadline is when it starts
            deadline = start_date

        logger.debug(
            "Calculated deadline for content",
            request_id=self.request_id,
            content_id=content.id,
            content_title=content.title,
            is_active=is_active,
            deadline=deadline.isoformat() if deadline else None
        )

        return deadline

    def get_nearest_deadline(
        self,
        content_list: List[Dict[str, Any]]
    ) -> Optional[datetime]:
        """
        Get nearest deadline from list of content items

        Args:
            content_list: List of content dictionaries with 'deadline' key

        Returns:
            Nearest deadline datetime or None
        """
        deadlines = [
            item['deadline']
            for item in content_list
            if item.get('deadline') is not None
        ]

        if not deadlines:
            return None

        # Sort and get earliest
        nearest = min(deadlines)

        logger.debug(
            "Found nearest deadline",
            request_id=self.request_id,
            nearest_deadline=nearest.isoformat() if nearest else None,
            total_deadlines=len(deadlines)
        )

        return nearest

    def should_refresh_playlist(
        self,
        current_playlist_hash: str,
        current_deadline: Optional[datetime]
    ) -> Tuple[bool, str]:
        """
        Determine if playlist should be refreshed

        Refresh triggers:
        1. Playlist content changed (different hash)
        2. Shuffle counter >= 5 (reshuffle every 5 cycles)
        3. Deadline reached (content activation/expiration)

        Args:
            current_playlist_hash: Hash of current playlist
            current_deadline: Current deadline datetime

        Returns:
            Tuple of (should_refresh, reason)
        """
        now = datetime.now(timezone.utc)

        # Check 1: Playlist content changed
        if self.last_content_hash != current_playlist_hash:
            logger.info(
                "Playlist refresh triggered: content changed",
                request_id=self.request_id,
                device_id=self.device_id
            )
            return True, "content_changed"

        # Check 2: Shuffle counter reached threshold
        if self.shuffle_enabled and self.shuffle_counter >= 5:
            logger.info(
                "Playlist refresh triggered: shuffle threshold reached",
                request_id=self.request_id,
                device_id=self.device_id,
                shuffle_counter=self.shuffle_counter
            )
            return True, "shuffle_threshold"

        # Check 3: Deadline reached
        if current_deadline and current_deadline <= now:
            logger.info(
                "Playlist refresh triggered: deadline reached",
                request_id=self.request_id,
                device_id=self.device_id,
                deadline=current_deadline.isoformat()
            )
            return True, "deadline_reached"

        return False, "no_refresh_needed"

    def get_device_content(
        self,
        include_inactive: bool = False
    ) -> Tuple[List[Dict[str, Any]], Optional[datetime]]:
        """
        Get content for device with deadline calculation

        This method combines:
        1. Playlist assignments (from PlaylistAssignment)
        2. Direct content assignments (from ContentAssignment)
        3. Tag-based assignments

        Args:
            include_inactive: Whether to include inactive content

        Returns:
            Tuple of (content_list, nearest_deadline)
        """
        logger.info(
            "Getting device content with deadlines",
            request_id=self.request_id,
            device_id=self.device_id,
            include_inactive=include_inactive
        )

        # Get device
        device = self.db.query(Device).filter(Device.id == self.device_id).first()
        if not device:
            raise NotFoundException(
                message=f"Device with ID {self.device_id} not found",
                resource_type="Device",
                resource_id=self.device_id
            )

        content_items = []

        # 1. Get content from assigned playlists
        playlist_assignments = self.db.query(PlaylistAssignment).filter(
            PlaylistAssignment.device_id == self.device_id
        ).all()

        for assignment in playlist_assignments:
            playlist = self.db.query(Playlist).filter(
                Playlist.id == assignment.playlist_id,
                Playlist.is_active == True
            ).first()

            if not playlist:
                continue

            # Get playlist content items ordered by order_index
            playlist_content_items = self.db.query(PlaylistContent).filter(
                PlaylistContent.playlist_id == playlist.id
            ).order_by(PlaylistContent.order_index).all()

            for pc_item in playlist_content_items:
                content = self.db.query(Content).filter(
                    Content.id == pc_item.content_id
                ).first()

                if not content:
                    continue

                # Skip inactive content unless requested
                if not include_inactive and not content.is_active:
                    continue

                # Calculate deadline (playlists don't have start/end dates yet)
                deadline = self.calculate_deadline(content)

                content_items.append({
                    'content_id': content.id,
                    'title': content.title,
                    'content_type': content.content_type,
                    'anthias_url': content.anthias_url,
                    'duration': pc_item.duration or content.duration,
                    'order_index': pc_item.order_index,
                    'playlist_id': playlist.id,
                    'playlist_name': playlist.name,
                    'deadline': deadline,
                    'is_active': content.is_active,
                    'source': 'playlist'
                })

        # 2. Get direct content assignments
        # Get device tags first
        device_tags = self.db.query(DeviceTag.tag_id).filter(
            DeviceTag.device_id == self.device_id
        ).all()
        device_tag_ids = [tag_id[0] for tag_id in device_tags]

        # Get direct assignments (device-based and tag-based)
        direct_assignments = self.db.query(ContentAssignment).filter(
            ContentAssignment.is_active == True,
            or_(
                ContentAssignment.device_id == self.device_id,
                ContentAssignment.tag_id.in_(device_tag_ids) if device_tag_ids else False
            )
        ).order_by(
            ContentAssignment.priority.desc(),
            ContentAssignment.display_order
        ).all()

        for assignment in direct_assignments:
            content = self.db.query(Content).filter(
                Content.id == assignment.content_id
            ).first()

            if not content:
                continue

            # Skip inactive content unless requested
            if not include_inactive and not content.is_active:
                continue

            # Calculate deadline using assignment dates
            deadline = self.calculate_deadline(
                content,
                assignment_start=assignment.start_date,
                assignment_end=assignment.end_date
            )

            # Check if content is currently active (based on schedule)
            now = datetime.now(timezone.utc)
            is_scheduled_active = True
            if assignment.start_date and assignment.end_date:
                is_scheduled_active = assignment.start_date <= now < assignment.end_date

            content_items.append({
                'content_id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'anthias_url': content.anthias_url,
                'duration': content.duration,
                'priority': assignment.priority,
                'display_order': assignment.display_order,
                'deadline': deadline,
                'is_active': content.is_active and is_scheduled_active,
                'source': 'direct_assignment',
                'start_date': assignment.start_date.isoformat() if assignment.start_date else None,
                'end_date': assignment.end_date.isoformat() if assignment.end_date else None
            })

        # Get nearest deadline
        nearest_deadline = self.get_nearest_deadline(content_items)

        logger.info(
            "Device content retrieved successfully",
            request_id=self.request_id,
            device_id=self.device_id,
            total_content_items=len(content_items),
            nearest_deadline=nearest_deadline.isoformat() if nearest_deadline else None
        )

        return content_items, nearest_deadline

    def get_active_content(self) -> Tuple[List[Dict[str, Any]], Optional[datetime]]:
        """
        Get currently active content with nearest deadline

        This is the main method for getting content to display.
        Only returns content that is currently active.

        Returns:
            Tuple of (active_content_list, nearest_deadline)
        """
        logger.info(
            "Getting active content",
            request_id=self.request_id,
            device_id=self.device_id
        )

        # Get all content with deadlines
        all_content, _ = self.get_device_content(include_inactive=False)

        # Filter to only active content
        now = datetime.now(timezone.utc)
        active_content = [
            item for item in all_content
            if item.get('is_active', True)
        ]

        # Calculate nearest deadline
        nearest_deadline = self.get_nearest_deadline(active_content)

        logger.info(
            "Active content retrieved",
            request_id=self.request_id,
            device_id=self.device_id,
            total_active=len(active_content),
            nearest_deadline=nearest_deadline.isoformat() if nearest_deadline else None
        )

        return active_content, nearest_deadline

    def get_next_refresh_time(self) -> Optional[datetime]:
        """
        Get the next time the playlist should be refreshed

        Returns the nearest deadline, which is when the playlist
        will need to be updated (content activation or expiration).

        Returns:
            Next refresh datetime or None
        """
        logger.info(
            "Getting next refresh time",
            request_id=self.request_id,
            device_id=self.device_id
        )

        _, nearest_deadline = self.get_active_content()

        if nearest_deadline:
            logger.info(
                "Next refresh time calculated",
                request_id=self.request_id,
                device_id=self.device_id,
                next_refresh=nearest_deadline.isoformat()
            )
        else:
            logger.info(
                "No refresh time needed (no scheduled content)",
                request_id=self.request_id,
                device_id=self.device_id
            )

        return nearest_deadline
