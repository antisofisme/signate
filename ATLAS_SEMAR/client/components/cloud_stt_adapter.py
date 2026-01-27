"""Cloud STT Adapter - Send audio to backend for transcription (ADR-004)."""

import base64
import requests
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CloudSTTError(Exception):
    """Cloud STT error."""
    pass


class CloudSTTAdapter:
    """Send audio to cloud backend for transcription using Whisper model."""

    def __init__(
        self,
        backend_url: str = "http://localhost:8001",
        timeout_ms: int = 120000,
        language: str = "id",
    ):
        """
        Args:
            backend_url: Backend API base URL
            timeout_ms: Timeout in milliseconds
            language: Language code (en, id, etc)
        """
        self.backend_url = backend_url
        self.timeout_s = timeout_ms / 1000
        self.language = language

    def transcribe(self, audio_buffer) -> str:
        """
        Send audio to backend STT endpoint.

        Args:
            audio_buffer: AudioBuffer with trimmed audio

        Returns:
            Transcribed text

        Raises:
            CloudSTTError: If transcription fails
        """
        try:
            # Convert int16 to base64
            audio_bytes = audio_buffer.samples.astype(np.int16).tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            print(f"[STT] Cloud transcription: {len(audio_bytes)} bytes → base64", flush=True)

            # Send to backend
            endpoint = f"{self.backend_url}/api/v1/stt/transcribe"
            files = {
                "audio_file": ("audio.raw", audio_bytes, "application/octet-stream"),
            }
            data = {
                "sample_rate": audio_buffer.sample_rate,
                "language": self.language,
            }

            print(f"[STT] POST {endpoint}", flush=True)
            response = requests.post(
                endpoint,
                files=files,
                data=data,
                timeout=self.timeout_s,
            )

            response.raise_for_status()

            result = response.json()

            if not result.get("success"):
                raise CloudSTTError(f"Backend error: {result.get('error', 'Unknown error')}")

            text = result.get("text", "")
            confidence = result.get("confidence", 0.0)

            print(f"[STT] Result: '{text}' (confidence: {confidence:.0%})", flush=True)

            return text

        except requests.Timeout:
            raise CloudSTTError(f"Cloud STT timeout after {self.timeout_s}s")
        except requests.RequestException as e:
            raise CloudSTTError(f"Cloud STT request failed: {str(e)}")
        except Exception as e:
            raise CloudSTTError(f"Cloud STT error: {str(e)}")
