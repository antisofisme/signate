/**
 * Test Utilities for Player Tests
 * Mock data generators and helper functions
 */

import type {
  Playlist,
  PlaylistItem,
  ContentItem,
} from '../../src/player/types/player.types';

/**
 * Create mock playlist with specified number of items
 */
export function createMockPlaylist(
  itemCount: number,
  itemOverrides: Partial<PlaylistItem> = {}
): Playlist {
  const items: PlaylistItem[] = [];

  for (let i = 0; i < itemCount; i++) {
    items.push(
      createMockPlaylistItem({
        id: i + 1,
        order: i,
        ...itemOverrides,
      })
    );
  }

  return {
    id: 1,
    name: 'Test Playlist',
    is_active: true,
    items,
  };
}

/**
 * Create mock playlist item
 */
export function createMockPlaylistItem(
  overrides: Partial<PlaylistItem> = {}
): PlaylistItem {
  const content: ContentItem = {
    id: 1,
    name: 'Test Content',
    type: 'video',
    file_path: 'http://example.com/video.mp4',
    url: null,
    thumbnail_path: null,
    metadata: null,
    ...overrides.content,
  };

  return {
    id: 1,
    content_id: content.id,
    duration: 10,
    order: 0,
    content,
    ...overrides,
  };
}

/**
 * Create valid test item
 */
export function createValidItem(id: number): PlaylistItem {
  return createMockPlaylistItem({
    id,
    content: {
      id: id + 100,
      name: `Valid Item ${id}`,
      type: 'video',
      file_path: `http://example.com/video${id}.mp4`,
      url: null,
      thumbnail_path: null,
      metadata: null,
    },
  });
}

/**
 * Create corrupted test item (404 URL)
 */
export function createCorruptedItem(id: number): PlaylistItem {
  return createMockPlaylistItem({
    id,
    content: {
      id: id + 100,
      name: `Corrupted Item ${id}`,
      type: 'video',
      file_path: 'http://example.com/nonexistent.mp4',
      url: null,
      thumbnail_path: null,
      metadata: null,
    },
  });
}

/**
 * Wait for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Create video element for testing
 */
export function createTestVideoElement(): HTMLVideoElement {
  const video = document.createElement('video');
  video.id = 'test-video';
  video.width = 1920;
  video.height = 1080;
  document.body.appendChild(video);
  return video;
}

/**
 * Cleanup test video element
 */
export function cleanupTestVideoElement(): void {
  const video = document.getElementById('test-video');
  if (video) {
    video.remove();
  }
}
