/**
 * Device Assignment Types
 * Types for playlist, content, and tag assignments
 */

// ========================================
// Playlist Assignments
// ========================================

export interface PlaylistAssignment {
  id: number;
  device_id: number;
  playlist_id: number;
  playlist_name: string;
  playlist_description?: string;
  is_active: boolean;
  assigned_at: string;
  assigned_by_id?: number;
  assigned_by_name?: string;
}

// ========================================
// Content Assignments
// ========================================

export interface ContentAssignment {
  id: number;
  device_id: number;
  content_id: number;
  content_name: string;
  content_type: 'image' | 'video' | 'web_url' | 'web_app';
  content_url?: string;
  thumbnail_url?: string;
  priority: number;
  schedule?: Record<string, any>;
  assigned_at: string;
  expires_at: string | null;
  assigned_by_id?: number;
  assigned_by_name?: string;
}

// ========================================
// Tag Assignments
// ========================================

export interface TagAssignment {
  id: number;
  device_id: number;
  tag_id: number;
  tag_name: string;
  tag_color?: string;
  assigned_at: string;
  assigned_by_id?: number;
  assigned_by_name?: string;
}

// ========================================
// Request Types
// ========================================

export interface AssignContentRequest {
  content_id: number;
  priority?: number;
  schedule?: Record<string, any>;
  expires_at?: string;
}

export interface AssignPlaylistRequest {
  playlist_id: number;
}

export interface AssignTagRequest {
  tag_id: number;
}

export interface BulkAssignPlaylistRequest {
  device_ids: number[];
}

// ========================================
// Response Types
// ========================================

export interface AssignmentResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface BulkAssignmentResponse {
  success: boolean;
  data: {
    assigned: number;
    failed: number;
    errors?: string[];
  };
  message?: string;
}

export interface AssignmentsListResponse<T> {
  success: boolean;
  data: {
    total: number;
    items: T[];
  };
}

// ========================================
// Assignment History
// ========================================

export type AssignmentType = 'playlist' | 'content' | 'tag';

export interface AssignmentHistoryItem {
  id: number;
  type: AssignmentType;
  action: 'assigned' | 'unassigned';
  entity_id: number;
  entity_name: string;
  device_id: number;
  device_name?: string;
  assigned_at: string;
  assigned_by_id?: number;
  assigned_by_name?: string;
  metadata?: Record<string, any>;
}

// ========================================
// Utility Types
// ========================================

export interface AssignmentFilter {
  type?: AssignmentType;
  skip?: number;
  limit?: number;
}

export interface ExpiringAssignment extends ContentAssignment {
  days_until_expiry: number;
  is_expiring_soon: boolean;
  is_expired: boolean;
}
