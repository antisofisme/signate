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

            const downloadSource = results.download.source || 'Internet';
            const uploadTarget = results.upload.target || 'Internet';
            const summary = `[Shell/Network] ✅ Diagnostics complete: Ping to BACKEND ${results.ping.avg}ms (min: ${results.ping.min}ms, max: ${results.ping.max}ms), Download from ${downloadSource}: ${results.download.mbps.toFixed(2)} Mbps, Upload to ${uploadTarget}: ${results.upload.mbps.toFixed(2)} Mbps`;
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
                        source: 'viewer'
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

        this.sendDirectLog('info', `[Shell/Network] Testing ping to BACKEND server (${sampleCount} samples)...`);

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
     * Optimized for accurate high-speed measurements (60-100+ Mbps)
     */
    testDownloadSpeed: async function() {
        this.sendDirectLog('info', '[Shell/Network] Testing download speed from CLOUDFLARE CDN...');

        const testDurationSeconds = 10; // 10 seconds for better accuracy
        let totalBytes = 0;
        const startTime = performance.now();

        try {
            // Use Cloudflare speed test endpoint with larger chunks
            const testUrls = [
                'https://speed.cloudflare.com/__down?bytes=10000000', // 10MB chunks
                'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png', // Fallback
            ];

            let testUrl = testUrls[0];
            let usedSource = 'Cloudflare';

            // Parallel downloads for maximum throughput
            const parallelRequests = 3; // 3 simultaneous downloads
            const downloadPromises = [];

            for (let i = 0; i < parallelRequests; i++) {
                const downloadTask = async () => {
                    while ((performance.now() - startTime) / 1000 < testDurationSeconds) {
                        try {
                            const response = await fetch(testUrl + '&nocache=' + Date.now() + '_' + i, {
                                method: 'GET',
                                cache: 'no-cache',
                                mode: 'cors'
                            });

                            if (!response.ok && testUrl === testUrls[0]) {
                                // Fallback to Google CDN if Cloudflare fails
                                if (i === 0) { // Only log once
                                    this.sendDirectLog('warn', '[Shell/Network] Cloudflare failed, switching to GOOGLE CDN...');
                                }
                                testUrl = testUrls[1];
                                usedSource = 'Google CDN';
                                continue;
                            }

                            const blob = await response.blob();
                            totalBytes += blob.size;

                        } catch (fetchError) {
                            // If first URL fails, try fallback
                            if (testUrl === testUrls[0]) {
                                if (i === 0) { // Only log once
                                    this.sendDirectLog('warn', '[Shell/Network] Cloudflare failed, switching to GOOGLE CDN...');
                                }
                                testUrl = testUrls[1];
                                usedSource = 'Google CDN';
                            } else {
                                // Silent fail for individual requests
                                break;
                            }
                        }
                    }
                };

                downloadPromises.push(downloadTask());
            }

            // Wait for all parallel downloads to complete
            await Promise.all(downloadPromises);

            const endTime = performance.now();
            const durationSeconds = (endTime - startTime) / 1000;
            const bytesPerSecond = totalBytes / durationSeconds;
            const mbps = (bytesPerSecond * 8) / (1024 * 1024); // Convert to Mbps

            this.sendDirectLog('info', `[Shell/Network] Download test completed using ${usedSource}`);

            return {
                bytes: totalBytes,
                duration: durationSeconds,
                mbps: mbps,
                source: usedSource
            };
        } catch (error) {
            this.sendDirectLog('error', `[Shell/Network] ❌ Download speed test failed: ${error.message}`);
            return { bytes: 0, duration: 0, mbps: 0 };
        }
    },

    /**
     * Test upload speed
     * Uploads dummy data to backend server to measure upload bandwidth
     * Optimized for accurate high-speed measurements (60-100+ Mbps)
     */
    testUploadSpeed: async function() {
        const state = window.ShellState;
        this.sendDirectLog('info', '[Shell/Network] Testing upload speed to BACKEND...');

        const testDurationSeconds = 10; // 10 seconds for better accuracy
        let totalBytes = 0;
        const startTime = performance.now();

        try {
            const uploadUrl = `${state.API_BASE_URL}/api/speedtest/upload`;
            const chunkSize = 1024 * 1024; // 1MB chunks

            // Pre-generate test data (reuse to save CPU)
            const testData = new ArrayBuffer(chunkSize);
            const view = new Uint8Array(testData);
            for (let i = 0; i < view.length; i++) {
                view[i] = Math.floor(Math.random() * 256);
            }

            // Parallel uploads for maximum throughput
            const parallelRequests = 3; // 3 simultaneous uploads
            const uploadPromises = [];

            for (let i = 0; i < parallelRequests; i++) {
                const uploadTask = async () => {
                    while ((performance.now() - startTime) / 1000 < testDurationSeconds) {
                        try {
                            const response = await fetch(uploadUrl, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/octet-stream' },
                                body: testData,
                                cache: 'no-cache'
                            });

                            if (response.ok) {
                                totalBytes += chunkSize;
                            }
                        } catch (error) {
                            // Silent fail for individual requests
                            break;
                        }
                    }
                };

                uploadPromises.push(uploadTask());
            }

            // Wait for all parallel uploads to complete
            await Promise.all(uploadPromises);

            const endTime = performance.now();
            const durationSeconds = (endTime - startTime) / 1000;
            const bytesPerSecond = totalBytes / durationSeconds;
            const mbps = (bytesPerSecond * 8) / (1024 * 1024); // Convert to Mbps

            this.sendDirectLog('info', `[Shell/Network] Upload test completed to Backend`);

            return {
                bytes: totalBytes,
                duration: durationSeconds,
                mbps: mbps,
                target: 'Backend'
            };
        } catch (error) {
            this.sendDirectLog('error', `[Shell/Network] ❌ Upload speed test failed: ${error.message}`);
            return { bytes: 0, duration: 0, mbps: 0, target: 'Backend' };
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
                        source: 'viewer',
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
