# JARVIS-L1-DEC-003: Prompt Shaping Contract

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 1 - Contracts & Boundaries

---

## Purpose

Define **how Jarvis wraps voice input before sending to Claude CLI** and **what it absolutely must NOT do**.

This is the last defense before Claude. It's also where the most dangerous temptation lives: adding "hidden intelligence".

Key principle: **Prompt shaping is mechanical, not semantic. Simple wrapping, never clever manipulation.**

---

## Core Contract: The Simple Wrapping Model

### What is Prompt Shaping?

```
VoiceInput(text, mode)
  ↓
┌──────────────────────────────────────┐
│ PROMPT SHAPING                       │
│                                      │
│ 1. Get current mode from session     │
│ 2. Get mode-specific prefix (lookup) │
│ 3. Prepend prefix to text            │
│ 4. Result: wrapped_prompt            │
└──────────────────────────────────────┘
  ↓
WrappedPrompt(prefix + text)
```

**That's it. No more, no less.**

---

## The Contract: Input → Output

### Input

```python
class PromptShapingInput:
    text: str           # Voice input (clean, from safety gate)
    mode: str           # Current session mode
                        # values: "default", "coding", "debug", "explain"
    session_id: str     # For debugging only, not used in wrapping
```

### Output

```python
class WrappedPrompt:
    prefix: str         # Mode-specific prefix (or empty)
    wrapped_text: str   # prefix + original text
    mode_applied: str   # Which mode was used
```

### The Wrapping Rules (DETERMINISTIC)

```python
def shape_prompt(text: str, mode: str) -> WrappedPrompt:
    """
    Simple, deterministic prompt shaping.
    """

    # Mode-to-prefix mapping (fixed, not context-dependent)
    MODE_PREFIXES = {
        "default": "",
        "coding": "[CODING] ",
        "debug": "[DEBUG] ",
        "explain": "[EXPLAIN] ",
    }

    # Lookup prefix
    prefix = MODE_PREFIXES.get(mode, "")

    # Wrap
    wrapped = prefix + text

    return WrappedPrompt(
        prefix=prefix,
        wrapped_text=wrapped,
        mode_applied=mode
    )
```

---

## What This Contract ALLOWS

### ✅ ALLOWED: Mechanical Prefix Wrapping

```
mode = "coding"
text = "build a function"
→ wrapped = "[CODING] build a function"
```

### ✅ ALLOWED: Mode-to-Prefix Mapping

```
mode = "default" → prefix = ""
mode = "coding" → prefix = "[CODING] "
mode = "debug" → prefix = "[DEBUG] "
mode = "explain" → prefix = "[EXPLAIN] "
```

### ✅ ALLOWED: Direct Text Concatenation

```
wrapped_text = prefix + text
```

### ✅ ALLOWED: Metrics & Logging

```
Log: mode applied, prefix used, original text
(for debugging, not decision-making)
```

---

## What This Contract FORBIDS (CRITICAL)

### ❌ FORBIDDEN: Context-Aware Wrapping

```
WRONG:
  if text contains "database" and mode="coding":
    wrapped = "[DATABASE CODING] " + text

CORRECT:
  if mode="coding":
    wrapped = "[CODING] " + text
```

**Rationale**: Context-dependent logic is hidden intelligence. Violates simplicity.

---

### ❌ FORBIDDEN: Conversation History Injection

```
WRONG:
  last_context = get_conversation_history()
  wrapped = f"[Previous: {last_context}] {text}"

CORRECT:
  Don't read history. Claude CLI owns memory.
  Jarvis only wraps current input.
```

**Rationale**: Violates "Claude is sole brain" principle.

---

### ❌ FORBIDDEN: Entity/Variable Substitution

```
WRONG:
  user_name = get_user_name()
  wrapped = f"@{user_name}: {text}"

CORRECT:
  wrapped = prefix + text
```

**Rationale**: Entity lookup is business logic. Jarvis doesn't decide who the user is.

---

### ❌ FORBIDDEN: Conditional Prefix Selection

```
WRONG:
  if text.startswith("help"):
    prefix = "[HELP REQUEST] "
  else if text.startswith("code"):
    prefix = "[CODE] "
  else:
    prefix = mode_prefix

CORRECT:
  prefix = MODE_PREFIXES[mode]
  (mode is controlled by user command, not text content)
```

**Rationale**: Text-driven prefix selection is semantic interpretation. Violates contract.

