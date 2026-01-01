# ADR-001: Hotkey Library Selection

**Status**: PROPOSED

**Date**: 2025-12-28

**Affects**: HotkeyListener (Week 1, critical path)

---

## Problem Statement

HotkeyListener must detect hotkey press/release and signal MainLoop non-blockingly.

**Context**:
- JARVIS-L3-ARCH-002 requires signal-only thread (no logic, no blocking)
- HotkeyListener runs in separate thread
- Must not block on hotkey detection
- Must work cross-platform (Windows, macOS, Linux)

**Why this matters**:
- Hotkey detection is the input enabler for entire voice pipeline
- Wrong library choice could violate "non-blocking" contract

---

## Options Considered

### Option A: pynput (PROPOSED)

**Pros**:
- Pure Python, no C extensions needed
- Cross-platform (Windows, macOS, Linux)
- Non-blocking listener API
- Simple: `GlobalHotKeys()` handles OS-level hooks
- Active maintenance

**Cons**:
- Depends on OS-specific hooks (macOS requires accessibility permissions)
- Library behavior varies by platform
- No built-in debounce (user must handle)

**Compliance with JARVIS contracts**:
- ✅ JARVIS-L3-ARCH-002: Non-blocking listener
- ✅ Signal-only design: no logic in callback
- ✅ Cross-platform: Windows/macOS/Linux supported

---

### Option B: keyboard (Alternative Considered)

**Why rejected**:
- More low-level, less abstraction
- Higher platform-specific complexity
- Steeper learning curve
- No significant advantage over pynput for this use case

---

### Option C: OS-level APIs (pynput under the hood)

**Why rejected**:
- Would require platform-specific code (xdotool for Linux, AppKit for macOS, Win32 for Windows)
- Massive complexity increase
- Maintenance burden across platforms
- pynput already wraps these; no point redoing

---

## Decision

**We will use pynput for HotkeyListener.**

**Rationale**:
- Meets all non-blocking requirements
- Cross-platform with minimal branching
- Proven in production voice applications
- Simple API fits signal-only design pattern

---

## Constraints & Requirements

**From JARVIS-L3-ARCH-002**:
- HotkeyListener must NOT access SessionState (✅ pynput doesn't require state)
- HotkeyListener must signal via threading.Event (✅ pynput callback can call event.set())
- No blocking (✅ pynput listener runs in background thread by default)

**Implementation must ensure**:
- [ ] Callback is single line: `event.set()`
- [ ] No debounce logic in listener (MainLoop decides if needed)
- [ ] Hotkey configurable (default F12)
- [ ] Cross-platform tested (Windows, macOS, Linux)

---

## Implementation Notes

**Where**: `jarvis/components/hotkey_listener.py`

**Pattern**:
```python
from pynput import keyboard

class HotkeyListener(threading.Thread):
    def __init__(self, hotkey_key="f12", signal_event=None):
        self.hotkey_key = hotkey_key
        self.signal_event = signal_event or threading.Event()

    def run(self):
        with keyboard.GlobalHotKeys({
            self.hotkey_key: self._on_hotkey
        }) as listener:
            listener.join()

    def _on_hotkey(self):
        """SINGLE LINE: Signal MainLoop"""
        self.signal_event.set()
```

**Testing**:
- [ ] Listener detects hotkey press
- [ ] Event is set reliably
- [ ] No blocking on main thread
- [ ] Cross-platform hotkey binding

---

## Related

- **JARVIS-L3-ARCH-002**: Threading & Concurrency (signal-only requirement)
- **JARVIS-L3-ARCH-001**: Component Decomposition (HotkeyListener spec)

---

## Compliance Verification

- [ ] Reviewed against JARVIS-L3-ARCH-002 (signal-only contract)
- [ ] Does NOT violate any Layer 0-3 contract
- [ ] Callback is genuinely non-blocking
- [ ] Code review will verify single-line callback

---

## Revision History

| Date | Status | Notes |
|------|--------|-------|
| 2025-12-28 | PROPOSED | Initial proposal for Week 1 |
