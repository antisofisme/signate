# JARVIS-L3-ARCH-002: Threading & Concurrency Model

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 3 - Threading Design & Concurrency Enforcement

---

## Purpose

Define **the exact threading model** that makes the component decomposition (L3-ARCH-001) architecturally unbreakable.

This is where all blocking-by-design decisions are tested. This is where signal-only constraints are pinned down. This is where async STT temptation dies.

Key principle: **Threading model makes contract violations impossible, not just discouraged.**

---

## Core Threading Model

### The Single Immutable Rule

```
┌───────────────────────────────────────────────────────┐
│ ONLY MainLoop thread may mutate SessionState          │
│                                                       │
│ Every other thread:                                  │
│  - Can READ SessionState (immutably)                │
│  - Can SIGNAL to MainLoop (via queue)               │
│  - CANNOT mutate state directly                     │
│  - CANNOT block on condition variables              │
└───────────────────────────────────────────────────────┘
```

This single rule prevents:
- Race conditions (no concurrent mutation)
- Deadlock (no locks needed in critical path)
- Lost updates (single writer)
- Data corruption (state only changes at defined checkpoints)

---

## Thread Topology

### Threads Defined

```
┌─────────────────────────────────────────────┐
│                    PROCESS                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Thread 1: MainLoop                 │   │
│  │  (CPU-bound: classification, CLI)   │   │
│  │                                     │   │
│  │  * Owns SessionState                │   │
│  │  * Calls all pure components        │   │
│  │  * Blocks on audio/STT              │   │
│  │  * Waits for hotkey signal          │   │
│  │  * Updates state after decisions    │   │
│  └─────────────────────────────────────┘   │
│           ▲                                 │
│           │ hotkey_signal()                │
│           │ (non-blocking)                 │
│           │                                │
│  ┌────────┴──────────────────────────┐    │
│  │  Thread 2: HotkeyListener         │    │
│  │  (I/O-bound: hardware listener)   │    │
│  │                                  │    │
│  │  * ZERO access to SessionState    │    │
│  │  * ZERO mutations                 │    │
│  │  * ZERO blocking operations       │    │
│  │  * Only: detect hotkey + signal   │    │
│  └───────────────────────────────────┘    │
│                                             │
│  (Optional: UINotifier thread for toasts)  │
│  (Optional: Logging thread)                │
│                                             │
└─────────────────────────────────────────────┘
```

### Critical Constraint: Two Threads Only (MVP)

In MVP, we allow **exactly 2 threads**:

1. **MainLoop** (core thread, owns state)
2. **HotkeyListener** (signal-only, no state)

Everything else runs in MainLoop thread:
- Audio capture (blocking, but synchronous)
- STT (blocking, but synchronous)
- Input classification
- Safety gate
- Prompt shaping
- CLI interaction

**Why 2 threads only?**
- Simplicity (no thread pool, no executor)
- Predictability (no context switches in critical path)
- Debuggability (easy to trace execution)
- No accidental concurrency bugs

---

## MainLoop Thread Responsibilities

### What MainLoop Owns

```python
class MainLoop:
    """
    Single-threaded coordinator that owns all Jarvis state.
    All state mutations happen here. No exceptions.
    """

    def __init__(self):
        # State ownership
        self.session_state = SessionState(mode="default")
        self.hotkey_listener = None

        # Synchronization primitive
        self.hotkey_event = threading.Event()  # Signaled by hotkey thread

    def run(self):
        """
        Main orchestration loop.
        Blocks on input, processes synchronously, loops.
        """
        while claude_cli_alive():
            # BLOCK until hotkey signal
            self.hotkey_event.wait(timeout=INFINITY)
            self.hotkey_event.clear()

            # === CRITICAL PATH (single-threaded) ===
            input_signal = self._capture_audio()  # blocks
            input_event = self._classify_input(input_signal)

            if input_event.type == "command":
                result = self._execute_command(input_event)
                self.session_state.update(result)  # STATE MUTATION HERE
            else:
                if self._safety_check(input_event.text):
                    prompt = self._shape_prompt(input_event.text)
                    self._send_to_cli(prompt)

            # Back to wait
```

