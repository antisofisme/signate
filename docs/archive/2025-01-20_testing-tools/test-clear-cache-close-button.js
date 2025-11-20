const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Disable cache
  await context.route('**/*', (route) => {
    route.continue({
      headers: {
        ...route.request().headers(),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  });

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/?bust=' + Date.now(), {
    waitUntil: 'domcontentloaded'
  });

  await page.waitForTimeout(3000);

  console.log('\n=== Testing Clear Cache Popup ===');

  // Click clear cache button
  const clearCacheBtn = await page.$('#clear-cache-btn');
  if (clearCacheBtn) {
    await clearCacheBtn.click();
    console.log('✓ Clear cache button clicked');

    await page.waitForSelector('.modal-overlay', { timeout: 2000 });
    await page.waitForTimeout(100);

    const modal = await page.$('.modal-overlay');
    if (modal) {
      // Check if close button exists
      const closeBtn = await modal.$('.modal-close');

      if (closeBtn) {
        console.log('✅ Close X button found!');

        // Check if it's visible
        const isVisible = await closeBtn.isVisible();
        console.log('Close button visible:', isVisible);

        // Get button text
        const btnText = await closeBtn.textContent();
        console.log('Button text:', btnText);

        // Check positioning
        const position = await closeBtn.evaluate(el => {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);
          return {
            top: styles.top,
            right: styles.right,
            position: styles.position
          };
        });
        console.log('Button position:', position);

        console.log('\n✅ CLEAR CACHE POPUP NOW HAS CLOSE BUTTON!');
      } else {
        console.log('❌ Close button NOT found!');
      }
    }
  }

  console.log('\nWaiting 5 seconds...');
  await page.waitForTimeout(5000);

  await browser.close();
})();
