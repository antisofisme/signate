const { chromium } = require('playwright');

(async () => {
  console.log('🔍 Debugging click issue on player...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Collect ALL console logs
  page.on('console', msg => {
    console.log('📝 CONSOLE:', msg.text());
  });

  // Collect errors
  page.on('pageerror', error => {
    console.log('❌ ERROR:', error.message);
  });

  console.log('📍 Loading page...');
  await page.goto('http://192.168.5.12:8080', { waitUntil: 'domcontentloaded' });

  // Wait for page to settle
  await page.waitForTimeout(5000);

  console.log('\n🔍 Inspecting page state...\n');

  // Check what's in the DOM
  const pageInfo = await page.evaluate(() => {
    const networkIcon = document.getElementById('network-status');
    const serverIcon = document.getElementById('server-status');
    const popup = document.getElementById('connection-log-popup');

    return {
      hasNetworkIcon: !!networkIcon,
      hasServerIcon: !!serverIcon,
      hasPopup: !!popup,
      networkIconHTML: networkIcon ? networkIcon.outerHTML : null,
      serverIconHTML: serverIcon ? serverIcon.outerHTML : null,
      popupHTML: popup ? popup.outerHTML.substring(0, 200) : null,
      windowConnectionLogPopup: typeof window.ConnectionLogPopup !== 'undefined',
      windowConnectionLogger: typeof window.ConnectionLogger !== 'undefined',
      windowNetworkSpeedTest: typeof window.NetworkSpeedTest !== 'undefined',
      bodyHTML: document.body.innerHTML.substring(0, 500)
    };
  });

  console.log('DOM State:');
  console.log('  - Network icon exists:', pageInfo.hasNetworkIcon);
  console.log('  - Server icon exists:', pageInfo.hasServerIcon);
  console.log('  - Popup exists:', pageInfo.hasPopup);
  console.log('  - window.ConnectionLogPopup:', pageInfo.windowConnectionLogPopup);
  console.log('  - window.ConnectionLogger:', pageInfo.windowConnectionLogger);
  console.log('  - window.NetworkSpeedTest:', pageInfo.windowNetworkSpeedTest);

  if (pageInfo.networkIconHTML) {
    console.log('\nNetwork Icon HTML:', pageInfo.networkIconHTML);
  }

  if (pageInfo.serverIconHTML) {
    console.log('Server Icon HTML:', pageInfo.serverIconHTML);
  }

  console.log('\nBody HTML (first 500 chars):', pageInfo.bodyHTML);

  // Try to click if icons exist
  if (pageInfo.hasNetworkIcon) {
    console.log('\n👆 Attempting to click network icon...');

    const networkIcon = await page.$('#network-status');
    if (networkIcon) {
      // Get bounding box
      const box = await networkIcon.boundingBox();
      console.log('  - Icon position:', box);

      // Check if clickable
      const isClickable = await networkIcon.evaluate(el => {
        const style = window.getComputedStyle(el);
        return {
          cursor: style.cursor,
          pointerEvents: style.pointerEvents,
          display: style.display,
          visibility: style.visibility,
          hasClickListener: el.onclick !== null
        };
      });
      console.log('  - Icon style:', isClickable);

      // Click
      await networkIcon.click();
      await page.waitForTimeout(2000);

      // Check popup
      const popupAfterClick = await page.$('#connection-log-popup');
      const isVisible = popupAfterClick ? await popupAfterClick.isVisible() : false;
      console.log('  - Popup visible after click:', isVisible);

      if (isVisible) {
        console.log('\n✅ SUCCESS! Popup appeared');
        await page.screenshot({ path: 'debug-success.png' });
      } else {
        console.log('\n❌ FAILED! Popup did not appear');
        await page.screenshot({ path: 'debug-failed.png' });
      }
    }
  } else {
    console.log('\n⚠️ No network icon found - check if page is in shell or player mode');
  }

  // Keep browser open for manual inspection
  console.log('\n⏸️  Browser will stay open for 30 seconds for manual inspection...');
  await page.waitForTimeout(30000);

  await browser.close();
})();
