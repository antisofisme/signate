const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Capture all console logs
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('ConnectionLog') || text.includes('Loaded') || text.includes('render')) {
      console.log('[Browser]', text);
    }
  });

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  console.log('\n=== Opening Connection Log Popup ===');

  const networkStatus = await page.$('#network-status');
  if (networkStatus) {
    await networkStatus.click();
    console.log('✓ Popup opened');

    await page.waitForTimeout(3000);

    // Check popup state
    const popupState = await page.evaluate(() => {
      const networkContainer = document.getElementById('network-logs');
      const serverContainer = document.getElementById('server-logs');
      const speedtestContainer = document.getElementById('speedtest-logs');

      return {
        networkHtml: networkContainer?.innerHTML.substring(0, 200),
        serverHtml: serverContainer?.innerHTML.substring(0, 100),
        speedtestHtml: speedtestContainer?.innerHTML.substring(0, 100),
        networkCount: document.getElementById('network-count')?.textContent,
        serverCount: document.getElementById('server-count')?.textContent,
        speedtestCount: document.getElementById('speedtest-count')?.textContent
      };
    });

    console.log('\nPopup state:');
    console.log('- Network count:', popupState.networkCount);
    console.log('- Network HTML:', popupState.networkHtml);
    console.log('- Server count:', popupState.serverCount);
    console.log('- Speedtest count:', popupState.speedtestCount);

    // Manually trigger load
    console.log('\n=== Manually Triggering Load ===');
    const manualLoad = await page.evaluate(async () => {
      if (!window.ConnectionLogger) return { error: 'ConnectionLogger not found' };

      const logs = await window.ConnectionLogger.getLogs(100);
      console.log('[Manual] Got logs:', logs.length);
      console.log('[Manual] First log:', logs[0]);

      return { count: logs.length, firstLog: logs[0] };
    });

    console.log('Manual load result:', manualLoad);
  }

  console.log('\nKeeping browser open for 15 seconds...');
  await page.waitForTimeout(15000);

  await browser.close();
})();
