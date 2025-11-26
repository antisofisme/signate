const puppeteer = require('puppeteer');

(async () => {
  console.log('🧪 Testing Console Interceptor...\n');
  
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Monitor console
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[ConsoleInterceptor]')) {
      console.log('📊', text);
    }
  });
  
  console.log('📍 Navigating to player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'networkidle2' });
  
  console.log('⏳ Waiting for interceptor to initialize...');
  await page.waitForTimeout(3000);
  
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
  
  console.log('\n🧪 Generating test logs...');
  await page.evaluate(() => {
    // Generate 60 logs to exceed batch size (50)
    for (let i = 0; i < 60; i++) {
      console.log(`[TEST-BATCH] Log number ${i}`);
    }
  });
  
  console.log('⏳ Waiting for auto-flush...');
  await page.waitForTimeout(2000);
  
  console.log('🔄 Triggering manual flush...');
  await page.evaluate(() => {
    window.consoleInterceptorService?.manualFlush();
  });
  
  console.log('⏳ Waiting for upload to complete...');
  await page.waitForTimeout(3000);
  
  const finalState = await page.evaluate(() => {
    return window.consoleInterceptorService?.getState();
  });
  
  console.log('\n📊 Final State:', JSON.stringify(finalState, null, 2));
  console.log('\n✅ Test complete! Check backend logs for console uploads.');
  
  await browser.close();
})();
