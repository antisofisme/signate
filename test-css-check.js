const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/?nocache=' + Date.now(), { waitUntil: 'domcontentloaded' });

  console.log('Waiting for page load...');
  await page.waitForTimeout(5000);

  console.log('\n=== Checking CSS Styles ===');

  // Check if style tag exists
  const styleExists = await page.$('#shared-modal-styles');
  console.log('SharedModal styles exist:', !!styleExists);

  if (styleExists) {
    const cssContent = await page.evaluate(() => {
      const style = document.getElementById('shared-modal-styles');
      return style ? style.textContent : null;
    });

    // Check specific CSS rules
    const hasOpacity0 = cssContent && cssContent.includes('opacity: 0');
    const hasVisibilityHidden = cssContent && cssContent.includes('visibility: hidden');
    const hasTransition = cssContent && cssContent.includes('transition: opacity');
    const hasShowClass = cssContent && cssContent.includes('.modal-overlay.show');

    console.log('CSS has "opacity: 0":', hasOpacity0);
    console.log('CSS has "visibility: hidden":', hasVisibilityHidden);
    console.log('CSS has transition:', hasTransition);
    console.log('CSS has .show class:', hasShowClass);

    if (!hasOpacity0 || !hasVisibilityHidden) {
      console.log('\n❌ CSS is WRONG! Initial state not set correctly');
      console.log('\nActual CSS for .modal-overlay:');
      const overlayCSS = cssContent.match(/\.modal-overlay \{[^}]+\}/);
      console.log(overlayCSS ? overlayCSS[0] : 'Not found');
    } else {
      console.log('\n✅ CSS is correct');
    }
  }

  console.log('\nWaiting 3 seconds before closing...');
  await page.waitForTimeout(3000);

  await browser.close();
})();
