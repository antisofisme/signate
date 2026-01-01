# Cloud STT Configuration (ADR-004)

## Architecture Decision

JARVIS now implements **Hybrid Cloud STT** for SaaS consistency:

- **Client-side**: VAD, audio trimming, quality gatekeeping
- **Server-side**: Whisper "large" model (95% accuracy)
- **Result**: Consistent UX regardless of PC specs

---

## Switching Between Local & Cloud STT

### Option 1: Local STT (Original, Fast Development)

Use local Whisper model on client PC.

**File**: `jarvis/main.py`

```python
# Use LOCAL STT (synchronous blocking)
from jarvis.components.stt_adapter import STTAdapter

orchestrator = MainLoopOrchestrator(
    stt_model="large",  # Still blocks client, different experience per PC
    stt_timeout_ms=60000,
)
```

**Pros**:
- ✅ Offline-first (no network required)
- ✅ Fast iteration (no server dependency)

**Cons**:
- ❌ Inconsistent UX (low-end PC waits 30s, high-end waits 3s)
- ❌ Not suitable for SaaS

---

### Option 2: Cloud STT (Production, Recommended)

Send audio to backend for processing.

**File**: `jarvis/main.py`

```python
# Use CLOUD STT (hybrid client/server)
from jarvis.components.cloud_stt_adapter import CloudSTTAdapter

# Instead of:
#   orchestrator = MainLoopOrchestrator(stt_model="large")

# Use:
orchestrator = MainLoopOrchestrator(
    stt_adapter=CloudSTTAdapter(
        backend_url="http://192.168.5.12:8001",  # Your backend server
        language="id",
    )
)
```

**Pros**:
- ✅ Consistent UX for all users
- ✅ Low-end PC no longer bottleneck
- ✅ Server can scale Whisper model independently
- ✅ Cost-efficient (audio quality controls waste)

**Cons**:
- ❌ Requires network (no offline support)
- ❌ Depends on server availability

---

## Audio Quality Gatekeeping (Automatic)

**BEFORE sending to STT** (local or cloud):

1. **Trim silence** → Remove leading/trailing silence
2. **Validate quality**:
   - ✓ Audio not empty
   - ✓ RMS energy ≥ 10 (sufficient volume)
   - ✓ Silence ratio ≤ 80% (not mostly quiet)
   - ✓ No severe clipping

**If audio fails**: Shown to user with clear message, NOT sent to STT/cloud

---

## Configuration Environment Variables

Create `.env.jarvis`:

```bash
# Cloud STT Configuration
JARVIS_STT_MODE=cloud          # "local" or "cloud"
JARVIS_BACKEND_URL=http://192.168.5.12:8001
JARVIS_STT_LANGUAGE=id
JARVIS_STT_TIMEOUT_MS=120000

# Local STT Configuration (if mode=local)
JARVIS_WHISPER_MODEL=large     # tiny, base, small, medium, large
```

---

## Backend API Endpoint

**POST** `/api/v1/stt/transcribe`

**Request**:
```
FormData:
- audio_file: Raw PCM audio (int16)
- sample_rate: 44100 (or device native rate)
- language: "id" (or other language)
```

**Response**:
```json
{
  "success": true,
  "text": "transcribed text",
  "confidence": 0.95,
  "language": "id",
  "duration_ms": 3800
}
```

**Error Response**:
```json
{
  "success": false,
  "text": "",
  "confidence": 0.0,
  "error": "Error message"
}
```

---

## Deployment Checklist

### Local Development

- [ ] Whisper model downloaded locally (first run only)
- [ ] Audio quality gatekeeping active
- [ ] Console output shows: `[AUDIO QUALITY PASSED]`

### Cloud Deployment (Recommended for SaaS)

- [ ] Backend running on server (port 8001)
- [ ] Whisper "large" model available on backend
- [ ] Network connectivity from client PC to backend
- [ ] Backend URL configured in JARVIS
- [ ] Audio quality gatekeeping active on client
- [ ] Console output shows: `[STT] Cloud transcription`

---

## Testing

### Test Local STT

```bash
cd SEMAR
python -u -m jarvis.main
# Press F12, speak, check console for [TRANSCRIPTION]
```

### Test Cloud STT

```bash
cd SEMAR
# Set backend URL
export JARVIS_BACKEND_URL=http://192.168.5.12:8001
python -u -m jarvis.main
# Press F12, speak, check console for [STT] Cloud transcription
```

---

## Files Modified/Created (ADR-004)

**Audio Quality Gatekeeping**:
- ✅ `jarvis/components/audio_capture.py` → AudioTrimmer, AudioQualityGates
- ✅ `jarvis/components/main_loop.py` → STEP 1.5 quality checks

**Cloud STT**:
- ✅ `jarvis/components/cloud_stt_adapter.py` → CloudSTTAdapter (NEW)
- ✅ `backend-python/services/stt/` → New service (NEW)
- ✅ `backend-python/services/stt/routes.py` → Endpoint implementation
- ✅ `backend-python/services/stt/use_cases/transcribe.py` → Whisper processing
- ✅ `backend-python/main.py` → Router registration

**Architecture Decision**:
- ✅ `docs/ADR/ADR-004-hybrid-cloud-stt.md` → Decision record

---

## Migration Path

### Week 1-4: Local STT (Development)
```python
stt_model="large"  # 20-30s per utterance, tests pass
```

### Week 5: Cloud STT (SaaS-Ready)
```python
cloud_stt = CloudSTTAdapter(backend_url="...")
# Consistent UX for all users
```

---

## Performance Impact

| Metric | Local STT | Cloud STT |
|--------|-----------|-----------|
| **Client PC Usage** | High (large model) | Low (trim/validate only) |
| **Network** | None | Audio upload (~100KB) |
| **Processing Time** | 3-30s (device-dependent) | ~30s consistent |
| **UX Consistency** | ❌ Variable | ✅ Consistent |
| **Scalability** | ❌ Limited | ✅ Unlimited |

---

## Troubleshooting

### Audio Quality Rejected
```
[AUDIO QUALITY REJECTED] Audio too quiet (RMS: 5.2, min: 10)
```
**Solution**: Speak louder, closer to microphone, reduce background noise

### Cloud STT Connection Failed
```
[STT] Cloud STT request failed: Connection refused
```
**Solution**:
- Check backend is running: `docker ps | grep backend`
- Check backend URL: `export JARVIS_BACKEND_URL=http://...`
- Check network connectivity: `ping 192.168.5.12`

### Whisper Model Download (First Time)
```
[STT] Loading Whisper model: large
```
- Takes 5-15 minutes (first time only)
- Large model is ~2.9 GB
- Subsequent runs use cached model

---

## Related Documentation

- **ADR-004**: `docs/ADR/ADR-004-hybrid-cloud-stt.md`
- **Audio Pipeline**: `docs/layer-0/JARVIS-DEC-001-audio-pipeline-latency-model.md`
- **Orchestration**: `docs/layer-2/JARVIS-L2-ARCH-001-orchestration-loop.md`
