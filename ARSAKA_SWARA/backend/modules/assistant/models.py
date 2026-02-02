"""
ATLAS_SEMAR Backend - Jarvis Module Models
Follows PANDAWA Clean Architecture standards (CORE-STD-01)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from shared.database import Base


class VoiceSessionModel(Base):
    """Voice session database model"""

    __tablename__ = "voice_sessions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Data columns
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    transcript = Column(Text, nullable=True)
    command = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="pending")

    # Booleans
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
