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
        if (this.testInProgress) {
            console.warn('[Network] Diagnostics already in progress, skipping...');
            return this.lastTestResults;
        }

        this.testInProgress = true;
        console.log('[Network] 🌐 Starting network diagnostics...');

        try {
            const results = {
                timestamp: new Date().toISOString(),
                ping: await this.testPing(),
                download: await this.testDownloadSpeed(),
                upload: await this.testUploadSpeed()
            };

            this.lastTestResults = results;

            console.log('[Network] ✅ Diagnostics complete:', {
                ping: `${results.ping.avg}ms (min: ${results.ping.min}ms, max: ${results.ping.max}ms)`,
                download: `${results.download.mbps.toFixed(2)} Mbps`,
                upload: `${results.upload.mbps.toFixed(2)} Mbps`
            });

            // Send results to backend
            await this.sendResults(results);

            return results;
        } catch (error) {
            console.error('[Network] ❌ Diagnostics failed:', error);
            return null;
        } finally {
            this.testInProgress = false;
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

        console.log(`[Network] Testing ping (${sampleCount} samples)...`);

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
                console.warn(`[Network] Ping sample ${i + 1} failed:`, error.message);
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

        console.log('[Network] Testing download speed...');

        // Use backend health endpoint with cache-busting
        // We'll measure how fast we can download multiple requests
        const testSizeKB = 100; // Approximate size to test
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
            console.error('[Network] Download speed test failed:', error);
            return { bytes: 0, duration: 0, mbps: 0 };
        }
    },

    /**
     * Test upload speed
     * Sends dummy data to backend and measures transfer rate
     */
    testUploadSpeed: async function() {
        const state = window.ShellState;

        console.log('[Network] Testing upload speed...');

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
            console.error('[Network] Upload speed test failed:', error);
            return { bytes: 0, duration: 0, mbps: 0 };
        }
    },

    /**
     * Send test results to backend
     */
    sendResults: async function(results) {
        const state = window.ShellState;

        if (!state.deviceId) {
            console.warn('[Network] No device ID, skipping results upload');
            return;
        }

        try {
            console.log('[Network] Sending diagnostics results to backend...');

            const response = await fetch(`${state.API_BASE_URL}/api/client/logs/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: state.deviceId,
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
                console.log('[Network] ✅ Diagnostics results sent to backend');
            } else {
                console.warn('[Network] ⚠️ Failed to send diagnostics results:', response.statusText);
            }
        } catch (error) {
            console.error('[Network] ❌ Error sending diagnostics results:', error);
        }
    },

    /**
     * Start periodic diagnostics
     * Runs on startup, then every 30 minutes
     */
    startPeriodicDiagnostics: function() {
        const DIAGNOSTICS_INTERVAL = 30 * 60 * 1000; // 30 minutes

        console.log('[Network] Starting periodic diagnostics (every 30 minutes)');

        // Run immediately on startup (after 5 seconds to let viewer stabilize)
        setTimeout(() => {
            this.runDiagnostics();
        }, 5000);

        // Then run every 30 minutes
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
