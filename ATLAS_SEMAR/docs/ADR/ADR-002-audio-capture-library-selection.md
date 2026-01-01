# ADR-002: Audio Capture Library Selection

**Status**: PROPOSED

**Date**: 2025-12-28

**Affects**: AudioCapture (Week 1, critical path)

---

## Problem Statement

AudioCapture must record audio synchronously while hotkey is held, detect silence (VAD), and return audio buffer.

**Context**:
- JARVIS-DEC-001 requires synchronous blocking capture (no async)
- Must capture while hotkey held (push-to-talk model)
- Must detect silence (1.5s VAD timeout)
- Must work cross-platform
- Audio must be raw PCM (no compression)

**Why this matters**:
- Audio quality and timing directly affect STT accuracy and latency SLA
- Wrong library choice could violate blocking guarantee or introduce latency creep

---

## Options Considered

### Option A: sounddevice (PROPOSED)

**Pros**:
- Synchronous, blocking API (native to architecture)
- Cross-platform (Windows, macOS, Linux via PortAudio)
- Simple: `rec()` records until told to stop
- Raw PCM output (no codec complexity)
- Extensive documentation

**Cons**:
- PortAudio backend dependency (external binary on some systems)
- No built-in VAD (must implement separately with Silero/WebRTC)

**Compliance with JARVIS contracts**:
- ✅ JARVIS-DEC-001: Synchronous blocking (core requirement)
- ✅ JARVIS-L3-ARCH-002: No async, no background threads
- ✅ Push-to-talk: Can detect hotkey release and stop recording

---

### Option B: pyaudio (Alternative Considered)

**Why rejected**:
- More verbose API (stream callback model, not ideal for push-to-talk)
- Callback model tempts async patterns (architecture risk)
- No significant advantage over sounddevice for synchronous use case

---

### Option C: librosa (Alternative Considered)

**Why rejected**:
- Designed for analysis, not real-time capture
- Adds heavy dependencies (numpy, scipy)
- Overkill for simple capture → buffer task
- Introduces latency

---

## Decision

**We will use sounddevice for AudioCapture.**

**Rationale**:
- Synchronous blocking API matches architecture requirement perfectly
- Simple to use: `sounddevice.rec()` returns immediately with buffer
- Cross-platform with minimal platform-specific code
- Raw PCM output avoids codec complexity
- Proven in production audio applications

---

## Constraints & Requirements

**From JARVIS-DEC-001**:
- Duration ceiling: 120s (hard limit)
- VAD timeout: 1.5s silence = end capture
- Sample rate: 16000 Hz
- Format: PCM (int16 or float32)

**From JARVIS-L3-ARCH-002**:
- Must be synchronous (blocking until hotkey release)
- Must not use async/await
- Must not spawn background threads

**Implementation must ensure**:
- [ ] Recording starts/stops synchronously with hotkey
- [ ] VAD timeout implemented (separate from sounddevice)
- [ ] Duration ceiling enforced
- [ ] Raw PCM returned as AudioBuffer
- [ ] Cross-platform tested

---

## Implementation Notes

**Where**: `jarvis/components/audio_capture.py`

**Pattern**:
```python
import sounddevice
import numpy as np

class AudioCapture:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def capture(self):
        """
        Capture audio while hotkey held.
        BLOCKS until hotkey release or timeout.
        Returns raw PCM or raises AudioCaptureError.
        """
        audio_buffer = []
        vad_silence_count = 0

        while True:
            # Read frame (blocks ~10ms)
            frame = sounddevice.rec(
                frames=160,  # ~10ms at 16kHz
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocking=True
            )

            audio_buffer.append(frame)

            # Check hotkey release
            if not self._is_hotkey_pressed():
                break

            # Check VAD silence
            if self._is_silent(frame):
                vad_silence_count += 1
                if vad_silence_count > 150:  # ~1.5s silence
                    break
            else:
                vad_silence_count = 0

            # Check duration ceiling
            if len(audio_buffer) * 10 > 120000:  # 120s
                raise AudioCaptureError("Audio too long")

        return AudioBuffer(samples=np.concatenate(audio_buffer))
```

**Testing**:
- [ ] Records while hotkey held
- [ ] Stops on hotkey release
- [ ] VAD timeout works (1.5s silence ends recording)
- [ ] Duration ceiling enforced (120s max)
- [ ] Raw PCM returned correctly
- [ ] Cross-platform tested (Windows, macOS, Linux)

---

## VAD Implementation Note

**Silence detection** (separate concern):
- Use simple RMS-based VAD (no external dependency)
- Threshold: energy < -40dB
- Or use Silero VAD if lightweight (Phase 2+)

**For Week 1**: RMS-based VAD is sufficient.

---

## Related

- **JARVIS-DEC-001**: Audio Pipeline & Latency (synchronous requirement)
- **JARVIS-L3-ARCH-002**: Threading & Concurrency (no async)
- **JARVIS-L3-ARCH-001**: Component Decomposition (AudioCapture spec)

---

## Compliance Verification

- [ ] Reviewed against JARVIS-DEC-001 (latency SLA, duration)
- [ ] Reviewed against JARVIS-L3-ARCH-002 (synchronous blocking)
- [ ] Does NOT violate any Layer 0-3 contract
- [ ] Code review will verify no async/await
- [ ] Latency testing will verify <1s capture-to-buffer

---

## Revision History

| Date | Status | Notes |
|------|--------|-------|
| 2025-12-28 | PROPOSED | Initial proposal for Week 1 |
