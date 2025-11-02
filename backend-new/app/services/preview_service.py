"""
Content Preview Service
Resolves and previews content for devices based on assignments, playlists, and tags
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.device import Device
from app.models.content import Content
from app.models.assignment import ContentAssignment
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment
from app.models.tag import Tag, DeviceTag

logger = logging.getLogger(__name__)


class PreviewService:
    """
    Service for previewing content resolution for devices

    This service implements the content resolution algorithm that determines
    what content will be shown on a device based on:
    - Direct content assignments
    - Playlist assignments
    - Tag-based content assignments
    - Scheduling rules (inclusive/exclusive)
    - Priority hierarchy
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_device_preview(
        self,
        device_id: int,
        preview_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get content preview for a device at a specific time

        Args:
            device_id: Device ID
            preview_time: Time to preview (defaults to now)

        Returns:
            Dict containing:
                - device: Device info
                - content_sources: List of content from each source
                - final_playlist: Resolved playlist in play order
                - resolution_log: Debug info about resolution process
        """
        if preview_time is None:
            preview_time = datetime.now()

        logger.info(f"Generating preview for device {device_id} at {preview_time}")

        # Get device
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Get all content sources
        direct_content = await self._get_direct_assignments(device_id, preview_time)
        playlist_content = await self._get_playlist_content(device_id, preview_time)
        tag_content = await self._get_tag_content(device_id, preview_time)

        # Apply content resolution algorithm
        final_playlist = await self._resolve_content(
            direct_content=direct_content,
            playlist_content=playlist_content,
            tag_content=tag_content,
            preview_time=preview_time
        )

        return {
            "device": {
                "id": device.id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "room_number": device.room_number,
                "location_type": device.location_type,
            },
            "preview_time": preview_time.isoformat(),
            "content_sources": {
                "direct_assignments": direct_content,
                "playlists": playlist_content,
                "tags": tag_content,
            },
            "final_playlist": final_playlist,
            "resolution_summary": {
                "total_sources": len(direct_content) + len(playlist_content) + len(tag_content),
                "final_content_count": len(final_playlist),
                "has_exclusive_playlists": any(
                    p.get("schedule_mode") == "exclusive" and p.get("is_active_now")
                    for p in playlist_content
                ),
            }
        }

    async def _get_direct_assignments(
        self,
        device_id: int,
        preview_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get direct content assignments for device

        Priority: 999 (highest)
        """
        assignments = self.db.query(ContentAssignment, Content).join(
            Content, ContentAssignment.content_id == Content.id
        ).filter(
            and_(
                ContentAssignment.device_id == device_id,
                ContentAssignment.is_active == True,
                Content.is_active == True,
                or_(
                    ContentAssignment.start_date.is_(None),
                    ContentAssignment.start_date <= preview_time
                ),
                or_(
                    ContentAssignment.end_date.is_(None),
                    ContentAssignment.end_date >= preview_time
                )
            )
        ).order_by(
            ContentAssignment.display_order.asc()
        ).all()

        result = []
        for assignment, content in assignments:
            result.append({
                "source": "direct_assignment",
                "source_id": assignment.id,
                "priority": 999,  # Direct assignments have highest priority
                "display_order": assignment.display_order,
                "content": content.to_dict(),
                "assignment_info": {
                    "start_date": assignment.start_date.isoformat() if assignment.start_date else None,
                    "end_date": assignment.end_date.isoformat() if assignment.end_date else None,
                    "notes": assignment.notes,
                }
            })

        logger.info(f"Found {len(result)} direct assignments for device {device_id}")
        return result

    async def _get_playlist_content(
        self,
        device_id: int,
        preview_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get content from assigned playlists

        Priority: User-defined playlist priority
        Scheduling: Check schedule_mode (inclusive/exclusive)
        """
        # Get assigned playlists
        assignments = self.db.query(PlaylistAssignment, Playlist).join(
            Playlist, PlaylistAssignment.playlist_id == Playlist.id
        ).filter(
            and_(
                PlaylistAssignment.device_id == device_id,
                Playlist.is_active == True
            )
        ).all()

        result = []
        for assignment, playlist in assignments:
            # Check if playlist is scheduled for this time
            is_scheduled, is_exclusive = self._check_playlist_schedule(playlist, preview_time)

            if is_scheduled:
                # Get playlist content
                playlist_items = self.db.query(PlaylistContent, Content).join(
                    Content, PlaylistContent.content_id == Content.id
                ).filter(
                    and_(
                        PlaylistContent.playlist_id == playlist.id,
                        Content.is_active == True
                    )
                ).order_by(
                    PlaylistContent.order_index.asc()
                ).all()

                for item, content in playlist_items:
                    result.append({
                        "source": "playlist",
                        "source_id": playlist.id,
                        "source_name": playlist.name,
                        "priority": playlist.priority,
                        "schedule_mode": playlist.schedule_mode or "inclusive",
                        "is_active_now": True,
                        "is_exclusive": is_exclusive,
                        "display_order": item.order_index,
                        "content": content.to_dict(),
                        "playlist_info": {
                            "schedule_start": playlist.schedule_start.isoformat() if playlist.schedule_start else None,
                            "schedule_end": playlist.schedule_end.isoformat() if playlist.schedule_end else None,
                            "schedule_days": playlist.schedule_days,
                            "schedule_timezone": playlist.schedule_timezone,
                        }
                    })

        logger.info(f"Found {len(result)} playlist items for device {device_id}")
        return result

    async def _get_tag_content(
        self,
        device_id: int,
        preview_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get content from tags assigned to device

        Priority: Based on tag_priority
        """
        # Get device tags
        device_tags = self.db.query(DeviceTag, Tag).join(
            Tag, DeviceTag.tag_id == Tag.id
        ).filter(
            DeviceTag.device_id == device_id
        ).order_by(
            Tag.tag_priority.desc()  # Higher priority first
        ).all()

        if not device_tags:
            logger.info(f"No tags found for device {device_id}")
            return []

        tag_ids = [tag.id for _, tag in device_tags]

        # Get content assignments for these tags
        assignments = self.db.query(ContentAssignment, Content, Tag).join(
            Content, ContentAssignment.content_id == Content.id
        ).join(
            Tag, ContentAssignment.tag_id == Tag.id
        ).filter(
            and_(
                ContentAssignment.tag_id.in_(tag_ids),
                ContentAssignment.is_active == True,
                Content.is_active == True,
                or_(
                    ContentAssignment.start_date.is_(None),
                    ContentAssignment.start_date <= preview_time
                ),
                or_(
                    ContentAssignment.end_date.is_(None),
                    ContentAssignment.end_date >= preview_time
                )
            )
        ).order_by(
            Tag.tag_priority.desc(),  # Tag priority first
            ContentAssignment.display_order.asc()  # Then content order
        ).all()

        result = []
        for assignment, content, tag in assignments:
            result.append({
                "source": "tag",
                "source_id": tag.id,
                "source_name": tag.tag_name,
                "priority": tag.tag_priority,
                "display_order": assignment.display_order,
                "content": content.to_dict(),
                "tag_info": {
                    "tag_color": tag.color,
                    "tag_description": tag.description,
                }
            })

        logger.info(f"Found {len(result)} tag-based content for device {device_id}")
        return result

    def _check_playlist_schedule(
        self,
        playlist: Playlist,
        check_time: datetime
    ) -> tuple[bool, bool]:
        """
        Check if playlist is scheduled for the given time

        Returns:
            (is_scheduled: bool, is_exclusive: bool)
        """
        # If no schedule defined, always active
        if not playlist.schedule_start or not playlist.schedule_end:
            return True, (playlist.schedule_mode == "exclusive")

        # Check time range
        current_time = check_time.time()
        if not (playlist.schedule_start <= current_time <= playlist.schedule_end):
            return False, False

        # Check days (if specified)
        if playlist.schedule_days:
            # schedule_days format: ["mon","tue","wed"]
            current_day = check_time.strftime("%a").lower()
            days_list = playlist.schedule_days.strip('[]"').split(',')
            days_list = [d.strip().strip('"') for d in days_list]

            if current_day not in days_list:
                return False, False

        # Playlist is scheduled
        is_exclusive = (playlist.schedule_mode == "exclusive")
        return True, is_exclusive

    async def _resolve_content(
        self,
        direct_content: List[Dict[str, Any]],
        playlist_content: List[Dict[str, Any]],
        tag_content: List[Dict[str, Any]],
        preview_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Apply content resolution algorithm

        Algorithm (SEQUENTIAL PRIORITY):
        1. Check for EXCLUSIVE playlists
           - If found, return ONLY exclusive playlist content
        2. Otherwise, merge all content sources:
           - Direct assignments (priority 999)
           - Playlist content (user-defined priority)
           - Tag content (tag_priority)
        3. Sort by priority (descending), then display_order (ascending)
        4. Return final playlist
        """
        # Check for exclusive playlists
        exclusive_playlists = [
            p for p in playlist_content
            if p.get("is_exclusive") and p.get("is_active_now")
        ]

        if exclusive_playlists:
            # EXCLUSIVE MODE: Only show content from highest priority exclusive playlist
            logger.info(f"Found {len(exclusive_playlists)} exclusive playlists, using exclusive mode")

            # Sort by priority and get highest
            exclusive_playlists.sort(key=lambda x: x["priority"], reverse=True)
            highest_priority = exclusive_playlists[0]["priority"]

            # Get all content from highest priority exclusive playlists
            exclusive_content = [
                p for p in exclusive_playlists
                if p["priority"] == highest_priority
            ]

            # Sort by display_order
            exclusive_content.sort(key=lambda x: x["display_order"])

            return self._format_final_playlist(exclusive_content)

        # INCLUSIVE MODE: Merge all sources
        logger.info("Using inclusive mode, merging all content sources")

        # Combine all content
        all_content = direct_content + playlist_content + tag_content

        # Sort by priority (desc) then display_order (asc)
        all_content.sort(key=lambda x: (-x["priority"], x["display_order"]))

        return self._format_final_playlist(all_content)

    def _format_final_playlist(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format final playlist for frontend consumption
        """
        result = []
        for idx, item in enumerate(content_list):
            result.append({
                "play_order": idx + 1,
                "source": item["source"],
                "source_id": item["source_id"],
                "source_name": item.get("source_name", "Direct Assignment"),
                "priority": item["priority"],
                "content": item["content"],
            })
        return result