---

### ❌ FORBIDDEN: System Prompt Injection

```
WRONG:
  system_prompt = f"You are a {mode} assistant. Be brief."
  send_to_claude(system_prompt, user_text)

CORRECT:
  wrapped = prefix + user_text
  send_to_claude(wrapped)
  (prefix is context hint, not system instruction)
```

**Rationale**: Jarvis never controls Claude's system instructions. That's not its role.

---

### ❌ FORBIDDEN: Reformatting or Cleaning Input

```
WRONG:
  cleaned_text = fix_grammar(text)
  wrapped = prefix + cleaned_text

CORRECT:
  wrapped = prefix + text
  (send original text, let Claude handle it)
```

**Rationale**: Modifying user input is presumption. Violates transparency.

---

### ❌ FORBIDDEN: Multi-Line Wrapping (Hidden Structure)

```
WRONG:
  wrapped = f"""
  [CODING MODE]
  User: {text}
  Context: {get_context()}
  """

CORRECT:
  wrapped = "[CODING] " + text
  (single-line, transparent, no hidden structure)
```

**Rationale**: Hidden structure is invisible to user. Violates transparency.

---

## Mode Prefix Semantics

### What Prefixes Mean (Documentation, Not Logic)

```
[CODING] - User is writing/reviewing code
           Claude may emphasize syntax, patterns, best practices
           (Claude interprets, not Jarvis enforces)

[DEBUG]   - User is debugging
           Claude may emphasize troubleshooting, error analysis
           (Claude interprets, not Jarvis enforces)

[EXPLAIN] - User wants explanation
           Claude may emphasize clarity, analogies
           (Claude interprets, not Jarvis enforces)

default   - No hint, normal conversation
           Claude responds naturally
```

**Critical**: These are **hints to Claude, not instructions**. Claude decides what to do with them.

**Hard requirement**: **Jarvis MUST NOT rely on Claude honoring these hints.**

Rationale: Prefix is best-effort context, not a behavioral contract. Claude may ignore prefixes and respond naturally. Jarvis accepts this uncertainty and does not make assumptions about Claude's behavior based on mode.


---

## Allowed & Forbidden Summary

### ✅ DO

- Simple prefix wrapping based on mode
- Fixed mode-to-prefix mapping
- Direct string concatenation
- Transparent, visible prefixes
- Pass original text unchanged
- Log for debugging

### ❌ DON'T

- Context-aware conditional logic
- History injection
- Entity resolution
- Text-driven prefix selection
- System prompt modification
- Input reformatting
- Hidden structural wrapping
- Semantic interpretation

---

## Five Concrete Scenarios

### Scenario 1: Default Mode (Empty Prefix) - PASS

```
Input:
  VoiceInput(
    text="what time is it",
    mode="default"
  )

Shaping:
  prefix = MODE_PREFIXES["default"] = ""
  wrapped = "" + "what time is it"
  wrapped = "what time is it"

Output:
  WrappedPrompt(
    prefix="",
    wrapped_text="what time is it",
    mode_applied="default"
  )

Send to Claude CLI:
  "what time is it"

Result: ✅ PASS
        No wrapping, transparent
```

---

### Scenario 2: Coding Mode (Deterministic Prefix) - PASS

```
Input:
  VoiceInput(
    text="build a function to sort an array",
    mode="coding"
  )

Shaping:
  prefix = MODE_PREFIXES["coding"] = "[CODING] "
  wrapped = "[CODING] " + "build a function to sort an array"
  wrapped = "[CODING] build a function to sort an array"

Output:
  WrappedPrompt(
    prefix="[CODING] ",
    wrapped_text="[CODING] build a function to sort an array",
    mode_applied="coding"
  )

Send to Claude CLI:
  "[CODING] build a function to sort an array"

Claude sees: Context hint that user is writing code
Claude decides: May emphasize syntax, patterns, etc.

Result: ✅ PASS
        Simple, transparent, deterministic
```

---

### Scenario 3: Debug Mode (Different Prefix) - PASS

```
Input:
  VoiceInput(
    text="why does this crash on line 42",
    mode="debug"
  )

Shaping:
  prefix = MODE_PREFIXES["debug"] = "[DEBUG] "
  wrapped = "[DEBUG] why does this crash on line 42"

Send to Claude CLI:
  "[DEBUG] why does this crash on line 42"

Claude sees: Context hint for debugging
Claude decides: May emphasize error analysis

Result: ✅ PASS
        Mode-driven, not context-driven
```

