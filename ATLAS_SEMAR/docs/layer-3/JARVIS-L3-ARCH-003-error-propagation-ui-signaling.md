# JARVIS-L3-ARCH-003: Error Propagation & UI Signaling

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 3 - Error Communication & User Feedback

---

## Purpose

Define **how Jarvis communicates failures, messages, and state** to the user **without inventing recovery logic**.

This is about **signal clarity**, not **smart recovery**. Users decide what to do with the signal.

Key principle: **No recovery happens unless user acts. Failure is explicit. User is always in control.**

---

## Core Principle: No Autonomy in Signaling

### What Jarvis Must NOT Do

```
❌ Auto-retry based on error type
❌ Choose recovery path for user
❌ Hide or minimize error
❌ Suggest "do this instead"
❌ Degrade functionality silently
❌ Save state to recover later
❌ Invoke callbacks or hooks
```

### What Jarvis MUST Do

```
✅ Display exact error message
✅ Show clear recovery action
✅ Return to ready state
✅ Wait for user action
✅ Make error self-evident
✅ Never assume success
```

---

## Signal Types: Three Categories

Jarvis can communicate via three channels:

### Signal Type 1: Toast (Non-blocking Message)

**Purpose**: Informational, success, or non-critical error

**Behavior**:
- Appears briefly (≤3-5 seconds)
- User can ignore and continue
- Doesn't require action
- Dismissible (click or auto-hide)

**Examples**:
```
✅ Command executed: "Mode: CODING"
ℹ️ "Sent to Claude"
⚠️ "Warning: long input (>10s). UX degraded."
```

**Forbidden Toast Content**:
- ❌ "Retrying..." (implies autonomy)
- ❌ "Hold on..." (vague time)
- ❌ "Processing..." (no end state)
- ❌ "Try again?" (decision required, use dialog)

**Technical**:
```python
class Toast:
    level: str  # "success", "info", "warning"
    message: str  # ≤100 characters
    duration_ms: int  # 3000-5000
    dismissible: bool  # True
    action: Optional[str]  # None (toast only signals, doesn't decide)
```

---

### Signal Type 2: Dialog (Blocking Confirmation)

**Purpose**: User must explicitly confirm or reject

**Behavior**:
- Blocks main loop until user responds
- Requires explicit Y/N or similar
- Cannot be ignored
- Modal (nothing else can happen)

**Examples**:
```
⚠️ DESTRUCTIVE OPERATION DETECTED

Pattern: rm -rf
Action requested: explain how to rm -rf safely

Continue? [Y] [N]
```

