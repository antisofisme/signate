const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Capture console logs
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('ConnectionLogger') || text.includes('ConnectionLogStorage')) {
      console.log('[Browser Console]', text);
    }
  });

  // Capture errors
  page.on('pageerror', error => {
    console.log('[Browser Error]', error.message);
  });

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  
  console.log('Waiting for initialization...');
  await page.waitForTimeout(5000);

  console.log('\n=== Checking ConnectionLogger State ===');
  
  const state = await page.evaluate(async () => {
    const result = {
      loggerExists: typeof window.ConnectionLogger !== 'undefined',
      storageExists: false,
      dbOpen: false,
      error: null
    };

    if (!window.ConnectionLogger) return result;

    try {
      // Try to access internal storage
      const count = await window.ConnectionLogger.getCount();
      result.storageExists = true;
      result.dbCount = count;

      // Try to add a test log
      await window.ConnectionLogger.log({
        eventType: 'network',
        status: 'online',
        latencyMs: 50
      });

      // Wait a bit
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Check if it was saved
      const newCount = await window.ConnectionLogger.getCount();
      result.afterAddCount = newCount;
      result.added = newCount > count;

    } catch (error) {
      result.error = error.message;
    }

    return result;
  });

  console.log('\nConnectionLogger State:');
  console.log(JSON.stringify(state, null, 2));

  console.log('\nWaiting 10 seconds for manual inspection...');
  await page.waitForTimeout(10000);

  await browser.close();
})();
