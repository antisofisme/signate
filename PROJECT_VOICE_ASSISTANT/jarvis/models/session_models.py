"""
Session state model.

See JARVIS-L3-ARCH-001: Component Decomposition for ownership rules.
See JARVIS-L3-ARCH-002: Threading & Concurrency Model for mutation rules.

Contract: Only MainLoop thread may mutate SessionState.
No other thread has write access.
"""

from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class SessionState:
    """
    In-memory session state owned by MainLoop.

    Contract (JARVIS-DEC-002, L3-ARCH-001, L3-ARCH-002):
    - Single-session model: Jarvis lifetime = Claude CLI lifetime
    - No persistence across CLI restart
    - Only MainLoop thread mutates this state
    - All other threads read-only or signal-based

    Data ownership:
    - mode: Current interaction mode
    - last_transcription: Last voice input (for "ulang" command)
    - metrics: Session statistics

    What this state does NOT own:
    - Conversation history (Claude owns)
    - User identity (not Jarvis' concern)
    - Terminal state (Claude owns)
    - Persistent preferences (Layer 0 forbids)
    """

    # ✅ Current interaction mode
    mode: str = "default"  # Options: default, coding, debug, explain

    # ✅ Last voice transcription (for ulang/resend command)
    last_transcription: Optional[str] = None

    # ✅ Session metrics (for diagnostics)
    input_count: int = 0
    error_count: int = 0
    start_time: float = field(default_factory=time.time)
    last_input_time: Optional[float] = None
    last_error_time: Optional[float] = None
    last_error_message: Optional[str] = None

    # ✅ Internal state
    is_ready: bool = True  # MainLoop is waiting for next input

    def reset_for_new_session(self) -> None:
        """
        Reset session state for a new Claude CLI session.

        This is called when the previous Claude process dies
        and a new one starts. All in-memory state is cleared.

        Contract (JARVIS-DEC-002):
        - No recovery from previous session
        - Fresh start for each Claude CLI
        - Metrics not carried over
        """
        self.mode = "default"
        self.last_transcription = None
        self.input_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_input_time = None
        self.last_error_time = None
        self.last_error_message = None
        self.is_ready = True

    def increment_input_count(self) -> None:
        """
        MainLoop calls this after input processed.

        Contract: Only MainLoop calls this.
        """
        self.input_count += 1
        self.last_input_time = time.time()

    def record_error(self, error_message: str) -> None:
        """
        MainLoop calls this when error occurs.

        Contract: Only MainLoop calls this.
        """
        self.error_count += 1
        self.last_error_time = time.time()
        self.last_error_message = error_message

    def update_mode(self, new_mode: str) -> None:
        """
        MainLoop calls this when mode command succeeds.

        Contract: Only MainLoop calls this.
        Valid modes are: default, coding, debug, explain.
        """
        if new_mode not in ["default", "coding", "debug", "explain"]:
            raise ValueError(f"Invalid mode: {new_mode}")
        self.mode = new_mode

    def update_last_transcription(self, text: str) -> None:
        """
        MainLoop calls this after voice input sent to Claude.

        Contract: Only MainLoop calls this.
        Used for ulang (resend) command.
        """
        self.last_transcription = text

    @property
    def session_duration_seconds(self) -> float:
        """Get session duration in seconds."""
        return time.time() - self.start_time

    @property
    def is_error_state(self) -> bool:
        """Check if session is in error state."""
        return self.error_count > 0

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"SessionState(mode={self.mode}, "
            f"inputs={self.input_count}, "
            f"errors={self.error_count}, "
            f"duration={self.session_duration_seconds:.1f}s)"
        )
