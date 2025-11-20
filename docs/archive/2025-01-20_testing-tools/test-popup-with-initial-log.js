const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);

  console.log('\n=== Checking Initial Log ===');

  const logInfo = await page.evaluate(async () => {
    if (!window.ConnectionLogger) return { error: 'ConnectionLogger not found' };

    const count = await window.ConnectionLogger.getCount();
    const logs = await window.ConnectionLogger.getLogs(10);

    return { count, logs };
  });

  console.log('Total logs:', logInfo.count);
  console.log('Log entries:', JSON.stringify(logInfo.logs, null, 2));

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

    // Check if log entries are visible
    const hasLogs = await page.evaluate(() => {
      const networkLogs = document.getElementById('network-logs');
      const noLogsMsg = networkLogs?.querySelector('.no-logs');
      const logEntries = networkLogs?.querySelectorAll('.log-entry');

      return {
        hasNoLogsMessage: !!noLogsMsg,
        logEntriesCount: logEntries?.length || 0,
        firstLogHtml: logEntries?.[0]?.outerHTML || null
      };
    });

    console.log('\nPopup content:');
    console.log('- Has "no logs" message:', hasLogs.hasNoLogsMessage);
    console.log('- Log entries visible:', hasLogs.logEntriesCount);
    if (hasLogs.firstLogHtml) {
      console.log('- First log entry:', hasLogs.firstLogHtml.substring(0, 200));
    }
  }

  console.log('\nKeeping browser open for 20 seconds...');
  await page.waitForTimeout(20000);

  await browser.close();
})();
