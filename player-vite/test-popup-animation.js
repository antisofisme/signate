const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => console.log('BROWSER:', msg.text()));

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'networkidle' });

  console.log('Waiting for page load...');
  await page.waitForTimeout(3000);

  console.log('\n=== Testing Factory Reset Popup ===');
  
  // Click factory reset button
  console.log('Clicking factory reset button...');
  const resetBtn = await page.$('#factory-reset-btn');
  if (resetBtn) {
    await resetBtn.click();
    console.log('✓ Factory reset button clicked');
    
    // Wait a bit for modal to start appearing
    await page.waitForTimeout(100);
    
    // Check if modal exists
    const modal = await page.$('.modal-overlay');
    if (modal) {
      console.log('✓ Modal element found');
      
      // Check initial state (should NOT have 'show' class immediately)
      const hasShowClass = await modal.evaluate(el => el.classList.contains('show'));
      console.log('Initial state - has "show" class:', hasShowClass);
      
      // Get computed opacity
      const opacity = await modal.evaluate(el => {
        return window.getComputedStyle(el).opacity;
      });
      console.log('Initial opacity:', opacity);
      
      // Wait for animation to complete
      await page.waitForTimeout(300);
      
      // Check after animation
      const hasShowClassAfter = await modal.evaluate(el => el.classList.contains('show'));
      console.log('After 300ms - has "show" class:', hasShowClassAfter);
      
      const opacityAfter = await modal.evaluate(el => {
        return window.getComputedStyle(el).opacity;
      });
      console.log('After 300ms - opacity:', opacityAfter);
      
      // Check transition property
      const transition = await modal.evaluate(el => {
        return window.getComputedStyle(el).transition;
      });
      console.log('CSS transition:', transition);
      
      if (hasShowClassAfter && opacityAfter === '1') {
        console.log('\n✅ ANIMATION WORKING! Modal fades in correctly');
      } else {
        console.log('\n❌ ANIMATION NOT WORKING! Modal appears without fade');
      }
      
      // Take screenshot
      await page.screenshot({ path: '/tmp/factory-reset-popup.png' });
      console.log('Screenshot saved to /tmp/factory-reset-popup.png');
      
    } else {
      console.log('❌ Modal not found');
    }
  } else {
    console.log('❌ Factory reset button not found');
  }

  console.log('\nWaiting 5 seconds before closing...');
  await page.waitForTimeout(5000);
  
  await browser.close();
})();
