const { chromium } = require('playwright');

(async () => {
  console.log('🚀 Starting Console Streaming Test...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const page = await browser.newPage();

  // Collect console logs
  const consoleLogs = [];
  page.on('console', msg => {
    const text = msg.text();
    consoleLogs.push(text);

    // Only show ConsoleStream messages
    if (text.includes('[ConsoleStream]')) {
      console.log(`📝 ${text}`);
    }
  });

  try {
    // 1. Navigate to CMS
    console.log('1️⃣ Navigating to CMS...');
    await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 2. Login
    console.log('2️⃣ Logging in...');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    console.log('3️⃣ Navigating to Devices page...');
    await page.goto('http://localhost:3000/devices', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 4. Find and click device 7650
    console.log('4️⃣ Looking for device 7650...');
    const deviceRow = page.locator('tr').filter({ hasText: '7650' }).first();
    await deviceRow.click();
    await page.waitForTimeout(2000);

    // 5. Click Console tab
    console.log('5️⃣ Clicking Console tab...');
    const consoleTab = page.locator('button, div').filter({ hasText: /^Console$/i }).first();
    await consoleTab.click();
    await page.waitForTimeout(3000);

    // 6. Check for logs in UI
    console.log('6️⃣ Checking for console logs in UI...\n');

    // Wait a bit for logs to arrive
    await page.waitForTimeout(5000);

    // Try to find log entries
    const logElements = await page.locator('[class*="log"], [class*="console"], li, div').filter({
      hasText: /\[Client|console\.log|error|warn/i
    }).count();

    console.log(`\n📊 RESULTS:`);
    console.log(`   Log elements found in DOM: ${logElements}`);

    // Check the "Live Streaming Active" text
    const streamingStatus = await page.locator('text=/Live Streaming Active/i').first();
    const statusText = await streamingStatus.textContent().catch(() => 'Not found');
    console.log(`   Streaming status: ${statusText}`);

    // Get all ConsoleStream messages
    const consoleStreamLogs = consoleLogs.filter(l => l.includes('[ConsoleStream]'));
    console.log(`\n📋 ConsoleStream Messages (${consoleStreamLogs.length} total):`);
    consoleStreamLogs.forEach(log => console.log(`   ${log}`));

    // Check for successful subscription
    const subscribed = consoleStreamLogs.some(l => l.includes('Subscription confirmed'));
    const receivedLogs = consoleStreamLogs.some(l => l.includes('Received logs'));

    console.log(`\n✅ Status Check:`);
    console.log(`   Subscription confirmed: ${subscribed ? '✅ YES' : '❌ NO'}`);
    console.log(`   Logs received: ${receivedLogs ? '✅ YES' : '❌ NO'}`);

    // Take screenshot
    await page.screenshot({ path: '/tmp/console_streaming_test.png', fullPage: true });
    console.log(`\n📸 Screenshot saved: /tmp/console_streaming_test.png`);

    // Keep browser open for inspection
    console.log('\n⏸️  Browser will stay open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    await browser.close();
    console.log('\n✅ Test completed!');
  }
})();
