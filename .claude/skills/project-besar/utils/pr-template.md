---
description: Pull Request template for PROJECT_BESAR
---

# Pull Request Template

## Template
```markdown
## Summary
<!-- Jelaskan perubahan secara singkat -->

## Type
- [ ] Feature baru
- [ ] Bug fix
- [ ] Refactor
- [ ] Performance improvement
- [ ] Documentation
- [ ] Test

## Changes
<!-- List perubahan utama -->
-

## Testing
<!-- Bagaimana cara test perubahan ini -->
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing done

## Checklist
- [ ] Code follows project standards
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] tenant_id filter checked (if DB related)

## Screenshots
<!-- Jika ada UI changes -->

## Related Issues
<!-- Link ke issue terkait -->
Closes #
```

## Branch Naming
```
feature/PB-123-short-description
bugfix/PB-123-short-description
hotfix/PB-123-critical-fix
refactor/PB-123-short-description
```

## Commit Message Format
```
type(scope): description

feat(pms): add reservation calendar view
fix(auth): resolve token refresh issue
refactor(api): simplify error handling
docs(readme): update installation steps
test(pos): add order service tests
```
