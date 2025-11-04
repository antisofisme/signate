/**
 * Device Types
 * TypeScript interfaces for device management
 */

export type DeviceStatus = 'pending' | 'active' | 'inactive';
export type DeviceType = 'tv' | 'monitor';
export type LocationType = 'guest_room' | 'lobby' | 'conference_room' | 'restaurant' | 'other';
export type PrivacyMode = 'none' | 'limited' | 'full';

export interface Device {
  id: number;
  device_type: DeviceType;
  device_name: string;
  organization_id: number;

  // Activation
  unique_code: string | null;
  code_expires_at: string | null;
  device_uuid: string | null;

  // Network info
  ip_address: string | null;
  platform: string | null;

  // Device metadata
  screen_width: number | null;
  screen_height: number | null;
  viewport_width: number | null;
  viewport_height: number | null;
  device_pixel_ratio: number | null;
  user_agent: string | null;
  connection_type: string | null;
  connection_speed: number | null;

  // WebOS specific
  model_name: string | null;
  firmware_version: string | null;

  // Status
  status: DeviceStatus;
  last_seen: string | null;
  is_online: boolean;

  // Display settings
  rotation: number;
  volume_enabled: boolean;

  // Hotel-specific
  room_number: string | null;
  location_type: LocationType;
  supports_personalization: boolean;
  privacy_mode: PrivacyMode;

  // Metadata
  created_at: string;
  updated_at: string | null;
  released_at: string | null;
}

export interface DeviceListResponse {
  devices: Device[];
  total: number;
  online: number;
}

export interface ActivateDeviceRequest {
  unique_code: string;
  device_name?: string;
  room_number?: string;
  location_type?: LocationType;
}

export interface UpdateDeviceRequest {
  device_name?: string;
  room_number?: string;
  location_type?: LocationType;
  rotation?: number;
  volume_enabled?: boolean;
  supports_personalization?: boolean;
  privacy_mode?: PrivacyMode;
}

export interface DeviceFilters {
  status?: DeviceStatus;
  online_only?: boolean;
}
