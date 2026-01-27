# Testing & Debugging Tools

## Overview

| Tool | Purpose | Strength |
|------|---------|----------|
| Playwright | Automated E2E testing | Multi-browser, fast |
| Chrome DevTools MCP | Deep debugging | Performance, memory |

---

## Playwright

**Installation:** `npm install playwright`
**Browser Support:** Chromium, Firefox, WebKit

### Use Cases
- Automated UI testing
- Toast notification testing
- User interaction simulation
- Screenshot & video recording

### Basic Usage

```javascript
const { chromium } = require('playwright');

async function testApp() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const page = await browser.newPage();

  // Console monitoring
  page.on('console', msg => console.log(`Console: ${msg.text()}`));

  // Navigate and test
  await page.goto('http://192.168.5.12:8080/');
  await page.waitForTimeout(5000);

  // Screenshot
  await page.screenshot({ path: '/tmp/screenshot.png' });

  await browser.close();
}

testApp();
```

### Strengths & Limitations

| Feature | Rating |
|---------|--------|
| Fast execution | ★★★★★ |
| Multi-browser | ★★★★★ |
| Automated testing | ★★★★★ |
| Console logs | ★★☆☆☆ |
| Performance profiling | ★☆☆☆☆ |
| Memory analysis | ☆☆☆☆☆ |

---

## Chrome DevTools MCP

**Installation:** `/tmp/chrome-devtools-mcp/`
**Purpose:** AI-powered deep debugging

### Use Cases
- Real-time console monitoring
- Network waterfall analysis
- Performance profiling
- Memory leak detection
- WebSocket debugging

### Usage with Playwright

```javascript
const { chromium } = require('playwright');

async function testWithDevTools() {
  const browser = await chromium.launch({
    headless: false,
    args: ['--remote-debugging-port=9222']
  });

  const page = await browser.newPage();

  // Categorized console monitoring
  const logs = { toast: [], errors: [], warnings: [] };

  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[Toast]')) logs.toast.push(text);
    if (msg.type() === 'error') logs.errors.push(text);
  });

  // Network monitoring
  page.on('response', async response => {
    const request = response.request();
    if (request.resourceType() === 'xhr') {
      console.log(`API: ${request.method()} ${request.url()} - ${response.status()}`);
    }
  });

  // Performance metrics
  const metrics = await page.evaluate(() => {
    const perf = performance.getEntriesByType('navigation')[0];
    return {
      domLoad: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
      totalTime: perf.loadEventEnd - perf.fetchStart
    };
  });

  // Memory usage
  const memory = await page.evaluate(() => ({
    usedHeap: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
    totalHeap: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
  }));

  console.log('Performance:', metrics);
  console.log('Memory:', memory);
  console.log('Console Logs:', logs);
}
```

### Strengths

| Feature | Rating |
|---------|--------|
| Console categorization | ★★★★★ |
| Network analysis | ★★★★★ |
| Performance profiling | ★★★★★ |
| Memory detection | ★★★★★ |
| Live DOM inspection | ★★★★★ |

---

## When to Use What

### Use Playwright
- CI/CD automated tests
- Multi-browser testing
- Simple UI interaction
- Screenshot/video recording

### Use Chrome DevTools MCP
- Complex issue debugging
- Performance optimization
- Memory leak investigation
- Network timing analysis
- Understanding WHY something works

### Use Both (Hybrid)
- Comprehensive testing + analysis
- Test automation + performance profiling
- Verify WHAT works + understand WHY

---

## Console Log Categorization Pattern

```javascript
const logs = {
  toast: [],
  clearCache: [],
  hardReset: [],
  shell: [],
  player: [],
  errors: [],
  warnings: []
};

page.on('console', msg => {
  const text = msg.text();
  if (text.includes('[Toast]')) logs.toast.push(text);
  if (text.includes('[ClearCache]')) logs.clearCache.push(text);
  if (text.includes('[HardReset]')) logs.hardReset.push(text);
  if (msg.type() === 'error') logs.errors.push(text);
  if (msg.type() === 'warning') logs.warnings.push(text);
});
```

---

## Performance Monitoring Pattern

```javascript
const metrics = await page.evaluate(() => {
  const perf = performance.getEntriesByType('navigation')[0];
  return {
    domLoad: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
    totalTime: perf.loadEventEnd - perf.fetchStart,
    memory: {
      used: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
      total: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
    }
  };
});
```

---

## Resources

- Playwright Docs: https://playwright.dev/
- Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp
