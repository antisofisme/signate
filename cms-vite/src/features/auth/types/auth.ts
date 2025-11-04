/**
 * Authentication Domain Types
 */

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'super_admin' | 'admin' | 'user';
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

export interface LoginResponse {
  success: boolean;
  data: {
    user: User;
    token: string;
    organizations: Organization[];
  };
}

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
