"""
MainLoop - Single synchronous orchestration loop

Architecture: JARVIS-L2-ARCH-001 (orchestration loop)
Single writer (MainLoop only) for SessionState

Pseudocode:
    while True:
        wait for hotkey press (blocking on event)
        clear hotkey event
        capture audio (blocking)
        transcribe via STT (blocking)
        classify input (deterministic)
        record result (explicit failure handling)
        loop
"""

import threading
from typing import Optional, Union

from jarvis.components.hotkey_listener import HotkeyListener
from jarvis.components.audio_capture import (
    AudioCapture,
    AudioCaptureError,
    AudioBuffer,
    AudioTrimmer,
    AudioQualityGates,
)
from jarvis.components.cloud_stt_adapter import CloudSTTAdapter, CloudSTTError
from jarvis.components.input_boundary import InputBoundary, InputSignal, CommandInput, VoiceInput, InputClassificationError
from jarvis.components.command_executor import CommandExecutor, CommandExecutionError
from jarvis.components.safety_gate import SafetyGate
from jarvis.components.prompt_shaper import PromptShaper, PromptShaperError
from jarvis.components.cli_adapter import CLIAdapter, CLIAdapterError


class SessionState:
    """
    Stateless session holder.

    JARVIS IS AMNESIC BY DESIGN.
    NO conversation memory, history, or temporal state.

    ONLY allowed state:
    - mode: affects HOW text is sent (user-specified)
    - is_active: daemon control flag

    FORBIDDEN:
    - last_audio
    - last_transcription
    - last_classification
    - last_error
    - input_count
    """

    def __init__(self):
        self.mode = "default"
        self.is_active = False

    def update_mode(self, mode: str):
        """MainLoop only. Mode affects next utterance input method."""
        self.mode = mode


