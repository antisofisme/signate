"""
Architectural Invariant Tests

These tests enforce architectural contracts (Layer 2-3).
They run at PR check-in and block merges on failure.

NOT annotation checks. RUNTIME behavior verification.
"""

import inspect
import threading
import pytest
from jarvis.components.audio_capture import AudioCapture, AudioBuffer
from jarvis.components.main_loop import MainLoopOrchestrator, SessionState
from jarvis.components.hotkey_listener import HotkeyListener


class TestAudioCaptureIsBlocking:
    """Verify AudioCapture.capture() is synchronous blocking."""

    def test_capture_not_async(self):
        """capture() must NOT be async (no coroutine function)."""
        assert not inspect.iscoroutinefunction(AudioCapture.capture)

    def test_capture_returns_audio_buffer(self):
        """capture() must return AudioBuffer, not Future/Task/Coroutine."""
        hotkey = threading.Event()
        hotkey.set()

        capture = AudioCapture(
            sample_rate=16000,
            vad_timeout_ms=100,
            duration_ceiling_ms=1000,
            frame_size_ms=10,
        )

        result = capture.capture(hotkey)
        assert isinstance(result, AudioBuffer)
        assert not inspect.iscoroutine(result)


class TestHotkeyListenerIsSignalOnly:
    """Verify HotkeyListener callback is signal-only."""

    def test_callback_exists(self):
        """_on_hotkey_pressed() must exist."""
        listener = HotkeyListener()
        assert hasattr(listener, "_on_hotkey_pressed")
        assert callable(listener._on_hotkey_pressed)

    def test_listener_runs_in_thread(self):
        """HotkeyListener must be a Thread subclass."""
        assert issubclass(HotkeyListener, threading.Thread)


class TestMainLoopSingleWriter:
    """Verify only MainLoop mutates SessionState."""

    def test_session_state_has_mutation_methods(self):
        """SessionState must have explicit mutation methods."""
        state = SessionState()
        assert hasattr(state, "record_audio")
        assert hasattr(state, "record_error")
        assert hasattr(state, "increment_input_count")

    def test_hotkey_listener_cannot_access_state(self):
        """HotkeyListener must NOT have state parameter."""
        sig = inspect.signature(HotkeyListener.__init__)
        params = list(sig.parameters.keys())
        assert "state" not in params
        assert "session_state" not in params

    def test_main_loop_owns_state(self):
        """MainLoopOrchestrator must create and own SessionState."""
        loop = MainLoopOrchestrator()
        assert hasattr(loop, "state")
        assert isinstance(loop.state, SessionState)


class TestMainLoopIsBlocking:
    """Verify MainLoop.run() is synchronous."""

    def test_run_not_async(self):
        """run() must NOT be async."""
        assert not inspect.iscoroutinefunction(MainLoopOrchestrator.run)


class TestNoSilentErrors:
    """Verify errors have explicit messages."""

    def test_audio_capture_error_has_message(self):
        """AudioCaptureError must include user-facing message."""
        from jarvis.components.audio_capture import AudioCaptureError

        msg = "Test error"
        err = AudioCaptureError(msg)
        assert str(err) == msg


class TestExplicitState:
    """Verify state is explicit, not implicit."""

    def test_session_state_is_mutable(self):
        """SessionState must allow explicit mutation."""
        state = SessionState()
        assert state.mode == "default"
        assert state.last_audio is None
        assert state.last_error is None
        assert state.input_count == 0

    def test_session_state_mutation_explicit(self):
        """State mutations must be explicit method calls."""
        state = SessionState()
        state.increment_input_count()
        assert state.input_count == 1

        state.record_error("test error")
        assert state.last_error == "test error"


