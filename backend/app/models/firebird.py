"""
Firebird Config Model
Configuration for external Firebird API integration
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class FirebirdConfig(Base):
    """
    Firebird API configuration model

    Stores configuration for integrating with external Firebird API
    to fetch guest information and other data.

    Attributes:
        id: Primary key
        config_key: Unique configuration key
        api_endpoint: Firebird API endpoint URL
        api_key: API key for authentication (encrypted)
        refresh_interval: How often to refresh data (in seconds)
        is_active: Whether this config is active
        last_sync: Last successful sync timestamp
        config_json: Additional configuration in JSON format
        notes: Admin notes about this integration
        created_at: Timestamp when config was created
        updated_at: Timestamp when config was last updated
    """

    __tablename__ = "firebird_config"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Config Info
    config_key = Column(String(50), unique=True, nullable=False, index=True)
    api_endpoint = Column(String(500), nullable=False)
    api_key = Column(String(255), nullable=False)  # Should be encrypted

    # Settings
    refresh_interval = Column(Integer, default=300, nullable=False)  # seconds
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Sync Info
    last_sync = Column(DateTime(timezone=True))

    # Additional Config
    config_json = Column(Text)  # JSON string for additional settings
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<FirebirdConfig(id={self.id}, key='{self.config_key}', active={self.is_active})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "config_key": self.config_key,
            "api_endpoint": self.api_endpoint,
            "refresh_interval": self.refresh_interval,
            "is_active": self.is_active,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Note: api_key is NOT included for security
        }
