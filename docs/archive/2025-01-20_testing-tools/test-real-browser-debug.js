const { chromium } = require('playwright');

(async () => {
  console.log('🔍 Debugging REAL browser state (keeping browser open)...\n');

  const browser = await chromium.launch({
    headless: false,  // Show browser
    slowMo: 1000
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Collect ALL console logs
  const allLogs = [];
  page.on('console', msg => {
    const text = msg.text();
    allLogs.push(text);
    console.log('📝', text);
  });

  // Collect ALL errors
  page.on('pageerror', error => {
    console.log('❌ PAGE ERROR:', error.message);
  });

  console.log('📍 Loading http://192.168.5.12:8080/...\n');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });

  // Wait longer for everything to initialize
  console.log('⏳ Waiting 10 seconds for full initialization...\n');
  await page.waitForTimeout(10000);

  // Check what's actually in the page
  const pageState = await page.evaluate(() => {
    return {
      // Window objects
      hasConnectionLogPopup: typeof window.ConnectionLogPopup !== 'undefined',
      hasConnectionLogger: typeof window.ConnectionLogger !== 'undefined',
      hasNetworkSpeedTest: typeof window.NetworkSpeedTest !== 'undefined',

      // DOM elements
      hasNetworkIcon: !!document.getElementById('network-status'),
      hasServerIcon: !!document.getElementById('server-status'),
      hasPopupElement: !!document.getElementById('connection-log-popup'),

      // Network icon details
      networkIconHTML: document.getElementById('network-status')?.outerHTML || null,
      serverIconHTML: document.getElementById('server-status')?.outerHTML || null,

      // Check if we're in shell or player mode
      hasShellContainer: !!document.getElementById('shell-container'),
      hasPlayerContainer: !!document.getElementById('player-container'),
      shellDisplay: document.getElementById('shell-container')?.style.display || 'unknown',
      playerDisplay: document.getElementById('player-container')?.style.display || 'unknown',

      // Check activation screen
      hasActivationScreen: !!document.querySelector('.activation-container'),
      activationScreenHTML: document.querySelector('.activation-container')?.outerHTML?.substring(0, 200) || null,

      // Body content preview
      bodyContent: document.body.innerHTML.substring(0, 1000)
    };
  });

  console.log('\n=== PAGE STATE ===');
  console.log('Window Objects:');
  console.log('  - ConnectionLogPopup:', pageState.hasConnectionLogPopup ? '✅ YES' : '❌ NO');
  console.log('  - ConnectionLogger:', pageState.hasConnectionLogger ? '✅ YES' : '❌ NO');
  console.log('  - NetworkSpeedTest:', pageState.hasNetworkSpeedTest ? '✅ YES' : '❌ NO');

  console.log('\nDOM Elements:');
  console.log('  - #network-status:', pageState.hasNetworkIcon ? '✅ YES' : '❌ NO');
  console.log('  - #server-status:', pageState.hasServerIcon ? '✅ YES' : '❌ NO');
  console.log('  - #connection-log-popup:', pageState.hasPopupElement ? '✅ YES' : '❌ NO');

  console.log('\nContainers:');
  console.log('  - #shell-container:', pageState.hasShellContainer ? '✅ YES' : '❌ NO', '- Display:', pageState.shellDisplay);
  console.log('  - #player-container:', pageState.hasPlayerContainer ? '✅ YES' : '❌ NO', '- Display:', pageState.playerDisplay);
  console.log('  - Activation screen:', pageState.hasActivationScreen ? '✅ YES' : '❌ NO');

  if (pageState.networkIconHTML) {
    console.log('\nNetwork Icon HTML:');
    console.log(pageState.networkIconHTML);
  }

  if (pageState.activationScreenHTML) {
    console.log('\nActivation Screen (preview):');
    console.log(pageState.activationScreenHTML);
  }

  console.log('\nRelevant Console Logs:');
  const relevantLogs = allLogs.filter(log =>
    log.includes('[ConnectionLogPopup]') ||
    log.includes('[ConnectionLogger]') ||
    log.includes('[NetworkSpeedTest]') ||
    log.includes('Initializing connection logging')
  );
  relevantLogs.forEach(log => console.log('  ', log));

  if (!pageState.hasConnectionLogPopup) {
    console.log('\n⚠️  PROBLEM: window.ConnectionLogPopup is NOT defined!');
    console.log('This means the module did not load or execute properly.');
  }

  if (!pageState.hasNetworkIcon) {
    console.log('\n⚠️  PROBLEM: #network-status icon is NOT in DOM!');
    console.log('Icons are probably shown only in PLAYER mode, not SHELL mode.');
    console.log('Current mode: shell-container display =', pageState.shellDisplay);
    console.log('               player-container display =', pageState.playerDisplay);
  }

  console.log('\n\n⏸️  Browser will stay open for 2 minutes for manual inspection...');
  console.log('You can:');
  console.log('  1. Open DevTools (F12)');
  console.log('  2. Check console for errors');
  console.log('  3. Try clicking icons manually');
  console.log('  4. Check if device is activated (should show player, not activation screen)');

  await page.waitForTimeout(120000);  // 2 minutes

  await browser.close();
  console.log('\n✅ Test completed');
})();
