# JARVIS-L1-DEC-004: CLI Interaction Contract

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 1 - Contracts & Boundaries

---

## Purpose

Define **the only way Jarvis touches Claude CLI** and **what it absolutely must NOT do**.

This is the final boundary before external system (Claude CLI). It's also where the most dangerous "cleverness" appears: monitoring, parsing, retrying, adapting based on output.

Key principle: **Jarvis is input only. Jarvis never reads output. Jarvis never monitors Claude.**

---

## Core Contract: Fire-and-Forget

### The Interaction Model

```
Jarvis
  ↓
Wrapped text (from prompt shaper) or Command result
  ↓
┌──────────────────────────────┐
│ CLI INTERACTION              │
│                              │
│ 1. Insert text in terminal   │
│ 2. Press Enter               │
│ 3. Return control to Claude  │
│ 4. STOP (don't look back)    │
└──────────────────────────────┘
  ↓
Claude CLI (responds in terminal)
  ↓
Jarvis does NOT:
  ❌ Read output
  ❌ Parse response
  ❌ Monitor progress
  ❌ Retry on error
  ❌ Track state
```

**That's the contract. Anything else violates it.**

---

## Interaction Types

### Type 1: Send Voice Input (WrappedPrompt)

**Contract**:
```python
class CLIInteraction:
    action: str         # "send_text" or "press_key"
    content: str        # Text to insert (if send_text)
    key: str            # Key name (if press_key)

class CLISendText(CLIInteraction):
    action = "send_text"
    content: str        # WrappedPrompt.wrapped_text
    # Example: "[CODING] build a sorting function"

# Process:
# 1. Insert content into terminal (character by character, simulating typing)
# 2. Wait for insertion to complete
# 3. Press Enter key
# 4. DONE — do not monitor output
```

**What happens**:
```
Terminal before:
  $ claude input>

Terminal after:
  $ claude input> [CODING] build a sorting function
  [cursor here, awaiting Enter]

Jarvis presses Enter:
  $ claude input> [CODING] build a sorting function
  [Claude CLI processes and responds]

Jarvis: ✓ DONE, return to ready state
```

---

### Type 2: Send Command Result (kirim / ulang)

**Contract**:
```python
class CLIPressKey(CLIInteraction):
    action = "press_key"
    key: str            # "Return" or "Enter"

# Process:
# 1. Press the key
# 2. Wait for key press to complete
# 3. DONE — do not monitor

# Example:
# - kirim command → press Enter (sends pending text)
# - ulang command → send last text + press Enter
```

**What happens**:
```
Terminal before (text pending):
  $ claude input> [CODING] build a function

Jarvis executes "kirim":
  1. Press Enter

Terminal after:
  $ claude input> [CODING] build a function
  [Claude CLI processes and responds]

Jarvis: ✓ DONE
```

---

## What This Contract ALLOWS

### ✅ ALLOWED: Text Insertion

```
Insert wrapped prompt into terminal:
  "[CODING] explain what this function does"
```

### ✅ ALLOWED: Key Press

```
Press Enter to confirm text:
  press_key("Return")
```

### ✅ ALLOWED: Timing

```
Wait for insertion to complete before pressing key
  insert_text(content)
  sleep(100ms)  # let terminal catch up
  press_key("Return")
```

### ✅ ALLOWED: Immediate Return

```
Return control immediately (no lingering process ties)
  insert_text(content)
  press_key("Return")
  return_immediately()

"Return control" means:
  - No handle to Claude CLI process kept
  - No callback registered
  - No watcher or timeout tied to CLI
  - No background thread monitoring CLI
  - Complete severing after Enter is pressed
```

### ✅ ALLOWED: Error Handling at Boundary

```
Handle local errors (text too long, encoding issue):
  if len(text) > MAX_LENGTH:
    display_error("Text too long")
    return
```

### ✅ ALLOWED: Logging

```
Log interaction for debugging:
  log: "sent text: {text}"
  log: "pressed: Return"
```

---

## What This Contract FORBIDS (CRITICAL)

### ❌ FORBIDDEN: Reading Terminal Output

```
WRONG:
  output = read_terminal()
  if "error" in output:
    retry_send()

CORRECT:
  insert_text(content)
  press_key("Return")
  (Claude CLI owns terminal, not Jarvis)
```

**Rationale**: Jarvis never reads. Claude CLI is autonomous system.

---

### ❌ FORBIDDEN: Parsing Claude's Response

