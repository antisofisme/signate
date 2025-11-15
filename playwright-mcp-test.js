/**
 * Playwright MCP Test - Connection Log Click Handler
 */

const { chromium } = require('playwright');

(async () => {
  console.log('🎭 Playwright MCP Test - Connection Log Popup\n');
  console.log('═══════════════════════════════════════════════════════\n');
  
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });
  
  const logs = {
    console: [],
    errors: [],
    network: []
  };
  
  // Capture console logs
  page.on('console', msg => {
    const text = msg.text();
    logs.console.push(text);
    if (text.includes('[ConnectionLogPopup]') || text.includes('clicked')) {
      console.log('📝', text);
    }
  });
  
  // Capture errors
  page.on('pageerror', error => {
    logs.errors.push(error.message);
    console.log('❌ ERROR:', error.message);
  });
  
  try {
    // Navigate
    console.log('🌐 Loading page: http://192.168.5.12:8080\n');
    await page.goto('http://192.168.5.12:8080', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // Wait for JS init
    await page.waitForTimeout(3000);
    
    // Test 1: Check elements exist
    console.log('TEST 1: Checking DOM elements\n');
    const elements = await page.evaluate(() => {
      return {
        networkStatus: !!document.getElementById('network-status'),
        serverStatus: !!document.getElementById('server-status'),
        networkCursor: window.getComputedStyle(document.getElementById('network-status')).cursor,
        serverCursor: window.getComputedStyle(document.getElementById('server-status')).cursor
      };
    });
    
    console.log('  Network status icon:', elements.networkStatus ? '✅' : '❌');
    console.log('  Server status icon:', elements.serverStatus ? '✅' : '❌');
    console.log('  Network cursor:', elements.networkCursor);
    console.log('  Server cursor:', elements.serverCursor);
    console.log('');
    
    // Test 2: Click network icon
    console.log('TEST 2: Clicking network icon\n');
    await page.click('#network-status');
    await page.waitForTimeout(1000);
    
    const popup1 = await page.evaluate(() => {
      const el = document.getElementById('connection-log-popup');
      if (!el) return { found: false, visible: false };
      const style = window.getComputedStyle(el);
      return {
        found: true,
        visible: style.display !== 'none',
        title: document.querySelector('#connection-log-popup h3')?.textContent?.trim() || '',
        filterCount: document.querySelectorAll('#connection-log-popup .filter-btn').length,
        activeFilter: document.querySelector('#connection-log-popup .filter-btn.active')?.dataset?.filter || ''
      };
    });
    
    console.log('  Popup found:', popup1.found ? '✅' : '❌');
    console.log('  Popup visible:', popup1.visible ? '✅' : '❌');
    if (popup1.visible) {
      console.log('  Title:', popup1.title);
      console.log('  Filter buttons:', popup1.filterCount);
      console.log('  Active filter:', popup1.activeFilter);
      await page.screenshot({ path: 'popup-network.png' });
      console.log('  📸 Screenshot: popup-network.png');
    }
    console.log('');
    
    // Close popup
    if (popup1.visible) {
      await page.click('#connection-log-close');
      await page.waitForTimeout(500);
    }
    
    // Test 3: Click server icon
    console.log('TEST 3: Clicking server icon\n');
    await page.click('#server-status');
    await page.waitForTimeout(1000);
    
    const popup2 = await page.evaluate(() => {
      const el = document.getElementById('connection-log-popup');
      if (!el) return { found: false, visible: false };
      const style = window.getComputedStyle(el);
      return {
        found: true,
        visible: style.display !== 'none',
        activeFilter: document.querySelector('#connection-log-popup .filter-btn.active')?.dataset?.filter || ''
      };
    });
    
    console.log('  Popup found:', popup2.found ? '✅' : '❌');
    console.log('  Popup visible:', popup2.visible ? '✅' : '❌');
    if (popup2.visible) {
      console.log('  Active filter:', popup2.activeFilter);
      await page.screenshot({ path: 'popup-server.png' });
      console.log('  📸 Screenshot: popup-server.png');
    }
    console.log('');
    
    // Test 4: Check console logs
    console.log('TEST 4: Analyzing console logs\n');
    const relevantLogs = logs.console.filter(log => 
      log.includes('[ConnectionLogPopup]')
    );
    
    const hasInit = relevantLogs.some(log => log.includes('Initialized'));
    const hasAttach = relevantLogs.some(log => log.includes('click handler attached'));
    const hasNetworkClick = relevantLogs.some(log => log.includes('Network icon clicked'));
    const hasServerClick = relevantLogs.some(log => log.includes('Server icon clicked'));
    
    console.log('  Initialization:', hasInit ? '✅' : '❌');
    console.log('  Click handlers attached:', hasAttach ? '✅' : '❌');
    console.log('  Network click detected:', hasNetworkClick ? '✅' : '❌');
    console.log('  Server click detected:', hasServerClick ? '✅' : '❌');
    console.log('');
    
    // Summary
    console.log('═══════════════════════════════════════════════════════\n');
    console.log('📊 TEST RESULTS SUMMARY\n');
    console.log('  ✓ Elements present:', elements.networkStatus && elements.serverStatus ? 'PASS' : 'FAIL');
    console.log('  ✓ Icons clickable:', elements.networkCursor === 'pointer' ? 'PASS' : 'FAIL');
    console.log('  ✓ Network icon click:', popup1.visible ? 'PASS' : 'FAIL');
    console.log('  ✓ Server icon click:', popup2.visible ? 'PASS' : 'FAIL');
    console.log('  ✓ Console logging:', hasInit && hasAttach ? 'PASS' : 'FAIL');
    
    const allPass = elements.networkStatus && 
                    elements.serverStatus && 
                    popup1.visible && 
                    popup2.visible;
    
    console.log('\n  🎯 Overall:', allPass ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED');
    console.log('\n═══════════════════════════════════════════════════════\n');
    
    await browser.close();
    process.exit(allPass ? 0 : 1);
    
  } catch (error) {
    console.error('\n💥 Test failed with error:', error.message);
    await page.screenshot({ path: 'error.png' });
    await browser.close();
    process.exit(1);
  }
})();
