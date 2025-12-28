# ENFORCEMENT STRATEGY: Architectural Guardrails

**Status**: DRAFT (Ready for team review)
**Date**: 2025-12-28
**Scope**: Operational enforcement (NOT design changes)

---

## Purpose

Define **how architectural contracts are enforced** during implementation.

This is NOT a redesign. This is **tooling to make violations impossible or obvious**.

Key principle: **Fail fast at startup. Fail PR at check-in. No silent degradation.**

---

## Three Layers of Enforcement

### Layer 1: Type System (Static Analysis)

**What it catches**: Signature violations

**Examples**:
```python
# ✅ OK (returns str)
def transcribe(audio: AudioBuffer) -> str: ...

# ❌ FAIL (returns Task)
def transcribe(audio: AudioBuffer) -> asyncio.Task[str]: ...
```

**Tools**: mypy, pyright, pylint
**Trigger**: Every commit (local), every PR (CI)
**Cost**: $0 (already have tools)
**Coverage**: ~20% of violations

---

### Layer 2: Architectural Invariant Tests (Runtime)

**What it catches**: Behavioral violations

**Examples**:
```python
# Test: STT must not be async
def test_transcribe_signature_is_not_async():
    assert not inspect.iscoroutinefunction(STTAdapter.transcribe)

# Test: Only MainLoop mutates SessionState
def test_main_loop_single_writer():
    # Verify HotkeyListener cannot access SessionState
    ...

# Test: Audio is blocking
def test_audio_capture_does_not_return_future():
    result = AudioCapture().capture(fake_audio)
    assert not asyncio.isfuture(result)
```

**Tools**: pytest (invariant test suite)
**Trigger**: Every PR (CI mandatory)
**Cost**: ~2-3 hours to write, then ~1ms per test
**Coverage**: ~60% of violations

---

### Layer 3: Code Review + ADR (Human)

**What it catches**: Architectural drift, policy violations

**Examples caught**:
- New async code path (Layer 3 tests catch it, but human understands why)
- New thread creation (violates JARVIS-L3-ARCH-002)
- State mutation outside MainLoop (violates design)
- Missing Layer reference (no excuse)

**Tools**: PR template, code review checklist, ADR gate
**Trigger**: Every PR (mandatory)
**Cost**: ~5-10 min shepherd review per PR
**Coverage**: ~99% of violations (if enforced)

---

## Enforcement Points (Where Violation is Caught)

| Violation | Caught By | Timing | Action |
|-----------|-----------|--------|--------|
| Type signature violation (async STT) | mypy | Local dev | PR rejected |
| Runtime async behavior | Invariant tests | PR check | PR rejected |
| No Layer reference | PR template | Code review | PR rejected |
| Missing ADR | Shepherd review | Code review | PR rejected |
| Threading race | Invariant tests | PR check | PR rejected |
| Silent error | Code review | Code review | PR rejected |
| Performance "optimization" | Code review | Code review | ADR required |

---

## Critical Violations (Automatic CI Rejection)

These fail CI automatically. No manual override.

1. **Type check fails** (mypy error)
2. **Invariant test fails** (pytest failure)
3. **PR template not filled** (automated check)

**Result**: PR cannot be merged. Period.

---

## Non-Critical Violations (Shepherd Review)

These caught by human code review (shepherd).

1. **Missing Layer reference** → Request clarification
2. **Design-adjacent choice** → Require ADR
3. **Performance concern** → Reference JARVIS-DEC-001
4. **Threading change** → Reference JARVIS-L3-ARCH-002

**Process**: Shepherd can reject, request changes, require ADR.

---

## CI/CD Pipeline

### Pre-commit (Local, Developer)

```bash
# Developer runs before commit
pytest tests/test_architectural_invariants.py
mypy jarvis/
```

### PR Check (Automatic)

```bash
# When PR created:
1. mypy check (type safety)
2. pytest invariant tests (architectural safety)
3. PR template validation (process compliance)
4. Grep check for known anti-patterns (async STT, etc.)
```

### Code Review (Human)

```
Shepherd checklist:
- [ ] References Layer N (0-3) or ADR
- [ ] ADR provided if new decision
- [ ] No async STT (grep + semantic check)
- [ ] No state mutations outside MainLoop
- [ ] Error handling is explicit
```

### Merge Gate

```
PR can only merge if:
- ✅ Type check passes (mypy)
- ✅ Invariant tests pass (pytest)
- ✅ PR template filled
- ✅ Shepherd approval
- ✅ No unresolved threads
```

---

## PR Template (Enforces Layer Awareness)

```markdown
# PR Description

## What changed?

[Description]

## Which Layer(s) does this touch?

- [ ] Layer 0 (Laws) — highly unlikely
- [ ] Layer 1 (Contracts) — requires ARCHLEAD approval
- [ ] Layer 2 (Orchestration) — requires ADR
- [ ] Layer 3 (Components) — most common
- [ ] None (config/tooling only)

## Architecture References

Which docs does this implementation follow?

- [ ] JARVIS-L3-ARCH-001 (components)
- [ ] JARVIS-L3-ARCH-002 (threading)
- [ ] JARVIS-L3-ARCH-003 (error handling)
- [ ] JARVIS-DEC-001 (audio pipeline)
- [ ] JARVIS-DEC-003 (command grammar)
- [ ] Other: [specify]

## ADR Provided?

- [ ] No ADR needed (implementation of locked contract)
- [ ] ADR-NNN provided (new design decision)
- [ ] ADR-NNN supersedes (existing decision changed)

## Risk Assessment

- [ ] No architectural risk
- [ ] Low risk (implementation only)
- [ ] Medium risk (adjacent to architecture)
- [ ] High risk (touches core contracts)

If medium/high: explain why and how mitigated.

---

## Checklist

- [ ] Code passes mypy (no type violations)
- [ ] Invariant tests pass (no architectural violations)
- [ ] Layer references filled above
- [ ] No async STT introduced
- [ ] No state mutations outside MainLoop
- [ ] Error messages are user-facing (not technical)
```

