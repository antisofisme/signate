/**
 * PMS (Property Management System) Types
 *
 * Types for hotel PMS integration
 */

export type PMSProvider = 'opera' | 'protel' | 'mews' | 'cloudbeds' | 'hotelogix' | 'other'

export interface PMSConfig {
  id?: number
  organization_id: number
  provider: PMSProvider
  is_active: boolean
  connection_config: PMSConnectionConfig
  sync_config: PMSSyncConfig
  field_mapping?: Record<string, string>
  created_at?: string
  updated_at?: string
}

export interface PMSConnectionConfig {
  host: string
  port: number
  protocol: 'http' | 'https' | 'tcp'
  username?: string
  password?: string
  api_key?: string
  timeout?: number
  retry_attempts?: number
  ssl_verify?: boolean
}

export interface PMSSyncConfig {
  auto_sync_enabled: boolean
  sync_interval_minutes: number
  sync_guests: boolean
  sync_rooms: boolean
  sync_reservations: boolean
  last_sync_at?: string
  next_sync_at?: string
}

export interface PMSGuest {
  id: number
  pms_guest_id: string
  organization_id: number
  first_name: string
  last_name: string
  email?: string
  phone?: string
  language?: string
  room_number?: string
  check_in_date?: string
  check_out_date?: string
  vip_status?: boolean
  preferences?: Record<string, any>
  custom_fields?: Record<string, any>
  synced_at: string
  created_at: string
}

export interface PMSRoom {
  id: number
  pms_room_id: string
  organization_id: number
  room_number: string
  room_type?: string
  floor?: number
  building?: string
  status: 'vacant' | 'occupied' | 'maintenance' | 'blocked'
  device_id?: number
  device?: {
    id: number
    name: string
    status: string
  }
  synced_at: string
  created_at: string
}

export interface PMSSyncStatus {
  is_syncing: boolean
  last_sync_at?: string
  next_sync_at?: string
  last_sync_status?: 'success' | 'error' | 'partial'
  last_sync_message?: string
  guests_synced?: number
  rooms_synced?: number
  errors?: string[]
}

export interface PMSStats {
  total_guests: number
  current_guests: number
  total_rooms: number
  occupied_rooms: number
  vacant_rooms: number
  mapped_devices: number
  unmapped_devices: number
  sync_success_rate?: number
  last_sync_duration?: number
}

// Request/Response types
export interface CreatePMSConfigRequest {
  provider: PMSProvider
  connection_config: PMSConnectionConfig
  sync_config: PMSSyncConfig
  field_mapping?: Record<string, string>
}

export interface UpdatePMSConfigRequest {
  provider?: PMSProvider
  is_active?: boolean
  connection_config?: Partial<PMSConnectionConfig>
  sync_config?: Partial<PMSSyncConfig>
  field_mapping?: Record<string, string>
}

export interface TestConnectionRequest {
  provider: PMSProvider
  connection_config: PMSConnectionConfig
}

export interface TestConnectionResponse {
  success: boolean
  message: string
  response_time_ms?: number
  pms_version?: string
  capabilities?: string[]
}

export interface TriggerSyncRequest {
  sync_guests?: boolean
  sync_rooms?: boolean
  sync_reservations?: boolean
  force?: boolean
}

export interface PMSGuestListResponse {
  guests: PMSGuest[]
  total: number
  page: number
  per_page: number
}

export interface PMSRoomListResponse {
  rooms: PMSRoom[]
  total: number
  page: number
  per_page: number
}

export interface MapRoomToDeviceRequest {
  room_id: number
  device_id: number
}

// Filter types
export interface PMSGuestFilters {
  search?: string
  room_number?: string
  is_current?: boolean
  language?: string
  vip_status?: boolean
  page?: number
  per_page?: number
}

export interface PMSRoomFilters {
  search?: string
  room_type?: string
  floor?: number
  status?: PMSRoom['status']
  has_device?: boolean
  page?: number
  per_page?: number
}

// Provider metadata
export interface PMSProviderInfo {
  id: PMSProvider
  name: string
  description: string
  logo?: string
  features: string[]
  connection_type: 'api' | 'database' | 'socket'
  requires_api_key: boolean
  requires_credentials: boolean
  documentation_url?: string
}

export const PMS_PROVIDERS: PMSProviderInfo[] = [
  {
    id: 'opera',
    name: 'Oracle Opera',
    description: 'Industry-leading hotel PMS by Oracle',
    features: ['Guest Management', 'Room Management', 'Reservations', 'Billing'],
    connection_type: 'api',
    requires_api_key: true,
    requires_credentials: true,
    documentation_url: 'https://docs.oracle.com/en/industries/hospitality/opera.html',
  },
  {
    id: 'protel',
    name: 'Protel PMS',
    description: 'European hotel management system',
    features: ['Guest Management', 'Room Management', 'Housekeeping'],
    connection_type: 'api',
    requires_api_key: false,
    requires_credentials: true,
    documentation_url: 'https://www.protel.net/',
  },
  {
    id: 'mews',
    name: 'Mews',
    description: 'Cloud-based hospitality platform',
    features: ['Guest Management', 'Online Check-in', 'Mobile Key'],
    connection_type: 'api',
    requires_api_key: true,
    requires_credentials: false,
    documentation_url: 'https://mews-systems.gitbook.io/',
  },
  {
    id: 'cloudbeds',
    name: 'Cloudbeds',
    description: 'All-in-one hotel management platform',
    features: ['PMS', 'Channel Manager', 'Booking Engine'],
    connection_type: 'api',
    requires_api_key: true,
    requires_credentials: false,
    documentation_url: 'https://hotels.cloudbeds.com/',
  },
  {
    id: 'hotelogix',
    name: 'Hotelogix',
    description: 'Cloud-based hotel PMS',
    features: ['Front Desk', 'Housekeeping', 'Reports'],
    connection_type: 'api',
    requires_api_key: true,
    requires_credentials: true,
    documentation_url: 'https://www.hotelogix.com/',
  },
  {
    id: 'other',
    name: 'Other / Custom',
    description: 'Custom PMS integration',
    features: ['Custom Integration'],
    connection_type: 'api',
    requires_api_key: false,
    requires_credentials: false,
  },
]
