/**
 * k6 Load Testing Script for Smart TV Digital Signage System
 *
 * This script tests the performance of the merged Anthias-Backend system
 * under various load conditions to validate our performance optimizations.
 *
 * Usage:
 *   k6 run 03-LOAD_TEST.js
 *   k6 run --vus 100 --duration 30s 03-LOAD_TEST.js
 *   k6 cloud 03-LOAD_TEST.js  # For cloud execution
 */

import http from 'k6/http';
import { check, group, sleep, fail } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://192.168.5.12:8001';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'your-auth-token-here';

// Custom metrics
const errorRate = new Rate('errors');
const cacheHitRate = new Rate('cache_hits');
const playlistGenTime = new Trend('playlist_generation_time');
const contentListTime = new Trend('content_list_time');
const deviceUpdateTime = new Trend('device_update_time');
const uploadTime = new Trend('upload_time');

// Test scenarios
export const options = {
  scenarios: {
    // Scenario 1: Gradual ramp-up to find breaking point
    gradual_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },   // Warm up to 100 users
        { duration: '5m', target: 100 },   // Stay at 100 users
        { duration: '2m', target: 500 },   // Ramp up to 500 users
        { duration: '5m', target: 500 },   // Stay at 500 users
        { duration: '2m', target: 1000 },  // Ramp up to 1000 users
        { duration: '5m', target: 1000 },  // Stay at 1000 users (peak)
        { duration: '2m', target: 0 },     // Ramp down to 0
      ],
    },

    // Scenario 2: Spike test for sudden load
    spike_test: {
      executor: 'ramping-vus',
      startTime: '20m',  // Start after gradual_load
      startVUs: 0,
      stages: [
        { duration: '10s', target: 0 },    // Start quiet
        { duration: '10s', target: 1000 }, // Spike to 1000 users
        { duration: '2m', target: 1000 },  // Hold spike
        { duration: '10s', target: 0 },    // Drop to 0
      ],
    },

    // Scenario 3: Steady state for cache testing
    steady_state: {
      executor: 'constant-vus',
      vus: 200,
      duration: '10m',
      startTime: '25m',  // Start after spike_test
    },
  },

  thresholds: {
    // Response time thresholds
    http_req_duration: ['p(95)<500', 'p(99)<1000'],

    // Custom metric thresholds
    errors: ['rate<0.01'],                    // Error rate under 1%
    cache_hits: ['rate>0.8'],                  // Cache hit rate over 80%
    playlist_generation_time: ['p(95)<100'],  // 95% under 100ms
    content_list_time: ['p(95)<200'],         // 95% under 200ms
    device_update_time: ['p(95)<150'],        // 95% under 150ms

    // Request rate
    http_reqs: ['rate>1000'],                 // At least 1000 req/s
  },
};

// Setup function (runs once at the beginning)
export function setup() {
  // Login and get authentication token if needed
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    username: 'admin',
    password: 'admin123',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  if (loginRes.status !== 200) {
    fail('Login failed');
  }

  const authToken = loginRes.json('access_token');

  // Create test data
  const testData = {
    authToken: authToken,
    deviceIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    playlistIds: [1, 2, 3, 4, 5],
    contentIds: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  };

  return testData;
}