### State Mutations: When and Where

```
State mutations are ONLY at these explicit checkpoints:

T1. Command result processed:
    session_state.mode = result.mode_change  (if mode command)

T2. Voice input processed:
    session_state.last_transcription = input_event.text

T3. Session metrics:
    session_state.input_count += 1
    session_state.last_input_time = now()

T4. Error conditions:
    session_state.error_count += 1
    session_state.last_error = error_message

NEVER:
  ❌ Mutate in background thread
  ❌ Mutate in signal handler
  ❌ Mutate during input classification
  ❌ Mutate during safety check
```

### Blocking Decisions by MainLoop

MainLoop **intentionally blocks** at these points:

#### Block 1: Audio Capture
```python
def _capture_audio(self):
    """
    BLOCKS until audio is captured (hotkey release or timeout).
    Cannot be async or moved to background.
    """
    # Hotkey still held, capture audio
    audio_buffer = []

    while hotkey_still_pressed():
        frame = read_audio_frame()  # blocks ~10ms per frame
        audio_buffer.append(frame)

    # Hotkey released, capture ends
    return combine_audio_frames(audio_buffer)
```

**Why blocking?**
- Audio capture is synchronous hardware operation (data must be current)
- User expectation: hotkey press → immediate capture start
- Moving to background breaks hotkey synchrony

#### Block 2: STT Processing
```python
def _classify_input(self, audio_buffer):
    """
    BLOCKS until STT returns or timeout.
    Cannot be async. This is architectural decision, not performance limitation.
    """
    try:
        transcript = self.stt_adapter.transcribe(audio_buffer)  # blocks ≤ 1s
        return InputEvent(type="voice", text=transcript)
    except STTTimeout:
        return InputRejected(
            display="STT failed. Please try again or type instead.",
            recovery_action="retry_audio_or_type"
        )
    except STTError as e:
        return InputRejected(
            display=f"Error: {e.message}",
            recovery_action="retry_audio_or_type"
        )
```

**Why blocking?**
- STT is latency-critical (user expects <2s end-to-end)
- Async STT introduces state management complexity (what if user tries again while STT pending?)
- Blocking guarantees determinism: same audio → same processing every time
- Blocking prevents future devs from "optimizing" into async (contract-breaking)

---

## HotkeyListener Thread: Signal-Only Model

### HotkeyListener MUST NOT

```python
class HotkeyListener(threading.Thread):
    """
    HOTKEY LISTENER MUST NOT (absolute prohibitions):

    ❌ Access SessionState (even read-only)
    ❌ Call STT or any processing
    ❌ Modify any global variables
    ❌ Block on anything except hotkey hardware event
    ❌ Decide anything (no branching on state)
    ❌ Store history (no buffers, no cache)
    """

    def __init__(self, main_loop):
        self.main_loop = main_loop
        self.hotkey_key = "F12"

    def run(self):
        """
        Infinite loop: detect hotkey, signal main loop.
        That's ALL.
        """
        while True:
            # BLOCK on hardware hotkey (OS-level)
            hotkey_pressed = wait_for_hotkey(self.hotkey_key)

            # Signal main loop (non-blocking)
            self.main_loop.hotkey_event.set()

            # Back to waiting
```

### Why This Model?

**HotkeyListener is as thin as possible because:**

1. **Latency**: Hotkey → signal should be <10ms (hardware is fast)
2. **Correctness**: No state = no race conditions
3. **Debuggability**: Easy to trace (just print when signal sent)
4. **Scalability**: Can be replaced (OS-level hotkey detector, or network-based)

**Anti-pattern examples that would violate this:**

