"""
InputBoundary - Deterministic input classification

Architecture: JARVIS-L1-DEC-001 (input contract)
Pattern: Pure function, deterministic grammar matching

No state mutation. No async. No caching.
Same input → Same output (always).
"""

from enum import Enum
from dataclasses import dataclass
from typing import Union, Optional


class InputType(Enum):
    """Input signal type."""
    VOICE = "voice"
    COMMAND = "command"
    UNKNOWN = "unknown"


@dataclass
class InputSignal:
    """Raw input signal (from external source)."""
    text: str
    source: str = "voice"

    def __post_init__(self):
        self.text = self.text.strip()


@dataclass
class VoiceInput:
    """Classified as voice input (to be transcribed via STT)."""
    text: str
    confidence: Optional[float] = None


@dataclass
class CommandInput:
    """Classified as command input (exact/prefix match)."""
    command: str
    args: Optional[str] = None


class InputClassificationError(Exception):
    """Input classification error (user-facing message)."""
    pass


class InputBoundary:
    """
    Deterministic input classifier.

    Pure function: no state access, no side effects.
    Classifies InputSignal → CommandInput | VoiceInput.

    Valid commands (exact/prefix match, case-insensitive):
    - "kirim" (send)
    - "ulang" (resend)
    - "mode {mode}" (change mode)
    - "help" (show help)

    Invalid commands → re-classified as voice.

    Pattern:
        classifier = InputBoundary()
        result = classifier.classify(InputSignal("kirim"))
        # Returns: CommandInput(command="kirim")

        result = classifier.classify(InputSignal("hello world"))
        # Returns: VoiceInput(text="hello world")
    """

    VALID_COMMANDS = {"kirim", "ulang", "mode", "help"}
    VALID_MODES = {"default", "coding", "debug", "explain"}

    def __init__(self):
        """Initialize classifier (stateless)."""
        pass

    def classify(self, signal: InputSignal) -> Union[CommandInput, VoiceInput]:
        """
        Classify input signal deterministically.

        Args:
            signal: InputSignal with text

        Returns:
            CommandInput or VoiceInput

        Raises:
            InputClassificationError: If classification fails
        """
        if not signal or not signal.text:
            raise InputClassificationError("Empty input signal")

        text = signal.text.strip().lower()

        if not text:
            raise InputClassificationError("Input contains only whitespace")

        command_result = self._try_match_command(text)
        if command_result is not None:
            return command_result

        return VoiceInput(text=signal.text)

    def _try_match_command(self, text: str) -> Optional[CommandInput]:
        """
        Attempt to match command (exact or prefix).

        Grammar (case-insensitive):
        - "kirim" → CommandInput(command="kirim")
        - "ulang" → CommandInput(command="ulang")
        - "mode {mode}" → CommandInput(command="mode", args="{mode}")
        - "help" → CommandInput(command="help")

        Args:
            text: Lowercase input text

        Returns:
            CommandInput if matches, None otherwise
        """
        words = text.split()

        if not words:
            return None

        first_word = words[0]

        if first_word == "kirim":
            return CommandInput(command="kirim")

        if first_word == "ulang":
            return CommandInput(command="ulang")

        if first_word == "help":
            return CommandInput(command="help")

        if first_word == "mode":
            if len(words) < 2:
                return None

            mode = words[1].lower()

            if mode not in self.VALID_MODES:
                return None

            return CommandInput(command="mode", args=mode)

        return None

    def get_valid_commands(self) -> dict:
        """
        Get list of valid commands (read-only).

        Returns:
            dict with command name and description
        """
        return {
            "kirim": "Send (press Enter)",
            "ulang": "Resend last transcription",
            "mode": "Change mode (default|coding|debug|explain)",
            "help": "Show help",
        }
