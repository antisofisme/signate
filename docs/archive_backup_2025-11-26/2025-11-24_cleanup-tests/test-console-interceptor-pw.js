const { chromium } = require('playwright');

(async () => {
  console.log('🧪 Testing Console Interceptor with Playwright...\n');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  const page = await browser.newPage();
  
  // Monitor console
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[ConsoleInterceptor]') || text.includes('[TEST')) {
      console.log('📊', text);
    }
  });
  
  console.log('📍 Navigating to player...');
  await page.goto('http://192.168.5.12:8080/');
  
  console.log('⏳ Waiting for page load...');
  await page.waitForTimeout(5000);
  
  console.log('🔍 Checking console interceptor state...');
  const state = await page.evaluate(() => {
    return window.consoleInterceptorService?.getState();
  });
  
  console.log('📊 Interceptor State:', JSON.stringify(state, null, 2));
  
  if (!state || !state.isActive) {
    console.log('❌ Console interceptor not active!');
    await browser.close();
    return;
  }
  
  console.log('\n🧪 Generating 60 test logs to trigger batch flush...');
  await page.evaluate(() => {
    for (let i = 0; i < 60; i++) {
      console.log(`[TEST-BATCH] Auto-test log number ${i}`);
    }
  });
  
  console.log('⏳ Waiting 2 seconds for auto-flush...');
  await page.waitForTimeout(2000);
  
  console.log('🔄 Triggering manual flush...');
  await page.evaluate(() => {
    window.consoleInterceptorService?.manualFlush();
  });
  
  console.log('⏳ Waiting 5 seconds for upload...');
  await page.waitForTimeout(5000);
  
  const finalState = await page.evaluate(() => {
    return window.consoleInterceptorService?.getState();
  });
  
  console.log('\n📊 Final State:', JSON.stringify(finalState, null, 2));
  console.log('\n✅ Test complete!');
  console.log('👉 Now check backend logs with:');
  console.log('   docker logs signage-backend-python --tail 50 | grep -E "Console|WSManager|console/upload"');
  
  await browser.close();
})();
