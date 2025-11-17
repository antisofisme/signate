# Testing Quick Reference

## Installation (First Time)

```bash
# Install all dependencies
npm install

# Install Playwright browsers
npx playwright install --with-deps
```

---

## Test Commands Cheat Sheet

### Unit Tests
```bash
npm run test:unit              # Run once with coverage
npm run test:unit:watch        # TDD mode (auto-rerun)
npm run test:unit:ui           # Visual UI debugger
```

### Integration Tests
```bash
npm run test:integration       # Run integration tests
```

### E2E Tests
```bash
npm run test:e2e              # Run all E2E tests
npm run test:e2e:ui           # Visual debugger
npm run test:e2e:debug        # Step-by-step debugger
npx playwright show-report    # View last test report
```

### Specific Tests
```bash
npm run test:performance      # Performance benchmarks
npm run test:regression       # Regression tests
```

### Full Suite
```bash
npm test                      # All tests (unit + integration + e2e)
```

---

## Common Test Patterns

### Unit Test Template
```typescript
import { describe, it, expect, beforeEach } from 'vitest';

describe('Component Name', () => {
  beforeEach(() => {
    // Setup before each test
  });

  it('should do something', () => {
    // Arrange
    const input = 'test';

    // Act
    const result = doSomething(input);

    // Assert
    expect(result).toBe('expected');
  });
});
```

### Integration Test Template
```typescript
import { describe, it, expect } from 'vitest';
import { setupMockBackend } from '../helpers/mock-backend';

describe('Integration Test', () => {
  it('should integrate components', async () => {
    const mock = setupMockBackend();
    mock.mockPlaylistResponse({ /* ... */ });

    // Test integrated behavior
    const result = await fetchAndProcess();

    expect(result).toBeDefined();
  });
});
```

### E2E Test Template
```typescript
import { test, expect } from '@playwright/test';

test('should complete user flow', async ({ page }) => {
  await page.goto('http://192.168.5.12:8080');

  // Interact with page
  await page.click('[data-testid="button"]');

  // Verify result
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

---

## Test Data Helpers

```typescript
// Create mock playlist
import { createMockPlaylist } from '../helpers/test-player';
const playlist = createMockPlaylist(3); // 3 items

// Create single item
import { createMockPlaylistItem } from '../helpers/test-player';
const item = createMockPlaylistItem({
  content: { file_path: 'video.mp4', type: 'video' }
});

// Mock backend response
import { setupMockBackend } from '../helpers/mock-backend';
const mock = setupMockBackend();
mock.mockPlaylistResponse({ playlist, has_changes: true });
```

---

## Debugging Tips

### Unit Test Not Working?
```bash
# Run specific test file
npx vitest tests/unit/your-test.test.ts

# Use UI debugger
npm run test:unit:ui
```

### E2E Test Failing?
```bash
# Run in headed mode (see browser)
npx playwright test --headed

# Run in debug mode (pause on errors)
npm run test:e2e:debug

# View last test results
npx playwright show-report
```

### Mock Not Working?
```typescript
// Check MSW server is running
beforeAll(() => server.listen());
afterAll(() => server.close());

// Log requests
server.events.on('request:start', ({ request }) => {
  console.log('Request:', request.method, request.url);
});
```

---

## Coverage Reports

```bash
# Generate coverage report
npm run test:unit

# View HTML report
open coverage/index.html          # macOS
xdg-open coverage/index.html      # Linux
start coverage/index.html         # Windows
```

---

## Test File Locations

```
tests/
├── unit/                    # Unit tests (*.test.ts)
├── integration/             # Integration tests (*.test.ts)
├── e2e/                     # E2E tests (*.spec.ts)
├── fixtures/                # Test data (JSON files)
└── helpers/                 # Utilities (test-player.ts, mock-backend.ts)
```

---

## Common Assertions

### Vitest (Unit/Integration)
```typescript
expect(value).toBe(expected)              // Strict equality (===)
expect(value).toEqual(expected)           // Deep equality
expect(value).toBeTruthy()                // Truthy value
expect(value).toBeFalsy()                 // Falsy value
expect(value).toBeNull()                  // null
expect(value).toBeUndefined()             // undefined
expect(value).toBeDefined()               // not undefined
expect(array).toContain(item)             // Array contains
expect(array).toHaveLength(3)             // Array/String length
expect(fn).toThrow()                      // Function throws
expect(fn).toThrow(/error message/)       // Throws with message
```

### Playwright (E2E)
```typescript
await expect(locator).toBeVisible()       // Element visible
await expect(locator).toBeHidden()        // Element hidden
await expect(locator).toHaveText('text')  // Text content
await expect(locator).toHaveValue('val')  // Input value
await expect(locator).toHaveCount(3)      # Count elements
await expect(page).toHaveTitle('Title')   # Page title
await expect(page).toHaveURL(/pattern/)   # URL pattern
```

---

## Performance Tips

### Keep Tests Fast
- Mock external dependencies
- Use Happy DOM (not JSDOM)
- Avoid unnecessary waits
- Parallelize when possible

### Reduce Flakiness
- Use proper waits (not timeouts)
- Add data-testid attributes
- Reset state in beforeEach
- Avoid hardcoded delays

---

## CI/CD Notes

Tests run automatically on:
- Push to main/develop/feature branches
- Pull requests

Pipeline order:
1. Unit tests (2 min)
2. Integration tests (5 min)
3. E2E tests (10 min)
4. Performance tests (15 min)

---

## Need Help?

1. Read full strategy: `TESTING_STRATEGY_VIDEOJS_MIGRATION.md`
2. Check setup guide: `TESTING_SETUP_GUIDE.md`
3. Review summary: `TEST_STRATEGY_SUMMARY.md`
4. Examine test examples in `tests/` directory
5. Consult framework docs:
   - Vitest: https://vitest.dev/
   - Playwright: https://playwright.dev/
   - MSW: https://mswjs.io/

---

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Test timeout | Increase timeout in test config |
| Element not found | Add data-testid attribute |
| Mock not working | Check MSW server is running |
| Coverage too low | Write more tests for uncovered code |
| Flaky test | Use proper waits, avoid hardcoded delays |
| Memory leak | Check cleanup in afterEach/destroy |

---

**Last Updated**: 2025-01-16
