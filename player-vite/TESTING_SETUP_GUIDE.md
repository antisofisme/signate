# Testing Setup Guide: Video.js Migration

## Quick Start

This guide helps you set up the comprehensive testing infrastructure for the Video.js migration in the digital signage player.

---

## Installation

### 1. Install Test Dependencies

```bash
cd /mnt/g/khoirul/signate/player-vite

# Install all testing dependencies
npm install --save-dev \
  vitest@^1.0.0 \
  @vitest/ui@^1.0.0 \
  @vitest/coverage-v8@^1.0.0 \
  @playwright/test@^1.40.0 \
  @testing-library/dom@^9.3.3 \
  happy-dom@^12.10.3 \
  msw@^2.0.0
```

### 2. Install Playwright Browsers

```bash
# Install Playwright browsers (Chromium, Firefox, WebKit)
npx playwright install --with-deps
```

---

## Available Test Commands

### Unit Tests (Vitest)

```bash
# Run all unit tests
npm run test:unit

# Run unit tests in watch mode (TDD)
npm run test:unit:watch

# Run unit tests with UI
npm run test:unit:ui

# Run unit tests with coverage report
npm run test:unit
```

### Integration Tests (Vitest + MSW)

```bash
# Run integration tests
npm run test:integration
```

### End-to-End Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI mode (visual debugger)
npm run test:e2e:ui

# Run E2E tests in debug mode
npm run test:e2e:debug

# Run performance tests only
npm run test:performance

# Run regression tests only
npm run test:regression
```

### Full Test Suite

```bash
# Run all tests (unit + integration + e2e)
npm test
```

---

## Directory Structure

After setup, your test directory will look like this:

```
player-vite/
├── tests/
│   ├── unit/                           # Unit tests (Vitest)
│   │   └── player-hls-initialization.test.ts
│   ├── integration/                    # Integration tests
│   │   └── (to be implemented)
│   ├── e2e/                            # E2E tests (Playwright)
│   │   ├── helpers.ts
│   │   └── sample-critical-path.spec.ts
│   ├── fixtures/                       # Test data
│   │   └── playlists/
│   ├── helpers/                        # Test utilities
│   │   ├── test-player.ts
│   │   └── mock-backend.ts
│   ├── setup.ts                        # Vitest global setup
│   └── integration-setup.ts            # MSW setup for integration tests
├── vitest.config.ts                    # Vitest configuration
├── vitest.integration.config.ts        # Integration test config
├── playwright.config.ts                # Playwright configuration
└── TESTING_STRATEGY_VIDEOJS_MIGRATION.md
```

---

## Configuration Files

### 1. Vitest Config (`vitest.config.ts`)

Configures unit tests with:
- Happy DOM environment (fast, lightweight)
- Path aliases (@player, @shell, @shared)
- Coverage thresholds (85%+ target)
- Global test setup

### 2. Playwright Config (`playwright.config.ts`)

Configures E2E tests with:
- Multi-browser support (Chromium, Firefox, WebKit)
- WebOS TV emulation
- Screenshot/video on failure
- Test retries in CI
- HTML/JUnit/JSON reporters

### 3. Test Setup Files

- `tests/setup.ts`: Global mocks (localStorage, matchMedia, IntersectionObserver)
- `tests/integration-setup.ts`: MSW server for API mocking

---

## Writing Tests

### Unit Test Example

**File**: `tests/unit/player-hls.test.ts`

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { PlayerHLS } from '@player/services/player-hls';
import { createTestVideoElement } from '../helpers/test-player';

describe('PlayerHLS', () => {
  let videoElement: HTMLVideoElement;

  beforeEach(() => {
    videoElement = createTestVideoElement();
    PlayerHLS.destroy(); // Reset singleton
  });

  it('should initialize without errors', () => {
    expect(() => PlayerHLS.init(videoElement)).not.toThrow();
  });

  it('should prevent double initialization', () => {
    PlayerHLS.init(videoElement);
    expect(() => PlayerHLS.init(videoElement)).toThrow(/already initialized/);
  });
});
```

### Integration Test Example

**File**: `tests/integration/playlist-sync.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { setupMockBackend } from '../helpers/mock-backend';
import { PlayerPlaylistSync } from '@player/services/player-playlist-sync';

describe('Playlist Sync Integration', () => {
  it('should sync playlist from backend', async () => {
    const mockBackend = setupMockBackend();

    mockBackend.mockPlaylistResponse({
      playlist: { id: 1, name: 'Test', is_active: true, items: [] },
      has_changes: true,
    });

    const result = await PlayerPlaylistSync.syncNow();
    expect(result).toBe(true);
  });
});
```

### E2E Test Example

**File**: `tests/e2e/critical-path.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { activateDevice, waitForPlayback } from './helpers';

test('should complete activation and playback', async ({ page }) => {
  await page.goto('http://192.168.5.12:8080');
  await activateDevice(page);
  await waitForPlayback(page);

  const video = page.locator('video');
  const isPlaying = await video.evaluate((v: HTMLVideoElement) =>
    !v.paused && v.currentTime > 0
  );

  expect(isPlaying).toBe(true);
});
```