**Forbidden Dialog Content**:
- ❌ "Do you want to retry?" (retry is forbidden)
- ❌ "Should we try something else?" (Jarvis doesn't decide alternatives)
- ❌ Time-limited dismissal (user controls timing)

**Technical**:
```python
class ConfirmationDialog:
    title: str  # "DESTRUCTIVE OPERATION DETECTED"
    message: str  # Pattern detected + what user said
    buttons: List[str]  # ["Y", "N"] only
    timeout_ms: Optional[int]  # None (user decides timing)
    default_action: str  # "N" (default is conservative)
```

---

### Signal Type 3: Error Display (Context-Aware Message)

**Purpose**: User did something invalid; here's what went wrong

**Behavior**:
- Clear explanation (not error code)
- Shows valid alternatives (if applicable)
- Returned to ready state automatically
- Shown as toast or status message

**Examples**:
```
🔴 Unknown mode 'python'. Modes: default, coding, debug, explain

🔴 STT failed. Please try again or type instead.

🔴 Input too long (157 seconds). Max: 120s. Please split into multiple inputs.
```

**Forbidden Error Messages**:
- ❌ "ERROR_CODE_4021" (user-hostile)
- ❌ "Fatal exception" (misleading)
- ❌ "Check logs for details" (user shouldn't debug Jarvis)
- ❌ "Try again in 5 seconds" (no auto-recovery promises)

**Technical**:
```python
class ErrorDisplay:
    level: str  # "error" or "warning"
    message: str  # Clear, user-facing explanation
    recovery_hint: Optional[str]  # e.g., "type instead"
    show_as: str  # "toast" or "status_line"
```

---

## Error Flow: From Component to User

### Flow Diagram

```
Error occurs at component
    ↓
Component returns Result or raises Exception
    ↓
MainLoop catches and determines signal type
    ↓
MainLoop decides: Toast vs Dialog vs Error
    ↓
UINotifier.display(signal)
    ↓
User sees clear message
    ↓
User acts (retry, type, confirm, interrupt)
    ↓
MainLoop continues
```

### Example: STT Failure Flow

```
T0: STT starts
T1: Whisper timeout (no response after 1.5s)

T2: STTAdapter.transcribe() raises STTTimeoutError
    └─ Error contains: timeout_ms=1500, max_allowed=1000

T3: MainLoop catches:
    try:
        transcript = stt_adapter.transcribe(audio)
    except STTTimeoutError as e:
        # Determine signal type: Toast (informational)
        signal = Toast(
            level="warning",
            message="STT failed. Please try again or type instead.",
            duration_ms=5000
        )

T4: MainLoop calls:
    ui_notifier.display(signal)

T5: User sees toast for 5 seconds

T6: User chooses:
    A) [F12] again → new audio capture (retry)
    B) Type manually → continue without voice
```

---

## Error Categories & Signal Mapping

### Category 1: Input Boundary Errors

**Errors**:
- Audio not captured (hotkey released before audio)
- Empty input
- Input too long (>120s)
- Input encoding invalid

**Signal Type**: **ERROR_DISPLAY** (toast)

**Messages**:
```
"No input detected. Please speak or type."
"Input too long (157s). Max: 120s. Please split."
"Input contains invalid characters. Please retype."
```

**Recovery Action**: Implicit (user knows what to do)

---

### Category 2: STT Errors

**Errors**:
- STT timeout (>1s)
- STT crash
- Whisper not available
- STT confidence <0.5

**Signal Type**: **ERROR_DISPLAY** (toast)

**Messages**:
```
"STT failed. Please try again or type instead."
"STT timeout. Please try again."
"Audio quality too low. Please speak clearly."
```

**Recovery Action**: User retry audio OR type

---

### Category 3: Safety Gate Rejections

**Errors**:
- Dangerous pattern detected (rm -rf, DROP TABLE, git reset, etc.)

**Signal Type**: **DIALOG** (confirmation)

**Message**:
```
⚠️ DESTRUCTIVE OPERATION DETECTED

Pattern: rm -rf
You said: "explain how to rm -rf safely"

Continue? [Y] [N]
```

**Recovery Action**: User explicit Y/N choice

---

### Category 4: Command Execution Errors

**Errors**:
- Invalid command argument (mode="invalid_mode")
- Command not recognized
- Command validation failed

**Signal Type**: **ERROR_DISPLAY** (toast)

**Messages**:
```
"Unknown mode 'python'. Modes: default, coding, debug, explain"
"Unknown command 'xyz'. Type 'help' for available commands."
"Invalid argument. Expected format: mode <mode_name>"
```

**Recovery Action**: User reissue command OR continue

---

### Category 5: CLI Interaction Errors

**Errors**:
- Text insertion failed (xdotool error)
- Key press failed (keyboard simulation issue)
- Terminal not responding (but this is CLI's problem, not ours)

**Signal Type**: **ERROR_DISPLAY** (toast)

**Messages**:
```
"Failed to insert text. Please try again."
"Keyboard input failed. Please retry or type manually."
"(No message) - user will notice terminal didn't advance"
```

**Recovery Action**: User retry OR type manually

---

### Category 6: Jarvis Internal Errors

**Errors**:
- Hotkey listener crashed
- State corruption
- Unexpected exception

**Signal Type**: **ERROR_DISPLAY** (toast) then **crash gracefully**

**Messages**:
```
"Jarvis error. Hotkey disabled. Please restart."
"Internal error. Please restart Jarvis."
```

**Recovery Action**: Restart Jarvis

---

## Signal Design Rules

### Rule 1: Messages Are User-Focused

❌ **BAD** (technical):
```
"STTException: whisper_model.transcribe() timeout at 1000ms"
```

✅ **GOOD** (user-focused):
```
"STT failed. Please try again or type instead."
```

---

### Rule 2: Messages Include Path Forward

❌ **BAD** (no path):
```
"Error occurred."
```

✅ **GOOD** (path shown):
```
"Unknown mode 'python'. Modes: default, coding, debug, explain"
```

---

### Rule 3: No Autonomous Recovery Suggested

❌ **BAD** (implies retry):
```
"STT failed. Retrying..."
```

✅ **GOOD** (user decides):
```
"STT failed. Please try again or type instead."
```

---

### Rule 4: Dialogs Are Final Decisions Only

❌ **BAD** (dialog for info):
```
Dialog: "Hello! Processing your request."
```

✅ **GOOD** (dialog for safety):
```
Dialog: "DESTRUCTIVE OPERATION. Continue? [Y] [N]"
```

---

### Rule 5: Errors Are Not Degraded Silently

❌ **BAD** (silent degradation):
```
# User says "rm -rf /"
# Jarvis internally strips "rm -rf" and sends "/"
# User thinks they're safe
```

✅ **GOOD** (explicit rejection):
```
Dialog: "DESTRUCTIVE: rm -rf. Continue? [Y] [N]"
User: [Y] → sends full text
User: [N] → aborts
```

---

## UINotifier Component Responsibilities

The UINotifier is **the only component that displays signals**.

```python
class UINotifier:
    """
    Display signals to user.
    MUST NOT:
      ❌ Decide what to display (MainLoop decides)
      ❌ Interpret error types (MainLoop decides)
      ❌ Auto-retry or recover (signal only)
      ❌ Store history (no logging here)

    MUST:
      ✅ Display messages clearly
      ✅ Respect signal type (toast vs dialog)
      ✅ Block on dialog until user responds
      ✅ Return control immediately after display
    """

    def display(self, signal: Union[Toast, Dialog, ErrorDisplay]) -> Optional[bool]:
        """
        Display a signal to user.

        Args:
            signal: Toast, Dialog, or ErrorDisplay

        Returns:
            For Dialog: True (Y), False (N)
            For Toast/Error: None
        """
        if isinstance(signal, Toast):
            self._show_toast(signal)
            return None

        elif isinstance(signal, Dialog):
            return self._show_dialog(signal)  # Blocks until user responds

        elif isinstance(signal, ErrorDisplay):
            self._show_error(signal)
            return None
```

---

## MainLoop: Error Handling Pattern

### Template: How MainLoop Propagates Errors

```python
def main_loop():
    """Main orchestration with error handling."""

    while claude_cli_alive():
        try:
            # Wait for input
            hotkey_event.wait()
            hotkey_event.clear()

            # Capture audio
            try:
                audio = capture_audio()
            except AudioCaptureError as e:
                ui_notifier.display(ErrorDisplay(
                    level="error",
                    message="Failed to capture audio. Please try again.",
                    show_as="toast"
                ))
                continue  # Back to wait

            # Classify input
            try:
                input_event = classify_input(audio)
            except InputClassificationError as e:
                ui_notifier.display(ErrorDisplay(
                    level="error",
                    message="Could not understand input. Please try again.",
                    show_as="toast"
                ))
                continue

            # Handle rejected input
            if input_event == InputRejected:
                ui_notifier.display(ErrorDisplay(
                    level="error",
                    message=input_event.display,
                    show_as="toast"
                ))
                continue

            # Route based on type
            if input_event.type == "command":
                try:
                    result = command_executor.execute(input_event)

                    # Handle command result
                    if result.success:
                        ui_notifier.display(Toast(
                            level="success",
                            message=result.display,
                            duration_ms=3000
                        ))

                        # Update state
                        if result.mode_change:
                            session_state.mode = result.mode_change
                    else:
                        ui_notifier.display(ErrorDisplay(
                            level="error",
                            message=result.display,
                            show_as="toast"
                        ))

                except CommandExecutionError as e:
                    ui_notifier.display(ErrorDisplay(
                        level="error",
                        message="Command failed. Please try again.",
                        show_as="toast"
                    ))

            # Voice input path
            else:
                # Safety check
                if safety_gate.contains_danger(input_event.text):
                    response = ui_notifier.display(Dialog(
                        title="DESTRUCTIVE OPERATION DETECTED",
                        message=f"Pattern: {safety_gate.last_detected_pattern}\n\nContinue? [Y] [N]",
                        buttons=["Y", "N"]
                    ))

                    if not response:  # User pressed N
                        ui_notifier.display(Toast(
                            level="info",
                            message="Operation canceled.",
                            duration_ms=2000
                        ))
                        continue

                # Shape prompt
                try:
                    prompt = prompt_shaper.shape(
                        input_event.text,
                        mode=session_state.mode
                    )
                except PromptShapingError as e:
                    ui_notifier.display(ErrorDisplay(
                        level="error",
                        message="Failed to shape prompt. Please try again.",
                        show_as="toast"
                    ))
                    continue

                # Send to CLI
                try:
                    send_to_cli(prompt)

                    ui_notifier.display(Toast(
                        level="success",
                        message="Sent to Claude",
                        duration_ms=2000
                    ))

                    # Update state
                    session_state.last_transcription = input_event.text

                except CLIInteractionError as e:
                    ui_notifier.display(ErrorDisplay(
                        level="error",
                        message="Failed to send to Claude. Please try again.",
                        show_as="toast"
                    ))

        except Exception as e:
            # Unexpected error
            session_state.error_count += 1
            ui_notifier.display(ErrorDisplay(
                level="error",
                message="Unexpected error. Please restart Jarvis.",
                show_as="toast"
            ))
            # Optionally: exit loop
```

---

## Concrete Message Library

### Success Messages

```
✅ Command executed: "Mode: CODING"
✅ Sent to Claude
✅ Mode changed to: debug
```

### Warning Messages

```
⚠️ STT failed. Please try again or type instead.
⚠️ Input too long (157s). Max: 120s. Please split.
⚠️ Audio quality low. Please speak clearly.
⚠️ Unknown mode 'python'. Modes: default, coding, debug, explain
```

### Dialog Messages

```
⚠️ DESTRUCTIVE OPERATION DETECTED
Pattern: rm -rf
You said: "delete all files with rm -rf"

Continue? [Y] [N]

---

⚠️ DESTRUCTIVE OPERATION DETECTED
Pattern: DROP TABLE
You said: "explain how to DROP TABLE users"

Continue? [Y] [N]
```

### Error Messages

```
🔴 No input detected. Please speak or type.
🔴 Failed to capture audio. Please try again.
🔴 STT failed. Please try again or type instead.
🔴 Failed to insert text. Please try again.
🔴 Internal error. Please restart Jarvis.
```

---

## No Recovery Logic: What Jarvis NEVER Does

### Forbidden: Auto-Retry

```python
# ❌ WRONG
for attempt in range(3):
    try:
        transcript = stt_adapter.transcribe(audio)
        break
    except STTError:
        if attempt < 2:
            time.sleep(0.5)
            continue
        else:
            raise

# ✅ CORRECT
transcript = stt_adapter.transcribe(audio)  # No retry loop
if transcript is None:
    ui_notifier.display(Toast(message="STT failed. Try again."))
```

### Forbidden: Degraded Fallback

```python
# ❌ WRONG
try:
    transcript = stt_adapter.transcribe(audio)
except STTError:
    # Fallback: use last transcription
    transcript = session_state.last_transcription
    ui_notifier.display(Toast("Using previous input..."))

# ✅ CORRECT
transcript = stt_adapter.transcribe(audio)  # No fallback
if not transcript:
    ui_notifier.display(Toast("STT failed. Try again."))
```

### Forbidden: Silent Degradation

```python
# ❌ WRONG
try:
    send_to_cli(prompt)
except CLIError:
    # Silently continue
    pass  # User won't know if text was sent

# ✅ CORRECT
try:
    send_to_cli(prompt)
    ui_notifier.display(Toast("Sent to Claude"))
except CLIError as e:
    ui_notifier.display(Toast("Failed to send. Try again."))
```

### Forbidden: Invented Recovery

```python
# ❌ WRONG
if stt_failed:
    # "Smart" recovery: use keyboard input instead
    ui_notifier.display(Toast("Switching to keyboard..."))
    # User didn't ask for this, Jarvis decided

# ✅ CORRECT
if stt_failed:
    ui_notifier.display(Toast("STT failed. Try again or type instead."))
    # User decides what to do next
```

---

## Signal Consistency Rules

### Rule: Same Error = Same Message

```python
# If STT fails, message is ALWAYS:
ERROR_MESSAGE = "STT failed. Please try again or type instead."

# Not:
# "STT error", "Transcription failed", "Audio processing error"
# All the same underlying issue get the same message for consistency
```

### Rule: Message Tone is Neutral (Not Apologetic)

```
✅ "STT failed. Please try again."     (neutral, factual)
✅ "Unknown mode. Modes: ..."           (factual, helpful)

❌ "Sorry, STT failed..."                (apologetic, fake)
❌ "Unfortunately, we couldn't..."      (verbose, formal)
```

### Rule: Duration Matches Message Type

| Signal Type | Duration | Reason |
|-------------|----------|--------|
| Success (modal) | 2-3s | Quick confirmation |
| Info | 3-5s | User can read |
| Warning (non-critical) | 5s | User should notice |
| Error (action needed) | Until user acts | User must respond |
| Dialog | Until user acts | Modal, no timeout |

---

## Testing Error Signals

### Test 1: STT Error Produces Correct Signal

```python
def test_stt_error_produces_toast():
    """Verify: STT failure → Error toast displayed."""

    mock_stt = MockSTT(raises=STTTimeoutError())
    ui_notifier = MockUINotifier()

    try:
        transcript = mock_stt.transcribe(audio)
    except STTTimeoutError:
        ui_notifier.display(ErrorDisplay(
            level="error",
            message="STT failed. Please try again or type instead."
        ))

    assert ui_notifier.last_display.level == "error"
    assert "STT failed" in ui_notifier.last_display.message
```

### Test 2: Safety Dialog Requires Explicit Response

```python
def test_safety_dialog_requires_user_action():
    """Verify: Safety gate shows dialog, blocks until response."""

    safety = SafetyGate()
    ui_notifier = MockUINotifier(user_response=False)

    if safety.contains_danger("rm -rf /"):
        response = ui_notifier.display(Dialog(
            title="DESTRUCTIVE OPERATION",
            message="Pattern: rm -rf\nContinue? [Y] [N]"
        ))

        assert response == False  # User said N
        # Execution stops here, no prompt shaping
```

### Test 3: Error Messages Are Consistent

```python
def test_error_message_consistency():
    """Verify: Same error type → same message every time."""

    messages = []
    for i in range(5):
        try:
            stt_adapter.transcribe(audio)  # Fails
        except STTTimeoutError:
            messages.append("STT failed. Please try again or type instead.")

    # All messages identical
    assert all(msg == messages[0] for msg in messages)
```

---

## Summary: UINotifier as Pure Display

| Aspect | Rule |
|--------|------|
| Decision-making | ❌ UINotifier doesn't decide what to display |
| Recovery logic | ❌ No retry, fallback, or recovery |
| State mutation | ❌ Doesn't change SessionState or signal state |
| Autonomy | ❌ Doesn't initiate action; only responds to MainLoop |
| History | ❌ Doesn't log; doesn't persist |
| Behavior | ✅ Displays signal based on type |
| Blocking | ✅ Dialog blocks until user responds |
| Control | ✅ Returns control to MainLoop immediately |

---

## Layer 3 Complete: From Architecture to User

This final component completes the architecture:

1. **L3-ARCH-001** (Component Decomposition): *What* each part does
2. **L3-ARCH-002** (Threading & Concurrency): *How* parts coordinate safely
3. **L3-ARCH-003** (Error Propagation & UI): *What user sees* and *how they interact*

Together: **Jarvis core is complete and defensible**.

---

## Next Phase: Reference Implementation

With Layers 0-3 complete, implementation can begin with confidence:

* Code structure follows component decomposition
* Threading enforces single-writer model
* Error handling follows explicit signal rules
* UX is consistent and predictable
* Contracts are unbreakable

Implementation becomes: *wiring components according to design, not inventing design during coding*.

---

**Ready for implementation review.**

