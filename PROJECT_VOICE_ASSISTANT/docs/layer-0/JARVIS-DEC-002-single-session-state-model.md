# JARVIS-DEC-002: Single-Session & State Model

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 0 - Foundational Concepts

---

## Overview

JARVIS-DEC-002 defines **session boundaries** and **state management** that prevent secondary memory, maintain Claude CLI as sole reasoning engine, and preserve simplicity.

Key principle: **Jarvis dies with Claude CLI**. No persistent memory between sessions.

---

## Core Concept: Session Lifecycle

```
┌────────────────────────────────────────────────────┐
│  USER STARTS CLAUDE CLI                           │
└────────────────────┬───────────────────────────────┘
                     │
                     ↓
       ┌──────────────────────────┐
       │  SESSION BEGINS          │
       │  (Jarvis initializes)    │
       │                          │
       │  Jarvis state:           │
       │  - mode = default        │
       │  - hotkey = F12          │
       │  - audio_device = default│
       │  - config loaded         │
       └──────────────────────────┘
                     │
                     ↓
       ┌──────────────────────────┐
       │  USER INTERACTS          │
       │  (voice input → Claude)  │
       │                          │
       │  Jarvis processes:       │
       │  - voice → text          │
       │  - apply mode            │
       │  - send to Claude CLI    │
       │                          │
       │  Claude CLI is authority │
       │  Jarvis does not store   │
       │  conversation content    │
       └──────────────────────────┘
                     │
       (repeat until Claude CLI closes)
                     │
                     ↓
┌────────────────────────────────────────────────────┐
│  USER CLOSES CLAUDE CLI (or Jarvis crashes)       │
└────────────────────┬───────────────────────────────┘
                     │
                     ↓
       ┌──────────────────────────┐
       │  SESSION ENDS            │
       │  (Jarvis terminates)     │
       │                          │
       │  ALL state cleared:      │
       │  - mode reset to default │
       │  - audio buffer cleared  │
       │  - pending requests null │
       │                          │
       │  ✅ Jarvis state NOT     │
       │  ✅ persisted to disk    │
       │  ✅ encrypted            │
       │  ✅ cached               │
       └──────────────────────────┘
                     │
                     ↓
       [NEW SESSION STARTS FROM SCRATCH]
```

---

## Session Definition

**What is a session?**

A session is **one continuous lifetime of Jarvis process linked to one Claude CLI lifetime**.

| Aspect | Rule |
|--------|------|
| Start | Claude CLI process starts → Jarvis initializes |
| End | Claude CLI process exits → Jarvis terminates |
| Memory | ZERO persistent state across session boundaries |
| State Reset | On Claude CLI restart → Jarvis starts fresh |
| Lifespan | Max = Claude CLI uptime |

---

## Jarvis State (In-Memory Only)

### Allowed State (Session-Local)

State that Jarvis **MAY** store during a session:

```python
class JarvisSessionState:
    """In-memory only, lost on Claude CLI exit"""

    # Mode: affects prompt shaping
    mode: str = "default"  # one of: default, coding, debug, explain

    # Configuration (loaded from config file, not modified)
    hotkey: str = "F12"
    audio_device: str = "default"
    stt_engine: str = "whisper_local"

    # Current buffer (transient, cleared after text insertion)
    audio_buffer: bytes = b""
    pending_transcription: Optional[str] = None

    # UI State (overlay)
    overlay_visible: bool = False
    last_command_issued: str = ""  # for "ulang" (resend) command

    # Metrics (for this session only)
    session_start_time: float
    total_voice_inputs: int = 0
    total_commands: int = 0
```

### FORBIDDEN State (NO Persistent Memory)

State that Jarvis **MUST NOT** store:

```python
❌ Conversation history       (Claude CLI owns this)
❌ User preferences by user  (violates single-user model)
❌ Voice input history       (violates privacy, secondary memory)
❌ Decision cache            (violates "Claude is sole brain")
❌ Custom mode templates     (Phase 2 only, if at all)
❌ API keys / tokens         (use config file only, not memory)
❌ Prompt refinement results (violates "no auxiliary LLM memory")
❌ Cross-session stats       (each session is independent)
```

---

## Mode Management

### What is Mode?

Mode is **a local state variable that affects prompt shaping** (how Jarvis frames user input before sending to Claude).

**NOT**:
- ❌ A system prompt injected into Claude
- ❌ A stored preference
- ❌ Part of conversation history
- ❌ Visible to Claude CLI

**IS**:
- ✅ Local state in Jarvis memory
- ✅ Affects how Jarvis wraps user text
- ✅ Reset on session restart
- ✅ Transparent to Claude (Claude never knows about mode)

### Supported Modes (MVP)

```
mode = "default"
  → No special wrapping
  → User input sent as-is to Claude CLI

mode = "coding"
  → Wrap: [CODING] {user_input}
  → Affects prompt framing for dev tasks
  → Example: user says "fix the bug"
             → Jarvis sends: "[CODING] fix the bug"

mode = "debug"
  → Wrap: [DEBUG] {user_input}
  → Affects prompt framing for debugging
  → Example: user says "what's the issue"
             → Jarvis sends: "[DEBUG] what's the issue"

mode = "explain"
  → Wrap: [EXPLAIN] {user_input}
  → Affects prompt framing for explanations
  → Example: user says "how does this work"
             → Jarvis sends: "[EXPLAIN] how does this work"
```

