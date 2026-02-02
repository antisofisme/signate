# COMPLIANCE LOCKED - JARVIS Architecture Enforcement

**Date**: 2025-12-29
**Status**: ✅ LOCKED
**Authority**: Post-Review Enforcement (User Confirmed)

---

## PREAMBLE

This document locks architectural decisions that prevent backsliding.

Every rule is non-negotiable.
Every violation is a bug, not a feature.
Jarvis is plumbing, not a brain.

---

## LOCKED LAWS (INVIOLABLE)

### 1. Jarvis IS NOT an LLM
- ❌ No conversation memory
- ❌ No context management
- ❌ No inference or interpretation
- ❌ No personality or tone
- ✅ Plain voice-to-text pipe

**Enforcement**: SessionState contains ONLY:
- `mode`: User-specified interaction mode
- `is_active`: Daemon control flag

**Deleted**: `last_audio`, `last_transcription`, `last_classification`, `last_error`, `input_count`

---

### 2. Claude CLI is the ONLY Brain

- ✅ Jarvis captures voice
- ✅ Jarvis sends text to Claude CLI
- ✅ Claude responds to terminal
- ✅ User reads and interacts with Claude normally

- ❌ Jarvis does NOT capture Claude's output
- ❌ Jarvis does NOT modify Claude's answers
- ❌ Jarvis does NOT interpret Claude's responses
- ❌ Jarvis does NOT maintain conversation context

**Enforcement**: CLIAdapter is fire-and-forget. No response handling.

---

### 3. No Silent Modifications

Any modification to user input without explicit user action is FORBIDDEN.

#### What's FORBIDDEN:
- PromptShaper prefixes like `[CODING]`
- Mode-based context injection
- Hidden semantic transformations
- Automatic prompt enhancement

#### Reason:
User input must reach Claude unchanged.
If user wants mode-specific behavior, they speak it explicitly.

**Enforcement**: `PromptShaper.shape()` returns text AS-IS, ignores mode parameter.

---

### 4. Jarvis Does NOT Evaluate Danger

Safety decisions are Claude's responsibility, not Jarvis's.

#### What's FORBIDDEN:
- Pattern matching for "dangerous" commands
- Confirmation dialogs
- Blocking inputs
- Risk assessment

#### Reason:
Jarvis assuming it can identify danger violates "Jarvis is plumbing, not a brain".

Claude will warn if needed.
User can override if needed.
Jarvis just passes input through.

**Enforcement**: `SafetyGate.check()` always returns `ALLOW`, no pattern matching.

---

### 5. Commands: ONLY `help`

All state-modifying commands deleted.

#### What's DELETED:
- `kirim` (send): Implicit - voice text goes to Claude automatically
- `ulang` (repeat): Requires memory - FORBIDDEN
- `mode` (change): Silent context injection - FORBIDDEN

#### What's KEPT:
- `help`: Static, stateless, informational

**Enforcement**: `CommandExecutor.VALID_COMMANDS = {"help"}` only.

---

### 6. Overlay UI: MINIMAL ONLY

UINotifier restricted to essential status only.

#### What's FORBIDDEN:
- Toast notifications
- Error displays
- Success confirmations
- Chat-like dialogs
- Friendly messages

#### What's ALLOWED:
- Status indicators (LISTENING, PROCESSING, READY)
- Confirmation prompts (yes/no only, for truly dangerous ops)

**Enforcement**: All Toast, Dialog, ErrorDisplay removed from main_loop.py.
Errors print to stdout.

---

### 7. No Conversation Memory

Amnesic design by enforcement.

#### Reason:
Memory enables temporal coupling.
Temporal coupling enables "assistant" behaviors.
"Assistant" behaviors violate "Jarvis is plumbing".

**Enforcement**:
- No `last_*` fields in SessionState
- No `input_count`
- Each utterance is independent
- No history between invocations

---

## ARCHITECTURAL CHANGES LOCKED

### SessionState (Simplified)

