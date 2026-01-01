"""
HotkeyListener - Signal-only hotkey detection thread

Architecture: JARVIS-L3-ARCH-002 (signal-only thread)
Library: pynput (ADR-001)

No state access. No blocking. No debounce. No logging.
Callbacks are single line: event.set() or event.clear()

Pattern:
- Hotkey press → event.set() (start audio capture)
- Hotkey release → event.clear() (stop audio capture)
"""

import threading
from pynput import keyboard


class HotkeyListener(threading.Thread):
    """
    Detect hotkey press/release in separate thread.

    Signals MainLoop via threading.Event:
    - Press: event.set() (MainLoop starts audio capture)
    - Release: event.clear() (MainLoop stops audio capture)

    Does NOT access SessionState or any shared state.
    Does NOT log or debounce.

    Pattern:
        listener = HotkeyListener(hotkey_key="f12", signal_event=hotkey_event)
        listener.daemon = False
        listener.start()

        # MainLoop waits for press
        hotkey_event.wait()
        # Now hotkey is pressed, start capture
        capture(hotkey_event)  # Blocks until release
        # hotkey_event.is_set() becomes False on release
    """

    def __init__(self, hotkey_key: str = "f12", signal_event: threading.Event = None):
        """
        Args:
            hotkey_key: Key to detect (e.g., "f12")
            signal_event: threading.Event to signal press/release
        """
        super().__init__()
        self.hotkey_key = hotkey_key.lower()
        self.signal_event = signal_event or threading.Event()
        self._listener = None

    def run(self):
        """
        Listen for hotkey press/release in background thread.
        Blocks indefinitely until listener is stopped.
        """
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._listener.start()
        self._listener.join()

    def _on_key_press(self, key):
        """Detect hotkey press. Single line only."""
        if self._key_matches(key):
            self.signal_event.set()

    def _on_key_release(self, key):
        """Detect hotkey release. Single line only."""
        if self._key_matches(key):
            self.signal_event.clear()

    def _key_matches(self, key) -> bool:
        """Check if key matches configured hotkey."""
        try:
            if hasattr(key, "name") and key.name == self.hotkey_key:
                return True
            if hasattr(key, "char") and key.char and key.char.lower() == self.hotkey_key:
                return True
        except AttributeError:
            pass
        return False