### Mode Reset

**When does mode reset?**

```
✅ Session end (Claude CLI closes)
   → mode = "default"

✅ User explicitly resets
   → "mode default" command

❌ Never automatically reset during session
   → Mode persists until user changes or session ends
```

---

## Last Command ("ulang" Resend)

### Purpose

Allow user to resend the last voice input without re-recording.

```
Scenario:
User: [F12 pressed, says "build a function"]
Jarvis: "build a function" → Claude CLI
Claude: [produces output]

User: [realizes they misspoke, wants to correct]
User: "ulang"  (command)
Jarvis: [re-sends "build a function" without new voice input]
User: [recognizes this is wrong]
User: [re-records with new voice input]
```

### State Management

```python
# Jarvis stores only:
last_transcription: Optional[str] = None

# On voice input → transcription complete:
last_transcription = transcribed_text

# On "ulang" command:
if last_transcription:
    send_to_claude(last_transcription)
else:
    display_error("Nothing to resend")

# On Claude CLI close:
last_transcription = None  # cleared
```

---

## Session Metrics (Observability Only)

**Allowed metrics** (session-local, not persisted):

```
jarvis.session.start_time         → when session began
jarvis.session.voice_inputs       → count of voice inputs
jarvis.session.commands_issued    → count of commands
jarvis.session.mode_changes       → count of mode switches
jarvis.session.errors             → count of errors
jarvis.session.fallbacks_to_typing → count of STT failures
```

**NOT persisted** between sessions.

**Used for**: Debugging current session, logging, not decision-making.

---

## Five Concrete Scenarios

### Scenario 1: Simple Session (Single Query)

```
T0: User starts Claude CLI
    → Jarvis initializes
    → mode = "default"
    → audio_buffer = empty

T1: User [F12] "how do I debug this"
    → Transcription: "how do I debug this"
    → last_transcription = "how do I debug this"
    → Send to Claude: "how do I debug this"

T2: Claude responds (Jarvis doesn't interfere)

T3: User closes Claude CLI
    → Jarvis terminates
    → ALL state cleared (mode, audio_buffer, last_transcription)
    → Session ends

Next Claude CLI start: Jarvis fresh, mode = "default"
```

### Scenario 2: Mode Changes During Session

```
T0: Claude CLI starts
    → mode = "default"

T1: User: "mode coding"
    → Jarvis: mode = "coding"
    → No text sent to Claude
    → Overlay: "Mode: CODING"

T2: User: [F12] "build a react component"
    → mode is still "coding"
    → Wrap input: "[CODING] build a react component"
    → Send to Claude

T3: User: "mode explain"
    → Jarvis: mode = "explain"
    → Overlay: "Mode: EXPLAIN"

T4: User: [F12] "what does this function do"
    → mode is now "explain"
    → Wrap input: "[EXPLAIN] what does this function do"
    → Send to Claude

T5: Claude CLI closes
    → mode reset to "default"
    → Next session starts fresh

Session metrics collected:
  - session.mode_changes = 2
  - session.voice_inputs = 2
  - session.duration = 15 minutes

⚠️ These metrics NOT saved to next session
```

### Scenario 3: Resend Last Input ("ulang")

```
T0: Session initialized, mode = "default"

T1: User: [F12] "fix the authentication bug"
    → Transcription: "fix the authentication bug"
    → last_transcription = "fix the authentication bug"
    → Send to Claude

T2: Claude responds with code

T3: User reads response, realizes they need more context
    User: "ulang"  (resend command)
    → Jarvis doesn't re-record voice
    → Resends: "fix the authentication bug"
    → Claude sees same input again (may provide different response)

T4: User: "mode debug"
    → mode = "debug"

T5: User: [F12] "where is the token validation"
    → Transcription: "where is the token validation"
    → last_transcription = "where is the token validation"
    → Wrap: "[DEBUG] where is the token validation"
    → Send to Claude

Session state:
  - mode = "debug"
  - last_transcription = "where is the token validation"
  - total_voice_inputs = 2
  - total_commands = 1 (ulang)
```

### Scenario 4: STT Failure & Manual Recovery

```
T0: Session starts, mode = "default"

T1: User: [F12] "explain the database schema"
    → Audio captured
    → VAD processes
    → Whisper STT fails (timeout, model error)

T2: Jarvis displays: "STT failed, please type instead"
    → last_transcription NOT updated
    → audio_buffer cleared
    → session.fallbacks_to_typing += 1

T3: User types manually: "explain the database schema"
    → Jarvis: this is keyboard input, not voice
    → last_transcription = "explain the database schema"
    → Send to Claude

T4: User: "ulang"
    → Resends: "explain the database schema"
    → Works (keyboard input doesn't have STT failures)

Note: Jarvis does NOT distinguish between voice and keyboard in last_transcription
      Both are treated as "last user input"
```

