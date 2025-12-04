"""
Playback Log Domain Entity
Business logic for analytics and playback tracking
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class PlaybackLog:
    """Playback log domain entity - Pure business logic"""

    # REQUIRED FIELDS
    content_id: int
    device_id: int
    organization_id: int
    started_at: datetime

    # OPTIONAL FIELDS WITH DEFAULTS
    id: Optional[int] = None
    playlist_id: Optional[int] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    expected_duration: Optional[int] = None
    completed: bool = False

    # Metadata
    device_info: Optional[Dict[str, Any]] = None
    playback_quality: Optional[str] = None  # SD, HD, FHD, 4K
    error_count: int = 0
    error_details: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: Optional[datetime] = None

    def is_completed(self) -> bool:
        """Check if playback was completed successfully"""
        return self.completed and self.ended_at is not None

    def get_actual_duration(self) -> Optional[int]:
        """Get actual playback duration in seconds"""
        if self.ended_at and self.started_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return self.duration_seconds

    def calculate_completion_rate(self) -> float:
        """Calculate completion rate percentage"""
        if not self.expected_duration or self.expected_duration == 0:
            return 0.0

        actual_duration = self.get_actual_duration()
        if not actual_duration:
            return 0.0

        rate = (actual_duration / self.expected_duration) * 100
        return min(rate, 100.0)  # Cap at 100%

    def has_errors(self) -> bool:
        """Check if playback had errors"""
        return self.error_count > 0

    def mark_as_completed(self, ended_at: datetime, duration_seconds: int):
        """Mark playback as completed"""
        self.ended_at = ended_at
        self.duration_seconds = duration_seconds
        self.completed = True

    def add_error(self, error_details: Dict[str, Any]):
        """Add error to playback log"""
        self.error_count += 1
        if self.error_details is None:
            self.error_details = {"errors": []}
        if "errors" not in self.error_details:
            self.error_details["errors"] = []
        self.error_details["errors"].append(error_details)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "log_id": self.id,  # Alias for player compatibility
            "content_id": self.content_id,
            "device_id": self.device_id,
            "playlist_id": self.playlist_id,
            "organization_id": self.organization_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "expected_duration": self.expected_duration,
            "completed": self.completed,
            "device_info": self.device_info,
            "playback_quality": self.playback_quality,
            "error_count": self.error_count,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class ContentPerformance:
    """Content performance metrics - Domain entity"""

    content_id: int
    title: str
    content_type: str
    total_plays: int
    completed_plays: int
    unique_devices: int
    avg_duration_seconds: Optional[float] = None
    last_played_at: Optional[datetime] = None
    completion_rate: Optional[float] = None

    def get_engagement_score(self) -> float:
        """Calculate engagement score (0-100)"""
        if self.total_plays == 0:
            return 0.0

        # Weighted score: completion rate (60%) + replay factor (40%)
        completion_weight = (self.completion_rate or 0) * 0.6
        replay_factor = min((self.total_plays / max(self.unique_devices, 1)) * 10, 40)

        return completion_weight + replay_factor


@dataclass
class DeviceEngagement:
    """Device engagement metrics - Domain entity"""

    device_id: int
    device_name: str
    total_plays: int
    unique_content: int
    total_watch_time_seconds: int
    last_playback_at: Optional[datetime] = None

    def get_watch_time_hours(self) -> float:
        """Get watch time in hours"""
        return round(self.total_watch_time_seconds / 3600, 2)

    def get_average_plays_per_content(self) -> float:
        """Calculate average plays per unique content"""
        if self.unique_content == 0:
            return 0.0
        return round(self.total_plays / self.unique_content, 2)

    def is_active(self, threshold_minutes: int = 30) -> bool:
        """Check if device is recently active"""
        if not self.last_playback_at:
            return False

        now = datetime.now(timezone.utc)
        time_diff = (now - self.last_playback_at).total_seconds() / 60
        return time_diff <= threshold_minutes