class MainLoopOrchestrator:
    """
    Single synchronous control loop.

    Coordinates:
    1. HotkeyListener (detects press, signals via event)
    2. AudioCapture (blocks until hotkey release or VAD timeout)
    3. STTAdapter (synchronous blocking transcription)
    4. InputBoundary (deterministic classification)

    Owns SessionState.
    All operations are blocking and synchronous.
    No async/await. No background threads except HotkeyListener.

    Explicit failure handling for all 6 failure modes:
    1. Audio capture fails → record error, continue
    2. STT timeout → record error, continue
    3. STT low confidence → record error, continue
    4. STT fails → record error, continue
    5. Input classification fails → record error, continue
    6. Unhandled error → record error, stop
    """

    def __init__(
        self,
        hotkey_key: str = "f12",
        sample_rate: int = 16000,
        vad_timeout_ms: int = 1500,
        duration_ceiling_ms: int = 120000,
        stt_model: str = "base",
        stt_timeout_ms: int = 30000,
        stt_language: str = "en",
    ):
        """
        Args:
            hotkey_key: Hotkey to detect (default F12)
            sample_rate: Audio sample rate (16000 Hz standard)
            vad_timeout_ms: VAD silence timeout (1500 ms = 1.5s)
            duration_ceiling_ms: Max duration (120000 ms = 120s)
            stt_model: Whisper model (tiny, base, small)
            stt_timeout_ms: STT timeout (1000 ms = 1s)
        """
        self.hotkey_key = hotkey_key
        self.sample_rate = sample_rate

        self.state = SessionState()
        self.state.is_active = True

        self.hotkey_event = threading.Event()
        self.hotkey_listener = HotkeyListener(
            hotkey_key=hotkey_key,
            signal_event=self.hotkey_event,
        )

        self.audio_capture = AudioCapture(
            sample_rate=sample_rate,
            vad_timeout_ms=vad_timeout_ms,
            duration_ceiling_ms=duration_ceiling_ms,
        )

        self.stt_adapter = CloudSTTAdapter(
            backend_url="http://localhost:8001",
            timeout_ms=stt_timeout_ms,
            language=stt_language,
        )

        self.input_boundary = InputBoundary()

        self.command_executor = CommandExecutor()

        self.safety_gate = SafetyGate()

        self.prompt_shaper = PromptShaper()

        self.cli_adapter = CLIAdapter()

        self._running = False

    def run(self):
        """
        Main loop (blocking).

        Orchestration:
        1. Start HotkeyListener thread
        2. Wait for hotkey press (blocking on event)
        3. Clear event (next iteration)
        4. Capture audio (blocking)
        5. Handle result
        6. Loop
        """
        self.hotkey_listener.daemon = False
        self.hotkey_listener.start()

        self._running = True

        try:
            while self._running:
                self._iteration()
        except KeyboardInterrupt:
            self._running = False
        except Exception as e:
            print(f"[MAINLOOP ERROR] {str(e)}", flush=True)
            self._running = False
        finally:
            self.state.is_active = False

    def _iteration(self):
        """
        Single iteration of main loop.

        Pipeline:
        1. Wait for hotkey press (event.set() by HotkeyListener)
        2. Capture audio (blocks until hotkey release or VAD timeout)
           - HotkeyListener sets event on press
           - HotkeyListener clears event on release
           - AudioCapture loops while event.is_set()
        3. Transcribe audio via Cloud STT API (blocking, with timeout)
        4. Classify transcription (deterministic)
        5. Record result (explicit failure handling)
        """
        self.hotkey_event.wait()
        # NOTE: Do NOT clear event here - HotkeyListener clears on release

        print("[F12 PRESSED] Recording audio...", flush=True)

        # STEP 1: Audio Capture (JARVIS-DEC-001)
        try:
            audio = self.audio_capture.capture(self.hotkey_event)
            print(f"[AUDIO CAPTURED] {audio.duration_ms}ms", flush=True)
        except AudioCaptureError as e:
            print(f"[AUDIO ERROR] {e}", flush=True)
            return

        # STEP 1.5: Audio Quality Gating (ADR-004: Hybrid Cloud STT)
        try:
            # Trim silence
            audio_trimmed = AudioTrimmer.trim(audio)
            print(f"[AUDIO TRIMMED] {audio_trimmed.duration_ms}ms (was {audio.duration_ms}ms)", flush=True)

            # Validate quality
            is_valid, reason = AudioQualityGates.validate(audio_trimmed)
            if not is_valid:
                print(f"[AUDIO QUALITY REJECTED] {reason}", flush=True)
                return

            audio = audio_trimmed  # Use trimmed audio for STT
            print(f"[AUDIO QUALITY PASSED] ✓", flush=True)
        except Exception as e:
            print(f"[AUDIO QUALITY ERROR] {e}", flush=True)
            return

        # STEP 2: STT Transcription via Cloud API (JARVIS-DEC-001, blocking)
        try:
            print("[TRANSCRIBING...] Processing with Cloud Whisper (backend API)...", flush=True)
            transcription = self.stt_adapter.transcribe(audio)
            print(f"[TRANSCRIPTION] '{transcription}'", flush=True)
        except CloudSTTError as e:
            print(f"[STT ERROR] {e}", flush=True)
            return

        # STEP 3: Input Classification (JARVIS-L1-DEC-001, deterministic)
        try:
            input_signal = InputSignal(text=transcription, source="hotkey")
            classified = self.input_boundary.classify(input_signal)

            if isinstance(classified, CommandInput):
                print(f"[CLASSIFIED] COMMAND '{classified.command}' (args: {classified.args})", flush=True)
            elif isinstance(classified, VoiceInput):
                print(f"[CLASSIFIED] VOICE INPUT", flush=True)
        except InputClassificationError as e:
            print(f"[CLASSIFICATION ERROR] {e}", flush=True)
            return

        # STEP 4: Route by classification type
        if isinstance(classified, CommandInput):
            print("[ROUTING] → CommandExecutor", flush=True)
            self._handle_command(classified)
        elif isinstance(classified, VoiceInput):
            print("[ROUTING] → CLIAdapter", flush=True)
            self._handle_voice_input(classified)

    def _handle_command(self, command: CommandInput):
        """
        Execute a recognized command (help only).

        Enforcement (Compliance Locked):
        - No toasts, no UI notifications
        - Print output to stdout
        - Silent failures go to stdout
        """
        try:
            result = self.command_executor.execute(
                command.command,
                command.args,
                self.state
            )
            print(f"[COMMAND OUTPUT]\n{result.message}", flush=True)

        except CommandExecutionError as e:
            print(f"[COMMAND ERROR] {str(e)}", flush=True)

    def _handle_voice_input(self, voice_input: VoiceInput):
        """
        Handle voice input (send to Claude CLI as-is).

        Enforcement (Compliance Locked):
        - No safety evaluation (SafetyGate is pass-through)
        - No prompt wrapping (PromptShaper is pass-through)
        - Send text directly to Claude
        - No toasts, no dialogs, no UI notifications
        """
        text = voice_input.text

        # Safety check (now pass-through, always ALLOW)
        safety_result = self.safety_gate.check(text)

        # Shape prompt (now pass-through, no modification)
        try:
            wrapped = self.prompt_shaper.shape(text=text, mode=self.state.mode)
        except PromptShaperError as e:
            print(f"[PROMPT SHAPER ERROR] {str(e)}", flush=True)
            return

        # Send to Claude CLI
        try:
            self.cli_adapter.send(wrapped.wrapped_text)
            print(f"[SENT TO CLAUDE] '{wrapped.wrapped_text}'", flush=True)
        except CLIAdapterError as e:
            print(f"[CLI ERROR] {str(e)}", flush=True)

    def stop(self):
        """Stop main loop gracefully."""
        self._running = False

    def get_state(self) -> SessionState:
        """Read-only access to session state."""
        return self.state
