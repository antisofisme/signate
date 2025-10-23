---
name: signage-refactor
description: Modular refactoring guidelines and best practices for Smart TV Signage project. Use for refactoring large components, adding features, debugging, and maintaining code quality.
type: guideline
version: 1.0.0
tags:
  - refactoring
  - react
  - modular-architecture
  - code-quality
  - web-admin
---

# Smart TV Signage - Modular Refactoring Skill

## When to Activate This Skill

Invoke this skill when you need to:

1. **Refactor monolithic components** (>500 lines)
2. **Add new features** following project standards
3. **Debug systematically** using project guidelines
4. **Review code quality** against standards
5. **Maintain consistency** across the codebase

## Quick Start Commands

```
Use signage-refactor skill to refactor [ComponentName]
Use signage-refactor skill to add [feature] following standards
Use signage-refactor skill debugging checklist for [issue]
```

## What This Skill Provides

### 📐 Architecture Standards
- Directory structure for web-admin
- Component organization patterns
- File size limits and guidelines
- Naming conventions

### 🔧 Design Principles
- Single Responsibility Principle
- Component Composition patterns
- Separation of Concerns
- DRY principles

### 🔄 Refactoring Workflow
- Step-by-step extraction process
- Component templates
- Hook templates
- Modal templates

### ✅ Quality Checklist
- Pre-commit checklist
- Component quality standards
- Hook quality standards
- Testing guidelines

### 🐛 Debugging Guidelines
- API troubleshooting
- Component debugging
- State management issues
- Common pitfalls to avoid

### 📦 Component Templates
- Page container template
- UI component template
- Modal component template
- Custom hook template

## Implementation Phases

1. **Infrastructure** (2h) - Setup folders, base components
2. **Common Logic** (2h) - Extract hooks, API layer
3. **Refactor Content** (6h) - Break down 2142-line component
4. **Refactor Devices** (4h) - Modularize device management
5. **Testing & Polish** (2h) - Integration testing, cleanup

**Total: 16 hours (2-3 days)**

## Key Metrics

### Before Refactoring
- Content.jsx: 2,142 lines ❌
- Devices.jsx: 725 lines ⚠️
- Maintainability: Low
- Testability: Difficult

### After Refactoring
- All files: <250 lines ✅
- Maintainability: High ⬆️ 500%
- Reusability: High ⬆️ 300%
- Testability: Excellent ⬆️ 400%

## Quick Reference

### File Size Limits
- Pages: 150-250 lines
- Components: 100-200 lines
- Modals: 150-300 lines
- Hooks: 100-250 lines

### Component Hierarchy
```
Page Container (data coordination)
  ├── Grid/List Component (layout)
  │   └── Card Component (item display)
  ├── Filter Component (user input)
  └── Modal Components (actions)
```

### Import Order
1. React imports
2. Third-party libraries
3. Internal (absolute paths)
4. Relative (same directory)

## Full Documentation

See complete guidelines in: `.claude/skills/signage-refactor.md`

---

**Version:** 1.0.0
**Last Updated:** 2025-10-23
**Project:** Smart TV Digital Signage System