---

### Scenario 4: Context-Aware Temptation (FORBIDDEN) - FAIL

```
Input:
  VoiceInput(
    text="build something for database optimization",
    mode="coding"
  )

WRONG APPROACH:
  if "database" in text and mode=="coding":
    prefix = "[DATABASE CODING] "  ← SEMANTIC INFERENCE
    wrapped = "[DATABASE CODING] build something..."

WHY FORBIDDEN:
  - Text-driven prefix selection violates contract
  - Jarvis is "reading" the content and making decisions
  - This is hidden intelligence (data extraction + logic)
  - Claude is no longer sole interpreter of intent

CORRECT APPROACH:
  prefix = MODE_PREFIXES["coding"] = "[CODING] "
  wrapped = "[CODING] build something for database optimization"
  (Let Claude decide that user is talking about databases)

Result: ❌ FAIL (if done wrong)
        ✅ PASS (if kept simple)
```

---

### Scenario 5: System Prompt Temptation (FORBIDDEN) - FAIL

```
Input:
  VoiceInput(
    text="explain how quicksort works",
    mode="explain"
  )

WRONG APPROACH:
  system_prompt = "You are an expert explainer. Use analogies and simple language."
  send_to_claude(system_prompt, text)

WHY FORBIDDEN:
  - Jarvis is controlling Claude's instructions
  - This violates "Claude is sole brain"
  - Hidden system behavior (user doesn't see system prompt)

CORRECT APPROACH:
  prefix = MODE_PREFIXES["explain"] = "[EXPLAIN] "
  wrapped = "[EXPLAIN] explain how quicksort works"
  (Send wrapped text without system prompt)
  (Claude reads "[EXPLAIN]" hint and decides how to respond)

Result: ❌ FAIL (if done wrong)
        ✅ PASS (if kept simple)
```

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- Deterministic, fixed mode-to-prefix mapping
- Simple string concatenation (prefix + text)
- Transparent prefixes (visible to user and Claude)
- Original text passed unchanged
- Single-line wrapping
- No context-dependent logic
- No hidden structure or injected content

❌ **MUST NOT HAVE**:
- Context-aware conditional prefixes
- Text content analysis for prefix selection
- History or conversation context injection
- Entity resolution or user identification
- System prompt injection
- Input reformatting or cleaning
- Multi-line wrapped structure
- Semantic interpretation of user intent

---

## Relationship to Other Layers

**Layer 1 (L1-DEC-001, 002)**:
- Input boundary produces clean VoiceInput
- Command executor routes commands away
- This contract receives guaranteed clean VoiceInput

**Layer 0 (DEC-002)**:
- Mode is set by command executor
- This contract uses mode value as-is
- Mode is already validated before reaching here

**Layer 2+ (will define)**:
- Prompt shaper outputs WrappedPrompt
- CLI adapter sends wrapped text to Claude
- Claude interprets prefix and responds

---

## Contract Violations (Examples of What NOT to Do)

### ❌ VIOLATION #1: Text Analysis for Prefix

```
WRONG:
  if "error" in text or "bug" in text:
    prefix = "[DEBUG] "
  else if "explain" in text:
    prefix = "[EXPLAIN] "
  else:
    prefix = mode_prefix

CORRECT:
  prefix = MODE_PREFIXES[mode]
  (user controls mode via command, not text content)
```

### ❌ VIOLATION #2: Context Injection

```
WRONG:
  previous = get_last_response()
  wrapped = f"[Previous context: {previous}] {text}"

CORRECT:
  wrapped = prefix + text
  (Claude has its own memory, no injection)
```

### ❌ VIOLATION #3: User Identification

```
WRONG:
  user = get_current_user()
  wrapped = f"[User: {user}] {text}"

CORRECT:
  wrapped = prefix + text
  (Jarvis doesn't identify users)
```

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Prefix mapping | Fixed, mode-based | Deterministic, not context-aware |
| Wrapping style | Single-line concatenation | Transparent, simple |
| Prefix meaning | Hint to Claude, not instruction | Claude is sole brain |
| Text modification | None, pass original | Transparency, user intent preserved |
| Logic complexity | None (lookup + concat) | Simplicity prevents hidden intelligence |

---

**Next**: JARVIS-L1-DEC-004 (CLI Interaction Contract)

