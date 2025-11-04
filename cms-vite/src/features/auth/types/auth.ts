/**
 * Authentication Domain Types
 */

import type { SuccessResponse } from '@/lib/api/responseTypes';
import type { UserRole } from '@/lib/auth/permissions';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  organization_id?: number;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: number;
  name: string;
  organization_pin: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginData {
  user: User;
  token: string;
  organizations: Organization[];
}

export type LoginResponse = SuccessResponse<LoginData>;

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  organization_id?: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  organizations: Organization[];
  selectedOrgId: number | null;
  isAuthenticated: boolean;
}
