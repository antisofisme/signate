# Claude Assistant Instructions

## 🎯 Communication Style
**TO THE POINT** - No verbose explanations, straight to facts.

## 📝 Documentation Rules

### Before Work (Analysis/Review):
- Detailed analysis allowed to prevent mistakes
- Still concise, no unnecessary context
- Focus on what needs to be done

### After Work (Reports):
**Format:**
```
Status: ✅/⚠️/🔴
Changes: file.py:123, file2.ts:45
Results: metric1: X→Y, tests: pass
Breaking: list only
Next: bullets
```

**Examples:**
```
✅ GOOD: "Updated CORS in config.py:67"
❌ BAD: "I modified the CORS configuration by adding..."
```

### Key Rules:
1. **UPDATE** existing docs, don't create new reports
2. Use **code references** (file:line) not explanations
3. **No duplicate** documentation
4. **No verbose** post-work reports

### Files to Update (not create):
- SPRINT_COMPLETE.md (update metrics)
- API_STATUS.md (update progress)
- CHANGELOG.md (append only)

### Prohibited:
- Creating DETAILED_REPORT.md files
- Long explanations of changes
- Multiple report files for same work
- Unnecessary background/context

## 🔄 Workflow
1. Analyze (concise but thorough)
2. Execute (track progress)
3. Report (brief summary only)
4. Update existing docs (don't create new)