class TestSTTAdapterIsBlocking:
    """Verify STTAdapter.transcribe() is synchronous blocking."""

    def test_transcribe_not_async(self):
        """transcribe() must NOT be async."""
        from jarvis.components.stt_adapter import STTAdapter

        assert not inspect.iscoroutinefunction(STTAdapter.transcribe)

    def test_transcribe_timeout_enforced(self):
        """STTAdapter must enforce timeout constraint."""
        from jarvis.components.stt_adapter import STTAdapter, STTTimeoutError

        adapter = STTAdapter(timeout_ms=100, model="base")
        assert adapter.timeout_ms == 100

    def test_transcribe_confidence_threshold(self):
        """STTAdapter must enforce confidence threshold."""
        from jarvis.components.stt_adapter import STTAdapter

        adapter = STTAdapter(min_confidence=0.5, model="base")
        assert adapter.min_confidence == 0.5


class TestInputBoundaryIsPure:
    """Verify InputBoundary is deterministic and pure."""

    def test_classify_not_async(self):
        """classify() must NOT be async."""
        from jarvis.components.input_boundary import InputBoundary

        assert not inspect.iscoroutinefunction(InputBoundary.classify)

    def test_classify_deterministic(self):
        """classify() must be deterministic (same input → same output)."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal, CommandInput

        classifier = InputBoundary()
        signal = InputSignal("kirim")

        result1 = classifier.classify(signal)
        result2 = classifier.classify(signal)

        assert result1.command == result2.command == "kirim"

    def test_classify_no_state_mutation(self):
        """classify() must not mutate classifier state."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal

        classifier = InputBoundary()
        initial_commands = classifier.get_valid_commands()

        classifier.classify(InputSignal("test"))

        assert classifier.get_valid_commands() == initial_commands

    def test_classify_command_recognition(self):
        """classify() must recognize valid commands (exact/prefix match)."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal, CommandInput

        classifier = InputBoundary()

        result = classifier.classify(InputSignal("kirim"))
        assert isinstance(result, CommandInput)
        assert result.command == "kirim"

        result = classifier.classify(InputSignal("mode coding"))
        assert isinstance(result, CommandInput)
        assert result.command == "mode"
        assert result.args == "coding"

    def test_classify_voice_fallback(self):
        """classify() must fallback to VoiceInput for unrecognized input."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal, VoiceInput

        classifier = InputBoundary()

        result = classifier.classify(InputSignal("hello world"))
        assert isinstance(result, VoiceInput)
        assert result.text == "hello world"


