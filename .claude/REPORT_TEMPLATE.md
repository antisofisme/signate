# Report Template - TO THE POINT

## Work: [Task Name]

**Status:** ✅ Complete / ⚠️ Issues / 🔴 Blocked

**Changes:**
- Modified: `file1.py:45-67`, `file2.ts:123`
- Added: `file3.py` (200 lines)
- Deleted: `old_file.js`

**Results:**
- Metric 1: X → Y
- Metric 2: A → B
- Tests: 45/45 passing
- Build: ✅ Success

**Breaking Changes:**
- API endpoint: `/old` → `/new`
- Response format: `{old}` → `{new}`
- Config: `OLD_VAR` → `NEW_VAR`

**Next:**
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

---

## Code Reference Examples

### ✅ GOOD
```
"Updated pagination in api/content.py:123-145"
"Fixed CORS in config.py:67"
"Added validation schema.py:89"
"Migrated 15 endpoints: api/devices.py:45-234"
```

### ❌ BAD
```
"I updated the pagination logic by changing the offset-based
approach to page-based approach in the content API file, which
involved modifying the query parameters and updating the response
structure to include page metadata, total counts, and navigation
links for better frontend integration..."
```

---

## Multi-Agent Report Format

### Agent 1: [Name]
**Status:** ✅ Complete
**Changes:** `file1.py:45`, `file2.py:67`
**Result:** 15/15 endpoints migrated

### Agent 2: [Name]
**Status:** ✅ Complete
**Changes:** `file3.ts:123`, `file4.tsx:89`
**Result:** 12/12 components updated

### Agent 3: [Name]
**Status:** ⚠️ Issues
**Changes:** `file5.py:234`
**Result:** 8/10 tests passing
**Blocker:** Missing dependency X

---

## Update Existing Files (Don't Create New)

### Files to Update:
- `SPRINT_COMPLETE.md` - Update progress metrics
- `API_STATUS.md` - Update endpoint counts
- `CHANGELOG.md` - Append new entries
- `README.md` - Update setup instructions if needed

### DON'T Create:
- `SPRINT_DETAILED_REPORT.md`
- `WORK_SUMMARY_[DATE].md`
- `MIGRATION_ANALYSIS_V2.md`
- `FINAL_REPORT.md`
