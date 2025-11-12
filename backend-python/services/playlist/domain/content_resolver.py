"""
Content Resolution Engine
Determines what content should play on a device based on:
- Direct playlist assignments
- Tag-based assignments
- Schedules
- Priorities
- PMS integration (for hotel rooms)
"""

from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from datetime import datetime, time, timezone
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from services.playlist.domain.playlist import Playlist
    from services.playlist.domain.interfaces import IPlaylistRepository
    from services.content.domain.interfaces import IContentRepository
    from services.device.domain.interfaces import IDeviceRepository
    from services.tag.domain.interfaces import ITagRepository
    from services.schedule.domain.interfaces import IScheduleRepository
    from services.pms.domain.interfaces import IPMSRepository

from shared.cache import cache

logger = logging.getLogger(__name__)


@dataclass
class ContentResolution:
    """
    Result of content resolution for a device
    Contains the playlist and metadata about why it was selected
    """
    playlist_id: int
    playlist_name: str
    resolution_type: str  # 'direct', 'tag', 'schedule', 'pms', 'default'
    priority: int
    schedule_id: Optional[int] = None
    tag_id: Optional[int] = None
    pms_data: Optional[Dict] = None
    content_items: List[Dict] = None


class ContentResolver:
    """
    Content Resolution Engine
    
    Resolution Order (highest to lowest priority):
    1. Active schedules with highest priority
    2. Direct device assignments
    3. Tag-based assignments (if device has tags)
    4. PMS-based content (for hotel rooms with guests)
    5. Default playlist for organization
    """
    
    def __init__(
        self,
        playlist_repo: "IPlaylistRepository",
        device_repo: "IDeviceRepository",
        tag_repo: "ITagRepository",
        schedule_repo: "IScheduleRepository",
        content_repo: "IContentRepository",
        pms_repo: Optional["IPMSRepository"] = None
    ):
        self.playlist_repo = playlist_repo
        self.device_repo = device_repo
        self.tag_repo = tag_repo
        self.schedule_repo = schedule_repo
        self.content_repo = content_repo
        self.pms_repo = pms_repo
    
    def resolve_content_for_device(
        self, 
        device_id: int,
        current_time: Optional[datetime] = None,
        use_cache: bool = True
    ) -> Optional[ContentResolution]:
        """
        Resolve what content should play on a device
        
        Args:
            device_id: Device ID
            current_time: Current time (for testing), defaults to now
            use_cache: Whether to use cache (default True)
            
        Returns:
            ContentResolution with playlist and metadata, or None
        """
        if not current_time:
            current_time = datetime.now(timezone.utc)
            
        # Check cache first
        cache_key = f"content_resolution:{device_id}"
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached resolution for device {device_id}")
                return ContentResolution(**cached_result)
            
        # Get device info
        device = self.device_repo.find_by_id(device_id)
        if not device or not device.is_active():
            logger.warning(f"Device {device_id} not found or inactive")
            return None
            
        # 1. Check for active schedules
        schedule_resolution = self._check_schedules(device, current_time)
        if schedule_resolution:
            if use_cache:
                cache.set(cache_key, schedule_resolution.__dict__, ttl=300)
            return schedule_resolution
            
        # 2. Check direct assignments
        direct_resolution = self._check_direct_assignment(device)
        if direct_resolution:
            if use_cache:
                cache.set(cache_key, direct_resolution.__dict__, ttl=300)
            return direct_resolution
            
        # 3. Check tag-based assignments
        tag_resolution = self._check_tag_assignments(device)
        if tag_resolution:
            if use_cache:
                cache.set(cache_key, tag_resolution.__dict__, ttl=300)
            return tag_resolution
            
        # 4. Check PMS content (for hotel rooms)
        if self.pms_repo and device.room_number:
            pms_resolution = self._check_pms_content(device)
            if pms_resolution:
                if use_cache:
                    cache.set(cache_key, pms_resolution.__dict__, ttl=300)
                return pms_resolution
                
        # 5. Get default playlist
        default_resolution = self._get_default_playlist(device.organization_id)
        
        # Cache the result for 5 minutes
        if default_resolution and use_cache:
            cache.set(cache_key, default_resolution.__dict__, ttl=300)
            
        return default_resolution
    
    def _check_schedules(self, device, current_time: datetime) -> Optional[ContentResolution]:
        """
        Check for active schedules that apply to this device
        
        Schedules can target:
        - Specific devices
        - Device tags
        - All devices in organization
        """
        # Get all active schedules for the organization
        schedules = self.schedule_repo.find_active_schedules(
            organization_id=device.organization_id,
            current_time=current_time
        )
        
        if not schedules:
            return None
            
        # Filter schedules that apply to this device
        applicable_schedules = []
        
        for schedule in schedules:
            # Check if schedule is currently active (time/day)
            if not self._is_schedule_active_now(schedule, current_time):
                continue
                
            # Check if schedule targets this device
            if self._does_schedule_apply_to_device(schedule, device):
                applicable_schedules.append(schedule)
        
        if not applicable_schedules:
            return None
            
        # Get highest priority schedule
        highest_priority_schedule = max(applicable_schedules, key=lambda s: s.priority)
        
        # Get playlist
        playlist = self.playlist_repo.find_by_id(highest_priority_schedule.playlist_id)
        if not playlist or not playlist.is_active:
            return None
            
        return ContentResolution(
            playlist_id=playlist.id,
            playlist_name=playlist.name,
            resolution_type='schedule',
            priority=highest_priority_schedule.priority,
            schedule_id=highest_priority_schedule.id,
            content_items=self._get_playlist_content(playlist)
        )
    
    def _check_direct_assignment(self, device) -> Optional[ContentResolution]:
        """
        Check if device has direct playlist assignment
        """
        if not device.assigned_playlist_id:
            return None
            
        playlist = self.playlist_repo.find_by_id(device.assigned_playlist_id)
        if not playlist or not playlist.is_active:
            return None
            
        return ContentResolution(
            playlist_id=playlist.id,
            playlist_name=playlist.name,
            resolution_type='direct',
            priority=50,  # Default priority for direct assignments
            content_items=self._get_playlist_content(playlist)
        )
    
    def _check_tag_assignments(self, device) -> Optional[ContentResolution]:
        """
        Check tag-based playlist assignments
        """
        # Get device tags
        device_tags = self.tag_repo.find_by_device_id(device.id)
        if not device_tags:
            return None
            
        # Check each tag for playlist assignments
        tag_playlists = []
        for tag in device_tags:
            if tag.assigned_playlist_id:
                playlist = self.playlist_repo.find_by_id(tag.assigned_playlist_id)
                if playlist and playlist.is_active:
                    tag_playlists.append({
                        'playlist': playlist,
                        'tag': tag,
                        'priority': tag.priority or 40
                    })
        
        if not tag_playlists:
            return None
            
        # Get highest priority tag playlist
        highest = max(tag_playlists, key=lambda tp: tp['priority'])
        
        return ContentResolution(
            playlist_id=highest['playlist'].id,
            playlist_name=highest['playlist'].name,
            resolution_type='tag',
            priority=highest['priority'],
            tag_id=highest['tag'].id,
            content_items=self._get_playlist_content(highest['playlist'])
        )
    
    def _check_pms_content(self, device) -> Optional[ContentResolution]:
        """
        Check for PMS-based content (guest welcome messages, etc.)
        """
        if not self.pms_repo:
            return None
            
        # Get guest info for room
        guest_info = self.pms_repo.get_guest_by_room(device.room_number)
        if not guest_info:
            return None
            
        # Get PMS template playlist
        pms_playlist = self.playlist_repo.find_pms_template(
            organization_id=device.organization_id
        )
        if not pms_playlist:
            return None
            
        # Process template with guest data
        processed_content = self._process_pms_template(
            pms_playlist,
            guest_info
        )
        
        return ContentResolution(
            playlist_id=pms_playlist.id,
            playlist_name=pms_playlist.name,
            resolution_type='pms',
            priority=60,  # Higher priority than default
            pms_data=guest_info,
            content_items=processed_content
        )
    
    def _get_default_playlist(self, organization_id: int) -> Optional[ContentResolution]:
        """
        Get default playlist for organization
        """
        playlist = self.playlist_repo.find_default_playlist(organization_id)
        if not playlist:
            return None
            
        return ContentResolution(
            playlist_id=playlist.id,
            playlist_name=playlist.name,
            resolution_type='default',
            priority=10,  # Lowest priority
            content_items=self._get_playlist_content(playlist)
        )
    
    def _is_schedule_active_now(self, schedule, current_time: datetime) -> bool:
        """
        Check if schedule is active at current time
        """
        # Check date range
        if schedule.start_date and current_time.date() < schedule.start_date:
            return False
        if schedule.end_date and current_time.date() > schedule.end_date:
            return False
            
        # Check days of week (from recurrence pattern)
        if schedule.recurrence_pattern and schedule.recurrence_pattern.get('days_of_week'):
            current_day = current_time.strftime('%A').lower()
            if current_day not in schedule.recurrence_pattern['days_of_week']:
                return False
            
        # Check time range
        current_time_only = current_time.time()
        if schedule.start_time and current_time_only < schedule.start_time:
            return False
        if schedule.end_time and current_time_only > schedule.end_time:
            return False
            
        return True
    
    def _does_schedule_apply_to_device(self, schedule, device) -> bool:
        """
        Check if schedule targets this device
        """
        # Check direct device targeting
        if schedule.device_ids and device.id in schedule.device_ids:
            return True
            
        # Check tag-based targeting
        if schedule.tag_ids:
            device_tags = self.tag_repo.find_by_device_id(device.id)
            device_tag_ids = [tag.id for tag in device_tags]
            if any(tag_id in device_tag_ids for tag_id in schedule.tag_ids):
                return True
                
        # Check if schedule applies to all devices
        if schedule.apply_to_all and not schedule.device_ids and not schedule.tag_ids:
            return True
            
        return False
    
    def _get_playlist_content(self, playlist: "Playlist") -> List[Dict]:
        """
        Get playlist content items with full details
        """
        content_items = []
        
        for item in playlist.items:
            content = self.content_repo.find_by_id(item.content_id)
            if content and content.is_active:
                content_items.append({
                    'content_id': content.id,
                    'title': content.title,
                    'content_type': content.content_type,
                    'file_url': content.file_url,
                    'duration': item.duration or content.duration,
                    'order': item.order,
                    'transition': item.transition_type,
                    'metadata': {
                        'width': content.width,
                        'height': content.height,
                        'file_size': content.file_size
                    }
                })
        
        # Sort by order
        content_items.sort(key=lambda x: x['order'])
        return content_items
    
    def _process_pms_template(self, playlist: "Playlist", guest_info: Dict) -> List[Dict]:
        """
        Process PMS template playlist with guest data
        Replace variables like {guest_name}, {room_number}, etc.
        """
        content_items = self._get_playlist_content(playlist)
        
        # Process each content item
        for item in content_items:
            # Replace variables in title
            if '{' in item['title']:
                item['title'] = self._replace_variables(item['title'], guest_info)
                
            # For text/HTML content, replace variables in content
            if 'content_data' in item and '{' in item['content_data']:
                item['content_data'] = self._replace_variables(
                    item['content_data'], 
                    guest_info
                )
        
        return content_items
    
    def _replace_variables(self, text: str, data: Dict) -> str:
        """
        Replace template variables with actual data
        """
        replacements = {
            '{guest_name}': data.get('guest_name', 'Guest'),
            '{room_number}': data.get('room_number', ''),
            '{check_in}': data.get('check_in', ''),
            '{check_out}': data.get('check_out', ''),
            '{welcome_message}': data.get('welcome_message', 'Welcome!')
        }
        
        for var, value in replacements.items():
            text = text.replace(var, str(value))
            
        return text
