const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

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

  console.log('\n=== Testing Close Button Functionality ===');

  const clearCacheBtn = await page.$('#clear-cache-btn');
  if (clearCacheBtn) {
    await clearCacheBtn.click();
    console.log('✓ Clear cache popup opened');

    await page.waitForSelector('.modal-overlay', { timeout: 2000 });
    await page.waitForTimeout(100);

    let modal = await page.$('.modal-overlay');
    if (modal) {
      const hasShowClass = await modal.evaluate(el => el.classList.contains('show'));
      console.log('Modal has "show" class:', hasShowClass);

      const closeBtn = await modal.$('.modal-close');
      if (closeBtn) {
        console.log('✓ Close button found');

        // Click close button
        await closeBtn.click();
        console.log('✓ Close button clicked');

        // Wait for fade out animation
        await page.waitForTimeout(300);

        // Check if modal is gone
        modal = await page.$('.modal-overlay');
        if (!modal) {
          console.log('✅ Modal removed from DOM after clicking close button');
        } else {
          const hasShowClassAfter = await modal.evaluate(el => el.classList.contains('show'));
          const opacity = await modal.evaluate(el => window.getComputedStyle(el).opacity);
          console.log('Modal still exists - has "show" class:', hasShowClassAfter);
          console.log('Modal opacity:', opacity);

          if (!hasShowClassAfter || opacity === '0') {
            console.log('✅ Modal is fading out/hidden');
          } else {
            console.log('❌ Modal still visible!');
          }
        }
      }
    }
  }

  console.log('\nWaiting 3 seconds...');
  await page.waitForTimeout(3000);

  await browser.close();
})();
