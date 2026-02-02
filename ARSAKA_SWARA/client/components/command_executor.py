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

    ENFORCEMENT: Only 'help' command remains.
    All state-modifying commands (kirim, ulang, mode) removed.

    Rationale (Compliance Locked):
    - kirim (send): Implicit - user text goes to Claude automatically
    - ulang (repeat): Requires memory - FORBIDDEN (amnesic design)
    - mode (change): Silent context injection - FORBIDDEN (Jarvis is transparent)
    - help: Static, stateless, allowed

    Pattern:
        executor = CommandExecutor()
        result = executor.execute(
            command_input=CommandInput(command="help", args=None),
            session_state=state
        )
    """

    VALID_COMMANDS = {"help"}

    def __init__(self):
        """Initialize executor (stateless)."""
        pass

    def execute(
        self, command_name: str, args: Optional[str], session_state
    ) -> ExecutionResult:
        """
        Execute command deterministically.

        Args:
            command_name: Command to execute ("help" only)
            args: Ignored
            session_state: Ignored

        Returns:
            ExecutionResult (success=True/False, message string)

        Raises:
            CommandExecutionError: If command unsupported
        """
        command = command_name.lower().strip()

        if not command:
            raise CommandExecutionError("Empty command")

        if command == "help":
            return self._execute_help()
        else:
            raise CommandExecutionError(
                f"Unknown command: {command}. Valid command: help"
            )

    def _execute_help(self) -> ExecutionResult:
        """Execute help (show available commands)."""
        help_text = (
            "JARVIS - Voice Input for Claude CLI\n\n"
            "Available command:\n"
            "  help - Show this help message\n\n"
            "Usage:\n"
            "  1. Press and hold F12\n"
            "  2. Speak your text or command\n"
            "  3. Release F12\n"
            "  4. Text appears in Claude CLI\n"
            "  5. Claude responds normally\n\n"
            "JARVIS is plumbing, not a brain.\n"
            "All processing happens in Claude."
        )

        return ExecutionResult(
            success=True,
            message=help_text
        )

    def get_valid_commands(self) -> dict:
        """Get list of valid commands (read-only)."""
        return {
            "help": "Show help message",
        }
