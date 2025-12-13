---
description: Refactoring workflow for PROJECT_BESAR
---

# Flow E2: Refactoring

## Pre-requisites
- [ ] Sufficient test coverage
- [ ] Clear refactoring goal
- [ ] No urgent deadlines

## Steps

### 1. Analyze Code
Code smells to look for:
- [ ] Long methods (> 20 lines)
- [ ] Large classes (> 200 lines)
- [ ] Deep nesting (> 3 levels)
- [ ] Duplicate code
- [ ] God classes

### 2. Ensure Test Coverage
```bash
# Backend
pytest --cov=app --cov-report=html

# Frontend
bun test --coverage
```
Target: 80%+ coverage on code to refactor

### 3. Refactor Incrementally
1. Small, atomic changes
2. Run tests after each change
3. Commit after each step
4. Don't change behavior

### 4. Safe Refactoring Patterns
- Extract Method
- Extract Class
- Rename for clarity
- Move to appropriate location
- Replace conditionals with polymorphism

### 5. Final Verification
- [ ] All tests pass
- [ ] Coverage maintained
- [ ] Manual testing passed

## Checklist
- [ ] Code analyzed
- [ ] Test coverage sufficient
- [ ] Refactored incrementally
- [ ] All tests pass
- [ ] No behavior changes