---

## ADR Requirements

**ADR is mandatory if**:

- New choice not in Layers 0-3 (e.g., UI framework)
- Non-trivial library selection (e.g., hotkey library)
- Implementation approach with options (e.g., audio device handling)

**ADR is optional if**:

- Direct implementation of locked contract
- Filling in skeleton with no choices
- Internal refactoring (no API/behavior change)

**ADR template**: See `docs/ADR/ADR-TEMPLATE.md`

---

## Metrics (Health Signals, Not KPIs)

**Track these monthly** to spot governance drift:

1. **PR Layer Awareness**
   - % of PRs that reference a Layer/ADR
   - Target: >90%
   - If <80%: review team discipline

2. **Invariant Test Coverage**
   - % of PRs caught by invariant tests before code review
   - Target: >50%
   - If <30%: tests need hardening

3. **ADR Usage**
   - ADRs written per month
   - Target: 2-4 per month (not zero, not excessive)
   - If zero: team skipping choices
   - If >10: too many discretionary decisions

4. **Architectural Violations**
   - PRs rejected due to architecture violation
   - Target: <5% of PRs
   - If >10%: enforcement not working
   - If 0%: team may be too conservative

---

## Important: Metrics Are SIGNALS, Not KPIs

**DO NOT** use these metrics as performance targets for developers.

**Example of WRONG usage**:
> "Developer must reference Layer in 100% of PRs"
> Result: Developers spam Layer references without understanding

**Example of RIGHT usage**:
> "If Layer references drop below 80%, team review discipline is slipping"
> Result: Shepherd conversation, team re-alignment

**Metrics track system health, not individual performance.**

---

## Responsibilities

| Role | Responsibility |
|------|-----------------|
| Developer | Read Layers 0-3 before implementation |
| Developer | Reference Layer/ADR in PR |
| Developer | Pass mypy + invariant tests before review |
| Code Reviewer | Check Layer references |
| Code Reviewer | Verify ADR provided if needed |
| Shepherd | Final gating (ensure consistency) |
| CI | Run type checks + invariant tests |

---

## Handling Violations

### Invariant Test Fails

**Response**: PR rejected, fix required.

**No exceptions.** (Invariant tests are architectural law)

---

### Code Review Finds Issue

**If minor** (style, clarity):
- Request changes, developer fixes

**If architectural** (references wrong Layer):
- Block PR, require ADR clarification
- May require redesign if touches contracts

**If policy** (missing Layer reference):
- Block PR, shepherd requests compliance

---

### Shepherd Disapproves

**Possible reasons**:
- Architecture drift (references wrong layer)
- ADR incomplete
- Performance concern (vs JARVIS-DEC-001)

**Resolution**:
1. Shepherd explains concern
2. Developer provides ADR or clarification
3. Shepherd approves or escalates

---

## Escalation Path

**If shepherd and developer disagree:**

1. Developer can request ARCHLEAD review
2. ARCHLEAD evaluates against Layers 0-3
3. Decision is final (binding)
4. Disagreement is logged (feed future ADRs)

**Default**: Shepherd decision is binding (faster iteration)

---

## Summary

**This strategy does 3 things**:

1. **Makes violations obvious** (type system + tests)
2. **Makes violations expensive** (PR rejection)
3. **Makes discipline visible** (Layer references, ADRs)

**Result**: Over time, team internalizes constraints and violations become rarer.

---

## Timeline

### Week 1: Setup
- [ ] Configure mypy/pyright in CI
- [ ] Add invariant test suite to pytest
- [ ] Update PR template
- [ ] Brief team on Layer awareness

### Week 2-4: Enforcement
- [ ] PRs rejected for mypy failures
- [ ] PRs rejected for invariant test failures
- [ ] Shepherd reviews Layer references
- [ ] First ADRs written

### Month 2+: Maturity
- [ ] Team references Layers naturally
- [ ] Fewer rejections (discipline internalized)
- [ ] ADRs become historical record
- [ ] Metrics stabilize at healthy levels

---

## FAQ

**Q: Won't this slow down development?**

A: Slightly (5-10 min shepherd review per PR). Worth it because:
- Prevents architectural debt (expensive to fix later)
- Speeds up integration (fewer surprises)
- Makes future changes easier

**Q: What if I disagree with the architecture?**

A: Write an ADR proposing the change. If ARCHLEAD approves, implement. Otherwise, follow design.

**Q: Can we add Layer 4?**

A: Only if Layers 0-3 no longer serve the architecture. Very unlikely. Ask ARCHLEAD.

**Q: What if an invariant test is too strict?**

A: Update the test + ADR explaining why. Must be approved by ARCHLEAD.

**Q: What about performance?**

A: Performance optimizations must reference JARVIS-DEC-001 (latency budget). If optimization violates SLA, rejected. If within SLA, proceed.

---

## Next Steps

1. **Review this document** (team discussion)
2. **Create files** (invariant tests, constraints, ADR template)
3. **Configure CI** (mypy, pytest, PR template)
4. **Brief team** (Layer awareness training)
5. **Enforce** (reject PRs that violate)

**Checkpoint**: After first 5 PRs, evaluate if enforcement is working.

---

**Architecture locked. Enforcement live. Implementation begins. 🔒**
