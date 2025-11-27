# Pattern Inconsistency Matrix - Visual Reference

## Detailed Comparison Table

```
╔════════════════╦═════════════════╦═════════════╦════════════╦════════════╦═════════════╦═════════╗
║    PATTERN     ║  ORGANIZATIONS  ║   DEVICES   ║  CONTENTS  ║ PLAYLISTS  ║  SCHEDULES  ║  MENUS  ║
║                ║   (Standard)    ║  (Business) ║(Business)  ║ (Business) ║ (Business)  ║(Business)║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Error Handler  ║ handleAPIError()║getApiError  ║getApiError ║getApiError ║getApiError  ║getApiErr║
║                ║     ✅          ║getMessage() ║getMessage()║getMessage()║getMessage() ║Message()║
║                ║                 ║     ❌      ║     ❌     ║     ❌     ║     ❌      ║    ❌   ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Toast Library  ║@/lib/notifications║  sonner   ║  sonner    ║  sonner    ║  sonner     ║ sonner  ║
║                ║   /toast        ║     ❌      ║     ❌     ║     ❌     ║     ❌      ║    ❌   ║
║                ║     ✅          ║             ║            ║            ║             ║         ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Query Key      ║ Complete Factory║ Complete   ║  Partial   ║ Complete   ║   NONE      ║Complete ║
║ Factory        ║     ✅          ║  Factory   ║  Factory   ║   ✅       ║     ❌      ║   ✅    ║
║                ║                 ║ + Inline   ║            ║            ║             ║         ║
║                ║                 ║  (mixed)   ║            ║            ║             ║         ║
║                ║                 ║     ⚠️     ║     ⚠️     ║            ║             ║         ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ API Pattern    ║ API Object      ║ API Object ║  Functions ║ API Object ║  Mixed      ║ API Obj ║
║ (organizationsApi║  ✅            ║(deviceApi) ║(getContent,║(playlistApi║(scheduleApi ║(menuApi)║
║                ║                 ║     ✅     ║ uploadCont ║    ✅      ║+ advanced)  ║   ✅    ║
║                ║                 ║            ║)    ❌     ║            ║      ⚠️     ║         ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Response       ║ Standard unwrap ║Custom unwrap║ Direct     ║ Standard   ║ Standard    ║Standard ║
║ Handling       ║ (data directly) ║ Function   ║ response.  ║ unwrap     ║ unwrap      ║ unwrap  ║
║                ║     ✅          ║   (non-std)║ data       ║    ✅      ║     ✅      ║    ✅   ║
║                ║                 ║     ⚠️     ║     ❌     ║            ║             ║         ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Optimistic     ║ Limited         ║ YES (delete)║   NO       ║   NO       ║   NO        ║   NO    ║
║ Updates        ║    ⚠️           ║     ✅     ║     ❌     ║     ❌     ║     ❌      ║    ❌   ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Cache          ║ Standardized    ║   Good     ║   Good     ║   Good     ║   Good      ║ Limited ║
║ Invalidation   ║     ✅          ║     ✅     ║     ✅     ║     ✅     ║     ✅      ║    ⚠️   ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ File Structure ║ Consolidated    ║ Over-split ║ Consolidated║Consolidated║  Split     ║  Split  ║
║                ║(1 api, 1 hook, ║ (6 api,    ║ (1 api,    ║(1 api,     ║(2 api,     ║(1 api,  ║
║                ║ 1 type file)   ║ 5 hook,    ║ 1 hook,    ║1 hook,     ║2 hook,     ║3 hooks) ║
║                ║     ✅          ║ 7 types)   ║ 1 type)    ║1 type)     ║2 types)    ║    ⚠️   ║
║                ║                 ║     ❌     ║     ✅     ║    ✅      ║     ⚠️     ║         ║
╠════════════════╬═════════════════╬═════════════╬════════════╬════════════╬═════════════╬═════════╣
║ Translation    ║ Full coverage   ║  Partial   ║  Partial   ║  Partial   ║  Partial    ║ Partial ║
║ Keys           ║     ✅          ║     ⚠️     ║     ⚠️     ║     ⚠️     ║     ⚠️      ║    ⚠️   ║
║                ║                 ║ (46 files) ║            ║            ║             ║         ║
╚════════════════╩═════════════════╩═════════════╩════════════╩════════════╩═════════════╩═════════╝
```

## Summary Statistics

### By Pattern Category

| Category | Issues | Severity | Effort |
|----------|--------|----------|--------|
| Error Handler | 5 features | HIGH | 1-2 hours |
| Toast Library | 5 features | HIGH | 30 mins |
| API Pattern | 1 feature | HIGH | 1 hour |
| Query Keys | 2 features | MEDIUM-HIGH | 2-3 hours |
| File Structure | 3 features | MEDIUM | 4-5 hours |
| Translations | 5 features | LOW | 2-3 hours |

### Scoring Summary

**Legend**: ✅ (Compliant) | ⚠️ (Partial/Mixed) | ❌ (Non-compliant)

| Feature | Score | Status | Priority |
|---------|-------|--------|----------|
| Organizations | 7/7 | ✅ Reference | - |
| Tags | 6/7 | ✅ Good | LOW |
| Devices | 3/7 | ⚠️ Mixed | HIGH |
| Contents | 4/7 | ⚠️ Mixed | HIGH |
| Playlists | 5/7 | ⚠️ Partial | MEDIUM |
| Schedules | 3/7 | ⚠️ Mixed | HIGH |
| Menus | 4/7 | ⚠️ Partial | MEDIUM |

---

## Critical Issues by Severity

### CRITICAL (Block Development)
1. **Error Handler Mismatch** - 2 different error handler utilities
2. **Toast Library Mismatch** - 2 different toast imports
3. **Contents API Pattern** - Violates established pattern

### HIGH (Breaks Consistency)
4. **Schedules Query Keys** - No factory pattern
5. **Devices Mixed Keys** - Hybrid factory/inline pattern

### MEDIUM (Maintainability)
6. **Devices Over-split** - 18 files instead of 3
7. **Translation Coverage** - Inconsistent localization

---

## Impact Assessment

### If Left Unfixed:
- New developers need to learn 2+ ways of doing the same thing
- Code review takes longer (inconsistent patterns)
- Refactoring is harder (scattered patterns)
- Testing becomes complex (mixed error handling)
- Maintenance burden increases

### If Fixed (Phase 1):
- Single source of truth for each pattern
- Easier onboarding
- Faster code reviews
- More predictable behavior
- Lower maintenance cost

---

## Next Steps

1. **Read full report**: `PATTERN_CONSISTENCY_ANALYSIS.md`
2. **Reference quick summary**: `PATTERN_CONSISTENCY_QUICK_SUMMARY.md`
3. **Use this matrix**: For quick visual comparison
4. **Implement Phase 1**: Critical fixes (2-3 hours)
5. **Plan Phase 2-3**: Additional improvements (6-8 hours)

