/**
 * Playlist Domain Types
 */

export interface Playlist {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  priority?: number;
  created_at: string;
  updated_at: string;
  organization_id: number;

  // Relationships
  contents?: PlaylistContent[];
  devices?: PlaylistDevice[];
}

export interface PlaylistContent {
  id: number;
  content_id: number;
  playlist_id: number;
  order_index: number;
  duration?: number; // Override content duration

  // Content details (populated)
  title?: string;
  file_type?: string;
  file_path?: string;
  thumbnail_path?: string;
}

export interface PlaylistDevice {
  id: number;
  device_id: number;
  device_name?: string;
  assigned_at: string;
}

export interface CreatePlaylistRequest {
  name: string;
  description?: string;
  is_active?: boolean;
  priority?: number;
  content_ids?: number[];
}

export interface UpdatePlaylistRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  priority?: number;
}

export interface ReorderPlaylistRequest {
  content_orders: Array<{
    content_id: number;
    order_index: number;
  }>;
}

export interface AssignDeviceRequest {
  device_ids: number[];
}

export interface UnassignDeviceRequest {
  device_ids: number[];
}
