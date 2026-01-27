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
        self.duration_ms = int(self.duration_seconds * 1000)

    def __len__(self):
        return len(self.samples)


class AudioCaptureError(Exception):
    """Audio capture error (user-facing message)."""
    pass


class AudioTrimmer:
    """Trim leading/trailing silence from audio (ADR-004: Hybrid Cloud STT)."""

    @staticmethod
    def trim(audio_buffer: "AudioBuffer", silence_threshold_db: float = -40) -> "AudioBuffer":
        """
        Remove leading and trailing silence.

        Args:
            audio_buffer: Input AudioBuffer
            silence_threshold_db: Silence threshold in dB

        Returns:
            AudioBuffer: Trimmed audio
        """
        samples = audio_buffer.samples.astype(float)
        rms_frames = []

        # Calculate RMS for each frame (10ms chunks)
        frame_size = int(audio_buffer.sample_rate * 0.01)  # 10ms
        for i in range(0, len(samples), frame_size):
            frame = samples[i : i + frame_size]
            if len(frame) > 0:
                rms = np.sqrt(np.mean(frame**2))
                db = 20 * np.log10(rms) if rms > 0 else -np.inf
                rms_frames.append(db)

        # Find first and last non-silent frame
        first_sound_idx = 0
        last_sound_idx = len(rms_frames) - 1

        for i, db in enumerate(rms_frames):
            if db >= silence_threshold_db:
                first_sound_idx = i
                break

        for i in range(len(rms_frames) - 1, -1, -1):
            if rms_frames[i] >= silence_threshold_db:
                last_sound_idx = i
                break

        # Convert frame indices to sample indices
        start_sample = first_sound_idx * frame_size
        end_sample = (last_sound_idx + 1) * frame_size

        trimmed_samples = samples[start_sample:end_sample].astype(audio_buffer.samples.dtype)

        print(f"[AUDIO] Trimmed: {start_sample} → {end_sample} samples", flush=True)
        return AudioBuffer(samples=trimmed_samples, sample_rate=audio_buffer.sample_rate)


class AudioQualityGates:
    """Quality gatekeeping for audio before cloud STT (ADR-004)."""

    # Thresholds (configurable)
    MIN_RMS = 10  # Minimum RMS energy
    MAX_SILENCE_RATIO = 0.8  # Max 80% silence
    MAX_CLIPPING_AMPLITUDE = 32700  # Near int16 max

    @staticmethod
    def validate(audio_buffer: "AudioBuffer") -> tuple[bool, str]:
        """
        Validate audio quality.

        Returns:
            (is_valid, reason) - reason is None if valid, else error message
        """
        # Gate 1: Not empty
        if len(audio_buffer.samples) == 0:
            return False, "Audio is empty"

        # Gate 2: Sufficient energy (RMS)
        rms = np.sqrt(np.mean(audio_buffer.samples.astype(float) ** 2))
        if rms < AudioQualityGates.MIN_RMS:
            return False, f"Audio too quiet (RMS: {rms:.1f}, min: {AudioQualityGates.MIN_RMS})"

        # Gate 3: Not silence-dominated
        silence_ratio = AudioQualityGates._compute_silence_ratio(audio_buffer)
        if silence_ratio > AudioQualityGates.MAX_SILENCE_RATIO:
            return (
                False,
                f"Mostly silence ({silence_ratio:.0%} silence ratio)",
            )

        # Gate 4: Not clipping
        max_amplitude = np.max(np.abs(audio_buffer.samples))
        if max_amplitude > AudioQualityGates.MAX_CLIPPING_AMPLITUDE:
            return False, "Audio clipping detected (amplitude too high)"

        return True, None

    @staticmethod
    def _compute_silence_ratio(audio_buffer: "AudioBuffer", silence_threshold_db: float = -40) -> float:
        """Compute ratio of silent frames."""
        samples = audio_buffer.samples.astype(float)
        frame_size = int(audio_buffer.sample_rate * 0.01)  # 10ms frames
        silent_count = 0
        total_frames = 0

        for i in range(0, len(samples), frame_size):
            frame = samples[i : i + frame_size]
            if len(frame) > 0:
                total_frames += 1
                rms = np.sqrt(np.mean(frame**2))
                db = 20 * np.log10(rms) if rms > 0 else -np.inf
                if db < silence_threshold_db:
                    silent_count += 1

        return silent_count / total_frames if total_frames > 0 else 1.0


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
            print("[AUDIO] Starting capture with continuous stream...", flush=True)
            frame_count = 0
            first_frame_with_sound = True

            # Use continuous stream instead of frame-by-frame rec()
            with sounddevice.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                device=1,  # Logitech Webcam (device index 1)
                blocksize=self.frame_size_samples,
            ) as stream:
                print("[AUDIO] Stream started", flush=True)

                while True:
                    frame_count += 1
                    frame, overflowed = stream.read(self.frame_size_samples)

                    if overflowed:
                        print("[AUDIO] ⚠️  Buffer overflow!", flush=True)

                    audio_frames.append(frame)
                    total_duration_ms += self.frame_size_ms

                    is_hotkey_pressed = hotkey_is_pressed.is_set()

                    # Check silence
                    is_silent = self._is_silent(frame)

                    # Show RMS for debugging (3 lines only, update in place)
                    rms = np.sqrt(np.mean(frame.astype(float) ** 2))
                    energy_db = 20 * np.log10(rms) if rms > 0 else -np.inf

                    # Show raw int16 values
                    frame_min = frame.min()
                    frame_max = frame.max()

                    status = "SILENT" if is_silent else "SOUND"

                    # Update 3 status lines (overwrite previous with \r)
                    print(f"\r[AUDIO] Frame {frame_count}/... | Status: {status} | RMS:{rms:.1f}dB Hotkey:{'HELD' if is_hotkey_pressed else 'RELEASED'}", end="", flush=True)

                    if not is_hotkey_pressed:
                        print()  # New line after loop
                        print("[AUDIO] Hotkey released - exiting capture", flush=True)
                        break

                    if is_silent:
                        vad_silence_count += 1
                        if vad_silence_count * self.frame_size_ms >= self.vad_timeout_ms:
                            print("[AUDIO] VAD timeout - exiting capture", flush=True)
                            break
                    else:
                        vad_silence_count = 0
                        if first_frame_with_sound:
                            print("[AUDIO] ✅ Sound detected!", flush=True)
                            first_frame_with_sound = False

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

        # Flatten to 1D array if needed
        if samples.ndim > 1:
            print(f"[AUDIO] Flattening {samples.ndim}D array to 1D", flush=True)
            samples = samples.flatten()

        duration_ms = len(samples) / self.sample_rate * 1000
        print(f"[AUDIO] Capture complete: {len(audio_frames)} frames, {duration_ms:.0f}ms total, shape={samples.shape}", flush=True)
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
