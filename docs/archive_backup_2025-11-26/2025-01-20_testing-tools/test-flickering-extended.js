const { chromium } = require('playwright');

(async () => {
  console.log('🔍 Testing for flickering with extended monitoring (30 seconds)...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  // Log all console messages
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[Flicker]') || text.includes('[Visibility]')) {
      console.log('📝 BROWSER:', text);
    }
  });

  console.log('📍 Loading player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  console.log('\n=== STARTING EXTENDED MONITORING ===\n');

  // Setup comprehensive monitoring
  await page.evaluate(() => {
    window.visibilityLog = [];
    let lastLogTime = 0;

    // Monitor all relevant elements
    const elementsToWatch = [
      'shell-container',
      'player-container',
      'connection-log-popup',
      'device-info-overlay',
      'loading',
      'error'
    ];

    // Create observer for each element
    elementsToWatch.forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            const now = Date.now();
            // Throttle logging to avoid spam (max 1 log per 50ms)
            if (now - lastLogTime < 50) return;
            lastLogTime = now;

            const styles = window.getComputedStyle(element);
            const change = {
              timestamp: now,
              element: id,
              display: styles.display,
              visibility: styles.visibility,
              opacity: styles.opacity,
              zIndex: styles.zIndex
            };

            window.visibilityLog.push(change);
            console.log('[Visibility]', JSON.stringify(change));
          });
        });

        observer.observe(element, {
          attributes: true,
          attributeFilter: ['style', 'class'],
          attributeOldValue: true
        });
      }
    });

    // Also monitor for any element additions/removals
    const bodyObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1 && node.className && node.className.includes('activation')) {
              console.log('[Flicker] Activation element added:', node.className);
            }
          });
          mutation.removedNodes.forEach(node => {
            if (node.nodeType === 1 && node.className && node.className.includes('activation')) {
              console.log('[Flicker] Activation element removed:', node.className);
            }
          });
        }
      });
    });

    bodyObserver.observe(document.body, { childList: true, subtree: true });

    console.log('[Test] Extended monitoring started');
  });

  // Get initial state
  const initialState = await page.evaluate(() => {
    const getState = (id) => {
      const el = document.getElementById(id);
      if (!el) return null;
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        visibility: styles.visibility,
        opacity: styles.opacity,
        zIndex: styles.zIndex
      };
    };

    return {
      shell: getState('shell-container'),
      player: getState('player-container'),
      popup: getState('connection-log-popup'),
      loading: getState('loading')
    };
  });

  console.log('Initial State:');
  console.log('  Shell:', initialState.shell);
  console.log('  Player:', initialState.player);
  console.log('  Popup:', initialState.popup);
  console.log('  Loading:', initialState.loading);

  // Wait before clicking
  console.log('\n⏱️  Waiting 3 seconds before click...');
  await page.waitForTimeout(3000);

  // Click network status
  console.log('\n👆 Clicking network status icon...');
  const networkIcon = await page.$('#network-status');

  if (networkIcon) {
    const startTime = Date.now();
    await networkIcon.click();

    console.log('\n⏱️  Monitoring for 30 seconds after click...');
    console.log('    Watch for any flickering or visibility changes...\n');

    // Monitor for 30 seconds
    for (let i = 0; i < 30; i++) {
      await page.waitForTimeout(1000);

      // Get current log count
      const logCount = await page.evaluate(() => window.visibilityLog.length);

      // Get current state every 5 seconds
      if (i % 5 === 0) {
        const currentState = await page.evaluate(() => {
          const getState = (id) => {
            const el = document.getElementById(id);
            if (!el) return null;
            const styles = window.getComputedStyle(el);
            return { display: styles.display, opacity: styles.opacity };
          };
          return {
            shell: getState('shell-container'),
            popup: getState('connection-log-popup')
          };
        });

        console.log(`  [${i}s] Shell: ${currentState.shell?.display} (opacity: ${currentState.shell?.opacity}), ` +
                    `Popup: ${currentState.popup?.display} (opacity: ${currentState.popup?.opacity}), ` +
                    `Changes logged: ${logCount}`);
      }
    }

    const endTime = Date.now();
    console.log(`\n⏱️  Monitoring completed (${((endTime - startTime) / 1000).toFixed(1)}s)\n`);

    // Get final report
    const changes = await page.evaluate(() => window.visibilityLog || []);

    console.log('='.repeat(60));
    console.log(`📊 TOTAL VISIBILITY CHANGES: ${changes.length}`);
    console.log('='.repeat(60));

    if (changes.length > 0) {
      console.log('\n⚠️  WARNING: Elements changed during monitoring!\n');

      // Group by element
      const byElement = {};
      changes.forEach(change => {
        if (!byElement[change.element]) {
          byElement[change.element] = [];
        }
        byElement[change.element].push(change);
      });

      Object.keys(byElement).forEach(element => {
        const elementChanges = byElement[element];
        console.log(`\n${element} (${elementChanges.length} changes):`);

        // Show first 5 and last 5 changes
        const showCount = Math.min(5, elementChanges.length);
        console.log('  First changes:');
        elementChanges.slice(0, showCount).forEach((change, i) => {
          const time = new Date(change.timestamp).toLocaleTimeString();
          console.log(`    ${i + 1}. [${time}] display:${change.display}, opacity:${change.opacity}, z-index:${change.zIndex}`);
        });

        if (elementChanges.length > 10) {
          console.log('  ...');
          console.log('  Last changes:');
          elementChanges.slice(-showCount).forEach((change, i) => {
            const time = new Date(change.timestamp).toLocaleTimeString();
            console.log(`    ${i + 1}. [${time}] display:${change.display}, opacity:${change.opacity}, z-index:${change.zIndex}`);
          });
        }
      });

      // Check for shell-container flickering specifically
      const shellChanges = byElement['shell-container'] || [];
      if (shellChanges.length > 0) {
        console.log('\n' + '='.repeat(60));
        console.log('❌ FLICKERING DETECTED IN ACTIVATION SCREEN (shell-container)');
        console.log(`   Total changes: ${shellChanges.length}`);
        console.log('='.repeat(60));
      }

    } else {
      console.log('\n✅ NO VISIBILITY CHANGES DETECTED');
      console.log('   - No flickering observed');
      console.log('   - All elements remained stable');
    }

    // Take final screenshot
    await page.screenshot({ path: 'screenshot-extended-test.png' });
    console.log('\n📸 Screenshot saved: screenshot-extended-test.png');

  } else {
    console.log('❌ Network status icon not found!');
  }

  await browser.close();
  console.log('\n✅ Extended test completed');
})();
