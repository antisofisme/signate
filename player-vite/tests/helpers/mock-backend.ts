/**
 * Mock Backend Utilities
 * For controlling mock API responses in integration tests
 */

import { server, http, HttpResponse } from '../integration-setup';
import type { PlaylistSyncResponse } from '../../src/player/types/player.types';

/**
 * Setup mock backend with controlled responses
 */
export function setupMockBackend() {
  let currentPlaylistResponse: PlaylistSyncResponse | null = null;

  return {
    /**
     * Mock playlist endpoint response
     */
    mockPlaylistResponse(response: PlaylistSyncResponse) {
      currentPlaylistResponse = response;

      server.use(
        http.get('http://192.168.5.12:8001/api/v1/client/playlist', () => {
          return HttpResponse.json(currentPlaylistResponse);
        })
      );
    },

    /**
     * Mock 404 error
     */
    mockNotFound() {
      server.use(
        http.get('http://192.168.5.12:8001/api/v1/client/playlist', () => {
          return HttpResponse.json(
            { error: 'Not found' },
            { status: 404 }
          );
        })
      );
    },

    /**
     * Mock network timeout
     */
    mockTimeout() {
      server.use(
        http.get('http://192.168.5.12:8001/api/v1/client/playlist', async () => {
          await new Promise((resolve) => setTimeout(resolve, 30000));
          return HttpResponse.json({});
        })
      );
    },

    /**
     * Mock 500 server error
     */
    mockServerError() {
      server.use(
        http.get('http://192.168.5.12:8001/api/v1/client/playlist', () => {
          return HttpResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
          );
        })
      );
    },

    /**
     * Reset to default handlers
     */
    reset() {
      server.resetHandlers();
      currentPlaylistResponse = null;
    },
  };
}
