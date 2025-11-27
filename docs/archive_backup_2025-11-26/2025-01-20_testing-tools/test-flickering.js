const { chromium } = require('playwright');

(async () => {
  console.log('🔍 Testing for flickering when opening popup...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  console.log('📍 Loading player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  console.log('\n=== CHECKING FOR FLICKERING ===\n');

  // Monitor visibility changes
  const visibilityLog = [];

  // Start monitoring shell-container and player-container visibility
  await page.evaluate(() => {
    window.visibilityChanges = [];

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
          const target = mutation.target;
          const id = target.id;
          const display = window.getComputedStyle(target).display;

          if (id === 'shell-container' || id === 'player-container') {
            window.visibilityChanges.push({
              timestamp: Date.now(),
              element: id,
              display: display,
              visibility: window.getComputedStyle(target).visibility,
              opacity: window.getComputedStyle(target).opacity
            });
          }
        }
      });
    });

    // Observe shell and player containers
    const shellContainer = document.getElementById('shell-container');
    const playerContainer = document.getElementById('player-container');

    if (shellContainer) {
      observer.observe(shellContainer, { attributes: true, attributeFilter: ['style'] });
    }
    if (playerContainer) {
      observer.observe(playerContainer, { attributes: true, attributeFilter: ['style'] });
    }

    console.log('[Test] Mutation observer started');
  });

  // Get initial state
  const initialState = await page.evaluate(() => {
    const shell = document.getElementById('shell-container');
    const player = document.getElementById('player-container');
    const activationScreen = document.querySelector('.activation-container');

    return {
      shell: {
        display: shell ? window.getComputedStyle(shell).display : null,
        visibility: shell ? window.getComputedStyle(shell).visibility : null,
        zIndex: shell ? window.getComputedStyle(shell).zIndex : null
      },
      player: {
        display: player ? window.getComputedStyle(player).display : null,
        visibility: player ? window.getComputedStyle(player).visibility : null,
        zIndex: player ? window.getComputedStyle(player).zIndex : null
      },
      activationScreen: {
        exists: !!activationScreen,
        display: activationScreen ? window.getComputedStyle(activationScreen).display : null
      }
    };
  });

  console.log('Initial State:');
  console.log('  Shell Container:', initialState.shell);
  console.log('  Player Container:', initialState.player);
  console.log('  Activation Screen:', initialState.activationScreen);

  // Take screenshot before click
  await page.screenshot({ path: 'screenshot-before-popup.png' });
  console.log('\n📸 Screenshot before click saved');

  // Click network status icon
  console.log('\n👆 Clicking network status icon...');
  const networkIcon = await page.$('#network-status');

  if (networkIcon) {
    await networkIcon.click();

    // Wait a bit and monitor changes
    await page.waitForTimeout(2000);

    // Get visibility changes
    const changes = await page.evaluate(() => window.visibilityChanges || []);

    console.log(`\n📊 Detected ${changes.length} visibility changes during popup open:`);

    if (changes.length > 0) {
      console.log('⚠️  WARNING: Elements changed visibility during popup open!');
      changes.forEach((change, index) => {
        console.log(`  ${index + 1}. [${new Date(change.timestamp).toLocaleTimeString()}] ${change.element}:`);
        console.log(`     display: ${change.display}, visibility: ${change.visibility}, opacity: ${change.opacity}`);
      });
    } else {
      console.log('✅ No visibility changes detected - no flickering!');
    }

    // Check popup state
    const popupState = await page.evaluate(() => {
      const popup = document.getElementById('connection-log-popup');
      if (!popup) return { exists: false };

      const styles = window.getComputedStyle(popup);
      return {
        exists: true,
        display: styles.display,
        visibility: styles.visibility,
        opacity: styles.opacity,
        zIndex: styles.zIndex,
        position: styles.position,
        background: styles.background
      };
    });

    console.log('\nPopup State:');
    console.log('  Exists:', popupState.exists ? '✅ YES' : '❌ NO');
    if (popupState.exists) {
      console.log('  Display:', popupState.display);
      console.log('  Visibility:', popupState.visibility);
      console.log('  Opacity:', popupState.opacity);
      console.log('  Z-Index:', popupState.zIndex);
      console.log('  Position:', popupState.position);
      console.log('  Background:', popupState.background.substring(0, 50) + '...');
    }

    // Take screenshot with popup open
    await page.screenshot({ path: 'screenshot-popup-open.png' });
    console.log('\n📸 Screenshot with popup open saved');

    // Check if activation screen is visible behind popup
    const backgroundCheck = await page.evaluate(() => {
      const shell = document.getElementById('shell-container');
      const popup = document.getElementById('connection-log-popup');

      if (!shell || !popup) return { canCheck: false };

      const shellRect = shell.getBoundingClientRect();
      const popupRect = popup.getBoundingClientRect();
      const shellStyles = window.getComputedStyle(shell);
      const popupStyles = window.getComputedStyle(popup);

      return {
        canCheck: true,
        shellVisible: shellStyles.display !== 'none',
        popupCoversScreen: popupRect.width >= window.innerWidth && popupRect.height >= window.innerHeight,
        shellZIndex: shellStyles.zIndex,
        popupZIndex: popupStyles.zIndex,
        popupBlocksShell: parseInt(popupStyles.zIndex) > parseInt(shellStyles.zIndex || '0')
      };
    });

    console.log('\nBackground Check:');
    if (backgroundCheck.canCheck) {
      console.log('  Shell still visible:', backgroundCheck.shellVisible ? '⚠️  YES (might flicker)' : '✅ NO');
      console.log('  Popup covers screen:', backgroundCheck.popupCoversScreen ? '✅ YES' : '❌ NO');
      console.log('  Shell z-index:', backgroundCheck.shellZIndex);
      console.log('  Popup z-index:', backgroundCheck.popupZIndex);
      console.log('  Popup blocks shell:', backgroundCheck.popupBlocksShell ? '✅ YES' : '❌ NO');
    }

    // Final verdict
    console.log('\n' + '='.repeat(50));
    if (changes.length === 0 && popupState.exists && backgroundCheck.popupBlocksShell) {
      console.log('✅ RESULT: NO FLICKERING DETECTED');
      console.log('   - Popup opened cleanly');
      console.log('   - No visibility changes');
      console.log('   - Popup properly covers background');
    } else if (changes.length > 0) {
      console.log('❌ RESULT: FLICKERING DETECTED');
      console.log(`   - ${changes.length} visibility changes observed`);
      console.log('   - Elements changed during popup open');
    } else {
      console.log('⚠️  RESULT: INCONCLUSIVE');
      console.log('   - Check screenshots manually');
    }
    console.log('='.repeat(50));

    // Keep browser open for manual inspection
    console.log('\n⏸️  Browser will stay open for 20 seconds for visual inspection...');
    await page.waitForTimeout(20000);

  } else {
    console.log('❌ Network status icon not found!');
  }

  await browser.close();
  console.log('\n✅ Test completed');
})();
