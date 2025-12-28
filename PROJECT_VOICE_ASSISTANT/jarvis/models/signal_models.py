"""
UI signal models.

See JARVIS-L3-ARCH-003: Error Propagation & UI Signaling for specifications.

Contract: Signals are pure data. UINotifier displays them.
No decision-making in signal creation (MainLoop decides).
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class SignalLevel(str, Enum):
    """Signal severity level."""

    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Toast:
    """
    Non-blocking message.

    Contract (JARVIS-L3-ARCH-003):
    - Appears briefly (3-5 seconds)
    - User can ignore
    - Doesn't require action
    - Dismissible

    Examples:
    - "Mode: CODING"
    - "Sent to Claude"
    - "STT failed. Try again or type instead."
    """

    level: SignalLevel
    message: str  # ≤100 characters, user-focused
    duration_ms: int = 3000
    dismissible: bool = True
    action: Optional[str] = None  # Intentionally None (no action in toast)


@dataclass
class Dialog:
    """
    Blocking confirmation dialog.

    Contract (JARVIS-L3-ARCH-003):
    - Blocks main loop until user responds
    - Requires explicit Y/N or similar
    - Cannot be ignored
    - Modal (nothing else can happen)

    Used ONLY for safety gates (user must make irreversible decision).
    """

    title: str
    message: str
    buttons: List[str]  # e.g., ["Y", "N"]
    timeout_ms: Optional[int] = None  # Intentionally None (user controls timing)
    default_action: str = "N"  # Conservative default (don't proceed)


@dataclass
class ErrorDisplay:
    """
    Error message with recovery hint.

    Contract (JARVIS-L3-ARCH-003):
    - Clear explanation (not error code)
    - Shows valid alternatives
    - Returned to ready state automatically
    - Shown as toast or status message

    Examples:
    - "Unknown mode 'python'. Modes: default, coding, debug, explain"
    - "STT failed. Please try again or type instead."
    - "Input too long (157s). Max: 120s. Please split."
    """

    level: SignalLevel = SignalLevel.ERROR
    message: str = ""  # Clear, user-facing explanation
    recovery_hint: Optional[str] = None  # e.g., "retry_audio_or_type"
    show_as: str = "toast"  # "toast" or "status_line"


# Union type for all signal types
Signal = toast | Dialog | ErrorDisplay


@dataclass
class SignalDispatch:
    """
    Container for signal to be displayed.

    Used by MainLoop to tell UINotifier what to display.
    """

    signal: Signal
    timestamp: Optional[float] = None
    priority: str = "normal"  # "normal" or "urgent"