```
WRONG:
  response = capture_output()
  if "I can't help" in response:
    send_follow_up("please try again")

CORRECT:
  insert_text(content)
  press_key("Return")
  (Claude will respond, user reads it)
```

**Rationale**: Claude's reasoning is sovereign. Jarvis doesn't interpret it.

---

### ❌ FORBIDDEN: Automatic Retry

```
WRONG:
  send_text(content)
  if no_response_received():
    retry_send()
  if error_detected():
    send_correction()

CORRECT:
  send_text(content)
  press_key("Return")
  (If something goes wrong, user handles it)
```

**Rationale**: Automatic retry is hidden decision-making. Violates transparency.

---

### ❌ FORBIDDEN: Monitoring Claude's Behavior

```
WRONG:
  send_text(content)
  monitor_output_for(5 seconds)
  if no_response:
    trigger_fallback()

CORRECT:
  send_text(content)
  press_key("Return")
  (Return control immediately)
```

**Rationale**: Claude's execution time is Claude's concern, not Jarvis'.

---

### ❌ FORBIDDEN: State Tracking Based on Output

```
WRONG:
  send_text(content)
  response = read_output()
  session.last_context = parse_response(response)
  if sentiment(response) == "confused":
    session.clarify_needed = True

CORRECT:
  send_text(content)
  press_key("Return")
  (Session state is user's responsibility)
```

**Rationale**: Jarvis doesn't track conversation state. Claude owns memory.

---

### ❌ FORBIDDEN: Modifying Text Based on Terminal State

```
WRONG:
  if terminal_is_empty():
    send_prompt("hello, are you there?")
  else:
    send_prompt(original_text)

CORRECT:
  send_text(content)
  press_key("Return")
  (Text is fixed from prompt shaper, terminal state irrelevant)
```

**Rationale**: Input is predetermined. Terminal state doesn't change it.

---

### ❌ FORBIDDEN: Waiting for Claude to Complete

```
WRONG:
  send_text(content)
  press_key("Return")
  wait_for_response(timeout=30s)
  if timeout:
    alert_user()

CORRECT:
  send_text(content)
  press_key("Return")
  return_immediately()
  (Claude takes as long as it needs)
```

**Rationale**: Jarvis is input-only, doesn't own Claude's lifecycle.

---

## Allowed & Forbidden Summary

### ✅ DO

- Insert text into terminal
- Press Enter/Return
- Wait for insertion to complete (briefly)
- Handle local input errors
- Log interactions
- Return control immediately

### ❌ DON'T

- Read terminal output
- Parse Claude's response
- Monitor Claude's behavior
- Auto-retry on perceived error
- Track conversation state from output
- Modify input based on terminal state
- Wait for Claude to finish
- Make decisions based on output
- Adapt behavior based on Claude's response

---

## Five Concrete Scenarios

### Scenario 1: Normal Voice Input - PASS

```
Input:
  WrappedPrompt(
    wrapped_text="[CODING] build a function"
  )

Execution:
  T0: Insert text: "[CODING] build a function"
  T1: Wait 100ms (insertion complete)
  T2: Press Enter key
  T3: Log: "sent text, pressed enter"
  T4: Return to ready state
  T5: Claude CLI receives input and responds (Jarvis doesn't care)

Result: ✅ PASS
        Fire-and-forget complete
        Jarvis control returns immediately
```

---

### Scenario 2: Command Execution (kirim) - PASS

```
Input:
  CLIPressKey(key="Return")
  (from kirim command)

Execution:
  T0: Press Return key
  T1: Wait 50ms (key press complete)
  T2: Log: "pressed return"
  T3: Return to ready state
  T4: Claude CLI executes pending text (Jarvis not monitoring)

Result: ✅ PASS
        Command executed, control returned
        No monitoring
```

---

### Scenario 3: Parsing Output Temptation - FORBIDDEN

```
Input:
  WrappedPrompt(wrapped_text="what's 2+2")

WRONG APPROACH:
  T0: Insert text
  T1: Press Enter
  T2: Read output from terminal
  T3: If "4" in output: mark as solved
  T4: If error detected: send clarification

WHY FORBIDDEN:
  - Jarvis is reading terminal (violation #1)
  - Jarvis is parsing Claude output (violation #2)
  - Jarvis is adapting based on response (violation #3)
  - This is hidden monitoring and decision-making

CORRECT APPROACH:
  T0: Insert text: "what's 2+2"
  T1: Press Enter
  T2: Return control
  T3: Claude responds
  T4: User reads response and decides next action
  (Jarvis completely uninvolved)

Result: ❌ FAIL (if done wrong)
        ✅ PASS (if kept simple)
```

