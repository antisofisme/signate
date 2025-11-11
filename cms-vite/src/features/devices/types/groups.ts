/**
 * Device Groups Types
 */

export interface DeviceGroup {
  id: number
  name: string
  description: string | null
  parent_group_id: number | null
  organization_id: number
  group_type: string | null
  sort_order: number
  default_playlist_id: number | null
  device_count: number
  parent_name: string | null
  full_path: string | null
  created_by: number | null
  created_at: string
  updated_at: string | null
}

export interface CreateDeviceGroupRequest {
  name: string
  description?: string
  parent_group_id?: number
  group_type?: 'chain' | 'hotel' | 'floor' | 'location' | 'custom'
  sort_order?: number
  default_playlist_id?: number
}

export interface UpdateDeviceGroupRequest {
  name?: string
  description?: string
  parent_group_id?: number
  group_type?: 'chain' | 'hotel' | 'floor' | 'location' | 'custom'
  sort_order?: number
  default_playlist_id?: number
}

export interface DeviceGroupStats {
  group_id: number
  total_devices: number
  online_devices: number
  offline_devices: number
}
