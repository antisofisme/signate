const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Disable cache
  await context.route('**/*', (route) => {
    route.continue({
      headers: {
        ...route.request().headers(),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
  });

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/?bust=' + Date.now(), {
    waitUntil: 'domcontentloaded'
  });

  await page.waitForTimeout(3000);

  console.log('\n=== Testing Connection Log Popup ===');

  // Check if network status icon exists
  const networkStatus = await page.$('#network-status');
  if (networkStatus) {
    console.log('✓ Network status icon found');
    
    // Click network status icon to open popup
    await networkStatus.click();
    console.log('✓ Network status icon clicked');

    await page.waitForTimeout(500);

    // Check if popup opened
    const modal = await page.$('.modal-overlay');
    if (modal) {
      console.log('✓ Popup opened');

      // Check for log sections
      const networkLogs = await page.$('#network-logs');
      const serverLogs = await page.$('#server-logs');
      const speedtestLogs = await page.$('#speedtest-logs');

      console.log('\nLog sections:');
      console.log('- Network logs section:', networkLogs ? '✓ Found' : '✗ Not found');
      console.log('- Server logs section:', serverLogs ? '✓ Found' : '✗ Not found');
      console.log('- Speed test logs section:', speedtestLogs ? '✓ Found' : '✗ Not found');

      // Check log counts
      if (networkLogs) {
        const networkCount = await page.$('#network-count');
        const networkCountText = networkCount ? await networkCount.textContent() : 'N/A';
        console.log('Network logs count:', networkCountText);

        const networkContent = await networkLogs.innerHTML();
        console.log('Network logs content:', networkContent.substring(0, 200));
      }

      if (serverLogs) {
        const serverCount = await page.$('#server-count');
        const serverCountText = serverCount ? await serverCount.textContent() : 'N/A';
        console.log('Server logs count:', serverCountText);

        const serverContent = await serverLogs.innerHTML();
        console.log('Server logs content:', serverContent.substring(0, 200));
      }

      // Check browser console for errors
      console.log('\n=== Checking for JavaScript errors ===');
      const logs = await page.evaluate(() => {
        return {
          hasConnectionLogger: typeof window.ConnectionLogger !== 'undefined',
          logCount: window.ConnectionLogger ? 'available' : 'N/A'
        };
      });
      console.log('ConnectionLogger available:', logs.hasConnectionLogger);

    } else {
      console.log('✗ Popup did not open');
    }
  } else {
    console.log('✗ Network status icon not found');
  }

  console.log('\nWaiting 5 seconds...');
  await page.waitForTimeout(5000);

  await browser.close();
})();
