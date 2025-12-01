/**
 * Playlist Domain Types
 */

export interface Playlist {
  id: number;
  name: string;
  description?: string | null;
  is_active: boolean;
  priority: number;
  schedule?: Record<string, any> | null;
  organization_id: number;
  created_by?: number | null;
  created_at: string;
  updated_at?: string | null;
  deleted_at?: string | null;

  // Computed fields
  content_count: number;
  total_duration: number;
  device_count: number;

  // Relationships
  contents?: PlaylistContent[];
  devices?: PlaylistDevice[];
  // NOTE: tags field removed - Tags are NOT assigned to Playlists
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
  location?: string;
}

// NOTE: PlaylistTag interface removed - Tags are NOT assigned to Playlists
// Tags are assigned to Devices and Content only

export interface CreatePlaylistRequest {
  name: string;
  description?: string;
  is_active?: boolean;
  priority?: number;
  schedule?: Record<string, any>;
}

export interface UpdatePlaylistRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
  priority?: number;
  schedule?: Record<string, any>;
}

export interface AddContentRequest {
  content_ids: number[];
}

export interface ReorderContentRequest {
  content_items: Array<{
    id: number;
    order_index: number;
    duration?: number;
  }>;
}

export interface AssignDevicesRequest {
  device_ids: number[];
}

// NOTE: AssignTagsRequest removed - Tags are NOT assigned to Playlists
// Tags are assigned to Devices and Content only

export interface PlaylistAssignmentsResponse {
  devices: PlaylistDevice[];
  // NOTE: tags field removed - Tags are NOT assigned to Playlists
}

export interface BulkOperationResponse {
  success: boolean;
  message: string;
  added?: number;
  assigned?: number;
  skipped_missing?: number[];
  skipped_duplicate?: number[];
}

export interface RemoveOperationResponse {
  success: boolean;
  message: string;
  removed?: number;
}
