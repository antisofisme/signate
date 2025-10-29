# .claude Configuration

## Files

### `settings.local.json`
Permissions configuration for Claude Code.

### `instructions.md`
Core instructions for Claude Assistant behavior:
- Communication style: TO THE POINT
- Documentation rules
- Report format

### `REPORT_TEMPLATE.md`
Template for creating concise reports.

## Quick Reference

### Before Work:
- Analyze (detailed but concise)
- Identify what needs to be done
- No unnecessary context

### During Work:
- Execute tasks
- Track progress
- Update existing docs

### After Work:
Report format:
```
Status: ✅
Changes: file.py:123
Results: X→Y
Breaking: list
Next: bullets
```

## Key Rules
1. ✅ UPDATE existing docs
2. ✅ Use code references (file:line)
3. ❌ NO verbose reports
4. ❌ NO duplicate documentation