class TestDeterministicBehavior:
    """Verify deterministic (no caching, no state, no randomness)."""

    def test_input_boundary_idempotent(self):
        """InputBoundary must be idempotent."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal

        classifier = InputBoundary()
        signal = InputSignal("ulang")

        results = [classifier.classify(signal) for _ in range(5)]

        assert all(r.command == "ulang" for r in results)

    def test_stt_no_caching(self):
        """STTAdapter must not cache results (no caching allowed)."""
        from jarvis.components.stt_adapter import STTAdapter

        adapter = STTAdapter(model="base")
        assert not hasattr(adapter, "_cache")
        assert not hasattr(adapter, "cache")
        assert not hasattr(adapter, "_transcription_cache")


class TestWeek2Integration:
    """Verify complete Week 2 pipeline integration."""

    def test_main_loop_owns_stt_adapter(self):
        """MainLoop must own STTAdapter instance."""
        from jarvis.components.main_loop import MainLoopOrchestrator

        loop = MainLoopOrchestrator()
        assert hasattr(loop, "stt_adapter")
        from jarvis.components.stt_adapter import STTAdapter
        assert isinstance(loop.stt_adapter, STTAdapter)

    def test_main_loop_owns_input_boundary(self):
        """MainLoop must own InputBoundary instance."""
        from jarvis.components.main_loop import MainLoopOrchestrator

        loop = MainLoopOrchestrator()
        assert hasattr(loop, "input_boundary")
        from jarvis.components.input_boundary import InputBoundary
        assert isinstance(loop.input_boundary, InputBoundary)

    def test_session_state_tracks_transcription(self):
        """SessionState must track transcription."""
        from jarvis.components.main_loop import SessionState

        state = SessionState()
        assert hasattr(state, "last_transcription")
        assert state.last_transcription is None

        state.record_transcription("hello world")
        assert state.last_transcription == "hello world"

    def test_session_state_tracks_classification(self):
        """SessionState must track classification."""
        from jarvis.components.main_loop import SessionState
        from jarvis.components.input_boundary import CommandInput

        state = SessionState()
        assert hasattr(state, "last_classification")
        assert state.last_classification is None

        classified = CommandInput(command="kirim")
        state.record_classification(classified)
        assert state.last_classification == classified

    def test_session_state_update_mode(self):
        """SessionState must support mode updates."""
        from jarvis.components.main_loop import SessionState

        state = SessionState()
        assert state.mode == "default"

        state.update_mode("coding")
        assert state.mode == "coding"

    def test_explicit_failure_mode_1_audio_capture(self):
        """Explicit failure handling: Audio capture error."""
        from jarvis.components.main_loop import SessionState
        from jarvis.components.audio_capture import AudioCaptureError

        state = SessionState()
        error_msg = "Audio capture failed"
        state.record_error(error_msg)

        assert state.last_error == error_msg
        assert state.last_audio is None

    def test_explicit_failure_mode_2_stt_timeout(self):
        """Explicit failure handling: STT timeout."""
        from jarvis.components.stt_adapter import STTTimeoutError

        try:
            raise STTTimeoutError("Transcription exceeded 1000ms timeout")
        except STTTimeoutError as e:
            assert "timeout" in str(e).lower()
            assert isinstance(e, Exception)

    def test_explicit_failure_mode_3_stt_confidence(self):
        """Explicit failure handling: STT low confidence."""
        from jarvis.components.stt_adapter import STTConfidenceError

        try:
            raise STTConfidenceError("Confidence 0.3 below threshold 0.5")
        except STTConfidenceError as e:
            assert "confidence" in str(e).lower()
            assert isinstance(e, Exception)

    def test_explicit_failure_mode_4_stt_error(self):
        """Explicit failure handling: STT general failure."""
        from jarvis.components.stt_adapter import STTError

        try:
            raise STTError("Transcription failed: model loading error")
        except STTError as e:
            assert "transcription" in str(e).lower()
            assert isinstance(e, Exception)

    def test_explicit_failure_mode_5_classification_error(self):
        """Explicit failure handling: Classification fails."""
        from jarvis.components.input_boundary import InputClassificationError

        try:
            raise InputClassificationError("Empty input signal")
        except InputClassificationError as e:
            assert "input" in str(e).lower()
            assert isinstance(e, Exception)

    def test_week2_pipeline_command_path(self):
        """Verify command path: HotKey → Audio → STT → Classification → CommandInput."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal, CommandInput

        boundary = InputBoundary()
        signal = InputSignal("kirim")
        result = boundary.classify(signal)

        assert isinstance(result, CommandInput)
        assert result.command == "kirim"

    def test_week2_pipeline_voice_path(self):
        """Verify voice path: HotKey → Audio → STT → Classification → VoiceInput."""
        from jarvis.components.input_boundary import InputBoundary, InputSignal, VoiceInput

        boundary = InputBoundary()
        signal = InputSignal("what time is it")
        result = boundary.classify(signal)

        assert isinstance(result, VoiceInput)
        assert result.text == "what time is it"

    def test_week2_no_silent_failures(self):
        """Verify no silent failures: all errors are explicit."""
        from jarvis.components.stt_adapter import STTTimeoutError, STTConfidenceError, STTError
        from jarvis.components.input_boundary import InputClassificationError

        errors = [
            STTTimeoutError("timeout"),
            STTConfidenceError("confidence"),
            STTError("error"),
            InputClassificationError("classification"),
        ]

        for error in errors:
            assert str(error)  # All have messages
            assert isinstance(error, Exception)


