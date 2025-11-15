const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Capture console
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('ConnectionLogger') || text.includes('Speed') || text.includes('health_check')) {
      console.log('[Browser]', text);
    }
  });

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });

  console.log('Waiting for initialization...');
  await page.waitForTimeout(5000);

  console.log('\n=== Initial Log Count ===');
  let count1 = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return 0;
    return await window.ConnectionLogger.getCount();
  });
  console.log('Count:', count1);

  console.log('\nWaiting 35 seconds for first health check and speed test...');
  await page.waitForTimeout(35000);

  console.log('\n=== After 35 seconds ===');
  let count2 = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return { count: 0, logs: [] };
    const count = await window.ConnectionLogger.getCount();
    const logs = await window.ConnectionLogger.getLogs(20);
    return { count, logs };
  });

  console.log('Count:', count2.count);
  console.log('Logs:');
  count2.logs.forEach(log => {
    console.log(`  - [${log.eventType}] ${log.status} at ${new Date(log.timestamp).toLocaleTimeString()}${log.latencyMs ? ` (${log.latencyMs}ms)` : ''}${log.downloadSpeedMbps ? ` DL:${log.downloadSpeedMbps.toFixed(2)}Mbps` : ''}`);
  });

  console.log('\n=== Opening Popup ===');
  const networkStatus = await page.$('#network-status');
  await networkStatus?.click();
  await page.waitForTimeout(2000);

  const popupCounts = await page.evaluate(() => {
    return {
      network: document.getElementById('network-count')?.textContent,
      server: document.getElementById('server-count')?.textContent,
      speedtest: document.getElementById('speedtest-count')?.textContent
    };
  });

  console.log('Popup counts:');
  console.log('  Network:', popupCounts.network);
  console.log('  Server:', popupCounts.server);
  console.log('  Speed Test:', popupCounts.speedtest);

  console.log('\nKeeping open for 30 seconds...');
  await page.waitForTimeout(30000);

  await browser.close();
})();
