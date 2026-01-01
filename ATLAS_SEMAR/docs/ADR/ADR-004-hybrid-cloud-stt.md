# ADR-004: Hybrid Cloud STT for SaaS Consistency

**Status**: ACCEPTED

**Date**: 2025-12-29

**Affects**: STTAdapter, AudioCapture (Week 5+ extension, SaaS deployment)

---

## Problem Statement

Current local Whisper processing creates inconsistent UX:
- Low-end PC users wait 20-30s for large model
- High-end PC users wait 3-5s for small model
- Cloud STT cost scales with silence & noise (inefficient)

**Context**:
- JARVIS-DEC-001: Audio pipeline must be deterministic
- JARVIS-L2-ARCH-001: Single blocking orchestration
- JARVIS-L1-DEC-004: Fire-and-forget CLI interaction
- JARVIS-L3-ARCH-003: Error propagation & UI signaling

**Why this matters**:
- SaaS consistency requires server-side processing
- Audio quality checks MUST happen client-side before cloud send
- Client must remain lightweight (no model downloads)
- Cloud cost efficiency requires upfront VAD/trimming

---

## Options Considered

### Option A: Hybrid Cloud STT (ACCEPTED)

**Client-side**:
- VAD (silence detection)
- Audio trimming (start/end silence removal)
- Quality gatekeeping (RMS, silence ratio)
- Early rejection of bad audio

**Server-side**:
- Whisper "large" processing (95% accuracy)
- Consistent latency for all users
- Centralized model management

**Pros**:
- ✅ Consistent UX regardless of PC specs
- ✅ Low-end PC no longer bottleneck
- ✅ Cloud cost scales with quality, not silence
- ✅ Client remains lightweight (no model)
- ✅ Deterministic error handling

**Cons**:
- Requires network connectivity
- Audio sent to server (privacy consideration)
- Slight latency increase (network + processing)

**Compliance with JARVIS contracts**:
- ✅ JARVIS-DEC-001: Client-side VAD remains deterministic
- ✅ JARVIS-L2-ARCH-001: Blocking orchestration maintained
- ✅ JARVIS-L1-DEC-004: Fire-and-forget for cloud (no retry logic)
- ✅ JARVIS-L3-ARCH-003: Clear error propagation to UI

---

### Option B: Local Large Model (REJECTED)

**Why rejected**:
- Inconsistent UX: low-end PC users suffer 20-30s wait
- Scalability nightmare: can't guarantee response time
- Model bloat: 2.9GB download requirement
- Violates SaaS first-run experience

---

### Option C: Whisper API (OpenAI) (ALTERNATIVE)

**Why not primary**:
- Cost per utterance (no free tier)
- Dependency on OpenAI availability
- Less control over model deployment

**Use case**:
- If self-hosted backend not available
- If cost not concern

---

## Decision

**We will implement Hybrid Cloud STT:**

1. **Client maintains**:
   - VAD (RMS-based silence detection)
   - Audio trimming (remove start/end silence)
   - Quality gatekeeping (reject empty/silent/noise-dominated)

2. **Server processes**:
   - Whisper "large" on trimmed audio
   - Return transcription + confidence

3. **Client never sends**:
   - Silence-only audio
   - Audio below quality threshold
   - Untrimmmed padded audio

**Rationale**:
- Maximizes cloud STT efficiency
- Maintains deterministic error handling
- Preserves lightweight client design

---

## Constraints & Requirements

**From architecture layers**:
- Client-side VAD must remain blocking (JARVIS-L3-ARCH-002)
- No state persistence beyond current utterance
- Audio quality check is deterministic (testable)
- Error messages user-facing (JARVIS-L3-ARCH-003)

**Implementation must ensure**:
- [ ] VAD threshold same for all users
- [ ] Trimmed audio starts immediately after first sound
- [ ] Quality gatekeeping is deterministic
- [ ] Rejected audio shows explicit reason to user
- [ ] No retry logic (fire-and-forget)
- [ ] Network errors handled gracefully

---

## Implementation Notes

**Where**:
- `jarvis/components/audio_capture.py` → Enhanced quality checks
- `jarvis/components/stt_adapter.py` → Cloud STT endpoint
- `backend/app/services/stt/` → FastAPI endpoint (NEW)

**Client-side quality gatekeeping**:
```python
class AudioQualityGates:
    @staticmethod
    def is_valid(audio_buffer: AudioBuffer) -> tuple[bool, Optional[str]]:
        # Check 1: Not empty
        if len(audio_buffer.samples) == 0:
            return False, "No audio captured"

        # Check 2: Sufficient energy (RMS)
        rms = np.sqrt(np.mean(audio_buffer.samples.astype(float) ** 2))
        if rms < 10:  # Threshold (configurable)
            return False, "Audio too quiet"

        # Check 3: Not noise-dominated
        silence_ratio = compute_silence_ratio(audio_buffer)
        if silence_ratio > 0.8:
            return False, "Mostly silence or noise"

        # Check 4: Not clipping
        max_amplitude = np.max(np.abs(audio_buffer.samples))
        if max_amplitude > 32700:  # Near int16 max
            return False, "Audio clipping detected"

        return True, None
```

**Server-side endpoint**:
```python
@router.post("/api/v1/transcribe")
async def transcribe(audio_file: UploadFile) -> TranscriptionResponse:
    # Load trimmed audio from client
    samples = load_audio(audio_file)

    # Process with Whisper large
    result = whisper.transcribe(
        samples,
        model="large",
        language="id"
    )

    return TranscriptionResponse(
        text=result["text"],
        confidence=result["segments"][0]["confidence"]
    )
```

**Testing**:
- [ ] Unit: AudioQualityGates with various audio samples
- [ ] Integration: Cloud STT with network mock
- [ ] Invariant: Error messages user-facing

---

## Compliance Verification

- [x] Reviewed against JARVIS-DEC-001 (deterministic audio pipeline)
- [x] Reviewed against JARVIS-L2-ARCH-001 (blocking orchestration)
- [x] Reviewed against JARVIS-L3-ARCH-003 (error propagation)
- [x] Does NOT change any locked contract
- [x] Client-side VAD remains blocking

---

## Related

- **JARVIS-DEC-001**: Audio pipeline latency model
- **JARVIS-L2-ARCH-001**: Orchestration loop (maintains blocking)
- **JARVIS-L3-ARCH-003**: Error propagation (user-facing messages)

---

## Revision History

| Date | Status | Notes |
|------|--------|-------|
| 2025-12-29 | ACCEPTED | Hybrid Cloud STT approved for SaaS consistency |
