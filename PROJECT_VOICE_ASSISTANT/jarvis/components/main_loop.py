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
from jarvis.components.audio_capture import AudioCapture, AudioCaptureError, AudioBuffer
from jarvis.components.stt_adapter import STTAdapter, STTTimeoutError, STTConfidenceError, STTError
from jarvis.components.input_boundary import InputBoundary, InputSignal, CommandInput, VoiceInput, InputClassificationError
from jarvis.components.command_executor import CommandExecutor, CommandExecutionError
from jarvis.components.safety_gate import SafetyGate, SafetyDecision
from jarvis.components.prompt_shaper import PromptShaper, PromptShaperError
from jarvis.components.cli_adapter import CLIAdapter, CLIAdapterError
from jarvis.components.ui_notifier import UINotifier, Toast, Dialog, ErrorDisplay


class SessionState:
    """
    In-memory session state holder.

    ONLY MainLoop may mutate this.
    HotkeyListener does NOT access.
    Components may READ (immutable copy only).
    """

    def __init__(self):
        self.mode = "default"
        self.last_audio: Optional[AudioBuffer] = None
        self.last_transcription: Optional[str] = None
        self.last_classification: Optional[Union[CommandInput, VoiceInput]] = None
        self.last_error: Optional[str] = None
        self.input_count = 0
        self.is_active = False

    def record_audio(self, audio: AudioBuffer):
        """MainLoop only."""
        self.last_audio = audio

    def record_transcription(self, text: str):
        """MainLoop only."""
        self.last_transcription = text

    def record_classification(self, classified: Union[CommandInput, VoiceInput]):
        """MainLoop only."""
        self.last_classification = classified

    def record_error(self, error: str):
        """MainLoop only."""
        self.last_error = error

    def increment_input_count(self):
        """MainLoop only."""
        self.input_count += 1

    def update_mode(self, mode: str):
        """MainLoop only."""
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
        stt_timeout_ms: int = 1000,
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

        self.stt_adapter = STTAdapter(
            model=stt_model,
            timeout_ms=stt_timeout_ms,
            language="en",
        )

        self.input_boundary = InputBoundary()

        self.command_executor = CommandExecutor()

        self.safety_gate = SafetyGate()

        self.prompt_shaper = PromptShaper()

        self.cli_adapter = CLIAdapter()

        self.ui_notifier = UINotifier()

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
            self.state.record_error(f"MainLoop error: {str(e)}")
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
        3. Transcribe audio via STT (blocking, with timeout)
        4. Classify transcription (deterministic)
        5. Record result (explicit failure handling)
        """
        self.hotkey_event.wait()
        # NOTE: Do NOT clear event here - HotkeyListener clears on release

        self.state.increment_input_count()

        # STEP 1: Audio Capture (JARVIS-DEC-001)
        try:
            audio = self.audio_capture.capture(self.hotkey_event)
            self.state.record_audio(audio)
        except AudioCaptureError as e:
            # Failure mode 1: Audio capture fails
            self.state.record_error(str(e))
            return

        # STEP 2: STT Transcription (JARVIS-DEC-001, blocking)
        try:
            transcription = self.stt_adapter.transcribe(audio)
            self.state.record_transcription(transcription)
        except STTTimeoutError as e:
            # Failure mode 2: STT timeout
            self.state.record_error(str(e))
            return
        except STTConfidenceError as e:
            # Failure mode 3: STT low confidence
            self.state.record_error(str(e))
            return
        except STTError as e:
            # Failure mode 4: STT general failure
            self.state.record_error(str(e))
            return

        # STEP 3: Input Classification (JARVIS-L1-DEC-001, deterministic)
        try:
            input_signal = InputSignal(text=transcription, source="hotkey")
            classified = self.input_boundary.classify(input_signal)
            self.state.record_classification(classified)
        except InputClassificationError as e:
            # Failure mode 5: Classification fails
            self.state.record_error(str(e))
            self.ui_notifier.display(ErrorDisplay(
                level="error",
                message=f"Input parsing failed. {str(e)}",
                show_as="toast"
            ))
            return

        # STEP 4: Route by classification type
        if isinstance(classified, CommandInput):
            self._handle_command(classified)
        elif isinstance(classified, VoiceInput):
            self._handle_voice_input(classified)

    def _handle_command(self, command: CommandInput):
        """
        Execute a recognized command.

        Commands: kirim, ulang, mode, help
        """
        try:
            result = self.command_executor.execute(
                command.command,
                command.args,
                self.state
            )

            # Display result
            if result.success:
                self.ui_notifier.display(Toast(
                    level="success",
                    message=result.message,
                    duration_ms=2000
                ))
            else:
                self.ui_notifier.display(ErrorDisplay(
                    level="error",
                    message=result.message,
                    show_as="toast"
                ))

        except CommandExecutionError as e:
            self.state.record_error(str(e))
            self.ui_notifier.display(ErrorDisplay(
                level="error",
                message=str(e),
                show_as="toast"
            ))

    def _handle_voice_input(self, voice_input: VoiceInput):
        """
        Handle voice input (send to Claude after safety check).

        Flow:
        1. Check safety (SafetyGate)
        2. If dangerous: show confirmation dialog
        3. If approved or safe: shape prompt and send to Claude
        """
        text = voice_input.text

        # STEP 4A: Safety check (JARVIS-DEC-003)
        safety_result = self.safety_gate.check(text)

        if safety_result.decision == SafetyDecision.REQUIRE_CONFIRMATION:
            # Ask for user confirmation
            response = self.ui_notifier.display(Dialog(
                title="⚠️  DANGEROUS OPERATION DETECTED",
                message=f"Pattern: {safety_result.matched_pattern}\n"
                        f"You said: \"{text}\"\n\n"
                        f"Continue? [Y] [N]"
            ))

            if not response:  # User pressed N
                self.ui_notifier.display(Toast(
                    level="info",
                    message="Operation cancelled.",
                    duration_ms=2000
                ))
                return

        # STEP 4B: Shape prompt (JARVIS-L1-DEC-003)
        try:
            wrapped = self.prompt_shaper.shape(
                text=text,
                mode=self.state.mode
            )
        except PromptShaperError as e:
            self.state.record_error(str(e))
            self.ui_notifier.display(ErrorDisplay(
                level="error",
                message=f"Failed to shape prompt. {str(e)}",
                show_as="toast"
            ))
            return

        # STEP 4C: Send to Claude CLI (JARVIS-L1-DEC-004, fire-and-forget)
        try:
            self.cli_adapter.send(wrapped.wrapped_text)
            self.ui_notifier.display(Toast(
                level="success",
                message="Sent to Claude",
                duration_ms=2000
            ))
        except CLIAdapterError as e:
            self.state.record_error(str(e))
            self.ui_notifier.display(ErrorDisplay(
                level="error",
                message=f"Failed to send to Claude. {str(e)}",
                show_as="toast"
            ))

    def stop(self):
        """Stop main loop gracefully."""
        self._running = False

    def get_state(self) -> SessionState:
        """Read-only access to session state."""
        return self.state
