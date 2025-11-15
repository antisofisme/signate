const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/?bust=' + Date.now(), {
    waitUntil: 'networkidle'
  });

  await page.waitForTimeout(3000);

  console.log('\n=== Checking ConnectionLogger ===');

  const loggerInfo = await page.evaluate(async () => {
    // Check if ConnectionLogger exists
    if (!window.ConnectionLogger) {
      return { error: 'ConnectionLogger not found' };
    }

    // Get log count
    const count = await window.ConnectionLogger.getCount();
    
    // Get all logs
    const logs = await window.ConnectionLogger.getLogs(100);

    return {
      loggerExists: true,
      count: count,
      logs: logs,
      sampleLog: logs.length > 0 ? logs[0] : null
    };
  });

  console.log('ConnectionLogger exists:', loggerInfo.loggerExists);
  console.log('Total logs in IndexedDB:', loggerInfo.count);
  console.log('Retrieved logs:', loggerInfo.logs ? loggerInfo.logs.length : 0);
  
  if (loggerInfo.sampleLog) {
    console.log('\nSample log entry:');
    console.log(JSON.stringify(loggerInfo.sampleLog, null, 2));
  } else {
    console.log('\n⚠️ No logs found in storage!');
    console.log('This means ConnectionLogger is not recording events yet.');
  }

  // Check if ConnectionLogger is initialized
  console.log('\n=== Manually trigger a test log ===');
  
  const testResult = await page.evaluate(async () => {
    try {
      // Try to log a test event
      await window.ConnectionLogger.log({
        eventType: 'network',
        status: 'online',
        latencyMs: 50
      });
      
      // Wait a bit for IndexedDB
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Get count again
      const newCount = await window.ConnectionLogger.getCount();
      
      return { success: true, newCount };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  console.log('Manual log test result:', testResult);

  console.log('\nWaiting 3 seconds...');
  await page.waitForTimeout(3000);

  await browser.close();
})();
