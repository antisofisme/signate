/**
 * Test Connection Log API Integration
 * Simulates player sending connection logs to backend
 */

const API_BASE = 'http://192.168.5.12:8001/api/v1';

async function testConnectionLogAPI() {
  console.log('=== Testing Connection Log API ===\n');

  // Step 1: Get a real device_id from database
  console.log('1. Checking for existing devices...');
  try {
    const devicesResponse = await fetch(`${API_BASE}/devices`, {
      headers: {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwidXNlcm5hbWUiOiJhZG1pbiIsInJvbGUiOiJBRE1JTiIsIm9yZ2FuaXphdGlvbl9pZCI6NCwiZXhwIjoxNzYzMDUyMDM1LCJpYXQiOjE3NjMwNTAyMzUsInR5cGUiOiJhY2Nlc3MifQ.PGA_7dHdHS4g6gmRLrZjVKqVCm_rIYHlueXJize7vvw'
      }
    });

    const devicesData = await devicesResponse.json();
    console.log('Devices response:', devicesData);

    let deviceId;
    if (devicesData.success && devicesData.data && devicesData.data.length > 0) {
      deviceId = devicesData.data[0].id;
      console.log(`✓ Found device ID: ${deviceId}\n`);
    } else {
      console.log('No devices found. Creating test device first...');
      // For now, let's use a real device_id from database
      deviceId = 6178;
      console.log(`Using device_id: ${deviceId} (from database)\n`);
    }

    // Step 2: Send connection logs (simulating player)
    console.log('2. Sending connection logs to backend...');

    const testLogs = {
      logs: [
        {
          logged_at: new Date().toISOString(),
          event_type: 'network',
          status: 'online',
          latency_ms: 45,
          error_message: null,
          download_speed_mbps: null,
          upload_speed_mbps: null,
          metadata: { test: true }
        },
        {
          logged_at: new Date(Date.now() - 30000).toISOString(),
          event_type: 'server',
          status: 'connected',
          latency_ms: 120,
          error_message: null,
          download_speed_mbps: null,
          upload_speed_mbps: null,
          metadata: { endpoint: '/api/v1/devices/heartbeat' }
        },
        {
          logged_at: new Date(Date.now() - 60000).toISOString(),
          event_type: 'speed_test',
          status: 'tested',
          latency_ms: 35,
          error_message: null,
          download_speed_mbps: 98.5,
          upload_speed_mbps: 45.2,
          metadata: { test_duration_ms: 5000 }
        }
      ]
    };

    console.log('Payload:', JSON.stringify(testLogs, null, 2));

    const response = await fetch(`${API_BASE}/devices/${deviceId}/connection-logs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testLogs)
    });

    const result = await response.json();
    console.log('\nResponse status:', response.status);
    console.log('Response body:', JSON.stringify(result, null, 2));

    if (response.ok) {
      console.log('\n✅ SUCCESS: Connection logs sent successfully!');
      console.log(`Saved ${testLogs.logs.length} log entries`);
    } else {
      console.log('\n❌ FAILED: Connection logs not sent');
      console.log('Error:', result);
    }

    // Step 3: Verify logs were stored in database (optional - requires auth)
    console.log('\n3. Verifying logs in database...');
    console.log('(This would require SQL query or admin API call)');

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testConnectionLogAPI();
