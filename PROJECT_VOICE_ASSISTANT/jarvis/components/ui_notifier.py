"""
UINotifier - Display signals to user

Architecture: JARVIS-L3-ARCH-003 (Error Propagation & UI Signaling)
Pattern: Signal-based display (toast, dialog, error)

Display-only. Never decides. Never retries. Never recovers.
MainLoop decides what to display, UINotifier displays it.
"""

import sys
from dataclasses import dataclass
from typing import Optional, Union


class UINotifierError(Exception):
    """UI notifier error."""
    pass


@dataclass
class Toast:
    """Non-blocking notification message (auto-dismiss)."""
    level: str  # "success", "info", "warning"
    message: str  # ≤100 characters
    duration_ms: int = 3000  # milliseconds to show


@dataclass
class Dialog:
    """Blocking confirmation dialog (requires Y/N response)."""
    title: str  # e.g., "DESTRUCTIVE OPERATION DETECTED"
    message: str  # Explanation
    buttons: list = None  # Default: ["Y", "N"]

    def __post_init__(self):
        if self.buttons is None:
            self.buttons = ["Y", "N"]


@dataclass
class ErrorDisplay:
    """Error message with optional recovery hint."""
    level: str  # "error" or "warning"
    message: str  # Clear, user-facing explanation
    recovery_hint: Optional[str] = None  # e.g., "try again or type instead"
    show_as: str = "toast"  # "toast" or "status"


class UINotifier:
    """
    Display signals to user (toast, dialog, error messages).

    Input: Signal (Toast, Dialog, or ErrorDisplay)
    Output: Display + user response (for dialogs)

    Contract (JARVIS-L3-ARCH-003):
    - DISPLAY-ONLY: Never decides what to display (MainLoop decides)
    - NO AUTONOMY: Never invents recovery or retry
    - SIGNAL-BASED: Only shows what MainLoop tells it
    - BLOCKING ON DIALOG: Dialog blocks until user responds
    - IMMEDIATE RETURN: Toast/Error returns immediately

    What UINotifier MUST NOT do:
    - ❌ Decide what error message to show
    - ❌ Auto-retry on error
    - ❌ Suggest recovery path
    - ❌ Auto-approve/reject dialog
    - ❌ Store history
    - ❌ Log (separate concern)

    What UINotifier MUST do:
    - ✅ Display message clearly
    - ✅ Respect signal type (toast vs dialog)
    - ✅ Block on dialog until user responds
    - ✅ Return control immediately after display

    Pattern:
        notifier = UINotifier()
        notifier.display(Toast(level="success", message="Sent to Claude"))
        # Toast shown briefly, returns immediately

        response = notifier.display(Dialog(title="...", message="..."))
        # Dialog blocks until user presses Y or N
        # Returns True (Y) or False (N)
    """

    def __init__(self):
        """Initialize notifier (stateless, display-only)."""
        pass

    def display(
        self, signal: Union[Toast, Dialog, ErrorDisplay]
    ) -> Optional[bool]:
        """
        Display a signal to user.

        Contract (JARVIS-L3-ARCH-003):
        - Toast: Shows briefly, returns None
        - Dialog: Blocks until user responds, returns True (Y) or False (N)
        - ErrorDisplay: Shows error, returns None

        Args:
            signal: Signal to display (Toast, Dialog, or ErrorDisplay)

        Returns:
            For Dialog: True (user pressed Y), False (user pressed N)
            For Toast/ErrorDisplay: None (non-blocking)

        Raises:
            UINotifierError: Only if display fails
        """
        if isinstance(signal, Toast):
            self._show_toast(signal)
            return None

        elif isinstance(signal, Dialog):
            return self._show_dialog(signal)

        elif isinstance(signal, ErrorDisplay):
            self._show_error(signal)
            return None

        else:
            raise UINotifierError(f"Unknown signal type: {type(signal)}")

    def _show_toast(self, toast: Toast) -> None:
        """
        Show toast message (non-blocking).

        - Display message to stderr (minimal)
        - No actual timeout (for CLI)
        - Return immediately

        Args:
            toast: Toast signal
        """
        try:
            print(f"[{toast.level.upper()}] {toast.message}", file=sys.stderr, flush=True)
        except (IOError, OSError) as e:
            raise UINotifierError(f"Failed to show toast: {e}")

    def _show_dialog(self, dialog: Dialog) -> bool:
        """
        Show confirmation dialog (blocking).

        - Display dialog with title and message
        - Prompt user for Y/N response
        - Block until user responds
        - Return True (Y) or False (N)

        Args:
            dialog: Dialog signal

        Returns:
            True if user pressed Y/y/yes, False if pressed N/n/no
        """
        try:
            # Display dialog
            print(f"\n⚠️  {dialog.title}", file=sys.stderr, flush=True)
            print(f"\n{dialog.message}", file=sys.stderr, flush=True)
            print(f"\nOptions: {' / '.join(dialog.buttons)}", file=sys.stderr, flush=True)

            # Prompt and wait for response
            while True:
                response = input("\nYour choice: ").strip().lower()
                if response in ["y", "yes"]:
                    return True
                elif response in ["n", "no"]:
                    return False
                else:
                    print(f"Invalid choice '{response}'. Please type Y or N.", file=sys.stderr, flush=True)

        except (EOFError, KeyboardInterrupt):
            # User interrupted, treat as rejection
            return False
        except Exception as e:
            raise UINotifierError(f"Failed to show dialog: {e}")

    def _show_error(self, error: ErrorDisplay) -> None:
        """
        Show error message.

        - Display error message to stderr
        - Include recovery hint if provided
        - Return immediately

        Args:
            error: ErrorDisplay signal
        """
        try:
            symbol = "🔴" if error.level == "error" else "⚠️"
            msg = f"{symbol} {error.message}"

            if error.recovery_hint:
                msg += f" ({error.recovery_hint})"

            print(msg, file=sys.stderr, flush=True)

        except (IOError, OSError) as e:
            raise UINotifierError(f"Failed to show error: {e}")
