# JARVIS-DEC-001: Audio Pipeline & Latency Model

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 0 - Foundational Concepts

---

## Overview

JARVIS-DEC-001 defines the **audio acquisition pipeline** and **latency guarantees** that enable deterministic, low-latency voice input to Claude CLI.

This is the **hard constraint layer**: latency is non-negotiable because it determines UX viability.

---

## Core Concept: The Audio Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  USER PUSHES HOTKEY (F12 or equivalent)                │
└─────────────────────┬───────────────────────────────────┘
                      │ (T0 = 0ms)
                      ↓
┌─────────────────────────────────────────────────────────┐
│  VOICE CAPTURE (audio buffer acquisition)              │
│  - Audio device receives input                          │
│  - Raw PCM frames accumulated to buffer                 │
│  - Duration: until user releases hotkey OR silence      │
│                                                          │
│  Latency: T0 → T0+50ms (worst case: hardware delay)     │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────┐
│  VAD (Voice Activity Detection) - Silero/WebRTC        │
│  - Remove silence from beginning/end                    │
│  - Identify speech regions                              │
│  - Trim buffer to speech-only content                   │
│                                                          │
│  Latency: T0+50ms → T0+100ms (VAD processing)           │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────┐
│  STT (Speech-to-Text) - Whisper                         │
│  - Convert audio to text                                │
│  - Quality: local preferred, API acceptable             │
│  - Output: raw transcription (no filtering)             │
│                                                          │
│  Latency: T0+100ms → T0+900ms (Whisper local ≤ 1s SLA)  │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────┐
│  TEXT → CLAUDE CLI                                      │
│  - Text inserted into terminal                          │
│  - Ready for command parsing / prompt shaping           │
│                                                          │
│  Latency: T0+900ms → T0+1200ms (typing simulation)      │
└─────────────────────────────┬────────────────────────────┘
                              │
                              ↓
                    [USER SEES TEXT]

                    Total: ≤ 2 seconds
```

---

## Latency SLA (ABSOLUTE)

| Stage | Latency | Cumulative | Status |
|-------|---------|-----------|--------|
| Hotkey → Audio capture | ≤ 50ms | T0+50ms | Hard constraint |
| VAD processing | ≤ 50ms | T0+100ms | Hard constraint |
| STT (Whisper local) | ≤ 800ms | T0+900ms | Hard constraint |
| Text insertion + typing sim | ≤ 300ms | T0+1200ms | Hard constraint |
| **END-TO-END** | **≤ 2000ms** | **T0+2000ms** | **WAJIB** |

### SLA Tiers

```
✅ GREEN (Acceptable):     ≤ 1.5s end-to-end → feels instant
⚠️  YELLOW (Degraded):    1.5s - 2.0s → noticeable but acceptable
❌ RED (Unusable):        > 2.0s → users prefer typing instead
```

### Utterance Length Scope

**Jarvis is optimized for short, command-like utterances (< 10 seconds audio). Long-form dictation is explicitly out of scope for MVP.**

* MVP design targets: quick commands, brief questions, code snippets
* Long utterances (> 10s): degraded UX, consider manual typing instead
* Phase 2 (streaming STT): may improve long-utterance latency if needed
* Current design intentionally accepts this limitation to keep implementation simple

---

## Design Constraints

### 1. Push-to-Talk Model

**Rule**: Hotkey-based activation ONLY

* Hard hotkey: F12, Alt+V, or user-configurable
* Voice capture begins on hotkey DOWN
* Voice capture ends on:
  * Hotkey UP (preferred), OR
  * Silence detected for 1.5s (fallback)

**Rationale**:
- No always-listening (privacy + latency)
- No background VAD processing (no secondary memory)
- Deterministic trigger (no ambiguity)
- User has explicit control

**What this is NOT**:
- ❌ Wake word detection
- ❌ Always-listening with background processing
- ❌ Continuous audio buffering

### 2. Audio Quality Assumptions

**Minimum acceptable quality**:
- Sample rate: 16kHz or higher
- Bit depth: 16-bit PCM
- Audio device: built-in mic, USB headset, or better
- SNR (Signal-to-Noise Ratio): -20dB or better (typical office environment)

**Out of scope**:
- ❌ Echo cancellation
- ❌ Noise suppression (beyond VAD)
- ❌ Microphone quality assurance

**UX Fallback**: If STT fails or latency exceeds 2s → user falls back to manual typing

### 3. STT Engine Selection

**MVP**: Whisper local (OpenAI Whisper)

**Why local**:
- Latency: local ≤ 1s guaranteed (no network dependency)
- No cloud round-trip
- Works offline
- One-time model download (≈ 100MB for base model)

**Optional API fallback** (Phase 2):
- Allowed only if:
  * Local STT fails (timeout, crash)
  * User explicitly configures API
  * Fallback is logged for debugging
  * Falls back to manual input if API unavailable

**NOT allowed**:
- ❌ Cloud-first STT
- ❌ Cloud STT in critical path
- ❌ Automatic cloud fallback without user awareness

### 4. VAD Sensitivity

**VAD behavior**:
- Detect speech start within 100ms (responsiveness)
- Trim silence at end (≥ 1.5s of silence → end capture)
- Preserve natural pauses within speech (< 1.5s silences kept)

**Rationale**:
- Voice may have natural pauses (thinking, breathing)
- Trim trailing silence (reduces false positives to STT)
- Responsive to speech start (feels interactive)

---

## Five Concrete Scenarios

### Scenario 1: Quick Command (Latency: 800ms)

```
User: [Presses F12]
       [Says: "build a function"]
       [Releases F12]

