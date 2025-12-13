---
description: Bug fix workflow for PROJECT_BESAR
---

# Flow E1: Bug Fix

## Steps

### 1. Reproduce Bug
- [ ] Steps to reproduce documented
- [ ] Expected vs actual behavior
- [ ] Environment details

### 2. Root Cause Analysis
- [ ] Identify affected code
- [ ] Understand why it happens
- [ ] Assess impact

### 3. Write Failing Test
```python
def test_should_not_crash_when_empty_input():
    """Regression test for Bug #XXX"""
    result = service.process([])
    assert result == []  # Should not raise
```

### 4. Implement Fix
- [ ] Minimal changes only
- [ ] Don't change other behavior
- [ ] Add defensive code

### 5. Verify Fix
- [ ] Regression test passes
- [ ] Existing tests pass
- [ ] Manual verification

## Bug Report Template
```markdown
## Bug
[Description]

## Steps to Reproduce
1. ...
2. ...

## Expected
[What should happen]

## Actual
[What happens]

## Root Cause
[Why it happens]

## Fix
[What was changed]
```

## Checklist
- [ ] Bug reproduced
- [ ] Root cause identified
- [ ] Regression test added
- [ ] Fix implemented
- [ ] All tests pass
