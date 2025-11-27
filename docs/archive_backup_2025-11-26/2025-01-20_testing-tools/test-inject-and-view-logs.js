const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  console.log('\n=== Injecting Test Logs ===');
  
  const injected = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return { error: 'ConnectionLogger not found' };
    
    // Inject 5 network logs
    for (let i = 0; i < 5; i++) {
      await window.ConnectionLogger.log({
        eventType: 'network',
        status: i % 2 === 0 ? 'online' : 'offline',
        latencyMs: 30 + Math.random() * 50,
        metadata: { test: true }
      });
    }
    
    // Inject 5 server logs
    for (let i = 0; i < 5; i++) {
      await window.ConnectionLogger.log({
        eventType: 'server',
        status: i % 2 === 0 ? 'connected' : 'disconnected',
        latencyMs: 100 + Math.random() * 100,
        errorMessage: i % 2 === 1 ? 'Connection timeout' : null,
        metadata: { test: true }
      });
    }
    
    // Inject 3 speed test logs
    for (let i = 0; i < 3; i++) {
      await window.ConnectionLogger.log({
        eventType: 'speed_test',
        status: 'tested',
        latencyMs: 40,
        downloadSpeedMbps: 80 + Math.random() * 40,
        uploadSpeedMbps: 30 + Math.random() * 20,
        metadata: { test: true }
      });
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
    const count = await window.ConnectionLogger.getCount();
    return { success: true, count };
  });

  console.log('Injection result:', injected);

  console.log('\n=== Opening Connection Log Popup ===');
  
  await page.waitForTimeout(1000);
  
  const networkStatus = await page.$('#network-status');
  if (networkStatus) {
    await networkStatus.click();
    console.log('✓ Popup opened via network icon');
    
    await page.waitForTimeout(2000);
    
    const counts = await page.evaluate(() => {
      return {
        network: document.getElementById('network-count')?.textContent,
        server: document.getElementById('server-count')?.textContent,
        speedtest: document.getElementById('speedtest-count')?.textContent
      };
    });
    
    console.log('\nLog counts in popup:');
    console.log('- Network:', counts.network);
    console.log('- Server:', counts.server);
    console.log('- Speed test:', counts.speedtest);
  }

  console.log('\nKeeping browser open for manual inspection (30 seconds)...');
  await page.waitForTimeout(30000);

  await browser.close();
})();