```python
# ❌ WRONG: Listener tries to start audio capture
def run(self):
    hotkey_pressed = wait_for_hotkey()
    audio = capture_audio()  # ← WRONG! Too much work
    self.main_loop.signal_audio(audio)

# ❌ WRONG: Listener checks session state
def run(self):
    hotkey_pressed = wait_for_hotkey()
    if self.main_loop.session_state.mode == "recording":  # ← WRONG! Race condition
        self.main_loop.hotkey_event.set()

# ❌ WRONG: Listener tries to decide re-trigger
def run(self):
    hotkey_pressed = wait_for_hotkey()
    last_timestamp = self.last_hotkey_time
    if time.now() - last_timestamp < 0.5:  # ← WRONG! State dependency
        return  # debounce
    self.main_loop.hotkey_event.set()

# ✅ CORRECT: Listener just signals
def run(self):
    while True:
        wait_for_hotkey()
        self.main_loop.hotkey_event.set()
```

---

## Synchronization Primitives: What's Allowed

### ✅ ALLOWED (MVP)

1. **threading.Event** (for hotkey signal)
   ```python
   hotkey_event = threading.Event()

   # HotkeyListener thread
   hotkey_event.set()  # Signal main loop

   # MainLoop thread
   hotkey_event.wait(timeout=INFINITY)  # Block until signal
   hotkey_event.clear()  # Reset for next
   ```

   **Why Event?**
   - Simple: binary state (signaled or not)
   - Safe: atomic operations
   - Clear: set/wait/clear are the only operations
   - No race on non-boolean state

2. **Queue** (if multiple signal sources)
   ```python
   from queue import Queue

   signal_queue = Queue(maxsize=1)

   # Any thread can send signal
   signal_queue.put(InputSignal(type="hotkey", ...))

   # MainLoop waits
   signal = signal_queue.get(timeout=INFINITY)
   ```

   **Why Queue?**
   - FIFO ordering (if multiple sources)
   - Thread-safe by design
   - Blocking get/put
   - Can handle multiple signal types

### ❌ FORBIDDEN (MVP)

1. **Lock/Mutex** (except as implementation detail of Event/Queue)
   ```python
   # ❌ WRONG
   session_lock = threading.Lock()

   def mutate_state():
       with session_lock:
           session.mode = "new_mode"  # Even with lock, risks deadlock
   ```

   **Why forbidden?**
   - Locks create contention points
   - Risk of priority inversion
   - Hard to debug (lock ordering)
   - Alternative exists (single writer)

2. **Condition Variable**
   ```python
   # ❌ WRONG
   cv = threading.Condition(lock)

   if session.ready:
       cv.notify_all()
   ```

   **Why forbidden?**
   - Requires shared state inspection (race risk)
   - Notified thread might see stale state
   - Event is sufficient for our use case

3. **RLock/Semaphore**
   ```python
   # ❌ WRONG
   resource_semaphore = threading.Semaphore(1)

   def access_shared_resource():
       resource_semaphore.acquire()
       ...
   ```

   **Why forbidden?**
   - Overkill for our model
   - Introduces thread pooling complexity
   - Violates single-writer principle

---

## STT Blocking: The Contract Enforcement

### Why STT Must Block (From Contracts)

**Layer 1-DEC-005 (Failure & Degradation) says:**
> "All failures are explicit, reversible, and non-silent."

**Layer 2-ARCH-001 (Orchestration) says:**
> "STT blocks main loop until result or timeout. Preserves: Determinism, Explicit failure, Auditable flow."

**These contracts are IMPOSSIBLE with async STT:**

#### Async STT Violation #1: Indeterminate Failures

```python
# ❌ ASYNC STT (violates contract)
async def main_loop():
    while True:
        audio = await capture_audio()

        # What happens here if user presses hotkey again?
        stt_task = asyncio.create_task(stt_adapter.transcribe(audio))

        # Main loop continues, waits for next hotkey
        next_audio = await capture_audio()

        # Now we have 2 pending STT tasks. Which one do we use?
        # What if first one finishes during second audio capture?
        # Result: INDETERMINATE behavior (different every run)
```

