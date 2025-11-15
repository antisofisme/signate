const { chromium } = require('playwright');

(async () => {
  console.log('🔍 Checking icon visibility on player...\n');

  const browser = await chromium.launch({
    headless: false
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  console.log('📍 Loading player...');
  await page.goto('http://192.168.5.12:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  console.log('\n=== CHECKING ICON VISIBILITY ===\n');

  // Check network-status
  const networkStatus = await page.evaluate(() => {
    const el = document.getElementById('network-status');
    if (!el) return { exists: false };

    const rect = el.getBoundingClientRect();
    const styles = window.getComputedStyle(el);

    return {
      exists: true,
      display: styles.display,
      visibility: styles.visibility,
      opacity: styles.opacity,
      position: styles.position,
      top: styles.top,
      left: styles.left,
      zIndex: styles.zIndex,
      width: rect.width,
      height: rect.height,
      x: rect.x,
      y: rect.y,
      inViewport: rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth
    };
  });

  console.log('Network Status Icon:');
  console.log('  Exists:', networkStatus.exists ? '✅ YES' : '❌ NO');
  if (networkStatus.exists) {
    console.log('  Display:', networkStatus.display);
    console.log('  Visibility:', networkStatus.visibility);
    console.log('  Opacity:', networkStatus.opacity);
    console.log('  Position:', `${networkStatus.position} (top: ${networkStatus.top}, left: ${networkStatus.left})`);
    console.log('  Size:', `${networkStatus.width}x${networkStatus.height}px`);
    console.log('  Location:', `(${networkStatus.x}, ${networkStatus.y})`);
    console.log('  In Viewport:', networkStatus.inViewport ? '✅ YES' : '❌ NO');
    console.log('  Z-Index:', networkStatus.zIndex);
  }

  // Check server-status
  const serverStatus = await page.evaluate(() => {
    const el = document.getElementById('server-status');
    if (!el) return { exists: false };

    const rect = el.getBoundingClientRect();
    const styles = window.getComputedStyle(el);

    return {
      exists: true,
      display: styles.display,
      visibility: styles.visibility,
      opacity: styles.opacity,
      position: styles.position,
      top: styles.top,
      left: styles.left,
      width: rect.width,
      height: rect.height,
      x: rect.x,
      y: rect.y
    };
  });

  console.log('\nServer Status Icon:');
  console.log('  Exists:', serverStatus.exists ? '✅ YES' : '❌ NO');
  if (serverStatus.exists) {
    console.log('  Display:', serverStatus.display);
    console.log('  Visibility:', serverStatus.visibility);
    console.log('  Opacity:', serverStatus.opacity);
    console.log('  Position:', `${serverStatus.position} (top: ${serverStatus.top}, left: ${serverStatus.left})`);
    console.log('  Size:', `${serverStatus.width}x${serverStatus.height}px`);
    console.log('  Location:', `(${serverStatus.x}, ${serverStatus.y})`);
  }

  // Check connection-status container
  const connectionStatus = await page.evaluate(() => {
    const el = document.getElementById('connection-status');
    if (!el) return { exists: false };

    const rect = el.getBoundingClientRect();
    const styles = window.getComputedStyle(el);

    return {
      exists: true,
      display: styles.display,
      visibility: styles.visibility,
      opacity: styles.opacity,
      position: styles.position,
      top: styles.top,
      left: styles.left,
      zIndex: styles.zIndex,
      width: rect.width,
      height: rect.height
    };
  });

  console.log('\nConnection Status Container:');
  console.log('  Exists:', connectionStatus.exists ? '✅ YES' : '❌ NO');
  if (connectionStatus.exists) {
    console.log('  Display:', connectionStatus.display);
    console.log('  Visibility:', connectionStatus.visibility);
    console.log('  Opacity:', connectionStatus.opacity);
    console.log('  Position:', `${connectionStatus.position} (top: ${connectionStatus.top}, left: ${connectionStatus.left})`);
    console.log('  Z-Index:', connectionStatus.zIndex);
  }

  // Check if shell-container or player-container is shown
  const containers = await page.evaluate(() => {
    const shell = document.getElementById('shell-container');
    const player = document.getElementById('player-container');

    return {
      shell: {
        exists: !!shell,
        display: shell ? window.getComputedStyle(shell).display : null
      },
      player: {
        exists: !!player,
        display: player ? window.getComputedStyle(player).display : null
      }
    };
  });

  console.log('\nContainer Status:');
  console.log('  Shell Container:', containers.shell.exists ? `display: ${containers.shell.display}` : 'NOT FOUND');
  console.log('  Player Container:', containers.player.exists ? `display: ${containers.player.display}` : 'NOT FOUND');

  // Take screenshot
  console.log('\n📸 Taking screenshot...');
  await page.screenshot({
    path: 'screenshot-icon-check.png',
    fullPage: false
  });
  console.log('✅ Screenshot saved: screenshot-icon-check.png');

  // Draw red boxes around the icons (if they exist)
  if (networkStatus.exists || serverStatus.exists) {
    await page.evaluate(() => {
      const networkEl = document.getElementById('network-status');
      const serverEl = document.getElementById('server-status');

      if (networkEl) {
        networkEl.style.border = '3px solid red';
        networkEl.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
      }
      if (serverEl) {
        serverEl.style.border = '3px solid red';
        serverEl.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
      }
    });

    await page.waitForTimeout(1000);
    await page.screenshot({
      path: 'screenshot-icon-highlighted.png',
      fullPage: false
    });
    console.log('✅ Screenshot with highlights saved: screenshot-icon-highlighted.png');
  }

  console.log('\n⏸️  Browser will stay open for 30 seconds for inspection...');
  await page.waitForTimeout(30000);

  await browser.close();
})();
