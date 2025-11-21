/**
 * PMS (Property Management System) Integration Types
 * Generated from backend-python/services/pms/dtos.py
 */

export type RoomStatus = 'available' | 'occupied' | 'cleaning' | 'maintenance';

// Guest Types
export interface Guest {
  id: number;
  organization_id: number;
  guest_name: string;
  room_number: string;
  checkin_date: string;
  checkout_date: string;
  email?: string;
  phone?: string;
  country?: string;
  reservation_no?: string;
  synced_at: string;
  updated_at: string;
}

export interface GuestListResponse {
  items: Guest[];
  total: number;
}

export interface GuestSyncRequest {
  organization_id: number;
  guest_name: string;
  room_number: string;
  checkin_date: string;
  checkout_date: string;
  email?: string;
  phone?: string;
  country?: string;
  reservation_no?: string;
}

export interface BulkGuestSyncRequest {
  guests: GuestSyncRequest[];
}

// Room Types
export interface Room {
  id: number;
  organization_id: number;
  room_number: string;
  room_type?: string;
  status: RoomStatus;
  floor?: string;
  bed_type?: string;
  max_occupancy?: number;
  synced_at: string;
  updated_at: string;
}

export interface RoomListResponse {
  items: Room[];
  total: number;
}

export interface RoomSyncRequest {
  organization_id: number;
  room_number: string;
  room_type?: string;
  status: RoomStatus;
  floor?: string;
  bed_type?: string;
  max_occupancy?: number;
}

export interface BulkRoomSyncRequest {
  rooms: RoomSyncRequest[];
}

// PMS Configuration Types
export interface PMSConfig {
  id: number;
  organization_id: number;
  api_key: string;
  is_active: boolean;
  last_synced_at?: string;
  sync_interval_minutes: number;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface CreatePMSConfigRequest {
  sync_interval_minutes?: number;
}

export interface UpdatePMSConfigRequest {
  is_active?: boolean;
  sync_interval_minutes?: number;
}

// PMS Statistics Types
export interface PMSStats {
  total_guests: number;
  checkins_today: number;
  checkouts_today: number;
  current_occupancy: number;
  total_rooms: number;
  available_rooms: number;
  occupied_rooms: number;
  last_synced_at?: string;
}
