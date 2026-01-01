"""Transcribe use case (ADR-004: Hybrid Cloud STT)."""

import base64
import io
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TranscribeUseCase:
    """Process audio transcription with Whisper model."""

    def __init__(self, model_name: str = "large"):
        """
        Args:
            model_name: Whisper model (tiny, base, small, medium, large)
        """
        try:
            import whisper
            self.whisper = whisper
            self.model = None
            self.model_name = model_name
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            raise

    def _load_model(self):
        """Lazy load Whisper model on first use."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = self.whisper.load_model(self.model_name)

    def execute(
        self,
        audio_data_b64: str,
        sample_rate: int,
        language: str = "id",
    ) -> dict:
        """
        Transcribe audio.

        Args:
            audio_data_b64: Base64-encoded int16 PCM audio
            sample_rate: Sample rate in Hz
            language: Language code

        Returns:
            {
                "text": "transcription",
                "confidence": 0.95,
                "language": "id",
                "segments": [...]
            }
        """
        try:
            # Load model on first use
            self._load_model()

            # Decode audio from base64
            audio_bytes = base64.b64decode(audio_data_b64)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

            # Convert int16 to float32 (Whisper requirement)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            logger.info(
                f"Transcribing {len(audio_int16)} samples @ {sample_rate}Hz, "
                f"duration {len(audio_int16)/sample_rate:.1f}s"
            )

            # Transcribe
            result = self.model.transcribe(
                audio_float32,
                language=language,
                fp16=True,  # Use FP16 if GPU available
            )

            # Extract confidence from first segment
            confidence = 1.0
            if result.get("segments") and len(result["segments"]) > 0:
                confidence = result["segments"][0].get("confidence", 1.0)

            return {
                "success": True,
                "text": result["text"],
                "confidence": confidence,
                "language": result.get("language", language),
                "segments": result.get("segments", []),
            }

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "language": language,
                "error": str(e),
            }
