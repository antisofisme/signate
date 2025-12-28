"""
Input models - Data structures for input signals and classification

Used by:
- InputBoundary (classifier)
- MainLoop (routes classified input)
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class InputSource(Enum):
    """Where input originated from."""
    HOTKEY = "hotkey"
    CLI = "cli"
    KEYBOARD = "keyboard"


@dataclass
class AudioBuffer:
    """Raw PCM audio data."""
    samples: "np.ndarray"
    sample_rate: int = 16000
    duration_seconds: float = 0.0

    def __post_init__(self):
        import numpy as np
        self.duration_seconds = len(self.samples) / self.sample_rate


@dataclass
class InputSignal:
    """Raw input signal (unclassified)."""
    text: str
    source: InputSource = InputSource.HOTKEY

    def __post_init__(self):
        self.text = self.text.strip()


class InputType(Enum):
    """Classified input type."""
    VOICE = "voice"
    COMMAND = "command"
    UNKNOWN = "unknown"


@dataclass
class VoiceInput:
    """Classified as voice input (speech to be transcribed)."""
    text: str
    confidence: Optional[float] = None
    original_signal: Optional[InputSignal] = None


@dataclass
class CommandInput:
    """Classified as command input (exact/prefix match)."""
    command: str
    args: Optional[str] = None
    original_signal: Optional[InputSignal] = None


@dataclass
class InputEvent:
    """Classified input event (ready for routing)."""
    input_type: InputType
    data: Optional[VoiceInput | CommandInput] = None

    def is_command(self) -> bool:
        return self.input_type == InputType.COMMAND

    def is_voice(self) -> bool:
        return self.input_type == InputType.VOICE

    def is_unknown(self) -> bool:
        return self.input_type == InputType.UNKNOWN
