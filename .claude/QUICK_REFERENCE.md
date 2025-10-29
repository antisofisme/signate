# Quick Reference - Documentation Rules

## ✅ DO THIS

### Code References
```
"Updated CORS: config.py:67"
"Fixed pagination: api/content.py:123-145"
"Added schema: schemas/device.py:89"
"Migrated 15 endpoints: api/devices.py"
```

### Brief Reports
```markdown
Status: ✅ Complete
Changes: api/content.py:123, schemas/content.py:45
Results: 15/15 endpoints migrated, tests pass
Breaking: Pagination changed to page-based
Next: Update frontend
```

### Update Existing Files
```bash
# Update existing analysis
echo "## Sprint 3 Update\nStatus: Complete" >> SPRINT_COMPLETE.md

# Append to changelog
echo "- Migrated Analytics API (13 endpoints)" >> CHANGELOG.md
```

## ❌ DON'T DO THIS

### Verbose Explanations
```
❌ "I have carefully analyzed the pagination implementation
   and decided to migrate from offset-based to page-based
   approach because it provides better performance and
   aligns with modern API best practices. The implementation
   involved modifying the query parameters to accept page
   and limit instead of offset and limit..."
```

### Creating Multiple Reports
```
❌ Creating:
   - SPRINT3_DETAILED_REPORT.md
   - SPRINT3_ANALYSIS.md
   - SPRINT3_SUMMARY.md
   - MIGRATION_REPORT_FINAL.md
```

### Long Commit Messages
```
❌ git commit -m "Updated the pagination implementation by
   changing from offset-based to page-based approach which
   involved modifying query parameters and response structure..."

✅ git commit -m "Migrate pagination to page-based (api/content.py:123)"
```

## Report Examples

### Single Task Report
```markdown
## Task: Fix CORS Configuration

Status: ✅ Complete
Changes: config.py:67-73
Results: CORS working for port 8080
Breaking: None
Next: Test with viewer
```

### Multi-Agent Report
```markdown
## Sprint 3: API Standardization

Agent 1: ✅ Analytics (13) + Health (4) = 17 endpoints
Agent 2: ✅ Reports (11) + Tasks (5) = 16 endpoints
Agent 3: ✅ WebSocket (4) endpoints

Total: 181/181 (100%)
Health Score: 10.0/10
Breaking: Commands pagination, WebSocket format
Next: Frontend updates
```

### Error Report
```markdown
## Issue: Build Failed

Status: 🔴 Blocked
Error: ModuleNotFoundError at api/analytics.py:15
Cause: Missing schemas/analytics.py import
Fix: Create schemas/analytics.py with required models
Next: Implement missing schemas
```

## File Organization

### Keep Updated
```
SPRINT_COMPLETE.md       - Progress metrics
CHANGELOG.md             - Change history
API_STATUS.md            - Endpoint counts
README.md                - Setup instructions
```

### Archive Old Reports
```bash
mkdir -p docs/archive
mv SPRINT1_DETAILED_*.md docs/archive/
mv MIGRATION_REPORT_*.md docs/archive/
```

## Communication Examples

### ✅ Good Communication
```
User: "Fix the login bug"
Claude: "Analyzing login flow..."
        [reads auth files]
        "Found issue: token validation at auth.py:45"
        [fixes code]
        "Fixed: Updated token check logic"

Status: ✅
Changes: auth.py:45-52
Result: Login working
```

### ❌ Bad Communication
```
User: "Fix the login bug"
Claude: "I'll help you fix the login bug. Let me start by
        analyzing the authentication flow to understand how
        the login process works. First, I'll examine the
        authentication service file to see how tokens are
        validated. After reviewing the code, I can see that
        the issue is in the token validation logic..."
        [creates DETAILED_LOGIN_FIX_REPORT.md]
```

## Quick Checklist

Before submitting work:
- [ ] Used code references (file:line)?
- [ ] Report is brief (< 20 lines)?
- [ ] Updated existing files, not created new?
- [ ] No verbose explanations?
- [ ] Breaking changes listed?
- [ ] Next steps clear?
