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
            this.sendDirectLog('warn', '[Shell/Network] Diagnostics already in progress, skipping...');
            return this.lastTestResults;
        }

        this.testInProgress = true;
        this.sendDirectLog('info', '[Shell/Network] 🌐 Starting network diagnostics...');

        try {
            const results = {
                timestamp: new Date().toISOString(),
                ping: await this.testPing(),
                download: await this.testDownloadSpeed(),
                upload: await this.testUploadSpeed()
            };

            this.lastTestResults = results;

            const summary = `[Shell/Network] ✅ Diagnostics complete: Ping ${results.ping.avg}ms (min: ${results.ping.min}ms, max: ${results.ping.max}ms), Download: ${results.download.mbps.toFixed(2)} Mbps, Upload: ${results.upload.mbps.toFixed(2)} Mbps`;
            this.sendDirectLog('info', summary);

            // Send results to backend
            await this.sendResults(results);

            return results;
        } catch (error) {
            this.sendDirectLog('error', `[Shell/Network] ❌ Diagnostics failed: ${error.message}`);
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
            state.originalConsole.error('[Shell/Network] Failed to send direct log:', error);
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

        this.sendDirectLog('info', `[Shell/Network] Testing ping (${sampleCount} samples)...`);

        for (let i = 0; i < sampleCount; i++) {
            const startTime = performance.now();

            try {
                const response = await fetch(`${state.API_BASE_URL}/health`, {
                    method: 'GET',
                    cache: 'no-cache'
                });

                if (response.ok) {
                    const endTime = performance.now();
                    const latency = Math.round(endTime - startTime);
                    pingResults.push(latency);
                }
            } catch (error) {
                this.sendDirectLog('warn', `[Shell/Network] Ping sample ${i + 1} failed: ${error.message}`);
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
     * Downloads data from public CDN to measure real internet speed
     */
    testDownloadSpeed: async function() {
        this.sendDirectLog('info', '[Shell/Network] Testing download speed from internet...');

        const testDurationSeconds = 5; // Test for 5 seconds
        const chunkSize = 1024 * 1024; // 1MB chunks
        let totalBytes = 0;
        const startTime = performance.now();

        try {
            // Use Cloudflare speed test endpoint or Google's public CDN
            // These are reliable public endpoints for speed testing
            const testUrls = [
                'https://speed.cloudflare.com/__down?bytes=1000000', // Cloudflare speed test
                'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png', // Google CDN fallback
            ];

            let testUrl = testUrls[0];

            // Download repeatedly until test duration is reached
            while ((performance.now() - startTime) / 1000 < testDurationSeconds) {
                const chunkStart = performance.now();

                try {
                    const response = await fetch(testUrl + '&nocache=' + Date.now(), {
                        method: 'GET',
                        cache: 'no-cache',
                        mode: 'cors'
                    });

                    if (!response.ok && testUrl === testUrls[0]) {
                        // Fallback to Google CDN if Cloudflare fails
                        testUrl = testUrls[1];
                        continue;
                    }

                    const blob = await response.blob();
                    totalBytes += blob.size;

                    // Small delay to prevent overwhelming the connection
                    await new Promise(resolve => setTimeout(resolve, 50));

                } catch (fetchError) {
                    // If first URL fails, try fallback
                    if (testUrl === testUrls[0]) {
                        testUrl = testUrls[1];
                    } else {
                        throw fetchError;
                    }
                }
            }

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
            this.sendDirectLog('error', `[Shell/Network] ❌ Download speed test failed: ${error.message}`);
            return { bytes: 0, duration: 0, mbps: 0 };
        }
    },

    /**
     * Test upload speed
     * Uploads dummy data to backend to measure upload speed
     */
    testUploadSpeed: async function() {
        const state = window.ShellState;

        this.sendDirectLog('info', '[Shell/Network] Testing upload speed...');

        const testDurationSeconds = 5; // Test for 5 seconds
        let totalBytes = 0;
        const startTime = performance.now();

        try {
            // Create dummy data chunks (100KB each)
            const chunkSize = 100 * 1024;

            // Upload repeatedly until test duration is reached
            while ((performance.now() - startTime) / 1000 < testDurationSeconds) {
                const testData = new ArrayBuffer(chunkSize);
                const view = new Uint8Array(testData);

                // Fill with random data
                for (let i = 0; i < view.length; i++) {
                    view[i] = Math.floor(Math.random() * 256);
                }

                const uploadStart = performance.now();

                // Upload to backend speedtest endpoint
                const response = await fetch(`${state.API_BASE_URL}/api/speedtest/upload`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/octet-stream' },
                    body: testData
                });

                if (response.ok) {
                    totalBytes += chunkSize;
                }

                // Small delay to prevent overwhelming the connection
                await new Promise(resolve => setTimeout(resolve, 50));
            }

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
            this.sendDirectLog('error', `[Shell/Network] ❌ Upload speed test failed: ${error.message}`);
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
            this.sendDirectLog('error', '[Shell/Network] ❌ No device ID - diagnostics should only run after activation!');
            return;
        }

        try {
            this.sendDirectLog('info', '[Shell/Network] Sending diagnostics results to backend...');

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
                this.sendDirectLog('info', '[Shell/Network] ✅ Diagnostics results sent to backend');
            } else {
                this.sendDirectLog('warn', `[Shell/Network] ⚠️ Failed to send diagnostics results: ${response.statusText}`);
            }
        } catch (error) {
            this.sendDirectLog('error', `[Shell/Network] ❌ Error sending diagnostics results: ${error.message}`);
        }
    },

    /**
     * Start periodic diagnostics
     * Runs every 30 minutes (after device activation)
     */
    startPeriodicDiagnostics: function() {
        const DIAGNOSTICS_INTERVAL = 30 * 60 * 1000; // 30 minutes

        this.sendDirectLog('info', '[Shell/Network] ⏰ Starting periodic diagnostics (every 30 minutes)');

        // Run every 30 minutes (no immediate run, already done in onActivated)
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
            const response = await fetch(`${state.API_BASE_URL}/health`, {
                method: 'GET',
                cache: 'no-cache'
            });

            if (response.ok) {
                const endTime = performance.now();
                return Math.round(endTime - startTime);
            }
        } catch (error) {
            console.warn('[Shell/Network] Quick ping failed:', error.message);
        }

        return null;
    }
};
