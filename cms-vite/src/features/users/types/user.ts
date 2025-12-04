/**
 * User Management Domain Types
 */

import type { SuccessResponse } from '@/lib/api/responseTypes';
import type { UserRole as BaseUserRole } from '@/lib/auth/permissions';

// Re-export UserRole for convenience
export type UserRole = BaseUserRole;

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Computed from backend
  organization_name?: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
  organization_id: number;
}

export interface UpdateUserRequest {
  email?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  new_password: string;
}

export interface UserListData {
  users: User[];
  total: number;
  active: number;
}

export interface UserListFilters {
  organization_id?: number;
  role?: UserRole;
  active_only?: boolean;
  // Sorting
  sort_by?: string;
  sort_dir?: 'asc' | 'desc' | null;
}

export type UserResponse = SuccessResponse<User>;
export type UserListResponse = SuccessResponse<UserListData>;
