"""
Playlist Manager Service
Playlist generation and management with play_order and shuffle support

This service implements:
1. Playlist generation from assignments
2. Play order sequencing
3. Shuffle mode support
4. Playlist change detection
5. Integration with deadline scheduler

MIGRATED TO QUICK WINS STANDARDS:
- Structured logging with StructuredLogger
- Custom exceptions (NotFoundException, BadRequestException)
- Type hints throughout
- Async patterns
- Production-ready error handling
"""

import hashlib
import json
from random import shuffle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.core.logging import StructuredLogger
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.playlist import Playlist, PlaylistContent, PlaylistAssignment
from app.models.content import Content
from app.models.device import Device
from app.models.tag import DeviceTag
from app.repositories.device_repository import DeviceRepository
from app.repositories.content_repository import ContentRepository

logger = StructuredLogger(__name__)


class PlaylistManager:
    """
    Playlist manager for content organization and playback

    Manages playlist generation with support for:
    - Multiple playlist assignments
    - Priority-based ordering
    - Shuffle mode
    - Play order sequencing
    - Change detection

    Attributes:
        db: Database session
        device_repo: Device repository for device queries
        content_repo: Content repository for content queries
        device_id: Device ID for playlist generation
        shuffle_enabled: Whether to shuffle playlist
        request_id: Request ID for logging
    """

    def __init__(
        self,
        db: Session,
        device_id: Optional[int] = None,
        shuffle_enabled: bool = False,
        request_id: Optional[str] = None
    ):
        """Initialize playlist manager"""
        self.db = db
        self.device_repo = DeviceRepository(db)
        self.content_repo = ContentRepository(db)
        self.device_id = device_id
        self.shuffle_enabled = shuffle_enabled
        self.request_id = request_id or "playlist_manager"

        logger.info(
            "Initializing PlaylistManager",
            request_id=self.request_id,
            device_id=device_id,
            shuffle_enabled=shuffle_enabled
        )

    def get_device_playlists(
        self,
        device_id: Optional[int] = None
    ) -> List[Playlist]:
        """
        Get all playlists assigned to a device

        Includes both direct device assignments and tag-based assignments.

        Args:
            device_id: Device ID (uses self.device_id if not provided)

        Returns:
            List of Playlist objects sorted by priority (descending)
        """
        device_id = device_id or self.device_id
        if not device_id:
            raise BadRequestException(
                message="Device ID is required",
                details={"error": "No device_id provided"}
            )

        logger.info(
            "Getting device playlists",
            request_id=self.request_id,
            device_id=device_id
        )

        # Get device using repository
        device = self.device_repo.get(device_id)
        if not device:
            raise NotFoundException(
                message=f"Device with ID {device_id} not found",
                resource_type="Device",
                resource_id=device_id
            )

        # Get playlist IDs from direct assignments
        direct_playlist_ids = self.db.query(PlaylistAssignment.playlist_id).filter(
            PlaylistAssignment.device_id == device_id
        ).distinct().all()
        direct_playlist_ids = [pid[0] for pid in direct_playlist_ids]

        # Get device tags
        device_tags = self.db.query(DeviceTag.tag_id).filter(
            DeviceTag.device_id == device_id
        ).distinct().all()
        device_tag_ids = [tag_id[0] for tag_id in device_tags]

        # Get playlist IDs from tag assignments
        tag_playlist_ids = []
        if device_tag_ids:
            tag_playlist_ids = self.db.query(PlaylistAssignment.playlist_id).filter(
                PlaylistAssignment.tag_id.in_(device_tag_ids)
            ).distinct().all()
            tag_playlist_ids = [pid[0] for pid in tag_playlist_ids]

        # Combine all playlist IDs
        all_playlist_ids = list(set(direct_playlist_ids + tag_playlist_ids))

        if not all_playlist_ids:
            logger.info(
                "No playlists assigned to device",
                request_id=self.request_id,
                device_id=device_id
            )
            return []

        # Get playlists sorted by priority (highest first)
        playlists = self.db.query(Playlist).filter(
            Playlist.id.in_(all_playlist_ids),
            Playlist.is_active == True
        ).order_by(Playlist.priority.desc()).all()

        logger.info(
            "Device playlists retrieved",
            request_id=self.request_id,
            device_id=device_id,
            total_playlists=len(playlists),
            direct_assignments=len(direct_playlist_ids),
            tag_assignments=len(tag_playlist_ids)
        )

        return playlists

    def generate_playlist(
        self,
        device_id: Optional[int] = None,
        apply_shuffle: bool = None
    ) -> List[Dict[str, Any]]:
        """
        Generate ordered playlist for a device

        Combines content from all assigned playlists:
        1. Get all assigned playlists (sorted by priority)
        2. Get content from each playlist (ordered by order_index)
        3. Combine and optionally shuffle
        4. Return ordered list of content items

        Args:
            device_id: Device ID (uses self.device_id if not provided)
            apply_shuffle: Override shuffle setting (uses self.shuffle_enabled if None)

        Returns:
            List of content item dictionaries with metadata
        """
        device_id = device_id or self.device_id
        if not device_id:
            raise BadRequestException(
                message="Device ID is required",
                details={"error": "No device_id provided"}
            )

        apply_shuffle = self.shuffle_enabled if apply_shuffle is None else apply_shuffle

        logger.info(
            "Generating playlist for device",
            request_id=self.request_id,
            device_id=device_id,
            apply_shuffle=apply_shuffle
        )

        # Get assigned playlists
        playlists = self.get_device_playlists(device_id)

        if not playlists:
            logger.info(
                "No playlists found for device",
                request_id=self.request_id,
                device_id=device_id
            )
            return []

        # Collect all content items
        all_content_items = []

        for playlist in playlists:
            # Get content items for this playlist
            playlist_content_items = self.db.query(PlaylistContent).filter(
                PlaylistContent.playlist_id == playlist.id
            ).order_by(PlaylistContent.order_index).all()

            for pc_item in playlist_content_items:
                # Get content using repository
                content = self.content_repo.get(pc_item.content_id)

                if not content or not content.is_active:
                    continue

                # Build content item dict
                content_item = {
                    'content_id': content.id,
                    'title': content.title,
                    'description': content.description,
                    'content_type': content.content_type,
                    'anthias_url': content.anthias_url,
                    'anthias_asset_id': content.anthias_asset_id,
                    'duration': pc_item.duration or content.duration,
                    'order_index': pc_item.order_index,
                    'playlist_id': playlist.id,
                    'playlist_name': playlist.name,
                    'playlist_priority': playlist.priority,
                    'file_size': content.file_size,
                    'mime_type': content.mime_type,
                    'resolution': content.resolution,
                    'width': content.width,
                    'height': content.height,
                    'is_active': content.is_active
                }

                # Add video-specific fields
                if content.content_type == 'video':
                    content_item.update({
                        'video_duration': content.video_duration,
                        'video_start_time': content.video_start_time,
                        'video_end_time': content.video_end_time,
                        'codec': content.codec,
                        'fps': content.fps,
                        'bitrate': content.bitrate,
                        'audio_codec': content.audio_codec,
                        'audio_bitrate': content.audio_bitrate,
                        'audio_sample_rate': content.audio_sample_rate
                    })

                all_content_items.append(content_item)

        # Apply shuffle if enabled
        if apply_shuffle and len(all_content_items) > 1:
            logger.info(
                "Shuffling playlist",
                request_id=self.request_id,
                device_id=device_id,
                item_count=len(all_content_items)
            )
            shuffle(all_content_items)

        logger.info(
            "Playlist generated successfully",
            request_id=self.request_id,
            device_id=device_id,
            total_items=len(all_content_items),
            total_playlists=len(playlists),
            shuffled=apply_shuffle
        )

        return all_content_items

    def calculate_playlist_hash(
        self,
        playlist_items: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate hash of playlist for change detection

        Creates a hash based on content IDs and order.
        Used to detect if playlist has changed.

        Args:
            playlist_items: List of content item dictionaries

        Returns:
            SHA256 hash string
        """
        # Create stable representation of playlist
        # Use content_id and order for hash (ignore other metadata)
        playlist_signature = json.dumps(
            [
                (item['content_id'], item.get('order_index', 0))
                for item in playlist_items
            ],
            sort_keys=True
        )

        # Calculate SHA256 hash
        hash_value = hashlib.sha256(playlist_signature.encode()).hexdigest()

        logger.debug(
            "Calculated playlist hash",
            request_id=self.request_id,
            hash_value=hash_value,
            item_count=len(playlist_items)
        )

        return hash_value

    def has_playlist_changed(
        self,
        device_id: int,
        previous_hash: str
    ) -> Tuple[bool, str]:
        """
        Check if playlist has changed for a device

        Args:
            device_id: Device ID
            previous_hash: Previous playlist hash

        Returns:
            Tuple of (has_changed, current_hash)
        """
        logger.info(
            "Checking for playlist changes",
            request_id=self.request_id,
            device_id=device_id,
            previous_hash=previous_hash
        )

        # Generate current playlist
        current_playlist = self.generate_playlist(device_id, apply_shuffle=False)
        current_hash = self.calculate_playlist_hash(current_playlist)

        has_changed = current_hash != previous_hash

        logger.info(
            "Playlist change detection complete",
            request_id=self.request_id,
            device_id=device_id,
            has_changed=has_changed,
            current_hash=current_hash,
            previous_hash=previous_hash
        )

        return has_changed, current_hash

    def get_playlist_metadata(
        self,
        device_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get metadata about device's playlist

        Returns summary information:
        - Total playlists
        - Total content items
        - Total duration
        - Playlist hash

        Args:
            device_id: Device ID (uses self.device_id if not provided)

        Returns:
            Dictionary with playlist metadata
        """
        device_id = device_id or self.device_id
        if not device_id:
            raise BadRequestException(
                message="Device ID is required",
                details={"error": "No device_id provided"}
            )

        logger.info(
            "Getting playlist metadata",
            request_id=self.request_id,
            device_id=device_id
        )

        # Get playlists
        playlists = self.get_device_playlists(device_id)

        # Generate playlist
        playlist_items = self.generate_playlist(device_id, apply_shuffle=False)

        # Calculate totals
        total_duration = sum(item.get('duration', 0) for item in playlist_items)
        playlist_hash = self.calculate_playlist_hash(playlist_items)

        metadata = {
            'device_id': device_id,
            'total_playlists': len(playlists),
            'total_items': len(playlist_items),
            'total_duration': total_duration,
            'playlist_hash': playlist_hash,
            'shuffle_enabled': self.shuffle_enabled,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

        logger.info(
            "Playlist metadata retrieved",
            request_id=self.request_id,
            device_id=device_id,
            metadata=metadata
        )

        return metadata
