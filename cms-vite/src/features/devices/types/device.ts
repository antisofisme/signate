/**
 * Device Domain Types
 */

export type DeviceType = 'tv' | 'monitor';
export type DeviceStatus = 'pending' | 'active' | 'inactive';
export type LocationType = 'guest_room' | 'lobby' | 'conference_room' | 'restaurant' | 'other';
export type PrivacyMode = 'none' | 'limited' | 'full';

export interface Device {
  id: number;
  device_type: DeviceType;
  device_name: string;
  organization_id: number;

  // Activation info
  unique_code?: string;
  code_expires_at?: string;
  device_uuid?: string;

  // Network info
  ip_address?: string;
  platform?: string;
  user_agent?: string;
  connection_type?: string;
  connection_speed?: number;
  connection_drops_count?: number;

  // GeoIP data (Phase 6)
  geo_city?: string;
  geo_country?: string;
  geo_country_code?: string;
  geo_region?: string;
  geo_isp?: string;
  geo_timezone?: string;
  geo_latitude?: number;
  geo_longitude?: number;

  // Device metadata
  screen_width?: number;
  screen_height?: number;
  viewport_width?: number;
  viewport_height?: number;
  device_pixel_ratio?: number;

  // WebOS specific
  model_name?: string;
  firmware_version?: string;

  // Status
  status: DeviceStatus;
  last_seen_at?: string;
  is_online: boolean;  // Computed field from backend

  // Display settings
  rotation: number;
  is_volume_enabled: boolean;

  // Hotel-specific
  room_number?: string;
  location_type: LocationType;
  is_personalization_supported: boolean;
  privacy_mode: PrivacyMode;

  // Assigned playlist info
  playlist_name?: string;  // Name of assigned playlist (from backend JOIN)

  // Metadata
  created_at: string;
  updated_at?: string;
  released_at?: string;

  // Relationships (optional, may not be included in all responses)
  tags?: DeviceTag[];
  playlists?: DevicePlaylist[];
}

export interface DeviceTag {
  id: number;
  tag_name: string;
  color?: string;
}

export interface DevicePlaylist {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  priority?: number;
}

export interface DeviceLog {
  id: number;
  device_id: number;
  event_type: string;
  message: string;
  metadata?: Record<string, any>;
  created_at: string;
}

/**
 * Device Capabilities (static data sent once on startup)
 * Corresponds to device_capabilities table
 */
export interface DeviceCapabilities {
  id: number;
  device_id: number;
  organization_id: number;

  // Screen & Display
  screen_width: number;
  screen_height: number;
  device_pixel_ratio: number;
  display_refresh_rate: number;

  // Hardware
  hardware_concurrency: number;
  device_memory_gb?: number;

  // Video Codec Support
  codec_h264: boolean;
  codec_h265: boolean;
  codec_vp9: boolean;
  codec_av1: boolean;

  // Audio Codec Support
  codec_aac: boolean;
  codec_opus: boolean;

  // Graphics
  webgl_version: string;
  webgl_renderer?: string;
  webgl_vendor?: string;

  // Software
  user_agent: string;
  platform: string;
  player_version: string;

  // Timestamps
  recorded_at: string;
  updated_at?: string;
}

export interface DeviceCommand {
  id: number;
  device_id: number;
  command_type: 'reboot' | 'screenshot' | 'volume' | 'brightness' | 'refresh';
  parameters?: Record<string, any>;
  status: 'pending' | 'sent' | 'completed' | 'failed';
  created_at: string;
  executed_at?: string;
}

export interface MonitorRegisterRequest {
  unique_code: string;
  device_name: string;
}

export interface TVRegisterRequest {
  unique_code: string;
  device_name: string;
}

export interface ActivateDeviceRequest {
  unique_code: string;
}
