const { chromium } = require('playwright');

(async () => {
  console.log('🎭 Playwright Test - Connection Log Popup\n');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  const logs = [];
  page.on('console', msg => {
    const text = msg.text();
    logs.push(text);
    if (text.includes('[ConnectionLogPopup]')) {
      console.log('📝', text);
    }
  });
  
  try {
    console.log('🌐 Loading page...\n');
    await page.goto('http://192.168.5.12:8080', { 
      waitUntil: 'domcontentloaded',
      timeout: 60000 
    });
    
    console.log('⏳ Waiting for page initialization...\n');
    await page.waitForTimeout(5000);
    
    console.log('🔍 Checking elements...\n');
    
    const result = await page.evaluate(() => {
      const networkIcon = document.getElementById('network-status');
      const serverIcon = document.getElementById('server-status');
      
      return {
        networkExists: !!networkIcon,
        serverExists: !!serverIcon,
        networkCursor: networkIcon ? window.getComputedStyle(networkIcon).cursor : null,
        serverCursor: serverIcon ? window.getComputedStyle(serverIcon).cursor : null
      };
    });
    
    console.log('Icons found:');
    console.log('  Network:', result.networkExists ? '✅' : '❌');
    console.log('  Server:', result.serverExists ? '✅' : '❌');
    console.log('  Network cursor:', result.networkCursor);
    console.log('  Server cursor:', result.serverCursor);
    console.log('');
    
    if (!result.networkExists) {
      console.log('❌ Network icon not found!');
      await browser.close();
      process.exit(1);
    }
    
    console.log('👆 Clicking network icon...\n');
    await page.click('#network-status');
    await page.waitForTimeout(2000);
    
    const popupState = await page.evaluate(() => {
      const popup = document.getElementById('connection-log-popup');
      if (!popup) return { exists: false };
      
      return {
        exists: true,
        display: window.getComputedStyle(popup).display,
        visible: window.getComputedStyle(popup).display !== 'none',
        title: document.querySelector('#connection-log-popup h3')?.textContent || ''
      };
    });
    
    console.log('Popup state:');
    console.log('  Exists:', popupState.exists ? '✅' : '❌');
    console.log('  Display:', popupState.display);
    console.log('  Visible:', popupState.visible ? '✅' : '❌');
    if (popupState.visible) {
      console.log('  Title:', popupState.title);
    }
    console.log('');
    
    await page.screenshot({ path: 'test-result.png' });
    console.log('📸 Screenshot saved: test-result.png\n');
    
    console.log('═══════════════════════════════════════════════════════');
    console.log(popupState.visible ? '✅ TEST PASSED - Popup shows on click!' : '❌ TEST FAILED - Popup did not show');
    console.log('═══════════════════════════════════════════════════════\n');
    
    await browser.close();
    process.exit(popupState.visible ? 0 : 1);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser.close();
    process.exit(1);
  }
})();