### Scenario 5: Crash & Recovery (Session Loss)

```
T0-T20: User works with Claude + Jarvis for 20 minutes
        → mode = "coding"
        → last_transcription = "optimize the sorting algorithm"
        → session.voice_inputs = 47
        → session.commands_issued = 12

T21: Jarvis crashes (segfault, exception)
        → Session state: LOST (no persistence)
        → Claude CLI still running
        → User may not notice

T22: User [F12] "what's the next step"
        → Jarvis re-initializes (fresh process)
        → mode = "default"  (LOST previous coding mode)
        → audio_buffer = empty
        → last_transcription = None  (LOST previous text)
        → session metrics reset

T23: User may realize mode is not "coding" anymore
        → User re-issues: "mode coding"
        → Continues work

UX Impact: ⚠️ Mode lost if Jarvis crashes
           (Acceptable: user can re-set mode easily)
```

---

## Implementation Checkpoints

### Before MVP Release

- [ ] Jarvis state is in-memory only (no disk persistence)
- [ ] Mode persists during Claude CLI session
- [ ] Mode resets to "default" on Claude CLI exit
- [ ] last_transcription used for "ulang" command only
- [ ] last_transcription cleared on new voice input
- [ ] Session metrics collected but not persisted
- [ ] No conversation history stored in Jarvis
- [ ] No user preference persistence
- [ ] Audio buffer cleared after each input

### Phase 2 (Optional Enhancement)

- [ ] Session recovery: Jarvis crash → resume mode (optional nice-to-have)
- [ ] Session history viewer: "what happened in this session" (non-persistent)
- [ ] Configuration persistence (separate from state)

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- Single-session model (Jarvis lifetime = Claude CLI lifetime)
- In-memory state only (no persistence across sessions)
- Mode as local state (affects prompt shaping, not stored in chat)
- No conversation history in Jarvis (Claude CLI owns this)
- Session reset on Claude CLI exit
- last_transcription for "ulang" command only

❌ **MUST NOT HAVE**:
- Persistent user preferences
- Cross-session memory
- Voice input history (privacy)
- Decision cache (violates "Claude is sole brain")
- Secondary memory storage
- Mode embedded as system prompt to Claude
- Conversation history in Jarvis memory

---

## State Diagram

```
┌─────────────────────┐
│  Claude CLI Exit    │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────────────────┐
│  SESSION_ENDED                  │
│  - mode → CLEARED               │
│  - audio_buffer → CLEARED       │
│  - last_transcription → CLEARED │
│  - overlay → HIDDEN             │
└──────────┬──────────────────────┘
           │
           ↓
        [SLEEP]
           │
           ↓
┌──────────────────────────────────┐
│  Claude CLI Start                │
└──────────┬───────────────────────┘
           │
           ↓
┌──────────────────────────────────┐
│  SESSION_STARTED                 │
│  - mode = "default"              │
│  - audio_buffer = empty          │
│  - last_transcription = None     │
│  - overlay = hidden (or visible) │
│  - config loaded from file       │
└──────────┬───────────────────────┘
           │
           ↓
┌──────────────────────────────────┐
│  READY FOR INPUT                 │
│  (waiting for F12 hotkey)        │
└──────────────────────────────────┘
           │
    ┌──────┴──────────────┬─────────┐
    ↓                     ↓         ↓
[F12 pressed]    [Command issued] [Mode change]
    │                     │         │
    ↓                     ↓         ↓
[Audio capture]   [Process cmd]  [Update mode]
    │                     │         │
    └──────┬──────────────┴─────────┘
           ↓
┌──────────────────────────────────┐
│  PROCESSING INPUT                │
│  (transcribing, wrapping, etc.)  │
└──────────┬───────────────────────┘
           │
           ↓
┌──────────────────────────────────┐
│  TEXT SENT TO CLAUDE CLI         │
└──────────┬───────────────────────┘
           │
           ↓
┌──────────────────────────────────┐
│  BACK TO READY FOR INPUT         │
│  (mode persists if not changed)  │
└──────────────────────────────────┘
```

---

## Relationship to Other Layers

**Layer 1 (Contracts)**:
- Session state boundaries define SDK input/output scope
- Session resets define session-scoped request handling

**Layer 2 (Architecture)**:
- Session model affects component lifecycle (Input Orchestrator)
- State reset affects error recovery

**Layer 3 (Implementation)**:
- Python multiprocessing: Jarvis process lifetime
- Configuration file loading (only once per session)

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Session lifespan | = Claude CLI lifespan | Simple, no cross-process coupling |
| State storage | In-memory only | No secondary memory |
| Mode reset | On Claude CLI exit | Clean slate each session |
| Metrics persistence | Not persisted | Prevents decision-making on stale data |
| last_transcription | Cleared on new input | Privacy, simplicity |
| Conversation history | Not stored | Claude CLI owns reasoning |
| User preferences | Loaded from config file only | No persistent state |

---

**Next**: JARVIS-DEC-003 (Command Grammar & Safety Model)

