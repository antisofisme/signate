"""JARVIS components."""

from jarvis.components.hotkey_listener import HotkeyListener
from jarvis.components.audio_capture import AudioCapture, AudioBuffer, AudioCaptureError
from jarvis.components.main_loop import MainLoopOrchestrator, SessionState
from jarvis.components.stt_adapter import (
    STTAdapter,
    STTTimeoutError,
    STTConfidenceError,
    STTError,
)
from jarvis.components.input_boundary import (
    InputBoundary,
    InputSignal,
    VoiceInput,
    CommandInput,
    InputClassificationError,
    InputType,
)
from jarvis.components.command_executor import (
    CommandExecutor,
    ExecutionResult,
    CommandExecutionError,
)
from jarvis.components.safety_gate import (
    SafetyGate,
    SafetyDecision,
    SafetyCheckResult,
    SafetyGateError,
)
from jarvis.components.prompt_shaper import (
    PromptShaper,
    PromptShaperError,
    WrappedPrompt,
)
from jarvis.components.cli_adapter import (
    CLIAdapter,
    CLIAdapterError,
)
from jarvis.components.ui_notifier import (
    UINotifier,
    UINotifierError,
    Toast,
    Dialog,
    ErrorDisplay,
)

__all__ = [
    "HotkeyListener",
    "AudioCapture",
    "AudioBuffer",
    "AudioCaptureError",
    "MainLoopOrchestrator",
    "SessionState",
    "STTAdapter",
    "STTTimeoutError",
    "STTConfidenceError",
    "STTError",
    "InputBoundary",
    "InputSignal",
    "VoiceInput",
    "CommandInput",
    "InputClassificationError",
    "InputType",
    "CommandExecutor",
    "ExecutionResult",
    "CommandExecutionError",
    "SafetyGate",
    "SafetyDecision",
    "SafetyCheckResult",
    "SafetyGateError",
    "PromptShaper",
    "PromptShaperError",
    "WrappedPrompt",
    "CLIAdapter",
    "CLIAdapterError",
    "UINotifier",
    "UINotifierError",
    "Toast",
    "Dialog",
    "ErrorDisplay",
]
