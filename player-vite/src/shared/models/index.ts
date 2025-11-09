/**
 * Shared Models
 * Barrel export for all model classes
 */

export { Content } from './content.model';
export type { ContentData, ContentMetadata, ContentType } from './content.model';

export { Playlist } from './playlist.model';
export type { PlaylistData } from './playlist.model';

export { Segment } from './segment.model';
export type { SegmentData } from './segment.model';

export { Device } from './device.model';
export type {
  DeviceData,
  DeviceStatus,
  DeviceStorage,
} from './device.model';

// Re-export validation result type (used by all models)
export type { ValidationResult } from './device.model';
