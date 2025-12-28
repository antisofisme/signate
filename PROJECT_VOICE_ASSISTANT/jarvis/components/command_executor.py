"""
CommandExecutor - Execute classified commands deterministically

Architecture: JARVIS-L3-ARCH-001 (component decomposition)
Pattern: Explicit command dispatch (no magic, no dynamic dispatch)

No parsing. No interpretation. No inference.
Every command is explicitly listed, explicitly handled.
Unknown commands fail loudly.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of command execution."""
    success: bool
    message: str
    error: Optional[str] = None


class CommandExecutionError(Exception):
    """Command execution error (user-facing message)."""
    pass


class CommandExecutor:
    """
    Execute already-classified commands.

    Input: CommandInput from InputBoundary
    Output: ExecutionResult (success or explicit error)

    Every command is explicitly handled.
    Unknown commands raise CommandExecutionError.

    Valid commands (locked by JARVIS-DEC-003):
    - kirim: Send (press Enter)
    - ulang: Resend last transcription
    - mode {mode}: Change mode (default|coding|debug|explain)
    - help: Show help

    Pattern:
        executor = CommandExecutor()
        result = executor.execute(
            command_input=CommandInput(command="mode", args="coding"),
            session_state=state
        )
    """

    VALID_COMMANDS = {"kirim", "ulang", "mode", "help"}
    VALID_MODES = {"default", "coding", "debug", "explain"}

    def __init__(self):
        """Initialize executor (stateless)."""
        pass

    def execute(
        self, command_name: str, args: Optional[str], session_state
    ) -> ExecutionResult:
        """
        Execute command deterministically.

        Args:
            command_name: Command to execute (e.g., "mode")
            args: Optional arguments (e.g., "coding" for mode command)
            session_state: SessionState to potentially mutate

        Returns:
            ExecutionResult (success=True/False, message string)

        Raises:
            CommandExecutionError: If command unsupported or execution fails
        """
        command = command_name.lower().strip()

        if not command:
            raise CommandExecutionError("Empty command")

        if command == "kirim":
            return self._execute_kirim()

        elif command == "ulang":
            return self._execute_ulang(session_state)

        elif command == "mode":
            return self._execute_mode(args, session_state)

        elif command == "help":
            return self._execute_help()

        else:
            raise CommandExecutionError(
                f"Unknown command: {command}. "
                f"Valid commands: {', '.join(self.VALID_COMMANDS)}"
            )

    def _execute_kirim(self) -> ExecutionResult:
        """
        Execute kirim (send/press Enter).

        Sends transcribed text or command to Claude.
        """
        return ExecutionResult(
            success=True,
            message="Command accepted (send pending)"
        )

    def _execute_ulang(self, session_state) -> ExecutionResult:
        """
        Execute ulang (resend last transcription).

        Resends the last transcribed text.
        """
        if not session_state.last_transcription:
            raise CommandExecutionError(
                "No previous transcription to resend. "
                "Use voice input or 'kirim' first."
            )

        return ExecutionResult(
            success=True,
            message=f"Resending: {session_state.last_transcription}"
        )

    def _execute_mode(
        self, mode_arg: Optional[str], session_state
    ) -> ExecutionResult:
        """
        Execute mode (change interaction mode).

        Valid modes: default, coding, debug, explain
        """
        if not mode_arg:
            raise CommandExecutionError(
                "Mode command requires argument. "
                f"Usage: mode {{{','.join(self.VALID_MODES)}}}"
            )

        mode = mode_arg.lower().strip()

        if mode not in self.VALID_MODES:
            raise CommandExecutionError(
                f"Invalid mode: {mode}. "
                f"Valid modes: {', '.join(self.VALID_MODES)}"
            )

        session_state.update_mode(mode)

        return ExecutionResult(
            success=True,
            message=f"Mode changed to: {mode}"
        )

    def _execute_help(self) -> ExecutionResult:
        """Execute help (show available commands)."""
        help_text = (
            "Available commands:\n"
            "  kirim - Send text (press Enter)\n"
            "  ulang - Resend last transcription\n"
            "  mode - Change mode (default|coding|debug|explain)\n"
            "  help - Show this help message"
        )

        return ExecutionResult(
            success=True,
            message=help_text
        )

    def get_valid_commands(self) -> dict:
        """Get list of valid commands (read-only)."""
        return {
            "kirim": "Send text to Claude",
            "ulang": "Resend last transcription",
            "mode": "Change interaction mode",
            "help": "Show help",
        }
