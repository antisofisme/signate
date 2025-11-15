const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  console.log('\n=== Checking Logs ===');
  
  const result = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return { error: 'ConnectionLogger not found' };
    
    const count = await window.ConnectionLogger.getCount();
    const logs = await window.ConnectionLogger.getLogs(10);
    
    return { count, logsLength: logs.length, firstLog: logs[0] || null };
  });

  console.log('Result:', JSON.stringify(result, null, 2));

  await page.waitForTimeout(3000);
  await browser.close();
})();
