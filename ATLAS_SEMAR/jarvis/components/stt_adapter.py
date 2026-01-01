"""
STTAdapter - Synchronous blocking Speech-to-Text

Architecture: JARVIS-DEC-001 (synchronous blocking)
Library: Whisper (local, no external API)

No async/await. No caching. No retries.
Deterministic: same audio input → same transcription output.
Blocks until transcription complete or timeout.
"""

import time
from typing import Optional
import numpy as np

try:
    import whisper
except ImportError:
    whisper = None


class STTTimeoutError(Exception):
    """STT exceeded timeout (user-facing message)."""
    pass


class STTConfidenceError(Exception):
    """STT confidence below threshold (user-facing message)."""
    pass


class STTError(Exception):
    """General STT error (user-facing message)."""
    pass


class STTAdapter:
    """
    Synchronous blocking Speech-to-Text via Whisper.

    BLOCKS until transcription complete or timeout.
    Returns text string or raises exception.

    Pattern:
        adapter = STTAdapter(model="base", timeout_ms=1000)
        text = adapter.transcribe(audio_buffer)
        # Returns: "hello world"
        # Or raises: STTTimeoutError, STTConfidenceError, STTError
    """

    def __init__(
        self,
        model: str = "base",
        timeout_ms: int = 1000,
        min_confidence: float = 0.5,
        language: str = "en",
    ):
        """
        Args:
            model: Whisper model size ("tiny", "base", "small")
            timeout_ms: Maximum transcription time in milliseconds (1000 = 1s)
            min_confidence: Minimum confidence threshold (0.0-1.0)
            language: Language code (default "en" = English)
        """
        self.model_name = model
        self.timeout_ms = timeout_ms
        self.min_confidence = min_confidence
        self.language = language

        self._model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model."""
        if whisper is None:
            raise ImportError(
                "Whisper not installed. "
                "Install with: pip install openai-whisper"
            )

        try:
            self._model = whisper.load_model(self.model_name)
        except Exception as e:
            raise STTError(
                f"Failed to load Whisper model '{self.model_name}': {str(e)}"
            )

    def transcribe(self, audio_buffer: "AudioBuffer") -> str:
        """
        Transcribe audio to text (blocking, synchronous).

        BLOCKS until transcription complete or timeout.

        Args:
            audio_buffer: AudioBuffer with PCM samples

        Returns:
            str: Transcribed text

        Raises:
            STTTimeoutError: If transcription exceeds timeout
            STTConfidenceError: If confidence below threshold
            STTError: If transcription fails
        """
        if self._model is None:
            raise STTError("STT model not loaded")

        print(f"[STT] Audio: {audio_buffer.duration_ms}ms, Language: {self.language}", flush=True)

        # Warn if audio is too short
        if audio_buffer.duration_ms < 500:
            print(f"[STT] ⚠️  Audio very short ({audio_buffer.duration_ms}ms). Whisper needs min 500ms.", flush=True)

        start_time = time.time()

        try:
            print(f"[STT] Starting Whisper transcription...", flush=True)

            # Convert int16 → float32 for Whisper
            audio_samples = audio_buffer.samples
            print(f"[STT] Audio shape: {audio_samples.shape}, dtype: {audio_samples.dtype}", flush=True)

            if audio_samples.dtype != np.float32:
                print(f"[STT] Converting {audio_samples.dtype} → float32...", flush=True)
                # Ensure 1D array
                if audio_samples.ndim > 1:
                    audio_samples = audio_samples.flatten()
                # Convert int16 to float32 with normalization
                audio_samples = audio_samples.astype(np.float32) / 32768.0  # Normalize int16 to [-1.0, 1.0]
                print(f"[STT] Conversion done. Shape: {audio_samples.shape}", flush=True)

            result = self._model.transcribe(
                audio_samples,
                language=self.language,
                fp16=False,
                verbose=False,
            )

            elapsed_ms = (time.time() - start_time) * 1000
            print(f"[STT] Transcription complete ({elapsed_ms:.0f}ms)", flush=True)

            if elapsed_ms > self.timeout_ms:
                raise STTTimeoutError(
                    f"Transcription exceeded {self.timeout_ms}ms timeout "
                    f"(took {elapsed_ms:.0f}ms)"
                )

            text = result.get("text", "").strip()
            confidence = self._extract_confidence(result)

            print(f"[STT] Raw result: {result}", flush=True)
            print(f"[STT] Text: '{text}' (confidence: {confidence:.1%})", flush=True)

            if not text:
                print(f"[STT] ⚠️  No speech detected. Confidence: {confidence:.1%}", flush=True)
                raise STTError(f"No speech detected (confidence: {confidence:.1%}). Try speaking louder or clearer.")

            if confidence < self.min_confidence:
                raise STTConfidenceError(
                    f"Confidence {confidence:.1%} below threshold {self.min_confidence:.1%}. "
                    f"Please try again or type manually."
                )

            return text

        except (STTTimeoutError, STTConfidenceError):
            raise
        except Exception as e:
            print(f"[STT] ERROR: {str(e)}", flush=True)
            raise STTError(f"Transcription failed: {str(e)}")

    def _extract_confidence(self, result: dict) -> float:
        """
        Extract confidence score from Whisper result.

        Whisper returns probability per segment.
        Use average of segment confidences.

        Args:
            result: Whisper transcribe() result dict

        Returns:
            float: Confidence between 0.0 and 1.0
        """
        segments = result.get("segments", [])

        if not segments:
            return 0.0

        confidences = []
        for segment in segments:
            no_speech_prob = segment.get("no_speech_prob", 0.0)
            confidence = 1.0 - no_speech_prob
            confidences.append(confidence)

        if not confidences:
            return 0.0

        avg_confidence = sum(confidences) / len(confidences)
        return avg_confidence
