const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening player with new bundle...');
  await page.goto('http://192.168.5.12:8080/?v=' + Date.now(), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  console.log('\n=== Test: Add log and verify ===');
  
  const result = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return { error: 'ConnectionLogger not found' };
    
    const before = await window.ConnectionLogger.getCount();
    
    await window.ConnectionLogger.log({
      eventType: 'network',
      status: 'online',
      latencyMs: 45
    });
    
    await new Promise(r => setTimeout(r, 1000));
    
    const after = await window.ConnectionLogger.getCount();
    const logs = await window.ConnectionLogger.getLogs(5);
    
    return { before, after, success: after > before, logs };
  });

  console.log('Result:', JSON.stringify(result, null, 2));

  if (result.success) {
    console.log('\n✅ SUCCESS: Logs are being saved!');
    
    // Now open popup
    console.log('\n=== Opening popup to verify display ===');
    await page.click('#network-status');
    await page.waitForTimeout(1000);
    
    const popupData = await page.evaluate(() => {
      return {
        network: document.getElementById('network-count')?.textContent,
        server: document.getElementById('server-count')?.textContent,
        speedtest: document.getElementById('speedtest-count')?.textContent
      };
    });
    
    console.log('Popup counts:', popupData);
  } else {
    console.log('\n❌ FAILED: Logs are NOT being saved');
  }

  await page.waitForTimeout(5000);
  await browser.close();
})();