// Main test function
export default function(data) {
  const headers = {
    'Authorization': `Bearer ${data.authToken}`,
    'Content-Type': 'application/json',
  };

  // Test Group 1: Playlist Operations (Most Critical)
  group('Playlist Operations', () => {
    const playlistId = randomItem(data.playlistIds);

    // Get playlist sequence (should be cached)
    const startTime = Date.now();
    const sequenceRes = http.get(
      `${BASE_URL}/api/playlists/${playlistId}/sequence`,
      { headers }
    );
    const duration = Date.now() - startTime;

    playlistGenTime.add(duration);

    check(sequenceRes, {
      'playlist sequence status 200': (r) => r.status === 200,
      'playlist sequence fast': (r) => r.timings.duration < 100,
      'playlist has content': (r) => JSON.parse(r.body).data.length > 0,
    });

    // Check if response was cached
    if (sequenceRes.headers['X-Cache-Status'] === 'HIT') {
      cacheHitRate.add(1);
    } else {
      cacheHitRate.add(0);
    }

    errorRate.add(sequenceRes.status !== 200);
  });

  // Test Group 2: Content Operations
  group('Content Operations', () => {
    // List content with pagination
    const startTime = Date.now();
    const contentRes = http.get(
      `${BASE_URL}/api/content?page=1&limit=50`,
      { headers }
    );
    const duration = Date.now() - startTime;

    contentListTime.add(duration);

    check(contentRes, {
      'content list status 200': (r) => r.status === 200,
      'content list fast': (r) => r.timings.duration < 200,
      'content list has items': (r) => JSON.parse(r.body).data.length > 0,
    });

    errorRate.add(contentRes.status !== 200);

    // Get content details
    const contentId = randomItem(data.contentIds);
    const detailRes = http.get(
      `${BASE_URL}/api/content/${contentId}`,
      { headers }
    );

    check(detailRes, {
      'content detail status 200': (r) => r.status === 200,
      'content detail has url': (r) => JSON.parse(r.body).data.file_url != null,
    });
  });

  // Test Group 3: Device Operations
  group('Device Operations', () => {
    const deviceId = randomItem(data.deviceIds);

    // Device heartbeat
    const startTime = Date.now();
    const heartbeatRes = http.post(
      `${BASE_URL}/api/devices/${deviceId}/heartbeat`,
      JSON.stringify({ status: 'online' }),
      { headers }
    );
    const duration = Date.now() - startTime;

    deviceUpdateTime.add(duration);

    check(heartbeatRes, {
      'heartbeat status 200': (r) => r.status === 200,
      'heartbeat fast': (r) => r.timings.duration < 50,
    });

    errorRate.add(heartbeatRes.status !== 200);

    // Get device content
    const contentRes = http.get(
      `${BASE_URL}/api/devices/${deviceId}/content`,
      { headers }
    );

    check(contentRes, {
      'device content status 200': (r) => r.status === 200,
      'device content not empty': (r) => {
        const body = JSON.parse(r.body);
        return body.data && (body.data.content.length > 0 || body.data.playlists.length > 0);
      },
    });
  });

  // Test Group 4: Search and Filter Operations
  group('Search Operations', () => {
    // Search content
    const searchRes = http.get(
      `${BASE_URL}/api/content?search=video`,
      { headers }
    );

    check(searchRes, {
      'search status 200': (r) => r.status === 200,
      'search results relevant': (r) => {
        const results = JSON.parse(r.body).data;
        return results.length > 0;
      },
    });

    // Filter by tag
    const tagRes = http.get(
      `${BASE_URL}/api/content?tag_id=1`,
      { headers }
    );

    check(tagRes, {
      'tag filter status 200': (r) => r.status === 200,
    });
  });

  // Test Group 5: Dashboard Statistics
  group('Dashboard Operations', () => {
    // Get dashboard stats
    const statsRes = http.get(
      `${BASE_URL}/api/dashboard/stats`,
      { headers }
    );

    check(statsRes, {
      'dashboard stats status 200': (r) => r.status === 200,
      'dashboard stats complete': (r) => {
        const stats = JSON.parse(r.body).data;
        return stats.devices_online !== undefined &&
               stats.total_content !== undefined;
      },
    });

    // Get activity logs
    const logsRes = http.get(
      `${BASE_URL}/api/activities?limit=10`,
      { headers }
    );

    check(logsRes, {
      'activity logs status 200': (r) => r.status === 200,
    });
  });

  // Random sleep between requests (0.5-2 seconds)
  sleep(randomIntBetween(0.5, 2));
}

// Teardown function (runs once at the end)
export function teardown(data) {
  // Cleanup test data if needed
  console.log('Test completed. Cleaning up...');

  // Generate summary report
  console.log('\n=== Performance Test Summary ===');
  console.log(`Error Rate: ${errorRate.rate * 100}%`);
  console.log(`Cache Hit Rate: ${cacheHitRate.rate * 100}%`);
}

// Helper function to simulate file upload (optional, heavy test)
export function uploadTest(data) {
  const headers = {
    'Authorization': `Bearer ${data.authToken}`,
  };

  // Create a small test file
  const file = {
    file: http.file('test-image.jpg', 'Test image content', 'image/jpeg'),
    title: `Test Upload ${Date.now()}`,
    duration: 10,
  };

  const startTime = Date.now();
  const uploadRes = http.post(
    `${BASE_URL}/api/content/upload`,
    file,
    { headers }
  );
  const duration = Date.now() - startTime;

  uploadTime.add(duration);

  check(uploadRes, {
    'upload status 201': (r) => r.status === 201,
    'upload returns id': (r) => JSON.parse(r.body).data.id != null,
    'upload under 2s': (r) => r.timings.duration < 2000,
  });

  errorRate.add(uploadRes.status !== 201);
}