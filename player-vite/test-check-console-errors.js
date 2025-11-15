const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Capture all console messages
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    console.log(`[${type}] ${text}`);
  });

  // Capture errors
  page.on('pageerror', error => {
    console.log('[ERROR]', error.message);
  });

  console.log('Opening player with cache disabled...');
  await page.goto('http://192.168.5.12:8080/?nocache=' + Date.now(), { 
    waitUntil: 'domcontentloaded' 
  });

  console.log('\nWaiting for ConnectionLogger init...');
  await page.waitForTimeout(8000);

  console.log('\n=== Manually test adding a log ===');
  const testResult = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return { error: 'ConnectionLogger not available' };
    
    try {
      await window.ConnectionLogger.log({
        eventType: 'network',
        status: 'online',
        latencyMs: 50
      });
      
      await new Promise(r => setTimeout(r, 1500));
      
      const count = await window.ConnectionLogger.getCount();
      const logs = await window.ConnectionLogger.getLogs(5);
      
      return { success: true, count, logs: logs.length };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  console.log('\nTest result:', JSON.stringify(testResult, null, 2));

  await page.waitForTimeout(5000);
  await browser.close();
})();
