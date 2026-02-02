"""
Exception definitions for JARVIS.

Contract: All exceptions represent explicit failures.
No auto-recovery. User decides next action.
"""


class JarvisException(Exception):
    """
    Base exception for all JARVIS errors.

    Contract:
    - Exception raised means failure is explicit (non-silent)
    - Message is user-facing (not technical jargon)
    - Does not imply retry or recovery
    """

    def __init__(self, message: str, recovery_hint: str = None):
        """
        Args:
            message: User-facing explanation
            recovery_hint: Optional hint for recovery (e.g., "try again or type")
        """
        self.message = message
        self.recovery_hint = recovery_hint
        super().__init__(self.message)


class AudioCaptureError(JarvisException):
    """
    Audio capture failed.

    Trigger:
    - Microphone not available
    - Audio device error
    - Hotkey release before audio captured

    Recovery: User can retry or type manually
    """

    pass


class STTError(JarvisException):
    """
    Base exception for STT (speech-to-text) failures.

    Contract:
    - STT is blocking (by design, see JARVIS-L3-ARCH-002)
    - Failure is explicit (not hidden in background)
    - User decides next action (retry or type)
    """

    pass


class STTTimeoutError(STTError):
    """
    STT exceeded timeout.

    Trigger:
    - Whisper processing > configured timeout (≤1s target)
    - Model not responding

    Recovery: User retry or type manually
    """

    def __init__(self, timeout_ms: int, max_allowed_ms: int = 1000):
        self.timeout_ms = timeout_ms
        self.max_allowed_ms = max_allowed_ms
        message = f"STT failed. Please try again or type instead."
        super().__init__(message, recovery_hint="retry_audio_or_type")


class STTConfidenceError(STTError):
    """
    STT confidence below threshold.

    Trigger:
    - Whisper returned text but confidence < 0.5

    Recovery: User retry with clearer speech or type manually
    """

    def __init__(self, confidence: float, threshold: float = 0.5):
        self.confidence = confidence
        self.threshold = threshold
        message = f"Audio quality too low. Please speak clearly."
        super().__init__(message, recovery_hint="retry_audio_or_type")


class InputClassificationError(JarvisException):
    """
    Input classification failed.

    Trigger:
    - Encoding error
    - Grammar parsing failure
    - Invalid input type

    Recovery: User retry with valid input
    """

    pass


class SafetyGateError(JarvisException):
    """
    Safety gate rejected input.

    Trigger:
    - Dangerous pattern detected (rm -rf, DROP TABLE, etc.)
    - User rejected confirmation dialog

    Recovery: User decides (continue or cancel)
    """

    def __init__(self, pattern: str = None, user_confirmed: bool = False):
        self.pattern = pattern
        self.user_confirmed = user_confirmed

        if not user_confirmed:
            message = f"Operation canceled."
        else:
            message = f"Dangerous pattern detected. Proceeding anyway."

        super().__init__(message)


class PromptShapingError(JarvisException):
    """
    Prompt shaping failed.

    Trigger:
    - Invalid mode
    - Unexpected input structure

    Recovery: User retry
    """

    pass


class CommandExecutionError(JarvisException):
    """
    Command execution failed.

    Trigger:
    - Invalid command argument
    - Command validation failed

    Recovery: User retry with valid arguments
    """

    pass


class CLIInteractionError(JarvisException):
    """
    Failed to interact with Claude CLI.

    Trigger:
    - Text insertion failed (xdotool error)
    - Key press failed
    - Terminal not available

    Recovery: User retry or type manually
    """

    pass


class JarvisInternalError(JarvisException):
    """
    Unexpected internal error.

    Trigger:
    - Uncaught exception
    - State corruption
    - Component failure

    Recovery: Restart Jarvis
    """

    def __init__(self, details: str = None):
        self.details = details
        message = "Internal error. Please restart Jarvis."
        super().__init__(message, recovery_hint="restart_jarvis")