---

### Scenario 4: Automatic Retry Temptation - FORBIDDEN

```
Input:
  WrappedPrompt(wrapped_text="build something complex")

WRONG APPROACH:
  T0: Insert text
  T1: Press Enter
  T2: Wait 5 seconds
  T3: Check if response received
  T4: If no response: send reminder prompt
  T5: If error detected: send apology + clarification

WHY FORBIDDEN:
  - Jarvis is monitoring (violation #1)
  - Jarvis is waiting (violation #2)
  - Jarvis is auto-retrying (violation #3)
  - This assumes Jarvis knows what "correct" response is

CORRECT APPROACH:
  T0: Insert text
  T1: Press Enter
  T2: Return immediately
  T3: Claude thinks as long as needed
  T4: User monitors progress themselves

Result: ❌ FAIL (if done wrong)
        ✅ PASS (if kept simple)
```

---

### Scenario 5: State Tracking from Output - FORBIDDEN

```
Input:
  WrappedPrompt(wrapped_text="explain recursion")

WRONG APPROACH:
  T0: Insert text
  T1: Press Enter
  T2: Capture output: "Recursion is... [long response]"
  T3: Parse sentiment: confident_tone = True
  T4: Update session: session.last_tone = "confident"
  T5: Next prompt uses session.last_tone for context

WHY FORBIDDEN:
  - Jarvis is reading output (violation #1)
  - Jarvis is parsing response (violation #2)
  - Jarvis is tracking conversation state (violation #3)
  - This assumes Claude is stateless (it's not, it has memory)

CORRECT APPROACH:
  T0: Insert text
  T1: Press Enter
  T2: Return immediately
  T3: Claude has its own memory of conversation
  T4: Next input from user, sent as-is to Claude
  (Jarvis doesn't track state)

Result: ❌ FAIL (if done wrong)
        ✅ PASS (if kept simple)
```

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- Text insertion into terminal
- Key press (Enter) to confirm
- Immediate return of control
- No reading terminal output
- No parsing Claude response
- No automatic retry logic
- No behavior monitoring
- Fire-and-forget model

❌ **MUST NOT HAVE**:
- Output reading
- Response parsing
- Auto-retry on any condition
- Monitoring Claude's execution
- State tracking from output
- Input modification based on terminal state
- Waiting for Claude completion
- Decision-making based on response

---

## The Philosophy: Jarvis is Input Only

Jarvis's entire job:

```
1. Capture voice input
2. Classify (command vs voice)
3. Shape prompt (if voice)
4. Insert text into terminal
5. Press Enter
6. DONE

Claude CLI's job:

1. Read input from terminal
2. Process and reason
3. Write response to terminal
4. Wait for next input

Boundary between them:

[ Jarvis ] ←——— text insertion + Enter ———→ [ Claude CLI ]

No feedback. No monitoring. No reading back.
```

---

## Relationship to Other Layers

**Layer 1 (L1-DEC-001, 002, 003)**:
- Input boundary produces WrappedPrompt or CommandResult
- This contract receives that and sends to CLI
- This is the last stop before Claude

**Layer 2+ (will define)**:
- User interaction loop (hotkey, text display)
- Error handling (local only)
- Session lifecycle

---

## Contract Violations (Examples of What NOT to Do)

### ❌ VIOLATION #1: Reading Output

```
WRONG:
  send_to_cli(text)
  output = cli.read_output()
  if error in output: retry()

CORRECT:
  send_to_cli(text)
  # Done, don't read back
```

### ❌ VIOLATION #2: Auto-Retry

```
WRONG:
  for attempt in 1..3:
    send_to_cli(text)
    if response_received():
      break

CORRECT:
  send_to_cli(text)
  # Let Claude respond in its own time
```

### ❌ VIOLATION #3: Monitoring

```
WRONG:
  send_to_cli(text)
  wait_for(response, timeout=5s)
  if timeout: fallback()

CORRECT:
  send_to_cli(text)
  # Return immediately
```

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Model | Fire-and-forget | Simple, no coupling |
| Text insertion | Allowed | Only way to send input |
| Key press | Allowed | Only way to confirm |
| Output reading | Forbidden | Violates isolation |
| Monitoring | Forbidden | Violates autonomy |
| State tracking | Forbidden | Claude owns state |
| Auto-retry | Forbidden | Hidden decision-making |

---

**Next**: JARVIS-L1-DEC-005 (Failure & Degradation Contract)

