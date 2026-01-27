"""
ATLAS_SEMAR Backend - Jarvis Module DTOs
Follows PANDAWA Clean Architecture standards (CORE-STD-02)
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Request DTOs
class VoiceCommandRequest(BaseModel):
    """Voice command request DTO"""

    audio_data: str = Field(..., description="Base64 encoded audio data")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")


class STTRequest(BaseModel):
    """Speech-to-text request DTO"""

    audio_data: str = Field(..., description="Base64 encoded audio data")


# Response DTOs
class VoiceCommandResponse(BaseModel):
    """Voice command response DTO"""

    session_id: str
    transcript: str
    command: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class STTResponse(BaseModel):
    """Speech-to-text response DTO"""

    transcript: str
    confidence: float

    class Config:
        from_attributes = True
