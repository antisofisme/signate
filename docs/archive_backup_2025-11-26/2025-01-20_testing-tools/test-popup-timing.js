const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Capture console
  page.on('console', msg => console.log('[Browser]', msg.text()));

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  console.log('\n=== Opening Popup ===');
  const networkStatus = await page.$('#network-status');
  await networkStatus?.click();

  // Wait longer for rendering
  await page.waitForTimeout(2000);

  // Check at different intervals
  for (let i = 0; i < 5; i++) {
    await page.waitForTimeout(200);
    const state = await page.evaluate(() => {
      const container = document.getElementById('network-logs');
      const entries = container?.querySelectorAll('.log-entry');
      const count = document.getElementById('network-count')?.textContent;

      return {
        iteration: null, // Will be set below
        containerExists: !!container,
        entriesCount: entries?.length || 0,
        countText: count,
        innerHTML: container?.innerHTML.substring(0, 300)
      };
    });
    state.iteration = i + 1;
    console.log(`\nIteration ${i + 1}:`, JSON.stringify(state, null, 2));
  }

  console.log('\nKeeping open for 10 more seconds...');
  await page.waitForTimeout(10000);

  await browser.close();
})();