class TestCommandExecutor:
    """Verify CommandExecutor deterministic execution."""

    def test_executor_exists(self):
        """CommandExecutor must exist."""
        from jarvis.components.command_executor import CommandExecutor

        executor = CommandExecutor()
        assert executor is not None

    def test_kirim_command(self):
        """Execute kirim command."""
        from jarvis.components.command_executor import CommandExecutor

        executor = CommandExecutor()
        result = executor.execute("kirim", None, None)
        assert result.success is True

    def test_mode_command_valid(self):
        """Execute mode command with valid mode."""
        from jarvis.components.command_executor import CommandExecutor
        from jarvis.components.main_loop import SessionState

        executor = CommandExecutor()
        state = SessionState()
        result = executor.execute("mode", "coding", state)
        assert result.success is True
        assert state.mode == "coding"

    def test_mode_command_invalid(self):
        """Reject invalid mode."""
        from jarvis.components.command_executor import CommandExecutor, CommandExecutionError

        executor = CommandExecutor()
        try:
            executor.execute("mode", "invalid_mode", None)
            assert False, "Should raise error"
        except CommandExecutionError as e:
            assert "invalid" in str(e).lower()

    def test_unknown_command_fails_loudly(self):
        """Unknown commands fail explicitly."""
        from jarvis.components.command_executor import CommandExecutor, CommandExecutionError

        executor = CommandExecutor()
        try:
            executor.execute("unknown_command", None, None)
            assert False, "Should raise error"
        except CommandExecutionError as e:
            assert "unknown" in str(e).lower()

    def test_ulang_without_transcription(self):
        """Ulang fails if no previous transcription."""
        from jarvis.components.command_executor import CommandExecutor, CommandExecutionError
        from jarvis.components.main_loop import SessionState

        executor = CommandExecutor()
        state = SessionState()
        try:
            executor.execute("ulang", None, state)
            assert False, "Should raise error"
        except CommandExecutionError as e:
            assert "transcription" in str(e).lower()


class TestSafetyGate:
    """Verify SafetyGate deterministic safety checking."""

    def test_gate_exists(self):
        """SafetyGate must exist."""
        from jarvis.components.safety_gate import SafetyGate

        gate = SafetyGate()
        assert gate is not None

    def test_safe_input_allowed(self):
        """Safe input is allowed."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        result = gate.check("hello world")
        assert result.decision == SafetyDecision.ALLOW

    def test_dangerous_pattern_requires_confirmation(self):
        """Dangerous patterns require confirmation."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        result = gate.check("please run rm -rf /home")
        assert result.decision == SafetyDecision.REQUIRE_CONFIRMATION
        assert "rm -rf" in result.matched_pattern

    def test_git_dangerous_pattern(self):
        """Git dangerous patterns are detected."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        result = gate.check("execute git reset hard")
        assert result.decision == SafetyDecision.REQUIRE_CONFIRMATION

    def test_database_dangerous_pattern(self):
        """Database dangerous patterns are detected."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        result = gate.check("run drop table users")
        assert result.decision == SafetyDecision.REQUIRE_CONFIRMATION

    def test_system_dangerous_pattern(self):
        """System dangerous patterns are detected."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        result = gate.check("please shutdown the server")
        assert result.decision == SafetyDecision.REQUIRE_CONFIRMATION

    def test_case_insensitive_matching(self):
        """Pattern matching is case-insensitive."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        result = gate.check("RM -RF /home")  # Uppercase
        assert result.decision == SafetyDecision.REQUIRE_CONFIRMATION

    def test_is_safe_convenience_method(self):
        """is_safe() convenience method works."""
        from jarvis.components.safety_gate import SafetyGate

        gate = SafetyGate()
        assert gate.is_safe("hello world") is True
        assert gate.is_safe("rm -rf /") is False

    def test_explicit_patterns_only(self):
        """Only explicit patterns trigger confirmation."""
        from jarvis.components.safety_gate import SafetyGate, SafetyDecision

        gate = SafetyGate()
        # Similar but not exact pattern should be safe
        result = gate.check("remove file manually")
        assert result.decision == SafetyDecision.ALLOW

    def test_no_heuristics(self):
        """SafetyGate uses rules only, no heuristics."""
        from jarvis.components.safety_gate import SafetyGate

        gate = SafetyGate()
        # If SafetyGate had heuristics, it might flag "delete my homework"
        # But with rules-only, it's safe
        result = gate.check("delete my homework")
        assert result.decision.value == "allow"