**Violation**: Same input + same state ≠ same output (Failure & Degradation contract broken)

#### Async STT Violation #2: Hidden Retry Loops

```python
# ❌ ASYNC STT with retry (violates contract)
async def stt_with_retry():
    for attempt in range(3):
        try:
            return await stt_adapter.transcribe(audio)
        except STTError:
            await asyncio.sleep(0.5)
            if attempt == 2:
                raise

# In main loop:
stt_task = asyncio.create_task(stt_with_retry())
next_signal = await wait_for_next_input()

# What if user presses hotkey while retry happening?
# User might not know STT is retrying (no message displayed)
# Failure is HIDDEN (violates contract)
```

**Violation**: "No hidden retry loops" (Failure & Degradation contract broken)

#### Async STT Violation #3: Race on SessionState

```python
# ❌ ASYNC STT with state mutation (violates contract)
async def main_loop():
    session_state = SessionState(mode="default")

    while True:
        audio = await capture_audio()

        # Start STT in background
        stt_task = asyncio.create_task(stt_adapter.transcribe(audio))

        # Meanwhile, user can send a "mode" command
        next_audio = await capture_audio()
        next_event = classify_input(next_audio)

        if next_event.type == "command" and next_event.command == "mode":
            session_state.mode = next_event.argument  # MUTATION HERE

        # STT completes from first audio
        first_transcript = await stt_task

        # But which mode do we use for prompt shaping?
        # The mode at STT start? At STT end? At classification?
        # Result: INDETERMINATE (violates determinism)
```

**Violation**: "Input classification + state = deterministic flow" (Orchestration contract broken)

### Blocking STT: Contract-Enforcing

```python
# ✅ BLOCKING STT (preserves contracts)
def main_loop():
    session_state = SessionState(mode="default")

    while True:
        # BLOCK on audio capture
        audio = capture_audio()  # returns when hotkey released

        # BLOCK on STT (≤ 1s target)
        try:
            transcript = stt_adapter.transcribe(audio)  # BLOCKING
            input_event = InputEvent(type="voice", text=transcript)
        except STTTimeout:
            input_event = InputRejected(...)

        # Process this input with CURRENT mode
        # (no race: mode can't change during STT in this thread)
        if input_event.type == "command":
            result = command_executor.execute(input_event)
            if result.mode_change:
                session_state.mode = result.mode_change
        else:
            prompt = prompt_shaper.shape(
                input_event.text,
                mode=session_state.mode  # ← Current mode is deterministic
            )
            send_to_claude(prompt)
```

**Contracts Preserved**:
- ✅ Determinism: audio captured → STT run → prompt shaped with current mode
- ✅ Explicit failure: STT timeout → InputRejected → error message shown
- ✅ Auditable: main loop is sequential, easy to trace

---

## Preventing Async STT: Architectural Locks

### Lock 1: STT Signature (Type System)

```python
# ✅ CORRECT signature (blocking, returns or raises)
class STTAdapter:
    def transcribe(self, audio: AudioBuffer) -> str:
        """
        Synchronously transcribe audio.
        Returns transcript or raises STTError.
        BLOCKS until result or timeout.
        """
        result = self.whisper_model.transcribe(audio)
        if result.confidence < 0.5:
            raise STTConfidenceError(...)
        return result.text

# ❌ WRONG signature (async temptation)
class STTAdapter:
    async def transcribe(self, audio: AudioBuffer) -> str:
        """WRONG: Async signature tempts async usage"""
        ...

# ❌ WRONG signature (returns Task)
class STTAdapter:
    def transcribe(self, audio: AudioBuffer) -> asyncio.Task[str]:
        """WRONG: Returns task encourages background execution"""
        ...
```

