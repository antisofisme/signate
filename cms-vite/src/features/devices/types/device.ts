/**
 * Device Domain Types
 */

export type DeviceType = 'tv' | 'monitor';
export type DeviceStatus = 'pending' | 'active' | 'inactive';

export interface Device {
  id: number;
  device_type: DeviceType;
  device_name: string;
  ip_address?: string;
  unique_code: string;
  code_expires_at?: string;
  platform?: string;
  model_name?: string;
  firmware_version?: string;
  status: DeviceStatus;
  last_seen?: string;
  created_at: string;
  updated_at: string;
  organization_id: number;

  // Screen info
  screen_width?: number;
  screen_height?: number;
  viewport_width?: number;
  viewport_height?: number;
  device_pixel_ratio?: number;

  // Network info
  user_agent?: string;
  connection_type?: string;
  connection_speed?: string;

  // Settings
  rotation?: number;
  volume_enabled?: boolean;

  // Relationships
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
