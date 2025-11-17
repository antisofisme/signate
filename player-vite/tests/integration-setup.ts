/**
 * Integration Test Setup
 * Mock Service Worker (MSW) configuration for API mocking
 */

import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { beforeAll, afterAll, afterEach } from 'vitest';

// Mock backend handlers
const handlers = [
  // Playlist endpoint
  http.get('http://192.168.5.12:8001/api/v1/client/playlist', ({ request }) => {
    const url = new URL(request.url);
    const deviceId = url.searchParams.get('device_id');

    if (!deviceId) {
      return HttpResponse.json(
        { error: 'device_id required' },
        { status: 400 }
      );
    }

    return HttpResponse.json({
      playlist: {
        id: 1,
        name: 'Default Playlist',
        is_active: true,
        items: [
          {
            id: 1,
            content_id: 101,
            duration: 10,
            order: 0,
            content: {
              id: 101,
              name: 'Test Video',
              type: 'video',
              file_path: 'http://example.com/video.mp4',
              url: null,
              thumbnail_path: null,
              metadata: null,
            },
          },
        ],
      },
      has_changes: true,
    });
  }),

  // Heartbeat endpoint
  http.post('http://192.168.5.12:8001/api/v1/client/heartbeat', async () => {
    return HttpResponse.json({ success: true });
  }),

  // Activation endpoint
  http.post('http://192.168.5.12:8001/api/v1/client/activate', async ({ request }) => {
    const body = await request.json() as any;

    if (body.activation_code === '123456') {
      return HttpResponse.json({
        device_id: 'test-device-123',
        success: true,
      });
    }

    return HttpResponse.json(
      { error: 'Invalid activation code' },
      { status: 400 }
    );
  }),
];

// Create MSW server
const server = setupServer(...handlers);

// Start server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
});

// Close server after all tests
afterAll(() => {
  server.close();
});

// Export server for custom handlers in tests
export { server, http, HttpResponse };
