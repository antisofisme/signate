/**
 * Playwright Test - Connection Log Popup Click Handler
 * Test apakah icon network/server bisa diklik dan popup muncul
 */

const { chromium } = require('playwright');

async function testConnectionLogClick() {
  console.log('🚀 Starting Playwright test for Connection Log Popup...\n');
  
  const browser = await chromium.launch({
    headless: true, // Headless mode
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  
  const page = await context.newPage();
  
  // Array untuk simpan console logs
  const consoleLogs = [];
  
  // Listen semua console logs dari browser
  page.on('console', msg => {
    const text = msg.text();
    consoleLogs.push(text);
    
    // Log yang penting ke terminal
    if (text.includes('[ConnectionLogPopup]') || 
        text.includes('[ConnectionLogger]') ||
        text.includes('clicked')) {
      console.log('📝 BROWSER:', text);
    }
  });
  
  // Listen errors
  page.on('pageerror', error => {
    console.log('❌ PAGE ERROR:', error.message);
  });
  
  try {
    console.log('📍 Navigating to: http://192.168.5.12:8080\n');
    await page.goto('http://192.168.5.12:8080', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    console.log('✅ Page loaded\n');
    
    // Wait untuk JavaScript selesai init
    await page.waitForTimeout(3000);
    
    console.log('🔍 Checking for status icons...\n');
    
    // Check apakah icon ada
    const networkStatus = await page.$('#network-status');
    const serverStatus = await page.$('#server-status');
    
    console.log('📋 Elements:');
    console.log('  - Network status icon:', networkStatus ? '✅ FOUND' : '❌ NOT FOUND');
    console.log('  - Server status icon:', serverStatus ? '✅ FOUND' : '❌ NOT FOUND');
    
    if (!networkStatus || !serverStatus) {
      console.log('\n❌ Status icons not found! Test failed.');
      await browser.close();
      return false;
    }
    
    // Check cursor style
    const networkCursor = await page.evaluate(() => {
      const el = document.getElementById('network-status');
      return el ? window.getComputedStyle(el).cursor : null;
    });
    
    const serverCursor = await page.evaluate(() => {
      const el = document.getElementById('server-status');
      return el ? window.getComputedStyle(el).cursor : null;
    });
    
    console.log('  - Network cursor:', networkCursor);
    console.log('  - Server cursor:', serverCursor);
    
    if (networkCursor === 'pointer' && serverCursor === 'pointer') {
      console.log('  ✅ Icons are clickable (cursor: pointer)\n');
    } else {
      console.log('  ⚠️ Icons may not be clickable\n');
    }
    
    // Screenshot before click
    await page.screenshot({ path: 'test-before-click.png' });
    console.log('📸 Screenshot saved: test-before-click.png\n');
    
    // Test click network icon
    console.log('👆 TEST 1: Clicking network status icon...\n');
    await networkStatus.click();
    await page.waitForTimeout(1000);
    
    // Check if popup appeared
    const popup = await page.$('#connection-log-popup');
    let popupVisible = false;
    
    if (popup) {
      popupVisible = await page.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.display !== 'none';
      }, popup);
    }
    
    console.log('📋 Popup Status:');
    console.log('  - Popup element:', popup ? '✅ FOUND' : '❌ NOT FOUND');
    console.log('  - Popup visible:', popupVisible ? '✅ YES' : '❌ NO');
    
    if (popupVisible) {
      console.log('\n✅ SUCCESS! Network icon click works!\n');
      
      // Get popup details
      const popupTitle = await page.evaluate(() => {
        const h3 = document.querySelector('#connection-log-popup h3');
        return h3 ? h3.textContent.trim() : null;
      });
      
      console.log('📋 Popup Details:');
      console.log('  - Title:', popupTitle);
      
      // Check filter buttons
      const filterCount = await page.$$eval('#connection-log-popup .filter-btn', 
        btns => btns.length
      );
      console.log('  - Filter buttons:', filterCount);
      
      // Check if network filter is active
      const activeFilter = await page.evaluate(() => {
        const active = document.querySelector('#connection-log-popup .filter-btn.active');
        return active ? active.dataset.filter : null;
      });
      console.log('  - Active filter:', activeFilter);
      
      // Screenshot popup
      await page.screenshot({ path: 'test-popup-open.png' });
      console.log('\n📸 Screenshot saved: test-popup-open.png\n');
      
      // Close popup
      const closeBtn = await page.$('#connection-log-close');
      if (closeBtn) {
        await closeBtn.click();
        await page.waitForTimeout(500);
        console.log('✅ Popup closed\n');
      }
      
    } else {
      console.log('\n❌ FAILED! Popup did not appear after clicking network icon\n');
      
      // Debug: check console logs
      console.log('📋 Console Logs Summary:');
      const popupLogs = consoleLogs.filter(log => log.includes('[ConnectionLogPopup]'));
      if (popupLogs.length > 0) {
        popupLogs.forEach(log => console.log('  -', log));
      } else {
        console.log('  - No ConnectionLogPopup logs found');
      }
      
      await page.screenshot({ path: 'test-failed.png' });
      console.log('\n📸 Screenshot saved: test-failed.png\n');
    }
    
    // Test click server icon
    console.log('👆 TEST 2: Clicking server status icon...\n');
    await serverStatus.click();
    await page.waitForTimeout(1000);
    
    const popup2 = await page.$('#connection-log-popup');
    let popup2Visible = false;
    
    if (popup2) {
      popup2Visible = await page.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.display !== 'none';
      }, popup2);
    }
    
    console.log('📋 Popup Status:');
    console.log('  - Popup visible:', popup2Visible ? '✅ YES' : '❌ NO');
    
    if (popup2Visible) {
      console.log('\n✅ SUCCESS! Server icon click works too!\n');
      
      // Check if server filter is active
      const activeFilter = await page.evaluate(() => {
        const active = document.querySelector('#connection-log-popup .filter-btn.active');
        return active ? active.dataset.filter : null;
      });
      console.log('  - Active filter:', activeFilter);
      
      await page.screenshot({ path: 'test-server-popup.png' });
      console.log('📸 Screenshot saved: test-server-popup.png\n');
    }
    
    // Summary
    console.log('═══════════════════════════════════════════════════════\n');
    console.log('📊 TEST SUMMARY:\n');
    console.log('  1. Network icon click:', popupVisible ? '✅ PASS' : '❌ FAIL');
    console.log('  2. Server icon click:', popup2Visible ? '✅ PASS' : '❌ FAIL');
    console.log('  3. Icons are clickable:', (networkCursor === 'pointer' && serverCursor === 'pointer') ? '✅ YES' : '❌ NO');
    
    const allPass = popupVisible && popup2Visible;
    console.log('\n  Overall Result:', allPass ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED');
    console.log('\n═══════════════════════════════════════════════════════\n');
    
    await browser.close();
    return allPass;
    
  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    await page.screenshot({ path: 'test-error.png' });
    await browser.close();
    return false;
  }
}

// Run test
testConnectionLogClick()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
