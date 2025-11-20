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

  const testPopup = async (buttonId, popupName) => {
    console.log(`\n=== Testing ${popupName} ===`);

    const btn = await page.$(buttonId);
    if (!btn) {
      console.log(`❌ ${popupName} button not found`);
      return;
    }

    await btn.click();
    console.log(`✓ ${popupName} opened`);

    await page.waitForSelector('.modal-overlay', { timeout: 2000 });
    await page.waitForTimeout(50);

    const modal = await page.$('.modal-overlay');
    if (modal) {
      // Check animation
      const hasShowClassInitial = await modal.evaluate(el => el.classList.contains('show'));
      const opacityInitial = await modal.evaluate(el => window.getComputedStyle(el).opacity);

      await page.waitForTimeout(250);

      const hasShowClass = await modal.evaluate(el => el.classList.contains('show'));
      const opacity = await modal.evaluate(el => window.getComputedStyle(el).opacity);

      // Check close button
      const closeBtn = await modal.$('.modal-close');

      // Check z-index
      const zIndex = await modal.evaluate(el => window.getComputedStyle(el).zIndex);

      console.log('Animation:', {
        hasShowClass: hasShowClass,
        opacity: opacity,
        zIndex: zIndex
      });

      console.log('Close button:', closeBtn ? '✅ Present' : '❌ Missing');

      if (hasShowClass && parseFloat(opacity) > 0.9 && closeBtn && zIndex === '200000') {
        console.log(`✅ ${popupName} is CONSISTENT!`);
      } else {
        console.log(`❌ ${popupName} has issues:`, {
          animation: !hasShowClass || parseFloat(opacity) <= 0.9,
          closeButton: !closeBtn,
          zIndex: zIndex !== '200000'
        });
      }

      // Close modal
      if (closeBtn) {
        await closeBtn.click();
        await page.waitForTimeout(300);
      } else {
        // Press Escape to close
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
      }
    }
  };

  await testPopup('#device-info-btn', 'Device Info Popup');
  await testPopup('#connection-log-btn', 'Connection Log Popup');
  await testPopup('#factory-reset-btn', 'Factory Reset Popup');
  await testPopup('#clear-cache-btn', 'Clear Cache Popup');

  console.log('\n=== Summary ===');
  console.log('All popups should have:');
  console.log('✅ Fade-in animation (opacity 0 → 1)');
  console.log('✅ Close X button');
  console.log('✅ Z-index: 200000');
  console.log('✅ "show" class added after mount');

  console.log('\nWaiting 3 seconds...');
  await page.waitForTimeout(3000);

  await browser.close();
})();