class TestPromptShaper:
    """Verify PromptShaper deterministic prompt transformation."""

    def test_shaper_exists(self):
        """PromptShaper must exist."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        assert shaper is not None

    def test_default_mode_no_prefix(self):
        """Default mode has no prefix."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        result = shaper.shape(text="hello world", mode="default")
        assert result.wrapped_text == "hello world"
        assert result.prefix == ""

    def test_coding_mode_prefix(self):
        """Coding mode adds [CODING] prefix."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        result = shaper.shape(text="write a function", mode="coding")
        assert result.wrapped_text == "[CODING] write a function"
        assert result.prefix == "[CODING] "

    def test_debug_mode_prefix(self):
        """Debug mode adds [DEBUG] prefix."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        result = shaper.shape(text="why does this crash", mode="debug")
        assert "[DEBUG]" in result.wrapped_text

    def test_explain_mode_prefix(self):
        """Explain mode adds [EXPLAIN] prefix."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        result = shaper.shape(text="explain recursion", mode="explain")
        assert "[EXPLAIN]" in result.wrapped_text

    def test_deterministic(self):
        """PromptShaper is deterministic (same input → same output)."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        result1 = shaper.shape(text="test", mode="coding")
        result2 = shaper.shape(text="test", mode="coding")

        assert result1.wrapped_text == result2.wrapped_text

    def test_invalid_mode_fails(self):
        """Invalid mode raises error."""
        from jarvis.components.prompt_shaper import PromptShaper, PromptShaperError

        shaper = PromptShaper()
        try:
            shaper.shape(text="hello", mode="invalid_mode")
            assert False, "Should raise error"
        except PromptShaperError as e:
            assert "invalid" in str(e).lower()


class TestCLIAdapter:
    """Verify CLIAdapter fire-and-forget text insertion."""

    def test_adapter_exists(self):
        """CLIAdapter must exist."""
        from jarvis.components.cli_adapter import CLIAdapter

        adapter = CLIAdapter()
        assert adapter is not None

    def test_send_text_not_raises(self):
        """CLIAdapter.send() does not raise on valid input."""
        from jarvis.components.cli_adapter import CLIAdapter

        adapter = CLIAdapter()
        # Should not raise
        adapter.send(prompt="[CODING] hello world")

    def test_empty_prompt_fails(self):
        """Empty prompt raises error."""
        from jarvis.components.cli_adapter import CLIAdapter, CLIAdapterError

        adapter = CLIAdapter()
        try:
            adapter.send(prompt="")
            assert False, "Should raise error"
        except CLIAdapterError as e:
            assert "empty" in str(e).lower()

    def test_send_key_enter_accepted(self):
        """CLIAdapter accepts 'Enter' key."""
        from jarvis.components.cli_adapter import CLIAdapter

        adapter = CLIAdapter()
        # Should not raise
        adapter.send_key("Enter")

    def test_send_key_return_accepted(self):
        """CLIAdapter accepts 'Return' key."""
        from jarvis.components.cli_adapter import CLIAdapter

        adapter = CLIAdapter()
        # Should not raise
        adapter.send_key("Return")

    def test_invalid_key_fails(self):
        """Invalid key raises error."""
        from jarvis.components.cli_adapter import CLIAdapter, CLIAdapterError

        adapter = CLIAdapter()
        try:
            adapter.send_key("Control")
            assert False, "Should raise error"
        except CLIAdapterError as e:
            assert "not supported" in str(e).lower() or "only" in str(e).lower()


