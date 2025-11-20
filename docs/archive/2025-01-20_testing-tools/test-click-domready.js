const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Starting click test (wait for domcontentloaded only)...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Collect console logs
  const logs = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    if (text.includes('[ConnectionLogPopup]')) {
      console.log('📝', text);
    }
  });

  console.log('📍 Navigating to player...');
  // Wait for domcontentloaded instead of networkidle (faster)
  await page.goto('http://192.168.5.12:8080', { waitUntil: 'domcontentloaded' });

  // Wait for ConnectionLogPopup to initialize
  await page.waitForTimeout(3000);

  console.log('\n🔍 Checking if click handlers are attached...');

  // Check for the log that confirms handlers are attached
  const handlerAttached = logs.some(log => log.includes('✅ Initialized with click handlers'));
  console.log('  - Click handlers attached:', handlerAttached ? '✅ YES' : '❌ NO');

  if (!handlerAttached) {
    console.log('\n❌ Click handlers not attached yet. Logs:');
    logs.filter(log => log.includes('[ConnectionLogPopup]')).forEach(log => console.log('  ', log));
    await browser.close();
    return;
  }

  // Try to find the icons
  console.log('\n🔍 Looking for status icons...');
  const networkStatus = await page.$('#network-status');
  const serverStatus = await page.$('#server-status');

  console.log('  - Network status:', networkStatus ? '✅ FOUND' : '❌ NOT FOUND');
  console.log('  - Server status:', serverStatus ? '✅ FOUND' : '❌ NOT FOUND');

  if (!networkStatus || !serverStatus) {
    console.log('\n❌ Icons not found in DOM');
    await browser.close();
    return;
  }

  // Check cursor style
  const networkCursor = await networkStatus.evaluate(el => window.getComputedStyle(el).cursor);
  const serverCursor = await serverStatus.evaluate(el => window.getComputedStyle(el).cursor);

  console.log('  - Network cursor:', networkCursor);
  console.log('  - Server cursor:', serverCursor);

  // Click network status
  console.log('\n👆 Clicking network status icon...');
  await networkStatus.click();
  await page.waitForTimeout(1000);

  // Check for popup
  const popup = await page.$('#connection-log-popup');
  const popupVisible = popup ? await popup.isVisible() : false;

  console.log('\n📋 Popup status:');
  console.log('  - Popup exists:', popup ? '✅ YES' : '❌ NO');
  console.log('  - Popup visible:', popupVisible ? '✅ YES' : '❌ NO');

  if (popupVisible) {
    console.log('\n🎉 SUCCESS! Connection log popup is working!');
    await page.screenshot({ path: 'screenshot-popup-success.png' });
    console.log('📸 Screenshot saved: screenshot-popup-success.png');

    // Wait to see the popup
    await page.waitForTimeout(5000);
  } else {
    console.log('\n❌ Popup did not appear after click');
    await page.screenshot({ path: 'screenshot-no-popup.png' });
    console.log('📸 Screenshot saved: screenshot-no-popup.png');
  }

  await browser.close();
  console.log('\n✅ Test completed');
})();