**BEFORE**:
```python
class SessionState:
    mode = "default"
    last_audio = None          # ❌ DELETED
    last_transcription = None  # ❌ DELETED
    last_classification = None # ❌ DELETED
    last_error = None          # ❌ DELETED
    input_count = 0            # ❌ DELETED
    is_active = False

    def record_audio(...): ...        # ❌ DELETED
    def record_transcription(...): ...# ❌ DELETED
    def record_classification(...): ...# ❌ DELETED
    def record_error(...): ...        # ❌ DELETED
    def increment_input_count(...): ...# ❌ DELETED
```

**AFTER**:
```python
class SessionState:
    mode = "default"
    is_active = False

    def update_mode(mode): ...  # ✅ KEPT
```

---

### CommandExecutor (Restricted)

**BEFORE**:
```python
VALID_COMMANDS = {"kirim", "ulang", "mode", "help"}

def _execute_kirim(): ...   # ❌ DELETED
def _execute_ulang(): ...   # ❌ DELETED
def _execute_mode(): ...    # ❌ DELETED
def _execute_help(): ...    # ✅ KEPT
```

**AFTER**:
```python
VALID_COMMANDS = {"help"}

def _execute_help(): ...    # ✅ KEPT
```

---

### PromptShaper (Pass-Through)

**BEFORE**:
```python
MODE_PREFIXES = {
    "default": "",
    "coding": "[CODING] ",
    "debug": "[DEBUG] ",
    "explain": "[EXPLAIN] ",
}

def shape(text, mode):
    prefix = MODE_PREFIXES[mode]
    wrapped = prefix + text
    return WrappedPrompt(prefix, wrapped, mode)
```

**AFTER**:
```python
def shape(text, mode=None):  # mode parameter ignored
    if not text:
        raise PromptShaperError("Cannot shape empty text")

    # PASS-THROUGH: No modification
    return WrappedPrompt(wrapped_text=text)
```

---

### SafetyGate (Pass-Through)

**BEFORE**:
```python
DANGEROUS_PATTERNS = {
    "file_ops": ["rm -rf", "rm -r", ...],
    "git_ops": ["git reset", ...],
    ...
}

def check(text):
    matched = self._find_dangerous_pattern(text)
    if matched:
        return SafetyCheckResult(REQUIRE_CONFIRMATION, ...)
    return SafetyCheckResult(ALLOW, ...)
```

**AFTER**:
```python
def check(text):
    if not text:
        raise SafetyGateError("Empty voice input")

    # PASS-THROUGH: Always allow
    return SafetyCheckResult(ALLOW, "...")
```

---

### MainLoop (Simplified)

**BEFORE**:
```python
# Handle command: show toast
result = command_executor.execute(...)
ui_notifier.display(Toast(...))

# Handle voice: safety check → confirmation → shape → send
safety_result = safety_gate.check(text)
if safety_result.decision == REQUIRE_CONFIRMATION:
    ui_notifier.display(Dialog(...))
wrapped = prompt_shaper.shape(text, mode)
ui_notifier.display(Toast("Sent to Claude"))
```

**AFTER**:
```python
# Handle command: print output
result = command_executor.execute(...)
print(result.message)

# Handle voice: pass through → send
safety_result = safety_gate.check(text)  # Always ALLOW
wrapped = prompt_shaper.shape(text, mode)  # Unchanged
cli_adapter.send(wrapped.wrapped_text)
```

---

## INVARIANTS (VERIFIED)

### Per-Utterance Isolation
- ✅ Each voice input is independent
- ✅ No prior context affects next input
- ✅ No transcription history required
- ✅ No classification memory

### Transparency
- ✅ All text reaching Claude is unmodified
- ✅ User input visible in terminal
- ✅ No hidden semantic transformations
- ✅ Jarvis presence minimal

### Plumbing Quality
- ✅ Boring architecture
- ✅ Deterministic behavior
- ✅ Zero inference
- ✅ Mechanical operation

---

## ANTI-PATTERNS (FORBIDDEN)

DO NOT ADD:
- ❌ Conversation memory
- ❌ Command shortcuts or aliases
- ❌ Context-aware responses
- ❌ "Helpful" prompt modifications
- ❌ UI dialogs or confirmations
- ❌ Error recovery logic
- ❌ State persistence
- ❌ Learning or caching
- ❌ Intelligent routing
- ❌ Personality or tone

---

## TESTING PROTOCOL

