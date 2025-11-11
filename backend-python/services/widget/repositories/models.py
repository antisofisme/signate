"""
Widget Models
SQLAlchemy models for widget system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from shared.database import Base


class Widget(Base):
    """Widget definitions"""

    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Widget Info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    widget_type = Column(String(50), nullable=False)  # 'clock', 'weather', 'news', 'hotel_info', 'custom'

    # Configuration
    config = Column(JSONB, nullable=False)  # Widget-specific settings
    layout = Column(JSONB)  # {"position": "top-right", "width": 300, "height": 100}

    # Status
    is_active = Column(Boolean, default=True)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uq_widgets_org_name'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "description": self.description,
            "widget_type": self.widget_type,
            "config": self.config,
            "layout": self.layout,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PlaylistWidget(Base):
    """Widget assignments to playlists"""

    __tablename__ = "playlist_widgets"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    widget_id = Column(Integer, ForeignKey("widgets.id", ondelete="CASCADE"), nullable=False)

    # Display settings
    position = Column(Integer, default=0)  # Order in playlist
    display_duration = Column(Integer)  # Seconds (NULL = always show)
    z_index = Column(Integer, default=100)  # Layer order

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('playlist_id', 'widget_id', name='uq_playlist_widgets'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "playlist_id": self.playlist_id,
            "widget_id": self.widget_id,
            "position": self.position,
            "display_duration": self.display_duration,
            "z_index": self.z_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
