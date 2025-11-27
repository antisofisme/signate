"""
Widget Domain Entity
Pure business logic for widget management
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone


class Widget:
    """Widget entity - pure Python domain object"""

    VALID_TYPES = ["clock", "weather", "news", "hotel_info", "custom"]

    def __init__(
        self,
        name: str,
        widget_type: str,
        config: Dict[str, Any],
        organization_id: int,
        id: Optional[int] = None,
        description: Optional[str] = None,
        layout: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
        created_by_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.widget_type = widget_type
        self.config = config or {}
        self.layout = layout or {}
        self.is_active = is_active
        self.organization_id = organization_id
        self.created_by_id = created_by_id
        self.created_at = created_at
        self.updated_at = updated_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Widget name cannot be empty")

        if len(self.name) > 255:
            raise ValueError("Widget name too long (max 255 characters)")

        if self.widget_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid widget type. Must be one of: {', '.join(self.VALID_TYPES)}")

        if not isinstance(self.config, dict):
            raise ValueError("Widget config must be a dictionary")

        if not self.organization_id:
            raise ValueError("Organization ID is required")

    def update_config(self, new_config: Dict[str, Any]):
        """Update widget configuration"""
        if not isinstance(new_config, dict):
            raise ValueError("Widget config must be a dictionary")

        self.config.update(new_config)
        self.updated_at = datetime.now(timezone.utc)

    def update_layout(self, new_layout: Dict[str, Any]):
        """Update widget layout settings"""
        if not isinstance(new_layout, dict):
            raise ValueError("Widget layout must be a dictionary")

        self.layout.update(new_layout)
        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        """Activate widget"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate widget"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def is_clock_widget(self) -> bool:
        """Check if this is a clock widget"""
        return self.widget_type == "clock"

    def is_weather_widget(self) -> bool:
        """Check if this is a weather widget"""
        return self.widget_type == "weather"

    def is_news_widget(self) -> bool:
        """Check if this is a news widget"""
        return self.widget_type == "news"

    def is_hotel_info_widget(self) -> bool:
        """Check if this is a hotel info widget"""
        return self.widget_type == "hotel_info"

    def is_custom_widget(self) -> bool:
        """Check if this is a custom widget"""
        return self.widget_type == "custom"

    def has_position(self) -> bool:
        """Check if widget has layout position defined"""
        return bool(self.layout and ("x" in self.layout or "position" in self.layout))

    def get_position(self) -> Optional[Dict[str, Any]]:
        """Get widget position from layout"""
        if not self.layout:
            return None

        return {
            "x": self.layout.get("x"),
            "y": self.layout.get("y"),
            "width": self.layout.get("width"),
            "height": self.layout.get("height"),
            "position": self.layout.get("position"),  # Named position like "top-right"
        }

    def __repr__(self):
        return f"<Widget(id={self.id}, name='{self.name}', type={self.widget_type}, active={self.is_active})>"


class PlaylistWidget:
    """Playlist widget assignment entity"""

    def __init__(
        self,
        playlist_id: int,
        widget_id: int,
        position: int,
        z_index: int,
        id: Optional[int] = None,
        display_duration: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.playlist_id = playlist_id
        self.widget_id = widget_id
        self.position = position
        self.display_duration = display_duration
        self.z_index = z_index
        self.created_at = created_at

        self._validate()

    def _validate(self):
        """Business rules validation"""
        if self.position < 0:
            raise ValueError("Position cannot be negative")

        if self.display_duration is not None and self.display_duration <= 0:
            raise ValueError("Display duration must be positive")

        if self.z_index < 0:
            raise ValueError("Z-index cannot be negative")

    def update_position(self, new_position: int):
        """Update widget position in playlist"""
        if new_position < 0:
            raise ValueError("Position cannot be negative")
        self.position = new_position

    def update_z_index(self, new_z_index: int):
        """Update widget z-index (layer order)"""
        if new_z_index < 0:
            raise ValueError("Z-index cannot be negative")
        self.z_index = new_z_index

    def update_display_duration(self, new_duration: Optional[int]):
        """Update display duration (None = always show)"""
        if new_duration is not None and new_duration <= 0:
            raise ValueError("Display duration must be positive")
        self.display_duration = new_duration

    def is_always_visible(self) -> bool:
        """Check if widget is always visible (no duration limit)"""
        return self.display_duration is None

    def is_timed(self) -> bool:
        """Check if widget has time-limited display"""
        return self.display_duration is not None

    def is_overlay(self) -> bool:
        """Check if widget is overlay (z-index > 0)"""
        return self.z_index > 0

    def __repr__(self):
        duration = f"{self.display_duration}s" if self.display_duration else "always"
        return f"<PlaylistWidget(id={self.id}, playlist={self.playlist_id}, widget={self.widget_id}, duration={duration})>"
