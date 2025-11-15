const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(40000); // Wait for logs to accumulate

  console.log('\n=== Opening Connection Log Popup ===');
  const networkStatus = await page.$('#network-status');
  await networkStatus?.click();
  await page.waitForTimeout(2000);

  // Check tabs
  const tabs = await page.evaluate(() => {
    const tabBtns = Array.from(document.querySelectorAll('.tab-btn'));
    return tabBtns.map(btn => ({
      text: btn.textContent?.trim(),
      active: btn.classList.contains('active'),
      dataTab: btn.getAttribute('data-tab')
    }));
  });

  console.log('\nTabs:');
  tabs.forEach(tab => console.log(`  - ${tab.text} ${tab.active ? '(active)' : ''}`));

  // Check table
  const tableInfo = await page.evaluate(() => {
    const table = document.querySelector('.log-table');
    if (!table) return { exists: false };

    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent?.trim());
    const rowCount = table.querySelectorAll('tbody tr').length;

    return {
      exists: true,
      headers,
      rowCount
    };
  });

  console.log('\nTable:');
  if (tableInfo.exists) {
    console.log('  Headers:', tableInfo.headers);
    console.log('  Rows:', tableInfo.rowCount);
  } else {
    console.log('  ❌ Table not found!');
  }

  // Test tab switching
  console.log('\n=== Testing Tab Switching ===');

  for (const tabName of ['server', 'speed_test', 'all']) {
    console.log(`\nSwitching to ${tabName} tab...`);

    await page.evaluate((tab) => {
      const btn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
      if (btn) btn.click();
    }, tabName);

    await page.waitForTimeout(500);

    const info = await page.evaluate(() => {
      const activeTab = document.querySelector('.tab-btn.active');
      const table = document.querySelector('.log-table');
      const rowCount = table?.querySelectorAll('tbody tr').length || 0;

      return {
        activeTab: activeTab?.textContent?.trim(),
        rowCount
      };
    });

    console.log(`  Active: ${info.activeTab}, Rows: ${info.rowCount}`);
  }

  console.log('\nKeeping browser open for 15 seconds...');
  await page.waitForTimeout(15000);

  await browser.close();
})();
