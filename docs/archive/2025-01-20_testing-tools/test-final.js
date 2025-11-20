const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  // Disable cache completely
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

  console.log('Opening player with cache disabled...');
  await page.goto('http://192.168.5.12:8080/?bust=' + Date.now(), {
    waitUntil: 'domcontentloaded'
  });

  console.log('Waiting for page load...');
  await page.waitForTimeout(5000);

  // Check loaded JS file name
  const jsFiles = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    return scripts.map(s => s.src);
  });
  console.log('Loaded JS files:', jsFiles.filter(f => f.includes('index-')));

  console.log('\n=== Testing Factory Reset Popup ===');

  const resetBtn = await page.$('#factory-reset-btn');
  if (resetBtn) {
    await resetBtn.click();
    console.log('✓ Factory reset button clicked');

    await page.waitForSelector('.modal-overlay', { timeout: 2000 });
    await page.waitForTimeout(50);

    const modal = await page.$('.modal-overlay');
    if (modal) {
      // Check if styles were injected
      const hasStyles = await page.evaluate(() => {
        return !!document.getElementById('shared-modal-styles');
      });
      console.log('SharedModal styles injected:', hasStyles);

      const hasShowClass = await modal.evaluate(el => el.classList.contains('show'));
      const opacity = await modal.evaluate(el => window.getComputedStyle(el).opacity);

      console.log('Has "show" class:', hasShowClass);
      console.log('Opacity:', opacity);

      await page.waitForTimeout(300);

      const hasShowClassAfter = await modal.evaluate(el => el.classList.contains('show'));
      const opacityAfter = await modal.evaluate(el => window.getComputedStyle(el).opacity);

      console.log('After 300ms - has "show" class:', hasShowClassAfter);
      console.log('After 300ms - opacity:', opacityAfter);

      if (hasShowClassAfter && opacityAfter === '1' && hasStyles) {
        console.log('\n✅ ANIMATION WORKING!');
      } else {
        console.log('\n❌ ANIMATION NOT WORKING!');
        console.log('Missing:', {
          styles: !hasStyles,
          showClass: !hasShowClassAfter,
          opacity: opacityAfter !== '1'
        });
      }
    }
  }

  console.log('\nWaiting 5 seconds...');
  await page.waitForTimeout(5000);

  await browser.close();
})();
