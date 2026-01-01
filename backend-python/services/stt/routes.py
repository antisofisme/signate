"""STT API routes (ADR-004: Hybrid Cloud STT)."""

from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
import base64
import logging

from .dtos import TranscribeRequest, TranscribeResponse
from .use_cases import TranscribeUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/stt", tags=["stt"])

# Lazy-initialize transcribe use case
_transcribe_uc: Optional[TranscribeUseCase] = None


def get_transcribe_uc() -> TranscribeUseCase:
    """Get or create transcribe use case (singleton)."""
    global _transcribe_uc
    if _transcribe_uc is None:
        _transcribe_uc = TranscribeUseCase(model_name="large")
    return _transcribe_uc


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio_file: UploadFile = File(...),
    sample_rate: int = Form(44100),
    language: str = Form("id"),
) -> TranscribeResponse:
    """
    Transcribe audio using Whisper model (large).

    Client sends:
    - audio_file: Raw PCM audio (int16)
    - sample_rate: Audio sample rate
    - language: Language code (en, id, etc)

    Server returns:
    - Transcribed text
    - Confidence score
    - Language detected
    """
    try:
        # Read audio file
        audio_bytes = await audio_file.read()

        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Get transcribe use case
        uc = get_transcribe_uc()

        # Transcribe
        result = uc.execute(
            audio_data_b64=audio_b64,
            sample_rate=sample_rate,
            language=language,
        )

        # Calculate duration
        import numpy as np
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        duration_ms = int(len(audio_int16) / sample_rate * 1000)

        if result["success"]:
            return TranscribeResponse(
                success=True,
                text=result["text"],
                confidence=result["confidence"],
                language=result["language"],
                duration_ms=duration_ms,
            )
        else:
            return TranscribeResponse(
                success=False,
                text="",
                confidence=0.0,
                language=language,
                duration_ms=duration_ms,
                error=result.get("error"),
            )

    except Exception as e:
        logger.error(f"Transcribe endpoint error: {str(e)}")
        return TranscribeResponse(
            success=False,
            text="",
            confidence=0.0,
            language=language,
            duration_ms=0,
            error=str(e),
        )