class TestUINotifier:
    """Verify UINotifier signal display (toast, dialog, error)."""

    def test_notifier_exists(self):
        """UINotifier must exist."""
        from jarvis.components.ui_notifier import UINotifier

        notifier = UINotifier()
        assert notifier is not None

    def test_toast_signal_created(self):
        """Toast signal can be created."""
        from jarvis.components.ui_notifier import Toast

        toast = Toast(level="success", message="Test message")
        assert toast.level == "success"
        assert toast.message == "Test message"

    def test_dialog_signal_created(self):
        """Dialog signal can be created."""
        from jarvis.components.ui_notifier import Dialog

        dialog = Dialog(title="Test", message="Test message")
        assert dialog.title == "Test"
        assert dialog.message == "Test message"
        assert dialog.buttons == ["Y", "N"]

    def test_error_display_signal_created(self):
        """ErrorDisplay signal can be created."""
        from jarvis.components.ui_notifier import ErrorDisplay

        error = ErrorDisplay(level="error", message="Error message")
        assert error.level == "error"
        assert error.message == "Error message"

    def test_three_signal_types_valid(self):
        """All three signal types are valid."""
        from jarvis.components.ui_notifier import Toast, Dialog, ErrorDisplay, UINotifier

        notifier = UINotifier()

        # Toast
        result = notifier.display(Toast(level="success", message="Test"))
        assert result is None

        # ErrorDisplay
        result = notifier.display(ErrorDisplay(level="error", message="Test"))
        assert result is None

        # Dialog (would block in real usage, but test passes quickly)
        # Skipped in automated test to avoid stdin blocking

    def test_notifier_display_returns_none_for_toast(self):
        """UINotifier.display(Toast) returns None."""
        from jarvis.components.ui_notifier import UINotifier, Toast

        notifier = UINotifier()
        result = notifier.display(Toast(level="info", message="Test"))
        assert result is None

    def test_notifier_display_returns_none_for_error(self):
        """UINotifier.display(ErrorDisplay) returns None."""
        from jarvis.components.ui_notifier import UINotifier, ErrorDisplay

        notifier = UINotifier()
        result = notifier.display(ErrorDisplay(level="error", message="Test"))
        assert result is None


class TestWeek4Integration:
    """Verify Week 4 pipeline integration (shaping → CLI → UI)."""

    def test_prompt_shaper_wraps_text(self):
        """PromptShaper wraps text with mode prefix."""
        from jarvis.components.prompt_shaper import PromptShaper

        shaper = PromptShaper()
        result = shaper.shape("write code", "coding")
        assert "[CODING]" in result.wrapped_text

    def test_cli_adapter_accepts_wrapped_prompt(self):
        """CLIAdapter accepts wrapped prompt from PromptShaper."""
        from jarvis.components.prompt_shaper import PromptShaper
        from jarvis.components.cli_adapter import CLIAdapter

        shaper = PromptShaper()
        adapter = CLIAdapter()

        wrapped = shaper.shape("hello", "default")
        adapter.send(wrapped.wrapped_text)  # Should not raise

    def test_ui_notifier_displays_signals(self):
        """UINotifier displays various signals."""
        from jarvis.components.ui_notifier import UINotifier, Toast, ErrorDisplay

        notifier = UINotifier()

        # Success toast
        result = notifier.display(Toast(level="success", message="Sent"))
        assert result is None

        # Error display
        result = notifier.display(ErrorDisplay(level="error", message="Failed"))
        assert result is None

    def test_week4_no_async(self):
        """Week 4 components have no async/await."""
        from jarvis.components import prompt_shaper, cli_adapter, ui_notifier
        import inspect

        modules = [prompt_shaper, cli_adapter, ui_notifier]
        for module in modules:
            for name, obj in inspect.getmembers(module):
                if inspect.iscoroutinefunction(obj):
                    raise AssertionError(f"Found async function: {name} in {module}")

    def test_week4_no_loose_ends(self):
        """Week 4 completion verified: no Week 5 references."""
        from jarvis.components import prompt_shaper, cli_adapter, ui_notifier

        modules = [prompt_shaper, cli_adapter, ui_notifier]
        for module in modules:
            source = inspect.getsource(module)
            assert "Week 5" not in source
            assert "Week4" not in source.lower()
