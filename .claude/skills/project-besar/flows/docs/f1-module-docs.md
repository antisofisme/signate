---
description: Update module documentation for PROJECT_BESAR
---

# Flow F1: Update Module Documentation

## Required Documents
```
modules/{module}/docs/
├── README.md       # Overview, quick start
├── ARCHITECTURE.md # Design decisions
├── API.md          # Endpoint reference
├── DATABASE.md     # Schema reference
└── CHANGELOG.md    # Version history
```

## Steps

### 1. Audit Existing Docs
- [ ] README.md current?
- [ ] ARCHITECTURE.md reflects design?
- [ ] API.md has all endpoints?
- [ ] DATABASE.md has all tables?
- [ ] CHANGELOG.md updated?

### 2. Update Documentation

**README.md Template**
```markdown
# {Module} Module

## Overview
[Brief description]

## Quick Start
\`\`\`bash
cd modules/{module}/backend && uvicorn app.main:app --reload
cd modules/{module}/frontend && bun dev
\`\`\`

## Features
- Feature 1
- Feature 2

## Dependencies
- Platform Auth
- Redis
```

### 3. Validate
- [ ] Links work
- [ ] Code examples run
- [ ] All sections present

## Checklist
- [ ] All docs audited
- [ ] Gaps filled
- [ ] Links verified
- [ ] Examples tested
