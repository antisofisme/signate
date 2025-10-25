/**
 * Network Diagnostics Module
 * Tests internet speed and backend latency
 */

window.ShellNetworkDiagnostics = {
    lastTestResults: null,
    testInProgress: false,

    /**
     * Run full network diagnostics
     */
    runDiagnostics: async function() {
        const state = window.ShellState;

        if (this.testInProgress) {
            this.sendDirectLog('warn', '[Network] Diagnostics already in progress, skipping...');
            return this.lastTestResults;
        }

        this.testInProgress = true;
        this.sendDirectLog('info', '[Network] 🌐 Starting network diagnostics...');

        try {
            const results = {
                timestamp: new Date().toISOString(),
                ping: await this.testPing(),
                download: await this.testDownloadSpeed(),
                upload: await this.testUploadSpeed()
            };

            this.lastTestResults = results;

            const summary = `[Network] ✅ Diagnostics complete: Ping ${results.ping.avg}ms (min: ${results.ping.min}ms, max: ${results.ping.max}ms), Download: ${results.download.mbps.toFixed(2)} Mbps, Upload: ${results.upload.mbps.toFixed(2)} Mbps`;
            this.sendDirectLog('info', summary);

            // Send results to backend
            await this.sendResults(results);

            return results;
        } catch (error) {
            this.sendDirectLog('error', `[Network] ❌ Diagnostics failed: ${error.message}`);
            return null;
        } finally {
            this.testInProgress = false;
        }
    },

    /**
     * Send log directly to backend (bypass ShellLogger)
     * Used for logs that need to be sent even before device activation
     */
    sendDirectLog: async function(level, message) {
        const state = window.ShellState;

        // Always print to console for debugging
        state.originalConsole[level](`${message}`);

        // If device not activated yet, skip backend sending
        // (These logs will be in browser console only)
        if (!state.deviceId) {
            return;
        }

        try {
            await fetch(`${state.API_BASE_URL}/api/client/logs/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: parseInt(state.deviceId),
                    logs: [{
                        level: level,
                        message: message,
                        timestamp: new Date().toISOString(),
                        source: 'browser-viewer'
                    }]
                })
            });
        } catch (error) {
            state.originalConsole.error('[Network] Failed to send direct log:', error);
        }
    },

    /**
     * Test ping/latency to backend
     * Sends 10 pings and calculates min/max/avg
     */
    testPing: async function() {
        const state = window.ShellState;
        const pingResults = [];
        const sampleCount = 10;

        this.sendDirectLog('info', `[Network] Testing ping (${sampleCount} samples)...`);

        for (let i = 0; i < sampleCount; i++) {
            const startTime = performance.now();

            try {
                const response = await fetch(`${state.API_BASE_URL}/api/health`, {
                    method: 'GET',
                    cache: 'no-cache'
                });

                if (response.ok) {
                    const endTime = performance.now();
                    const latency = Math.round(endTime - startTime);
                    pingResults.push(latency);
                }
            } catch (error) {
                this.sendDirectLog('warn', `[Network] Ping sample ${i + 1} failed: ${error.message}`);
            }

            // Small delay between pings
            if (i < sampleCount - 1) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
        }

        if (pingResults.length === 0) {
            throw new Error('All ping attempts failed');
        }

        const avg = Math.round(pingResults.reduce((a, b) => a + b, 0) / pingResults.length);
        const min = Math.min(...pingResults);
        const max = Math.max(...pingResults);

        return { min, max, avg, samples: pingResults };
    },

    /**
     * Test download speed
     * Downloads a dummy file and measures transfer rate
     */
    testDownloadSpeed: async function() {
        const state = window.ShellState;

        this.sendDirectLog('info', '[Network] Testing download speed...');

        // Use backend health endpoint with cache-busting
        // We'll measure how fast we can download multiple requests
        const startTime = performance.now();
        let totalBytes = 0;

        try {
            // Make 5 parallel requests to simulate download
            const requests = Array(5).fill().map(async () => {
                const response = await fetch(`${state.API_BASE_URL}/api/health?t=${Date.now()}`, {
                    cache: 'no-cache'
                });
                const text = await response.text();
                return text.length;
            });

            const sizes = await Promise.all(requests);
            totalBytes = sizes.reduce((a, b) => a + b, 0);

            const endTime = performance.now();
            const durationSeconds = (endTime - startTime) / 1000;
            const bytesPerSecond = totalBytes / durationSeconds;
            const mbps = (bytesPerSecond * 8) / (1024 * 1024); // Convert to Mbps

            return {
                bytes: totalBytes,
                duration: durationSeconds,
                mbps: mbps
            };
        } catch (error) {
            this.sendDirectLog('error', `[Network] Download speed test failed: ${error.message}`);
            return { bytes: 0, duration: 0, mbps: 0 };
        }
    },

    /**
     * Test upload speed
     * Sends dummy data to backend and measures transfer rate
     */
    testUploadSpeed: async function() {
        const state = window.ShellState;

        this.sendDirectLog('info', '[Network] Testing upload speed...');

        // Create dummy data to upload (100 KB)
        const testData = 'x'.repeat(100 * 1024);
        const startTime = performance.now();

        try {
            // We'll use the heartbeat endpoint as it accepts POST
            // This is just for speed testing, actual data doesn't matter
            const response = await fetch(`${state.API_BASE_URL}/api/devices/heartbeat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: state.deviceId || 0,
                    device_type: 'monitor',
                    test_data: testData // Add dummy data for upload test
                })
            });

            const endTime = performance.now();
            const durationSeconds = (endTime - startTime) / 1000;
            const bytes = testData.length;
            const bytesPerSecond = bytes / durationSeconds;
            const mbps = (bytesPerSecond * 8) / (1024 * 1024); // Convert to Mbps

            return {
                bytes: bytes,
                duration: durationSeconds,
                mbps: mbps
            };
        } catch (error) {
            this.sendDirectLog('error', `[Network] Upload speed test failed: ${error.message}`);
            return { bytes: 0, duration: 0, mbps: 0 };
        }
    },

    /**
     * Send test results to backend
     * NOTE: Diagnostics hanya jalan setelah device activated, jadi deviceId pasti ada
     */
    sendResults: async function(results) {
        const state = window.ShellState;

        if (!state.deviceId) {
            this.sendDirectLog('error', '[Network] ❌ No device ID - diagnostics should only run after activation!');
            return;
        }

        try {
            this.sendDirectLog('info', '[Network] Sending diagnostics results to backend...');

            const response = await fetch(`${state.API_BASE_URL}/api/client/logs/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: parseInt(state.deviceId),
                    logs: [{
                        level: 'info',
                        message: `Network Diagnostics - Ping: ${results.ping.avg}ms, Download: ${results.download.mbps.toFixed(2)} Mbps, Upload: ${results.upload.mbps.toFixed(2)} Mbps`,
                        timestamp: results.timestamp,
                        source: 'browser-viewer',
                        metadata: JSON.stringify(results)
                    }]
                })
            });

            if (response.ok) {
                this.sendDirectLog('info', '[Network] ✅ Diagnostics results sent to backend');
            } else {
                this.sendDirectLog('warn', `[Network] ⚠️ Failed to send diagnostics results: ${response.statusText}`);
            }
        } catch (error) {
            this.sendDirectLog('error', `[Network] ❌ Error sending diagnostics results: ${error.message}`);
        }
    },

    /**
     * Start periodic diagnostics
     * Runs every 30 minutes (after device activation)
     */
    startPeriodicDiagnostics: function() {
        const DIAGNOSTICS_INTERVAL = 30 * 60 * 1000; // 30 minutes

        console.log('[Network] ⏰ Starting periodic diagnostics (every 30 minutes)');

        // Run every 30 minutes (no immediate run, already done in init or onActivated)
        setInterval(() => {
            this.runDiagnostics();
        }, DIAGNOSTICS_INTERVAL);
    },

    /**
     * Quick ping test (single sample)
     * Used by heartbeat to measure latency
     */
    quickPing: async function() {
        const state = window.ShellState;
        const startTime = performance.now();

        try {
            const response = await fetch(`${state.API_BASE_URL}/api/health`, {
                method: 'GET',
                cache: 'no-cache'
            });

            if (response.ok) {
                const endTime = performance.now();
                return Math.round(endTime - startTime);
            }
        } catch (error) {
            console.warn('[Network] Quick ping failed:', error.message);
        }

        return null;
    }
};
