"""
CLIAdapter - Send text to Claude CLI

Architecture: JARVIS-L1-DEC-004 (CLI Interaction Contract)
Pattern: Fire-and-forget text insertion (no reading, no monitoring)

Never reads output. Never waits. Never retries.
Insert text, press Enter, return immediately.
"""

import sys
import time


class CLIAdapterError(Exception):
    """CLI adapter error (user-facing message)."""
    pass


class CLIAdapter:
    """
    Send shaped prompt to Claude CLI via stdout.

    Input: Shaped prompt text
    Output: None (fire-and-forget)

    Contract (JARVIS-L1-DEC-004):
    - FIRE-AND-FORGET: Insert text, press Enter, done
    - NO READING: Never read terminal output
    - NO PARSING: Never interpret Claude's response
    - NO MONITORING: Never check if Claude is responding
    - NO COUPLING: No process handles, complete severing after Enter
    - IMMEDIATE RETURN: Control back to MainLoop instantly

    Implementation:
    - Write shaped prompt to stdout
    - Flush to ensure delivery
    - ENTER implicit (newline sent)
    - Return immediately
    - (Works with piped input to Claude CLI)

    Pattern:
        adapter = CLIAdapter()
        adapter.send(prompt="[CODING] write a function")
        # Text sent, Jarvis returns to ready state
        # Claude CLI reads from stdin and responds independently
    """

    def __init__(self):
        """Initialize adapter (stateless, fire-and-forget)."""
        pass

    def send(self, prompt: str) -> None:
        """
        Send shaped prompt to Claude CLI.

        Contract (JARVIS-L1-DEC-004):
        - FIRE-AND-FORGET: Insert text and press Enter
        - SYNCHRONOUS: Returns after text is sent
        - NON-BLOCKING: Doesn't wait for Claude
        - IMMEDIATE RETURN: No hooks, no callbacks, no lingering state

        Args:
            prompt: Shaped prompt text (from PromptShaper)

        Raises:
            CLIAdapterError: If sending fails (shouldn't happen)
        """
        if not prompt:
            raise CLIAdapterError("Cannot send empty prompt")

        try:
            # Write to stdout (which can be piped to Claude CLI)
            print(prompt, flush=True)
            sys.stdout.flush()
            # ENTER is implicit (print adds newline)
        except (IOError, OSError) as e:
            raise CLIAdapterError(f"Failed to send prompt: {e}")

    def send_key(self, key: str) -> None:
        """
        Send keyboard key press (fire-and-forget).

        Contract (JARVIS-L1-DEC-004):
        - Used for commands like "kirim" (press Enter only)
        - Synchronous, immediate return
        - No waiting for Claude

        Args:
            key: Key name (e.g., "Return", "Enter")

        Raises:
            CLIAdapterError: If key press fails
        """
        if key.lower() not in ["return", "enter"]:
            raise CLIAdapterError(
                f"Only Return/Enter supported, got: {key}"
            )

        try:
            # For stdin piping, Enter is sent as newline
            print(flush=True)
            sys.stdout.flush()
        except (IOError, OSError) as e:
            raise CLIAdapterError(f"Failed to send key: {e}")