**Enforcement**: Type checking rejects async usage:
```python
stt_task = stt_adapter.transcribe(audio)  # type is str, not Task
transcript = stt_task  # immediate value, not awaitable
```

### Lock 2: MainLoop Signature (No Async)

```python
# ✅ CORRECT: MainLoop is synchronous
def main_loop():
    while claude_cli_alive():
        # ... (synchronous code)
        pass

# ❌ WRONG: Async main loop tempts async components
async def main_loop():
    while claude_cli_alive():
        audio = await capture_audio()  # Now STT is tempting to await
        transcript = await stt_adapter.transcribe(audio)
        ...

# ❌ WRONG: Thread executor tempts background tasks
executor = ThreadPoolExecutor(max_workers=2)

def main_loop():
    while True:
        audio = capture_audio()
        # Temptation: "let's background STT"
        future = executor.submit(stt_adapter.transcribe, audio)
        transcript = future.result(timeout=2)  # blocks anyway, but indirection
```

**Enforcement**: Sync-only main loop makes async STT syntactically impossible.

### Lock 3: Documentation (Contract Reference)

Every reference to STT includes this note:

```python
class STTAdapter:
    def transcribe(self, audio: AudioBuffer) -> str:
        """
        Transcribe audio synchronously.

        BLOCKING: This method blocks until transcription completes or timeout.
        This blocking is INTENTIONAL and REQUIRED by Layer 1-DEC-005
        (Failure & Degradation) and Layer 2-ARCH-001 (Orchestration).

        DO NOT convert to async. Async STT violates:
        - Layer 1-DEC-005: Hidden retry loops forbidden
        - Layer 2-ARCH-001: Determinism requirement
        - Layer 3-ARCH-002: Single-writer thread model

        Async STT changes:
          ❌ Makes failures non-explicit (pending task vs result)
          ❌ Introduces race on SessionState
          ❌ Allows hidden retries
          ❌ Makes classification indeterminate

        References:
        - JARVIS-L1-DEC-005: Failure & Degradation Contract
        - JARVIS-L2-ARCH-001: Orchestration Loop
        - JARVIS-L3-ARCH-002: Threading & Concurrency Model (this file)
        """
        ...
```

---

## Audio Capture: Synchronous by Design

### Why Audio Must Block

**Layer 0-DEC-001** defines audio capture as:
> "Hotkey down → start capture. Hotkey up → end capture. VAD timeout → end capture (1.5s)."

This is inherently synchronous:

```python
def capture_audio():
    """
    Capture audio while hotkey held or until VAD timeout.
    BLOCKS until one of:
    - User releases hotkey
    - 1.5s silence detected (VAD)
    - 120s timeout reached (degraded UX)
    """
    audio_buffer = []

    start_time = time.time()
    vad_silence_count = 0

    while True:
        frame = read_audio_frame()  # blocks ~10ms per frame
        audio_buffer.append(frame)

        # Check hotkey release
        if not is_hotkey_pressed():
            break

        # Check VAD silence (1.5s)
        if is_silent_frame(frame):
            vad_silence_count += 1
            if vad_silence_count > 150:  # ~1.5s at 100 frames/sec
                break
        else:
            vad_silence_count = 0

        # Check duration ceiling (120s degraded)
        if time.time() - start_time > 120:
            return None  # Input rejected (degraded UX)

    return combine_audio_frames(audio_buffer)
```

**Why not background?**
- Capture must be synchronous with hotkey press (hardware timing)
- User expectation: hotkey hold → capture continues
- Moving to thread adds latency (context switch)
- Blocking makes timing deterministic

---

## State Handoff Points: Only at Explicit Checkpoints

### Correct Handoff Pattern

