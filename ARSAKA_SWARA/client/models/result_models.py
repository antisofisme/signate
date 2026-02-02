"""
Result models from components.

See JARVIS-L1-DEC-002: Command Execution Boundary for specifications.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CommandResult:
    """
    Result of command execution.

    Contract (JARVIS-L1-DEC-002):
    - Success flag + display message
    - Optional side effects (mode change)
    - Never sent to Claude
    - Clear indication of success or failure
    """

    success: bool
    display: str  # User-facing message (success or error)
    mode_change: Optional[str] = None  # New mode if mode command (e.g., "coding")
    command_executed: Optional[str] = None  # Which command was executed
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Validate success state."""
        if not self.success and self.mode_change:
            raise ValueError("Failed command cannot change mode")


@dataclass
class ExecutionResult:
    """
    Generic execution result for any operation.

    Used for operations that may succeed or fail.
    """

    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    timestamp: Optional[float] = None