---

## Test Data Fixtures

### Create Test Playlists

**File**: `tests/fixtures/playlists/mixed-content.json`

```json
{
  "id": 1,
  "name": "Mixed Content",
  "is_active": true,
  "items": [
    {
      "id": 1,
      "content_id": 101,
      "duration": 15,
      "order": 0,
      "content": {
        "id": 101,
        "name": "Video",
        "type": "video",
        "file_path": "http://192.168.5.12:8001/uploads/videos/test.mp4",
        "url": null,
        "thumbnail_path": null,
        "metadata": null
      }
    }
  ]
}
```

---

## Running Tests in CI/CD

### GitHub Actions Integration

Tests automatically run on:
- Push to `main`, `develop`, `feature/*` branches
- Pull requests

**Workflow**:
1. Unit tests (with coverage upload to Codecov)
2. Integration tests
3. E2E tests (with artifact uploads)
4. Performance tests

---

## Coverage Reports

After running `npm run test:unit`, coverage reports are generated:

```
coverage/
├── index.html          # HTML report (open in browser)
├── coverage.json       # JSON data
└── lcov.info          # LCOV format (for CI tools)
```

Open coverage report:
```bash
open coverage/index.html  # macOS
xdg-open coverage/index.html  # Linux
```

---

## Debugging Tests

### Unit Tests

```bash
# Run specific test file
npx vitest tests/unit/player-hls.test.ts

# Run with debugger
npm run test:debug

# Use Vitest UI (visual debugger)
npm run test:unit:ui
```

### E2E Tests

```bash
# Run specific test file
npx playwright test tests/e2e/critical-path.spec.ts

# Run with UI mode (visual debugger)
npm run test:e2e:ui

# Run in debug mode (step through)
npm run test:e2e:debug

# View last test report
npx playwright show-report
```

---

## Test Development Workflow (TDD)

### 1. Write Failing Test First

```typescript
it('should play HLS content', async () => {
  const playlist = createMockPlaylist(1, {
    content: { file_path: 'stream.m3u8', type: 'video' }
  });

  await PlayerHLS.loadPlaylist(playlist);

  // This will fail initially
  expect(PlayerHLS.getState().isPlaying).toBe(true);
});
```

### 2. Run Test (It Should Fail)

```bash
npm run test:unit:watch
```

### 3. Implement Minimal Code

Implement just enough code to make the test pass.

### 4. Verify Test Passes

Watch mode automatically reruns - test should turn green.

### 5. Refactor

Clean up implementation while keeping test green.

---

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use `beforeEach` to reset state
- Clean up after tests (destroy singletons, clear timers)

### 2. Mock External Dependencies
- Use MSW for API mocking (integration tests)
- Mock browser APIs (localStorage, matchMedia)
- Avoid real network calls in unit tests

### 3. Descriptive Test Names
```typescript
// Good
it('should prevent PlayerHLS usage before initialization')

// Bad
it('should work')
```

### 4. Arrange-Act-Assert Pattern
```typescript
it('should load playlist', async () => {
  // Arrange
  const playlist = createMockPlaylist(3);
  PlayerHLS.init(videoElement);

  // Act
  await PlayerHLS.loadPlaylist(playlist);

  // Assert
  expect(PlayerHLS.getState().playlist).toEqual(playlist);
});
```

### 5. Test Edge Cases
- Empty playlists
- Network failures
- Race conditions
- Invalid input
- Memory leaks

---

## Troubleshooting

### Issue: Tests Timeout

**Solution**: Increase timeout in test or config
```typescript
it('slow test', async () => {
  // ...
}, { timeout: 30000 }); // 30 seconds
```

### Issue: Playwright Cannot Find Elements

**Solution**: Add test IDs to components
```typescript
<div data-testid="activation-screen">...</div>
```

### Issue: MSW Not Intercepting Requests

**Solution**: Verify server is started in `beforeAll`
```typescript
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});
```

### Issue: Coverage Not Generated

**Solution**: Run with coverage flag
```bash
npm run test:unit -- --coverage
```

---

## Next Steps

1. Install dependencies: `npm install`
2. Install Playwright browsers: `npx playwright install --with-deps`
3. Run sample tests: `npm run test:unit`
4. Implement Video.js migration
5. Write comprehensive tests following strategy document
6. Achieve 85%+ coverage
7. Run full test suite before deployment

---

## Resources

- **Testing Strategy**: `TESTING_STRATEGY_VIDEOJS_MIGRATION.md`
- **Vitest Docs**: https://vitest.dev/
- **Playwright Docs**: https://playwright.dev/
- **MSW Docs**: https://mswjs.io/
- **Testing Library**: https://testing-library.com/

---

## Support

For questions or issues:
1. Review testing strategy document
2. Check test examples in `tests/` directory
3. Consult Vitest/Playwright documentation
4. Review CI/CD workflow in `.github/workflows/test.yml`

Happy Testing!