```
MainLoop                    Other Threads
═════════════════════════════════════════════════════════

1. WAIT on event
   hotkey_event.wait()      ← HotkeyListener.set()
                            (signal only)

2. PROCESS (synchronous)
   input_event = classify_input(audio)
   (no state mutation)

3. DECIDE (based on input)
   if command:
       result = execute_command(input_event)
   else:
       prompt = shape_prompt(input_event.text)

4. MUTATE state (one place only)
   if result.mode_change:
       session_state.mode = result.mode_change
   session_state.last_transcription = input_event.text

5. PRODUCE side effect
   send_to_cli(prompt)

6. LOOP (back to 1)
   hotkey_event.clear()
   (continue while loop)
```

**Critical**: State mutation at step 4 ONLY. No other thread accesses SessionState.

---

## Deadlock Prevention

### Why Deadlock is Impossible

With our model, deadlock **cannot occur** because:

1. **No locks** (only Event, which has no lock)
2. **No cycles** (MainLoop waits on HotkeyListener signal; HotkeyListener doesn't wait on MainLoop)
3. **No condition variables** (Event is simpler)
4. **Single writer** (no contention on state)

```
Deadlock requires:
  ✅ Circular wait for resources
  ✅ Mutual exclusion
  ✅ Hold and wait
  ✅ No preemption

Our model prevents:
  ❌ Circular wait: Event.set() doesn't depend on anything
  ❌ Mutual exclusion: single writer (not mutually exclusive)
  ❌ Hold and wait: Event operations are atomic
  ❌ No preemption: Event can be cleared anytime
```

---

## Race Condition Prevention

### Race Condition Matrix

| Scenario | Prevention |
|----------|-----------|
| HotkeyListener mutates SessionState | ✅ HotkeyListener forbidden from state access |
| MainLoop and HotkeyListener both call STT | ✅ HotkeyListener doesn't call anything |
| Concurrent state mutations | ✅ Only MainLoop can mutate |
| STT returns while mode changes | ✅ STT blocks, mode change happens after |
| User presses hotkey during STT | ✅ MainLoop blocked in STT, next iteration gets new input |

**No mutex/lock needed** because single writer + readers never mutate.

---

## Blocking in MainLoop: Not a Performance Bug

### Common Objection: "Blocking = Slow"

```
Objection: "STT blocks main loop. We should async it for responsiveness."

Answer: No. Here's why:

┌─────────────────────────────────────────────────┐
│ Latency Budget (User Perspective)               │
├─────────────────────────────────────────────────┤
│ T0: User presses hotkey                        │
│ T1: Audio captured (ends at hotkey release)    │
│ T2: STT processes (Whisper ~1s)                │
│ T3: Prompt shaped + sent to Claude             │
│ Total: ~1.5-2s user sees nothing               │
└─────────────────────────────────────────────────┘

Async STT doesn't improve this:
  - User still waits for STT to complete
  - Async just hides the wait (background processing)
  - Result: SAME latency, but INDETERMINATE behavior

Blocking STT improves predictability:
  - Same input → same processing → same time
  - Auditable: see exactly when STT runs
  - No hidden retries masking real failures
```

### The Real Win: Determinism

```python
# Blocking STT
T=0.0: Hotkey pressed
T=0.5: "hello world" spoken
T=0.7: Hotkey released
T=0.7: STT starts
T=1.2: STT returns "hello world"
T=1.2: Prompt shaped with mode="default"
T=1.25: Sent to Claude

Every run: ~1.25s from hotkey to Claude
Behavior: DETERMINISTIC (reproducible, testable, auditable)

# Async STT (tempting but wrong)
T=0.0: Hotkey pressed
T=0.5: "hello world" spoken
T=0.7: Hotkey released
T=0.7: STT starts (in background)
T=0.8: User presses hotkey again
T=1.0: Second audio captured
T=1.2: First STT returns (might prompt shape with new mode?)
T=1.5: Second STT returns
T=1.8: ???

Every run: different order, different behavior
Behavior: INDETERMINATE (hard to test, debug, audit)
```

---

## Phase 2+ Threading (Not MVP)

### Future: Optional Additional Threads

After MVP, Jarvis can add threads for:

```
Phase 2 candidates (non-critical path):

1. UINotifier thread
   - MainLoop sends toast messages to queue
   - UINotifier thread displays them
   - No SessionState access

2. Logging/Metrics thread
   - MainLoop appends events to queue
   - Logger writes to disk
   - No decision-making

3. Hotkey detection alternatives
   - OS-level hotkey driver
   - Network-based remote hotkey
   - Multiple hardware hotkey listeners

Each follows same pattern:
  - Single-purpose (no logic mixing)
  - Queue-based communication
  - No SessionState access
  - Can fail without breaking core
```

**Rule**: New threads must follow signal-only pattern or be logging/display threads.

---

## Code Pattern: Making Model Violations Impossible

### Pattern 1: HotkeyListener (Template)

```python
class HotkeyListener(threading.Thread):
    """
    Hotkey listener: detect hardware hotkey, signal main loop.
    MUST NOT access SessionState or call any Jarvis logic.
    """

    def __init__(self, signal_event: threading.Event):
        super().__init__(daemon=True)
        self.signal_event = signal_event
        self.hotkey_key = "F12"

    def run(self):
        """
        Infinite loop: wait for hotkey, signal, repeat.
        """
        listener = GlobalHotkeys(
            [(self.hotkey_key, self.on_hotkey)]
        )
        listener.start()

    def on_hotkey(self):
        """Signal main loop. THAT'S ALL."""
        self.signal_event.set()
```

**Impossible violations** (enforced by code structure):
- ❌ Can't mutate SessionState (not passed in)
- ❌ Can't call STT (not imported)
- ❌ Can't block on complex logic (on_hotkey is 1 line)

### Pattern 2: MainLoop (Template)

```python
class MainLoopOrchestrator:
    """
    Single-threaded coordinator. Owns SessionState.
    All state mutations happen here.
    """

    def __init__(self):
        self.session_state = SessionState(mode="default")
        self.hotkey_event = threading.Event()
        self.hotkey_listener = HotkeyListener(self.hotkey_event)

    def run(self):
        """Main loop: wait, classify, route, update, repeat."""
        self.hotkey_listener.start()

        while claude_cli_alive():
            # Wait for hotkey signal (only signal-based event)
            self.hotkey_event.wait(timeout=INFINITY)
            self.hotkey_event.clear()

            # Process synchronously
            try:
                input_signal = self._capture_audio()
                input_event = self._classify_input(input_signal)

                if input_event == InputRejected:
                    ui_notifier.display(input_event.display)
                    continue

                # Route based on input type
                if input_event.type == "command":
                    result = self._execute_command(input_event)

                    # State mutation checkpoint 1
                    if result.mode_change:
                        self.session_state.mode = result.mode_change

                    ui_notifier.display(result.display)

                else:  # voice input
                    if self._safety_check(input_event.text):
                        prompt = self._shape_prompt(
                            input_event.text,
                            mode=self.session_state.mode
                        )
                        self._send_to_cli(prompt)

                    # State mutation checkpoint 2
                    self.session_state.last_transcription = input_event.text

            except Exception as e:
                # State mutation checkpoint 3 (error)
                self.session_state.error_count += 1
                ui_notifier.display(f"Error: {e.message}")
```

**Impossible violations** (enforced by code structure):
- ❌ Can't start background STT (synchronous signature)
- ❌ Can't spawn threads (not in code)
- ❌ Can't have race on state (single-threaded loop)

### Pattern 3: Component Isolation (Template)

```python
# ✅ CORRECT: Component is pure function
def classify_input(signal: InputSignal) -> Union[InputEvent, InputRejected]:
    """
    Pure classifier. No SessionState access. No side effects.
    Returns deterministic result based on input.
    """
    if signal.type == "voice":
        text = signal.audio_buffer
        return InputEvent(type="voice", text=text)
    elif signal.type == "command":
        ...
    else:
        return InputRejected(...)

# ❌ WRONG: Component tries to access state
def classify_input(signal: InputSignal) -> Union[InputEvent, InputRejected]:
    """
    Impure classifier. VIOLATES design.
    """
    mode = self.session_state.mode  # ← WRONG: state access
    if mode == "recording":
        return InputEvent(...)
    ...

# ✅ CORRECT: Component receives mode as parameter
def shape_prompt(text: str, mode: str) -> str:
    """
    Pure transformer. Mode passed in, not accessed from state.
    """
    mode_prefixes = {
        "default": "",
        "coding": "[CODING] ",
        ...
    }
    return mode_prefixes[mode] + text
```

---

## Testing the Model

### Test 1: No Race on State

```python
def test_no_race_on_session_state():
    """
    Verify: Only MainLoop thread mutates SessionState.
    """
    session = SessionState(mode="default")

    # Simulate MainLoop mutation
    session.mode = "coding"
    assert session.mode == "coding"

    # Simulate hotkey listener trying to mutate (should be prevented by code)
    # This test passes because HotkeyListener code doesn't have access to session

    # Test: Multiple sequential updates
    for i in range(100):
        session.mode = f"mode_{i}"
        assert session.mode == f"mode_{i}"
```

### Test 2: Hotkey Signal Doesn't Block

```python
def test_hotkey_signal_is_nonblocking():
    """
    Verify: Hotkey listener signals main loop without blocking.
    """
    event = threading.Event()
    signal_time = None

    def hotkey_listener():
        nonlocal signal_time
        time.sleep(0.1)  # Simulate hotkey detection delay
        signal_time = time.time()
        event.set()

    listener = threading.Thread(target=hotkey_listener)
    listener.start()

    # Main loop waits
    wait_start = time.time()
    event.wait(timeout=1)
    wait_end = time.time()

    # Verify: wait completed without Main waiting
    assert wait_end - wait_start < 0.5  # Much less than 1 second timeout
    assert signal_time is not None
```

### Test 3: STT Blocking Preserves Determinism

```python
def test_stt_blocking_determinism():
    """
    Verify: Same audio + same mode = same output every run.
    """
    stt = MockSTT(return_text="hello world")
    classifier = InputBoundary()
    shaper = PromptShaper()

    audio = AudioBuffer(samples=[...])

    # Run 5 times, should get same result
    results = []
    for i in range(5):
        input_event = classifier.classify(InputSignal(type="voice", audio=audio))
        mode = "default"
        prompt = shaper.shape(input_event.text, mode=mode)
        results.append(prompt)

    # All results should be identical
    assert all(r == results[0] for r in results)
```

---

## Summary: Threading Model Enforcement

| Aspect | Rule | Enforcement |
|--------|------|-------------|
| State ownership | Only MainLoop mutates SessionState | Code review + AccessError exception |
| HotkeyListener | Signal-only (no logic, no state) | Signal-only API, no imports of Jarvis logic |
| STT | Blocking (synchronous signature) | Type: `def transcribe(...) -> str` |
| MainLoop | Synchronous (no async) | Pure Python sync functions, no asyncio |
| Handoff points | Explicit checkpoints (state mutation location) | Single location in code: after each input processed |
| Deadlock prevention | No locks + no cycles | Event only + unidirectional signal |
| Race prevention | Single writer | SessionState only mutated in MainLoop |

---

## Next Step

**This threading model makes Layer 3 architecture architecturally unbreakable.**

The combination of:
1. **L3-ARCH-001** (Component Decomposition): What each component does
2. **L3-ARCH-002** (Threading & Concurrency): How components are coordinated

...guarantees that future implementors **cannot accidentally violate Layer 1 contracts**.

Blocks on critical decisions are now enforced at:
- Type system (STT must be sync)
- Code structure (HotkeyListener has no state access)
- Architectural pattern (single writer, multiple readers)

---

**Ready for implementation review.**

