"""DTOs for STT service (ADR-004: Hybrid Cloud STT)."""

from pydantic import BaseModel, Field
from typing import Optional


class TranscribeRequest(BaseModel):
    """Client sends trimmed audio to backend."""

    # Audio file (base64 encoded or multipart)
    audio_data: str = Field(..., description="Base64-encoded audio samples (int16 PCM)")
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    language: str = Field(default="id", description="Language code (en, id, etc)")
    format: str = Field(default="wav", description="Audio format")


class TranscribeResponse(BaseModel):
    """Backend returns transcription + metadata."""

    success: bool = Field(default=True, description="Transcription succeeded")
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Model confidence (0-1)")
    language: str = Field(..., description="Detected language")
    duration_ms: int = Field(..., description="Audio duration in ms")
    error: Optional[str] = Field(default=None, description="Error message if failed")