T0: F12 pressed
T0+30ms: First audio frames captured
T0+60ms: Speech detected by VAD
T0+200ms: F12 released, audio buffer complete
T0+400ms: VAD trim silence
T0+600ms: Whisper returns "build a function"
T0+700ms: Text inserted in Claude CLI

Result: ✅ 700ms (well under 2s)
UX: Feels instant, natural conversation pace
```

### Scenario 2: Complex Query (Latency: 1200ms)

```
User: [Presses F12]
       [Says: "I need to optimize the database queries
               but I don't know where to start with indexing"]
       [Releases F12]

T0: F12 pressed
T0+50ms: Audio capture begins
T0+100ms: Speech detected
T0+4000ms: User releases F12 (long query, ~4 seconds of speech)
T0+4100ms: VAD trims silence
T0+5200ms: Whisper processes 4s audio (local model slower for long audio)
T0+5400ms: Text ready

Result: ⚠️ 5.4s total (exceeds SLA)
UX Problem: Too long - might lose user attention
Mitigation: Streaming STT (Phase 2) for queries > 2s
```

### Scenario 3: STT Fallback (Manual Input)

```
User: [Presses F12]
       [Says: "what is the meaning of life"]
       [Releases F12]

T0: F12 pressed
T0+50ms: Audio captured
T0+600ms: VAD ready
T0+1200ms: Whisper timeout (crashes or model not loaded)

Result: ❌ STT failed
Action: Jarvis displays toast: "STT failed, please type instead"
        Resets audio buffer, returns to keyboard input
UX: User types manually - acceptable degradation
```

### Scenario 4: Silence Handling (Natural Pause)

```
User: [Presses F12]
       [Says: "build a"]
       [Pauses 0.8s - thinking]
       [Says: "function in rust"]
       [Releases F12]

T0: F12 pressed
T0+50ms: Audio capture, speech detected
T0+600ms: First phrase captured ("build a")
T0+700ms: Silence detected (0.1s) - VAD PRESERVES (< 1.5s threshold)
T0+1300ms: User speaks again ("function in rust")
T0+2000ms: F12 released
T0+2100ms: VAD trims trailing silence
T0+3200ms: Whisper returns "build a function in rust"

Result: ✅ Pause preserved, full phrase transcribed
UX: Natural conversation, no stuttering
```

### Scenario 5: Network Latency (Whisper API, Phase 2)

```
User: [Presses F12]
       [Says: "what's in the config file"]
       [Releases F12]

T0: F12 pressed
T0+100ms: Audio buffer complete
T0+200ms: VAD processed
T0+300ms: Send to Whisper API (local fallback unavailable)
T0+800ms: Network latency (API call in progress)
T0+1200ms: API returns result
T0+1300ms: Text inserted

Result: ✅ 1.3s (within 2s SLA, but tight)
Scenario: Phase 2 only (API enabled by user config)
Next: Implement streaming STT to avoid buffer-before-send
```

---

## Implementation Checkpoints

### Before MVP Release

- [ ] F12 hotkey captures audio without network calls
- [ ] VAD detects speech within 100ms
- [ ] VAD trims silence correctly (< 1.5s preserved, ≥ 1.5s removed)
- [ ] Whisper local ≤ 800ms for typical queries (5-10s audio)
- [ ] Text inserted in Claude CLI ≤ 100ms after STT
- [ ] End-to-end latency ≤ 2s for 90% of queries (p90 SLA)
- [ ] Timeout handling: graceful fallback to manual input
- [ ] Error messages clear (e.g., "STT failed, type instead")

### Before Phase 2 (API/Streaming)

- [ ] Streaming STT for queries > 2s (reduce buffer delay)
- [ ] API fallback only on local STT failure
- [ ] Network latency monitored (alert if > 1.5s)
- [ ] Graceful degradation to manual input
- [ ] Config: allow user to select Whisper API vs local

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- Push-to-talk hotkey only (no always-listening)
- End-to-end latency ≤ 2s (hard limit)
- Whisper local in MVP
- Automatic fallback to manual input on STT failure
- No cloud dependency in critical path

❌ **MUST NOT HAVE**:
- Background voice processing
- Always-listening / wake word
- Cloud STT in MVP critical path
- Streaming audio without user awareness
- Latency trade-offs that exceed 2s

---

## Audio Quality Metrics (Observability)

**Metrics to collect** (for debugging):

```
jarvis.audio.capture_latency_ms     → latency T0 to audio buffer complete
jarvis.vad.processing_time_ms       → time to detect/trim silence
jarvis.stt.processing_time_ms       → Whisper processing time
jarvis.stt.success_rate             → % of successful STT attempts
jarvis.stt.timeout_rate             → % of STT timeouts
jarvis.e2e_latency_ms               → total hotkey to text insertion
jarvis.e2e_sla_compliance           → % queries ≤ 2s (target: 90%+)
jarvis.fallback_to_manual_input     → # of times user fell back to typing
```

**Alerting**:
- 🔴 **CRITICAL**: e2e_latency > 3s (more than 10% of queries)
- 🟡 **WARNING**: e2e_latency > 2.5s (more than 10% of queries)
- 🟢 **INFO**: STT failure rate (track for pattern analysis)

---

## Relationship to Other Layers

**Layer 1 (Contracts)**:
- Audio pipeline output → text input to SDK contract

**Layer 2 (Architecture)**:
- Audio pipeline is part of Input Orchestrator boundary

**Layer 3 (Implementation)**:
- Whisper integration, VAD configuration, hotkey setup

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Activation | Push-to-talk hotkey | No always-listening |
| Audio capture | Until hotkey release OR 1.5s silence | User control |
| VAD | Silero/WebRTC | Fast, local, accurate |
| STT | Whisper local MVP | ≤ 1s, no network |
| SLA | ≤ 2s end-to-end | UX threshold |
| Fallback | Manual typing | Graceful degradation |
| Config (MVP) | Hotkey, audio device | Simple, user control |

---

**Next**: JARVIS-DEC-002 (Single-Session & State Model)

