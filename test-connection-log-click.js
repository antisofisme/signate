const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Starting Playwright test for connection log popup...\n');
  
  const browser = await chromium.launch({
    headless: false, // Show browser untuk debugging
    slowMo: 500 // Slow down untuk bisa lihat
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  
  const page = await context.newPage();
  
  // Enable console logging from page
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[ConnectionLogPopup]') || 
        text.includes('[ConnectionLogger]') || 
        text.includes('[NetworkSpeedTest]')) {
      console.log('📝 BROWSER LOG:', text);
    }
  });
  
  console.log('📍 Navigating to player: http://192.168.5.12:8080');
  await page.goto('http://192.168.5.12:8080', { waitUntil: 'networkidle' });
  
  // Wait for page to fully load
  await page.waitForTimeout(3000);
  console.log('✅ Page loaded\n');
  
  // Check if status icons exist
  console.log('🔍 Checking for status icons...');
  const networkStatus = await page.$('#network-status');
  const serverStatus = await page.$('#server-status');
  
  console.log('  - Network status icon:', networkStatus ? '✅ FOUND' : '❌ NOT FOUND');
  console.log('  - Server status icon:', serverStatus ? '✅ FOUND' : '❌ NOT FOUND');
  
  if (!networkStatus || !serverStatus) {
    console.log('\n❌ Status icons not found! Stopping test.');
    await browser.close();
    return;
  }
  
  // Get cursor style to check if clickable
  const networkCursor = await page.$eval('#network-status', el => window.getComputedStyle(el).cursor);
  const serverCursor = await page.$eval('#server-status', el => window.getComputedStyle(el).cursor);
  
  console.log('  - Network status cursor:', networkCursor);
  console.log('  - Server status cursor:', serverCursor);
  console.log('');
  
  // Take screenshot before click
  await page.screenshot({ path: 'screenshot-before-click.png' });
  console.log('📸 Screenshot saved: screenshot-before-click.png\n');
  
  // Test clicking network status
  console.log('👆 Clicking network status icon...');
  await networkStatus.click();
  await page.waitForTimeout(1000);
  
  // Check if popup appeared
  const popup = await page.$('#connection-log-popup');
  const popupVisible = popup ? await popup.isVisible() : false;
  
  console.log('  - Popup element:', popup ? '✅ FOUND' : '❌ NOT FOUND');
  console.log('  - Popup visible:', popupVisible ? '✅ YES' : '❌ NO');
  
  if (popupVisible) {
    console.log('\n✅ SUCCESS! Connection log popup opened!\n');
    
    // Take screenshot of popup
    await page.screenshot({ path: 'screenshot-popup-open.png' });
    console.log('📸 Screenshot saved: screenshot-popup-open.png');
    
    // Get popup content
    const popupTitle = await page.$eval('#connection-log-popup h3', el => el.textContent.trim());
    console.log('📋 Popup title:', popupTitle);
    
    // Check filter buttons
    const filterBtns = await page.$$('#connection-log-popup .filter-btn');
    console.log('📋 Filter buttons found:', filterBtns.length);
    
    // Wait a bit to see the popup
    await page.waitForTimeout(2000);
    
    // Close popup
    console.log('\n👆 Clicking close button...');
    const closeBtn = await page.$('#connection-log-close');
    if (closeBtn) {
      await closeBtn.click();
      await page.waitForTimeout(500);
      console.log('✅ Popup closed');
    }
  } else {
    console.log('\n❌ FAILED! Popup did not open after click.\n');
    
    // Check for JavaScript errors
    console.log('🔍 Checking for JavaScript errors in console...');
    
    await page.screenshot({ path: 'screenshot-failed.png' });
    console.log('📸 Screenshot saved: screenshot-failed.png');
  }
  
  // Test clicking server status
  console.log('\n👆 Clicking server status icon...');
  await serverStatus.click();
  await page.waitForTimeout(1000);
  
  const popup2 = await page.$('#connection-log-popup');
  const popup2Visible = popup2 ? await popup2.isVisible() : false;
  
  console.log('  - Popup visible:', popup2Visible ? '✅ YES' : '❌ NO');
  
  if (popup2Visible) {
    console.log('✅ Server status click also works!');
    await page.waitForTimeout(2000);
  }
  
  console.log('\n🏁 Test completed!');
  console.log('📝 Check screenshots for visual confirmation.');
  
  await browser.close();
})();
