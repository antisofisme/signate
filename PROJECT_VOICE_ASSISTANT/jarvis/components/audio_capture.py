"""
AudioCapture - Synchronous blocking audio capture with VAD

Architecture: JARVIS-DEC-001 (synchronous blocking)
Library: sounddevice (ADR-002)

No async/await. No background threads. No caching.
Blocks until hotkey release or VAD timeout.
Raw PCM output only.
RMS-based silence detection (Week 1 acceptable).
"""

import threading
import numpy as np
import sounddevice


class AudioBuffer:
    """Raw PCM audio data container."""

    def __init__(self, samples: np.ndarray, sample_rate: int = 16000):
        """
        Args:
            samples: Raw PCM samples (int16 or float32)
            sample_rate: Sample rate in Hz (default 16000)
        """
        self.samples = samples
        self.sample_rate = sample_rate
        self.duration_seconds = len(samples) / sample_rate

    def __len__(self):
        return len(self.samples)


class AudioCaptureError(Exception):
    """Audio capture error (user-facing message)."""
    pass


class AudioCapture:
    """
    Synchronous blocking audio capture.

    Starts on hotkey press.
    Stops on hotkey release OR VAD timeout (1.5s silence).
    Returns raw PCM AudioBuffer.

    Pattern:
        capture = AudioCapture(sample_rate=16000)
        hotkey_is_pressed = threading.Event()
        
        # In MainLoop:
        audio_buffer = capture.capture(hotkey_is_pressed)
        # Blocks until hotkey release or VAD timeout
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        vad_timeout_ms: int = 1500,
        duration_ceiling_ms: int = 120000,
        frame_size_ms: int = 10,
    ):
        """
        Args:
            sample_rate: Sample rate in Hz (16000 = standard)
            vad_timeout_ms: VAD timeout in milliseconds (1500 = 1.5s silence)
            duration_ceiling_ms: Maximum duration in milliseconds (120000 = 120s)
            frame_size_ms: Frame duration in milliseconds (10ms = ~optimal latency)
        """
        self.sample_rate = sample_rate
        self.vad_timeout_ms = vad_timeout_ms
        self.duration_ceiling_ms = duration_ceiling_ms
        self.frame_size_ms = frame_size_ms
        self.frame_size_samples = int(sample_rate * frame_size_ms / 1000)

        self.vad_silence_threshold = -40

    def capture(self, hotkey_is_pressed: threading.Event) -> AudioBuffer:
        """
        Capture audio while hotkey is pressed.

        BLOCKS until:
        - Hotkey is released, OR
        - VAD timeout (1.5s silence), OR
        - Duration ceiling (120s)

        Args:
            hotkey_is_pressed: threading.Event that is set while hotkey held

        Returns:
            AudioBuffer: Raw PCM audio data

        Raises:
            AudioCaptureError: If duration exceeds ceiling or capture fails
        """
        audio_frames = []
        vad_silence_count = 0
        total_duration_ms = 0

        try:
            while True:
                frame = sounddevice.rec(
                    frames=self.frame_size_samples,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                    blocking=True,
                )

                audio_frames.append(frame)
                total_duration_ms += self.frame_size_ms

                if not hotkey_is_pressed.is_set():
                    break

                if self._is_silent(frame):
                    vad_silence_count += 1
                    if vad_silence_count * self.frame_size_ms >= self.vad_timeout_ms:
                        break
                else:
                    vad_silence_count = 0

                if total_duration_ms >= self.duration_ceiling_ms:
                    raise AudioCaptureError(
                        f"Audio duration {total_duration_ms}ms exceeds "
                        f"ceiling {self.duration_ceiling_ms}ms"
                    )

        except Exception as e:
            if isinstance(e, AudioCaptureError):
                raise
            raise AudioCaptureError(f"Audio capture failed: {str(e)}")

        samples = np.concatenate(audio_frames)
        return AudioBuffer(samples=samples, sample_rate=self.sample_rate)

    def _is_silent(self, frame: np.ndarray) -> bool:
        """
        Detect silence using RMS energy.

        Threshold: -40dB (approximately 0.01 linear amplitude)

        Args:
            frame: Audio frame (numpy array)

        Returns:
            bool: True if frame is silent
        """
        if len(frame) == 0:
            return True

        rms = np.sqrt(np.mean(frame.astype(float) ** 2))

        if rms == 0:
            energy_db = -np.inf
        else:
            energy_db = 20 * np.log10(rms)

        return energy_db < self.vad_silence_threshold