### Unit Tests (Locked Behavior)

```python
def test_session_state_no_memory():
    """Verify SessionState has NO history fields"""
    state = SessionState()
    assert not hasattr(state, 'last_audio')
    assert not hasattr(state, 'last_transcription')
    assert not hasattr(state, 'last_error')
    # ... etc

def test_command_executor_help_only():
    """Verify ONLY 'help' command exists"""
    executor = CommandExecutor()
    assert executor.VALID_COMMANDS == {"help"}
    result = executor.execute("help", None, None)
    assert result.success

    with pytest.raises(CommandExecutionError):
        executor.execute("ulang", None, None)
    with pytest.raises(CommandExecutionError):
        executor.execute("mode", "coding", None)

def test_prompt_shaper_pass_through():
    """Verify PromptShaper does NOT modify text"""
    shaper = PromptShaper()
    text = "write a function"
    result = shaper.shape(text, mode="coding")
    assert result.wrapped_text == text
    assert "[CODING]" not in result.wrapped_text

def test_safety_gate_always_allow():
    """Verify SafetyGate always returns ALLOW"""
    gate = SafetyGate()
    result = gate.check("rm -rf /")
    assert result.decision == SafetyDecision.ALLOW

    result = gate.check("anything at all")
    assert result.decision == SafetyDecision.ALLOW
```

### Integration Tests

```python
def test_voice_pipeline_pass_through():
    """Verify voice input → CLI without modification"""
    # Press F12
    # Speak: "what is Python?"
    # Verify terminal receives: "what is Python?" (unchanged)
    # Verify NO [CODING] prefix
    # Verify NO safety confirmation
```

---

## ENFORCEMENT CHECKLIST

Use this checklist for code review:

### Memory
- [ ] SessionState has only `mode` and `is_active`
- [ ] No `last_*` fields
- [ ] No `input_count`
- [ ] All history-recording methods deleted

### Commands
- [ ] Only `help` command exists
- [ ] `ulang` deleted
- [ ] `mode` deleted
- [ ] `kirim` deleted

### Prompt Shaping
- [ ] PromptShaper returns text unchanged
- [ ] No `[MODE]` prefixes
- [ ] Mode parameter ignored
- [ ] No semantic modification

### Safety
- [ ] SafetyGate always returns ALLOW
- [ ] No pattern matching
- [ ] No confirmation dialogs
- [ ] No input blocking

### UI/UX
- [ ] No Toast notifications
- [ ] No ErrorDisplay for failures
- [ ] No Dialog confirmations
- [ ] Errors print to stdout
- [ ] Status kept minimal

### CLI Integration
- [ ] Direct text injection to Claude
- [ ] No output capture
- [ ] Fire-and-forget semantics
- [ ] User reads Claude output in terminal

---

## AMENDMENT PROTOCOL

**NO amendments** without explicit user approval and documented rationale.

If a rule conflicts with new requirements:
1. Document the conflict
2. Request user clarification
3. Do NOT proceed without approval
4. Update this document with amendment

**Example amendment format**:
```
AMENDMENT #1 (2025-01-01)
Reason: [Explicit business justification]
Change: [Specific rule change]
Approved by: [User confirmation]
Impact: [Assessment of compliance risk]
```

---

## SUMMARY: Jarvis Minimal Viable Behavior

```
Press F12 (hotkey)
  ↓
Speak text
  ↓
F12 release (hotkey)
  ↓
[Audio Capture + VAD + Trim + Quality Check]
  ↓
[Whisper STT]
  ↓
[Classify: Command or Voice?]
  ↓
If Command:
  - Execute help → Print output
  - Unknown → Print error
  ↓
If Voice:
  - Pass text through (no modification)
  - Send to Claude CLI
  - User reads response
  ↓
Loop (wait for next hotkey)
```

**Total lines of logic**: ~50 (excluding audio/STT libraries)
**Complexity**: Minimal
**Memory**: None
**Intelligence**: Zero
**Status**: Plumbing ✅

---

## LOCKED BY

**User**: [Confirmed 2025-12-29]
**Status**: IMMUTABLE

Changes require explicit user approval.
No emergency overrides.
No "just this once" exceptions.

This is the contract.
